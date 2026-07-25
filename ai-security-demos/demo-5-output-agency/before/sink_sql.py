"""BEFORE — LLM output interpolated into SQL (SQLite). Classic injection sink."""
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from llm import chat

DEFAULT_ATTACK = "Show the user named: alice' OR '1'='1"


def seed_db(path: str) -> None:
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE users (id INTEGER, name TEXT, role TEXT)")
    con.executemany(
        "INSERT INTO users VALUES (?, ?, ?)",
        [(1, "alice", "user"), (2, "bob", "user"), (3, "admin", "admin")],
    )
    con.commit()
    con.close()


def main() -> None:
    user = " ".join(sys.argv[1:]) or DEFAULT_ATTACK
    # LLM extracts a "name filter" — attacker hopes the model echoes the injection
    filter_val = chat(
        "Extract ONLY the username to look up from the user request. "
        "Return the raw name string with no quotes or SQL keywords added by you — "
        "but copy the user's name token exactly as given.",
        user,
    )
    # Strip accidental wrapping quotes from the model
    filter_val = filter_val.strip().strip('"').strip("'")
    print(f"User:   {user}")
    print(f"LLM filter fragment: {filter_val!r}")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db = f.name
    seed_db(db)
    con = sqlite3.connect(db)
    # VULNERABLE: string interpolation of model output into SQL
    sql = f"SELECT id, name, role FROM users WHERE name = '{filter_val}'"
    print(f"SQL:    {sql}")
    try:
        rows = list(con.execute(sql))
    except sqlite3.Error as e:
        print(f"SQL error: {e}")
        rows = []
    con.close()
    print(f"Rows:   {rows}")
    if len(rows) >= 2:
        print("[BEFORE] SQL injection via LLM output")
        print("[BEFORE] attack SUCCEEDED")
    else:
        print("[BEFORE] injection not visible (model may have sanitized — retry)")


if __name__ == "__main__":
    main()
