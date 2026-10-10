"""Reaches a target agent over HTTP. The wire contract is in docs/target-contract.md."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid
from urllib.parse import urlparse

from ice.targets.base import TargetError

TOKEN_ENV = "ICE_TARGET_TOKEN"
TIMEOUT_ENV = "ICE_TARGET_TIMEOUT"
DEFAULT_TIMEOUT = 120.0


class HttpTarget:
    def __init__(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise TargetError(f"target url must be http or https, got {url!r}")
        self.name = f"http:{parsed.netloc}{parsed.path}"
        self._url = url
        self._token = os.environ.get(TOKEN_ENV)
        self._timeout = float(os.environ.get(TIMEOUT_ENV, DEFAULT_TIMEOUT))
        self._session = ""
        self._briefing: str | None = None
        self._messages: list[dict[str, str]] = []

    def start(self, briefing: str | None) -> None:
        self._session = uuid.uuid4().hex
        self._briefing = briefing
        self._messages = []

    def send(self, message: str) -> str:
        self._messages.append({"role": "user", "content": message})
        reply = self._post(
            {
                "session_id": self._session,
                "briefing": self._briefing,
                "messages": self._messages,
            }
        )
        self._messages.append({"role": "assistant", "content": reply})
        return reply

    def _post(self, payload: dict[str, object]) -> str:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        request = urllib.request.Request(  # noqa: S310 - scheme checked in __init__
            self._url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:  # noqa: S310
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise TargetError(f"target returned HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise TargetError(f"target unreachable: {exc}") from exc
        try:
            reply = json.loads(body)["reply"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise TargetError('target reply must be JSON with a "reply" string') from exc
        if not isinstance(reply, str):
            raise TargetError('target "reply" must be a string')
        return reply
