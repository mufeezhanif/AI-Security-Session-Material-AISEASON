"""Shared sandbox helpers — ALL destructive/file ops stay under ./sandbox only."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SANDBOX = ROOT / "sandbox"


def reset_sandbox() -> Path:
    """Create a clean sandbox with a couple of demo files."""
    if SANDBOX.exists():
        shutil.rmtree(SANDBOX)
    SANDBOX.mkdir(parents=True)
    (SANDBOX / "notes.txt").write_text("demo notes — safe to delete in class\n", encoding="utf-8")
    (SANDBOX / "data.csv").write_text("id,name\n1,alice\n", encoding="utf-8")
    return SANDBOX


def resolve_in_sandbox(user_path: str) -> Path:
    """Resolve a path and ensure it stays inside SANDBOX (no escape)."""
    raw = Path(user_path)
    candidate = (SANDBOX / raw).resolve() if not raw.is_absolute() else raw.resolve()
    sandbox_resolved = SANDBOX.resolve()
    if sandbox_resolved not in candidate.parents and candidate != sandbox_resolved:
        # Also allow paths written as sandbox/foo
        try:
            candidate.relative_to(sandbox_resolved)
        except ValueError as e:
            raise PermissionError(f"path escapes sandbox: {user_path}") from e
    try:
        candidate.relative_to(sandbox_resolved)
    except ValueError as e:
        raise PermissionError(f"path escapes sandbox: {user_path}") from e
    return candidate
