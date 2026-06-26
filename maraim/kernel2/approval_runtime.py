
import time
import uuid

class ApprovalRuntime:
    def __init__(self, event_bus, memory):
        self.event_bus = event_bus
        self.memory = memory
        self.approvals = {}

    def create(self, task, context=None):
        approval_id = str(uuid.uuid4())
        approval = {
            "id": approval_id,
            "status": "waiting",
            "task": task,
            "context": context or {},
            "created_at": time.time(),
            "decision": None
        }
        self.approvals[approval_id] = approval
        self.event_bus.emit("approval:created", {"approval_id": approval_id})
        return {"ok": True, "approval": approval}

    def decide(self, approval_id, decision, notes=""):
        if approval_id not in self.approvals:
            return {"ok": False, "error": "approval_not_found"}
        approval = self.approvals[approval_id]
        approval["status"] = decision
        approval["decision"] = {"decision": decision, "notes": notes, "decided_at": time.time()}
        self.memory.remember_long({"approval": approval})
        self.event_bus.emit("approval:decided", {"approval_id": approval_id, "decision": decision})
        return {"ok": True, "approval": approval}

    def status(self):
        return {
            "waiting": len([x for x in self.approvals.values() if x["status"] == "waiting"]),
            "total": len(self.approvals),
            "approvals": list(self.approvals.values())
        }
