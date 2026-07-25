"""
Compare BEFORE vs AFTER for the SAME alice query.

Prints what leaked vs what was isolated/redacted.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "before"))
sys.path.insert(0, str(ROOT / "after"))

# Import modules under aliases to avoid name clash
import importlib.util


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


before_mod = _load("before_rag", ROOT / "before" / "rag.py")
after_mod = _load("after_rag", ROOT / "after" / "rag.py")

from seed_docs import BOB_SECRET  # noqa: E402

QUERY = "What private profile secrets and contact details do you know?"
TENANT = "alice"

MARKERS = [
    BOB_SECRET,
    "bob.private@example.com",
    "123-45-6789",
    "555-010-2002",
    "bob.hr@example.com",
]


def hits(text: str) -> list[str]:
    return [m for m in MARKERS if m in text]


def main() -> None:
    print("=" * 72)
    print(f"COMPARE as tenant={TENANT!r} query={QUERY!r}")
    print("=" * 72)

    print("\n--- BEFORE ---")
    b_reply, b_docs, b_log = before_mod.answer(TENANT, QUERY)
    b_ctx = "\n".join(d["text"] for d in b_docs)
    print(f"Retrieved tenants: {[d['tenant'] for d in b_docs]}")
    print(f"Answer:\n{b_reply}\n")

    print("--- AFTER ---")
    a_reply, a_docs, a_log = after_mod.answer(TENANT, QUERY)
    a_ctx = "\n".join(d["text"] for d in a_docs)
    print(f"Retrieved tenants: {[d['tenant'] for d in a_docs]}")
    print(f"Answer:\n{a_reply}\n")

    print("=" * 72)
    print(f"{'marker':<28} | {'before':^10} | {'after':^10}")
    print("-" * 72)
    for m in MARKERS:
        in_b = m in b_reply or m in b_ctx or m in b_log
        in_a = m in a_reply or m in a_ctx or m in a_log
        print(f"{m:<28} | {'LEAKED' if in_b else '—':^10} | {'held' if not in_a else 'LEAK':^10}")

    print()
    if hits(b_reply + b_ctx):
        print("[BEFORE] attack SUCCEEDED — bob PII/secret reachable as alice")
    if not hits(a_reply + a_ctx):
        print("[AFTER] attack BLOCKED — ACL + redaction isolated alice")
    else:
        print("[AFTER] residual marker found — check Presidio/ACL config")


if __name__ == "__main__":
    main()
