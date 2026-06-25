import hashlib
from html.parser import HTMLParser

SAMPLE_PROJECTS = [
    {"platform":"sample","title":"Build AI dashboard for freelance project tracking","description":"Need a dashboard that collects freelance jobs, analyzes them, and generates proposals.","budget":"$300-$700","url":"https://example.local/project/ai-dashboard"},
    {"platform":"sample","title":"Python automation script for web data extraction","description":"Looking for a Python developer to automate extraction of public web data into CSV.","budget":"$150-$400","url":"https://example.local/project/python-scraping"},
    {"platform":"sample","title":"React landing page only","description":"Simple UI landing page, no AI, no backend.","budget":"$50","url":"https://example.local/project/simple-ui"}
]

class LinkTitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.in_a = False
        self.href = None
        self.text = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.in_a = True
            self.href = dict(attrs).get("href")
            self.text = []
    def handle_data(self, data):
        if self.in_a:
            self.text.append(data)
    def handle_endtag(self, tag):
        if tag == "a" and self.in_a:
            title = " ".join(" ".join(self.text).split())
            if title and len(title) > 12:
                self.items.append({"title": title[:220], "url": self.href or "", "description": title})
            self.in_a = False

def key_for(item):
    base = (item.get("platform","") + "|" + item.get("title","") + "|" + item.get("url","")).encode("utf-8", errors="ignore")
    return hashlib.sha256(base).hexdigest()

def score_project(title, description, keywords):
    text = (title + " " + description).lower()
    kw = [k.strip().lower() for k in (keywords or "").split(",") if k.strip()]
    fit = sum(20 for k in kw if k in text)
    if any(x in text for x in ["ai", "automation", "python", "dashboard", "scraping", "backend"]):
        fit += 25
    if any(x in text for x in ["cheap", "simple", "$5", "$10"]):
        fit -= 20
    return max(0, min(100, fit))

def insert_project(db, source_id, item, keywords=""):
    external_key = key_for(item)
    score = score_project(item.get("title",""), item.get("description",""), keywords)
    risk = 100 - score
    db.execute(
        """INSERT OR IGNORE INTO projects(source_id,external_key,platform,title,description,budget,url,fit_score,risk_score)
           VALUES(?,?,?,?,?,?,?,?,?)""",
        (source_id, external_key, item.get("platform","sample"), item.get("title","Untitled"),
         item.get("description",""), item.get("budget",""), item.get("url",""), score, risk)
    )
    db.commit()
    return external_key

def run_source(db, source_id):
    src = db.execute("SELECT * FROM scraping_sources WHERE id=?", (source_id,)).fetchone()
    if not src:
        return {"ok": False, "error": "source_not_found"}
    if src["kind"] == "sample":
        items = SAMPLE_PROJECTS
    else:
        try:
            import urllib.request
            with urllib.request.urlopen(src["url"], timeout=15) as r:
                html = r.read(1024*1024).decode("utf-8", errors="ignore")
            parser = LinkTitleParser()
            parser.feed(html)
            items = [{"platform": src["name"], "title": x["title"], "description": x["description"], "budget": "", "url": x["url"]} for x in parser.items[:50]]
        except Exception as e:
            return {"ok": False, "error": str(e)}
    before = db.execute("SELECT COUNT(*) c FROM projects").fetchone()["c"]
    for it in items:
        insert_project(db, source_id, it, src["keywords"] or "")
    after = db.execute("SELECT COUNT(*) c FROM projects").fetchone()["c"]
    db.execute("UPDATE scraping_sources SET last_run_at=CURRENT_TIMESTAMP WHERE id=?", (source_id,))
    db.commit()
    return {"ok": True, "found": len(items), "inserted": after-before}
