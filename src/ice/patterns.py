"""One place that compiles and runs bank patterns, so matching is uniform."""

from __future__ import annotations

import re
from functools import lru_cache

FLAGS = re.IGNORECASE | re.DOTALL
EVIDENCE_PAD = 60


class PatternError(ValueError):
    """A bank pattern is not a valid regular expression."""


@lru_cache(maxsize=4096)
def compile_pattern(pattern: str) -> re.Pattern[str]:
    try:
        return re.compile(pattern, FLAGS)
    except re.error as exc:
        raise PatternError(f"bad pattern {pattern!r}: {exc}") from exc


def first_match(patterns: list[str], text: str) -> str | None:
    """Return a short excerpt around the first hit, or None when nothing hits."""
    for pattern in patterns:
        found = compile_pattern(pattern).search(text)
        if found:
            start = max(found.start() - EVIDENCE_PAD, 0)
            end = min(found.end() + EVIDENCE_PAD, len(text))
            return " ".join(text[start:end].split())
    return None
