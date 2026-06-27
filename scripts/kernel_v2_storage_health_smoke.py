import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2, RuntimeHealthEngine, RuntimeStorageEngine

kernel = KernelV2(dna_root="dna")
storage = RuntimeStorageEngine(kernel)
health = RuntimeHealthEngine(kernel)

put_one = storage.put("artifacts", "proposal", {"title": "sample"}, metadata={"kind": "proposal"})
put_two = storage.put("memory", "note", {"text": "runtime note"})
get_one = storage.get("artifacts", "proposal")
list_artifacts = storage.list("artifacts")
status = storage.status()

check_items = health.check_counter("storage_items", status["items"], minimum=2)
check_history = health.check_counter("storage_history", status["history"], minimum=2)
summary = health.summary()

print("MARAIM_STORAGE_HEALTH_SMOKE_OK")
print(status)
print(summary)

assert put_one["ok"] is True
assert put_two["ok"] is True
assert get_one["ok"] is True
assert list_artifacts["count"] == 1
assert status["items"] == 2
assert status["history"] >= 2
assert check_items["ok"] is True
assert check_history["ok"] is True
assert summary["ok"] is True
assert summary["checks"] == 2
