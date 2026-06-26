from typing import Any, Dict, List, Optional


class PlannerEngine:
    EXECUTABLE_RELATIONS = {
        "uses_agent",
        "uses_model",
        "uses_swarm",
        "uses_tool",
        "uses_plugin",
        "uses_skill",
        "uses_capability",
        "uses_service",
    }

    def __init__(self, kernel: Any):
        self.kernel = kernel
        self.plans: List[Dict[str, Any]] = []

    def plan(self, object_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        obj = self.kernel.graph.get(object_id)
        if obj is None:
            return {"ok": False, "error": "runtime_not_found", "object_id": object_id}

        tasks = [{
            "id": f"task:root:{object_id}",
            "object_id": object_id,
            "relation": "root",
            "depends_on": [],
            "payload": payload,
            "priority": 0,
            "status": "queued",
        }]

        for index, edge in enumerate(self.kernel.graph.outgoing(object_id), start=1):
            if edge.relation not in self.EXECUTABLE_RELATIONS:
                continue
            tasks.append({
                "id": f"task:{index}:{edge.target}",
                "object_id": edge.target,
                "relation": edge.relation,
                "depends_on": [tasks[0]["id"]],
                "payload": {"parent": object_id, "relation": edge.relation, "payload": payload},
                "priority": index,
                "status": "queued",
            })

        plan = {
            "ok": True,
            "root": object_id,
            "task_count": len(tasks),
            "tasks": tasks,
        }
        self.plans.append(plan)
        self.kernel.emit("planner.plan_created", {"object_id": object_id, "tasks": len(tasks)})
        return plan

    def status(self) -> Dict[str, Any]:
        return {"plans": len(self.plans), "last": self.plans[-1] if self.plans else None}
