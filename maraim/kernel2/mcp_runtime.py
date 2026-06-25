class MCPRuntime:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.tools = {}

    def register_tool(self, key, fn, description=""):
        self.tools[key] = {"fn": fn, "description": description}
        self.event_bus.emit("mcp:tool_registered", {"key": key, "description": description})

    def run_tool(self, key, payload=None):
        if key not in self.tools:
            return {"ok": False, "error": f"tool_not_found:{key}"}
        try:
            result = self.tools[key]["fn"](payload or {})
            self.event_bus.emit("mcp:tool_executed", {"key": key, "ok": True})
            return {"ok": True, "result": result}
        except Exception as exc:
            self.event_bus.emit("mcp:tool_executed", {"key": key, "ok": False, "error": str(exc)})
            return {"ok": False, "error": str(exc)}

    def list_tools(self):
        return [{"key": k, "description": v["description"]} for k, v in self.tools.items()]
