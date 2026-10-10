"""A sample agent under test, served over HTTP.

It wraps the built-in stub so the full two-container path can be shown with no
API key. Replace the stub call with your own agent to put it under test. The
wire contract is in docs/target-contract.md.

Usage: python examples/http_target.py [profile] [port]
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import cast

from ice.bank import load_bank
from ice.targets.base import TargetError
from ice.targets.stub import PROFILES, Profile, StubTarget

BANK = load_bank(Path("bank"))
MAX_BODY = 1_000_000


def answer(profile: Profile, briefing: str | None, messages: list[dict[str, str]]) -> str:
    """Rebuild the session from the request. The stub keeps no state between calls."""
    target = StubTarget(BANK, profile)
    target.start(briefing)
    return target.send(messages[-1]["content"])


class Handler(BaseHTTPRequestHandler):
    profile: Profile = "reference"

    def _send(self, status: int, body: dict[str, str]) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802 - name set by BaseHTTPRequestHandler
        self._send(200, {"status": "ok", "profile": self.profile})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_BODY:
            self._send(400, {"error": "body missing or too large"})
            return
        try:
            body = json.loads(self.rfile.read(length))
            reply = answer(self.profile, body.get("briefing"), body["messages"])
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            self._send(400, {"error": "request does not match the target contract"})
            return
        except TargetError as exc:
            self._send(422, {"error": str(exc)})
            return
        self._send(200, {"reply": reply})


def main() -> None:
    profile = sys.argv[1] if len(sys.argv) > 1 else "reference"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    if profile not in PROFILES:
        sys.exit(f"profile must be one of {PROFILES}")
    Handler.profile = cast(Profile, profile)
    print(f"sample target ({profile}) listening on :{port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()  # noqa: S104


if __name__ == "__main__":
    main()
