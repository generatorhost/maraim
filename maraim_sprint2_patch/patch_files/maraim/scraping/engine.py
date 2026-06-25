import hashlib
import json
from maraim.scraping.adapters import get_adapter, adapter_manifest

def key_for(item):
    base = (item.get("platform","") + "|" + item.get("title","") + "|" + item.get("url","")).encode("utf-8", errors="ignore")
    return hashlib.sha256(base).hexdigest()

def score_project(title, description, keywords):
    text = (title + " " + description).lower()
    kw = [k.strip().lower() for k in (keywords or "").split(",") if k.strip()]
    fit = sum(20 for k in kw if k in text)
    if any(x in text for x in ["ai", "automation", "python", "dashboard", "scraping", "backend", "ollama"]):
        fit += 25
    if any(x in text for x in ["cheap", "simple", "$5", "$10"]):
        fit -= 20
    return max(0, min(100, fit))

def register_builtin_adapters(db):
    for adapter in adapter_manifest():
        db.execute("INSERT OR IGNORE INTO scraping_adapters(adapter_key,title,status) VALUES(?,?,?)", (adapter["key"], adapter["title"], "active"))
    db.commit()

def enqueue_source(db, source_id, reason="manual"):
    cur = db.execute("INSERT INTO scraping_queue(source_id,status,reason) VALUES(?,?,?)", (source_id, "queued", reason))
    db.commit()
    return {"ok": True, "queue_id": cur.lastrowid}

def queue_status(db):
    return [dict(r) for r in db.execute("""
        SELECT q.*, s.name source_name, s.kind source_kind
        FROM scraping_queue q LEFT JOIN scraping_sources s ON q.source_id=s.id
        ORDER BY q.id DESC LIMIT 100
    """).fetchall()]

def insert_project(db, source_id, item, keywords=""):
    external_key = key_for(item)
    score = score_project(item.get("title",""), item.get("description",""), keywords)
    db.execute(
        """INSERT OR IGNORE INTO projects(source_id,external_key,platform,title,description,budget,url,fit_score,risk_score)
           VALUES(?,?,?,?,?,?,?,?,?)""",
        (source_id, external_key, item.get("platform","sample"), item.get("title","Untitled"),
         item.get("description",""), item.get("budget",""), item.get("url",""), score, 100-score)
    )
    db.commit()
    return external_key

def run_source(db, source_id):
    src = db.execute("SELECT * FROM scraping_sources WHERE id=?", (source_id,)).fetchone()
    if not src:
        return {"ok": False, "error": "source_not_found"}
    source = dict(src)
    adapter = get_adapter(source.get("kind") or "sample")
    try:
        items = adapter.collect(source)
    except Exception as e:
        db.execute("INSERT INTO audit_logs(event_type,entity_type,entity_id,payload) VALUES(?,?,?,?)",
                   ("scraping_error", "source", str(source_id), json.dumps({"error": str(e)}, ensure_ascii=False)))
        db.commit()
        return {"ok": False, "error": str(e)}
    before = db.execute("SELECT COUNT(*) c FROM projects").fetchone()["c"]
    for item in items:
        insert_project(db, source_id, item, src["keywords"] or "")
    after = db.execute("SELECT COUNT(*) c FROM projects").fetchone()["c"]
    db.execute("UPDATE scraping_sources SET last_run_at=CURRENT_TIMESTAMP WHERE id=?", (source_id,))
    db.execute("INSERT INTO audit_logs(event_type,entity_type,entity_id,payload) VALUES(?,?,?,?)",
               ("scraping_source_run", "source", str(source_id), json.dumps({"found": len(items), "inserted": after-before}, ensure_ascii=False)))
    db.commit()
    return {"ok": True, "found": len(items), "inserted": after-before}

def run_queue_once(db, limit=10):
    jobs = db.execute("SELECT * FROM scraping_queue WHERE status='queued' ORDER BY id LIMIT ?", (limit,)).fetchall()
    results = []
    for job in jobs:
        db.execute("UPDATE scraping_queue SET status='running', started_at=CURRENT_TIMESTAMP WHERE id=?", (job["id"],))
        db.commit()
        result = run_source(db, job["source_id"])
        status = "done" if result.get("ok") else "failed"
        db.execute("UPDATE scraping_queue SET status=?, finished_at=CURRENT_TIMESTAMP, result=? WHERE id=?",
                   (status, json.dumps(result, ensure_ascii=False), job["id"]))
        db.commit()
        results.append({"queue_id": job["id"], "result": result})
    return {"ok": True, "processed": len(results), "results": results}

def create_scheduler_job(db, source_id, interval_minutes=60):
    cur = db.execute(
        """INSERT INTO scheduler_jobs(job_type,source_id,interval_minutes,status,next_run_at)
           VALUES('scraping_source',?,?, 'active', CURRENT_TIMESTAMP)""",
        (source_id, interval_minutes)
    )
    db.commit()
    return {"ok": True, "job_id": cur.lastrowid}

def scheduler_status(db):
    return [dict(r) for r in db.execute("""
        SELECT j.*, s.name source_name
        FROM scheduler_jobs j LEFT JOIN scraping_sources s ON j.source_id=s.id
        ORDER BY j.id DESC LIMIT 100
    """).fetchall()]

def run_due_scheduler(db):
    jobs = db.execute("""
        SELECT * FROM scheduler_jobs
        WHERE status='active'
          AND (next_run_at IS NULL OR datetime(next_run_at) <= datetime('now'))
        ORDER BY id LIMIT 20
    """).fetchall()
    enqueued = []
    for job in jobs:
        q = enqueue_source(db, job["source_id"], reason=f"scheduler:{job['id']}")
        db.execute(
            "UPDATE scheduler_jobs SET last_run_at=CURRENT_TIMESTAMP, next_run_at=datetime('now', '+' || interval_minutes || ' minutes') WHERE id=?",
            (job["id"],)
        )
        db.commit()
        enqueued.append(q)
    return {"ok": True, "due_jobs": len(jobs), "enqueued": enqueued}
