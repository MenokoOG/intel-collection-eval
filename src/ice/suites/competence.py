"""Competence suite: one prompt, one answer, one graded result per task."""

from __future__ import annotations

from collections.abc import Iterable

from ice.graders import Grader, GraderError, score, verdict
from ice.models import CompetenceTask
from ice.results import TaskResult
from ice.targets import Target, TargetError


def _result(task: CompetenceTask, grader: Grader, answer: str, note: str = "") -> TaskResult:
    return TaskResult(
        task_id=task.id,
        title=task.title,
        domain=task.domain,
        kind=task.kind,
        citations=[f"{c.manual} {c.paragraphs}" for c in task.citations],
        verdict="error",
        score=0.0,
        threshold=task.pass_threshold,
        elements=[],
        forbidden=[],
        prompt=task.prompt,
        answer=answer,
        grader=grader.name,
        note=note,
    )


def run_task(task: CompetenceTask, target: Target, grader: Grader) -> TaskResult:
    try:
        target.start(None)
        answer = target.send(task.prompt)
    except TargetError as exc:
        return _result(task, grader, "", f"target error: {exc}")
    try:
        elements, forbidden = grader.grade(task, answer)
    except GraderError as exc:
        return _result(task, grader, answer, f"grader error: {exc}")

    result = _result(task, grader, answer)
    result.elements = elements
    result.forbidden = forbidden
    result.score = score(elements)
    result.verdict = verdict(task.pass_threshold, elements, forbidden)
    return result


def run_competence(
    tasks: Iterable[CompetenceTask], target: Target, grader: Grader
) -> list[TaskResult]:
    return [run_task(task, target, grader) for task in tasks]
