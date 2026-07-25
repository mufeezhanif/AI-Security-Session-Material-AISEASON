# Running garak against Groq (OpenAI-compatible)

Garak probes the model for jailbreaks / leakage. Point it at **Groq**, not OpenAI.

## Prerequisites

```bash
pip install garak
# GROQ_API_KEY in .env — garak's OpenAI-compatible path reads OPENAI_API_KEY
```

On Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = $env:GROQ_API_KEY   # same Groq key
$env:OPENAI_BASE_URL = "https://api.groq.com/openai/v1"
# some garak versions use:
$env:OPENAI_API_BASE = "https://api.groq.com/openai/v1"
```

## Example probe (small / classroom-friendly)

```bash
garak --model_type openai.OpenAICompatible `
  --model_name llama-3.3-70b-versatile `
  --probes promptinject `
  --generations 1
```

Or:

```bash
garak -m openai.OpenAICompatible -n llama-3.3-70b-versatile -p dan,promptinject --generations 1
```

Exact flags vary by garak version — run `garak --help` if a flag differs.

## Against demo-4 HTTP instead

Garak is model-centric. Prefer **promptfoo** (`promptfooconfig.yaml`) for the FastAPI `/chat` target. Use garak for direct Groq probing; promote any failing probe into `regression_tests.py`.

## After a hit

1. Copy the failing payload into [`attacks.md`](attacks.md).
2. Add a pytest case in [`regression_tests.py`](regression_tests.py).
3. Re-run `pytest` in CI so the attack cannot regress silently.
