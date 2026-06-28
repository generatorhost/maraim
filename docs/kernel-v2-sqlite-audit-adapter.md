# Kernel v2 SQLite Audit Adapter

Branch: `v1.2-execution-engine`

## Decision

SQLite is enabled as an optional local persistence adapter for audit events only.

It does not replace RuntimeStore, RuntimeStorageEngine, RuntimeGraph, or kernel state.

## Public API

```python
from maraim.kernel_v2 import SQLiteAuditAdapter
```

## CI Smoke

```bash
python scripts/kernel_v2_sqlite_audit_adapter_smoke.py
```

The smoke uses `:memory:` so CI does not create repository files.

## Scope

Allowed:

- audit event persistence
- local SQLite database path supplied by caller
- query/list/status for audit events

Not allowed here:

- runtime object persistence
- graph persistence
- adapter execution state
- model storage
- replacing RuntimeStore
