import json
from pathlib import Path

class DNARuntime:
    """
    Runtime interpreter مباشر:
    - لا compile منفصل
    - لا cache ثابت
    - يقرأ JSON/MD/TXT من dna/source ويحولها إلى Registry Objects في الذاكرة
    """
    def __init__(self, registry, dna_root="dna/source"):
        self.registry = registry
        self.dna_root = Path(dna_root)
        self.loaded_files = {}

    def load(self):
        self.dna_root.mkdir(parents=True, exist_ok=True)
        count = 0
        for path in self.dna_root.rglob("*"):
            if path.is_file() and path.suffix.lower() in [".json", ".md", ".txt"]:
                count += self.load_file(path)
        return {"ok": True, "loaded": count, "root": str(self.dna_root)}

    def load_file(self, path):
        text = path.read_text(encoding="utf-8", errors="ignore")
        suffix = path.suffix.lower()
        if suffix == ".json":
            try:
                data = json.loads(text)
            except Exception:
                data = {"type": "knowledge", "id": path.stem, "text": text}
        else:
            data = {"type": self._classify(path, text), "id": path.stem, "text": text}

        items = data if isinstance(data, list) else [data]
        loaded = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            entity_type = item.get("type") or self._classify(path, text)
            entity_id = item.get("id") or item.get("key") or path.stem
            self.registry.register(entity_type, entity_id, item, source=str(path))
            loaded += 1
        self.loaded_files[str(path)] = loaded
        return loaded

    def reload(self):
        return self.load()

    def _classify(self, path, text):
        low = (str(path) + "\n" + text[:2000]).lower()
        if "chief" in low or "رئيس" in low:
            return "chief"
        if "team" in low or "فريق" in low:
            return "team"
        if "agent" in low or "وكيل" in low:
            return "agent"
        if "workflow" in low or "pipeline" in low:
            return "workflow"
        if "scrap" in low or "crawler" in low:
            return "scraping"
        if "model" in low or "ollama" in low or "gguf" in low or "onnx" in low:
            return "model"
        return "knowledge"
