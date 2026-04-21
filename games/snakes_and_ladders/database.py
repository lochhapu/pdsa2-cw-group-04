import sqlite3

DB_NAME = "snake_ladder.db"

def get_connection():
    return sqlite3.connect(DB_NAME)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Enable foreign key enforcement in SQLite
    cursor.execute("PRAGMA foreign_keys = ON")

    # Players — stores only player identity
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT    NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Game Sessions — one row per game played
    # board_size is a session-level attribute (same for all 5 rounds)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS game_sessions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id   INTEGER NOT NULL,
        board_size  INTEGER NOT NULL,
        final_score INTEGER,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES players(id)
    )
    """)

    # Game Rounds — one row per round within a session
    # player_id removed: already reachable via session_id -> game_sessions
    # board_size removed: already reachable via session_id -> game_sessions
    # player_answer added: stores the raw fact, is_correct derived from it at insert
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS game_rounds (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id     INTEGER NOT NULL,
        round_number   INTEGER NOT NULL,
        correct_answer INTEGER NOT NULL,
        player_answer  INTEGER,
        is_correct     INTEGER NOT NULL DEFAULT 0,
        bfs_time       REAL,
        dfs_time       REAL,
        created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES game_sessions(id)
    )
    """)

    conn.commit()
    conn.close()