from maraim.ai.ollama_router import generate

def analyze_project(db, project_id):
    p = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not p:
        return {"ok": False, "error": "project_not_found"}
    prompt = f"""حلل مشروع فريلانس بالعربية باختصار:
العنوان: {p['title']}
الوصف: {p['description']}
الميزانية: {p['budget']}
أخرج: الملاءمة، المخاطر، سبب الاختيار، أول خطوة."""
    out = generate(prompt, task="analysis")
    score = int(p["fit_score"] or 0)
    risk = "low" if score >= 70 else "medium" if score >= 40 else "high"
    db.execute("INSERT INTO project_analysis(project_id,model,summary,score,risk) VALUES(?,?,?,?,?)",
               (project_id, out.get("model"), out.get("response"), score, risk))
    db.execute("UPDATE projects SET status='analyzed' WHERE id=?", (project_id,))
    db.commit()
    return {"ok": True, "analysis": out.get("response"), "model": out.get("model"), "score": score, "risk": risk}

def generate_proposal(db, project_id):
    p = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not p:
        return {"ok": False, "error": "project_not_found"}
    prompt = f"""اكتب Proposal احترافي قصير لمشروع:
{p['title']}
{p['description']}
يجب أن يكون عمليًا، غير مبالغ، ويحتوي سؤالًا ذكيًا للعميل."""
    out = generate(prompt, task="proposal")
    price = p["budget"] or "حسب التفاصيل"
    duration = "3-7 أيام حسب النطاق"
    cur = db.execute("INSERT INTO proposals(project_id,body,price,duration) VALUES(?,?,?,?)",
                     (project_id, out.get("response"), price, duration))
    proposal_id = cur.lastrowid
    db.execute("INSERT INTO approvals(entity_type,entity_id,status,notes) VALUES('proposal',?,'pending','waiting_user_review')",
               (proposal_id,))
    db.execute("UPDATE projects SET status='proposal_ready' WHERE id=?", (project_id,))
    db.commit()
    return {"ok": True, "proposal_id": proposal_id, "body": out.get("response"), "model": out.get("model")}
