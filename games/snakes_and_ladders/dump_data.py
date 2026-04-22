import sqlite3

DB_NAME = "snake_ladder.db"

def dump_sql():
    conn = sqlite3.connect(DB_NAME)
    
    with open("data_dump.sql", "w") as f:
        for line in conn.iterdump():
            f.write(f"{line}\n")
    
    conn.close()
    print("✅ data_dump.sql created successfully!")

def print_all_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("📋 PLAYERS TABLE")
    print("="*60)
    cursor.execute("SELECT * FROM players")
    players = cursor.fetchall()
    print(f"{'ID':<5} {'NAME':<20} {'CREATED AT':<25}")
    print("-"*60)
    for row in players:
        print(f"{row[0]:<5} {row[1]:<20} {str(row[2]):<25}")

    print("\n" + "="*60)
    print("🎮 GAME ROUNDS TABLE")
    print("="*60)
    cursor.execute("""
        SELECT 
            g.id,
            p.name,
            g.round_number,
            g.board_size,
            g.correct_answer,
            g.bfs_time,
            g.dfs_time,
            g.is_correct
        FROM game_rounds g
        JOIN players p ON p.id = g.player_id
        ORDER BY g.id
    """)
    rounds = cursor.fetchall()
    print(f"{'ID':<5} {'PLAYER':<15} {'ROUND':<7} {'BOARD':<7} {'ANSWER':<8} {'BFS TIME':<12} {'DFS TIME':<12} {'CORRECT':<8}")
    print("-"*80)
    for row in rounds:
        print(f"{row[0]:<5} {row[1]:<15} {row[2]:<7} {row[3]:<7} {row[4]:<8} {row[5]:<12.6f} {row[6]:<12.6f} {'Yes' if row[7] else 'No':<8}")

    print("\n" + "="*60)
    print("📊 SUMMARY PER PLAYER")
    print("="*60)
    cursor.execute("""
        SELECT 
            p.name,
            COUNT(g.id) as total_rounds,
            SUM(g.is_correct) as correct,
            ROUND(AVG(g.bfs_time), 6) as avg_bfs,
            ROUND(AVG(g.dfs_time), 6) as avg_dfs
        FROM game_rounds g
        JOIN players p ON p.id = g.player_id
        GROUP BY p.id
    """)
    summary = cursor.fetchall()
    print(f"{'PLAYER':<15} {'ROUNDS':<8} {'CORRECT':<10} {'AVG BFS':<12} {'AVG DFS':<12}")
    print("-"*60)
    for row in summary:
        print(f"{row[0]:<15} {row[1]:<8} {row[2]:<10} {row[3]:<12.6f} {row[4]:<12.6f}")

    conn.close()

if __name__ == "__main__":
    dump_sql()
    print_all_data()