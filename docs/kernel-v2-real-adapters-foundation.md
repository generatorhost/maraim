# Kernel v2 Real Adapters Foundation

Branch: `v1.2-execution-engine`

## Status

Real adapters are currently foundation plans only.

They define safe contracts for:

- Git adapter planning
- Archive adapter planning
- Folder adapter planning

They do not perform real clone, archive extraction, folder scanning, network access, subprocess execution, filesystem writes, or database writes.

## Public API

```python
from maraim.kernel_v2 import RealAdapterFoundation
```

## Smoke

```bash
python scripts/kernel_v2_real_adapters_foundation_smoke.py
```

The canonical gate also includes this smoke:

```bash
python scripts/kernel_v2_all_smoke.py
```

## Next Promotion Rule

Real Git/Archive/Folder operations must not be implemented until sandbox and permission enforcement are production-ready.
