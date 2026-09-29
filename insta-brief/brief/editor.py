"""The editor: picks the day's stories and writes the copy for every slide.

Three modes:
  claude — Claude API reads the ranked candidates and writes headlines, summaries, caption.
  basic  — no AI; uses feed titles/blurbs as-is (useful for testing the pipeline).
  manual — someone else (Claude Code's brief-editor agent, or you) writes edition.json.

Whatever writes the edition, `finalize()` checks it against the candidates and
turns it into the render-ready shape.
"""

from __future__ import annotations

import datetime as dt
import json
import re

# What a story makes the reader feel. High-arousal emotions (awe, anger, anxiety) and useful or
# surprising stories get shared; low-arousal sadness does not (Berger & Milkman 2012, see VIRALITY.md).
EMOTIONS = ("AWE", "USEFUL", "SURPRISE", "PRIDE", "JOY", "ANGER", "ANXIETY", "SAD")

EDITION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["cover", "stories", "quick_hits", "caption_hook", "engagement_question", "share_line", "hashtags"],
    "properties": {
        "cover": {
            "type": "object",
            "additionalProperties": False,
            "required": ["hook_accent", "hook_rest"],
            "properties": {"hook_accent": {"type": "string"}, "hook_rest": {"type": "string"}},
        },
        "stories": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["candidate_id", "category", "emotion", "headline", "highlight", "tease", "stat", "stat_label",
                             "summary", "why_it_matters", "alt_text"],
                "properties": {
                    "candidate_id": {"type": "string"},
                    "category": {"type": "string"},
                    "emotion": {"type": "string", "enum": list(EMOTIONS)},
                    "headline": {"type": "string"},
                    "highlight": {"type": "string"},
                    "tease": {"type": "string"},
                    "stat": {"type": "string"},
                    "stat_label": {"type": "string"},
                    "summary": {"type": "string"},
                    "why_it_matters": {"type": "string"},
                    "alt_text": {"type": "string"},
                },
            },
        },
        "quick_hits": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["candidate_id", "text"],
                "properties": {"candidate_id": {"type": "string"}, "text": {"type": "string"}},
            },
        },
        "caption_hook": {"type": "string"},
        "engagement_question": {"type": "string"},
        "share_line": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
    },
}

GUIDE = """\
You are the editor of "{name}" ({handle}), an Instagram news page. Each edition is one
carousel of about 8 slides: a cover, {n} story slides, a "Today in numbers" slide (built from the
stories' stats) and a final slide with {q} quick hits, a question and a share line.

Audience: {audience}

HOW INSTAGRAM DECIDES WHO SEES THIS (the research is in VIRALITY.md)
- Strangers only see the post if the people who do see it SEND it to friends (DM shares count
  3-5x more than likes), save it, and spend time on it (swipes, reading). Write for sends and saves.
- Slide 2 matters as much as the cover: Instagram re-shows slide 2 to people who scrolled past
  the cover. Story #1 must work on its own as a second hook.
- Carousels with 8-10 slides get the most engagement; every slide must earn the next swipe.
- The page must read as ORIGINAL work, not a repost of other outlets (Instagram stopped recommending
  aggregators' carousels in 2026). Never copy a publisher's headline or sentences: re-tell each story
  in your own words, add the number that matters and why it matters to the reader.
- No engagement bait: "comment YES", "tag 3 friends", "like if you agree" get demoted. Ask a real
  question people want to answer with a reason.
- Posts about politics, elections, governments and protests are not recommended to non-followers.

THE VIRALITY FORMULA: STOP → SWIPE → FEEL → SHARE
1. STOP. The cover makes a stranger stop scrolling: a 5-8 word hook about the most shareable story
   (a number, a famous name or a stake for the reader) on a photo with a face or strong contrast,
   with a curiosity gap only the carousel closes.
2. SWIPE. Every story slide ends on an open loop: its "Next" bar teases the next story ("Next: the
   ₹ change hitting your wallet"). Stats appear as stickers on the photos and again on the numbers
   slide, which people save.
3. FEEL. High-arousal emotions spread: AWE (records, firsts, science, space), ANGER at an injustice
   or a scam, ANXIETY about something readers can act on, plus USEFUL, SURPRISE, PRIDE and JOY
   stories. SAD stories spread least. Build an arc: open with the most shareable story, give readers
   something useful for their money, and put an AWE / JOY / PRIDE story last. At most one SAD story.
4. SHARE. The last slide asks one question people can answer with an opinion and a reason, and
   tells readers exactly who to send the post to. People share when you name the friend.

HOW TO PICK: THE SEND TEST
Each candidate has `score` (how big the story is: outlets covering it, freshness), `viral` (how
shareable its topic usually is on Instagram) and `flags` (money, wow, pride, stars, surprise,
outrage, alert, numbers, political, grim). Use them as hints, then ask of each candidate: "Would an
18-35 year-old in India forward this to a friend or the family WhatsApp group, or save it?"
Stories that usually pass:
- money in the reader's pocket: prices, EMIs, salaries, taxes, fuel, UPI, jobs, exams, new rules
- India pride, firsts and records; big cricket and sports moments; famous names (stars, athletes, CEOs)
- tech and apps people use every day; trains, flights and travel; space and science "wow"
- "wait, what?" surprises, weird-but-true, big numbers, scams exposed, wholesome human stories
Stories that rarely pass: routine political statements, court procedure, diplomacy without stakes.

- Story #1 (slide 2) and the cover are what non-followers see, so they must be the most shareable
  story AND not political (flag `political`). Put political stories on slide 4 or later, and lead
  with them only when nothing else comes close. Never lead with a tragedy unless it is the day's
  overwhelming story.
- Every edition needs at least one USEFUL "your money" story and one AWE / JOY / PRIDE story when the
  candidates have them. At most 2 stories from one category, at most 2 political stories.
- Order: #1 most shareable (non-political); a "your money" story early; politics and heavy news in
  the middle; the AWE / JOY / PRIDE story last.
- Importance still counts: a huge story (high `score`, many `sources`) belongs in the carousel even
  if it is not fun, just not always as #1.
- Skip opinion pieces, live blogs, stale stories, near-duplicates of the same event, and anything you
  cannot summarise from the material given.
- Quick hits: {q} other notable stories not already in the carousel. Favour useful, surprising or
  feel-good one-liners over dry ones.

HOW TO WRITE: SPECIFIC BEATS GENERIC
(The quoted examples below are made up to show the style. Never reuse their facts.)
- headline: at most ~10 words, Title Case, active voice, present tense. It sits on the photo in big
  white type, so short wins. Lead with the most surprising or useful element: a number (₹, %, a
  record), a famous name, or what changes for the reader. Use "You/Your" when the story really is
  about the reader. No wire-speak ("amid", "slams", "mulls", "sources say"). "Your AC Will Cost ₹3,000
  More From Oct 1" beats "Appliance Makers Announce Price Revision". Curiosity is good; clickbait that
  misleads is not.
- highlight: the 1-4 words that get the red marker, the part that makes someone stop scrolling (the
  number, the name, the twist). Copy it exactly from the headline.
- emotion: the main feeling the story gives the reader, one of AWE, USEFUL, SURPRISE, PRIDE, JOY,
  ANGER, ANXIETY, SAD. Be honest; it is used to check the edition's arc.
- tease: at most 6 words, shown on the slide *before* this story as "Next: …". Tease without
  telling: open a question the slide answers ("Why your bank is open today", "The record nobody
  expected"). Never give away the answer or repeat the headline.
- stat: the story's key number for the photo sticker and the "Today in numbers" slide, at most 8
  characters: "₹3,000", "25 bps", "5.25%", "1st", "120 yrs", "3x". Only a number that is in the
  material; empty string if the story has no honest number. Aim for at least 3 stats per edition.
- stat_label: at most 5 words saying what the stat is, readable on its own on the numbers slide
  ("more for a new AC", "India's rank this year"). Empty string when stat is empty.
- summary: 25-40 words in 2-3 short sentences; each sentence becomes a bullet point on the slide.
  Sentence 1: what happened. Sentence 2: the key number or name. Sentence 3: what happens next.
  Plain English, no jargon, your own words.
- why_it_matters: at most 16 words on what it means for the reader ("Your salary lands on time this
  month"), not for institutions. Empty string if there is no honest answer.
- category: one short caps label such as INDIA, WORLD, MONEY, TECH, SPORTS, CULTURE, SCIENCE, HEALTH,
  POLITICS, CLIMATE.
- alt_text: one sentence describing the slide for screen readers and Instagram and Google search.
  Include the key names and keywords people would search for.
- cover: the first thing a stranger sees, in huge type on story #1's photo. hook_accent (2-4 words,
  red marker) + hook_rest (3-5 words): 5-8 words in total. Make it concrete and open a curiosity
  gap: a stake ("Your bank" / "is open after all"), a surprise ("Greece did it" / "for the first time
  ever"), or a number ("₹3,000 more" / "for your next AC"). Never generic ("Today's top stories",
  "Your daily brief"). Do not repeat the #1 headline word for word.
- quick_hits text: at most 12 words, one line of news, no full stop.
- caption_hook: the first line of the caption, at most 15 words; Instagram cuts it off after ~125
  characters and search reads it first, so it names the #1 story's key name or keyword and its most
  intriguing fact.
- engagement_question: shown on the last slide and in the caption, at most 12 words. A question about
  one story with two clear sides that people want to answer AND explain ("Five-day bank week: good
  idea or bad? Why?"). Detailed comments count; one-word replies barely do. Never engagement bait
  ("comment YES", "tag 3 friends", "type 1 if").
- share_line: shown on the last slide and in the caption. At most 12 words, names who to send the
  post to, tied to a story, starts with "Send this to" ("Send this to the friend who still banks on
  Saturdays"). Specific beats "someone". Never "tag".
- hashtags: 3-5 specific hashtags including the # sign; people search for topics, not #news.
- Write in {language}.

ACCURACY — NON-NEGOTIABLE
- Use only facts present in the candidate material (titles, other_titles, summary, related,
  article_text). Never add numbers, names, dates or quotes that are not there. When sources
  disagree, use the more cautious version or leave the detail out.
- Attribute claims ("police said", "according to the company"); use "accused"/"alleged" where it applies.
- Deaths, disasters, crime: sober and respectful, no puns, never highlight a victim's name.
- Politics and elections: neutral wording, no taking sides.
- Refer to stories only by the candidate ids you were given.
"""


def guide(cfg: dict) -> str:
    b, f, e = cfg["brand"], cfg["format"], cfg["editor"]
    return GUIDE.format(
        name=b["name"], handle=b["handle"], n=f["stories"], q=f["quick_hits"],
        audience=" ".join(e["audience"].split()), language=e.get("language", "English"),
    )


def _brief_candidate(c: dict) -> dict:
    keep = {k: c[k] for k in ("id", "title", "category", "sources", "age_hours", "score", "viral", "flags") if c.get(k) not in (None, [])}
    if len(c.get("other_titles", [])) > 1:
        keep["other_titles"] = c["other_titles"][1:5]
    for k, n in (("summary", 600), ("article_text", 1500)):
        if c.get(k):
            keep[k] = c[k][:n]
    if c.get("related"):
        keep["related"] = c["related"][:5]
    return keep


def edit_with_claude(candidates: list[dict], cfg: dict, date: dt.date) -> dict:
    import anthropic

    pool = [_brief_candidate(c) for c in candidates[:32]]
    user = (
        f"Today is {date:%A, %d %B %Y}. Here are today's ranked story candidates as JSON. "
        f"Build today's edition.\n\n{json.dumps(pool, ensure_ascii=False, indent=1)}"
    )
    client = anthropic.Anthropic()
    with client.beta.messages.stream(
        model=cfg["editor"].get("model", "claude-opus-5"),
        max_tokens=32000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        thinking={"type": "adaptive"},
        output_config={"effort": cfg["editor"].get("effort", "high"), "format": {"type": "json_schema", "schema": EDITION_SCHEMA}},
        system=guide(cfg),
        messages=[{"role": "user", "content": user}],
    ) as stream:
        msg = stream.get_final_message()

    if msg.stop_reason == "refusal":
        detail = getattr(msg, "stop_details", None)
        raise RuntimeError(f"Claude declined to write this edition ({getattr(detail, 'category', None)}). Try --mode basic.")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("Claude's answer was cut off (max_tokens). Try again or lower editor.effort.")
    text = next(b.text for b in msg.content if b.type == "text")
    return json.loads(text)


def _lead_phrase(headline: str) -> str:
    """Basic-mode highlight: the leading run of capitalised words (a name), else the first two words."""
    words = headline.split()
    run = []
    for w in words[:4]:
        if w[:1].isupper() or w[:1].isdigit() or w[:1] in "₹$":
            run.append(w)
        else:
            break
    if 1 <= len(run) <= 3 and len(run) < len(words):
        return " ".join(run)
    return " ".join(words[:2])


def _clip_words(text: str, n: int) -> str:
    words = text.split()
    if len(words) <= n:
        return text.strip()
    cut = " ".join(words[:n])
    end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    return cut[: end + 1] if end > len(cut) * 0.5 else cut.rstrip(",;:") + "…"


def edit_basic(candidates: list[dict], cfg: dict, date: dt.date) -> dict:
    n, q = cfg["format"]["stories"], cfg["format"]["quick_hits"]
    cap = cfg["news"].get("per_category_max", 2)
    picked, per_cat = [], {}
    for c in candidates:
        if per_cat.get(c["category"], 0) >= cap and len(candidates) > n * 2:
            continue
        picked.append(c)
        per_cat[c["category"]] = per_cat.get(c["category"], 0) + 1
        if len(picked) == n:
            break
    rest = [c for c in candidates if c not in picked][:q]
    stories = []
    for c in picked:
        headline = re.split(r"\s[|:–]\s", c["title"])[0]
        body = c.get("summary") or c.get("article_text") or ""
        stories.append(
            {
                "candidate_id": c["id"],
                "category": "BIG STORY" if c["category"] == "TOP" else c["category"],
                "headline": headline,
                "highlight": _lead_phrase(headline),
                "emotion": "",
                "tease": "",
                "stat": "",
                "stat_label": "",
                "summary": _clip_words(body, 40),
                "why_it_matters": "",
                "alt_text": f"News slide: {headline}",
            }
        )
    return {
        "cover": {"hook_accent": "Today's top stories", "hook_rest": "in 60 seconds"},
        "stories": stories,
        "quick_hits": [{"candidate_id": c["id"], "text": _clip_words(c["title"], 12).rstrip(".…")} for c in rest],
        "caption_hook": f"Your 60-second catch-up on {date:%d %B}'s biggest stories 👇",
        "engagement_question": "Which of these stories surprised you most?",
        "share_line": "",
        "hashtags": ["#news", "#india", "#headlines", "#dailybrief"],
    }


_ABBREV = re.compile(r"\b(?:Mr|Mrs|Ms|Dr|St|Jr|Sr|vs|No|Rs|Govt|Gen|Lt|Col|Capt|Prof|Inc|Ltd|Co|Jan|Feb|Aug|Sept?|Oct|Nov|Dec)\.$", re.I)


def bullets(summary: str, limit: int = 3) -> list[str]:
    """Split a summary into the slide's bullet points without breaking on "Dr.", "U.S." or "5.25%"."""
    parts, cur = [], ""
    for chunk in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9₹$\"'(“‘])", " ".join(summary.split())):
        cur = f"{cur} {chunk}".strip()
        if _ABBREV.search(cur) or re.search(r"\b[A-Z]\.$", cur):
            continue  # "Dr. Rao" or "U.S. Senate": the sentence goes on
        parts.append(cur)
        cur = ""
    if cur:
        parts.append(cur)
    if len(parts) > limit:
        parts = parts[: limit - 1] + [" ".join(parts[limit - 1 :])]
    return parts


KEYCAPS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


def finalize(raw: dict, candidates: list[dict], cfg: dict) -> tuple[dict, list[str]]:
    """Validate a raw edition against the candidates; return (render-ready edition, warnings)."""
    by_id = {c["id"]: c for c in candidates}
    warnings: list[str] = []
    stories, used = [], set()
    for s in raw.get("stories", []):
        cid = s.get("candidate_id")
        c = by_id.get(cid)
        if not s.get("headline") or not s.get("summary"):
            warnings.append(f"story {cid!r} is missing a headline or summary — dropped")
            continue
        if c is None and not s.get("sources"):
            warnings.append(f"story '{s.get('headline', '')[:40]}' has unknown candidate_id {cid!r} and no sources — dropped")
            continue
        if cid and cid in used:
            warnings.append(f"duplicate story {cid} dropped")
            continue
        if cid:
            used.add(cid)
        headline = " ".join(s["headline"].split())
        hl = s.get("highlight", "").strip()
        i = headline.lower().find(hl.lower()) if hl else -1
        if i < 0:
            warnings.append(f"highlight {hl!r} not in headline {headline!r} — using lead words")
            hl = _lead_phrase(headline)
            i = headline.find(hl)
        hl = headline[i : i + len(hl)]
        stat, stat_label = " ".join((s.get("stat") or "").split()), " ".join((s.get("stat_label") or "").split())
        if len(stat) > 10:
            warnings.append(f"stat {stat!r} for {cid} is {len(stat)} characters (max 8) — dropped from the sticker")
            stat, stat_label = "", ""
        elif len(stat) > 8:
            warnings.append(f"stat {stat!r} for {cid} is {len(stat)} characters (max 8); it will be shrunk to fit")
        emotion = (s.get("emotion") or "").strip().upper()
        if emotion and emotion not in EMOTIONS:
            warnings.append(f"emotion {emotion!r} for {cid} is not one of {', '.join(EMOTIONS)} — ignored")
        n_words = len(s["summary"].split())
        if n_words > 48:
            warnings.append(f"summary for {cid} is {n_words} words (aim for 25-40); it will be shrunk to fit")
        longest = max((len(b.split()) for b in bullets(s["summary"])), default=0)
        if longest > 26:
            warnings.append(f"summary for {cid} has a {longest}-word sentence; use 2-3 short sentences (each one is a bullet on the slide)")
        stories.append(
            {
                "rank": len(stories) + 1,
                "candidate_id": cid,
                "category": s.get("category", "").upper()[:14],
                "emotion": emotion if emotion in EMOTIONS else "",
                "headline": headline,
                "hl_before": headline[:i],
                "hl_text": hl,
                "hl_after": headline[i + len(hl) :],
                "tease": " ".join((s.get("tease") or "").split()).rstrip("."),
                "stat": stat,
                "stat_label": stat_label if stat else "",
                "summary": s["summary"].strip(),
                "why_it_matters": s.get("why_it_matters", "").strip(),
                "alt_text": s.get("alt_text", headline),
                "sources": s.get("sources") or (c["sources"][:3] if c else []),
                "link": s.get("link") or (c["links"][0]["url"] if c and c.get("links") else ""),
                "images": s["images"] if "images" in s else (c["images"] if c else []),  # [] = typographic card
                "image_position": s.get("image_position", ""),
                "credit": s.get("credit", ""),
            }
        )
    if stories and stories[0]["category"] in ("POLITICS", "ELECTIONS"):
        warnings.append("story #1 is POLITICS: Instagram won't show it to non-followers, so lead with a non-political story if one is close")
    want = cfg["format"]["stories"]
    if len(stories) < want:
        warnings.append(f"only {len(stories)} stories (config asks for {want})")
    stories = stories[:want]
    # Quick hits carry news claims too, so they must point at a real candidate
    # (unless no candidates were loaded at all, e.g. the sample edition).
    hits = []
    for h in raw.get("quick_hits", []):
        text, hid = (h.get("text") or "").strip().rstrip("."), h.get("candidate_id")
        if not text:
            continue
        if by_id and hid not in by_id:
            warnings.append(f"quick hit {text[:40]!r} has unknown candidate_id {hid!r} — dropped")
            continue
        if hid and hid in used:
            warnings.append(f"quick hit {hid} repeats a story or another quick hit — dropped")
            continue
        if hid:
            used.add(hid)
        hits.append({"text": text, "candidate_id": hid})
    hits = hits[: cfg["format"]["quick_hits"]]
    tags = [t if t.startswith("#") else f"#{t}" for t in raw.get("hashtags", [])][:5]
    edition = {
        "cover": raw.get("cover") or {"hook_accent": "Today's top stories", "hook_rest": "in 60 seconds"},
        "stories": stories,
        "quick_hits": hits,
        "caption_hook": raw.get("caption_hook", ""),
        "engagement_question": raw.get("engagement_question", ""),
        "share_line": (raw.get("share_line") or "").strip(),
        "hashtags": tags,
    }
    warnings += formula_warnings(edition)
    edition["caption"] = build_caption(edition, cfg)
    return edition, warnings


BAIT = re.compile(r"\b(comment|type|reply|drop)\s+(yes|no|a?\s?\d|['\"“]?\w+['\"”]?\s+below)\b|\btag\s+(a|your|\d+|three|two)\b|"
                  r"\blike\s+(if|this if)\b|\bdouble[- ]tap\b|\bfollow\s+for\s+follow\b", re.I)
GENERIC_HOOKS = ("top stories", "headlines", "daily brief", "your brief", "60 seconds", "today's news", "news today")


def formula_warnings(ed: dict) -> list[str]:
    """Check the edition against the STOP → SWIPE → FEEL → SHARE formula (see GUIDE)."""
    out = []
    hook = f"{ed['cover'].get('hook_accent', '')} {ed['cover'].get('hook_rest', '')}".lower()
    if any(g in hook for g in GENERIC_HOOKS):
        out.append(f"STOP: cover hook {hook.strip()!r} is generic; name something concrete from story #1")
    for s in ed["stories"][1:]:
        if not s["tease"]:
            out.append(f"SWIPE: story #{s['rank']} has no tease, so slide {s['rank']} can't end on 'Next: …'")
        elif len(s["tease"].split()) > 6:
            out.append(f"SWIPE: tease for #{s['rank']} is {len(s['tease'].split())} words (max 6)")
    n_stats = sum(1 for s in ed["stories"] if s.get("stat"))
    if ed["stories"] and n_stats < 3:
        out.append(f"SAVE: only {n_stats} stories have a stat; the 'Today in numbers' slide needs 3, so it is skipped")
    moods = [s.get("emotion", "") for s in ed["stories"]]
    if any(moods):
        if moods.count("SAD") > 1:
            out.append(f"FEEL: {moods.count('SAD')} SAD stories; sadness spreads least, keep it to one")
        if moods[0] == "SAD":
            out.append("FEEL: story #1 is SAD; lead with an AWE, USEFUL, SURPRISE or PRIDE story if one is close")
        if not any(m in ("AWE", "JOY", "PRIDE") for m in moods):
            out.append("FEEL: no AWE / JOY / PRIDE story; the edition needs one high point, ideally last")
        elif moods[-1] not in ("AWE", "JOY", "PRIDE", "SURPRISE"):
            out.append(f"FEEL: the last story is {moods[-1] or 'untagged'}; end on AWE / JOY / PRIDE so people leave on a high")
    q = ed.get("engagement_question", "")
    if not q:
        out.append("SHARE: no engagement_question for the last slide")
    elif len(q.split()) > 12:
        out.append(f"SHARE: engagement question is {len(q.split())} words; make it answerable at a glance (max 12)")
    for field in ("engagement_question", "share_line", "caption_hook"):
        if BAIT.search(ed.get(field, "")):
            out.append(f"SHARE: {field} looks like engagement bait ({BAIT.search(ed[field]).group(0)!r}); Instagram demotes it")
    share = ed.get("share_line", "")
    if not share:
        out.append("SHARE: no share_line ('Send this to the friend who …')")
    elif len(share.split()) > 12:
        out.append(f"SHARE: share_line is {len(share.split())} words (max 12)")
    return out


def build_caption(ed: dict, cfg: dict) -> str:
    lines = [ed["caption_hook"], ""]
    for s in ed["stories"]:
        num = KEYCAPS[s["rank"] - 1] if s["rank"] <= len(KEYCAPS) else f"{s['rank']}."
        lines.append(f"{num} {s['headline']}")
    if ed["quick_hits"]:
        lines += ["", "⚡ Quick hits on the last slide"]
    if ed["engagement_question"]:
        lines += ["", f"💬 {ed['engagement_question']}"]
    share = ed.get("share_line") or "Send it to someone who needs to know"
    lines += ["", f"✈️ {share}", f"📌 Save this for later  ·  🗞️ Follow {cfg['brand']['handle']} for your daily brief"]
    sources = list(dict.fromkeys(src for s in ed["stories"] for src in s["sources"]))
    if sources:
        lines += ["", "Sources: " + ", ".join(sources)]
    if ed["hashtags"]:
        lines += ["", " ".join(ed["hashtags"])]
    return "\n".join(lines).strip() + "\n"
