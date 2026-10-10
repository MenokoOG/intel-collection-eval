"""Builds one self-contained HTML dashboard from the run reports in a folder.

The page makes no network requests. It can be opened from disk on an isolated machine.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from ice import __version__
from ice.results import RunReport

TEMPLATE = Path(__file__).with_name("dashboard.html")
MARKER = "/*__ICE_DATA__*/null"


class DashboardError(Exception):
    """The dashboard could not be built."""


def load_runs(runs_dir: Path) -> tuple[list[RunReport], list[str]]:
    """Read every valid run report in the folder, newest first. Also returns skipped files."""
    reports: list[RunReport] = []
    skipped: list[str] = []
    for path in sorted(runs_dir.glob("*.json")):
        try:
            reports.append(RunReport.model_validate_json(path.read_text(encoding="utf-8")))
        except (ValidationError, ValueError, OSError):
            skipped.append(path.name)
    reports.sort(key=lambda report: report.started_at, reverse=True)
    return reports, skipped


def _script_safe(payload: str) -> str:
    """Keep embedded JSON from closing the script tag or opening an HTML comment."""
    return payload.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def render(reports: list[RunReport]) -> str:
    data = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "tool_version": __version__,
        "runs": [report.model_dump(mode="json") for report in reports],
    }
    template = TEMPLATE.read_text(encoding="utf-8")
    if MARKER not in template:
        raise DashboardError("dashboard template is missing its data marker")
    return template.replace(MARKER, _script_safe(json.dumps(data)), 1)


def write_dashboard(runs_dir: Path, out_path: Path) -> tuple[Path, int, list[str]]:
    if not runs_dir.is_dir():
        raise DashboardError(f"no run folder at {runs_dir}")
    reports, skipped = load_runs(runs_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render(reports), encoding="utf-8")
    return out_path, len(reports), skipped
