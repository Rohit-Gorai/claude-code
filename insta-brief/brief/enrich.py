"""Open the top stories' article pages to get a lead photo and a few paragraphs of text.

The extra text gives the editor real facts to summarise (RSS blurbs are often one
line), and the og:image is usually the best-quality photo for the slide.
"""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import USER_AGENT
from .fetch import direct_links
from .photos import usable_image_url


def _ld_images(soup) -> list[tuple[int, str]]:
    """Lead-photo URLs from the page's JSON-LD (often larger than og:image), with width when given."""
    found = []

    def walk(node):
        if isinstance(node, list):
            for n in node:
                walk(n)
        elif isinstance(node, dict):
            img = node.get("image")
            for i in img if isinstance(img, list) else [img]:
                if isinstance(i, str):
                    found.append((0, i))
                elif isinstance(i, dict) and (i.get("url") or i.get("contentUrl")):
                    try:
                        width = int(str(i.get("width") or 0).rstrip("px") or 0)
                    except ValueError:
                        width = 0
                    found.append((width, i.get("url") or i.get("contentUrl")))
            for k in ("@graph", "mainEntity"):
                walk(node.get(k))

    for tag in soup.find_all("script", type="application/ld+json")[:6]:
        try:
            walk(json.loads(tag.string or ""))
        except Exception:
            continue
    return found


def _article(url: str) -> dict:
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text[:3_000_000], "html.parser")

    def meta(*names):
        for n in names:
            tag = soup.find("meta", attrs={"property": n}) or soup.find("meta", attrs={"name": n})
            if tag and tag.get("content"):
                return tag["content"].strip()
        return ""

    scope = soup.find("article") or soup
    paras = [re.sub(r"\s+", " ", p.get_text(" ")).strip() for p in scope.find_all("p")]
    junk = ("also read", "read more", "subscribe", "subscription", "newsletter", "sign up", "unlock", "download the app")
    paras = [p for p in paras if len(p) > 70 and not any(j in p.lower()[:160] for j in junk)]
    lead = meta("og:image", "og:image:secure_url", "og:image:url", "twitter:image", "twitter:image:src")
    extra = [u for _, u in sorted(_ld_images(soup), key=lambda x: -x[0])]
    return {
        "image": lead,
        "images": list(dict.fromkeys(urljoin(url, u) for u in [lead, *extra] if u and u.startswith(("http", "/")))),
        "description": meta("og:description", "description", "twitter:description"),
        "text": " ".join(paras)[:1800],
    }


def enrich(candidates: list[dict], top: int, log=print) -> None:
    """Mutates the first `top` candidates in place: adds article_text and a lead image."""

    def one(c):
        for url in direct_links(c)[:3]:
            try:
                return c, _article(url), url
            except Exception:
                continue
        return c, None, None

    with ThreadPoolExecutor(max_workers=8) as pool:
        for c, art, url in pool.map(one, candidates[:top]):
            if not art:
                continue
            if art["text"]:
                c["article_text"] = art["text"]
            if art["description"] and len(art["description"]) > len(c.get("summary", "")):
                c["summary"] = art["description"][:600]
            page = [u for u in art["images"] if usable_image_url(u)]
            if page:  # the article's lead photo (and its larger JSON-LD versions) go first
                c["images"] = list(dict.fromkeys([*page[:3], *c["images"]]))
    log(f"  enriched {sum(1 for c in candidates[:top] if c.get('article_text'))}/{min(top, len(candidates))} stories with article text")
