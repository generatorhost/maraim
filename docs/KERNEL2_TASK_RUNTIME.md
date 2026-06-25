# Kernel 2 Task Runtime

Adds the first task-oriented OS core.

## Added

- MemoryRuntime
- SchedulerRuntime
- WorkflowRuntime
- MCP tools:
  - workflow.run
  - memory.status
  - scheduler.status
- Workflow DNA: project-acquisition
- Smoke test

## Test

```powershell
python scripts/kernel2_task_runtime_smoke.py
```

Expected:

```text
MARAIM_KERNEL2_TASK_RUNTIME_SMOKE_OK
```
