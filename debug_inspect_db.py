from db import get_conn, init_db

# Initialize schema
init_db()

con = get_conn()
cur = con.execute("INSERT INTO items(name,quantity) VALUES(?,?)", ("X", 1))
item_id = cur.lastrowid
row = con.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
print("fetched row type:", type(row))
print("row as dict:", dict(row))
con.close()
