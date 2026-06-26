# Maraim Modularization Policy

## Purpose

Large files must be split into focused modules to keep Maraim fast to load, easy to repair, and safe to evolve.

## Rule

No core Kernel v2 file should grow into a mixed responsibility file.

A file should normally contain one engine, one manager, one runtime family, or one narrow concern.

## Target Structure

```text
maraim/kernel_v2/
├── runtime_object.py
├── runtime_graph.py
├── dna_manager.py
├── lifecycle.py
├── resource_manager.py
├── object_manager.py
├── engines.py
├── event_bus.py
├── memory.py
├── planner.py
├── scheduler.py
├── execution.py
├── evolution.py
├── registry.py
├── diagnostics.py
└── __init__.py
```

## Current Direction

Managers that grow beyond a small foundation must move out of `engines.py` into dedicated files.

Examples already separated:

- `lifecycle.py`
- `resource_manager.py`
- `object_manager.py`

Next split candidates:

- Event Bus Engine
- Memory Engine
- Planner Engine
- Scheduler Engine
- Execution Engine
- Evolution Engine

## Design Constraints

- Keep public imports stable through `maraim/kernel_v2/__init__.py`.
- Do not break existing smoke tests.
- Do not duplicate logic.
- Do not create JSON/YAML registries.
- Do not hard-code Agent, Model, Plugin, Tool, or Swarm into the Kernel.
- Each module must remain RuntimeObject-compatible.

## Refactor Method

For every split:

1. Move one engine into its own file.
2. Keep the same class name.
3. Update imports in `engines.py` or `__init__.py`.
4. Run `python scripts/kernel_v2_smoke.py`.
5. Only then split the next engine.

## Success Criteria

A modularization step is valid only when:

- Smoke test passes.
- Public imports remain stable.
- No duplicate implementation exists.
- No behavior is removed.
- The Kernel remains small and stable.

## Principle

**Small files, stable interfaces, no duplicated logic, no Kernel type explosion.**
