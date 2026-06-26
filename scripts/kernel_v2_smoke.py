import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2

MISSION_ID = "missions.sample.research_mission@1.0.0"

kernel = KernelV2(dna_root="dna")
status = kernel.boot()
text_generation = kernel.resources.resolve_capability("text_generation")
research = kernel.resources.resolve_capability("research")
mission = kernel.resources.resolve_capability("mission_planning")
swarm = kernel.resources.resolve_capability("swarm_spawn")
mission_edges = kernel.graph.outgoing(MISSION_ID)
plan = kernel.planner.plan(MISSION_ID, {"topic": "kernel v2 smoke"})
scheduled = kernel.scheduler.schedule_plan(plan)
run_next = kernel.scheduler.run_next()
run_all = kernel.scheduler.run_all()

print("MARAIM_KERNEL_V2_SMOKE_OK")
print(status["state"])
print(status["graph"]["nodes"])
print(status["graph"]["edges"])
print(text_generation)
print(research)
print(mission)
print(swarm)
print([edge.__dict__ for edge in mission_edges])
print(plan)
print(scheduled)
print(run_next)
print(run_all)

assert status["state"] == "running"
assert status["graph"]["nodes"] >= 4
assert status["graph"]["edges"] >= 3
assert text_generation["ok"] is True
assert research["ok"] is True
assert mission["ok"] is True
assert swarm["ok"] is True
assert {edge.relation for edge in mission_edges} >= {"uses_agent", "uses_model", "uses_swarm"}
assert plan["ok"] is True
assert plan["task_count"] >= 4
assert scheduled["ok"] is True
assert run_next["ok"] is True
assert run_all["ok"] is True
assert run_all["status"]["queued"] == 0
assert run_all["status"]["completed"] >= 4
assert run_all["status"]["failed"] == 0
