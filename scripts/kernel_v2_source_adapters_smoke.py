import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from maraim.kernel_v2 import ArchiveSourceAdapter, FolderSourceAdapter, GitSourceAdapter, KernelV2

kernel = KernelV2(dna_root="dna")

git_adapter = GitSourceAdapter(kernel)
archive_adapter = ArchiveSourceAdapter(kernel)
folder_adapter = FolderSourceAdapter(kernel)

git_result = git_adapter.prepare_git_url(
    "https://example.com/repo.git",
    branch="feature/runtime",
    paths=[
        "plugins/freelance_plugin.py",
        "connectors/source_connector.py",
        "providers/language_provider.py",
    ],
    file_contents={
        "plugins/freelance_plugin.py": "def prepare(project):\n    return project\n",
        "connectors/source_connector.py": "def collect(source):\n    return source\n",
        "providers/language_provider.py": "def complete(prompt):\n    return prompt\n",
    },
)

archive_result = archive_adapter.prepare_archive(
    "sample.mdp.zip",
    paths=["tools/proposal_tool.py", "models/sample.gguf"],
    file_contents={"tools/proposal_tool.py": "def draft(project):\n    return project\n"},
)

folder_result = folder_adapter.prepare_folder(
    "sample_folder",
    paths=["agents/research_agent.py", "workflows/research_workflow.py"],
    file_contents={"agents/research_agent.py": "class ResearchAgent:\n    pass\n"},
)

print("MARAIM_SOURCE_ADAPTERS_SMOKE_OK")
print(git_adapter.status())
print(archive_adapter.status())
print(folder_adapter.status())

assert git_result["ok"] is True
assert archive_result["ok"] is True
assert folder_result["ok"] is True
assert git_result["manifest"]["source_type"] == "git"
assert archive_result["manifest"]["source_type"] == "archive"
assert folder_result["manifest"]["source_type"] == "folder"
assert git_result["package"]["ok"] is True
assert archive_result["package"]["ok"] is True
assert folder_result["package"]["ok"] is True
assert {"plugin", "connector", "provider"}.issubset({obj["kind"] for obj in git_result["package"]["runtime_objects"]})
assert {"tool", "model"}.issubset({obj["kind"] for obj in archive_result["package"]["runtime_objects"]})
assert {"agent", "workflow"}.issubset({obj["kind"] for obj in folder_result["package"]["runtime_objects"]})
assert git_adapter.status()["imports"] == 1
assert archive_adapter.status()["imports"] == 1
assert folder_adapter.status()["imports"] == 1
