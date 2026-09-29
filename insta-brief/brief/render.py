"""Turn a finalized edition into Instagram-ready slides (JPEG) + caption files."""

from __future__ import annotations

import base64
import datetime as dt
import functools
import io
import math
import os
from pathlib import Path
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image

from . import photos
from .config import ROOT, write_json

TEMPLATES = ROOT / "templates"
FONTS = ROOT / "assets" / "fonts"


FONT_FACES = [  # (family, file, weight, style)
    ("Poppins", "Poppins-Medium.ttf", "500", "normal"),
    ("Poppins", "Poppins-SemiBold.ttf", "600", "normal"),
    ("Poppins", "Poppins-Bold.ttf", "700", "normal"),
    ("Poppins", "Poppins-ExtraBold.ttf", "800", "normal"),
    ("Poppins", "Poppins-Black.ttf", "900", "normal"),
]
MIN_STATS = 3  # the "Today in numbers" slide needs at least this many stories with a stat


@functools.cache
def font_css() -> str:
    """Fonts are inlined as data URIs: Chromium refuses to load fonts across file:// URLs."""
    rules = []
    for family, file, weight, style in FONT_FACES:
        data = base64.b64encode((FONTS / file).read_bytes()).decode()
        rules.append(
            f'@font-face {{ font-family: "{family}"; font-weight: {weight}; font-style: {style}; '
            f'src: url(data:font/ttf;base64,{data}) format("truetype"); }}'
        )
    return "\n".join(rules)


def logo_uri(brand: dict, key: str = "logo") -> str:
    """A logo as a data URI (so rendering never depends on file:// access rules)."""
    if not brand.get(key):
        return logo_uri(brand) if key != "logo" else ""
    path = Path(brand[key])
    path = path if path.is_absolute() else ROOT / path
    mime = "image/svg+xml" if path.suffix.lower() == ".svg" else f"image/{path.suffix.lower().lstrip('.').replace('jpg', 'jpeg')}"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def _credit(story: dict, image_url: str | None) -> str:
    src = ", ".join(story["sources"][:2])
    if not image_url or not image_url.startswith("http"):
        return src
    host = urlparse(image_url).netloc.removeprefix("www.")
    return f"{src} · Photo: {host}" if src else f"Photo: {host}"


def _prepare_images(edition: dict, img_dir: Path, html_dir: Path, fmt: dict, log=print) -> None:
    """Pick and prepare the sharpest photo for each story (see photos.py) and report its quality."""
    img_dir.mkdir(parents=True, exist_ok=True)
    cover_slot = (fmt["width"], fmt["height"])                # story #1's photo also fills the whole cover
    story_slot = (fmt["width"], round(fmt["height"] * 0.62))  # the photo area of a story slide, at most
    missing, soft, tried = [], [], 0
    for s in edition["stories"]:
        slot = cover_slot if s["rank"] == 1 else story_slot
        photo = photos.pick(s.get("images", []), slot)
        if not photo:
            s["image_file"] = ""
            s["credit"] = s.get("credit") or _credit(s, None)
            missing.append(f"#{s['rank']}")
            tried += len(s.get("images", []))
            log(f"  no usable photo for #{s['rank']} ({len(s.get('images', []))} URL(s) tried) — using a designed fallback card")
            continue
        path = photos.save(photo, img_dir / f"story{s['rank']}", slot, ai=fmt.get("ai_upscale", True))
        s["image_file"] = os.path.relpath(path, html_dir)
        s["credit"] = s.get("credit") or _credit(s, photo.url)
        stretch = photo.stretch(slot)
        size = "vector" if photo.fmt == "SVG" else f"{photo.width}×{photo.height}"
        how = {"ai": "AI-upscaled", "sharpened": "enlarged + sharpened"}.get(photo.enhanced, "")
        log(f"  #{s['rank']} photo {size} → {photos.verdict(stretch)} on the {'cover' if s['rank'] == 1 else 'slide'}"
            + (f" (needed {stretch:.1f}×, {how})" if how else ""))
        if stretch > photos.OK:
            soft.append(f"#{s['rank']} (needs ~{math.ceil(photo.width * stretch / 100) * 100}px wide)")
    n = len(edition["stories"])
    log(f"  Photos: {n - len(missing)}/{n} stories have a real photo" + (f"; missing {', '.join(missing)}" if missing else ""))
    if soft:
        log(f"  ! Soft photos: {', '.join(soft)}. They were enhanced, but a bigger original (Wikimedia, a press kit, "
            "the agency's full-size file) will still look sharper.")
    if missing and tried and len(missing) == n:
        log("  ! Every photo download failed. If this machine blocks news/image websites, allow them and re-render.")


def stat_stories(edition: dict) -> list[dict]:
    return [s for s in edition["stories"] if s.get("stat")]


def plan_slides(edition: dict) -> list[tuple[str, str, dict]]:
    """The carousel, in order: cover → stories → today in numbers (if enough stats) → quick hits."""
    stories = edition["stories"]
    stats = stat_stories(edition)
    has_numbers = len(stats) >= MIN_STATS
    slides = [("cover", "cover.html.j2", {"cover": edition["cover"], "lead": stories[0] if stories else {}, "rest": stories[1:5], "stories": stories, "dark_top": True})]
    for i, s in enumerate(stories):
        if i + 1 < len(stories):
            text = stories[i + 1].get("tease") or stories[i + 1]["headline"]
        else:
            text = "Today in numbers" if has_numbers else "Quick hits"
        slides.append((f"story{s['rank']}", "story.html.j2", {"story": s, "next_text": text, "dark_top": True}))
    if has_numbers:
        slides.append(("numbers", "numbers.html.j2", {"stats": stats[:5], "dark_top": True}))
    if edition.get("quick_hits"):
        slides.append(("quickhits", "wrap.html.j2", {
            "quick_hits": edition["quick_hits"],
            "question": edition.get("engagement_question", ""),
            "share_line": edition.get("share_line", ""),
            "dark_top": False,
        }))
    return slides


def render(edition: dict, cfg: dict, out_dir: Path, date: dt.date, log=print) -> list[Path]:
    from playwright.sync_api import sync_playwright

    out_dir = Path(out_dir)
    html_dir = out_dir / "_html"
    html_dir.mkdir(parents=True, exist_ok=True)
    fmt, brand = cfg["format"], cfg["brand"]
    _prepare_images(edition, out_dir / "images", html_dir, fmt, log)

    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["j2", "html"]))
    tall = fmt["height"] >= 1400
    slides = plan_slides(edition)
    common = {
        "brand": brand,
        "fmt": fmt,
        "css": (TEMPLATES / "style.css").read_text(encoding="utf-8"),
        "font_css": font_css(),
        "logo": logo_uri(brand),
        "logo_white": logo_uri(brand, "logo_white"),
        "date_short": f"{date.day} {date:%b}".upper(),
        "total": len(slides),
        "min_media": 700 if tall else 620,        # story photo never shrinks below this
        "cover_min_photo": 560 if tall else 480,  # cover text starts no higher than this
    }

    written = []
    launch = {"executable_path": os.environ["BRIEF_CHROMIUM"]} if os.environ.get("BRIEF_CHROMIUM") else {}
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": fmt["width"], "height": fmt["height"]}, device_scale_factor=1)
        for n, (kind, tpl, ctx) in enumerate(slides, 1):
            html = env.get_template(tpl).render(**common, **ctx, kind=kind.rstrip("0123456789"), index=n)
            html_path = html_dir / f"{n:02d}_{kind}.html"
            html_path.write_text(html, encoding="utf-8")
            page.goto(html_path.resolve().as_uri())
            page.evaluate("window.__layout()")
            out = out_dir / f"{n:02d}_{kind}.jpg"
            # Lossless capture, then one high-quality JPEG with full colour resolution (4:4:4), so red
            # text and fine detail stay crisp after Instagram re-compresses the upload.
            shot = Image.open(io.BytesIO(page.screenshot(type="png"))).convert("RGB")
            shot.save(out, "JPEG", quality=fmt.get("jpeg_quality", 100), subsampling=0, optimize=True)
            written.append(out)
            log(f"  ✓ {out.name}")
        browser.close()

    (out_dir / "caption.txt").write_text(edition["caption"], encoding="utf-8")
    alt = []
    for n, (kind, _, ctx) in enumerate(slides, 1):
        if kind == "cover":
            alt.append(f"Slide {n}: {brand['name']} — {edition['cover']['hook_accent']} {edition['cover']['hook_rest']}")
        elif kind.startswith("story"):
            alt.append(f"Slide {n}: {ctx['story']['alt_text']}")
        elif kind == "numbers":
            alt.append(f"Slide {n}: Today in numbers — " + "; ".join(f"{s['stat']} {s.get('stat_label', '')}".strip() for s in ctx["stats"]))
        else:
            alt.append(f"Slide {n}: Quick hits — " + "; ".join(h["text"] for h in edition["quick_hits"]))
    (out_dir / "alt_text.txt").write_text("\n".join(alt) + "\n", encoding="utf-8")
    write_json(out_dir / "edition.final.json", edition)
    return written
