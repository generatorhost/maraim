# Maraim Kernel Unification Audit V1

## Decision

`main/maraim/kernel2` is the current Source of Truth.

`v1.2-execution-engine/maraim/kernel_v2` is an experimental branch and must not be merged wholesale into `main`.

## Evidence

- `main` default branch contains `maraim/kernel2`.
- `kernel2` exports `MaraimKernel` from `maraim/kernel2/__init__.py`.
- `kernel2/kernel.py` mounts real runtime families: dna, mcp, memory, scheduler, workflow, approval, agents, teams, chief, organization, task_executor.
- `scripts/kernel2_smoke.py` imports `MaraimKernel` from `maraim.kernel2`.
- `v1.2-execution-engine` is ahead of `main` by 292 commits and adds a parallel `maraim/kernel_v2` tree.

## Current kernel2 KEEP list

Keep these as canonical components:

- `maraim/kernel2/kernel.py` — canonical orchestration kernel.
- `maraim/kernel2/lifecycle.py` — kernel state lifecycle.
- `maraim/kernel2/service_container.py` — service registration.
- `maraim/kernel2/event_bus.py` — event bus with history and queue.
- `maraim/kernel2/registry.py` — runtime registry.
- `maraim/kernel2/runtime_manager.py` — runtime mount/start/stop/status.
- `maraim/kernel2/dna_runtime.py` — DNA runtime.
- `maraim/kernel2/mcp_runtime.py` — MCP runtime.
- `maraim/kernel2/memory_runtime.py` — memory runtime.
- `maraim/kernel2/scheduler_runtime.py` — scheduler runtime.
- `maraim/kernel2/workflow_runtime.py` — workflow runtime.
- `maraim/kernel2/approval_runtime.py` — approval runtime.
- `maraim/kernel2/agent_runtime.py` — agent runtime.
- `maraim/kernel2/team_runtime.py` — team runtime.
- `maraim/kernel2/chief_runtime.py` — chief runtime.
- `maraim/kernel2/organization_runtime.py` — organization runtime.
- `maraim/kernel2/task_executor_runtime.py` — task execution runtime.
- `scripts/kernel2_smoke.py` — canonical main smoke.

## kernel_v2 MERGE candidates

Merge selectively into `kernel2` only after adapter design review:

- Runtime Store concepts.
- Hot Reload concepts.
- Runtime Systems concepts for plugin/connector/provider/tool.
- Runtime Workspace Manager as a kernel2 workspace utility.
- Runtime Execution Gate as a kernel2 pre-run validator.
- SQLite Audit Adapter only if audit persistence is required.
- Audit Persistence Bridge only after kernel2 audit model exists.
- Persistence Health/Checkpoint/Recovery only after persistence is canonical.
- Source Operation Specs and Source Spec Validator only as review-only source import planning.
- Metrics, Trace, Report, Snapshot helpers if they map cleanly to kernel2 event bus.

## kernel_v2 REMOVE / do-not-merge-wholesale list

Do not merge these wholesale:

- Entire `maraim/kernel_v2` package as a second kernel.
- `scripts/kernel_v2_*` smoke sprawl as canonical CI.
- Phase/plus wrapper files that were created to work around editing constraints.
- Production bridge record-only phases as runtime capability.
- Real engine roadmap files as implementation.
- Duplicate EventBus, Lifecycle, RuntimeObject, RuntimeGraph, Scheduler, Planner, Execution layers if kernel2 already provides the canonical abstraction.

## Required next steps

1. Stop creating new `kernel_v2` code.
2. Keep `main/maraim/kernel2` as the only active kernel.
3. Create a small `kernel2_extensions` or direct `kernel2` modules only when they serve a real gap.
4. Migrate one useful concept at a time from `kernel_v2` into `kernel2`.
5. Keep one canonical smoke path: `scripts/kernel2_smoke.py` plus small targeted kernel2 smoke files.
6. Do not merge branch `v1.2-execution-engine` into `main` wholesale.
7. If local `C:\Users\DELL\Downloads\maraim_1_0_sprint1` contains newer code, upload it as a separate branch or zip for comparison before any merge.

## Final rule

There must be exactly one active kernel in the project: `maraim.kernel2.MaraimKernel`.
