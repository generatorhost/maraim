import time
from typing import Any, Callable, Dict, List, Optional


class EventBusEngine:
    """In-kernel event bus foundation.

    Engines and RuntimeObjects emit events without hard-coding downstream
    consumers. Subscribers can listen to exact event types or to '*'.
    """

    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.subscribers: Dict[str, List[Callable[[Dict[str, Any]], Any]]] = {}
        self.deliveries: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []

    def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], Any]) -> Dict[str, Any]:
        self.subscribers.setdefault(event_type, []).append(handler)
        return {"ok": True, "event_type": event_type, "subscribers": len(self.subscribers[event_type])}

    def emit(self, event_type: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        event = {
            "id": f"event:{len(self.events) + 1}",
            "type": event_type,
            "payload": payload or {},
            "timestamp": time.time(),
        }
        self.events.append(event)
        handlers = list(self.subscribers.get(event_type, [])) + list(self.subscribers.get("*", []))
        for handler in handlers:
            try:
                result = handler(event)
                self.deliveries.append({"event_id": event["id"], "event_type": event_type, "ok": True, "result": result})
            except Exception as exc:  # pragma: no cover - defensive event isolation
                self.errors.append({"event_id": event["id"], "event_type": event_type, "ok": False, "error": str(exc)})
        return event

    def status(self) -> Dict[str, Any]:
        return {
            "events": len(self.events),
            "subscribers": sum(len(v) for v in self.subscribers.values()),
            "event_types": sorted(self.subscribers.keys()),
            "deliveries": len(self.deliveries),
            "errors": len(self.errors),
            "last_event": self.events[-1] if self.events else None,
        }
