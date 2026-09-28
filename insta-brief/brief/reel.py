"""Turn a rendered carousel into a vertical Reel (reel.mp4).

Reels are how Instagram shows a page to people who don't follow it yet (Trial Reels go *only* to
non-followers), while carousels mostly reach existing followers. The Reel is the same slides on a
9:16 canvas with a slow push-in and crossfades. It is silent on purpose: add a trending track in
the Instagram app when posting.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PIL import Image

W, H = 1080, 1920
SLIDE_W = 940  # narrower than the frame so Instagram's like/comment buttons don't cover the text
TOP = 230      # starts below the Reels header
ZOOM = 0.04    # slow push-in over each slide


def ffmpeg_exe() -> str | None:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


def timeline(n_slides: int, cover_seconds: float, seconds: float) -> list[tuple[float, float]]:
    """(start, end) in seconds for each slide."""
    spans, t = [], 0.0
    for i in range(n_slides):
        d = cover_seconds if i == 0 else seconds
        spans.append((t, t + d))
        t += d
    return spans


def make_reel(slides: list[Path], out: Path, paper: str = "#F1EEE8", cover_seconds: float = 2.0,
              seconds: float = 3.5, fps: int = 30, fade: float = 0.35, size: tuple[int, int] = (W, H),
              log=print) -> Path | None:
    exe = ffmpeg_exe()
    if not exe:
        log("  (no ffmpeg found, so no reel.mp4: run `pip install imageio-ffmpeg`)")
        return None
    w, h = size
    sw = round(w * SLIDE_W / W)
    imgs = [Image.open(p).convert("RGB") for p in slides]
    sh = round(sw * imgs[0].height / imgs[0].width)
    x0, y0 = (w - sw) // 2, min(round(h * TOP / H), h - sh)
    bg = Image.new("RGB", (w, h), paper)
    spans = timeline(len(imgs), cover_seconds, seconds)

    def slide_at(i: int, t: float) -> Image.Image:
        start, end = spans[i]
        z = 1 + ZOOM * min(max((t - start) / (end - start), 0), 1)
        zw, zh = round(sw * z), round(sh * z)
        big = imgs[i].resize((zw, zh), Image.BICUBIC)
        left, top = (zw - sw) // 2, (zh - sh) // 2
        return big.crop((left, top, left + sw, top + sh))

    cmd = [exe, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
           "-r", str(fps), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
           "-preset", "medium", "-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = spans[-1][1]
    for k in range(round(total * fps)):
        t = k / fps
        i = next(j for j, (s, e) in enumerate(spans) if t < e or j == len(spans) - 1)
        tile = slide_at(i, t)
        end = spans[i][1]
        if i + 1 < len(imgs) and t > end - fade:
            tile = Image.blend(tile, slide_at(i + 1, end), (t - (end - fade)) / fade)
        frame = bg.copy()
        frame.paste(tile, (x0, y0))
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        log("  ! ffmpeg failed, so there is no reel.mp4")
        return None
    log(f"  ✓ {out.name} ({total:.0f}s, 9:16)")
    return out
