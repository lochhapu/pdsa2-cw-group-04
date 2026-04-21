import sqlite3

def dump_sqlite_db(db_path, output_file):
    conn = sqlite3.connect(db_path)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in conn.iterdump():
            f.write(f"{line}\n")
    
    conn.close()
    print(f"Database dumped to {output_file}")

if __name__ == "__main__":
    dump_sqlite_db("min_cost_game.db", "dump.sql")