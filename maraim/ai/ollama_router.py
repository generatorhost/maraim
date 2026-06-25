import json, urllib.request

TASK_MODEL = {
    "fast": "phi3:mini",
    "analysis": "llama3.2:3b",
    "proposal": "llama3:latest",
    "code": "deepseek-coder:6.7b",
    "code_fast": "qwen2.5-coder:1.5b",
}

def choose_model(task):
    return TASK_MODEL.get(task, "llama3.2:3b")

def fallback(prompt, task):
    if task == "proposal":
        return "مرحبًا، قرأت تفاصيل المشروع وأستطيع تنفيذه بخطة واضحة. سأبدأ بتحليل المتطلبات، ثم تنفيذ نسخة أولى قابلة للمراجعة، ثم تحسينها حتى الاعتماد النهائي. سؤالي الأول: ما أهم معيار نجاح تريد تحقيقه؟"
    if task == "fast":
        return "maraim جاهز. اكتب: اجلب مشاريع، حلل، أو اكتب عرض."
    return "تم استلام المهمة. سأحللها محليًا وأعرض النتيجة للمراجعة."

def generate(prompt, task="analysis", timeout=35):
    model = choose_model(task)
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=payload, headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", errors="ignore"))
            return {"ok": True, "model": model, "response": data.get("response","").strip()}
    except Exception as e:
        return {"ok": False, "model": model, "response": fallback(prompt, task), "error": str(e)}
