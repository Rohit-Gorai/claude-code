"""Small inset maps with a pin, for "where did this happen" on a story's photo.

Borders come from Natural Earth's India point-of-view dataset (public domain), so maps of India
show India's official boundaries, as an Indian news page must. The pin must fall inside the
named country, which catches wrong coordinates before they reach a slide.
"""

from __future__ import annotations

import functools
import json
import math

from .config import ROOT

MAP_FILE = ROOT / "assets" / "maps" / "countries.json"


@functools.cache
def countries() -> dict:
    return json.loads(MAP_FILE.read_text(encoding="utf-8"))


def _inside(lon: float, lat: float, ring: list) -> bool:
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def contains(iso3: str, lat: float, lon: float, slack: float = 0.35) -> bool:
    """Is (lat, lon) in the country (or within `slack` degrees of its coast, for port cities)?"""
    c = countries().get((iso3 or "").upper())
    if not c:
        return False
    if any(_inside(lon, lat, r) for r in c["rings"]):
        return True
    return any(math.hypot(x - lon, y - lat) <= slack for r in c["rings"] for x, y in r)


def _bbox(rings: list) -> tuple[float, float, float, float]:
    xs = [x for r in rings for x, _ in r]
    ys = [y for r in rings for _, y in r]
    return min(xs), min(ys), max(xs), max(ys)


def inset_svg(iso3: str, lat: float, lon: float, size: int = 260) -> str:
    """An SVG map of the country with its neighbours faded around it and a pin at (lat, lon)."""
    world = countries()
    home = world[iso3.upper()]
    # Frame the main landmass (the ring holding the pin, else the biggest), not far-flung islands.
    rings = sorted(home["rings"], key=len, reverse=True)
    main = next((r for r in rings if _inside(lon, lat, r)), rings[0])
    x0, y0, x1, y1 = _bbox([main])
    x0, x1, y0, y1 = min(x0, lon), max(x1, lon), min(y0, lat), max(y1, lat)
    span = max(x1 - x0, (y1 - y0), 6.0) * 1.18  # small countries still get some context
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    k = math.cos(math.radians(cy))  # equirectangular, corrected for latitude
    scale = size / span

    def pt(x: float, y: float) -> tuple[float, float]:
        return (size / 2 + (x - cx) * k * scale, size / 2 - (y - cy) * scale)

    def path(ring: list) -> str:
        return "M" + "L".join(f"{a:.1f},{b:.1f}" for a, b in (pt(x, y) for x, y in ring)) + "Z"

    half = span / 2 / max(k, 0.3) + 2
    near = []
    for code, c in world.items():
        if code == iso3.upper():
            continue
        bx0, by0, bx1, by1 = _bbox(c["rings"])
        if bx1 < cx - half or bx0 > cx + half or by1 < cy - span or by0 > cy + span:
            continue
        near.append("".join(path(r) for r in c["rings"]))
    px, py = pt(lon, lat)
    return (
        f'<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">'
        f'<path d="{"".join(near)}" fill="#3a3a40" stroke="#56565e" stroke-width="1"/>'
        f'<path d="{"".join(path(r) for r in home["rings"])}" fill="#f4efe6" stroke="#ffffff" stroke-width="1.5"/>'
        f'<circle cx="{px:.1f}" cy="{py:.1f}" r="15" fill="#E3120B" opacity=".25"/>'
        f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7.5" fill="#E3120B" stroke="#fff" stroke-width="3"/>'
        "</svg>"
    )
