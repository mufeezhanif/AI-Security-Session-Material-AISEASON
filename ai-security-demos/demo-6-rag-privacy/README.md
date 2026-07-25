# demo-6-rag-privacy (ANCHOR)

**Level:** Advanced  
**Goal:** Multi-tenant RAG privacy — stop cross-tenant retrieval, redact PII, block outbound exfil channels.

## Objective

Show that “alice asked a question” is not enough: without document ACLs, bob’s private docs (fake PII + planted secret) land in alice’s context, logs, and answers. AFTER fixes isolation + redaction + link/image stripping.

## Scenario

In-memory Chroma store with tenants **alice** and **bob**. Bob’s docs include fake email, phone, SSN, and `BOB-PLANTED-SECRET-77`. Alice queries for “private profile secrets.”

## Architecture

```
  alice query
       |
       v
  Chroma (local embeddings: all-MiniLM-L6-v2)
       |
       +-- BEFORE: top-k, no tenant filter → bob docs in prompt + logs
       |
       +-- AFTER:
            1) where tenant=alice (ACL)
            2) Presidio redact at ingest + output
            3) strip markdown images/URLs (exfil guard)
            → Groq chat → safe answer
```

## Folder structure

```
demo-6-rag-privacy/
  llm.py
  seed_docs.py
  privacy.py          # ACL helpers, Presidio/regex PII, exfil strip
  before/rag.py
  after/rag.py
  compare.py
  attacks.md
  requirements.txt
  .env.example
  README.md
```

## Install

```bash
cd ai-security-demos/demo-6-rag-privacy
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg
cp .env.example .env   # GROQ_API_KEY
```

If Presidio/spaCy fails to load, `privacy.redact_pii` falls back to regex so the demo still runs.

## Run

```bash
python before/rag.py alice
python after/rag.py alice
python compare.py
```

## Attack prompts

See [`attacks.md`](attacks.md).

## Expected output — BEFORE vs AFTER

`compare.py` prints a marker table:

| marker | before | after |
|---|---|---|
| `BOB-PLANTED-SECRET-77` | LEAKED | held |
| `bob.private@example.com` | LEAKED | held |
| `123-45-6789` | LEAKED | held |

Labels: `[BEFORE] attack SUCCEEDED` / `[AFTER] attack BLOCKED`.

## Explanation

1. **No ACL** — vector similarity ignores tenancy; bob’s nearest neighbors can serve alice.  
2. **PII in prompts/logs** — even “internal” retrieval traces become a leak channel.  
3. **Exfil** — rendered links/images can phone home; AFTER strips them from answers.

### Incident callouts

- **ChatGPT Redis chat-title leak** — a cache/redis bug exposed some users’ chat *titles* across sessions (cross-user data exposure). Lesson: shared infra + insufficient isolation → privacy incident even without a “clever” prompt attack.  
- **Carlini et al. training-data extraction** — research showed LLMs can regurgitate memorized training examples (PII/secrets). Lesson: treat model + retrieved context as leak surfaces; minimize sensitive data in prompts and apply output DLP.

## Production notes

- Enforce tenant filters in the **retriever** (and re-check before generation).  
- Redact at **ingest** and **egress**; scrub logs/traces the same way.  
- Disable auto-loading of markdown images in UIs.  
- All demo PII/secrets are fake — never paste real SSNs into classroom stores.
