"""Turn a finalized edition into Instagram-ready slides (JPEG) + caption files."""

from __future__ import annotations

import base64
import datetime as dt
import functools
import math
import os
import random
from pathlib import Path
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import ROOT, date_label, edition_number, write_json
from .enrich import download_image

TEMPLATES = ROOT / "templates"
FONTS = ROOT / "assets" / "fonts"


FONT_FACES = [  # (family, file, weight, style)
    ("Playfair Display", "PlayfairDisplay.ttf", "400 900", "normal"),
    ("Crimson Pro", "CrimsonPro.ttf", "200 900", "normal"),
    ("Crimson Pro", "CrimsonPro-Italic.ttf", "200 900", "italic"),
    ("Poppins", "Poppins-SemiBold.ttf", "600", "normal"),
    ("Poppins", "Poppins-Bold.ttf", "700", "normal"),
    ("Poppins", "Poppins-ExtraBold.ttf", "800", "normal"),
]


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


def creases(seed: int, width: int, height: int, n: int = 16) -> str:
    """Faint fold lines (light edge + soft shadow) so the paper reads as crumpled newsprint."""
    r = random.Random(seed)
    paths = []
    for _ in range(n):
        x1, y1 = r.uniform(-200, width + 200), r.uniform(-200, height + 200)
        angle, length = r.uniform(0, math.pi), r.uniform(500, 1600)
        x2, y2 = x1 + length * math.cos(angle), y1 + length * math.sin(angle)
        mx, my = (x1 + x2) / 2 + r.uniform(-60, 60), (y1 + y2) / 2 + r.uniform(-60, 60)
        d = f"M{x1:.0f},{y1:.0f} Q{mx:.0f},{my:.0f} {x2:.0f},{y2:.0f}"
        paths.append(
            f'<path d="{d}" stroke="#000" stroke-opacity="{r.uniform(.05, .12):.2f}" stroke-width="3" fill="none" '
            f'filter="url(#soft)" transform="translate(2,2)"/>'
            f'<path d="{d}" stroke="#fff" stroke-opacity="{r.uniform(.5, .9):.2f}" stroke-width="2.5" fill="none" filter="url(#soft)"/>'
        )
    return "".join(paths)


def _credit(story: dict, image_url: str | None) -> str:
    src = ", ".join(story["sources"][:2])
    if not image_url or not image_url.startswith("http"):
        return f"Source: {src}" if src else ""
    host = urlparse(image_url).netloc.removeprefix("www.")
    return f"Source: {src}  ·  Image: {host}" if src else f"Image: {host}"


def _prepare_images(edition: dict, img_dir: Path, html_dir: Path, log=print) -> None:
    img_dir.mkdir(parents=True, exist_ok=True)
    for s in edition["stories"]:
        path, url = download_image(s.get("images", []), img_dir / f"story{s['rank']}")
        s["image_file"] = os.path.relpath(path, html_dir) if path else ""
        s["credit"] = s.get("credit") or _credit(s, url)
        s["fallback_word"] = s["hl_text"] or s["category"]
        if not path:
            log(f"  no usable photo for #{s['rank']} — using a typographic card")


def render(edition: dict, cfg: dict, out_dir: Path, date: dt.date, log=print) -> list[Path]:
    from playwright.sync_api import sync_playwright

    out_dir = Path(out_dir)
    html_dir = out_dir / "_html"
    html_dir.mkdir(parents=True, exist_ok=True)
    _prepare_images(edition, out_dir / "images", html_dir, log)

    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["j2", "html"]))
    fmt, brand = cfg["format"], cfg["brand"]
    common = {
        "brand": brand,
        "fmt": fmt,
        "css": (TEMPLATES / "style.css").read_text(encoding="utf-8"),
        "font_css": font_css(),
        "edition_no": edition_number(cfg, date),
        "date_str": date_label(date),
        "min_figure": 300 if fmt["height"] >= 1400 else 250,
    }
    stories = edition["stories"]
    slides = [("cover", "cover.html.j2", {"cover": edition["cover"], "cover_stories": stories[:3]})]
    for i, s in enumerate(stories):
        slides.append((f"story{s['rank']}", "story.html.j2", {"story": s, "last": i == len(stories) - 1}))
    if edition.get("quick_hits"):
        slides.append(("quickhits", "wrap.html.j2", {"quick_hits": edition["quick_hits"]}))

    written = []
    launch = {"executable_path": os.environ["BRIEF_CHROMIUM"]} if os.environ.get("BRIEF_CHROMIUM") else {}
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": fmt["width"], "height": fmt["height"]}, device_scale_factor=1)
        for n, (kind, tpl, ctx) in enumerate(slides, 1):
            seed = date.toordinal() % 97 + n
            html = env.get_template(tpl).render(
                **common, **ctx, kind=kind.rstrip("0123456789"), seed=seed,
                creases=creases(seed, fmt["width"], fmt["height"]),
            )
            html_path = html_dir / f"{n:02d}_{kind}.html"
            html_path.write_text(html, encoding="utf-8")
            page.goto(html_path.resolve().as_uri())
            page.evaluate("window.__layout()")
            out = out_dir / f"{n:02d}_{kind}.jpg"
            page.screenshot(path=str(out), type="jpeg", quality=fmt.get("jpeg_quality", 95))
            written.append(out)
            log(f"  ✓ {out.name}")
        browser.close()

    (out_dir / "caption.txt").write_text(edition["caption"], encoding="utf-8")
    alt = [f"Slide 1: {brand['name']} — {edition['cover']['hook_accent']} {edition['cover']['hook_rest']}"]
    alt += [f"Slide {s['rank'] + 1}: {s['alt_text']}" for s in stories]
    if edition.get("quick_hits"):
        alt.append(f"Slide {len(stories) + 2}: Quick hits — " + "; ".join(h["text"] for h in edition["quick_hits"]))
    (out_dir / "alt_text.txt").write_text("\n".join(alt) + "\n", encoding="utf-8")
    write_json(out_dir / "edition.final.json", edition)
    return written
