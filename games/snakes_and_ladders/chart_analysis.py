import matplotlib.pyplot as plt

# ---------------- DATA STORAGE ---------------- #
round_numbers = []
bfs_times = []
dfs_times = []
round_data = []


# ---------------- STORE DATA ---------------- #
def add_round_data(round_no, bfs_time, dfs_time):
    round_numbers.append(round_no)
    round_data.append((round_no, bfs_time, dfs_time))
    bfs_times.append(bfs_time)
    dfs_times.append(dfs_time)


# ---------------- PLOT CHART ---------------- #
def show_time_chart():
    plt.figure(figsize=(8, 5))

    plt.plot(round_numbers, bfs_times, marker='o', label="BFS Time")
    plt.plot(round_numbers, dfs_times, marker='o', label="DFS Time")

    plt.title("BFS vs DFS Time per Round (20 Rounds)")
    plt.xlabel("Round Number")
    plt.ylabel("Time (seconds)")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()