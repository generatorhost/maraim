# Local Sprint1 Intake Audit V1

Uploaded archive reviewed: `maraim_1_0_sprint1 (2)(1).zip`

## Summary

The archive is a full Git working copy, not just a source snapshot.

The active branch inside the archive is:

```text
v1.2-execution-engine
```

The local repository branches inside the archive include:

```text
main
next-phase
v1.2-execution-engine
origin/main
origin/v1.2-execution-engine
```

## File inventory excluding `.git` and `__pycache__`

```text
Total files: 75
Python files: 55
SQLite files: 3
```

Top-level distribution:

```text
.gitignore: 1
README.md: 1
SMOKE_TEST_RESULT.txt: 1
app.py: 1
data: 3
dna: 9
docs: 6
maraim: 45
public: 1
scripts: 5
start_maraim_linux.sh: 1
start_maraim_windows.bat: 1
```

SQLite files found:

```text
data/direct.sqlite
data/test2.sqlite
data/x2.sqlite
```

## Working tree finding

`git status` inside the uploaded archive shows 38 modified files.

However, when whitespace and end-of-line differences are ignored, there are no semantic diffs detected by:

```text
git diff --ignore-space-at-eol
git diff -w
```

Therefore, the visible local modifications are treated as line-ending/format noise unless a future manual diff proves otherwise.

## Smoke checks executed from the archive

The following local smokes passed:

```text
python scripts/kernel2_smoke.py
python scripts/kernel2_task_runtime_smoke.py
python scripts/kernel2_app_bridge_smoke.py
```

Kernel2 smoke result confirmed:

- Kernel reached `running` state.
- Services registered: agent_runtime, approval_runtime, chief_runtime, dna_runtime, event_bus, mcp_runtime, memory_runtime, organization_runtime, registry, runtime_manager, scheduler_runtime, task_executor_runtime, team_runtime, workflow_runtime.
- Registry counts included: 3 agents, 1 chief, 3 teams, 2 workflows.
- MCP tools included status, DNA reload, chief route task, workflow run, memory status, scheduler status, approval create, scheduler run next, scheduler run all.

## Intake decision

The uploaded local archive does not replace `main/maraim/kernel2`.

The correct decision remains:

```text
Source of Truth: main/maraim/kernel2
```

The local archive is useful as evidence that kernel2 smoke/task/app bridge functionality already exists and passes locally, but it should not be treated as an independent source of truth.

## Merge policy

Do not copy the archive wholesale into GitHub.

Do not merge the embedded `v1.2-execution-engine` branch wholesale.

Allowed next actions:

1. Normalize line endings using repository policy.
2. Keep `kernel2` as canonical.
3. Compare only specific files when there is a real semantic difference.
4. Selectively migrate useful `kernel_v2` concepts into `kernel2` after design review.
5. Ignore `.git`, `__pycache__`, and SQLite runtime data files unless explicitly needed for test fixtures.

## Completion estimate after this intake

```text
Kernel2 foundation: 70%
Task/runtime society: 45%
App bridge: 35%
Production-ready execution: 20%
Whole project: 40%
```

This percentage is lower than earlier optimistic estimates because the project is now judged against the unified source of truth only, not against parallel experimental branches.
