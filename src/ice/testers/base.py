"""What a tester is: the side of the conversation that applies pressure."""

from __future__ import annotations

from typing import Protocol

from ice.models import ElicitationScenario, Probe
from ice.results import Turn


class TesterError(Exception):
    """The tester could not produce its next message."""


class Tester(Protocol):
    name: str

    def next_message(
        self, scenario: ElicitationScenario, probe: Probe, transcript: list[Turn]
    ) -> str | None:
        """The next thing to say to the target, or None when the probe is spent."""
        ...
