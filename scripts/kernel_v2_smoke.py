import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.dna.compiler import compile_dna
from maraim.kernel_v2 import (
    DNAExtractorEngine,
    DNAPackageEngine,
    KernelV2,
    ModelEngine,
    RuntimeLifecycleManager,
    RuntimeObjectManager,
    RuntimeResourceManager,
)

MISSION_ID = "missions.sample.research_mission@1.0.0"
AGENT_ID = "agents.sample.research_agent@1.0.0"

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
resources = RuntimeResourceManager(kernel, capacity={"cpu_units": 16, "ram_mb": 2048, "threads": 8})
resource_allocate = resources.allocate(MISSION_ID, {"cpu_units": 2, "ram_mb": 256, "threads": 1}, reason="smoke_execution")
resource_rebalance = resources.rebalance()
resource_release = resources.release(MISSION_ID)
resource_status = resources.status()
objects = RuntimeObjectManager(kernel)
object_snapshot = objects.snapshot(AGENT_ID, label="before_update")
object_update = objects.update(AGENT_ID, metadata={"smoke": "updated"}, capabilities=["research", "task_execution", "smoke_capability"])
object_restore = objects.restore(AGENT_ID)
object_clone = objects.clone(AGENT_ID, new_key="research_agent_clone")
clone_id = object_clone.get("clone", {}).get("id")
object_archive = objects.archive(clone_id) if clone_id else {"ok": False}
object_delete = objects.delete(clone_id) if clone_id else {"ok": False}
object_status = objects.status()
extractor = DNAExtractorEngine(kernel)
project_paths = [
    "agents/research_agent.py",
    "workflows/research_workflow.py",
    "missions/research_mission.yaml",
    "tasks/discover_task.yaml",
    "jobs/nightly_job.yaml",
    "skills/research_skill.md",
    "capabilities/text_generation.yaml",
    "tools/browser_tool.py",
    "plugins/upwork_plugin.py",
    "connectors/github_connector.py",
    "integrations/slack_integration.py",
    "providers/openai_provider.py",
    "services/report_service.py",
    "microservices/worker_service.py",
    "apis/research_api.py",
    "routes/health.py",
    "mcp/server.py",
    "models/sample.gguf",
    "models/embed.onnx",
    "models/adapter.safetensors",
    "knowledge/guide.md",
    "documents/spec.pdf",
    "memory/seed.jsonl",
    "vectorstores/chroma.index",
    "embeddings/embedder.py",
    "datasets/leads.csv",
    "pipelines/research_pipeline.yaml",
    "stages/extract_stage.yaml",
    "events/project_found.yaml",
    "triggers/daily_trigger.yaml",
    "schedules/daily.yaml",
    "schedulers/priority_scheduler.py",
    "queues/jobs_queue.yaml",
    "topics/events_topic.yaml",
    "runtimes/python_runtime.py",
    "executors/task_executor.py",
    "planners/mission_planner.py",
    "analyzers/market_analyzer.py",
    "reviewers/quality_reviewer.py",
    "generators/proposal_generator.py",
    "validators/output_validator.py",
    "optimizers/cost_optimizer.py",
    "reasoners/research_reasoner.py",
    "orchestrators/swarm_orchestrator.py",
    "coordinators/team_coordinator.py",
    "communicators/email_communicator.py",
    "prompts/system_prompt.md",
    "templates/report_template.md",
    "policies/data_policy.md",
    "rules/pricing_rule.yaml",
    "permissions/user_permissions.yaml",
    "guardrails/safety_guardrail.md",
    "security/sandbox_policy.md",
    "ui/App.tsx",
    "components/Card.tsx",
    "pages/Dashboard.tsx",
    "screens/ApprovalScreen.tsx",
    "dashboards/executive_dashboard.json",
    "artifacts/sample_report.docx",
    "projects/project_profile.json",
    "organizations/org.json",
    "tenants/default_tenant.json",
    "users/admin_user.json",
    "marketplaces/freelance_market.json",
    "freelance/upwork_source.json",
    "remote_work/remote_source.json",
    "automation/followup.yaml",
    "notifications/email_channel.yaml",
    "monitoring/metrics.yaml",
    "logs/app.log",
    "storage/minio.yaml",
    "cache/redis.yaml",
    "deployments/docker-compose.yml",
    "environments/.env",
    "database/schema.sql",
    "package.json",
    "docker-compose.yml",
    "assets/logo.png",
]
contents = {
    "agents/research_agent.py": "from fastapi import APIRouter\nimport os\nclass ResearchAgent:\n    pass\ndef analyze_project():\n    return True\nrouter = APIRouter()\n@router.get('/research')\ndef route():\n    return {}\nOPENAI_API_KEY=os.getenv('OPENAI_API_KEY')\n",
    "apis/research_api.py": "from fastapi import FastAPI\napp = FastAPI()\n@app.post('/api/research')\ndef api_research():\n    return {}\n",
    "tools/browser_tool.py": "import requests\ndef browse(url):\n    return requests.get(url).text\n",
    "services/report_service.py": "import redis\nimport psycopg2\ndef run_service():\n    return 'ok'\n",
    "providers/openai_provider.py": "import openai\ndef call_provider():\n    return openai\n",
    "workflows/research_workflow.py": "def plan():\n    return ['discover','analyze']\n",
    "environments/.env": "OPENAI_API_KEY=test\nDATABASE_URL=postgres://local\n",
    "package.json": '{"dependencies":{"react":"latest","vite":"latest","axios":"latest"}}',
    "requirements.txt": "fastapi\nrequests\nredis\npsycopg2\n",
}
extracted = extractor.extract_from_tree("sample_project", project_paths, metadata={"source": "smoke"}, file_contents=contents)
extractor_status = extractor.status()
package_engine = DNAPackageEngine(kernel)
package_import = package_engine.import_package(extracted)
package_export = package_engine.export_package(extracted["package_id"])
package_dependency_resolution = package_engine.resolve_dependencies(extracted["package_id"])
package_status = package_engine.status()
normalized_package = package_engine.packages[extracted["package_id"]]
extracted_kinds = {obj["kind"] for obj in extracted["runtime_objects"]}
model_engine = ModelEngine(kernel)
model_register = model_engine.register_from_runtime_objects(extracted["runtime_objects"])
gguf_models = model_engine.resolve_by_format("gguf")
onnx_models = model_engine.resolve_by_format("onnx")
safetensors_models = model_engine.resolve_by_format("safetensors")
load_gguf = model_engine.load_model("models/sample.gguf")
unload_gguf = model_engine.unload_model("models/sample.gguf")
model_status = model_engine.status()
with tempfile.TemporaryDirectory() as tmp:
    legacy_root = Path(tmp)
    (legacy_root / "agents").mkdir()
    (legacy_root / "agents" / "legacy_agent.py").write_text("class LegacyAgent:\n    pass\ndef run():\n    return True\n", encoding="utf-8")
    legacy_compile = compile_dna(None, str(legacy_root))

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
print(resource_allocate)
print(resource_rebalance)
print(resource_release)
print(resource_status)
print(object_snapshot)
print(object_update)
print(object_restore)
print(object_clone)
print(object_archive)
print(object_delete)
print(object_status)
print(extracted)
print(extractor_status)
print(package_import)
print(package_export)
print(package_dependency_resolution)
print(package_status)
print(model_register)
print(gguf_models)
print(onnx_models)
print(safetensors_models)
print(load_gguf)
print(unload_gguf)
print(model_status)
print(legacy_compile)

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
assert resource_allocate["ok"] is True
assert resource_rebalance["ok"] is True
assert resource_release["ok"] is True
assert resource_status["allocations"] == 0
assert resource_status["history"] >= 3
assert object_snapshot["ok"] is True
assert object_update["ok"] is True
assert object_restore["ok"] is True
assert object_clone["ok"] is True
assert object_archive["ok"] is True
assert object_delete["ok"] is True
assert object_status["snapshots"] >= 1
assert object_status["archived"] >= 1
assert object_status["history"] >= 6
assert extracted["ok"] is True
assert extracted["inventory"]["files"] >= 70
assert extracted["runtime_objects"]
assert len(extracted_kinds) >= 45
assert {"model", "agent", "workflow", "mission", "tool", "plugin", "connector", "provider", "api", "service", "mcp_server", "prompt", "policy", "dataset", "vectorstore", "database", "ui_screen", "dashboard", "deployment", "environment"}.issubset(extracted_kinds)
assert extracted["export_name"].endswith(".mdp")
assert extracted["semantic"]["content_files"] >= 8
assert extracted["semantic"]["routes"]
assert extracted["semantic"]["functions"]
assert extracted["semantic"]["environment_keys"]
assert extracted["semantic"]["api_clients"]
assert extracted["semantic"]["database_signals"]
assert "fastapi" in extracted["inventory"]["frameworks"]
assert any("api_routes" in obj["capabilities"] for obj in extracted["runtime_objects"])
assert any(edge["relation"] == "can_use_model" for edge in extracted["graph_edges"])
assert any(edge["relation"] == "governed_by" for edge in extracted["graph_edges"])
assert extractor_status["extractions"] >= 1
assert package_import["ok"] is True
assert package_import["package_runtime"]
assert package_import["manifest"]["schema_version"] == DNAPackageEngine.SCHEMA_VERSION
assert "gguf" in package_import["manifest"]["requirements"]["model_formats"]
assert "onnx" in package_import["manifest"]["requirements"]["model_formats"]
assert "safetensors" in package_import["manifest"]["requirements"]["model_formats"]
assert len(package_import["mounted_objects"]) >= len(extracted["runtime_objects"])
assert package_export["ok"] is True
assert package_export["export_name"].endswith(".mdp")
assert "\"manifest\"" in package_export["content"]
assert "\"package_graph\"" in package_export["content"]
assert package_dependency_resolution["ok"] is True
assert package_status["packages"] >= 1
assert package_status["package_objects"] >= 1
assert package_status["package_graph_edges"] >= len(normalized_package["runtime_objects"])
assert normalized_package["package_graph"]["node_count"] >= len(normalized_package["runtime_objects"])
assert normalized_package["package_graph"]["edge_count"] >= len(normalized_package["runtime_objects"])
assert model_register["ok"] is True
assert model_register["count"] >= 3
assert gguf_models["ok"] is True
assert onnx_models["ok"] is True
assert safetensors_models["ok"] is True
assert load_gguf["ok"] is True
assert unload_gguf["ok"] is True
assert model_status["models"] >= 3
assert model_status["formats"]["gguf"] >= 1
assert model_status["formats"]["onnx"] >= 1
assert model_status["formats"]["safetensors"] >= 1
assert legacy_compile["ok"] is True
assert legacy_compile["deprecated"] is True
assert legacy_compile["adapter"] == "DNAExtractorEngine"
assert legacy_compile["package"]["export_name"].endswith(".mdp")
