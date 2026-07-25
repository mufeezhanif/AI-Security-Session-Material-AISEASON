"""
Layered guardrails for the AFTER /chat pipeline.

Layers:
  1. Input: regex/heuristic injection pre-filter + Llama Guard (Groq) + llm-guard Regex
  2. Output: Llama Guard (same model; Groq has no OpenAI Moderation API) + PII redaction
  3. Structured: Pydantic ChatResponse (validated by FastAPI)
  4. Framework: llm-guard scanners wrap input/output
     Swap to guardrails-ai: see `run_with_guardrails_ai` stub + README note.
"""
from __future__ import annotations

import re
from typing import Literal

from llm import PLANTED_SECRET, SUPPORT_SYSTEM, get_client, get_guard_model, get_model
from schemas import ChatResponse

# --- 1a. Lightweight heuristic pre-filter (injection-ish phrasing) ---
INJECTION_RE = re.compile(
    r"ignore (all |any )?(previous|prior|above) (instructions|prompts)|"
    r"disregard (the )?(rules|instructions|system)|"
    r"print (your )?system prompt|"
    r"reveal (your )?(system|hidden) (prompt|instructions)|"
    r"jailbreak|dan mode|developer mode",
    re.I,
)

# Fake PII patterns for classroom redaction demos
PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[EMAIL_REDACTED]"),
    (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "[PHONE_REDACTED]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_REDACTED]"),
    (re.compile(re.escape(PLANTED_SECRET), re.I), "[SECRET_REDACTED]"),
]


def heuristic_injection(text: str) -> bool:
    return bool(INJECTION_RE.search(text))


def redact_pii(text: str) -> tuple[str, bool]:
    """Return (redacted_text, changed?)."""
    out = text
    changed = False
    for pat, repl in PII_PATTERNS:
        new = pat.sub(repl, out)
        if new != out:
            changed = True
            out = new
    return out, changed


def llama_guard(
    text: str,
    role: Literal["user", "assistant"] = "user",
) -> tuple[bool, str]:
    """
    Call Llama Guard on Groq. Returns (is_safe, detail).
    Groq has no Moderation endpoint — this is the substitute.
    """
    # Compact prompt compatible with Llama Guard style classifiers
    prompt = (
        f"Check whether the following {role} message is safe for a customer-support chatbot. "
        "Reply with exactly 'safe' or 'unsafe' on the first line, then an optional category "
        "(S1 violent crimes, S2 scams, S7 privacy, S11 jailbreak/injection, etc.).\n\n"
        f"<{role}>\n{text}\n</{role}>"
    )
    try:
        r = get_client().chat.completions.create(
            model=get_guard_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=64,
        )
        detail = (r.choices[0].message.content or "").strip()
    except Exception as e:  # noqa: BLE001 — demo should still run if guard model unavailable
        # Fail open for connectivity issues would be unsafe in prod; here we fail closed on errors
        # except we note the error — prefer fail-closed for teaching:
        return False, f"llama_guard_error:{e}"
    first = detail.splitlines()[0].strip().lower() if detail else "unsafe"
    is_safe = first.startswith("safe") and not first.startswith("unsafe")
    return is_safe, detail.replace("\n", " | ")[:200]


def _llm_guard_scanners():
    """
    Framework layer — llm-guard Regex scanners.
    To swap to guardrails-ai, see run_with_guardrails_ai() below and README.
    """
    from llm_guard.input_scanners import Regex as InRegex
    from llm_guard.input_scanners.regex import MatchType
    from llm_guard.output_scanners import Regex as OutRegex

    # Block classic injection phrases / secret exfil patterns at framework edge
    in_scan = InRegex(
        patterns=[
            r"(?i)ignore (all |any )?(previous|prior|above)",
            r"(?i)system prompt",
            r"(?i)FAKE-GUARD-SECRET",
        ],
        is_blocked=True,
        match_type=MatchType.SEARCH,
        redact=False,
    )
    out_scan = OutRegex(
        patterns=[
            re.escape(PLANTED_SECRET),
            r"(?i)attacker\.example",
            r"!\[[^\]]*\]\(https?://[^)]+\)",
        ],
        is_blocked=True,
        match_type=MatchType.SEARCH,
        redact=False,
    )
    return in_scan, out_scan


def llm_guard_input(text: str) -> tuple[bool, str]:
    """Returns (allowed, reason)."""
    try:
        in_scan, _ = _llm_guard_scanners()
        _sanitized, is_valid, risk = in_scan.scan(text)
        if not is_valid:
            return False, f"llm-guard input Regex risk={risk}"
        return True, "ok"
    except Exception as e:  # noqa: BLE001
        # If llm-guard missing/misconfigured, fall back to heuristic only (already run)
        return True, f"llm-guard skipped ({e})"


def llm_guard_output(prompt: str, text: str) -> tuple[bool, str]:
    """Output Regex.scan(prompt, output) per llm-guard API."""
    try:
        _, out_scan = _llm_guard_scanners()
        _sanitized, is_valid, risk = out_scan.scan(prompt, text)
        if not is_valid:
            return False, f"llm-guard output Regex risk={risk}"
        return True, "ok"
    except Exception as e:  # noqa: BLE001
        return True, f"llm-guard skipped ({e})"


def call_llm(user_message: str) -> str:
    r = get_client().chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": SUPPORT_SYSTEM},
            {"role": "user", "content": user_message},
        ],
    )
    return r.choices[0].message.content or ""


def run_secured_chat(message: str) -> ChatResponse:
    """Full defense-in-depth pipeline → validated ChatResponse."""
    # 1a. Heuristic
    if heuristic_injection(message):
        return ChatResponse(
            reply="[BLOCKED] Possible prompt injection (heuristic).",
            blocked=True,
            reason="injection_heuristic",
            layer="input_heuristic",
        )

    # 1b. Llama Guard (input)
    safe, detail = llama_guard(message, role="user")
    if not safe:
        return ChatResponse(
            reply="[BLOCKED] Input failed Llama Guard safety check.",
            blocked=True,
            reason=detail,
            layer="input_llama_guard",
        )

    # 4. llm-guard framework (input)
    ok, why = llm_guard_input(message)
    if not ok:
        return ChatResponse(
            reply="[BLOCKED] Input failed llm-guard scanner.",
            blocked=True,
            reason=why,
            layer="input_llm_guard",
        )

    # LLM
    raw = call_llm(message)

    # 2a. Llama Guard (output) — moderation substitute
    safe_out, detail_out = llama_guard(raw, role="assistant")
    if not safe_out:
        return ChatResponse(
            reply="[BLOCKED] Output failed Llama Guard safety check.",
            blocked=True,
            reason=detail_out,
            layer="output_llama_guard",
        )

    # 2b. PII / secret redaction
    redacted, pii_hit = redact_pii(raw)
    if pii_hit:
        return ChatResponse(
            reply=redacted,
            blocked=True,
            reason="planted_secret_or_pii_redacted",
            layer="output_pii",
        )

    # 4. llm-guard framework (output)
    ok_out, why_out = llm_guard_output(message, redacted)
    if not ok_out:
        return ChatResponse(
            reply="[BLOCKED] Output failed llm-guard scanner.",
            blocked=True,
            reason=why_out,
            layer="output_llm_guard",
        )

    # 3. Structured — caller validates via response_model=ChatResponse
    return ChatResponse(reply=redacted, blocked=False, reason=None, layer=None)


def run_with_guardrails_ai(message: str) -> ChatResponse:
    """
    Optional swap target (not used by default).

    Example sketch::

        from guardrails import Guard
        from schemas import ChatResponse
        guard = Guard.from_pydantic(output_class=ChatResponse)
        # guard(prompt=..., llm_api=...)

    Keep llm-guard as the default framework wrapper; flip AFTER to call this
    instead of run_secured_chat if you prefer guardrails-ai.
    """
    raise NotImplementedError("Swap stub — use run_secured_chat (llm-guard) by default")
