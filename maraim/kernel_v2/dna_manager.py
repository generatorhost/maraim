import importlib.util
import inspect
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Type

from .runtime_graph import RuntimeGraph
from .runtime_object import RuntimeObject


class DNAManager:
    """Discovers and mounts live Python RuntimeObjects from DNA space.

    No compiler, no JSON, no YAML, no generated registry. Python runtime files
    are executable DNA objects.
    """

    def __init__(self, root: str | Path = "dna"):
        self.root = Path(root)
        self.discovered: Dict[str, RuntimeObject] = {}
        self.disabled: set[str] = set()

    def discover(self) -> List[RuntimeObject]:
        self.root.mkdir(parents=True, exist_ok=True)
        objects: List[RuntimeObject] = []
        for path in self.root.rglob("*.py"):
            if path.name.startswith("_"):
                continue
            objects.extend(self._load_runtime_objects(path))
        self._validate_no_duplicate(objects)
        self.discovered = {obj.id: obj for obj in objects}
        return objects

    def mount_all(self, kernel: Any) -> Dict[str, Any]:
        if not self.discovered:
            self.discover()
        mounted = []
        for obj in self.discovered.values():
            if obj.id in self.disabled:
                continue
            obj.discover(kernel).validate(kernel).mount(kernel).connect(kernel)
            kernel.graph.add_node(obj)
            mounted.append(obj.id)
        return {"ok": True, "mounted": mounted}

    def add_runtime(self, obj: RuntimeObject) -> RuntimeObject:
        if obj.id in self.discovered:
            raise ValueError(f"duplicate_runtime_object:{obj.id}")
        self.discovered[obj.id] = obj
        return obj

    def remove_runtime(self, object_id: str) -> bool:
        return self.discovered.pop(object_id, None) is not None

    def enable_runtime(self, object_id: str) -> bool:
        self.disabled.discard(object_id)
        return object_id in self.discovered

    def disable_runtime(self, object_id: str) -> bool:
        if object_id not in self.discovered:
            return False
        self.disabled.add(object_id)
        return True

    def reload_runtime(self, object_id: str) -> Dict[str, Any]:
        # Runtime reload is intentionally conservative in this foundation.
        # Later phases can support module reloading, hot replacement, and migration.
        if object_id not in self.discovered:
            return {"ok": False, "error": "runtime_not_found"}
        return {"ok": True, "runtime": self.discovered[object_id].status()}

    def status(self) -> Dict[str, Any]:
        return {
            "root": str(self.root),
            "discovered": len(self.discovered),
            "disabled": sorted(self.disabled),
            "objects": [obj.status() for obj in self.discovered.values()],
        }

    def _load_runtime_objects(self, path: Path) -> List[RuntimeObject]:
        module_name = "maraim_dna_" + "_".join(path.with_suffix("").parts)
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            return []
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        objects: List[RuntimeObject] = []
        for _, value in inspect.getmembers(module):
            if isinstance(value, RuntimeObject):
                objects.append(value)
            elif inspect.isclass(value) and issubclass(value, RuntimeObject) and value is not RuntimeObject:
                try:
                    objects.append(value())
                except TypeError:
                    continue
        return objects

    def _validate_no_duplicate(self, objects: Iterable[RuntimeObject]) -> None:
        seen = set()
        for obj in objects:
            if obj.id in seen:
                raise ValueError(f"duplicate_runtime_object:{obj.id}")
            seen.add(obj.id)
