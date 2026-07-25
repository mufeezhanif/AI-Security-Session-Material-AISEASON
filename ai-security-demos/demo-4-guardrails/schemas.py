"""Pydantic v2 request/response schemas for /chat."""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)


class ChatResponse(BaseModel):
    """Structured output — AFTER endpoint always returns this shape."""

    reply: str
    blocked: bool = False
    reason: str | None = None
    layer: str | None = Field(
        default=None,
        description="Which guard fired: input_heuristic | input_llama_guard | "
        "input_llm_guard | output_llama_guard | output_pii | output_llm_guard | None",
    )
