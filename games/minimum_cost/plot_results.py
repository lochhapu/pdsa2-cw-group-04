import sqlite3
import matplotlib.pyplot as plt

# Connect to database
conn = sqlite3.connect("min_cost_game.db")
c = conn.cursor()

# Get last 20 rounds
c.execute("""
SELECT round_id, greedy_time, hungarian_time 
FROM results 
ORDER BY round_id DESC 
LIMIT 20
""")
data = c.fetchall()
data.reverse()

conn.close()

# Extract data
rounds = []
greedy_times = []
hungarian_times = []

for row in data:
    round_id, g_time, h_time = row
    rounds.append(round_id)
    greedy_times.append(g_time)
    hungarian_times.append(h_time)

# Plot
plt.figure()

plt.plot(rounds, greedy_times, marker='o', label='Greedy Algorithm')
plt.plot(rounds, hungarian_times, marker='s', label='Hungarian Algorithm')

plt.xlabel("Game Round")
plt.ylabel("Execution Time (seconds)")
plt.title("Algorithm Time Comparison Over 20 Rounds")

plt.legend()
plt.grid()

plt.show()