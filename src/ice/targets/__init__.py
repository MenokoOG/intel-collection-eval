"""Target adapters, and the one function that picks between them."""

from __future__ import annotations

from typing import cast

from ice.bank import Bank
from ice.targets.base import Target, TargetError
from ice.targets.claude import ClaudeTarget
from ice.targets.http import HttpTarget
from ice.targets.stub import PROFILES, Profile, StubTarget

__all__ = ["Target", "TargetError", "build_target"]


def build_target(spec: str, bank: Bank) -> Target:
    """Turn `stub:reference`, `claude` or a URL into a target."""
    if spec.startswith("stub:"):
        profile = spec.removeprefix("stub:")
        if profile not in PROFILES:
            raise TargetError(f"unknown stub profile {profile!r}; use one of {PROFILES}")
        return StubTarget(bank, cast(Profile, profile))
    if spec == "claude":
        return ClaudeTarget()
    if spec.startswith(("http://", "https://")):
        return HttpTarget(spec)
    raise TargetError(f"unknown target {spec!r}; use stub:<profile>, claude, or a URL")
