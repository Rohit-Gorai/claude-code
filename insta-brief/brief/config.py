"""Config loading and small shared helpers."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)


def load_config(path: str | Path | None = None) -> dict:
    path = Path(path) if path else ROOT / "config.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def edition_number(cfg: dict, date: dt.date) -> str:
    first = cfg["brand"].get("first_edition_date") or date
    if isinstance(first, str):
        first = dt.date.fromisoformat(first)
    return f"No. {max(1, (date - first).days + 1):03d}"


def date_label(date: dt.date) -> str:
    return f"{date.day:02d} {date.strftime('%B').upper()} {date.year}"


def read_json(path: str | Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, data) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
