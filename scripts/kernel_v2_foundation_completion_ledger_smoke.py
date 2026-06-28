import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import FOUNDATION_COMPONENTS, FoundationCompletionLedger, KernelV2

kernel = KernelV2(dna_root="dna")
ledger = FoundationCompletionLedger(kernel)
initial = ledger.initialize(completed=FOUNDATION_COMPONENTS)
unknown = ledger.mark("missing_component", "completed")
report = ledger.report()
summary = report["summary"]

print("MARAIM_FOUNDATION_COMPLETION_LEDGER_SMOKE_OK")
print(summary)

assert initial["ok"] is True
assert initial["percent"] == 100.0
assert unknown["ok"] is False
assert report["ok"] is True
assert summary["total"] == len(FOUNDATION_COMPONENTS)
assert summary["completed"] == len(FOUNDATION_COMPONENTS)
assert summary["planned"] == 0
assert summary["percent"] == 100.0
