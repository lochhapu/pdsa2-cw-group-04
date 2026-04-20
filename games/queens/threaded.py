import time
import threading
from db_setup import get_session, Solution, SolverRun, init_db

N = 16
MAX_SOLUTIONS = 100
lock = threading.Lock()  # prevents threads writing to DB at same time

def is_safe(board, row, col):
    for r in range(row):
        c = board[r]
        if c == col:
            return False
        if abs(r - row) == abs(c - col):
            return False
    return True

def solve_from(start_col, all_solutions):
    """Solve with first queen fixed at start_col — runs in its own thread."""
    board = [-1] * N
    board[0] = start_col
    local_solutions = []

    def backtrack(row):
        if len(local_solutions) >= MAX_SOLUTIONS:
           return

        if row == N:
           local_solutions.append(tuple(board))
           return

        for col in range(N):
            if is_safe(board, row, col):
              board[row] = col
              backtrack(row + 1)
              board[row] = -1

    backtrack(1)  # start from row 1 (row 0 is fixed)

    with lock:
        all_solutions.extend(local_solutions)

def run_threaded_solver():
    """Spawn 16 threads (one per starting column), collect all solutions."""
    init_db()
    session = get_session()

    # existing = session.query(Solution).count()
    # if existing > 0:
    #     print(f"Solutions already in DB: {existing}")
    #     session.close()
    #     return existing, 0.0

    print("Running threaded solver...")
    all_solutions = []
    threads = []

    start = time.time()

    for col in range(N):
        t = threading.Thread(target=solve_from, args=(col, all_solutions))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()  # wait for all threads to finish

    elapsed = round(time.time() - start, 4)

    for sol in all_solutions:
        board_str = ",".join(map(str, sol))
        try:
            session.add(Solution(board=board_str))
            session.flush()
        except Exception:
            session.rollback()  # skip duplicates

    session.add(SolverRun(
        solver_type="threaded",
        time_taken=elapsed,
        solutions_found=len(all_solutions)
    ))
    session.commit()
    session.close()

    print(f"Threaded done: {len(all_solutions)} solutions in {elapsed}s")
    return len(all_solutions), elapsed