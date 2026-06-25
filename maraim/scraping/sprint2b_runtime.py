import json

SPRINT2B_TABLES = [
    """CREATE TABLE IF NOT EXISTS scraping_adapters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        adapter_key TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS scraping_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER NOT NULL,
        status TEXT DEFAULT 'queued',
        reason TEXT,
        result TEXT,
        started_at TEXT,
        finished_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS scheduler_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_type TEXT NOT NULL,
        source_id INTEGER,
        interval_minutes INTEGER DEFAULT 60,
        status TEXT DEFAULT 'active',
        last_run_at TEXT,
        next_run_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )"""
]

SPRINT2B_TOOLS = [
    ("enqueue_source","Enqueue scraping source","Add source to scraping queue","{\"source_id\":\"number\"}"),
    ("run_queue","Run scraping queue","Process queued scraping jobs","{}"),
    ("run_scheduler","Run scheduler","Enqueue due scheduler jobs","{}")
]

def ensure_sprint2b(db):
    for stmt in SPRINT2B_TABLES:
        db.execute(stmt)
    for row in SPRINT2B_TOOLS:
        db.execute("INSERT OR IGNORE INTO mcp_tools(key,title,description,input_schema) VALUES(?,?,?,?)", row)
    try:
        from maraim.scraping.engine import register_builtin_adapters
        register_builtin_adapters(db)
    except Exception:
        pass
    db.commit()
    return {"ok": True}

def scraping_runtime_status(db):
    ensure_sprint2b(db)
    return {
        "adapters": [dict(r) for r in db.execute("SELECT * FROM scraping_adapters ORDER BY adapter_key").fetchall()],
        "queue": [dict(r) for r in db.execute("""
            SELECT q.*, s.name source_name, s.kind source_kind
            FROM scraping_queue q
            LEFT JOIN scraping_sources s ON q.source_id=s.id
            ORDER BY q.id DESC LIMIT 100
        """).fetchall()],
        "scheduler": [dict(r) for r in db.execute("""
            SELECT j.*, s.name source_name
            FROM scheduler_jobs j
            LEFT JOIN scraping_sources s ON j.source_id=s.id
            ORDER BY j.id DESC LIMIT 100
        """).fetchall()]
    }
