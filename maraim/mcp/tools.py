import json
from pathlib import Path
from maraim.dna.compiler import compile_dna
from maraim.scraping.engine import run_source
from maraim.runtime.freelance import analyze_project, generate_proposal

SAFE_ROOT = Path.cwd().resolve()

def run_tool(db, key, params):
    try:
        if key == "compile_dna":
            result = compile_dna(db, Path("dna/source"))
        elif key == "run_source":
            result = run_source(db, int(params.get("source_id", 1)))
        elif key == "analyze_project":
            result = analyze_project(db, int(params["project_id"]))
        elif key == "generate_proposal":
            result = generate_proposal(db, int(params["project_id"]))
        elif key == "list_files":
            p = (SAFE_ROOT / params.get("path",".")).resolve()
            if not str(p).startswith(str(SAFE_ROOT)):
                raise ValueError("unsafe_path")
            result = {"ok": True, "files": [x.name for x in p.iterdir()][:200]}
        else:
            result = {"ok": False, "error": "unknown_tool"}
        ok = bool(result.get("ok", True))
    except Exception as e:
        result = {"ok": False, "error": str(e)}
        ok = False
    db.execute("INSERT INTO mcp_executions(tool_key,input,output,ok) VALUES(?,?,?,?)",
               (key, json.dumps(params, ensure_ascii=False), json.dumps(result, ensure_ascii=False), 1 if ok else 0))
    db.commit()
    return result
