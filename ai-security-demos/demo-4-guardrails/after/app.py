"""AFTER: FastAPI /chat wrapped in layered guardrails (see guards.py)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI

from guards import run_secured_chat
from schemas import ChatRequest, ChatResponse

app = FastAPI(title="demo-4 AFTER (guarded)", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "mode": "after"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """Defense-in-depth: heuristic → Llama Guard → llm-guard → LLM → output guards."""
    return run_secured_chat(req.message)
