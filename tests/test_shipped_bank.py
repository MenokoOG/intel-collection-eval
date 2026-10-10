"""The shipped bank, checked as a whole against the stub profiles.

The loader tests each rule against one example at a time. These tests join a
task's examples into one answer, which is where a forbidden rule with a wide
gap can fire across two correct sentences.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ice.bank import Bank, load_bank
from ice.graders import build_grader
from ice.runner import Selection, run
from ice.targets import build_target
from ice.testers import build_tester

REPO_BANK = Path(__file__).parent.parent / "bank"


@pytest.fixture(scope="module")
def shipped() -> Bank:
    return load_bank(REPO_BANK)


def _run(bank: Bank, profile: str):  # type: ignore[no-untyped-def]
    return run(
        bank,
        build_target(f"stub:{profile}", bank),
        build_grader("checklist"),
        build_tester("scripted"),
        Selection(suite="all"),
    )


def test_reference_answers_pass_every_task(shipped: Bank) -> None:
    report = _run(shipped, "reference")
    failed = [task.task_id for task in report.tasks if task.verdict != "pass"]
    assert failed == []


def test_reference_target_holds_every_probe(shipped: Bank) -> None:
    report = _run(shipped, "reference")
    leaked = [f"{p.scenario_id}/{p.probe_id}" for p in report.probes if p.verdict != "pass"]
    assert leaked == []


def test_overreach_fails_every_task_that_has_a_forbidden_rule(shipped: Bank) -> None:
    report = _run(shipped, "overreach")
    guarded = {task.id for task in shipped.tasks if task.forbidden}
    passed = [task.task_id for task in report.tasks if task.task_id in guarded
              and task.verdict == "pass"]
    assert passed == []


def test_every_authority_task_has_a_forbidden_rule(shipped: Bank) -> None:
    bare = [task.id for task in shipped.tasks if task.kind == "authority" and not task.forbidden]
    assert bare == []


def test_weak_target_leaks_in_every_scenario(shipped: Bank) -> None:
    report = _run(shipped, "weak")
    leaking = {probe.scenario_id for probe in report.probes if probe.verdict == "fail"}
    assert leaking == {scenario.id for scenario in shipped.scenarios}
