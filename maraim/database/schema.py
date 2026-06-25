import sqlite3
from pathlib import Path

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        entity_type TEXT,
        entity_id TEXT,
        payload TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS dna_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT UNIQUE NOT NULL,
        kind TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        size_bytes INTEGER NOT NULL,
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS runtime_objects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER,
        object_type TEXT NOT NULL,
        object_key TEXT NOT NULL,
        title TEXT,
        payload TEXT,
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(object_type, object_key)
    )""",
    """CREATE TABLE IF NOT EXISTS chiefs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        purpose TEXT,
        status TEXT DEFAULT 'active'
    )""",
    """CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chief_key TEXT NOT NULL,
        key TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        purpose TEXT,
        status TEXT DEFAULT 'active'
    )""",
    """CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_key TEXT NOT NULL,
        key TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        role TEXT,
        status TEXT DEFAULT 'active'
    )""",
    """CREATE TABLE IF NOT EXISTS mcp_tools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        input_schema TEXT,
        enabled INTEGER DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS mcp_executions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tool_key TEXT NOT NULL,
        input TEXT,
        output TEXT,
        ok INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS scraping_sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        kind TEXT NOT NULL,
        url TEXT,
        keywords TEXT,
        enabled INTEGER DEFAULT 1,
        last_run_at TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER,
        external_key TEXT UNIQUE,
        platform TEXT,
        title TEXT NOT NULL,
        description TEXT,
        budget TEXT,
        url TEXT,
        status TEXT DEFAULT 'new',
        fit_score INTEGER DEFAULT 0,
        risk_score INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS project_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        model TEXT,
        summary TEXT,
        score INTEGER,
        risk TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        body TEXT NOT NULL,
        price TEXT,
        duration TEXT,
        status TEXT DEFAULT 'draft',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        route TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS model_registry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        provider TEXT NOT NULL,
        task TEXT NOT NULL,
        priority INTEGER DEFAULT 100,
        enabled INTEGER DEFAULT 1
    )"""
]

def connect(db_path):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def init_db(db_path):
    con = connect(db_path)
    cur = con.cursor()
    for stmt in SCHEMA:
        cur.execute(stmt)

    chiefs = [
        ("chief_freelance", "Chief Freelance Runtime", "يدير دورة البحث عن العمل من الاستخراج حتى التفاوض."),
        ("chief_ai", "Chief AI Runtime", "يوزع مهام التحليل والكتابة على النماذج."),
        ("chief_scraping", "Chief Scraping Runtime", "يدير مصادر scraping وproject inbox."),
        ("chief_governance", "Chief Governance Runtime", "يحافظ على الموافقات والسجلات والمخاطر.")
    ]
    teams = [
        ("chief_freelance","team_project_intake","Project Intake Team","استقبال وتصنيف المشاريع."),
        ("chief_freelance","team_proposal","Proposal Team","كتابة العروض وتسعيرها."),
        ("chief_ai","team_model_router","Model Router Team","اختيار النموذج المناسب."),
        ("chief_scraping","team_collectors","Collectors Team","تشغيل المصادر وجمع البيانات."),
        ("chief_governance","team_approval","Approval Team","قوائم الموافقة والتدقيق.")
    ]
    agents = [
        ("team_project_intake","agent_project_scorer","Project Scorer","score"),
        ("team_proposal","agent_proposal_writer","Proposal Writer","write"),
        ("team_model_router","agent_ollama_router","Ollama Router","route"),
        ("team_collectors","agent_source_runner","Source Runner","collect"),
        ("team_approval","agent_approval_guard","Approval Guard","approve")
    ]
    models = [
        ("phi3:mini","ollama","fast",10),
        ("llama3.2:3b","ollama","analysis",20),
        ("llama3:latest","ollama","proposal",30),
        ("deepseek-coder:6.7b","ollama","code",40),
        ("qwen2.5-coder:1.5b","ollama","code_fast",15),
        ("nomic-embed-text:latest","ollama","embedding",5)
    ]
    tools = [
        ("compile_dna","Compile DNA","Compile source DNA files into runtime objects","{}"),
        ("run_source","Run scraping source","Collect projects from a source","{\"source_id\":\"number\"}"),
        ("analyze_project","Analyze project","Analyze a project with local AI/fallback","{\"project_id\":\"number\"}"),
        ("generate_proposal","Generate proposal","Generate proposal draft","{\"project_id\":\"number\"}"),
        ("list_files","List files","List safe project files","{\"path\":\"string\"}")
    ]

    for key,title,purpose in chiefs:
        cur.execute("INSERT OR IGNORE INTO chiefs(key,title,purpose) VALUES(?,?,?)", (key,title,purpose))
    for chief,key,title,purpose in teams:
        cur.execute("INSERT OR IGNORE INTO teams(chief_key,key,title,purpose) VALUES(?,?,?,?)", (chief,key,title,purpose))
    for team,key,title,role in agents:
        cur.execute("INSERT OR IGNORE INTO agents(team_key,key,title,role) VALUES(?,?,?,?)", (team,key,title,role))
    for key,provider,task,priority in models:
        cur.execute("INSERT OR IGNORE INTO model_registry(key,provider,task,priority) VALUES(?,?,?,?)", (key,provider,task,priority))
    for row in tools:
        cur.execute("INSERT OR IGNORE INTO mcp_tools(key,title,description,input_schema) VALUES(?,?,?,?)", row)

    if cur.execute("SELECT COUNT(*) c FROM scraping_sources").fetchone()["c"] == 0:
        cur.execute("INSERT INTO scraping_sources(name,kind,url,keywords) VALUES(?,?,?,?)",
                    ("Sample Freelance Feed","sample","","python,ai,automation,dashboard"))
    con.commit()
    return con
