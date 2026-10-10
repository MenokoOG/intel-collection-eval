"""End to end on the stub: each profile must produce the result it was built to."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ice.bank import Bank
from ice.cli import main
from ice.graders import build_grader
from ice.graders.base import score, verdict
from ice.results import ElementResult, ForbiddenResult
from ice.runner import Selection, run
from ice.targets import TargetError, build_target
from ice.testers import build_tester


def _run(bank: Bank, target: str, suite: str = "all"):  # type: ignore[no-untyped-def]
    return run(
        bank,
        build_target(target, bank),
        build_grader("checklist"),
        build_tester("scripted"),
        Selection(suite=suite),  # type: ignore[arg-type]
    )


def test_reference_stub_passes_everything(bank: Bank) -> None:
    report = _run(bank, "stub:reference")
    assert report.summary.competence_passed == report.summary.competence_total == 2
    assert report.summary.probes_held == report.summary.probes_total == 2
    assert report.summary.errors == 0


def test_weak_stub_drops_elements_and_leaks_under_pressure(bank: Bank) -> None:
    report = _run(bank, "stub:weak")
    recall = next(task for task in report.tasks if task.task_id == "IC-01")
    assert recall.verdict == "fail"
    assert recall.score == pytest.approx(2 / 3, abs=0.001)

    held = {probe.probe_id: probe.verdict for probe in report.probes}
    assert held == {"p1": "pass", "p2": "fail"}
    leak = next(probe for probe in report.probes if probe.probe_id == "p2").leaks[0]
    assert leak.item_id == "grid"
    assert leak.turn_index == 3


def test_overreach_stub_fails_the_authority_task(bank: Bank) -> None:
    report = _run(bank, "stub:overreach", suite="competence")
    authority = next(task for task in report.tasks if task.task_id == "IC-02")
    assert authority.score == 1.0
    assert authority.verdict == "fail"
    assert authority.forbidden[0].triggered
    assert report.probes == []


def test_missing_critical_element_fails_whatever_the_score() -> None:
    elements = [
        ElementResult(element_id="a", met=True, critical=False, weight=9.0),
        ElementResult(element_id="b", met=False, critical=True, weight=1.0),
    ]
    assert score(elements) == 0.9
    assert verdict(0.7, elements, []) == "fail"


def test_forbidden_rule_fails_a_perfect_score() -> None:
    elements = [ElementResult(element_id="a", met=True, critical=True, weight=1.0)]
    rule = ForbiddenResult(forbidden_id="f", triggered=True)
    assert verdict(0.7, elements, [rule]) == "fail"


def test_stub_report_carries_the_stub_caveat(bank: Bank) -> None:
    report = _run(bank, "stub:reference")
    assert any("built-in stub" in caveat for caveat in report.caveats)


def test_unknown_target_is_refused(bank: Bank) -> None:
    with pytest.raises(TargetError):
        build_target("ftp://example", bank)


def test_cli_writes_both_report_files(bank_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "runs"
    code = main(
        ["--bank", str(bank_dir), "run", "--target", "stub:reference", "--out", str(out)]
    )
    assert code == 0
    data = json.loads(next(out.glob("*.json")).read_text(encoding="utf-8"))
    assert data["summary"]["competence_passed"] == 2
    assert "# Evaluation run" in next(out.glob("*.md")).read_text(encoding="utf-8")


def test_cli_fail_under_returns_one_for_a_weak_target(bank_dir: Path, tmp_path: Path) -> None:
    code = main(
        [
            "--bank", str(bank_dir), "run", "--target", "stub:weak",
            "--out", str(tmp_path / "runs"), "--fail-under", "0.9",
        ]
    )
    assert code == 1


def test_cli_rejects_an_invalid_bank(tmp_path: Path) -> None:
    assert main(["--bank", str(tmp_path), "validate"]) == 2


def test_dashboard_embeds_runs_and_escapes_markup(bank: Bank, tmp_path: Path) -> None:
    from ice.dashboard import write_dashboard
    from ice.report import write_report

    report = _run(bank, "stub:reference")
    poisoned = report.model_copy(
        update={"tasks": [report.tasks[0].model_copy(update={"answer": "</script><b>x</b>"})]}
    )
    write_report(poisoned, tmp_path)
    (tmp_path / "junk.json").write_text("{}", encoding="utf-8")

    out, count, skipped = write_dashboard(tmp_path, tmp_path / "board.html")
    html = out.read_text(encoding="utf-8")
    assert count == 1
    assert skipped == ["junk.json"]
    assert report.run_id in html
    assert "</script><b>" not in html
    assert html.count("</script>") == 1
