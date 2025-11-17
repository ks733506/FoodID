"""Quick inspection of DB schema, sample rows, and insert behavior for debugging."""

import pprint

from db import get_conn, init_db

print("Initializing DB (runs init_db())")
try:
    init_db()
except Exception as e:
    print("init_db() raised:", repr(e))

with get_conn() as con:
    print("\nPRAGMA database_list:")
    pprint.pprint(con.execute("PRAGMA database_list").fetchall())

    print('\nPRAGMA table_info("items"):')
    pprint.pprint(con.execute("PRAGMA table_info('items')").fetchall())

    print("\nExisting rows (first 3):")
    rows = con.execute("SELECT * FROM items LIMIT 3").fetchall()
    for r in rows:
        try:
            print(dict(r))
        except Exception:
            print("Could not convert row to dict, raw:", r)

    print("\nInserting a test row to observe defaults...")
    cur = con.execute(
        "INSERT INTO items(name,quantity) VALUES(?,?)", ("InspectItem", 7)
    )
    inserted_id = cur.lastrowid
    new_row = con.execute("SELECT * FROM items WHERE id=?", (inserted_id,)).fetchone()
    try:
        print("Inserted row:", dict(new_row))
    except Exception:
        print("Inserted raw row:", new_row)

print("\nDone")
