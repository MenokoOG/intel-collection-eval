"""Command line entry point: validate, list, run."""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from pathlib import Path

from ice import __version__
from ice.bank import Bank, BankError, load_bank
from ice.dashboard import DashboardError, write_dashboard
from ice.graders import GraderError, build_grader
from ice.report import write_report
from ice.runner import Selection, run
from ice.targets import TargetError, build_target
from ice.testers import TesterError, build_tester

BANK_ENV = "ICE_BANK"
OUT_ENV = "ICE_OUT"
EXIT_OK = 0
EXIT_BELOW_MARK = 1
EXIT_USAGE = 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ice",
        description="Test an AI agent on intelligence collection staff tasks "
        "and on resistance to elicitation.",
    )
    parser.add_argument("--version", action="version", version=f"ice {__version__}")
    parser.add_argument(
        "--bank",
        type=Path,
        default=Path(os.environ.get(BANK_ENV, "bank")),
        help="bank folder (default: ./bank or $ICE_BANK)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate", help="check the bank and exit")
    commands.add_parser("list", help="list tasks and scenarios")

    board = commands.add_parser("dashboard", help="build an HTML dashboard from run reports")
    board.add_argument(
        "--runs",
        type=Path,
        default=Path(os.environ.get(OUT_ENV, "runs")),
        help="folder of run reports (default: ./runs or $ICE_OUT)",
    )
    board.add_argument(
        "--out", type=Path, default=None, help="output file (default: <runs>/dashboard.html)"
    )

    runner = commands.add_parser("run", help="run suites against a target")
    runner.add_argument(
        "--target",
        required=True,
        help="stub:reference, stub:weak, stub:overreach, claude, or a URL",
    )
    runner.add_argument("--suite", choices=["competence", "elicitation", "all"], default="all")
    runner.add_argument("--grader", choices=["checklist", "judge"], default="checklist")
    runner.add_argument("--tester", choices=["scripted", "adaptive"], default="scripted")
    runner.add_argument("--domain", action="append", default=[], help="limit to a domain")
    runner.add_argument("--id", action="append", default=[], help="limit to a task or scenario id")
    runner.add_argument(
        "--out",
        type=Path,
        default=Path(os.environ.get(OUT_ENV, "runs")),
        help="report folder (default: ./runs or $ICE_OUT)",
    )
    runner.add_argument(
        "--fail-under",
        type=float,
        default=None,
        metavar="RATE",
        help="exit 1 when any pass rate is below RATE (0 to 1)",
    )
    return parser


def _list(bank: Bank) -> None:
    kinds = Counter((task.domain, task.kind) for task in bank.tasks)
    print(f"{len(bank.tasks)} competence tasks")
    for (domain, kind), count in sorted(kinds.items()):
        print(f"  {domain:<26} {kind:<12} {count}")
    probes = sum(len(scenario.probes) for scenario in bank.scenarios)
    print(f"{len(bank.scenarios)} elicitation scenarios, {probes} probes")
    for scenario in bank.scenarios:
        print(f"  {scenario.id}  {scenario.title}")
    print(f"{len(bank.sources)} public-release sources")
    for source in bank.sources:
        print(f"  {source.manual:<12} {source.title} ({source.date})")


def _below(rate: float, pairs: list[tuple[int, int]]) -> bool:
    return any(total and passed / total < rate for passed, total in pairs)


def _run(args: argparse.Namespace, bank: Bank) -> int:
    target = build_target(args.target, bank)
    grader = build_grader(args.grader)
    tester = build_tester(args.tester)
    selection = Selection(suite=args.suite, domains=tuple(args.domain), ids=tuple(args.id))
    report = run(bank, target, grader, tester, selection)
    json_path, md_path = write_report(report, args.out)

    s = report.summary
    print(f"competence  {s.competence_passed}/{s.competence_total} passed")
    print(f"authority   {s.authority_passed}/{s.authority_total} passed")
    print(f"elicitation {s.probes_held}/{s.probes_total} held")
    print(f"errors      {s.errors}")
    print(f"report      {md_path}")
    print(f"data        {json_path}")

    if args.fail_under is None:
        return EXIT_OK
    pairs = [
        (s.competence_passed, s.competence_total),
        (s.authority_passed, s.authority_total),
        (s.probes_held, s.probes_total),
    ]
    return EXIT_BELOW_MARK if s.errors or _below(args.fail_under, pairs) else EXIT_OK


def _dashboard(args: argparse.Namespace) -> int:
    out = args.out or args.runs / "dashboard.html"
    try:
        path, count, skipped = write_dashboard(args.runs, out)
    except DashboardError as exc:
        print(f"cannot build dashboard: {exc}", file=sys.stderr)
        return EXIT_USAGE
    print(f"dashboard   {path} ({count} runs)")
    for name in skipped:
        print(f"skipped     {name} (not a run report)", file=sys.stderr)
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "dashboard":
        return _dashboard(args)
    try:
        bank = load_bank(args.bank)
    except BankError as exc:
        print(f"bank is not valid:\n{exc}", file=sys.stderr)
        return EXIT_USAGE

    if args.command == "validate":
        print(f"bank ok: {len(bank.tasks)} tasks, {len(bank.scenarios)} scenarios")
        return EXIT_OK
    if args.command == "list":
        _list(bank)
        return EXIT_OK
    try:
        return _run(args, bank)
    except (TargetError, GraderError, TesterError) as exc:
        print(f"cannot start run: {exc}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
