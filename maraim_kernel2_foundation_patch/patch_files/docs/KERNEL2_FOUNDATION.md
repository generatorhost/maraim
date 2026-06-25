# Maraim Kernel 2.0 Foundation

This patch introduces the new operating-kernel foundation without removing the existing app.

## Included

- Boot lifecycle
- Service container
- Event bus
- Runtime registry
- Runtime manager
- Direct DNA Runtime interpreter
- MCP Runtime skeleton
- Smoke script

## Test

```powershell
python scripts/kernel2_smoke.py
```

Expected:

```text
MARAIM_KERNEL2_SMOKE_OK
```

## Commit

```powershell
git add .
git commit -m "Add kernel 2 foundation"
git push
```
