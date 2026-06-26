import hashlib
import time
from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, List, Optional


class DNAExtractorEngine:
    """Extracts project DNA from repository/file-tree metadata.

    This foundation is intentionally source-agnostic. A caller can pass a list of
    paths from a Git repo, ZIP archive, tarball, or uploaded folder. Later layers
    can add fetch/clone/extract adapters without changing the Kernel.
    """

    CODE_EXTENSIONS = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs",
        ".java", ".go", ".rs", ".php", ".rb", ".cs", ".cpp", ".c",
    }
    MODEL_EXTENSIONS = {".gguf", ".onnx", ".safetensors", ".pt", ".pth", ".h5", ".joblib", ".mlx", ".trt"}
    ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".pdf", ".docx", ".pptx", ".xlsx"}
    CONFIG_NAMES = {
        "package.json", "pyproject.toml", "requirements.txt", "dockerfile",
        "docker-compose.yml", "compose.yml", "vite.config.js", "next.config.js",
        "tsconfig.json", "pytest.ini", "tox.ini", "setup.py", "go.mod", "cargo.toml",
    }

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.extractions: List[Dict[str, Any]] = []

    def extract_from_tree(self, source_id: str, paths: Iterable[str], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        normalized = sorted({self._normalize_path(path) for path in paths if path})
        fingerprint = self._fingerprint(normalized)
        inventory = self._inventory(normalized)
        runtime_objects = self._detect_runtime_objects(normalized)
        graph_edges = self._build_edges(runtime_objects)
        package = {
            "ok": True,
            "source_id": source_id,
            "package_id": f"mdp:{source_id}:{fingerprint[:12]}",
            "format": "maraim-dna-package-foundation",
            "created_at": time.time(),
            "fingerprint": fingerprint,
            "metadata": metadata or {},
            "inventory": inventory,
            "runtime_objects": runtime_objects,
            "graph_edges": graph_edges,
            "export_name": f"{self._safe_name(source_id)}.mdp",
        }
        self.extractions.append(package)
        if self.kernel is not None:
            self.kernel.emit("dna_extractor.package_created", {"package_id": package["package_id"], "objects": len(runtime_objects)})
        return package

    def _normalize_path(self, path: str) -> str:
        return str(PurePosixPath(path.replace("\\", "/"))).lstrip("/")

    def _fingerprint(self, paths: List[str]) -> str:
        digest = hashlib.sha256()
        for path in paths:
            digest.update(path.encode("utf-8"))
            digest.update(b"\n")
        return digest.hexdigest()

    def _inventory(self, paths: List[str]) -> Dict[str, Any]:
        extensions: Dict[str, int] = {}
        top_dirs: Dict[str, int] = {}
        for path in paths:
            p = PurePosixPath(path)
            suffix = p.suffix.lower()
            if suffix:
                extensions[suffix] = extensions.get(suffix, 0) + 1
            if p.parts:
                top_dirs[p.parts[0]] = top_dirs.get(p.parts[0], 0) + 1
        return {
            "files": len(paths),
            "extensions": extensions,
            "top_dirs": top_dirs,
            "languages": self._detect_languages(extensions),
            "frameworks": self._detect_frameworks(paths),
        }

    def _detect_languages(self, extensions: Dict[str, int]) -> List[str]:
        mapping = {
            ".py": "python", ".js": "javascript", ".jsx": "javascript",
            ".ts": "typescript", ".tsx": "typescript", ".mjs": "javascript",
            ".java": "java", ".go": "go", ".rs": "rust", ".php": "php",
        }
        return sorted({mapping[ext] for ext in extensions if ext in mapping})

    def _detect_frameworks(self, paths: List[str]) -> List[str]:
        joined = "\n".join(paths).lower()
        found = []
        if "package.json" in joined:
            found.append("node")
        if "requirements.txt" in joined or "pyproject.toml" in joined:
            found.append("python")
        if "dockerfile" in joined or "docker-compose" in joined:
            found.append("docker")
        if "next.config" in joined:
            found.append("nextjs")
        if "vite.config" in joined:
            found.append("vite")
        return sorted(set(found))

    def _detect_runtime_objects(self, paths: List[str]) -> List[Dict[str, Any]]:
        objects: List[Dict[str, Any]] = []
        for path in paths:
            p = PurePosixPath(path)
            name = p.name.lower()
            suffix = p.suffix.lower()
            top = p.parts[0].lower() if p.parts else "root"
            if suffix in self.MODEL_EXTENSIONS:
                objects.append(self._object(path, "model", ["model_asset", suffix.lstrip(".")]))
            elif suffix in self.ASSET_EXTENSIONS:
                objects.append(self._object(path, "asset", ["asset"] + ([suffix.lstrip(".")] if suffix else [])))
            elif name in self.CONFIG_NAMES:
                objects.append(self._object(path, "configuration", ["project_configuration"]))
            elif top in {"agents", "agent"} and suffix in self.CODE_EXTENSIONS:
                objects.append(self._object(path, "agent", ["task_execution"])
                )
            elif top in {"workflows", "workflow"}:
                objects.append(self._object(path, "workflow", ["workflow_definition"]))
            elif top in {"tools", "tool"}:
                objects.append(self._object(path, "tool", ["tool_execution"]))
            elif top in {"plugins", "plugin"}:
                objects.append(self._object(path, "plugin", ["plugin_extension"]))
            elif top in {"knowledge", "docs", "documents"}:
                objects.append(self._object(path, "knowledge", ["knowledge_source"]))
            elif suffix in self.CODE_EXTENSIONS:
                objects.append(self._object(path, "code", ["source_code"]))
        return objects

    def _object(self, path: str, kind: str, capabilities: List[str]) -> Dict[str, Any]:
        key = self._safe_name(path).replace(".", "_")[:80]
        return {
            "id": f"extracted.{kind}.{key}@1.0.0",
            "kind": kind,
            "source_path": path,
            "capabilities": capabilities,
            "metadata": {"extracted": True},
        }

    def _build_edges(self, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        edges: List[Dict[str, Any]] = []
        configs = [obj for obj in objects if obj["kind"] == "configuration"]
        for obj in objects:
            if obj["kind"] != "configuration":
                for config in configs[:3]:
                    edges.append({"source": obj["id"], "relation": "uses_configuration", "target": config["id"], "metadata": {}})
        return edges

    def _safe_name(self, value: str) -> str:
        return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value).strip("_") or "project"

    def status(self) -> Dict[str, Any]:
        return {
            "extractions": len(self.extractions),
            "last": self.extractions[-1] if self.extractions else None,
        }
