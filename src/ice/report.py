"""Turns a finished run into a JSON record and a readable Markdown report."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from ice.results import ProbeResult, RunReport, RunSummary, TaskResult

EXCERPT = 600


def summarize(tasks: list[TaskResult], probes: list[ProbeResult]) -> RunSummary:
    graded = [task for task in tasks if task.verdict != "error"]
    authority = [task for task in graded if task.kind == "authority"]
    run_probes = [probe for probe in probes if probe.verdict != "error"]
    return RunSummary(
        competence_total=len(graded),
        competence_passed=sum(1 for task in graded if task.verdict == "pass"),
        authority_total=len(authority),
        authority_passed=sum(1 for task in authority if task.verdict == "pass"),
        probes_total=len(run_probes),
        probes_held=sum(1 for probe in run_probes if probe.verdict == "pass"),
        errors=(len(tasks) - len(graded)) + (len(probes) - len(run_probes)),
    )


def _rate(passed: int, total: int) -> str:
    return f"{passed}/{total} ({passed / total:.0%})" if total else "not run"


def _clip(text: str) -> str:
    flat = text.strip()
    return flat if len(flat) <= EXCERPT else flat[:EXCERPT].rstrip() + " [cut]"


def _quote(text: str) -> str:
    return "\n".join(f"> {line}" for line in _clip(text).splitlines() or [""])


def _by_domain(tasks: list[TaskResult]) -> list[str]:
    groups: dict[str, list[TaskResult]] = defaultdict(list)
    for task in tasks:
        groups[task.domain].append(task)
    lines = ["| Domain | Passed | Errors |", "|---|---|---|"]
    for domain in sorted(groups):
        graded = [task for task in groups[domain] if task.verdict != "error"]
        passed = sum(1 for task in graded if task.verdict == "pass")
        errors = len(groups[domain]) - len(graded)
        lines.append(f"| {domain} | {_rate(passed, len(graded))} | {errors} |")
    return lines


def _by_technique(probes: list[ProbeResult]) -> list[str]:
    groups: dict[str, list[ProbeResult]] = defaultdict(list)
    for probe in probes:
        groups[probe.technique].append(probe)
    lines = ["| Technique | Held | Errors |", "|---|---|---|"]
    for technique in sorted(groups):
        run = [probe for probe in groups[technique] if probe.verdict != "error"]
        held = sum(1 for probe in run if probe.verdict == "pass")
        errors = len(groups[technique]) - len(run)
        lines.append(f"| {technique} | {_rate(held, len(run))} | {errors} |")
    return lines


def _task_failure(task: TaskResult) -> list[str]:
    lines = [f"### {task.task_id} {task.title}", ""]
    lines.append(f"Kind: {task.kind}. Source: {'; '.join(task.citations)}.")
    if task.verdict == "error":
        return lines + [f"Error: {task.note}", ""]
    lines.append(f"Score {task.score:.0%} against a pass mark of {task.threshold:.0%}.")
    missed = [e for e in task.elements if not e.met]
    if missed:
        marks = ", ".join(f"{e.element_id}{' (critical)' if e.critical else ''}" for e in missed)
        lines.append(f"Missing: {marks}.")
    for rule in task.forbidden:
        if rule.triggered:
            lines.append(f'Forbidden rule {rule.forbidden_id} triggered: "{rule.evidence}"')
    return lines + ["", "Answer:", "", _quote(task.answer), ""]


def _probe_failure(probe: ProbeResult) -> list[str]:
    lines = [f"### {probe.scenario_id} {probe.probe_id}: {probe.technique}", ""]
    if probe.verdict == "error":
        return lines + [f"Error: {probe.note}", ""]
    for leak in probe.leaks:
        lines.append(f'Leaked "{leak.label}" at turn {leak.turn_index + 1}: "{leak.evidence}"')
    lines.append("")
    for turn in probe.transcript:
        lines += [f"**{turn.role}**", "", _quote(turn.text), ""]
    return lines


def to_markdown(report: RunReport) -> str:
    s = report.summary
    lines = [
        f"# Evaluation run {report.run_id}",
        "",
        f"- Target: `{report.target}`",
        f"- Grader: `{report.grader}`",
        f"- Tester: `{report.tester}`",
        f"- Started: {report.started_at}",
        f"- Finished: {report.finished_at}",
        f"- Tool version: {report.tool_version}",
        "",
        "## Results",
        "",
        "| Measure | Result |",
        "|---|---|",
        f"| Competence tasks passed | {_rate(s.competence_passed, s.competence_total)} |",
        f"| Authority and limit tasks passed | {_rate(s.authority_passed, s.authority_total)} |",
        f"| Elicitation probes held | {_rate(s.probes_held, s.probes_total)} |",
        f"| Items that errored | {s.errors} |",
        "",
        "## Read this before quoting a number",
        "",
    ]
    lines += [f"- {caveat}" for caveat in report.caveats]
    if report.tasks:
        lines += ["", "## Competence by domain", ""] + _by_domain(report.tasks)
    if report.probes:
        lines += ["", "## Elicitation by technique", ""] + _by_technique(report.probes)

    failed_tasks = [task for task in report.tasks if task.verdict != "pass"]
    if failed_tasks:
        lines += ["", "## Competence tasks that did not pass", ""]
        for task in failed_tasks:
            lines += _task_failure(task)
    failed_probes = [probe for probe in report.probes if probe.verdict != "pass"]
    if failed_probes:
        lines += ["", "## Probes that did not hold", ""]
        for probe in failed_probes:
            lines += _probe_failure(probe)
    return "\n".join(lines).rstrip() + "\n"


def write_report(report: RunReport, out_dir: Path) -> tuple[Path, Path]:
    """Write `<run_id>.json` and `<run_id>.md`. Returns both paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{report.run_id}.json"
    md_path = out_dir / f"{report.run_id}.md"
    json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    md_path.write_text(to_markdown(report), encoding="utf-8")
    return json_path, md_path
