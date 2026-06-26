
import time

class TaskExecutorRuntime:
    def __init__(self, event_bus, memory, organization, scraping_runner=None, analysis_runner=None, proposal_runner=None):
        self.event_bus = event_bus
        self.memory = memory
        self.organization = organization
        self.scraping_runner = scraping_runner
        self.analysis_runner = analysis_runner
        self.proposal_runner = proposal_runner
        self.executions = []

    def execute(self, task):
        task_type = task.get("type", "unknown")
        started = time.time()

        routed = self.organization.route_task(task)

        result = {
            "ok": True,
            "task_type": task_type,
            "routed": routed,
            "output": self._simulate_output(task),
            "duration_ms": int((time.time() - started) * 1000)
        }

        self.executions.append({
            "task": task,
            "result": result,
            "created_at": time.time()
        })

        self.memory.remember_long({
            "executed_task": task,
            "result": result
        })

        self.event_bus.emit("task_executor:completed", result)
        return result

    def _simulate_output(self, task):
        t = task.get("type")
        if t == "project_discovery":
             
            if self.scraping_runner:
                return self.scraping_runner()
            return "Project discovery task executed by scouting team."
        if t == "project_analysis":
            
            if self.analysis_runner:
                return self.analysis_runner(task)
            return "Project analysis task executed by analysis team."
        if t == "proposal_generation":
            
            if self.proposal_runner:
                return self.proposal_runner(task)
            return "Proposal generation task executed by proposal team."
        if t == "approval_wait":
            return "Approval task created and waiting for user decision."
        if t == "remember":
            return "Workflow result stored in memory."
        return "Generic task executed."

    def status(self):
        return {
            "executions": len(self.executions),
            "last": self.executions[-1] if self.executions else None
        }
