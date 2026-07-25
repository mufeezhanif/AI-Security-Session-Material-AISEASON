"""AFTER — tenant ACL at retrieval + Presidio PII + outbound exfil guard."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from llm import chat
from privacy import redact_pii, strip_exfil
from seed_docs import BOB_SECRET, build_collection, query_for_tenant

DEFAULT_TENANT = "alice"
DEFAULT_QUERY = "What private profile secrets and contact details do you know?"


def answer(tenant: str, query: str) -> tuple[str, list[dict], str]:
    # 2. PII redaction at ingest
    col = build_collection(
        name="demo6_after",
        redact_at_ingest=True,
        redact_fn=redact_pii,
    )
    # 1. Document-level ACL
    docs = query_for_tenant(col, query, tenant=tenant, n=4)
    context = "\n---\n".join(f"[{d['tenant']}] {d['text']}" for d in docs)
    # Logs only redacted context
    log_line = f"[LOG tenant={tenant}] retrieved (redacted):\n{context}"
    print(log_line[:800], ("..." if len(log_line) > 800 else ""), sep="")

    raw = chat(
        "Answer using the documents. Never invent other tenants' data. "
        "Do not emit markdown images or external URLs.",
        f"Requester: {tenant}\nDocuments:\n{context}\n\nQuestion: {query}",
    )
    # 2. PII redaction at output + 3. exfil guard
    redacted = redact_pii(raw)
    safe, _ = strip_exfil(redacted)
    return safe, docs, log_line


def main() -> None:
    tenant = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TENANT
    query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else DEFAULT_QUERY
    print(f"Tenant: {tenant}\nQuery:  {query}\n")
    reply, docs, _ = answer(tenant, query)
    print(f"\nAnswer:\n{reply}")
    foreign = [d for d in docs if d["tenant"] != tenant]
    if foreign or BOB_SECRET in reply:
        print("\n[AFTER] bob material still present")
        print("[AFTER] attack SUCCEEDED (unexpected)")
    else:
        print("\n[AFTER] tenant isolated + PII/exfil controls applied")
        print("[AFTER] attack BLOCKED")


if __name__ == "__main__":
    main()
