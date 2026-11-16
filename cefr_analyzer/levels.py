"""Shared CEFR ordering. A CEFR-J sublevel is collapsed to its CEFR band."""

import re

LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")


def levels_in(value: str) -> list[str]:
    return re.findall(r"[ABC][12]", str(value).upper())


def lowest(values) -> str | None:
    found = []
    for value in values:
        found.extend(levels_in(value))
    return min(found, key=LEVELS.index) if found else None


def number(level: str) -> int:
    return LEVELS.index(level) + 1


def band(score: float) -> str:
    return LEVELS[max(0, min(5, int(score + 0.5) - 1))]
