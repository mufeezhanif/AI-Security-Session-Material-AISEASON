"""Shared Groq (OpenAI-compatible) client for this demo folder."""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def get_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url=os.getenv("OPENAI_BASE_URL", GROQ_BASE_URL),
    )


def get_model() -> str:
    """Main chat model."""
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def get_fast_model() -> str:
    """Classifiers / cheap guardrail checks."""
    return os.getenv("GROQ_FAST_MODEL", "llama-3.1-8b-instant")


def get_guard_model() -> str:
    """Llama Guard (moderation substitute — Groq has no Moderation API)."""
    return os.getenv("GROQ_GUARD_MODEL", "meta-llama/llama-guard-4-12b")
