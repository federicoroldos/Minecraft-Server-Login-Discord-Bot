from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class EventType(str, Enum):
    JOIN = "join"
    LEAVE = "leave"
    DEATH = "death"


@dataclass(frozen=True)
class PlayerEvent:
    type: EventType
    player: str
    raw_line: str
    message: str | None = None


_ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
_MC_COLOR_CODE_RE = re.compile(r"\u00a7[0-9A-FK-ORa-fk-or]")

_JOIN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r": \[\+\] (?P<player>[^\s]+)\s*$"),
    re.compile(r": (?P<player>.+) joined the game\s*$"),
]

_LEAVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r": \[-\] (?P<player>[^\s]+)\s*$"),
    re.compile(r": (?P<player>.+) left the game\s*$"),
]

_DEATH_PATTERNS: list[re.Pattern[str]] = [
    # English (default)
    re.compile(
        r"^(?:"
        r"died|"
        r"was\b|"
        r"fell\b|"
        r"blew up|"
        r"hit the ground too hard|"
        r"experienced kinetic energy|"
        r"drowned|"
        r"burned|"
        r"went up in flames|"
        r"walked into\b|"
        r"tried to swim in lava|"
        r"starved|"
        r"suffocated|"
        r"withered|"
        r"froze"
        r")\b",
        re.IGNORECASE,
    ),
    # Spanish (common variants). This list is intentionally broad, but still
    # anchored to the start of the death message to avoid false positives.
    re.compile(
        r"^(?:"
        r"mur(?:i[oó]|io)|"
        r"fue (?:asesinad[oa]|abatid[oa]|disparad[oa]|eliminad[oa]) por|"
        r"se (?:ahog[oó]|quemo|quem[oó]|asfixi[oó])|"
        r"intent[oó] nadar en lava|"
        r"cay[oó]|"
        r"recibi[oó] (?:daño|danio) cin[eé]tico|"
        r"muri[oó] de hambre|"
        r"se (?:marchit[oó]|congel[oó])|"
        r"fue alcanzad[oa] por un rayo|"
        r"fue atravesad[oa]"
        r")\b",
        re.IGNORECASE,
    ),
]

_PLAYER_PREFIX_RE = re.compile(r": (?P<player>[A-Za-z0-9_]{1,16}) (?P<rest>.+)\s*$")


def _strip_ansi(s: str) -> str:
    s = _ANSI_ESCAPE_RE.sub("", s)
    return _MC_COLOR_CODE_RE.sub("", s)


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

    # Vanilla/Paper death messages look like:
    #   "[Server thread/INFO]: playerName was slain by Zombie"
    # We whitelist common death-message patterns (English + Spanish) to avoid
    # matching chat/advancements.
    m = _PLAYER_PREFIX_RE.search(clean)
    if m:
        player = m.group("player")
        rest = m.group("rest").strip()
        if any(pat.search(rest) for pat in _DEATH_PATTERNS):
            return PlayerEvent(
                type=EventType.DEATH,
                player=player,
                raw_line=clean,
                message=f"{player} {rest}",
            )

    return None

