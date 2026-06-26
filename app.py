import json, os, urllib.parse
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

from maraim.database.schema import init_db
from maraim.dna.compiler import compile_dna
from maraim.scraping.engine import run_source, enqueue_source, run_queue_once, create_scheduler_job, run_due_scheduler
from maraim.scraping.sprint2b_runtime import ensure_sprint2b, scraping_runtime_status
from maraim.runtime.freelance import analyze_project, generate_proposal
from maraim.mcp.tools import run_tool
from maraim.ai.ollama_router import generate
from maraim.kernel2.app_bridge import kernel_status, route_task, run_workflow

DB_PATH = "data/maraim.sqlite"
db = init_db(DB_PATH)
ensure_sprint2b(db)

def rows(sql, params=()):
    return [dict(r) for r in db.execute(sql, params).fetchall()]

def row(sql, params=()):
    r = db.execute(sql, params).fetchone()
    return dict(r) if r else None

def safe_count(table):
    try:
        return row(f"SELECT COUNT(*) c FROM {table}")["c"]
    except Exception:
        return 0

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="public", **kwargs)

    def send_json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self):
        n = int(self.headers.get("Content-Length", "0"))
        if n <= 0:
            return {}
        return json.loads(self.rfile.read(n).decode("utf-8"))

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        if path == "/api/kernel2/status":
            self.send_json(kernel_status()); return

        if path == "/api/status":
            self.send_json({
                "ok": True,
                "name": "maraim",
                "version": "1.0-sprint2b",
                "db": DB_PATH,
                "kernel2": kernel_status(),
                "counts": {
                    "projects": safe_count("projects"),
                    "runtime_objects": safe_count("runtime_objects"),
                    "mcp_tools": safe_count("mcp_tools"),
                    "proposals": safe_count("proposals"),
                    "approvals": safe_count("approvals"),
                    "scraping_queue": safe_count("scraping_queue"),
                    "scheduler_jobs": safe_count("scheduler_jobs"),
                    "scraping_adapters": safe_count("scraping_adapters")
                }
            }); return

        if path == "/api/projects":
            self.send_json(rows("SELECT * FROM projects ORDER BY fit_score DESC, id DESC LIMIT 200")); return
        if path == "/api/sources":
            self.send_json(rows("SELECT * FROM scraping_sources ORDER BY id")); return
        if path == "/api/scraping/runtime":
            self.send_json(scraping_runtime_status(db)); return
        if path == "/api/mcp":
            self.send_json({"tools": rows("SELECT * FROM mcp_tools ORDER BY key"), "executions": rows("SELECT * FROM mcp_executions ORDER BY id DESC LIMIT 50")}); return
        if path == "/api/approvals":
            self.send_json(rows("""SELECT a.*, p.body, pr.title project_title FROM approvals a
                                   LEFT JOIN proposals p ON a.entity_id=p.id AND a.entity_type='proposal'
                                   LEFT JOIN projects pr ON p.project_id=pr.id
                                   ORDER BY a.id DESC LIMIT 100""")); return
        if path == "/api/audit":
            self.send_json(rows("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100")); return
        return super().do_GET()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        body = self.read_json()

        if path == "/api/kernel2/route":
            self.send_json(route_task(body)); return
        if path == "/api/kernel2/workflow":
            self.send_json(run_workflow(body.get("workflow_id", "project-acquisition"), body)); return

        if path == "/api/dna/compile":
            self.send_json(compile_dna(db, Path("dna/source"))); return
        if path == "/api/sources/run":
            self.send_json(run_source(db, int(body.get("source_id", 1)))); return
        if path == "/api/scraping/enqueue":
            self.send_json(enqueue_source(db, int(body.get("source_id", 1)), body.get("reason", "manual"))); return
        if path == "/api/scraping/run_queue":
            self.send_json(run_queue_once(db, int(body.get("limit", 10)))); return
        if path == "/api/scheduler/create":
            self.send_json(create_scheduler_job(db, int(body.get("source_id", 1)), int(body.get("interval_minutes", 60)))); return
        if path == "/api/scheduler/run_due":
            self.send_json(run_due_scheduler(db)); return
        if path == "/api/projects/analyze":
            self.send_json(analyze_project(db, int(body["project_id"]))); return
        if path == "/api/projects/proposal":
            self.send_json(generate_proposal(db, int(body["project_id"]))); return
        if path == "/api/mcp/run":
            self.send_json(run_tool(db, body.get("tool_key"), body.get("params", {}))); return
        if path == "/api/chat":
            msg = body.get("message","")
            db.execute("INSERT INTO chat_messages(role,content,route) VALUES('user',?,?)", (msg, "incoming"))
            low = msg.lower()
            if "queue" in low or "طابور" in msg:
                out = enqueue_source(db, 1, "chat")
                reply = f"تمت إضافة مصدر المشاريع إلى Queue: {out}"
                route = "scraping_queue"
            elif "scheduler" in low or "جدول" in msg:
                out = run_due_scheduler(db)
                reply = f"تم تشغيل Scheduler: {out}"
                route = "scheduler"
            elif "scrap" in low or "استخراج" in msg or "اجلب" in msg:
                out = run_source(db, 1)
                reply = f"تم تشغيل مصدر المشاريع. النتيجة: {out}"
                route = "scraping"
            elif "proposal" in low or "عرض" in msg:
                projects = rows("SELECT id,title FROM projects ORDER BY fit_score DESC LIMIT 1")
                reply = generate_proposal(db, projects[0]["id"]).get("body") if projects else "لا توجد مشاريع في Project Inbox. شغّل Scraping أولًا."
                route = "proposal"
            elif "analy" in low or "حلل" in msg:
                projects = rows("SELECT id,title FROM projects ORDER BY fit_score DESC LIMIT 1")
                reply = analyze_project(db, projects[0]["id"]).get("analysis") if projects else "لا توجد مشاريع لتحليلها. شغّل Scraping أولًا."
                route = "analysis"
            else:
                reply = generate(msg, task="fast").get("response")
                route = "chat"
            db.execute("INSERT INTO chat_messages(role,content,route) VALUES('assistant',?,?)", (reply, route))
            db.commit()
            self.send_json({"ok": True, "route": route, "response": reply}); return

        self.send_json({"ok": False, "error": "not_found"}, 404)

if __name__ == "__main__":
    port = int(os.environ.get("MARAIM_PORT", "8790"))
    print(f"maraim 1.0 kernel2 bridge running at http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
