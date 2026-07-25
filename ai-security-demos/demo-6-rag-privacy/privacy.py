"""
Privacy controls: document ACL helpers, Presidio PII redaction, outbound exfil guard.

Presidio at ingest + output. If spaCy/Presidio is unavailable, falls back to regex
so the classroom demo still runs (README documents the preferred Presidio path).
"""
from __future__ import annotations

import re
from functools import lru_cache

# --- Outbound exfil guard (markdown images / links / raw URLs) ---
_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]+\)", re.I)
_MD_LINK = re.compile(r"\[[^\]]*\]\((https?://[^)]+)\)", re.I)
_RAW_URL = re.compile(r"https?://[^\s)>\"]+", re.I)

# Regex fallback PII (fake classroom patterns)
_FALLBACK_PII = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "<EMAIL>"),
    (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "<PHONE>"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "<SSN>"),
    (re.compile(r"\b(?:ALICE|BOB)-PLANTED-SECRET-\d+\b"), "<SECRET>"),
]


@lru_cache(maxsize=1)
def _presidio():
    """Lazy-init Presidio analyzer + anonymizer. Returns None if unavailable."""
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine

        return AnalyzerEngine(), AnonymizerEngine()
    except Exception:
        return None


def redact_pii(text: str) -> str:
    """PII detection + redaction (Presidio preferred; regex fallback)."""
    engines = _presidio()
    if engines is not None:
        analyzer, anonymizer = engines
        results = analyzer.analyze(
            text=text,
            language="en",
            entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "PERSON"],
        )
        if results:
            text = anonymizer.anonymize(text=text, analyzer_results=results).text
        # Always scrub planted demo secrets even if Presidio misses them
        text = re.sub(r"\b(?:ALICE|BOB)-PLANTED-SECRET-\d+\b", "<SECRET>", text)
        return text

    out = text
    for pat, repl in _FALLBACK_PII:
        out = pat.sub(repl, out)
    return out


def strip_exfil(text: str) -> tuple[str, bool]:
    """Strip markdown images/links and raw URLs from answers. Returns (text, changed?)."""
    original = text
    text = _MD_IMAGE.sub("[IMAGE_REMOVED]", text)
    text = _MD_LINK.sub("[LINK_REMOVED]", text)
    text = _RAW_URL.sub("[URL_REMOVED]", text)
    return text, text != original


def acl_allows(doc_tenant: str | None, requester: str) -> bool:
    """Document-level ACL: tenant metadata must match requester."""
    return (doc_tenant or "") == requester


def filter_docs_for_tenant(docs: list[dict], tenant: str) -> list[dict]:
    return [d for d in docs if acl_allows(d.get("tenant"), tenant)]
