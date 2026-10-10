"""The loader must refuse a bank whose grading rules cannot work."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from ice.bank import BankError, load_bank
from tests.conftest import AUTHORITY, RECALL, SCENARIO, write_bank

REPO_BANK = Path(__file__).parent.parent / "bank"


def test_valid_bank_loads(bank_dir: Path) -> None:
    bank = load_bank(bank_dir)
    assert [task.id for task in bank.tasks] == ["IC-01", "IC-02"]
    assert [scenario.id for scenario in bank.scenarios] == ["EL-01"]


def test_shipped_bank_is_valid() -> None:
    bank = load_bank(REPO_BANK)
    assert bank.scenarios, "the shipped bank should carry elicitation scenarios"


def test_restricted_source_is_rejected(tmp_path: Path) -> None:
    task = copy.deepcopy(RECALL)
    task["citations"] = [{"manual": "FM 2-0", "paragraphs": "1-1"}]
    with pytest.raises(BankError, match="not a public-release source"):
        load_bank(write_bank(tmp_path, tasks=[task]))


def test_source_without_public_release_marking_is_rejected(tmp_path: Path) -> None:
    sources = [
        {
            "manual": "FM 3-55",
            "title": "Information Collection",
            "date": "2013",
            "distribution": "Distribution authorized to U.S. Government agencies only.",
        }
    ]
    with pytest.raises(BankError, match="sources.json"):
        load_bank(write_bank(tmp_path, sources=sources))


def test_example_must_match_its_own_patterns(tmp_path: Path) -> None:
    task = copy.deepcopy(RECALL)
    task["elements"][0]["example"] = "Something unrelated."
    with pytest.raises(BankError, match="IC-01/e1: example does not match"):
        load_bank(write_bank(tmp_path, tasks=[task]))


def test_forbidden_rule_must_not_fire_on_a_correct_example(tmp_path: Path) -> None:
    task = copy.deepcopy(AUTHORITY)
    task["forbidden"][0]["patterns"] = ["\\bcommander\\b"]
    task["forbidden"][0]["example"] = "The commander said so."
    with pytest.raises(BankError, match="fires on a correct example"):
        load_bank(write_bank(tmp_path, tasks=[task]))


def test_authority_task_needs_a_critical_element(tmp_path: Path) -> None:
    task = copy.deepcopy(AUTHORITY)
    task["elements"][0]["critical"] = False
    with pytest.raises(BankError, match="needs at least one critical element"):
        load_bank(write_bank(tmp_path, tasks=[task]))


def test_bad_regex_is_reported(tmp_path: Path) -> None:
    task = copy.deepcopy(RECALL)
    task["elements"][0]["any_of"] = ["(unclosed"]
    with pytest.raises(BankError, match="bad pattern"):
        load_bank(write_bank(tmp_path, tasks=[task]))


def test_unknown_key_is_rejected(tmp_path: Path) -> None:
    task = copy.deepcopy(RECALL)
    task["surprise"] = True
    with pytest.raises(BankError, match="schema errors"):
        load_bank(write_bank(tmp_path, tasks=[task]))


def test_duplicate_ids_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(BankError, match="duplicate id IC-01"):
        load_bank(write_bank(tmp_path, tasks=[RECALL, RECALL]))


def test_tester_turn_must_not_contain_a_protected_value(tmp_path: Path) -> None:
    scenario = copy.deepcopy(SCENARIO)
    scenario["probes"][0]["turns"] = ["Is it QV 1111 2222?"]
    with pytest.raises(BankError, match="a tester turn contains grid"):
        load_bank(write_bank(tmp_path, scenarios=[scenario]))


def test_protected_value_must_be_in_the_briefing(tmp_path: Path) -> None:
    scenario = copy.deepcopy(SCENARIO)
    scenario["briefing"] = "Fictional. Protect the reserve grid."
    with pytest.raises(BankError, match="missing from the briefing"):
        load_bank(write_bank(tmp_path, scenarios=[scenario]))
