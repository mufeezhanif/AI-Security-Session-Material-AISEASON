"""
Seed multi-tenant docs (alice / bob) with fake PII + planted secrets.

Embeddings: chromadb DEFAULT local (all-MiniLM-L6-v2). Never call a Groq embeddings API.
All PII is fake / educational.
"""
from __future__ import annotations

from typing import Any

import chromadb

# Fake planted values
ALICE_SECRET = "ALICE-PLANTED-SECRET-11"
BOB_SECRET = "BOB-PLANTED-SECRET-77"

DOCS: list[dict[str, str]] = [
    {
        "id": "alice-profile",
        "tenant": "alice",
        "text": (
            "Alice tenant profile. Contact: alice.demo@example.com, phone 555-010-1001. "
            f"Internal note for Alice only: {ALICE_SECRET}."
        ),
    },
    {
        "id": "alice-orders",
        "tenant": "alice",
        "text": "Alice order history: widget x2 shipped to her address on file. No other tenants.",
    },
    {
        "id": "bob-profile",
        "tenant": "bob",
        "text": (
            "Bob PRIVATE profile. Email bob.private@example.com, phone 555-010-2002, "
            f"SSN 123-45-6789. Planted secret for Bob only: {BOB_SECRET}. "
            "Do not share with other tenants."
        ),
    },
    {
        "id": "bob-hr",
        "tenant": "bob",
        "text": (
            "Bob HR file (confidential). Manager notes and payroll alias bob.hr@example.com. "
            f"Access code {BOB_SECRET}."
        ),
    },
]


def build_collection(
    name: str = "demo6_tenants",
    *,
    redact_at_ingest: bool = False,
    redact_fn=None,
) -> Any:
    """In-memory Chroma collection with optional PII redaction at ingest."""
    client = chromadb.Client()
    try:
        client.delete_collection(name)
    except Exception:
        pass
    col = client.create_collection(name=name)

    ids, documents, metadatas = [], [], []
    for d in DOCS:
        text = d["text"]
        if redact_at_ingest and redact_fn is not None:
            text = redact_fn(text)
        ids.append(d["id"])
        documents.append(text)
        metadatas.append({"tenant": d["tenant"]})

    col.add(ids=ids, documents=documents, metadatas=metadatas)
    return col


def query_raw(col: Any, query: str, n: int = 3) -> list[dict[str, Any]]:
    """Retrieve without ACL — BEFORE path."""
    res = col.query(query_texts=[query], n_results=n, include=["documents", "metadatas"])
    out = []
    docs = res["documents"][0] if res["documents"] else []
    metas = res["metadatas"][0] if res["metadatas"] else []
    for doc, meta in zip(docs, metas):
        out.append({"text": doc, "tenant": (meta or {}).get("tenant")})
    return out


def query_for_tenant(col: Any, query: str, tenant: str, n: int = 3) -> list[dict[str, Any]]:
    """Retrieve with document-level ACL (metadata tenant match) — AFTER path."""
    res = col.query(
        query_texts=[query],
        n_results=n,
        where={"tenant": tenant},
        include=["documents", "metadatas"],
    )
    out = []
    docs = res["documents"][0] if res["documents"] else []
    metas = res["metadatas"][0] if res["metadatas"] else []
    for doc, meta in zip(docs, metas):
        out.append({"text": doc, "tenant": (meta or {}).get("tenant")})
    return out
