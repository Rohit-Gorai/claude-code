"""Open the top stories' article pages to get a lead photo and a few paragraphs of text.

The extra text gives the editor real facts to summarise (RSS blurbs are often one
line), and the og:image is usually the best-quality photo for the slide.
"""

from __future__ import annotations

import io
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from PIL import Image

from .config import ROOT, USER_AGENT
from .fetch import direct_links

MIN_IMAGE_WIDTH = 560  # smaller images look blurry across a 912px-wide slide
# Share-card images with a big publisher logo burned in (e.g. The Guardian's "overlay-base64" cards).
WATERMARKED = ("overlay-base64",)


def usable_image_url(url: str) -> bool:
    return bool(url) and not any(w in url for w in WATERMARKED)


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
    return {
        "image": meta("og:image", "og:image:url", "twitter:image"),
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
            if usable_image_url(art["image"]):
                c["images"] = [art["image"], *[u for u in c["images"] if u != art["image"]]]
    log(f"  enriched {sum(1 for c in candidates[:top] if c.get('article_text'))}/{min(top, len(candidates))} stories with article text")


def download_image(urls: list[str], dest_stem: Path) -> tuple[Path, str] | tuple[None, None]:
    """Save the first usable (big enough, decodable) image. Returns (file path, source url)."""
    for url in urls:
        if not usable_image_url(url):
            continue
        try:
            if url.startswith(("http://", "https://")):
                r = requests.get(url, headers={"User-Agent": USER_AGENT, "Referer": url}, timeout=20)
                r.raise_for_status()
                data = r.content
            else:
                local = Path(url.removeprefix("file://"))
                data = (local if local.is_absolute() or local.exists() else ROOT / local).read_bytes()
            if url.lower().endswith(".svg") or data[:5] == b"<?xml" or data[:4] == b"<svg":
                path = dest_stem.with_suffix(".svg")
                path.write_bytes(data)
                return path, url
            img = Image.open(io.BytesIO(data))
            if img.width < MIN_IMAGE_WIDTH:
                continue
            img = img.convert("RGB")
            path = dest_stem.with_suffix(".jpg")
            img.save(path, "JPEG", quality=92)
            return path, url
        except Exception:
            continue
    return None, None
