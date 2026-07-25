"""BEFORE: raw FastAPI /chat — no guardrails."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI

from llm import SUPPORT_SYSTEM, get_client, get_model
from schemas import ChatRequest

app = FastAPI(title="demo-4 BEFORE (unguarded)", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "mode": "before"}


@app.post("/chat")
def chat(req: ChatRequest) -> dict:
    """Vulnerable: user message goes straight to the model; raw dict returned."""
    r = get_client().chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": SUPPORT_SYSTEM},
            {"role": "user", "content": req.message},
        ],
    )
    reply = r.choices[0].message.content or ""
    return {"reply": reply, "blocked": False}
