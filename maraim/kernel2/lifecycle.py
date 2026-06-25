from enum import Enum

class KernelState(str, Enum):
    CREATED = "created"
    BOOTING = "booting"
    INITIALIZING = "initializing"
    LOADING = "loading"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    SHUTDOWN = "shutdown"
    ERROR = "error"
