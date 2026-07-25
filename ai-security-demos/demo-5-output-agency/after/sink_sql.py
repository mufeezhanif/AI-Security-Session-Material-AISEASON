"""AFTER — parameterized SQL; LLM output used only as a bound parameter."""
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
    filter_val = chat(
        "Extract ONLY the username to look up. Return the raw name token only.",
        user,
    )
    filter_val = filter_val.strip().strip('"').strip("'")
    print(f"User:   {user}")
    print(f"LLM filter fragment: {filter_val!r}")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db = f.name
    seed_db(db)
    con = sqlite3.connect(db)
    # FIXED: parameter binding — injection characters are data, not SQL
    sql = "SELECT id, name, role FROM users WHERE name = ?"
    print(f"SQL:    {sql}  params=({filter_val!r},)")
    rows = list(con.execute(sql, (filter_val,)))
    con.close()
    print(f"Rows:   {rows}")
    if len(rows) <= 1 and not any(r[1] == "admin" for r in rows):
        print("[AFTER] parameterized query — injection neutralized")
        print("[AFTER] attack BLOCKED")
    else:
        print("[AFTER] unexpected row set")
        print("[AFTER] attack SUCCEEDED (unexpected)")


if __name__ == "__main__":
    main()
