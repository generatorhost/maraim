# Kernel v2 Canonical Gates

Branch: `v1.2-execution-engine`

## Official CI Gate

The official single command for Kernel v2 validation is:

```bash
python scripts/kernel_v2_ci_gate.py
```

This command runs:

1. `scripts/kernel_v2_canonical_guard.py`
2. `scripts/kernel_v2_all_smoke.py`

## Official Smoke Gate

The official smoke entrypoint is:

```bash
python scripts/kernel_v2_all_smoke.py
```

`kernel_v2_all_smoke.py` directly lists and runs every real smoke test. Transitional `plus` gates must not be used as public entrypoints or CI entrypoints.

## Canonical Guard

Run:

```bash
python scripts/kernel_v2_canonical_guard.py
```

This checks that:

- `kernel_v2_all_smoke.py` contains every required real smoke test.
- `kernel_v2_all_smoke.py` does not depend on transitional plus gates.
- Phase4 uses public API imports.
- Phase4 is exported from `maraim.kernel_v2`.
- Phase4 smoke does not use deep imports.
- Real adapters foundation is exported from `maraim.kernel_v2`.

## Official CI

```text
.github/workflows/kernel-v2-canonical-smoke.yml
```

Only the canonical workflow should run on push or pull request for Kernel v2 validation.
