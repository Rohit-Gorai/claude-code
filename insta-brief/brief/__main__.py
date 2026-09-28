"""Command line entry point.

    python -m brief run                 # fetch → edit (Claude) → render, all in one go
    python -m brief run --mode basic    # same, without AI (feed titles as-is)
    python -m brief fetch               # just rank today's candidates → candidates.json
    python -m brief edit                # candidates.json → edition.json (Claude or basic)
    python -m brief guide               # print the editorial rules + edition.json schema
    python -m brief check               # validate a hand/agent-written edition.json
    python -m brief render              # edition.json → slides + caption + reel.mp4
    python -m brief reel                # rendered slides → reel.mp4 only
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from .config import ROOT, load_config, read_json, write_json


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def cmd_fetch(cfg, out: Path, date) -> list[dict]:
    from .enrich import enrich
    from .fetch import cluster, fetch_all

    _log(f"Fetching {len(cfg['news']['feeds'])} feeds…")
    items = fetch_all(cfg["news"]["feeds"], cfg["news"]["max_age_hours"], log=_log)
    if not items:
        raise SystemExit("No fresh news items fetched — check your internet connection / feed URLs.")
    candidates = cluster(items)
    _log(f"{len(items)} headlines → {len(candidates)} story clusters. Reading top articles…")
    enrich(candidates, cfg["news"].get("enrich_top", 24), log=_log)
    write_json(out / "candidates.json", candidates)
    _log(f"Wrote {out / 'candidates.json'}")
    return candidates


def cmd_edit(cfg, out: Path, date, mode: str, candidates: list[dict]) -> dict:
    from .editor import edit_basic, edit_with_claude

    _log(f"Editing with mode={mode}…")
    raw = edit_with_claude(candidates, cfg, date) if mode == "claude" else edit_basic(candidates, cfg, date)
    write_json(out / "edition.json", raw)
    _log(f"Wrote {out / 'edition.json'}")
    return raw


def cmd_check(cfg, raw: dict, candidates: list[dict]) -> dict:
    from .editor import finalize

    edition, warnings = finalize(raw, candidates, cfg)
    for w in warnings:
        _log(f"  ! {w}")
    _log(f"Edition OK: {len(edition['stories'])} stories, {len(edition['quick_hits'])} quick hits, {len(warnings)} warning(s).")
    return edition


def cmd_render(cfg, out: Path, date, edition: dict) -> None:
    from .render import render

    _log("Rendering slides…")
    files = render(edition, cfg, out, date, log=_log)
    reel = " + reel.mp4" if (out / "reel.mp4").exists() else ""
    _log(f"\nDone → {out}/  ({len(files)} slides + caption.txt + alt_text.txt{reel})")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="brief", description="Make today's Instagram news carousel.")
    ap.add_argument("command", choices=["run", "fetch", "edit", "guide", "check", "render", "reel"])
    ap.add_argument("--config", help="path to config.yaml")
    ap.add_argument("--date", help="edition date YYYY-MM-DD (default: today)")
    ap.add_argument("--out", help="output folder (default: output/<date>)")
    ap.add_argument("--mode", choices=["claude", "basic", "manual"], help="override editor.mode")
    ap.add_argument("--candidates", help="candidates.json (default: <out>/candidates.json)")
    ap.add_argument("--edition", help="edition.json (default: <out>/edition.json)")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    date = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    out = Path(args.out) if args.out else ROOT / "output" / date.isoformat()
    mode = args.mode or cfg["editor"].get("mode", "claude")
    cand_path = Path(args.candidates) if args.candidates else out / "candidates.json"
    ed_path = Path(args.edition) if args.edition else out / "edition.json"
    load_cands = lambda: read_json(cand_path) if cand_path.exists() else []

    if args.command == "guide":
        import json

        from .editor import EDITION_SCHEMA, guide

        print(guide(cfg))
        print("EDITION.JSON SCHEMA\n" + json.dumps(EDITION_SCHEMA, indent=1))
        return
    out.mkdir(parents=True, exist_ok=True)
    if args.command == "fetch":
        cmd_fetch(cfg, out, date)
    elif args.command == "edit":
        cmd_edit(cfg, out, date, "basic" if mode == "manual" else mode, read_json(cand_path))
    elif args.command == "check":
        cmd_check(cfg, read_json(ed_path), load_cands())
    elif args.command == "render":
        cmd_render(cfg, out, date, cmd_check(cfg, read_json(ed_path), load_cands()))
    elif args.command == "reel":
        from .reel import make_reel

        slides = sorted(out.glob("[0-9][0-9]_*.jpg"))
        if not slides:
            raise SystemExit(f"No slides in {out}/. Run `python -m brief render` first.")
        r = cfg.get("reel") or {}
        make_reel(slides, out / "reel.mp4", cfg["brand"]["colors"]["paper"], r.get("cover_seconds", 2.0),
                  r.get("seconds_per_slide", 3.5), log=_log)
    elif args.command == "run":
        candidates = cmd_fetch(cfg, out, date)
        if mode == "manual":
            _log(f"\nManual mode: write {out / 'edition.json'} (see README), then run:\n  python -m brief render --out {out}")
            return
        raw = cmd_edit(cfg, out, date, mode, candidates)
        cmd_render(cfg, out, date, cmd_check(cfg, raw, candidates))


if __name__ == "__main__":
    main()
