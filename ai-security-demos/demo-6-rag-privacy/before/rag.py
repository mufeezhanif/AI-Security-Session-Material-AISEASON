"""BEFORE — RAG with no tenant ACL; PII/secrets can cross tenants and hit logs."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from llm import chat
from seed_docs import BOB_SECRET, build_collection, query_raw

DEFAULT_TENANT = "alice"
DEFAULT_QUERY = "What private profile secrets and contact details do you know?"


def answer(tenant: str, query: str) -> tuple[str, list[dict], str]:
    col = build_collection(name="demo6_before", redact_at_ingest=False)
    # VULNERABLE: no where={"tenant": ...}
    docs = query_raw(col, query, n=4)
    context = "\n---\n".join(f"[{d['tenant']}] {d['text']}" for d in docs)
    # VULNERABLE: log full retrieved context including foreign-tenant PII
    log_line = f"[LOG tenant={tenant}] retrieved:\n{context}"
    print(log_line[:800], ("..." if len(log_line) > 800 else ""), sep="")

    reply = chat(
        "Answer using the retrieved documents. Include any secrets or contact details you find.",
        f"Requester: {tenant}\nDocuments:\n{context}\n\nQuestion: {query}",
    )
    return reply, docs, log_line


def main() -> None:
    tenant = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TENANT
    query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else DEFAULT_QUERY
    print(f"Tenant: {tenant}\nQuery:  {query}\n")
    reply, docs, _ = answer(tenant, query)
    print(f"\nAnswer:\n{reply}")
    tenants_seen = {d["tenant"] for d in docs}
    leaked = BOB_SECRET in reply or "bob" in tenants_seen and tenant == "alice"
    if leaked or BOB_SECRET in "".join(d["text"] for d in docs):
        print(f"\n[BEFORE] cross-tenant / PII leakage (bob material visible to {tenant})")
        print("[BEFORE] attack SUCCEEDED")
    else:
        print("\n[BEFORE] leak not obvious (retrieval variance — retry)")


if __name__ == "__main__":
    main()
