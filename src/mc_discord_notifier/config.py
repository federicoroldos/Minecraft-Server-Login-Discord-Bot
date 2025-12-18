from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AppConfig:
    channel_id: int
    log_path: str
    start_from_end: bool = True
    poll_interval_seconds: float = 0.25
    debounce_seconds: float = 2.0
    messages: dict[str, str] | None = None


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))

    def get(key: str, default: Any = None) -> Any:
        return raw[key] if key in raw else default

    channel_id = int(get("channel_id", 0))
    log_path = str(get("log_path", "")).strip()
    if channel_id <= 0:
        raise ValueError("config.channel_id must be a Discord channel ID (integer).")
    if not log_path:
        raise ValueError("config.log_path must be a path to latest.log.")

    messages = get("messages", None)
    if messages is not None and not isinstance(messages, dict):
        raise ValueError("config.messages must be an object.")

    return AppConfig(
        channel_id=channel_id,
        log_path=log_path,
        start_from_end=bool(get("start_from_end", True)),
        poll_interval_seconds=float(get("poll_interval_seconds", 0.25)),
        debounce_seconds=float(get("debounce_seconds", 2.0)),
        messages=messages,
    )

