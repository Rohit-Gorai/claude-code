"""Pull RSS feeds, group headlines about the same event, and rank the groups.

The ranking is the "what is everyone talking about" signal: a story covered by
many outlets, recently, and featured in top-story feeds floats to the top.
"""

from __future__ import annotations

import datetime as dt
import html
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

from .config import USER_AGENT

STOPWORDS = set(
    """a an the and or but of to in on at for from by with as is are was were be been being it its this that these those
    has have had will would can could may might should says said say new news live latest update updates today watch
    video photos report reports after over amid into up out about than more most just what why how who when where
    vs his her their our your they them he she we you not no yes all any some first last big top day week year
    """.split()
)
SKIP = re.compile(
    r"\b(horoscope|quiz|crossword|wordle|sudoku|live blog|live updates|podcast|in pictures|op-ed|editorial|"
    r"letters to the editor|obituary|sponsored|deal of the day|how to watch|where to watch|lottery result)\b"
    r"|\bopinion\s*[:|–-]|\|\s*opinion\b",
    re.I,
)


MONTHS = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
DATES = re.compile(
    rf"\b(?:\d{{1,2}}(?:st|nd|rd|th)?\s+{MONTHS}|{MONTHS}\s+\d{{1,2}}(?:st|nd|rd|th)?|{MONTHS})\b|\b20[2-3]\d\b"
    r"|\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
)


def _tokens(title: str) -> set[str]:
    # Dates ("September 27", "2026") appear in unrelated headlines and must not glue stories together.
    text = DATES.sub(" ", title.lower().replace("’", "'").replace("'s", ""))
    words = re.findall(r"[a-z0-9₹$%]+", text)
    out = set()
    for w in words:
        if w in STOPWORDS or (len(w) < 3 and not w.isdigit()):
            continue
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.add(w)
    return out


def _text(fragment: str) -> str:
    if not fragment:
        return ""
    return re.sub(r"\s+", " ", BeautifulSoup(fragment, "html.parser").get_text(" ")).strip()


def _host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _is_google(url: str) -> bool:
    return "news.google." in url


def _entry_images(entry, summary_html: str) -> list[str]:
    urls = []
    for m in entry.get("media_content", []) or []:
        if m.get("url") and (m.get("medium") in (None, "image") or "image" in m.get("type", "")):
            urls.append(m["url"])
    for m in entry.get("media_thumbnail", []) or []:
        if m.get("url"):
            urls.append(m["url"])
    for enc in entry.get("enclosures", []) or []:
        if "image" in enc.get("type", "") and enc.get("href"):
            urls.append(enc["href"])
    if summary_html and "<img" in summary_html:
        img = BeautifulSoup(summary_html, "html.parser").find("img")
        if img and img.get("src"):
            urls.append(img["src"])
    return [u for u in dict.fromkeys(urls) if u.startswith("http")]


def _load(feed: dict) -> bytes:
    url = feed["url"]
    if url.startswith(("http://", "https://")):
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
        r.raise_for_status()
        return r.content
    return Path(url.removeprefix("file://")).read_bytes()


def parse_feed(feed: dict, content: bytes, now: dt.datetime) -> list[dict]:
    parsed = feedparser.parse(content)
    feed_title = feed.get("name") or _text(parsed.feed.get("title", "")) or _host(feed["url"])
    feed_title = re.split(r"\s[-|:]\s", feed_title)[0].strip()
    items = []
    for e in parsed.entries:
        title = html.unescape(e.get("title", "")).strip()
        link = e.get("link", "")
        if not title or not link:
            continue
        source = (e.get("source") or {}).get("title") or feed_title
        if title.endswith(f" - {source}"):
            title = title[: -len(source) - 3].strip()
        when = e.get("published_parsed") or e.get("updated_parsed")
        published = dt.datetime(*when[:6], tzinfo=dt.timezone.utc) if when else now
        summary_html = e.get("summary", "") or ""
        related = []
        if _is_google(link) and "<li" in summary_html:
            # Google News topic feeds list other outlets' headlines for the same story.
            soup = BeautifulSoup(summary_html, "html.parser")
            for li in soup.find_all("li"):
                a, font = li.find("a"), li.find("font")
                if a and a.get_text(strip=True):
                    related.append(f"{a.get_text(strip=True)} — {font.get_text(strip=True) if font else ''}".strip(" —"))
            summary = ""
        else:
            summary = _text(summary_html)
            if summary.startswith(title[:40]) or _is_google(link):
                summary = "" if len(summary) < len(title) + 20 else summary
        items.append(
            {
                "title": title,
                "link": link,
                "source": source,
                "category": feed.get("category", "TOP"),
                "top": bool(feed.get("top")),
                "published": published,
                "summary": summary[:700],
                "related": related[:8],
                "images": _entry_images(e, summary_html),
            }
        )
    return items


def fetch_all(feeds: list[dict], max_age_hours: float, now: dt.datetime | None = None, log=print) -> list[dict]:
    now = now or dt.datetime.now(dt.timezone.utc)

    def one(feed):
        try:
            return feed, parse_feed(feed, _load(feed), now), None
        except Exception as exc:  # a dead feed must never kill the run
            return feed, [], exc

    items = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        for feed, got, err in pool.map(one, feeds):
            short = feed["url"][:70]
            if err:
                log(f"  ✗ {short}  ({type(err).__name__}: {str(err)[:80]})")
                continue
            fresh = [i for i in got if (now - i["published"]).total_seconds() <= max_age_hours * 3600]
            fresh = [i for i in fresh if not SKIP.search(i["title"])]
            log(f"  ✓ {short}  {len(fresh)}/{len(got)} fresh")
            items.extend(fresh)
    return items


def _similar(a: set[str], b: set[str]) -> bool:
    if not a or not b:
        return False
    shared = len(a & b)
    overlap = shared / min(len(a), len(b))
    return (shared >= 3 and overlap >= 0.45) or (shared >= 2 and overlap >= 0.75) or shared / len(a | b) >= 0.5


def cluster(items: list[dict], now: dt.datetime | None = None, limit: int = 60) -> list[dict]:
    """Greedy clustering on headline keywords, then score each cluster."""
    now = now or dt.datetime.now(dt.timezone.utc)
    clusters: list[list[dict]] = []
    toks: list[list[set[str]]] = []
    for item in sorted(items, key=lambda i: i["published"], reverse=True):
        t = _tokens(item["title"])
        for ci, members in enumerate(toks):
            if any(_similar(t, m) for m in members):
                clusters[ci].append(item)
                members.append(t)
                break
        else:
            clusters.append([item])
            toks.append([t])

    out = []
    for members in clusters:
        sources = list(dict.fromkeys(m["source"] for m in members))
        newest = max(m["published"] for m in members)
        age_h = max(0.0, (now - newest).total_seconds() / 3600)
        related = max((m["related"] for m in members), key=len)
        images = list(dict.fromkeys(u for m in members for u in m["images"]))
        cats = Counter(m["category"] for m in members if m["category"] != "TOP")
        titles = list(dict.fromkeys(m["title"] for m in members))
        summaries = sorted({m["summary"] for m in members if m["summary"]}, key=len, reverse=True)
        score = (
            1.5 * len(sources)
            + 0.5 * min(len(related), 6)
            + 2.0 * 0.5 ** (age_h / 10)
            + (1.0 if any(m["top"] for m in members) else 0.0)
            + (0.3 if images else 0.0)
        )
        out.append(
            {
                "title": min(titles, key=lambda s: abs(len(s) - 75)),
                "other_titles": titles[:6],
                "summary": summaries[0] if summaries else "",
                "related": related,
                "sources": sources[:8],
                "links": [{"url": m["link"], "source": m["source"]} for m in members][:10],
                "category": cats.most_common(1)[0][0] if cats else "TOP",
                "published": newest.isoformat(),
                "age_hours": round(age_h, 1),
                "images": images[:6],
                "score": round(score, 2),
            }
        )
    out.sort(key=lambda c: c["score"], reverse=True)
    return [{"id": f"c{i:02d}", **c} for i, c in enumerate(out[:limit], 1)]


def direct_links(candidate: dict) -> list[str]:
    return [l["url"] for l in candidate["links"] if not _is_google(l["url"])]


if __name__ == "__main__":  # quick manual check: python -m brief.fetch
    from .config import load_config

    cfg = load_config()
    got = fetch_all(cfg["news"]["feeds"], cfg["news"]["max_age_hours"], log=lambda m: print(m, file=sys.stderr))
    for c in cluster(got)[:20]:
        print(f'{c["score"]:5.1f}  {len(c["sources"])} src  {c["category"]:8} {c["title"]}')
