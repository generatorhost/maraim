import time
from typing import Any, Dict, Iterable, List


REAL_ENGINE_STAGES = [
    "git_adapter_clone",
    "git_adapter_pull",
    "git_adapter_checkout",
    "archive_adapter_zip",
    "archive_adapter_tar",
    "folder_adapter_snapshot",
    "folder_adapter_diff",
    "workspace_manager",
    "sandbox_process_limits",
    "sandbox_permission_enforcement",
    "model_manager_gguf",
    "model_manager_onnx",
    "model_manager_safetensors",
    "provider_runtime_openai",
    "provider_runtime_local",
    "plugin_loader",
    "connector_runtime_http",
    "connector_runtime_filesystem",
    "swarm_scheduler",
    "swarm_task_queue",
]


class RealEnginesRoadmap:
    """Mandatory roadmap for the next twenty real engine stages."""

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.items: Dict[str, Dict[str, Any]] = {}

    def initialize(self) -> Dict[str, Any]:
        for stage in REAL_ENGINE_STAGES:
            self.items[stage] = {"stage": stage, "status": "planned", "created_at": time.time()}
        return self.summary()

    def mark(self, stage: str, status: str = "planned") -> Dict[str, Any]:
        if stage not in self.items:
            return {"ok": False, "error": "stage_not_found", "stage": stage}
        self.items[stage]["status"] = status
        self.items[stage]["updated_at"] = time.time()
        if self.kernel is not None and hasattr(self.kernel, "emit"):
            self.kernel.emit("real_engines_roadmap.marked", self.items[stage])
        return {"ok": True, "item": self.items[stage]}

    def require_outputs(self, outputs: Dict[str, Iterable[str]]) -> Dict[str, Any]:
        missing = []
        for stage in REAL_ENGINE_STAGES:
            values = list(outputs.get(stage, []))
            if not values:
                missing.append(stage)
            elif stage in self.items:
                self.items[stage]["required_outputs"] = values
        return {"ok": not missing, "missing": missing, "summary": self.summary()}

    def summary(self) -> Dict[str, Any]:
        total = len(REAL_ENGINE_STAGES)
        initialized = len(self.items)
        with_outputs = len([item for item in self.items.values() if item.get("required_outputs")])
        return {"ok": initialized == total, "total": total, "initialized": initialized, "with_outputs": with_outputs}

    def report(self) -> Dict[str, Any]:
        return {"ok": True, "summary": self.summary(), "stages": list(self.items.values())}
