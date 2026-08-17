"""Веб-панель AgentMesh (FastAPI).

Предоставляет REST API и простую страницу для:
- просмотра пула агентов и их загрузки
- запуска оркестрации цели с шагами
- просмотра результатов задач
- веб-сокета для логов в реальном времени
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from agentmesh.agents.factory import coder, critic, researcher
from agentmesh.core.orchestrator import Orchestrator
from agentmesh.core.planner import plan
from agentmesh.core.router import Router
from agentmesh.llm.providers import OpenAICompatClient


class TaskRequest(BaseModel):
    goal: str
    steps: list[str] = []
    agent: str = "any"
    api_key: str | None = None
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"


class RunResult(BaseModel):
    goal: str
    tasks: list[dict[str, Any]]
    success: bool
    load: dict[str, int]


def create_app() -> FastAPI:
    app = FastAPI(title="AgentMesh Panel", version="0.1.0")

    # единственный общий оркестратор (создаётся при первом запуске)
    orch: Orchestrator | None = None
    _lock = asyncio.Lock()

    def _get_orchestrator(req: TaskRequest) -> Orchestrator:
        nonlocal orch
        if orch is not None:
            return orch
        client = OpenAICompatClient(
            api_key=req.api_key,
            base_url=req.base_url,
            model=req.model,
        )
        router = Router()
        router.register(researcher(client))
        router.register(coder(client))
        router.register(critic(client))
        orch = Orchestrator(router)
        return orch

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return """<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<title>AgentMesh</title>
<style>
body{font-family:system-ui;background:#0f172a;color:#e2e8f0;margin:0;padding:2rem}
.card{background:#1e293b;border-radius:12px;padding:1.5rem;margin-bottom:1rem}
input,textarea{width:100%;background:#0f172a;border:1px solid #334155;color:#e2e8f0;padding:.6rem;border-radius:8px;margin:.3rem 0}
button{background:#38bdf8;border:0;color:#06283d;font-weight:700;padding:.7rem 1.4rem;border-radius:8px;cursor:pointer}
pre{background:#0f172a;padding:1rem;border-radius:8px;overflow:auto;max-height:400px}
h1{background:linear-gradient(90deg,#38bdf8,#a78bfa);-webkit-background-clip:text;color:transparent}
</style></head><body>
<h1>⚡ AgentMesh Control Panel</h1>
<div class="card"><h2>Запуск оркестрации</h2>
<label>Цель <input id="goal" value="Проанализируй задачу и предложи план"></label>
<label>Шаги (через |) <textarea id="steps">Исследуй|Предложи решение|Оцени риски</textarea></label>
<label>API key <input id="key" placeholder="sk-..."></label>
<label>Модель <input id="model" value="gpt-4o-mini"></label>
<button onclick="run()">Запустить</button></div>
<div class="card"><h2>Лог</h2><pre id="log">(пусто)</pre></div>
<script>
const log=el=>(document.getElementById('log').textContent+=el+'\n');
async function run(){const goal=document.getElementById('goal').value;
const steps=document.getElementById('steps').value.split('|').map(s=>s.trim()).filter(Boolean);
log('→ отправляю: '+goal);
const r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({goal,steps,api_key:document.getElementById('key').value,
model:document.getElementById('model').value})});
const d=await r.json();
log('✓ успех: '+d.success);
for(const t of d.tasks){log('· ['+t.agent+'] '+t.title+' -> '+t.status);
if(t.result&&typeof t.result==='string')log('  '+t.result.slice(0,400));}
log('Загрузка: '+JSON.stringify(d.load));}
</script></body></html>"""

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "name": "AgentMesh", "version": "0.1.0"}

    @app.post("/api/run", response_model=RunResult)
    async def run_task(req: TaskRequest) -> RunResult:
        o = _get_orchestrator(req)
        steps = req.steps or [req.goal]
        p = plan(
            req.goal,
            steps,
            agent_for_step=lambda i: req.agent if req.agent != "any" else None,
        )
        async with _lock:
            await o.run(p)
        return RunResult(
            goal=req.goal,
            tasks=[t.model_dump() for t in p.tasks],
            success=all(t.status.value == "done" for t in p.tasks),
            load=o.stats()["load"],
        )

    @app.websocket("/ws")
    async def ws_logs(ws: WebSocket) -> None:
        await ws.accept()
        try:
            while True:
                await ws.receive_text()
                await ws.send_text("pong")
        except WebSocketDisconnect:
            pass

    return app


app = create_app()