import hashlib
import re
import time
from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, List, Optional


class DNAExtractorEngine:
    """Universal DNA extraction foundation.

    Converts repository, archive, or folder file trees into MDP-ready runtime
    object specifications. The extractor remains source-agnostic: Git, ZIP,
    folder, uploaded archive, registry, or asset adapters can all pass paths and
    optional text contents into the same pipeline.
    """

    CODE_EXTENSIONS = {
        ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs",
        ".java", ".go", ".rs", ".php", ".rb", ".cs", ".cpp", ".c",
    }
    MODEL_EXTENSIONS = {".gguf", ".onnx", ".safetensors", ".pt", ".pth", ".h5", ".joblib", ".mlx", ".trt"}
    ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".pdf", ".docx", ".pptx", ".xlsx"}
    DATASET_EXTENSIONS = {".csv", ".parquet", ".jsonl", ".ndjson", ".arrow", ".sqlite", ".db"}
    CONFIG_NAMES = {
        "package.json", "pyproject.toml", "requirements.txt", "dockerfile",
        "docker-compose.yml", "compose.yml", "vite.config.js", "next.config.js",
        "tsconfig.json", "pytest.ini", "tox.ini", "setup.py", "go.mod", "cargo.toml",
    }

    DIRECTORY_KIND_RULES = {
        "agents": ("agent", ["task_execution"]),
        "agent": ("agent", ["task_execution"]),
        "workflows": ("workflow", ["workflow_definition"]),
        "workflow": ("workflow", ["workflow_definition"]),
        "missions": ("mission", ["mission_definition"]),
        "mission": ("mission", ["mission_definition"]),
        "tasks": ("task", ["task_definition"]),
        "jobs": ("job", ["job_definition"]),
        "skills": ("skill", ["skill_definition"]),
        "capabilities": ("capability", ["capability_definition"]),
        "tools": ("tool", ["tool_execution"]),
        "tool": ("tool", ["tool_execution"]),
        "plugins": ("plugin", ["plugin_extension"]),
        "plugin": ("plugin", ["plugin_extension"]),
        "connectors": ("connector", ["external_connection"]),
        "integrations": ("integration", ["integration_bridge"]),
        "providers": ("provider", ["provider_binding"]),
        "services": ("service", ["service_runtime"]),
        "microservices": ("service", ["service_runtime", "microservice"]),
        "apis": ("api", ["api_surface"]),
        "routes": ("api", ["api_route"]),
        "mcp": ("mcp_server", ["mcp_protocol"]),
        "prompts": ("prompt", ["prompt_template"]),
        "templates": ("template", ["template_asset"]),
        "policies": ("policy", ["policy_rule"]),
        "rules": ("rule", ["rule_definition"]),
        "permissions": ("permission", ["permission_rule"]),
        "guardrails": ("guardrail", ["safety_guardrail"]),
        "security": ("security", ["security_control"]),
        "knowledge": ("knowledge", ["knowledge_source"]),
        "docs": ("knowledge", ["knowledge_source"]),
        "documents": ("document", ["document_source"]),
        "memory": ("memory", ["memory_seed"]),
        "memories": ("memory", ["memory_seed"]),
        "vectorstores": ("vectorstore", ["vector_index"]),
        "embeddings": ("embedding", ["embedding_model_or_index"]),
        "datasets": ("dataset", ["dataset_source"]),
        "data": ("dataset", ["dataset_source"]),
        "pipelines": ("pipeline", ["pipeline_definition"]),
        "stages": ("stage", ["pipeline_stage"]),
        "events": ("event", ["event_definition"]),
        "triggers": ("trigger", ["trigger_definition"]),
        "schedules": ("schedule", ["schedule_definition"]),
        "schedulers": ("scheduler", ["scheduler_definition"]),
        "queues": ("queue", ["queue_definition"]),
        "topics": ("topic", ["pubsub_topic"]),
        "runtimes": ("runtime", ["runtime_component"]),
        "executors": ("executor", ["execution_worker"]),
        "planners": ("planner", ["planning_component"]),
        "analyzers": ("analyzer", ["analysis_component"]),
        "reviewers": ("reviewer", ["review_component"]),
        "generators": ("generator", ["generation_component"]),
        "validators": ("validator", ["validation_component"]),
        "optimizers": ("optimizer", ["optimization_component"]),
        "reasoners": ("reasoner", ["reasoning_component"]),
        "orchestrators": ("orchestrator", ["orchestration_component"]),
        "coordinators": ("coordinator", ["coordination_component"]),
        "communicators": ("communicator", ["communication_component"]),
        "ui": ("ui", ["ui_surface"]),
        "components": ("ui_component", ["ui_component"]),
        "pages": ("ui_screen", ["ui_screen"]),
        "screens": ("ui_screen", ["ui_screen"]),
        "dashboards": ("dashboard", ["dashboard_surface"]),
        "artifacts": ("artifact", ["artifact_output"]),
        "projects": ("project", ["project_definition"]),
        "organizations": ("organization", ["organization_definition"]),
        "tenants": ("tenant", ["tenant_definition"]),
        "users": ("user", ["user_definition"]),
        "marketplaces": ("marketplace", ["marketplace_surface"]),
        "freelance": ("freelance", ["freelance_domain"]),
        "remote_work": ("remote_work", ["remote_work_domain"]),
        "automation": ("automation", ["automation_definition"]),
        "notifications": ("notification", ["notification_channel"]),
        "monitoring": ("monitoring", ["monitoring_signal"]),
        "logs": ("log", ["log_source"]),
        "storage": ("storage", ["storage_binding"]),
        "cache": ("cache", ["cache_binding"]),
        "deployments": ("deployment", ["deployment_definition"]),
        "environments": ("environment", ["environment_definition"]),
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
            "runtime_kind_signals": sorted({self._classify_path(path, semantic or {})[0] for path in paths}),
        }

    def _detect_languages(self, extensions: Dict[str, int]) -> List[str]:
        mapping = {
            ".py": "python", ".js": "javascript", ".jsx": "javascript",
            ".ts": "typescript", ".tsx": "typescript", ".mjs": "javascript",
            ".java": "java", ".go": "go", ".rs": "rust", ".php": "php",
            ".rb": "ruby", ".cs": "csharp", ".cpp": "cpp", ".c": "c",
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
        if "django" in text:
            found.append("django")
        if "langchain" in text:
            found.append("langchain")
        if "llama_index" in text or "llama-index" in text:
            found.append("llama_index")
        return sorted(set(found))

    def _semantic_inventory(self, paths: List[str], contents: Dict[str, str]) -> Dict[str, Any]:
        routes: List[Dict[str, str]] = []
        functions: List[Dict[str, str]] = []
        classes: List[Dict[str, str]] = []
        imports: List[str] = []
        dependencies: List[str] = []
        secrets: List[Dict[str, str]] = []
        environment_keys: List[Dict[str, str]] = []
        api_clients: List[Dict[str, str]] = []
        database_signals: List[Dict[str, str]] = []
        queue_signals: List[Dict[str, str]] = []

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
            environment_keys.extend({"path": path, "key": key} for key in self._extract_environment_keys(text))
            api_clients.extend({"path": path, "client": client} for client in self._detect_api_clients(text))
            database_signals.extend({"path": path, "database": db} for db in self._detect_database_signals(text))
            queue_signals.extend({"path": path, "queue": queue} for queue in self._detect_queue_signals(text))
            if lower_path.endswith("requirements.txt"):
                dependencies.extend(line.strip().split("==")[0] for line in text.splitlines() if line.strip() and not line.strip().startswith("#"))
            if lower_path.endswith("package.json"):
                dependencies.extend(self._extract_package_json_dependencies(text))

        return {
            "content_files": len(contents),
            "imports": sorted(set(imports))[:300],
            "dependencies": sorted(set(dependencies))[:300],
            "routes": routes[:300],
            "functions": functions[:500],
            "classes": classes[:500],
            "secret_signals": secrets[:150],
            "environment_keys": environment_keys[:150],
            "api_clients": api_clients[:150],
            "database_signals": database_signals[:150],
            "queue_signals": queue_signals[:150],
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
        return list(dict.fromkeys(names))

    def _extract_routes(self, text: str) -> List[str]:
        routes = re.findall(r"@\w+\.(?:get|post|put|delete|patch)\(['\"]([^'\"]+)", text)
        routes += re.findall(r"(?:app|router)\.(?:get|post|put|delete|patch)\(['\"]([^'\"]+)", text)
        return sorted(set(routes))

    def _detect_secret_signals(self, text: str) -> List[str]:
        signals = []
        for token in ["api_key", "secret", "password", "private_key", "access_token", "client_secret"]:
            if token in text.lower():
                signals.append(token)
        return sorted(set(signals))

    def _extract_environment_keys(self, text: str) -> List[str]:
        keys = re.findall(r"(?:os\.getenv|process\.env)\(['\"]?([A-Z0-9_]+)", text)
        keys += re.findall(r"^([A-Z0-9_]{3,})=", text, flags=re.MULTILINE)
        return sorted(set(keys))

    def _detect_api_clients(self, text: str) -> List[str]:
        lower = text.lower()
        clients = []
        for token in ["openai", "anthropic", "gemini", "ollama", "huggingface", "requests", "axios", "fetch("]:
            if token in lower:
                clients.append(token.rstrip("("))
        return sorted(set(clients))

    def _detect_database_signals(self, text: str) -> List[str]:
        lower = text.lower()
        return sorted({db for db in ["postgres", "mysql", "sqlite", "mongodb", "redis", "qdrant", "chroma", "pinecone"] if db in lower})

    def _detect_queue_signals(self, text: str) -> List[str]:
        lower = text.lower()
        return sorted({q for q in ["celery", "rabbitmq", "kafka", "redis", "sqs", "pubsub", "queue"] if q in lower})

    def _extract_package_json_dependencies(self, text: str) -> List[str]:
        deps = []
        for match in re.findall(r'"([A-Za-z0-9_@/.-]+)"\s*:\s*"[^"]+"', text):
            if match not in {"name", "version", "description", "main", "type"}:
                deps.append(match)
        return deps

    def _detect_runtime_objects(self, paths: List[str], semantic: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        semantic = semantic or {}
        objects: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for path in paths:
            kind, capabilities = self._classify_path(path, semantic)
            obj = self._object(path, kind, capabilities, semantic)
            if obj["id"] not in seen:
                objects.append(obj)
                seen.add(obj["id"])
        return objects

    def _classify_path(self, path: str, semantic: Dict[str, Any]) -> tuple[str, List[str]]:
        p = PurePosixPath(path)
        name = p.name.lower()
        suffix = p.suffix.lower()
        top = p.parts[0].lower() if p.parts else "root"
        stem = p.stem.lower()

        if suffix in self.MODEL_EXTENSIONS:
            return "model", ["model_asset", suffix.lstrip(".")]
        if top in self.DIRECTORY_KIND_RULES:
            return self.DIRECTORY_KIND_RULES[top]
        if name in {"schema.sql", "migration.sql"} or top in {"migrations", "database", "db", "schemas"}:
            return "database", ["database_schema"]
        if suffix in self.DATASET_EXTENSIONS:
            return "dataset", ["dataset_source", suffix.lstrip(".")]
        if suffix in self.ASSET_EXTENSIONS:
            return "asset", ["asset"] + ([suffix.lstrip(".")] if suffix else [])
        if name in self.CONFIG_NAMES or name.startswith(".") or name.endswith((".env", ".ini", ".toml", ".yaml", ".yml")):
            if "docker" in name:
                return "deployment", ["deployment_definition", "containerized"]
            if name.endswith(".env") or name == ".env":
                return "environment", ["environment_definition"]
            return "configuration", ["project_configuration"]
        if stem in {"prompt", "system_prompt", "instructions"}:
            return "prompt", ["prompt_template"]
        if stem in {"policy", "policies"}:
            return "policy", ["policy_rule"]
        if stem in {"readme", "architecture", "spec", "blueprint"}:
            return "knowledge", ["knowledge_source", "documentation"]
        if any(route.get("path") == path for route in semantic.get("routes", [])):
            return "api", ["api_surface", "api_routes"]
        if suffix in self.CODE_EXTENSIONS:
            return "code", ["source_code"]
        return "artifact", ["project_artifact"]

    def _object(self, path: str, kind: str, capabilities: List[str], semantic: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        semantic = semantic or {}
        key = self._safe_name(path).replace(".", "_")[:80]
        path_functions = [item["name"] for item in semantic.get("functions", []) if item.get("path") == path]
        path_classes = [item["name"] for item in semantic.get("classes", []) if item.get("path") == path]
        path_routes = [item["route"] for item in semantic.get("routes", []) if item.get("path") == path]
        path_env = [item["key"] for item in semantic.get("environment_keys", []) if item.get("path") == path]
        path_api_clients = [item["client"] for item in semantic.get("api_clients", []) if item.get("path") == path]
        path_databases = [item["database"] for item in semantic.get("database_signals", []) if item.get("path") == path]
        path_queues = [item["queue"] for item in semantic.get("queue_signals", []) if item.get("path") == path]
        inferred = list(capabilities)
        if path_routes:
            inferred.append("api_routes")
        if path_functions:
            inferred.append("callable_units")
        if path_classes:
            inferred.append("class_units")
        if path_env:
            inferred.append("environment_variables")
        if path_api_clients:
            inferred.append("external_api_client")
        if path_databases:
            inferred.append("database_usage")
        if path_queues:
            inferred.append("queue_usage")
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
                "environment_keys": path_env[:50],
                "api_clients": path_api_clients[:50],
                "databases": path_databases[:50],
                "queues": path_queues[:50],
            },
        }

    def _build_edges(self, objects: List[Dict[str, Any]], semantic: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        edges: List[Dict[str, Any]] = []
        configs = [obj for obj in objects if obj["kind"] in {"configuration", "environment"}]
        models = [obj for obj in objects if obj["kind"] == "model"]
        tools = [obj for obj in objects if obj["kind"] == "tool"]
        knowledge = [obj for obj in objects if obj["kind"] in {"knowledge", "document"}]
        policies = [obj for obj in objects if obj["kind"] in {"policy", "rule", "guardrail", "permission", "security"}]
        prompts = [obj for obj in objects if obj["kind"] == "prompt"]
        connectors = [obj for obj in objects if obj["kind"] in {"connector", "integration", "provider"}]
        services = [obj for obj in objects if obj["kind"] in {"service", "api", "mcp_server"}]
        storage = [obj for obj in objects if obj["kind"] in {"database", "storage", "cache", "vectorstore", "embedding"}]
        for obj in objects:
            if obj["kind"] not in {"configuration", "environment"}:
                for config in configs[:5]:
                    edges.append({"source": obj["id"], "relation": "uses_configuration", "target": config["id"], "metadata": {}})
            if obj["kind"] in {"agent", "workflow", "mission", "task", "service", "api", "tool", "plugin", "orchestrator"}:
                for model in models[:3]:
                    edges.append({"source": obj["id"], "relation": "can_use_model", "target": model["id"], "metadata": {}})
                for tool in tools[:8]:
                    if tool["id"] != obj["id"]:
                        edges.append({"source": obj["id"], "relation": "can_use_tool", "target": tool["id"], "metadata": {}})
                for item in knowledge[:8]:
                    edges.append({"source": obj["id"], "relation": "can_use_knowledge", "target": item["id"], "metadata": {}})
                for prompt in prompts[:5]:
                    edges.append({"source": obj["id"], "relation": "can_use_prompt", "target": prompt["id"], "metadata": {}})
                for connector in connectors[:5]:
                    edges.append({"source": obj["id"], "relation": "can_use_connector", "target": connector["id"], "metadata": {}})
                for item in storage[:5]:
                    edges.append({"source": obj["id"], "relation": "can_use_storage", "target": item["id"], "metadata": {}})
            if obj["kind"] in {"workflow", "mission", "pipeline", "automation"}:
                for service in services[:5]:
                    edges.append({"source": obj["id"], "relation": "can_call_service", "target": service["id"], "metadata": {}})
            if policies and obj["kind"] not in {"policy", "rule", "guardrail", "permission", "security"}:
                for policy in policies[:5]:
                    edges.append({"source": obj["id"], "relation": "governed_by", "target": policy["id"], "metadata": {}})
        return self._dedupe_edges(edges)

    def _dedupe_edges(self, edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        result = []
        for edge in edges:
            key = (edge.get("source"), edge.get("relation"), edge.get("target"))
            if key in seen:
                continue
            seen.add(key)
            result.append(edge)
        return result

    def _safe_name(self, value: str) -> str:
        return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value).strip("_") or "project"

    def status(self) -> Dict[str, Any]:
        return {"extractions": len(self.extractions), "last": self.extractions[-1] if self.extractions else None}
