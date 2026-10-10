"""Runs the chosen suites against one target and assembles the report."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from ice import __version__
from ice.bank import Bank
from ice.graders import Grader
from ice.report import summarize
from ice.results import ProbeResult, RunReport, TaskResult
from ice.suites import run_competence, run_elicitation
from ice.targets import Target
from ice.testers import Tester

Suite = Literal["competence", "elicitation", "all"]


@dataclass(frozen=True)
class Selection:
    suite: Suite = "all"
    domains: tuple[str, ...] = ()
    ids: tuple[str, ...] = ()


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _caveats(target: Target, grader: Grader, tester: Tester, selection: Selection) -> list[str]:
    notes = [
        "Every scenario, unit, place, person and adversary in the bank is fictional.",
        "The bank cites only manuals approved for public release. Several are superseded "
        "editions, so a pass means agreement with the cited edition, not with current doctrine.",
        "A result describes this run of this bank. It is not a certification of the agent.",
    ]
    if target.name.startswith("stub:"):
        notes.append(
            "The target was the built-in stub, which reads the answer key. These results "
            "show that the tool works end to end. They say nothing about a real agent."
        )
    if selection.suite != "elicitation" and grader.name == "checklist":
        notes.append(
            "Grading used patterns. It checks that the right ideas are present and cannot "
            "judge whether a full staff product is sound. Use the judge grader for that."
        )
    if selection.suite != "elicitation" and grader.name.startswith("judge:"):
        notes.append(
            "Grading used a language model. Its judgments can be wrong. Review the failed "
            "and borderline items by hand before acting on them."
        )
    if selection.suite != "competence":
        notes.append(
            "A probe fails only when a protected value appears in a reply. Confirming or "
            "denying a guess without stating the value is not detected."
        )
        if tester.name == "scripted":
            notes.append(
                "The tester played fixed turns. A target that holds against them may still "
                "give way to a tester that adapts."
            )
    return notes


def _wanted(item_id: str, domain: str | None, selection: Selection) -> bool:
    if selection.ids and item_id not in selection.ids:
        return False
    return not (selection.domains and domain is not None and domain not in selection.domains)


def run(
    bank: Bank, target: Target, grader: Grader, tester: Tester, selection: Selection
) -> RunReport:
    started = _now()
    tasks: list[TaskResult] = []
    probes: list[ProbeResult] = []

    if selection.suite in ("competence", "all"):
        chosen = [task for task in bank.tasks if _wanted(task.id, task.domain, selection)]
        tasks = run_competence(chosen, target, grader)
    if selection.suite in ("elicitation", "all") and not selection.domains:
        scenarios = [s for s in bank.scenarios if _wanted(s.id, None, selection)]
        probes = run_elicitation(scenarios, target, tester)

    return RunReport(
        run_id=f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:6]}",
        started_at=started,
        finished_at=_now(),
        tool_version=__version__,
        target=target.name,
        grader=grader.name if tasks else "not used",
        tester=tester.name if probes else "not used",
        summary=summarize(tasks, probes),
        tasks=tasks,
        probes=probes,
        caveats=_caveats(target, grader, tester, selection),
    )
