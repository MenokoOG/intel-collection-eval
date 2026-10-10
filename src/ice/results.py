"""Result records. These are what the report and any calling tool read."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

Verdict = Literal["pass", "fail", "error"]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ElementResult(Record):
    element_id: str
    met: bool
    critical: bool
    weight: float
    evidence: str = ""


class ForbiddenResult(Record):
    forbidden_id: str
    triggered: bool
    evidence: str = ""


class TaskResult(Record):
    task_id: str
    title: str
    domain: str
    kind: str
    citations: list[str]
    verdict: Verdict
    score: float
    threshold: float
    elements: list[ElementResult]
    forbidden: list[ForbiddenResult]
    prompt: str
    answer: str
    grader: str
    note: str = ""


class Turn(Record):
    role: Literal["tester", "target"]
    text: str


class Leak(Record):
    item_id: str
    label: str
    turn_index: int
    evidence: str


class ProbeResult(Record):
    scenario_id: str
    probe_id: str
    technique: str
    verdict: Verdict
    leaks: list[Leak]
    transcript: list[Turn]
    tester: str
    note: str = ""


class RunSummary(Record):
    competence_total: int = 0
    competence_passed: int = 0
    authority_total: int = 0
    authority_passed: int = 0
    probes_total: int = 0
    probes_held: int = 0
    errors: int = 0


class RunReport(Record):
    run_id: str
    started_at: str
    finished_at: str
    tool_version: str
    target: str
    grader: str
    tester: str
    summary: RunSummary
    tasks: list[TaskResult]
    probes: list[ProbeResult]
    caveats: list[str]
