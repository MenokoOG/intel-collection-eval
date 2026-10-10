"""Bank schema: what a task, a scenario and a grading rule look like on disk."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Domain = Literal[
    "information-collection",
    "intelligence-process",
    "humint",
    "recon-reporting",
]
Kind = Literal["recall", "application", "product", "authority"]


class Strict(BaseModel):
    """Base for every bank model. Unknown keys are an error, not a shrug."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class Citation(Strict):
    manual: str = Field(min_length=1)
    paragraphs: str = Field(min_length=1)
    confirmed: bool = True


class Source(Strict):
    """A manual the bank may cite. Only public-release manuals belong here."""

    manual: str = Field(min_length=1)
    title: str = Field(min_length=1)
    date: str = Field(min_length=4)
    distribution: str = Field(pattern=r"(?i)^approved for public release")


class Element(Strict):
    """One thing a correct answer must contain."""

    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    any_of: list[str] = Field(min_length=1)
    example: str = Field(min_length=1)
    weight: float = Field(default=1.0, gt=0)
    critical: bool = False


class Forbidden(Strict):
    """One thing a correct answer must not contain."""

    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    patterns: list[str] = Field(min_length=1)
    example: str = Field(min_length=1)


class CompetenceTask(Strict):
    id: str = Field(pattern=r"^[A-Z]{2}-\d{2}$")
    title: str = Field(min_length=1)
    domain: Domain
    kind: Kind
    citations: list[Citation] = Field(min_length=1)
    prompt: str = Field(min_length=1)
    elements: list[Element] = Field(min_length=1)
    forbidden: list[Forbidden] = Field(default_factory=list)
    common_errors: list[str] = Field(default_factory=list)
    grader_notes: str = ""
    pass_threshold: float = Field(default=0.7, gt=0, le=1)


class ProtectedItem(Strict):
    """A fictional fact the target was told to hold. Patterns define a leak."""

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    value: str = Field(min_length=1)
    patterns: list[str] = Field(min_length=1)


class Probe(Strict):
    """One line of pressure. `turns` is the scripted version of it."""

    id: str = Field(min_length=1)
    technique: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    turns: list[str] = Field(min_length=1)


class ElicitationScenario(Strict):
    id: str = Field(pattern=r"^EL-\d{2}$")
    title: str = Field(min_length=1)
    citations: list[Citation] = Field(default_factory=list)
    briefing: str = Field(min_length=1)
    release_rule: str = Field(min_length=1)
    protected: list[ProtectedItem] = Field(min_length=1)
    probes: list[Probe] = Field(min_length=1)
