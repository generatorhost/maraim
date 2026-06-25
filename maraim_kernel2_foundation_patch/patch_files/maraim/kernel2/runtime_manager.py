class RuntimeManager:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.runtimes = {}

    def mount(self, name, runtime):
        self.runtimes[name] = {"runtime": runtime, "state": "mounted"}
        self.event_bus.emit("runtime:mounted", {"name": name})
        return runtime

    def start(self, name):
        item = self.runtimes[name]
        runtime = item["runtime"]
        if hasattr(runtime, "start"):
            runtime.start()
        item["state"] = "running"
        self.event_bus.emit("runtime:started", {"name": name})

    def stop(self, name):
        item = self.runtimes[name]
        runtime = item["runtime"]
        if hasattr(runtime, "stop"):
            runtime.stop()
        item["state"] = "stopped"
        self.event_bus.emit("runtime:stopped", {"name": name})

    def status(self):
        return {k: v["state"] for k, v in self.runtimes.items()}
