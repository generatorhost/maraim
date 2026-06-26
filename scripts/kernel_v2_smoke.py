import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import KernelV2, RuntimeLifecycleManager

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
evolution_status = kernel.evolution.status()
memory_status = kernel.memory.status()
event_bus_status = kernel.event_bus.status()
episodic = kernel.memory.recall("episodic")
procedural = kernel.memory.recall("procedural")
dna_memory = kernel.memory.recall("dna")
working = kernel.memory.recall("working")
semantic = kernel.memory.recall("semantic")
collective = kernel.memory.recall("collective")
lifecycle = RuntimeLifecycleManager(kernel)
lifecycle_register = lifecycle.register_graph()
lifecycle_busy = lifecycle.transition(MISSION_ID, "busy", reason="smoke_execution")
lifecycle_heartbeat = lifecycle.heartbeat(MISSION_ID, latency_ms=1, load=1, queue=0)
lifecycle_idle = lifecycle.transition(MISSION_ID, "idle", reason="smoke_completed")
lifecycle_status = lifecycle.status()

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
print(evolution_status)
print(memory_status)
print(event_bus_status)
print(episodic)
print(procedural)
print(dna_memory)
print(working)
print(semantic)
print(collective)
print(lifecycle_register)
print(lifecycle_busy)
print(lifecycle_heartbeat)
print(lifecycle_idle)
print(lifecycle_status)

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
assert evolution_status["experiences"] >= 1
assert evolution_status["lessons"] >= 1
assert evolution_status["last_lesson"]["recommendation"] == "reuse_current_task_graph"
assert memory_status["episodic"] >= 1
assert memory_status["procedural"] >= 1
assert memory_status["dna"] >= 1
assert memory_status["working"] >= 1
assert memory_status["semantic"] >= 1
assert memory_status["collective"] >= 1
assert event_bus_status["events"] >= 1
assert event_bus_status["subscribers"] >= 3
assert event_bus_status["deliveries"] >= 3
assert event_bus_status["errors"] == 0
assert episodic["ok"] is True
assert procedural["ok"] is True
assert dna_memory["ok"] is True
assert working["ok"] is True
assert semantic["ok"] is True
assert collective["ok"] is True
assert lifecycle_register["ok"] is True
assert lifecycle_register["count"] >= 4
assert lifecycle_busy["ok"] is True
assert lifecycle_heartbeat["ok"] is True
assert lifecycle_idle["ok"] is True
assert lifecycle_status["runtimes"] >= 4
assert lifecycle_status["healthy"] >= 4
assert lifecycle_status["transitions"] >= 2
