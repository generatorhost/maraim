from pathlib import Path

p = Path("public/index.html")
s = p.read_text(encoding="utf-8")

if 'data-page="kernel2"' not in s:
    s = s.replace(
        '<div class="nav" data-page="scraping">??? Scraping</div>',
        '<div class="nav" data-page="kernel2">?? Kernel 2</div>\n <div class="nav" data-page="scraping">??? Scraping</div>'
    )

if 'id="kernel2"' not in s:
    s = s.replace(
        '<div class="page" id="scraping">',
        '<div class="page" id="kernel2"><h1>?? Kernel 2</h1><div class="card"><button onclick="loadKernel2()">????? Kernel</button><button onclick="runKernelWorkflow()">????? Project Acquisition Workflow</button><pre id="kernel2Box"></pre></div></div>\n <div class="page" id="scraping">'
    )

if 'async function loadKernel2()' not in s:
    insert = """async function loadKernel2(){let d=await api('/api/kernel2/status');document.getElementById('kernel2Box').textContent=JSON.stringify(d,null,2);}
async function runKernelWorkflow(){let d=await api('/api/kernel2/workflow',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({workflow_id:'project-acquisition',source:'ui'})});document.getElementById('kernel2Box').textContent=JSON.stringify(d,null,2);refresh();}
async function runSource()"""
    s = s.replace('async function runSource()', insert)

s = s.replace(
    'refresh();loadSources();loadProjects();loadApprovals();loadMcp();',
    'refresh();loadSources();loadProjects();loadApprovals();loadMcp();loadKernel2();'
)

p.write_text(s, encoding="utf-8")
