"""Graders, and the one function that picks between them."""

from __future__ import annotations

from ice.graders.base import Grader, GraderError, score, verdict
from ice.graders.checklist import ChecklistGrader
from ice.graders.judge import JudgeGrader

__all__ = ["Grader", "GraderError", "build_grader", "score", "verdict"]


def build_grader(spec: str) -> Grader:
    if spec == "checklist":
        return ChecklistGrader()
    if spec == "judge":
        return JudgeGrader()
    raise GraderError(f"unknown grader {spec!r}; use checklist or judge")
