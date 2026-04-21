import sqlite3

conn = sqlite3.connect("queens.db")

with open("dump.sql", "w") as f:
    for line in conn.iterdump():
        f.write(line + "\n")

conn.close()

print("Dump created successfully")