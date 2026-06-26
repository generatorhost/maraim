from maraim.kernel2 import MaraimKernel
from maraim.database.schema import init_db
from maraim.scraping.engine import run_source

_kernel = None
_db = None

def scraping_runner():
    global _db
    if _db is None:
        _db = init_db('data/maraim.sqlite')
    return run_source(_db, 1)

def get_kernel():
    global _kernel
    if _kernel is None:
        _kernel = MaraimKernel(scraping_runner=scraping_runner)
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
