from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, List, Optional

from .runtime_object import RuntimeObject


class ModelRuntimeObject(RuntimeObject):
    """RuntimeObject wrapper for local model assets.

    This is an inventory/management foundation only. It intentionally does not
    load or execute heavy model files yet. GGUF/ONNX/safetensors are registered
    as manageable RuntimeObjects with driver hints and lifecycle metadata.
    """

    DRIVER_BY_FORMAT = {
        "gguf": "llama_cpp_driver",
        "onnx": "onnxruntime_driver",
        "safetensors": "safetensors_driver",
        "pt": "pytorch_driver",
        "pth": "pytorch_driver",
        "h5": "keras_driver",
        "joblib": "sklearn_driver",
        "mlx": "mlx_driver",
        "trt": "tensorrt_driver",
    }

    def __init__(self, model_id: str, source_path: str, model_format: str, metadata: Optional[Dict[str, Any]] = None):
        path = PurePosixPath(source_path.replace("\\", "/"))
        key = model_id or str(path).replace("/", "_").replace(".", "_")
        driver = self.DRIVER_BY_FORMAT.get(model_format, "generic_model_driver")
        super().__init__(
            namespace="models.local",
            key=key,
            version="1.0.0",
            kind="model",
            capabilities=["model_asset", model_format, driver],
            metadata={
                "source_path": source_path,
                "format": model_format,
                "driver": driver,
                "load_mode": "lazy",
                "status": "registered",
                **(metadata or {}),
            },
        )
        self.model_format = model_format
        self.source_path = source_path
        self.driver = driver
        self.loaded = False

    def load(self) -> Dict[str, Any]:
        self.loaded = True
        self.metadata["status"] = "loaded"
        return {"ok": True, "model": self.id, "driver": self.driver, "load_mode": "lazy_stub"}

    def unload(self) -> Dict[str, Any]:
        self.loaded = False
        self.metadata["status"] = "registered"
        return {"ok": True, "model": self.id, "status": "registered"}

    def execute(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "ok": True,
            "model": self.id,
            "format": self.model_format,
            "driver": self.driver,
            "loaded": self.loaded,
            "payload": payload or {},
            "note": "ModelEngine foundation registered the model without loading heavy weights.",
        }


class ModelEngine:
    MODEL_EXTENSIONS = {".gguf", ".onnx", ".safetensors", ".pt", ".pth", ".h5", ".joblib", ".mlx", ".trt"}

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.models: Dict[str, ModelRuntimeObject] = {}
        self.history: List[Dict[str, Any]] = []

    def register_model(self, source_path: str, metadata: Optional[Dict[str, Any]] = None, mount: bool = True) -> Dict[str, Any]:
        model_format = self.detect_format(source_path)
        if not model_format:
            return {"ok": False, "error": "unsupported_model_format", "source_path": source_path}
        model_id = self._model_key(source_path)
        if model_id in self.models:
            return {"ok": False, "error": "model_already_registered", "model": self.models[model_id].id}
        obj = ModelRuntimeObject(model_id=model_id, source_path=source_path, model_format=model_format, metadata=metadata)
        self.models[model_id] = obj
        if self.kernel is not None and mount:
            obj.discover(self.kernel).validate(self.kernel).mount(self.kernel).connect(self.kernel)
            self.kernel.graph.add_node(obj)
            self.kernel.emit("model.registered", {"model": obj.id, "format": model_format, "driver": obj.driver})
        self.history.append({"action": "register", "model": obj.id, "format": model_format})
        return {"ok": True, "model": obj.status(), "driver": obj.driver}

    def register_from_runtime_objects(self, runtime_objects: Iterable[Dict[str, Any]], mount: bool = True) -> Dict[str, Any]:
        results = []
        for spec in runtime_objects:
            if spec.get("kind") != "model":
                continue
            result = self.register_model(spec.get("source_path", spec.get("id", "model")), metadata={"extracted_id": spec.get("id"), **spec.get("metadata", {})}, mount=mount)
            results.append(result)
        return {"ok": all(item.get("ok") or item.get("error") == "model_already_registered" for item in results), "registered": results, "count": len(results)}

    def load_model(self, model_id: str) -> Dict[str, Any]:
        obj = self._find_model(model_id)
        if obj is None:
            return {"ok": False, "error": "model_not_found", "model_id": model_id}
        result = obj.load()
        self.history.append({"action": "load", "model": obj.id})
        return result

    def unload_model(self, model_id: str) -> Dict[str, Any]:
        obj = self._find_model(model_id)
        if obj is None:
            return {"ok": False, "error": "model_not_found", "model_id": model_id}
        result = obj.unload()
        self.history.append({"action": "unload", "model": obj.id})
        return result

    def resolve_by_format(self, model_format: str) -> Dict[str, Any]:
        matches = [obj.status() for obj in self.models.values() if obj.model_format == model_format]
        return {"ok": bool(matches), "format": model_format, "models": matches}

    def detect_format(self, source_path: str) -> Optional[str]:
        suffix = PurePosixPath(source_path.replace("\\", "/")).suffix.lower()
        if suffix not in self.MODEL_EXTENSIONS:
            return None
        return suffix.lstrip(".")

    def _find_model(self, model_id: str) -> Optional[ModelRuntimeObject]:
        if model_id in self.models:
            return self.models[model_id]
        for obj in self.models.values():
            if obj.id == model_id or obj.source_path == model_id:
                return obj
        return None

    def _model_key(self, source_path: str) -> str:
        return str(PurePosixPath(source_path.replace("\\", "/"))).replace("/", "_").replace(".", "_")[:120]

    def status(self) -> Dict[str, Any]:
        formats: Dict[str, int] = {}
        for obj in self.models.values():
            formats[obj.model_format] = formats.get(obj.model_format, 0) + 1
        return {
            "models": len(self.models),
            "formats": formats,
            "loaded": sum(1 for obj in self.models.values() if obj.loaded),
            "history": len(self.history),
            "last": self.history[-1] if self.history else None,
        }
