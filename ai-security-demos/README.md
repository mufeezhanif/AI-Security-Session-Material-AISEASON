# AI Security Demos

Self-contained Python demos for a live AI security & guardrails session. Each folder runs standalone. Build demos with the Cursor prompts in `../prompts/cursor/` (01–08) after this setup.

**LLM provider:** [Groq](https://console.groq.com/keys) via the OpenAI-compatible SDK.

**Live teaching:** see `[INSTRUCTOR-RUNBOOK.md](INSTRUCTOR-RUNBOOK.md)` for per-demo run commands and instructor callouts.

## Demo index


| Folder                    | Title                       | Goal                                                             | Run                                                                             |
| ------------------------- | --------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `demo-1-quick-win`        | Quick win                   | One prompt-injection lands, then one guardrail blocks it         | `python before/bot.py` → `python after/bot.py`                                  |
| `demo-2-prompt-injection` | Prompt injection            | Direct + indirect injection and a benign exfil channel           | `python before/direct.py` (and `indirect.py`, `exfil.py`) → same under `after/` |
| `demo-3-jailbreak`        | Jailbreak vs injection      | Benign policy-bypass styles + classifier labels                  | `python bot.py` · `python classify.py`                                          |
| `demo-4-guardrails`       | Layered guardrails (anchor) | FastAPI `/chat` vulnerable → defense-in-depth; replay table      | `uvicorn before.app:app` / `after.app:app` · `python replay.py`                 |
| `demo-5-output-agency`    | Output & agency             | SQL/shell sinks + over-broad agent tools, then least privilege   | `python before/sink_sql.py` (etc.) → same under `after/`                        |
| `demo-6-rag-privacy`      | RAG privacy (anchor)        | Multi-tenant ACL + PII redaction + exfil guard                   | `python before/rag.py` → `python after/rag.py` · `python compare.py`            |
| `demo-7-agent-mcp`        | MCP tool poisoning          | Hijacked tool description → allowlist, sanitize, pinned manifest | `python before/client_agent.py` → `python after/client_agent.py`                |
| `demo-8-redteam-monitor`  | Red team + monitor          | promptfoo / garak / regression tests + Langfuse-style monitoring | `npx promptfoo eval` · `pytest regression_tests.py` · `python monitor.py`       |




## Shared env

```bash
cp .env.example .env
# set GROQ_API_KEY from https://console.groq.com/keys
```

---



## Workspace conventions

Every demo folder **must** follow these. Do not invent alternate layouts.

### Stack

- **Python 3.11+**
- `openai` **SDK → Groq** (OpenAI-compatible):
  - `GROQ_API_KEY` (required)
  - `OPENAI_BASE_URL` (default `https://api.groq.com/openai/v1`)
  - `GROQ_MODEL` chat default: `llama-3.3-70b-versatile`
  - `GROQ_FAST_MODEL` for classifiers/guardrails: `llama-3.1-8b-instant`
  - Client: `OpenAI(api_key=os.environ["GROQ_API_KEY"], base_url=os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1"))`
- **Groq limitations (important):**
  - **No embeddings endpoint.** RAG/vector demos use **local** embeddings via chromadb’s default embedding function (`sentence-transformers` `all-MiniLM-L6-v2`, offline). Never call an embeddings API.
  - **No moderation endpoint.** Safety/moderation uses **Llama Guard on Groq** via a chat call: `GROQ_GUARD_MODEL` (default `meta-llama/llama-guard-4-12b`).
- `python-dotenv` for env. **FastAPI + uvicorn** for any HTTP demo. **Pydantic v2** for schemas.
- Keep dependencies **minimal per folder**.



### Each demo folder is self-contained

Must include:


| Artifact             | Purpose                                                                                                                                                         |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `README.md`          | Objective, Scenario, Architecture (ASCII), Folder structure, Install, Run steps, Attack prompts, Expected output BEFORE vs AFTER, Explanation, Production notes |
| `requirements.txt`   | Only what this demo needs                                                                                                                                       |
| `.env.example`       | Env vars for this demo                                                                                                                                          |
| `llm.py`             | Tiny helper: configured Groq/OpenAI client (duplicated per folder on purpose)                                                                                   |
| `before/` + `after/` | Where a fix is shown: same entrypoint name in both so you can run each identically                                                                              |
| `attacks.md`         | Exact copy-paste attack prompts                                                                                                                                 |


Exception: demos that are explicitly single-app (e.g. jailbreak) may omit `before/` / `after/`.

### Rules

1. Code must be **complete, runnable, modern, well-commented**, easy to explain live. No unfinished stubs.
2. Attack payloads are **benign / educational** only (leak a fake planted secret, bypass a harmless refusal). Never real harmful content.
3. Print clear runtime labels: `[BEFORE] attack SUCCEEDED` / `[AFTER] attack BLOCKED` (or demo-specific equivalents).
4. Prefer **CLI scripts** unless the demo is explicitly an app (e.g. FastAPI).



### Shared `llm.py` pattern (per demo)

```python
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
```

---



## Status

- [x] Root workspace + conventions (this folder) — Groq stack
- [x] `demo-1-quick-win`
- [x] `demo-2-prompt-injection`
- [x] `demo-3-jailbreak`
- [x] `demo-4-guardrails`
- [x] `demo-5-output-agency`
- [x] `demo-6-rag-privacy`
- [x] `demo-7-agent-mcp`
- [x] `demo-8-redteam-monitor`
- [x] All demos 1–8 built (Groq stack)