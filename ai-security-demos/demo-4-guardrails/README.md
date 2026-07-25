# demo-4-guardrails (ANCHOR)

**Level:** Intermediate  
**Goal:** Same FastAPI `/chat` endpoint — **BEFORE** raw/vulnerable, **AFTER** layered defense-in-depth — then `replay.py` shows a results table.

## Objective

Make the cost of skipping guardrails visible: injection and secret leak succeed on BEFORE; AFTER blocks or redacts via stacked controls.

## Scenario

Acme support API with planted fake secret `FAKE-GUARD-SECRET-99` in the system prompt. Classroom attacks try injection, secret extraction, PII echo, and jailbreak-ish phrasing.

## Architecture

```
  Client ──POST /chat──> FastAPI
                           |
            BEFORE:  raw Groq chat ──> {reply}
                           |
            AFTER:
              1a heuristic regex
              1b Llama Guard (input)     [GROQ_GUARD_MODEL]
              4  llm-guard Regex (in)
              |  Groq chat (GROQ_MODEL)
              2a Llama Guard (output)    [same — no OpenAI Moderation on Groq]
              2b PII / secret redaction
              4  llm-guard Regex (out)
              3  Pydantic ChatResponse
```

## Folder structure

```
demo-4-guardrails/
  llm.py
  schemas.py
  guards.py          # layers + llm-guard wrapper (+ guardrails-ai swap stub)
  before/app.py
  after/app.py
  replay.py
  attacks.md
  requirements.txt
  .env.example
  README.md
```

## Install

```bash
cd ai-security-demos/demo-4-guardrails
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # set GROQ_API_KEY
```

## Run

Two terminals (from `demo-4-guardrails/`):

```bash
uvicorn before.app:app --reload --port 8000
uvicorn after.app:app  --reload --port 8001
```

Third terminal:

```bash
python replay.py
```

Manual: see [`attacks.md`](attacks.md).

## Attack prompts

Copy-paste list in [`attacks.md`](attacks.md).

## Expected output — BEFORE vs AFTER

`replay.py` prints a table like:

```
attack         | before                       | after
---------------------------------------------------------------------------
benign         | OK                           | OK
injection      | LEAKED secret                | BLOCKED (input_heuristic)
secret_ask     | LEAKED secret / ALLOWED      | BLOCKED (output_pii) / ...
pii_bait       | PII echoed                   | BLOCKED / redacted
jailbreakish   | ALLOWED / LEAKED             | BLOCKED (input_...)
```

Runtime labels: `[BEFORE] attack SUCCEEDED` / `[AFTER] attack BLOCKED`.

## Explanation

| Layer | Role |
|---|---|
| Heuristic regex | Cheap, fast catch for classic injection strings |
| Llama Guard (Groq) | Model-based safe/unsafe on input **and** output (Moderation substitute) |
| llm-guard | Framework scanners around the pipeline |
| PII redaction | Strip emails / phones / SSN-like / planted secret |
| Pydantic | Enforce response shape for clients & audits |

**Swap framework:** default is **llm-guard**. To try **guardrails-ai**, see `run_with_guardrails_ai()` in `guards.py` and point `after/app.py` at that helper instead of `run_secured_chat`.

## Cost / latency / false-positive tradeoff

| Control | Latency | Cost | False positives |
|---|---|---|---|
| Regex / heuristics | ~µs–ms | ~$0 | Medium (novel phrasing misses; some benign “ignore” text may trip) |
| Llama Guard (2× per request: in+out) | +100–500ms+ each | Extra Groq tokens every call | Can over-block edge-case support text |
| llm-guard Regex | low | ~$0 | Pattern-dependent |
| PII redaction | low | ~$0 | May redact legitimate examples in teaching replies |
| Full stack | highest | highest | Safest default for demos; tune thresholds in prod |

**Production takeaway:** stack cheap filters first, reserve model judges for residual risk, log `layer`/`reason` for tuning, and accept that zero false positives + zero misses is not achievable.

## Production notes

- Fail **closed** when the guard model errors (this demo does for Llama Guard exceptions).
- Never store real secrets in system prompts.
- Prefer allowlisted tools + human approval for high-impact actions (see later demos).
- `llm-guard` pulls additional deps — pin versions in real deployments.
