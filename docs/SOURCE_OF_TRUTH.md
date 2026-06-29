# Maraim Source of Truth

The active source of truth is:

```text
main/maraim/kernel2
```

The canonical kernel import is:

```python
from maraim.kernel2 import MaraimKernel
```

Rules:

1. Do not create a second active kernel package.
2. Do not merge `maraim/kernel_v2` wholesale into `main`.
3. Use `kernel_v2` only as a reference branch for selective migration.
4. Keep `scripts/kernel2_smoke.py` as the canonical smoke entrypoint on `main`.
5. New runtime work must extend `kernel2` or clearly documented kernel2 utilities.
6. Local folders such as `maraim_1_0_sprint1` are not source of truth until uploaded and audited.
