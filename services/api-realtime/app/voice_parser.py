import re
from typing import Literal

from shared_schemas.realtime import SituationEvent


HashSide = Literal["left", "middle", "right"]


def _extract_down(transcript: str) -> int:
    lower = transcript.lower()
    if "4th" in lower or "fourth" in lower:
        return 4
    if "3rd" in lower or "third" in lower:
        return 3
    if "2nd" in lower or "second" in lower:
        return 2
    return 1


def _extract_distance(transcript: str) -> int:
    match = re.search(r"and\s+(\d{1,2})", transcript.lower())
    if not match:
        return 5
    value = int(match.group(1))
    return min(max(value, 1), 99)


def _extract_shell(transcript: str) -> str:
    lower = transcript.lower()
    if "cover 2" in lower or "tampa 2" in lower:
        return "Cover 2"
    if "cover 4" in lower or "quarters" in lower:
        return "Cover 4"
    if "cover 1" in lower:
        return "Cover 1"
    return "Cover 3"


def _extract_front(transcript: str) -> str:
    lower = transcript.lower()
    if "nickel" in lower:
        return "Nickel"
    if "dime" in lower:
        return "Dime"
    if "3-4" in lower:
        return "3-4"
    return "Base"


def _extract_hash(transcript: str) -> HashSide:
    lower = transcript.lower()
    if "left hash" in lower:
        return "left"
    if "middle" in lower:
        return "middle"
    return "right"


def parse_situation_from_transcript(transcript: str) -> SituationEvent:
    return SituationEvent(
        down=_extract_down(transcript),
        distance=_extract_distance(transcript),
        yard_line=42,
        clock_seconds=300,
        offense_personnel="11",
        defense_shell=_extract_shell(transcript),
        defense_front=_extract_front(transcript),
        hash=_extract_hash(transcript),
    )
