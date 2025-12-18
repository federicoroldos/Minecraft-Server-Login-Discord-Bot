from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class TailState:
    log_path: str
    offset_bytes: int
    file_size_bytes: int


def load_state(path: str | Path) -> TailState | None:
    state_path = Path(path)
    if not state_path.exists():
        return None
    raw = json.loads(state_path.read_text(encoding="utf-8"))
    return TailState(
        log_path=str(raw.get("log_path", "")),
        offset_bytes=int(raw.get("offset_bytes", 0)),
        file_size_bytes=int(raw.get("file_size_bytes", 0)),
    )


def save_state(path: str | Path, state: TailState) -> None:
    state_path = Path(path)
    state_path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")

