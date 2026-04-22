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
        fig, ax = plt.subplots(figsize=(10, 6))
        
        lines = []
        if warnsdorff_times:
            line_w, = ax.plot(warnsdorff_runs, warnsdorff_times, marker='o', linestyle='-', color='#2ca02c', label='Warnsdorff Algorithm')
            lines.append(line_w)
        
        if backtracking_times:
            line_b, = ax.plot(backtracking_runs, backtracking_times, marker='s', linestyle='--', color='#1f77b4', label='Backtracking Algorithm')
            lines.append(line_b)

        ax.set_title("Knight's Tour: Backtracking vs Warnsdorff (Execution Time)", fontsize=14, pad=15)
        ax.set_xlabel("Execution Run / Game Round", fontsize=12)
        ax.set_ylabel("Execution Time (milliseconds)", fontsize=12)
        ax.grid(True, linestyle=':', alpha=0.7)
        ax.legend(loc="upper right")
        
        # Add margins to prevent overlapping with edges and title
        ax.margins(x=0.05, y=0.20)
        
        # Tooltip annotation setup
        annot = ax.annotate("", xy=(0,0), xytext=(20,20), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", edgecolor="gray", alpha=0.9),
                            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))
        annot.set_visible(False)

        def update_annot(ind, line):
            x, y = line.get_data()
            x_val = x[ind["ind"][0]]
            y_val = y[ind["ind"][0]]
            annot.xy = (x_val, y_val)
            lbl = line.get_label()
            text = f"{lbl}\nRun: {x_val}\nTime: {y_val:.2f} ms"
            annot.set_text(text)
            annot.get_bbox_patch().set_alpha(0.9)
            
            # Dynamically adjust tooltip position if near the right edge
            xlim = ax.get_xlim()
            if x_val > (xlim[0] + xlim[1]) / 2:
                annot.set_position((-15, 15))
                annot.set_ha("right")
            else:
                annot.set_position((15, 15))
                annot.set_ha("left")

        def hover(event):
            vis = annot.get_visible()
            if event.inaxes == ax:
                for line in lines:
                    cont, ind = line.contains(event)
                    if cont:
                        update_annot(ind, line)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            if vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", hover)
        
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
