import hashlib
import re
import time
from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, List, Optional


class DNAExtractorEngine:
    """Extracts project DNA from repository/file-tree metadata and light content signals.

    This engine is source-agnostic. A caller can pass paths from Git, ZIP,
    tarball, uploaded archive, or folder. Optional file_contents enables
    semantic extraction without changing the Kernel.
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

    def extract_from_tree(
        self,
        source_id: str,
        paths: Iterable[str],
        metadata: Optional[Dict[str, Any]] = None,
        file_contents: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        normalized = sorted({self._normalize_path(path) for path in paths if path})
        contents = {self._normalize_path(k): v for k, v in (file_contents or {}).items()}
        fingerprint = self._fingerprint(normalized, contents)
        semantic = self._semantic_inventory(normalized, contents)
        inventory = self._inventory(normalized, semantic)
        runtime_objects = self._detect_runtime_objects(normalized, semantic)
        graph_edges = self._build_edges(runtime_objects, semantic)
        package = {
            "ok": True,
            "source_id": source_id,
            "package_id": f"mdp:{source_id}:{fingerprint[:12]}",
            "format": "maraim-dna-package-foundation",
            "created_at": time.time(),
            "fingerprint": fingerprint,
            "metadata": metadata or {},
            "inventory": inventory,
            "semantic": semantic,
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

    def _fingerprint(self, paths: List[str], contents: Optional[Dict[str, str]] = None) -> str:
        digest = hashlib.sha256()
        for path in paths:
            digest.update(path.encode("utf-8"))
            digest.update(b"\n")
            if contents and path in contents:
                digest.update(hashlib.sha256(contents[path].encode("utf-8", errors="ignore")).hexdigest().encode("utf-8"))
                digest.update(b"\n")
        return digest.hexdigest()

    def _inventory(self, paths: List[str], semantic: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
            "frameworks": self._detect_frameworks(paths, semantic or {}),
        }

    def _detect_languages(self, extensions: Dict[str, int]) -> List[str]:
        mapping = {
            ".py": "python", ".js": "javascript", ".jsx": "javascript",
            ".ts": "typescript", ".tsx": "typescript", ".mjs": "javascript",
            ".java": "java", ".go": "go", ".rs": "rust", ".php": "php",
        }
        return sorted({mapping[ext] for ext in extensions if ext in mapping})

    def _detect_frameworks(self, paths: List[str], semantic: Dict[str, Any]) -> List[str]:
        joined = "\n".join(paths).lower()
        text = "\n".join(semantic.get("imports", [])) + "\n" + "\n".join(semantic.get("dependencies", []))
        text = text.lower()
        found = []
        if "package.json" in joined:
            found.append("node")
        if "requirements.txt" in joined or "pyproject.toml" in joined:
            found.append("python")
        if "dockerfile" in joined or "docker-compose" in joined:
            found.append("docker")
        if "next.config" in joined or "next" in text:
            found.append("nextjs")
        if "vite.config" in joined or "vite" in text:
            found.append("vite")
        if "fastapi" in text:
            found.append("fastapi")
        if "flask" in text:
            found.append("flask")
        if "react" in text:
            found.append("react")
        return sorted(set(found))

    def _semantic_inventory(self, paths: List[str], contents: Dict[str, str]) -> Dict[str, Any]:
        routes: List[Dict[str, str]] = []
        functions: List[Dict[str, str]] = []
        classes: List[Dict[str, str]] = []
        imports: List[str] = []
        dependencies: List[str] = []
        secrets: List[Dict[str, str]] = []

        for path in paths:
            text = contents.get(path, "")
            if not text:
                continue
            lower_path = path.lower()
            imports.extend(self._extract_imports(text))
            functions.extend({"path": path, "name": name} for name in self._extract_functions(text))
            classes.extend({"path": path, "name": name} for name in self._extract_classes(text))
            routes.extend({"path": path, "route": route} for route in self._extract_routes(text))
            secrets.extend({"path": path, "signal": signal} for signal in self._detect_secret_signals(text))
            if lower_path.endswith("requirements.txt"):
                dependencies.extend(line.strip().split("==")[0] for line in text.splitlines() if line.strip() and not line.strip().startswith("#"))
            if lower_path.endswith("package.json"):
                dependencies.extend(self._extract_package_json_dependencies(text))

        return {
            "content_files": len(contents),
            "imports": sorted(set(imports))[:200],
            "dependencies": sorted(set(dependencies))[:200],
            "routes": routes[:200],
            "functions": functions[:300],
            "classes": classes[:300],
            "secret_signals": secrets[:100],
        }

    def _extract_imports(self, text: str) -> List[str]:
        found = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("import "):
                found.append(stripped.split()[1].split(".")[0].strip("'\";"))
            elif stripped.startswith("from "):
                found.append(stripped.split()[1].split(".")[0].strip("'\";"))
            elif " from " in stripped and stripped.startswith("import"):
                parts = stripped.split(" from ")
                if len(parts) == 2:
                    found.append(parts[1].strip().strip("'\";"))
        return [x for x in found if x]

    def _extract_functions(self, text: str) -> List[str]:
        names = re.findall(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", text, flags=re.MULTILINE)
        names += re.findall(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", text, flags=re.MULTILINE)
        return names

    def _extract_classes(self, text: str) -> List[str]:
        names = re.findall(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)", text, flags=re.MULTILINE)
        names += re.findall(r"^\s*(?:export\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)", text, flags=re.MULTILINE)
        return names

    def _extract_routes(self, text: str) -> List[str]:
        routes = re.findall(r"@\w+\.(?:get|post|put|delete|patch)\(['\"]([^'\"]+)", text)
        routes += re.findall(r"(?:app|router)\.(?:get|post|put|delete|patch)\(['\"]([^'\"]+)", text)
        return sorted(set(routes))

    def _detect_secret_signals(self, text: str) -> List[str]:
        signals = []
        for token in ["api_key", "secret", "password", "private_key", "access_token"]:
            if token in text.lower():
                signals.append(token)
        return sorted(set(signals))

    def _extract_package_json_dependencies(self, text: str) -> List[str]:
        deps = []
        for match in re.findall(r'"([A-Za-z0-9_@/.-]+)"\s*:\s*"[^"]+"', text):
            if match not in {"name", "version", "description", "main", "type"}:
                deps.append(match)
        return deps

    def _detect_runtime_objects(self, paths: List[str], semantic: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        semantic = semantic or {}
        objects: List[Dict[str, Any]] = []
        for path in paths:
            p = PurePosixPath(path)
            name = p.name.lower()
            suffix = p.suffix.lower()
            top = p.parts[0].lower() if p.parts else "root"
            if suffix in self.MODEL_EXTENSIONS:
                objects.append(self._object(path, "model", ["model_asset", suffix.lstrip(".")], semantic))
            elif suffix in self.ASSET_EXTENSIONS:
                objects.append(self._object(path, "asset", ["asset"] + ([suffix.lstrip(".")] if suffix else []), semantic))
            elif name in self.CONFIG_NAMES:
                objects.append(self._object(path, "configuration", ["project_configuration"], semantic))
            elif top in {"agents", "agent"} and suffix in self.CODE_EXTENSIONS:
                objects.append(self._object(path, "agent", ["task_execution"], semantic))
            elif top in {"workflows", "workflow"}:
                objects.append(self._object(path, "workflow", ["workflow_definition"], semantic))
            elif top in {"tools", "tool"}:
                objects.append(self._object(path, "tool", ["tool_execution"], semantic))
            elif top in {"plugins", "plugin"}:
                objects.append(self._object(path, "plugin", ["plugin_extension"], semantic))
            elif top in {"knowledge", "docs", "documents"}:
                objects.append(self._object(path, "knowledge", ["knowledge_source"], semantic))
            elif suffix in self.CODE_EXTENSIONS:
                objects.append(self._object(path, "code", ["source_code"], semantic))
        return objects

    def _object(self, path: str, kind: str, capabilities: List[str], semantic: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        semantic = semantic or {}
        key = self._safe_name(path).replace(".", "_")[:80]
        path_functions = [item["name"] for item in semantic.get("functions", []) if item.get("path") == path]
        path_classes = [item["name"] for item in semantic.get("classes", []) if item.get("path") == path]
        path_routes = [item["route"] for item in semantic.get("routes", []) if item.get("path") == path]
        inferred = list(capabilities)
        if path_routes:
            inferred.append("api_routes")
        if path_functions:
            inferred.append("callable_units")
        if path_classes:
            inferred.append("class_units")
        return {
            "id": f"extracted.{kind}.{key}@1.0.0",
            "kind": kind,
            "source_path": path,
            "capabilities": sorted(set(inferred)),
            "metadata": {
                "extracted": True,
                "functions": path_functions[:50],
                "classes": path_classes[:50],
                "routes": path_routes[:50],
            },
        }

    def _build_edges(self, objects: List[Dict[str, Any]], semantic: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        edges: List[Dict[str, Any]] = []
        configs = [obj for obj in objects if obj["kind"] == "configuration"]
        models = [obj for obj in objects if obj["kind"] == "model"]
        tools = [obj for obj in objects if obj["kind"] == "tool"]
        knowledge = [obj for obj in objects if obj["kind"] == "knowledge"]
        for obj in objects:
            if obj["kind"] != "configuration":
                for config in configs[:3]:
                    edges.append({"source": obj["id"], "relation": "uses_configuration", "target": config["id"], "metadata": {}})
            if obj["kind"] in {"agent", "workflow"}:
                for model in models[:2]:
                    edges.append({"source": obj["id"], "relation": "can_use_model", "target": model["id"], "metadata": {}})
                for tool in tools[:5]:
                    edges.append({"source": obj["id"], "relation": "can_use_tool", "target": tool["id"], "metadata": {}})
                for item in knowledge[:5]:
                    edges.append({"source": obj["id"], "relation": "can_use_knowledge", "target": item["id"], "metadata": {}})
        return edges

    def _safe_name(self, value: str) -> str:
        return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value).strip("_") or "project"

    def status(self) -> Dict[str, Any]:
        return {"extractions": len(self.extractions), "last": self.extractions[-1] if self.extractions else None}
