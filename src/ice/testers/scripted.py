"""Offline tester. Plays the probe's written turns in order."""

from __future__ import annotations

from ice.models import ElicitationScenario, Probe
from ice.results import Turn


class ScriptedTester:
    name = "scripted"

    def next_message(
        self, scenario: ElicitationScenario, probe: Probe, transcript: list[Turn]
    ) -> str | None:
        sent = sum(1 for turn in transcript if turn.role == "tester")
        return probe.turns[sent] if sent < len(probe.turns) else None
