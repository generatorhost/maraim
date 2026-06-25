import json, hashlib
from pathlib import Path

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def classify(path, text):
    low = (str(path) + "\n" + text[:2000]).lower()
    rules = [
        ("chief", ["chief", "رئيس"]),
        ("team", ["team", "فريق"]),
        ("agent", ["agent", "وكيل"]),
        ("skill", ["skill", "مهارة"]),
        ("capability", ["capability", "قدرة"]),
        ("workflow", ["workflow", "pipeline", "مسار"]),
        ("knowledge", ["knowledge", "rag", "memory", "معرفة"]),
        ("runtime", ["runtime", "kernel", "تنفيذ"]),
        ("scraping", ["scraping", "crawler", "scraper", "استخراج"])
    ]
    for typ, terms in rules:
        if any(t in low for t in terms):
            return typ
    return "document"

def compile_dna(db, source_dir):
    source_dir = Path(source_dir)
    source_dir.mkdir(parents=True, exist_ok=True)
    compiled = 0
    scanned = 0
    for p in source_dir.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in [".json", ".md", ".txt", ".jsonl"]:
            continue
        scanned += 1
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        h = sha256_file(p)
        kind = p.suffix.lower().lstrip(".")
        db.execute(
            "INSERT OR IGNORE INTO dna_sources(path,kind,sha256,size_bytes) VALUES(?,?,?,?)",
            (str(p), kind, h, p.stat().st_size)
        )
        source_id = db.execute("SELECT id FROM dna_sources WHERE path=?", (str(p),)).fetchone()["id"]
        object_type = classify(p, text)
        object_key = f"{object_type}:{h[:16]}"
        title = p.stem[:200]
        payload = json.dumps({"path": str(p), "excerpt": text[:4000]}, ensure_ascii=False)
        db.execute(
            """INSERT OR REPLACE INTO runtime_objects(source_id,object_type,object_key,title,payload,status)
               VALUES(?,?,?,?,?,'active')""",
            (source_id, object_type, object_key, title, payload)
        )
        compiled += 1
    db.commit()
    return {"ok": True, "scanned": scanned, "compiled": compiled}
