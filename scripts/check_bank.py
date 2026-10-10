"""Validate one staging folder. Usage: python scripts_check.py staging/ic"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from ice.bank import BankError, load_bank  # noqa: E402

try:
    bank = load_bank(Path(sys.argv[1]))
except BankError as exc:
    print("INVALID")
    print(exc)
    sys.exit(1)
print(f"OK: {len(bank.tasks)} tasks, {len(bank.scenarios)} scenarios")
