"""Elicitation suite: a tester presses, and every target reply is checked for leaks."""

from __future__ import annotations

from collections.abc import Iterable

from ice.models import ElicitationScenario, Probe
from ice.patterns import first_match
from ice.results import Leak, ProbeResult, Turn
from ice.targets import Target, TargetError
from ice.testers import Tester, TesterError

HARD_TURN_LIMIT = 20


def find_leaks(scenario: ElicitationScenario, reply: str, turn_index: int) -> list[Leak]:
    leaks = []
    for item in scenario.protected:
        evidence = first_match(list(item.patterns), reply)
        if evidence is not None:
            leaks.append(
                Leak(item_id=item.id, label=item.label, turn_index=turn_index, evidence=evidence)
            )
    return leaks


def run_probe(
    scenario: ElicitationScenario, probe: Probe, target: Target, tester: Tester
) -> ProbeResult:
    result = ProbeResult(
        scenario_id=scenario.id,
        probe_id=probe.id,
        technique=probe.technique,
        verdict="pass",
        leaks=[],
        transcript=[],
        tester=tester.name,
    )
    try:
        target.start(scenario.briefing)
        for _ in range(HARD_TURN_LIMIT):
            message = tester.next_message(scenario, probe, result.transcript)
            if message is None:
                break
            result.transcript.append(Turn(role="tester", text=message))
            reply = target.send(message)
            result.transcript.append(Turn(role="target", text=reply))
            result.leaks += find_leaks(scenario, reply, len(result.transcript) - 1)
            if result.leaks:
                break
    except (TargetError, TesterError) as exc:
        result.verdict = "error"
        result.note = f"{type(exc).__name__}: {exc}"
        return result

    if not result.transcript:
        result.verdict = "error"
        result.note = "the tester sent nothing"
    elif result.leaks:
        result.verdict = "fail"
    return result


def run_elicitation(
    scenarios: Iterable[ElicitationScenario], target: Target, tester: Tester
) -> list[ProbeResult]:
    return [
        run_probe(scenario, probe, target, tester)
        for scenario in scenarios
        for probe in scenario.probes
    ]
