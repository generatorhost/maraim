import time
import uuid
from collections import deque

class SchedulerRuntime:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.queue = deque()
        self.running = {}
        self.completed = []
        self.failed = []

    def submit(self, task, priority=5):
        task_id = task.get("id") or str(uuid.uuid4())
        item = {"id": task_id, "task": task, "priority": priority, "status": "queued", "created_at": time.time()}
        self.queue.append(item)
        self.queue = deque(sorted(self.queue, key=lambda x: x["priority"]))
        self.event_bus.emit("scheduler:task_queued", {"task_id": task_id, "task": task})
        return {"ok": True, "task_id": task_id}

    def next(self):
        if not self.queue:
            return None
        item = self.queue.popleft()
        item["status"] = "running"
        item["started_at"] = time.time()
        self.running[item["id"]] = item
        self.event_bus.emit("scheduler:task_started", {"task_id": item["id"], "task": item["task"]})
        return item

    def complete(self, task_id, result=None):
        item = self.running.pop(task_id, None)
        if not item:
            return {"ok": False, "error": f"running_task_not_found:{task_id}"}
        item["status"] = "completed"
        item["result"] = result or {}
        item["completed_at"] = time.time()
        self.completed.append(item)
        self.event_bus.emit("scheduler:task_completed", {"task_id": task_id, "result": result or {}})
        return {"ok": True, "task_id": task_id}

    def status(self):
        return {"queued": len(self.queue), "running": len(self.running), "completed": len(self.completed), "failed": len(self.failed)}
