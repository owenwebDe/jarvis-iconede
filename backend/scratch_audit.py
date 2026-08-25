import sqlite3
import os
import sys

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("========================================")
print("  JARVIS WORK VERIFICATION AUDIT")
print("========================================")

# 1. Inspect data directory
print("\n--- 1. FILES IN DATA DIRECTORY ---")
for f in os.listdir("data"):
    fpath = os.path.join("data", f)
    if os.path.isfile(fpath):
        size = os.path.getsize(fpath)
        print(f"File: {f} ({size} bytes)")
    else:
        print(f"Directory: {f}")

# 2. Inspect SQLite Database
db_path = os.path.join("data", "jarvis.db")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"\n--- 2. DATABASE TABLES IN {db_path} ---")
    for t in tables:
        count = cur.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
        print(f"Table '{t}': {count} rows")
        if count > 0:
            cols = [d[0] for d in cur.execute(f'SELECT * FROM "{t}" LIMIT 1').description]
            print(f"  Columns: {cols}")
            sample = cur.execute(f'SELECT * FROM "{t}" ORDER BY rowid DESC LIMIT 5').fetchall()
            for row in sample:
                print(f"  -> {row}")
    conn.close()

# 3. Inspect Spawns in Registry
reg_db = os.path.join("data", "agents_registry.db")
if os.path.exists(reg_db):
    conn = sqlite3.connect(reg_db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"\n--- 3. AGENT REGISTRY IN {reg_db} ---")
    for t in tables:
        count = cur.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
        print(f"Table '{t}': {count} rows")
        sample = cur.execute(f'SELECT * FROM "{t}" ORDER BY rowid DESC LIMIT 5').fetchall()
        for row in sample:
            print(f"  -> {row}")
    conn.close()
