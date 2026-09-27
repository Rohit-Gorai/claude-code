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

EDITION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["cover", "stories", "quick_hits", "caption_hook", "engagement_question", "hashtags"],
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
                "required": ["candidate_id", "category", "headline", "highlight", "summary", "why_it_matters", "alt_text"],
                "properties": {
                    "candidate_id": {"type": "string"},
                    "category": {"type": "string"},
                    "headline": {"type": "string"},
                    "highlight": {"type": "string"},
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
        "hashtags": {"type": "array", "items": {"type": "string"}},
    },
}

GUIDE = """\
You are the editor of "{name}" ({handle}), an Instagram news page. Each edition is one
carousel: a cover slide, {n} story slides, and a final "quick hits" slide with {q} one-liners.

Audience: {audience}

HOW TO PICK
- Biggest first. Favour stories many outlets are covering (`sources`, `score`) and stories that
  touch readers' lives: money and prices, jobs, tech they use, safety, big sporting moments,
  major world events, big culture moments.
- Story #1 matters most. Instagram re-shows slide 2 to people who didn't swipe, so #1 must be the
  strongest, most broadly interesting story of the day.
- Mix it up: at most 2 stories from one category. Include one uplifting or "wow" story (science,
  sport, achievement, something surprising) when there is one — those get shared.
- Skip opinion pieces, live blogs, stale stories, near-duplicates of the same event, and anything you
  cannot summarise from the material given.
- Quick hits: {q} other notable stories that are not already in the carousel.

HOW TO WRITE
- headline: at most ~11 words, Title Case, active voice, present tense, concrete. "Rupee Falls to
  Record Low Against Dollar" beats "Rupee Sees Movement". Curiosity is good; clickbait that
  misleads is not.
- highlight: the 1-4 word hook of the headline that gets coloured red, usually the who/what at the
  start ("Ai+ Smartphone" in "Ai+ Smartphone Powers Bigg Boss 20"). Copy it exactly from the headline.
- summary: 25-40 words of plain English: what happened, the key number or name, what happens next.
  Short sentences. No jargon.
- why_it_matters: at most 16 words, the "so what" for an ordinary reader. Empty string if there is no
  honest answer.
- category: one short caps label such as INDIA, WORLD, MONEY, TECH, SPORTS, CULTURE, SCIENCE, HEALTH,
  POLITICS, CLIMATE.
- alt_text: one sentence describing the slide for screen readers and Instagram search.
- cover: two short lines. hook_accent (red, 2-4 words) + hook_rest (3-6 words). Either a promise
  ("Today's biggest headlines" / "in 60 seconds") or a teaser built on story #1. Do not repeat the
  #1 headline word for word.
- quick_hits text: at most 12 words, one line of news, no full stop.
- caption_hook: the first line of the caption, at most 15 words, makes people tap "more".
- engagement_question: one civil question tied to a story that invites opinions in the comments.
- hashtags: 3-5 relevant hashtags including the # sign.
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
    keep = {k: c[k] for k in ("id", "title", "category", "sources", "age_hours", "score") if k in c}
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
        "hashtags": ["#news", "#india", "#headlines", "#dailybrief"],
    }


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
        n_words = len(s["summary"].split())
        if n_words > 48:
            warnings.append(f"summary for {cid} is {n_words} words (aim for 25-40); it will be shrunk to fit")
        stories.append(
            {
                "rank": len(stories) + 1,
                "candidate_id": cid,
                "category": s.get("category", "").upper()[:14],
                "headline": headline,
                "hl_before": headline[:i],
                "hl_text": hl,
                "hl_after": headline[i + len(hl) :],
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
        "hashtags": tags,
    }
    edition["caption"] = build_caption(edition, cfg)
    return edition, warnings


def build_caption(ed: dict, cfg: dict) -> str:
    lines = [ed["caption_hook"], ""]
    for s in ed["stories"]:
        num = KEYCAPS[s["rank"] - 1] if s["rank"] <= len(KEYCAPS) else f"{s['rank']}."
        lines.append(f"{num} {s['headline']}")
    if ed["quick_hits"]:
        lines += ["", "⚡ Quick hits on the last slide"]
    if ed["engagement_question"]:
        lines += ["", f"💬 {ed['engagement_question']}"]
    lines += [
        "",
        "📌 Save this for later  ·  ✈️ Send it to someone who needs to know",
        f"🗞️ Follow {cfg['brand']['handle']} for your daily brief",
    ]
    sources = list(dict.fromkeys(src for s in ed["stories"] for src in s["sources"]))
    if sources:
        lines += ["", "Sources: " + ", ".join(sources[:8])]
    if ed["hashtags"]:
        lines += ["", " ".join(ed["hashtags"])]
    return "\n".join(lines).strip() + "\n"
