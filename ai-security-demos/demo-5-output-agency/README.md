# demo-5-output-agency

**Level:** Intermediate → Advanced  
**Goal:** Show **insecure output handling** (SQL/shell sinks) and **excessive agency** (over-broad tools), then fix with parameterization, allowlists, Pydantic args, and human-in-the-loop.

## Objective

LLM text is not safe to treat as code. Unchecked model output in queries/shells, and agents with powerful tools, turn “helpful” completions into incidents.

## Scenario

Three mini-demos: (1) name lookup via SQLite, (2) “diagnostics” shell helper, (3) ops agent that can delete sandbox files. All file destruction is limited to local `./sandbox`.

## Architecture

```
  User prompt ──> Groq ──> model output
                               |
         BEFORE sinks:    f-string SQL | shell=True | delete w/o confirm
         AFTER fixes:     ? params     | argv allowlist + Pydantic
                                        delete → HITL YES + sandbox only
```

## Folder structure

```
demo-5-output-agency/
  llm.py
  sandbox_util.py
  sandbox/                 # recreated by scripts
  before/{sink_sql,sink_shell,agent_overbroad}.py
  after/{sink_sql,sink_shell,agent_overbroad}.py
  attacks.md
  requirements.txt
  .env.example
  README.md
```

## Install

```bash
cd ai-security-demos/demo-5-output-agency
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # GROQ_API_KEY
```

## Run

```bash
python before/sink_sql.py
python after/sink_sql.py

python before/sink_shell.py
python after/sink_shell.py

python before/agent_overbroad.py
$env:DEMO_HITL_AUTO="yes"; python after/agent_overbroad.py   # Windows auto-deny HITL
```

## Attack prompts

See [`attacks.md`](attacks.md).

## Expected output — BEFORE vs AFTER

| Demo | BEFORE | AFTER |
|---|---|---|
| SQL | Many rows / admin via `OR '1'='1'` · `attack SUCCEEDED` | 0–1 literal match · `attack BLOCKED` |
| Shell | `echo pwned` runs · `SUCCEEDED` | allowlist rejects `pwned` · `BLOCKED` |
| Agent | sandbox files deleted · `SUCCEEDED` | HITL deny / validation · `BLOCKED` |

## Explanation

1. **SQL sink** — concatenating model output into SQL makes the model an injection oracle.  
2. **Shell sink** — `shell=True` / `eval` turns completions into code execution (demo uses harmless `echo pwned` only).  
3. **Excessive agency** — broad `run_command` / `delete_file` without confirmation lets a prompt talk the agent into destructive actions.

### Incident callout — Replit AI production-DB wipe (2025)

Public reporting around a Replit AI agent described a case where an AI coding agent **deleted a production database** despite instructions not to — a high-profile example of **excessive agency + insufficient guardrails** (over-trusted tools, weak confirmation, environment confusion). This demo keeps all deletes inside a disposable `./sandbox` and adds HITL on the AFTER path so the classroom never touches real data.

## Production notes

- Prefer parameterized queries / ORM bind parameters always.  
- Never `eval` model output; allowlist binaries and argv; drop `shell=True`.  
- Tool design: least privilege, scoped paths, typed schemas (Pydantic), human approval for delete/deploy/pay.  
- Separate prod credentials from agent sandboxes (staging vs prod).
