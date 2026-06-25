import json, os, urllib.parse
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

from maraim.database.schema import init_db
from maraim.dna.compiler import compile_dna
from maraim.scraping.engine import run_source
from maraim.runtime.freelance import analyze_project, generate_proposal
from maraim.mcp.tools import run_tool
from maraim.ai.ollama_router import generate

DB_PATH = "data/maraim.sqlite"
db = init_db(DB_PATH)

def rows(sql, params=()):
    return [dict(r) for r in db.execute(sql, params).fetchall()]

def row(sql, params=()):
    r = db.execute(sql, params).fetchone()
    return dict(r) if r else None

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
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            self.send_json({
                "ok": True,
                "name": "maraim",
                "version": "1.0-sprint1",
                "db": DB_PATH,
                "counts": {
                    "projects": row("SELECT COUNT(*) c FROM projects")["c"],
                    "runtime_objects": row("SELECT COUNT(*) c FROM runtime_objects")["c"],
                    "mcp_tools": row("SELECT COUNT(*) c FROM mcp_tools")["c"],
                    "proposals": row("SELECT COUNT(*) c FROM proposals")["c"],
                    "approvals": row("SELECT COUNT(*) c FROM approvals")["c"]
                }
            }); return

        if path == "/api/projects":
            self.send_json(rows("SELECT * FROM projects ORDER BY fit_score DESC, id DESC LIMIT 200")); return
        if path == "/api/sources":
            self.send_json(rows("SELECT * FROM scraping_sources ORDER BY id")); return
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

        if path == "/api/dna/compile":
            self.send_json(compile_dna(db, Path("dna/source"))); return
        if path == "/api/sources/run":
            self.send_json(run_source(db, int(body.get("source_id", 1)))); return
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
            if "scrap" in low or "استخراج" in msg or "اجلب" in msg:
                out = run_source(db, 1)
                reply = f"تم تشغيل مصدر المشاريع. النتيجة: {out}"
                route = "scraping"
            elif "proposal" in low or "عرض" in msg:
                projects = rows("SELECT id,title FROM projects ORDER BY fit_score DESC LIMIT 1")
                if projects:
                    out = generate_proposal(db, projects[0]["id"])
                    reply = out.get("body", str(out))
                else:
                    reply = "لا توجد مشاريع في Project Inbox. شغّل Scraping أولًا."
                route = "proposal"
            elif "analy" in low or "حلل" in msg:
                projects = rows("SELECT id,title FROM projects ORDER BY fit_score DESC LIMIT 1")
                if projects:
                    out = analyze_project(db, projects[0]["id"])
                    reply = out.get("analysis", str(out))
                else:
                    reply = "لا توجد مشاريع لتحليلها. شغّل Scraping أولًا."
                route = "analysis"
            else:
                out = generate(msg, task="fast")
                reply = out.get("response")
                route = "chat"
            db.execute("INSERT INTO chat_messages(role,content,route) VALUES('assistant',?,?)", (reply, route))
            db.commit()
            self.send_json({"ok": True, "route": route, "response": reply}); return

        self.send_json({"ok": False, "error": "not_found"}, 404)

if __name__ == "__main__":
    port = int(os.environ.get("MARAIM_PORT", "8790"))
    print(f"maraim 1.0 sprint1 running at http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
