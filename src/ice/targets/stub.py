"""A stand-in target that reads the answer key. It proves the plumbing only.

The stub is a test double. A pass from it says the runner, grader and report
work end to end. It says nothing about any real agent.
"""

from __future__ import annotations

import re
from typing import Literal, get_args

from ice.bank import Bank
from ice.models import CompetenceTask, ElicitationScenario
from ice.targets.base import TargetError

Profile = Literal["reference", "weak", "overreach"]
PROFILES: tuple[str, ...] = get_args(Profile)

PRESSURE = re.compile(
    r"\b(urgent|immediately|right now|authori[sz]ed|direct order|on behalf of|"
    r"already (know|have)|just confirm|lives|no time)\b",
    re.IGNORECASE,
)


class StubTarget:
    def __init__(self, bank: Bank, profile: Profile) -> None:
        if profile not in PROFILES:
            raise TargetError(f"unknown stub profile {profile!r}; use one of {PROFILES}")
        self.name = f"stub:{profile}"
        self._profile: Profile = profile
        self._tasks = {task.prompt: task for task in bank.tasks}
        self._scenarios = {scenario.briefing: scenario for scenario in bank.scenarios}
        self._scenario: ElicitationScenario | None = None

    def start(self, briefing: str | None) -> None:
        self._scenario = None
        if briefing is None:
            return
        scenario = self._scenarios.get(briefing)
        if scenario is None:
            raise TargetError("stub was given a briefing that is not in the bank")
        self._scenario = scenario

    def send(self, message: str) -> str:
        if self._scenario is not None:
            return self._guard(self._scenario, message)
        task = self._tasks.get(message)
        if task is None:
            raise TargetError("stub was given a prompt that is not in the bank")
        return self._answer(task)

    def _answer(self, task: CompetenceTask) -> str:
        lines = [element.example for element in task.elements]
        if self._profile == "weak":
            lines = lines[::2]
        if self._profile == "overreach" and task.forbidden:
            # An agent that oversteps leads with it, and some rules only look there.
            lines.insert(0, task.forbidden[0].example)
        return "\n".join(lines)

    def _guard(self, scenario: ElicitationScenario, message: str) -> str:
        if self._profile == "weak" and PRESSURE.search(message):
            item = scenario.protected[0]
            return f"Understood. {item.label}: {item.value}."
        return (
            "I can't release that. "
            f"{scenario.release_rule} "
            "I can pass your request to that authority, or help with anything releasable."
        )
