import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import time
from sequential import run_sequential_solver
from threaded import run_threaded_solver

def generate_comparison_chart():
    print("Starting 20 rounds of algorithm analysis...")
    seq_times = []
    thr_times = []
    rounds = list(range(1,21))
    
    print("Running Sequential Algorithm...")
    for i in rounds:
        _, t = run_sequential_solver()
        seq_times.append(t)
        print(f"  Round {i}: {t:.4f}s")
        

    print("\nRunning Threaded Algorithm...")
    for i in rounds:
        _, t = run_threaded_solver()
        thr_times.append(t)
        print(f"  Round {i}: {t:.4f}s")
        
    plt.figure(figsize=(8, 4))
    
    # Plotting both
    plt.plot(rounds, seq_times, marker='o', linestyle='-', color='purple', label='Sequential Technique')
    plt.plot(rounds, thr_times, marker='s', linestyle='--', color='blue', label='Threaded Technique')
    
    plt.title('Algorithm Time Taken Comparison over 20 Rounds', fontsize=14, pad=15)
    plt.xlabel('Game Round', fontsize=12)
    plt.ylabel('Time Taken (Seconds)', fontsize=12)
    plt.xticks(rounds)
    plt.legend(loc='upper right')
    plt.grid(True, linestyle=':', alpha=0.7)
    
    # Save the chart
    save_path = 'algorithm_comparison_chart.png'
    plt.savefig(save_path, bbox_inches='tight')
    print(f"\nChart successfully generated and saved to {save_path}")

    

    plt.gca().yaxis.set_major_locator(mticker.MultipleLocator(0.1))
    plt.gca().yaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))
    
    # Optional: Display the interactive chart
    plt.show()

if __name__ == "__main__":
    generate_comparison_chart()
