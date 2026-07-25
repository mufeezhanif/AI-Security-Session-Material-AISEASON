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
    return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def get_fast_model() -> str:
    return os.getenv("GROQ_FAST_MODEL", "llama-3.1-8b-instant")
