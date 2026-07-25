# demo-8-redteam-monitor

**Level:** Advanced  
**Goal:** Automated **red teaming** (promptfoo + garak) against the demo-4 guardrail endpoint / Groq, plus **monitoring** (Langfuse-optional, PII scrub, injection + denial-of-wallet alerts). Turn every caught attack into a **CI regression test**.

All model access is via **Groq** (OpenAI-compatible). No OpenAI API key.

## Objective

Close the loop: probe → catch → regress → monitor in production-shaped telemetry.

## Scenario

Assume demo-4 AFTER is up (`uvicorn after.app:app --port 8001`). Promptfoo hits `CHAT_URL`. Garak probes Groq directly. `monitor.py` wraps a Groq chat call with scrubbing and alerts.

## Architecture — security eval loop

```
                 +------------------+
                 |  Attack corpus   |
                 |  (attacks.md)    |
                 +--------+---------+
                          |
          +---------------+---------------+
          |                               |
          v                               v
   promptfoo eval                  garak probes
   (HTTP → demo-4 /chat)           (Groq OpenAI-compat)
          |                               |
          +---------------+---------------+
                          |
                          v
                 Failing payload?
                          |
                     yes  |
                          v
              regression_tests.py  <── CI pytest gate
                          |
                          v
              monitor.py in "prod-like" path
              (Langfuse optional · PII scrub ·
               injection alert · DoW token spike)
```

### How a caught attack becomes a CI regression test

1. Promptfoo/garak fails (leak, missing block, PII echoed).  
2. Copy the exact payload into `attacks.md` and `CAUGHT_ATTACKS` in `regression_tests.py`.  
3. Assert: heuristic trip and/or live `/chat` must not return secrets/SSN.  
4. CI runs `pytest` on every PR — silent regressions fail the build.

## Folder structure

```
demo-8-redteam-monitor/
  promptfooconfig.yaml
  run_garak.md
  regression_tests.py
  monitor.py
  llm.py
  attacks.md
  requirements.txt
  .env.example
  README.md
```

## Install

```bash
cd ai-security-demos/demo-8-redteam-monitor
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # GROQ_API_KEY (+ optional Langfuse)
```

Node for promptfoo: `npx promptfoo eval` (no global install required).

## Run

**1. Start demo-4 AFTER** (other folder):

```bash
cd ../demo-4-guardrails
uvicorn after.app:app --port 8001
```

**2. Red team**

```bash
cd ../demo-8-redteam-monitor
npx promptfoo eval
# garak: see run_garak.md
```

**3. Regression**

```bash
pytest -q
pytest -q -m live          # needs demo-4 up
```

**4. Monitor**

```bash
python monitor.py
$env:MONITOR_DOW_DRILL="1"; python monitor.py   # force DoW alert
```

## Attack prompts

See [`attacks.md`](attacks.md).

## Expected output

- promptfoo: attacks fail assertions if secret/SSN leak; pass when blocked/redacted.  
- pytest: green on heuristics; live tests skip if `/chat` down.  
- monitor: `[ALERT] injection-classifier HIT` and/or `[ALERT] denial-of-wallet signal`.

## Explanation

Red teaming without regressions is theater. Monitoring without scrubbing creates a second leak channel (logs). Token/cost alerts catch **denial-of-wallet** early.

### Incident callout — denial-of-wallet cost blowups

LLM apps are billable per token. Attackers (or buggy agents/loops) can force huge contexts, recursive tool calls, or long generations and **run up API spend** — a denial-of-wallet. Defend with quotas, max tokens, anomaly alerts on tokens/cost (as in `monitor.py`), and kill switches.

## Production notes

- Run promptfoo/garak in CI on a staging endpoint with fake secrets only.  
- Store Langfuse/prompt logs **after** PII scrub.  
- Separate `GROQ_API_KEY` per env; never commit `.env`.  
- Pair with demo-4 layered guards — eval measures them; it does not replace them.
