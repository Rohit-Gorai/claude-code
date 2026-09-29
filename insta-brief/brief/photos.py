"""Get the sharpest possible photo for every slide.

News sites hand out small, re-compressed copies of their photos (`photo-1200x675.jpg`,
`?w=800`, Wikimedia `800px-` thumbnails). For each image URL we also try the bigger versions
the same server usually has, keep the original file bytes (no re-compression), and pick the
photo that needs the least stretching to fill its space on the slide:

    stretch = max(slot width / photo width, slot height / photo height)

1.0 or less is pixel-sharp. The cover is the hardest slot (1080×1440 filled edge to edge,
so a landscape photo needs to be ~2560px wide). When a photo has to be stretched anyway, it is
enlarged with Lanczos resampling and a light unsharp mask, which looks crisper than letting the
browser stretch it.
"""

from __future__ import annotations

import io
import math
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

import requests
from PIL import Image, ImageFilter, ImageOps

from .config import ROOT, USER_AGENT

MIN_WIDTH = 480            # anything smaller is never used
MAX_SIDE = 4000            # bigger originals are scaled down to this (plenty for a 1080px slide)
MAX_BYTES = 40_000_000
SHARP, OK = 1.0, 1.3       # stretch thresholds: ≤1.0 sharp, ≤1.3 fine, above that visibly soft
WATERMARKED = ("overlay-base64", "branded_news")  # share cards with a publisher logo burned in (Guardian, BBC)
# Query parameters that only resize/re-compress; everything else (signatures, ids) is kept.
SIZE_PARAMS = {
    "w", "width", "h", "height", "resize", "fit", "size", "quality", "q", "crop", "strip", "downsize",
    "im", "impolicy", "imwidth", "dpr", "auto", "format", "fm", "ar", "c", "sz", "wid", "hei", "scale",
    "output-quality", "output-format", "compress", "type",
}


def usable_image_url(url: str) -> bool:
    return bool(url) and not any(w in url for w in WATERMARKED)


def bigger_variants(url: str) -> list[str]:
    """URLs that likely serve a larger version of the same photo, best first, the original last."""
    if not url.startswith(("http://", "https://")):
        return [url]
    parts = urlsplit(url)
    host, path = parts.netloc.lower(), parts.path
    query = parse_qsl(parts.query, keep_blank_values=True)
    out = []
    # An image proxy with the original inside it: ...?url=https%3A%2F%2F...
    for k, v in query:
        v = unquote(v)
        if k.lower() in ("url", "src", "image", "img") and v.startswith("http"):
            out += bigger_variants(v)
    up = path
    if "wikimedia.org" in host:  # /thumb/a/ab/Name.jpg/800px-Name.jpg → /a/ab/Name.jpg (the original)
        up = re.sub(r"^(/wikipedia/[^/]+/)thumb/(\w/\w\w/[^/]+)/[^/]+$", r"\1\2", up)
    up = re.sub(r"-\d{2,4}x\d{2,4}(\.(?:jpe?g|png|webp))$", r"\1", up, flags=re.I)  # WordPress: photo-1200x675.jpg
    up = re.sub(r"/upload/(?:[a-z]{1,2}_[^/]+/)+", "/upload/", up)                   # Cloudinary transforms
    up = re.sub(r"/tr:[^/]+/", "/", up)                                             # ImageKit transforms
    if "ichef.bbci.co.uk" in host:                                                  # BBC: /news/976/ → /news/2048/
        up = re.sub(r"/(news|ace/standard|ace/ws)/\d{3,4}/", r"/\1/2048/", up)
    if "googleusercontent.com" in host or "ggpht.com" in host:                      # =w1200-h630 → =s0 (original)
        up = re.sub(r"=[swh]\d+[^/]*$", "=s0", up)
    lean = urlencode([(k, v) for k, v in query if k.lower() not in SIZE_PARAMS])
    for p, q in ((up, lean), (up, parts.query), (path, lean), (path, parts.query)):
        out.append(urlunsplit((parts.scheme, parts.netloc, p, q, "")))
    return list(dict.fromkeys(out))


@dataclass
class Photo:
    data: bytes
    url: str
    width: int
    height: int
    fmt: str

    def stretch(self, slot: tuple[int, int]) -> float:
        return max(slot[0] / self.width, slot[1] / self.height)


def _get(url: str) -> bytes:
    if not url.startswith(("http://", "https://")):
        local = Path(url.removeprefix("file://"))
        return (local if local.is_absolute() or local.exists() else ROOT / local).read_bytes()
    with requests.get(url, headers={"User-Agent": USER_AGENT, "Referer": url}, timeout=20, stream=True) as r:
        r.raise_for_status()
        data = b""
        for chunk in r.iter_content(1 << 16):
            data += chunk
            if len(data) > MAX_BYTES:
                raise ValueError("image too large")
        return data


def _decode(data: bytes, url: str) -> Photo | None:
    img = Image.open(io.BytesIO(data))
    img.load()
    w, h = ImageOps.exif_transpose(img).size if img.getexif().get(0x0112, 1) != 1 else img.size
    if w < MIN_WIDTH or not 0.4 <= w / h <= 2.6:  # tiny, or a banner/strip rather than a photo
        return None
    return Photo(data, url, w, h, (img.format or "").upper())


def best_version(url: str, log=None) -> Photo | None:
    """Download the largest version of one photo among `bigger_variants(url)`."""
    best = None
    for v in bigger_variants(url)[:5]:
        try:
            photo = _decode(_get(v), v)
        except Exception:
            continue
        if photo and (best is None or photo.width * photo.height > best.width * best.height):
            best = photo
        if best and best.width >= 2400:
            break
    return best


def pick(urls: list[str], slot: tuple[int, int], limit: int = 6) -> Photo | None:
    """The photo to use for a slot: the first sharp one, else the least stretched.

    URLs come best-first (the editor's choice, or the article's lead photo), so an earlier photo
    wins unless a later one is clearly sharper (needs less than 85% of its stretch).
    """
    tried: list[Photo] = []
    for url in [u for u in urls if usable_image_url(u)][:limit]:
        if url.lower().split("?")[0].endswith(".svg"):
            try:
                return Photo(_get(url), url, 10_000, 10_000, "SVG")  # vectors are always sharp
            except Exception:
                continue
        photo = best_version(url)
        if not photo:
            continue
        if photo.stretch(slot) <= SHARP:
            return photo
        tried.append(photo)
    if not tried:
        return None
    best = min(tried, key=lambda p: p.stretch(slot))
    for p in tried:  # keep the earlier (better-chosen) photo when it is nearly as sharp
        if p.stretch(slot) <= best.stretch(slot) / 0.85:
            return p
    return best


def save(photo: Photo, dest_stem: Path, slot: tuple[int, int]) -> Path:
    """Write the photo for rendering: original bytes when possible, enhanced when it must stretch."""
    if photo.fmt == "SVG":
        path = dest_stem.with_suffix(".svg")
        path.write_bytes(photo.data)
        return path
    img = Image.open(io.BytesIO(photo.data))
    img = ImageOps.exif_transpose(img)
    s = photo.stretch(slot)
    if s > 1.02:
        # Enlarge once, carefully, instead of letting the browser stretch it.
        img = img.convert("RGB").resize((math.ceil(img.width * s), math.ceil(img.height * s)), Image.LANCZOS)
        img = img.filter(ImageFilter.UnsharpMask(radius=min(2.5, 0.9 * s), percent=int(45 + 25 * min(s - 1, 1.2)), threshold=2))
    elif max(img.size) > MAX_SIDE:
        img = img.convert("RGB")
        img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    elif photo.fmt in ("JPEG", "PNG", "WEBP"):
        path = dest_stem.with_suffix("." + photo.fmt.lower().replace("jpeg", "jpg"))
        path.write_bytes(photo.data)  # untouched original: no second round of compression
        return path
    path = dest_stem.with_suffix(".jpg")
    img.convert("RGB").save(path, "JPEG", quality=97, subsampling=0, optimize=True)
    return path


def verdict(stretch: float) -> str:
    return "sharp" if stretch <= SHARP else "fine" if stretch <= OK else "soft"
