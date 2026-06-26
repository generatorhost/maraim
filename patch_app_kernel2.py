from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

if "from maraim.kernel2.app_bridge import" not in s:
    s = s.replace(
        "from maraim.ai.ollama_router import generate\n",
        "from maraim.ai.ollama_router import generate\nfrom maraim.kernel2.app_bridge import kernel_status, route_task, run_workflow\n"
    )

if '"kernel2": kernel_status(),' not in s:
    s = s.replace(
        '"db": DB_PATH,\n',
        '"db": DB_PATH,\n                "kernel2": kernel_status(),\n',
        1
    )

if 'if path == "/api/kernel2/status":' not in s:
    s = s.replace(
        '        if path == "/api/status":\n',
        '        if path == "/api/kernel2/status":\n            self.send_json(kernel_status()); return\n\n        if path == "/api/status":\n',
        1
    )

if 'if path == "/api/kernel2/route":' not in s:
    s = s.replace(
        '        if path == "/api/dna/compile":\n',
        '        if path == "/api/kernel2/route":\n            self.send_json(route_task(body)); return\n        if path == "/api/kernel2/workflow":\n            self.send_json(run_workflow(body.get("workflow_id", "project-acquisition"), body)); return\n\n        if path == "/api/dna/compile":\n',
        1
    )

s = s.replace(
    'maraim 1.0 sprint2b running at',
    'maraim 1.0 kernel2 bridge running at'
)

p.write_text(s, encoding="utf-8")
