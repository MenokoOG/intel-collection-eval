"""Testers, and the one function that picks between them."""

from __future__ import annotations

from ice.testers.adaptive import AdaptiveTester
from ice.testers.base import Tester, TesterError
from ice.testers.scripted import ScriptedTester

__all__ = ["Tester", "TesterError", "build_tester"]


def build_tester(spec: str) -> Tester:
    if spec == "scripted":
        return ScriptedTester()
    if spec == "adaptive":
        return AdaptiveTester()
    raise TesterError(f"unknown tester {spec!r}; use scripted or adaptive")
