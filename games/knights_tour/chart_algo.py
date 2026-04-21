import os
import sqlite3
from pathlib import Path
import matplotlib.pyplot as plt

def display_algorithm_chart():
    """Fetches algorithm test execution times from the database and plots them using matplotlib."""
    
    db_path = Path(__file__).parent / "db" / "knightstourdb.db"
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query results for Warnsdorff and Backtracking algorithms
        query = '''
            SELECT 
                r.round_id,
                a.name as algorithm,
                ar.execution_time_ms,
                bs.dimension
            FROM algorithm_result ar
            JOIN algorithm a ON ar.algo_id = a.algo_id
            JOIN game_round r ON ar.round_id = r.round_id
            JOIN board_size bs ON r.size_id = bs.size_id
            WHERE a.name LIKE '%Warnsdorff%' OR a.name LIKE '%Backtracking%'
            ORDER BY ar.recorded_at ASC
        '''
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print("No algorithm test data found in the database.")
            print("Please ensure you have run the algorithm comparisons or played the game to generate data before visualizing.")
            return
            
        warnsdorff_runs = []
        warnsdorff_times = []
        
        backtracking_runs = []
        backtracking_times = []
        
        w_idx = 1
        b_idx = 1
        
        for row in rows:
            round_id, algo, exe_time, dimension = row
            if 'Warnsdorff' in algo:
                warnsdorff_runs.append(w_idx)
                warnsdorff_times.append(exe_time)
                w_idx += 1
            elif 'Backtracking' in algo:
                backtracking_runs.append(b_idx)
                backtracking_times.append(exe_time)
                b_idx += 1
                
        # Setup Chart
        plt.figure(figsize=(10, 6))
        
        if warnsdorff_times:
            plt.plot(warnsdorff_runs, warnsdorff_times, marker='o', linestyle='-', color='#2ca02c', label='Warnsdorff Algorithm')
        
        if backtracking_times:
            plt.plot(backtracking_runs, backtracking_times, marker='s', linestyle='--', color='#1f77b4', label='Backtracking Algorithm')

        plt.title("Knight's Tour: Backtracking vs Warnsdorff (Execution Time)", fontsize=14, pad=15)
        plt.xlabel("Execution Run / Game Round", fontsize=12)
        plt.ylabel("Execution Time (milliseconds)", fontsize=12)
        plt.grid(True, linestyle=':', alpha=0.7)
        plt.legend(loc="upper right")
        
        # Adding some margin to avoid clipping
        plt.tight_layout()
        
        # Save output specifically next to the script
        save_path = Path(__file__).parent / "algorithm_comparison_chart.png"
        plt.savefig(save_path, bbox_inches='tight')
        print(f"Chart successfully generated and saved to: {save_path}")
        
        # Display the chart to the user window
        plt.show()

    except sqlite3.Error as e:
        print(f"Failed to query database: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    display_algorithm_chart()
