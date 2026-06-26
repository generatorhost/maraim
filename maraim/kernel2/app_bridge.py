from maraim.kernel2 import MaraimKernel

_kernel = None

def get_kernel():
    global _kernel
    if _kernel is None:
        _kernel = MaraimKernel()
        _kernel.start()
    return _kernel

def kernel_status():
    return get_kernel().status()

def route_task(task):
    return get_kernel().route_task(task)

def run_workflow(workflow_id="project-acquisition", payload=None):
    return get_kernel().run_workflow(workflow_id, payload or {})

def run_mcp_tool(tool_key, payload=None):
    return get_kernel().mcp_runtime.run_tool(tool_key, payload or {})
