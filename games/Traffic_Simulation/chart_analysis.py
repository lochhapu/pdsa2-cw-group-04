"""
traffic_chart.py
Run this file independently to simulate 20 rounds of the Traffic Flow Game
and display a comparison chart of Ford-Fulkerson vs Edmonds-Karp execution times.

Run with: python traffic_chart.py
Requires:  traffic_game.py in the same folder
           pip install matplotlib
"""

import time
import copy
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Pull only the algorithm functions and graph generator from the game
from traffic_game import generate_graph, ford_fulkerson, edmonds_karp

# ─────────────────────────────────────────────
#  SIMULATE 20 ROUNDS
# ─────────────────────────────────────────────
TOTAL_ROUNDS = 20

round_numbers = []
ff_times      = []   # Ford-Fulkerson (DFS) times in ms
ek_times      = []   # Edmonds-Karp  (BFS) times in ms

print("Simulating 20 rounds...\n")
print(f"{'Round':<8} {'FF (ms)':<14} {'EK (ms)':<14} {'Max Flow'}")
print("-" * 48)

for r in range(1, TOTAL_ROUNDS + 1):
    graph, _ = generate_graph()

    # Time Ford-Fulkerson
    t0 = time.perf_counter()
    flow = ford_fulkerson(copy.deepcopy(graph))
    ff_ms = (time.perf_counter() - t0) * 1000

    # Time Edmonds-Karp
    t0 = time.perf_counter()
    edmonds_karp(copy.deepcopy(graph))
    ek_ms = (time.perf_counter() - t0) * 1000

    round_numbers.append(r)
    ff_times.append(ff_ms)
    ek_times.append(ek_ms)

    print(f"{r:<8} {ff_ms:<14.4f} {ek_ms:<14.4f} {flow}")

# ─────────────────────────────────────────────
#  PLOT
# ─────────────────────────────────────────────
BG      = "#0d0f14"
CARD    = "#141720"
AMBER   = "#f0a500"
GREEN   = "#22c97a"
FG      = "#e8eaf2"
FG2     = "#9498b0"
GRID    = "#252836"

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor(BG)
ax.set_facecolor(CARD)

# Plot lines
ax.plot(round_numbers, ff_times,
        marker='o', markersize=7, linewidth=2,
        color=AMBER, label="Ford-Fulkerson (DFS)")

ax.plot(round_numbers, ek_times,
        marker='s', markersize=7, linewidth=2,
        color=GREEN, label="Edmonds-Karp (BFS)")

# Titles and labels
ax.set_title("Algorithm Execution Time per Round  ·  20 Rounds",
             color=FG, fontsize=14, fontweight='bold', pad=16)
ax.set_xlabel("Round Number", color=FG2, fontsize=11)
ax.set_ylabel("Execution Time (ms)", color=FG2, fontsize=11)

# Ticks
ax.set_xticks(round_numbers)
ax.tick_params(colors=FG2)
for spine in ax.spines.values():
    spine.set_edgecolor(GRID)

# Grid
ax.grid(True, color=GRID, linestyle='--', linewidth=0.8, alpha=0.8)

# Legend
ff_patch = mpatches.Patch(color=AMBER, label="Ford-Fulkerson (DFS)")
ek_patch = mpatches.Patch(color=GREEN, label="Edmonds-Karp  (BFS)")
ax.legend(handles=[ff_patch, ek_patch],
          facecolor=CARD, edgecolor=GRID,
          labelcolor=FG, fontsize=10)

plt.tight_layout()
plt.show()