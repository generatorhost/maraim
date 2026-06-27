# Kernel v2 Canonical Gates

Branch: `v1.2-execution-engine`

## Official Gate

The official smoke entrypoint is:

```bash
python scripts/kernel_v2_all_smoke.py
```

This is the only public smoke gate name that should be used by developers, CI, and future documentation.

## Internal Gates

The following files are internal transition gates and should not be treated as public entrypoints:

- `scripts/kernel_v2_phase2_all_smoke.py`
- `scripts/kernel_v2_phase2_plus_smoke.py`
- `scripts/kernel_v2_phase2_plus2_smoke.py`
- `scripts/kernel_v2_phase2_plus3_smoke.py`
- `scripts/kernel_v2_phase2_plus4_smoke.py`

They remain only to avoid breaking previous work and to keep each phase auditable.

## Canonical Guard

Run:

```bash
python scripts/kernel_v2_canonical_guard.py
```

This checks that:

- `kernel_v2_all_smoke.py` calls the latest internal gate.
- Phase4 uses public API imports.
- Phase4 is exported from `maraim.kernel_v2`.
- Phase4 smoke does not use deep imports.

## Official CI

```text
.github/workflows/kernel-v2-canonical-smoke.yml
```
