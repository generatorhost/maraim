import json
import time
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional

from .dna_extractor_engine import DNAExtractorEngine
from .runtime_object import RuntimeObject


class PackageRuntimeObject(RuntimeObject):
    def __init__(self, package: Dict[str, Any]):
        package_id = package.get("package_id", "mdp:unknown:0")
        key = package_id.replace(":", ".").replace("/", ".")
        super().__init__(
            namespace="packages.mdp",
            key=key,
            version=str(package.get("version", "1.0.0")),
            kind="package",
            capabilities=package.get("capabilities", ["dna_package", "runtime_package"]),
            metadata={
                "package_id": package_id,
                "format": package.get("format"),
                "source_id": package.get("source_id"),
                "fingerprint": package.get("fingerprint"),
                "objects": len(package.get("runtime_objects", [])),
                "edges": len(package.get("graph_edges", [])),
            },
        )
        self.package = package

    def execute(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "ok": True,
            "package_id": self.package.get("package_id"),
            "runtime_objects": len(self.package.get("runtime_objects", [])),
            "graph_edges": len(self.package.get("graph_edges", [])),
            "payload": payload or {},
        }


class DNAExtractedRuntimeObject(RuntimeObject):
    def __init__(self, spec: Dict[str, Any]):
        object_id = spec.get("id", "extracted.unknown.object@1.0.0")
        base, _, version = object_id.partition("@")
        parts = base.split(".")
        key = parts[-1] if parts else object_id
        namespace = ".".join(parts[:-1]) if len(parts) > 1 else "extracted"
        super().__init__(
            namespace=namespace,
            key=key,
            version=version or "1.0.0",
            kind=spec.get("kind", "runtime"),
            capabilities=spec.get("capabilities", []),
            metadata=spec.get("metadata", {}),
        )
        self.source_path = spec.get("source_path")
        self.spec = spec

    def execute(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "ok": True,
            "object_id": self.id,
            "kind": self.kind,
            "source_path": self.source_path,
            "payload": payload or {},
        }


class DNAPackageEngine:
    TEXT_EXTENSIONS = {".json", ".md", ".txt", ".jsonl", ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".toml", ".yml", ".yaml"}

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.packages: Dict[str, Dict[str, Any]] = {}
        self.package_objects: Dict[str, str] = {}
        self.history: List[Dict[str, Any]] = []

    def import_package(self, package: Dict[str, Any], activate: bool = True) -> Dict[str, Any]:
        validation = self.validate_package(package)
        if not validation.get("ok"):
            return validation
        package_id = package["package_id"]
        if package_id in self.packages:
            return {"ok": False, "error": "package_already_imported", "package_id": package_id}
        self.packages[package_id] = package
        package_runtime = PackageRuntimeObject(package)
        mounted_objects: List[str] = []
        mounted_edges: List[Dict[str, Any]] = []
        if self.kernel is not None and activate:
            package_runtime.discover(self.kernel).validate(self.kernel).mount(self.kernel).connect(self.kernel)
            self.kernel.graph.add_node(package_runtime)
            self.package_objects[package_id] = package_runtime.id
            mounted_objects.append(package_runtime.id)
            for spec in package.get("runtime_objects", []):
                obj = DNAExtractedRuntimeObject(spec)
                obj.discover(self.kernel).validate(self.kernel).mount(self.kernel).connect(self.kernel)
                self.kernel.graph.add_node(obj)
                self.kernel.graph.add_edge(package_runtime.id, "exports", obj.id, {"package_id": package_id})
                mounted_objects.append(obj.id)
            for edge in package.get("graph_edges", []):
                source = edge.get("source")
                target = edge.get("target")
                relation = edge.get("relation")
                if source and target and relation and self.kernel.graph.get(source) and self.kernel.graph.get(target):
                    self.kernel.graph.add_edge(source, relation, target, edge.get("metadata", {}))
                    mounted_edges.append(edge)
            self.kernel.emit("dna_package.imported", {"package_id": package_id, "objects": len(mounted_objects), "edges": len(mounted_edges)})
        record = {"action": "import", "package_id": package_id, "timestamp": time.time(), "objects": len(mounted_objects), "edges": len(mounted_edges)}
        self.history.append(record)
        return {"ok": True, "package_id": package_id, "package_runtime": self.package_objects.get(package_id), "mounted_objects": mounted_objects, "mounted_edges": mounted_edges}

    def import_project_tree(self, source_id: str, paths: Iterable[str], metadata: Optional[Dict[str, Any]] = None, file_contents: Optional[Dict[str, str]] = None, activate: bool = True) -> Dict[str, Any]:
        extractor = DNAExtractorEngine(self.kernel)
        package = extractor.extract_from_tree(source_id, paths, metadata=metadata, file_contents=file_contents)
        imported = self.import_package(package, activate=activate)
        return {"ok": imported.get("ok", False), "extracted": package, "imported": imported}

    def import_archive(self, archive_path: str, source_id: Optional[str] = None, activate: bool = True) -> Dict[str, Any]:
        archive = Path(archive_path)
        if not archive.exists():
            return {"ok": False, "error": "archive_not_found", "archive_path": archive_path}
        if archive.suffix.lower() not in {".zip", ".mdp"}:
            return {"ok": False, "error": "unsupported_archive", "archive_path": archive_path}
        paths: List[str] = []
        contents: Dict[str, str] = {}
        mdp_manifest: Optional[Dict[str, Any]] = None
        with zipfile.ZipFile(archive, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                rel = str(PurePosixPath(info.filename)).lstrip("/")
                paths.append(rel)
                if rel in {"mdp.json", "manifest/mdp.json", "manifest/package.json"}:
                    try:
                        mdp_manifest = json.loads(zf.read(info).decode("utf-8"))
                    except Exception:
                        mdp_manifest = None
                if PurePosixPath(rel).suffix.lower() in self.TEXT_EXTENSIONS and info.file_size <= 1024 * 1024:
                    try:
                        contents[rel] = zf.read(info).decode("utf-8", errors="ignore")
                    except Exception:
                        pass
        if mdp_manifest and "runtime_objects" in mdp_manifest and "package_id" in mdp_manifest:
            return self.import_package(mdp_manifest, activate=activate)
        return self.import_project_tree(source_id or archive.stem, paths, metadata={"source_archive": archive.name}, file_contents=contents, activate=activate)

    def validate_package(self, package: Dict[str, Any]) -> Dict[str, Any]:
        required = ["package_id", "runtime_objects", "graph_edges", "export_name"]
        missing = [key for key in required if key not in package]
        if missing:
            return {"ok": False, "error": "invalid_mdp_package", "missing": missing}
        if not isinstance(package.get("runtime_objects"), list):
            return {"ok": False, "error": "invalid_runtime_objects"}
        if not isinstance(package.get("graph_edges"), list):
            return {"ok": False, "error": "invalid_graph_edges"}
        return {"ok": True, "package_id": package["package_id"]}

    def export_package(self, package_id: str) -> Dict[str, Any]:
        package = self.packages.get(package_id)
        if not package:
            return {"ok": False, "error": "package_not_found", "package_id": package_id}
        payload = json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True)
        return {"ok": True, "package_id": package_id, "export_name": package.get("export_name", "package.mdp"), "content": payload}

    def status(self) -> Dict[str, Any]:
        return {"packages": len(self.packages), "package_objects": len(self.package_objects), "history": len(self.history), "last": self.history[-1] if self.history else None}
