import sqlite3
from datetime import datetime
import os
from pathlib import Path

class DatabaseHelper:
    """
    A comprehensive database helper for the Knight's Tour application.
    Handles all database operations including creating tables, saving game results,
    retrieving scores, and managing player data.
    """
    
    def __init__(self, db_path=None):
        """Initialize the database connection and create tables if they don't exist."""
        if db_path is None:
            # Default to db folder next to this file
            db_dir = Path(__file__).parent
            db_path = db_dir / "knightstourdb.db"
        else:
            db_path = Path(db_path)
        
        self.db_path = str(db_path)
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Establish database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            raise Exception(f"Failed to connect to database: {e}")
    
    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        try:
            # Players table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_games INTEGER DEFAULT 0,
                    total_wins INTEGER DEFAULT 0
                )
            ''')
            
            # Game results table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_results (
                    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    board_size INTEGER NOT NULL,
                    start_position TEXT NOT NULL,
                    completion_status TEXT NOT NULL,
                    moves_count INTEGER NOT NULL,
                    total_squares INTEGER NOT NULL,
                    time_taken INTEGER,
                    path TEXT,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id) REFERENCES players(player_id)
                )
            ''')
            
            # Session tracking table (for temporary game sessions)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    board_size INTEGER NOT NULL,
                    start_position TEXT NOT NULL,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    FOREIGN KEY (player_id) REFERENCES players(player_id)
                )
            ''')
            
            self.conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Failed to create tables: {e}")
    
    def create_or_get_player(self, player_name):
        """Create a new player or get existing player ID."""
        try:
            self.cursor.execute('SELECT player_id FROM players WHERE player_name = ?', (player_name,))
            result = self.cursor.fetchone()
            
            if result:
                return result[0]
            else:
                self.cursor.execute('INSERT INTO players (player_name) VALUES (?)', (player_name,))
                self.conn.commit()
                return self.cursor.lastrowid
        except sqlite3.Error as e:
            raise Exception(f"Failed to create/get player: {e}")
    
    def save_game_result(self, player_id, board_size, start_position, completion_status, 
                        moves_count, total_squares, time_taken=None, path=None):
        """
        Save a game result to the database.
        
        Args:
            player_id: ID of the player
            board_size: Size of the board (e.g., 8 for 8x8)
            start_position: Starting position as a string (e.g., "0,0")
            completion_status: Status of the game ("won", "lost", "quit", etc.)
            moves_count: Number of moves made
            total_squares: Total squares on the board (board_size * board_size)
            time_taken: Time taken in seconds (optional)
            path: Full path as a string or list representation (optional)
        """
        try:
            # Convert path to string if it's a list
            if isinstance(path, list):
                path = str(path)
            
            self.cursor.execute('''
                INSERT INTO game_results 
                (player_id, board_size, start_position, completion_status, moves_count, 
                 total_squares, time_taken, path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (player_id, board_size, start_position, completion_status, moves_count, 
                  total_squares, time_taken, path))
            
            self.conn.commit()
            
            # Update player stats if won
            if completion_status.lower() == "won":
                self._update_player_stats(player_id, win=True)
            else:
                self._update_player_stats(player_id, win=False)
            
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            raise Exception(f"Failed to save game result: {e}")
    
    def _update_player_stats(self, player_id, win=False):
        """Update player statistics."""
        try:
            self.cursor.execute('''
                UPDATE players 
                SET total_games = total_games + 1
                WHERE player_id = ?
            ''', (player_id,))
            
            if win:
                self.cursor.execute('''
                    UPDATE players 
                    SET total_wins = total_wins + 1
                    WHERE player_id = ?
                ''', (player_id,))
            
            self.conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Failed to update player stats: {e}")
    
    def get_leaderboard(self, limit=10, order_by="wins"):
        """
        Retrieve the leaderboard.
        
        Args:
            limit: Number of top players to retrieve
            order_by: "wins" or "games" - how to sort the leaderboard
        
        Returns:
            List of tuples containing (player_name, total_games, total_wins, win_rate)
        """
        try:
            if order_by.lower() == "wins":
                query = '''
                    SELECT player_name, total_games, total_wins, 
                           ROUND(CAST(total_wins AS FLOAT) / total_games * 100, 2) as win_rate
                    FROM players
                    WHERE total_games > 0
                    ORDER BY total_wins DESC, win_rate DESC
                    LIMIT ?
                '''
            else:  # order by games
                query = '''
                    SELECT player_name, total_games, total_wins, 
                           ROUND(CAST(total_wins AS FLOAT) / total_games * 100, 2) as win_rate
                    FROM players
                    WHERE total_games > 0
                    ORDER BY total_games DESC
                    LIMIT ?
                '''
            
            self.cursor.execute(query, (limit,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            raise Exception(f"Failed to retrieve leaderboard: {e}")
    
    def get_player_stats(self, player_id):
        """Get statistics for a specific player."""
        try:
            self.cursor.execute('''
                SELECT player_id, player_name, total_games, total_wins, created_at
                FROM players
                WHERE player_id = ?
            ''', (player_id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            raise Exception(f"Failed to retrieve player stats: {e}")
    
    def get_player_game_history(self, player_id, limit=50):
        """Get game history for a specific player."""
        try:
            self.cursor.execute('''
                SELECT game_id, board_size, completion_status, moves_count, 
                       total_squares, time_taken, completed_at
                FROM game_results
                WHERE player_id = ?
                ORDER BY completed_at DESC
                LIMIT ?
            ''', (player_id, limit))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            raise Exception(f"Failed to retrieve player game history: {e}")
    
    def get_stats_by_board_size(self, board_size):
        """Get aggregated statistics for a specific board size."""
        try:
            self.cursor.execute('''
                SELECT board_size, COUNT(*) as total_games,
                       SUM(CASE WHEN completion_status = 'won' THEN 1 ELSE 0 END) as total_wins,
                       AVG(moves_count) as avg_moves,
                       AVG(time_taken) as avg_time
                FROM game_results
                WHERE board_size = ?
                GROUP BY board_size
            ''', (board_size,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            raise Exception(f"Failed to retrieve stats by board size: {e}")
    
    def get_all_board_size_stats(self):
        """Get statistics for all board sizes."""
        try:
            self.cursor.execute('''
                SELECT board_size, COUNT(*) as total_games,
                       SUM(CASE WHEN completion_status = 'won' THEN 1 ELSE 0 END) as total_wins,
                       AVG(moves_count) as avg_moves,
                       AVG(time_taken) as avg_time
                FROM game_results
                GROUP BY board_size
                ORDER BY board_size
            ''')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            raise Exception(f"Failed to retrieve all board size stats: {e}")
    
    def start_game_session(self, player_id, board_size, start_position):
        """Start a new game session and return session ID."""
        try:
            self.cursor.execute('''
                INSERT INTO game_sessions (player_id, board_size, start_position)
                VALUES (?, ?, ?)
            ''', (player_id, board_size, start_position))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            raise Exception(f"Failed to start game session: {e}")
    
    def end_game_session(self, session_id):
        """End a game session."""
        try:
            self.cursor.execute('''
                UPDATE game_sessions 
                SET end_time = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (session_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Failed to end game session: {e}")
    
    def get_all_players(self):
        """Get list of all players."""
        try:
            self.cursor.execute('''
                SELECT player_id, player_name, total_games, total_wins, created_at
                FROM players
                ORDER BY player_name
            ''')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            raise Exception(f"Failed to retrieve all players: {e}")
    
    def delete_player(self, player_id):
        """Delete a player and their game results."""
        try:
            # Delete game results first (foreign key constraint)
            self.cursor.execute('DELETE FROM game_results WHERE player_id = ?', (player_id,))
            self.cursor.execute('DELETE FROM game_sessions WHERE player_id = ?', (player_id,))
            self.cursor.execute('DELETE FROM players WHERE player_id = ?', (player_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Failed to delete player: {e}")
    
    def clear_all_data(self):
        """Clear all data from the database. WARNING: This cannot be undone."""
        try:
            self.cursor.execute('DELETE FROM game_results')
            self.cursor.execute('DELETE FROM game_sessions')
            self.cursor.execute('DELETE FROM players')
            self.conn.commit()
        except sqlite3.Error as e:
            raise Exception(f"Failed to clear database: {e}")
    
    def close(self):
        """Close the database connection."""
        try:
            if self.conn:
                self.conn.close()
        except sqlite3.Error as e:
            raise Exception(f"Failed to close database: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Convenience function for quick access
def get_db(db_path=None):
    """Get a database helper instance."""
    return DatabaseHelper(db_path)


if __name__ == "__main__":
    # Example usage for testing
    with DatabaseHelper() as db:
        # Create a player
        player_id = db.create_or_get_player("TestPlayer")
        print(f"Player ID: {player_id}")
        
        # Save a game result
        game_id = db.save_game_result(
            player_id=player_id,
            board_size=8,
            start_position="0,0",
            completion_status="won",
            moves_count=64,
            total_squares=64,
            time_taken=120,
            path="[(0,0), (1,2), (2,4), ...]"
        )
        print(f"Game saved with ID: {game_id}")
        
        # Get leaderboard
        leaderboard = db.get_leaderboard(limit=5)
        print("Leaderboard:", leaderboard)
        
        # Get player stats
        stats = db.get_player_stats(player_id)
        print("Player stats:", stats)
