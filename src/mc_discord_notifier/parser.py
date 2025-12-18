from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class EventType(str, Enum):
    JOIN = "join"
    LEAVE = "leave"


@dataclass(frozen=True)
class PlayerEvent:
    type: EventType
    player: str
    raw_line: str


_ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")

_JOIN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r": \[\+\] (?P<player>[^\s]+)\s*$"),
    re.compile(r": (?P<player>.+) joined the game\s*$"),
]

_LEAVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r": \[-\] (?P<player>[^\s]+)\s*$"),
    re.compile(r": (?P<player>.+) left the game\s*$"),
]


def _strip_ansi(s: str) -> str:
    return _ANSI_ESCAPE_RE.sub("", s)


def parse_line(line: str) -> PlayerEvent | None:
    clean = _strip_ansi(line).rstrip("\r\n")

    for pat in _JOIN_PATTERNS:
        m = pat.search(clean)
        if m:
            return PlayerEvent(type=EventType.JOIN, player=m.group("player"), raw_line=clean)

    for pat in _LEAVE_PATTERNS:
        m = pat.search(clean)
        if m:
            return PlayerEvent(type=EventType.LEAVE, player=m.group("player"), raw_line=clean)

    return None

