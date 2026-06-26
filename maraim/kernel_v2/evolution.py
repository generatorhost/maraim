import time
from typing import Any, Dict, List


class EvolutionEngine:
    def __init__(self, kernel: Any):
        self.kernel = kernel
        self.experiences: List[Dict[str, Any]] = []
        self.lessons: List[Dict[str, Any]] = []

    def observe_run(self, run: Dict[str, Any]) -> Dict[str, Any]:
        experience = {
            "id": f"experience:{len(self.experiences) + 1}",
            "timestamp": time.time(),
            "processed": run.get("processed", 0),
            "queued": run.get("status", {}).get("queued", 0),
            "completed": run.get("status", {}).get("completed", 0),
            "failed": run.get("status", {}).get("failed", 0),
            "duration_ms": run.get("duration_ms", 0),
            "success": run.get("status", {}).get("failed", 0) == 0,
            "relations": [item.get("result", {}).get("task", {}).get("relation") for item in run.get("results", [])],
        }
        self.experiences.append(experience)
        lesson = self._lesson_from_experience(experience)
        self.lessons.append(lesson)
        self.kernel.memory.remember_experience(experience, lesson)
        self.kernel.emit("evolution.experience_recorded", {"experience_id": experience["id"], "success": experience["success"]})
        self.kernel.emit("evolution.lesson_created", {"lesson_id": lesson["id"], "recommendation": lesson["recommendation"]})
        return {"ok": True, "experience": experience, "lesson": lesson}

    def _lesson_from_experience(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        recommendation = "reuse_current_task_graph" if experience["success"] else "inspect_failed_runtime_objects"
        return {
            "id": f"lesson:{len(self.lessons) + 1}",
            "experience_id": experience["id"],
            "recommendation": recommendation,
            "reason": {
                "processed": experience["processed"],
                "failed": experience["failed"],
                "duration_ms": experience["duration_ms"],
            },
        }

    def status(self) -> Dict[str, Any]:
        return {
            "experiences": len(self.experiences),
            "lessons": len(self.lessons),
            "last_experience": self.experiences[-1] if self.experiences else None,
            "last_lesson": self.lessons[-1] if self.lessons else None,
        }
