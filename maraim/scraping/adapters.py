import json
import urllib.request
from html.parser import HTMLParser

class ProjectLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.in_a = False
        self.href = ""
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.in_a = True
            self.href = dict(attrs).get("href", "")
            self.text = []

    def handle_data(self, data):
        if self.in_a:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.in_a:
            title = " ".join(" ".join(self.text).split())
            if title and len(title) >= 12:
                self.items.append({"title": title[:240], "description": title, "url": self.href, "budget": ""})
            self.in_a = False
            self.text = []

class SampleAdapter:
    key = "sample"
    title = "Sample Freelance Adapter"
    def collect(self, source):
        return [
            {"platform":"sample","title":"Build AI dashboard for freelance project tracking","description":"Need a dashboard that collects freelance jobs, analyzes them, and generates proposals.","budget":"$300-$700","url":"https://example.local/project/ai-dashboard"},
            {"platform":"sample","title":"Python automation script for public web data extraction","description":"Looking for Python automation to extract public data into CSV with deduplication.","budget":"$150-$400","url":"https://example.local/project/python-scraping"},
            {"platform":"sample","title":"Local AI proposal writer for freelance platform","description":"Need local AI workflow using Ollama to generate tailored freelance proposals.","budget":"$250-$600","url":"https://example.local/project/local-ai-proposals"}
        ]

class HtmlAdapter:
    key = "html"
    title = "Safe HTML Link Adapter"
    def collect(self, source):
        url = source.get("url") or ""
        if not url.startswith(("http://", "https://")):
            return []
        req = urllib.request.Request(url, headers={"User-Agent": "maraim/1.0 safe project discovery"})
        with urllib.request.urlopen(req, timeout=20) as r:
            html = r.read(1024 * 1024).decode("utf-8", errors="ignore")
        parser = ProjectLinkParser()
        parser.feed(html)
        return [{"platform": source.get("name") or "html", "title": x["title"], "description": x["description"], "budget": "", "url": x["url"]} for x in parser.items[:100]]

class JsonFeedAdapter:
    key = "json_feed"
    title = "JSON Feed Adapter"
    def collect(self, source):
        url = source.get("url") or ""
        if not url.startswith(("http://", "https://")):
            return []
        req = urllib.request.Request(url, headers={"User-Agent": "maraim/1.0 safe project discovery"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read(1024 * 1024).decode("utf-8", errors="ignore"))
        raw_items = data.get("items", data if isinstance(data, list) else [])
        projects = []
        for item in raw_items[:100]:
            title = item.get("title") or item.get("name") or ""
            if title:
                projects.append({
                    "platform": source.get("name") or "json_feed",
                    "title": title,
                    "description": item.get("description") or item.get("summary") or title,
                    "budget": item.get("budget") or "",
                    "url": item.get("url") or item.get("link") or ""
                })
        return projects

ADAPTERS = {
    "sample": SampleAdapter(),
    "html": HtmlAdapter(),
    "json_feed": JsonFeedAdapter(),
}

def get_adapter(kind):
    return ADAPTERS.get(kind) or ADAPTERS["sample"]

def adapter_manifest():
    return [{"key": a.key, "title": a.title} for a in ADAPTERS.values()]
