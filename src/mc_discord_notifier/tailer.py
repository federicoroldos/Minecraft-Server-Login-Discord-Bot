from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .parser import PlayerEvent, parse_line
from .state import TailState, load_state, save_state


@dataclass(frozen=True)
class TailerSettings:
    log_path: str
    start_from_end: bool
    poll_interval_seconds: float
    state_path: str


class LogTailer:
    def __init__(self, settings: TailerSettings, on_event: Callable[[PlayerEvent], None]) -> None:
        self._settings = settings
        self._on_event = on_event
        self._stop = False

        self._path = Path(settings.log_path)
        self._buf = b""
        self._offset = 0

    def stop(self) -> None:
        self._stop = True

    def _initial_offset(self) -> int:
        state = load_state(self._settings.state_path)
        if state and os.path.normcase(state.log_path) == os.path.normcase(self._settings.log_path):
            try:
                size = self._path.stat().st_size
            except FileNotFoundError:
                return 0
            if 0 <= state.offset_bytes <= size:
                return state.offset_bytes

        if self._settings.start_from_end:
            try:
                return self._path.stat().st_size
            except FileNotFoundError:
                return 0

        return 0

    def run_forever(self) -> None:
        self._offset = self._initial_offset()

        while not self._stop:
            try:
                size = self._path.stat().st_size
                if size < self._offset:
                    self._offset = 0
                    self._buf = b""

                if size > self._offset:
                    with self._path.open("rb") as f:
                        f.seek(self._offset)
                        data = f.read()
                    self._offset += len(data)
                    self._consume(data)

                save_state(
                    self._settings.state_path,
                    TailState(
                        log_path=self._settings.log_path,
                        offset_bytes=self._offset,
                        file_size_bytes=size,
                    ),
                )
            except FileNotFoundError:
                pass
            except OSError:
                pass

            time.sleep(self._settings.poll_interval_seconds)

    def _consume(self, data: bytes) -> None:
        self._buf += data
        while True:
            idx = self._buf.find(b"\n")
            if idx == -1:
                break
            raw_line = self._buf[: idx + 1]
            self._buf = self._buf[idx + 1 :]

            line = raw_line.decode("utf-8", errors="ignore")
            event = parse_line(line)
            if event:
                self._on_event(event)

