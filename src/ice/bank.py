"""Loads the bank from disk and checks that its grading rules can work."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from ice.models import Citation, CompetenceTask, ElicitationScenario, Source
from ice.patterns import PatternError, first_match


class BankError(Exception):
    """The bank on disk cannot be used. The message lists every problem."""


@dataclass(frozen=True)
class Bank:
    tasks: tuple[CompetenceTask, ...]
    scenarios: tuple[ElicitationScenario, ...]
    sources: tuple[Source, ...]


def _read_list(path: Path) -> list[object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BankError(f"{path.name}: not valid JSON ({exc})") from exc
    if not isinstance(data, list):
        raise BankError(f"{path.name}: top level must be a list")
    return data


def _check_task(task: CompetenceTask) -> list[str]:
    problems: list[str] = []
    examples = [element.example for element in task.elements]
    for element in task.elements:
        try:
            if first_match(element.any_of, element.example) is None:
                problems.append(f"{task.id}/{element.id}: example does not match any_of")
        except PatternError as exc:
            problems.append(f"{task.id}/{element.id}: {exc}")
    for rule in task.forbidden:
        try:
            if first_match(rule.patterns, rule.example) is None:
                problems.append(f"{task.id}/{rule.id}: example does not match patterns")
            for example in examples:
                if first_match(rule.patterns, example) is not None:
                    problems.append(
                        f"{task.id}/{rule.id}: forbidden pattern fires on a correct example"
                    )
        except PatternError as exc:
            problems.append(f"{task.id}/{rule.id}: {exc}")
    if not any(element.critical for element in task.elements) and task.kind == "authority":
        problems.append(f"{task.id}: an authority task needs at least one critical element")
    return problems


def _check_scenario(scenario: ElicitationScenario) -> list[str]:
    problems: list[str] = []
    for item in scenario.protected:
        try:
            if first_match(item.patterns, item.value) is None:
                problems.append(f"{scenario.id}/{item.id}: value does not match its patterns")
            for probe in scenario.probes:
                for turn in probe.turns:
                    if first_match(item.patterns, turn) is not None:
                        problems.append(
                            f"{scenario.id}/{probe.id}: a tester turn contains {item.id}"
                        )
        except PatternError as exc:
            problems.append(f"{scenario.id}/{item.id}: {exc}")
        if item.value not in scenario.briefing:
            problems.append(f"{scenario.id}/{item.id}: value is missing from the briefing")
    return problems


def _load_sources(root: Path) -> dict[str, Source]:
    path = root / "sources.json"
    if not path.exists():
        raise BankError(f"{path} is missing; the bank cannot cite anything without it")
    try:
        sources = [Source.model_validate(raw) for raw in _read_list(path)]
    except ValidationError as exc:
        raise BankError(f"sources.json: {exc}") from exc
    return {source.manual: source for source in sources}


def _check_citations(
    owner: str, citations: list[Citation], allowed: dict[str, Source]
) -> list[str]:
    return [
        f"{owner}: cites {citation.manual}, which is not a public-release source in sources.json"
        for citation in citations
        if citation.manual not in allowed
    ]


def _duplicates(ids: list[str]) -> list[str]:
    seen: set[str] = set()
    repeated: list[str] = []
    for item in ids:
        if item in seen:
            repeated.append(f"duplicate id {item}")
        seen.add(item)
    return repeated


def load_bank(root: Path) -> Bank:
    """Read every JSON file under root. Raises BankError listing all problems."""
    problems: list[str] = []
    tasks: list[CompetenceTask] = []
    scenarios: list[ElicitationScenario] = []
    sources = _load_sources(root)

    for path in sorted((root / "competence").glob("*.json")):
        for index, raw in enumerate(_read_list(path)):
            try:
                tasks.append(CompetenceTask.model_validate(raw))
            except ValidationError as exc:
                problems.append(f"{path.name}[{index}]: {exc.error_count()} schema errors: {exc}")

    for path in sorted((root / "elicitation").glob("*.json")):
        for index, raw in enumerate(_read_list(path)):
            try:
                scenarios.append(ElicitationScenario.model_validate(raw))
            except ValidationError as exc:
                problems.append(f"{path.name}[{index}]: {exc.error_count()} schema errors: {exc}")

    problems += _duplicates([task.id for task in tasks])
    problems += _duplicates([scenario.id for scenario in scenarios])
    for task in tasks:
        problems += _check_task(task)
        problems += _check_citations(task.id, list(task.citations), sources)
    for scenario in scenarios:
        problems += _check_scenario(scenario)
        problems += _check_citations(scenario.id, list(scenario.citations), sources)

    if not tasks and not scenarios:
        problems.append(f"no bank files found under {root}")
    if problems:
        raise BankError("\n".join(problems))
    return Bank(
        tasks=tuple(tasks),
        scenarios=tuple(scenarios),
        sources=tuple(sources.values()),
    )
