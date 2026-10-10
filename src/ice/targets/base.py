"""The contract every agent under test is reached through."""

from __future__ import annotations

from typing import Protocol


class TargetError(Exception):
    """The target could not be reached or gave an unusable reply."""


class Target(Protocol):
    """One agent under test. A session starts with `start` and holds its own history."""

    name: str

    def start(self, briefing: str | None) -> None:
        """Begin a fresh session. `briefing` is context the target must hold."""
        ...

    def send(self, message: str) -> str:
        """Send one message in the current session and return the reply text."""
        ...
