"""What a grader is, and the scoring rule every grader shares."""

from __future__ import annotations

from typing import Protocol

from ice.models import CompetenceTask
from ice.results import ElementResult, ForbiddenResult, Verdict


class GraderError(Exception):
    """The grader could not produce a judgment for this answer."""


class Grader(Protocol):
    name: str

    def grade(
        self, task: CompetenceTask, answer: str
    ) -> tuple[list[ElementResult], list[ForbiddenResult]]:
        """Judge one answer. Returns a result for every element and forbidden rule."""
        ...


def score(elements: list[ElementResult]) -> float:
    total = sum(element.weight for element in elements)
    met = sum(element.weight for element in elements if element.met)
    return round(met / total, 4) if total else 0.0


def verdict(
    threshold: float, elements: list[ElementResult], forbidden: list[ForbiddenResult]
) -> Verdict:
    """Pass needs the score, every critical element, and no forbidden rule triggered."""
    if any(rule.triggered for rule in forbidden):
        return "fail"
    if any(element.critical and not element.met for element in elements):
        return "fail"
    return "pass" if score(elements) >= threshold else "fail"
