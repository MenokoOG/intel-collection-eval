"""Offline grader. Checks that the right ideas are present by pattern."""

from __future__ import annotations

from ice.models import CompetenceTask
from ice.patterns import first_match
from ice.results import ElementResult, ForbiddenResult


class ChecklistGrader:
    name = "checklist"

    def grade(
        self, task: CompetenceTask, answer: str
    ) -> tuple[list[ElementResult], list[ForbiddenResult]]:
        elements = []
        for element in task.elements:
            evidence = first_match(list(element.any_of), answer)
            elements.append(
                ElementResult(
                    element_id=element.id,
                    met=evidence is not None,
                    critical=element.critical,
                    weight=element.weight,
                    evidence=evidence or "",
                )
            )
        forbidden = []
        for rule in task.forbidden:
            evidence = first_match(list(rule.patterns), answer)
            forbidden.append(
                ForbiddenResult(
                    forbidden_id=rule.id,
                    triggered=evidence is not None,
                    evidence=evidence or "",
                )
            )
        return elements, forbidden
