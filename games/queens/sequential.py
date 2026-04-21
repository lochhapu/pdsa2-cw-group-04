import time
from db_setup import get_session, Solution, SolverRun, init_db

N = 16  # board size
MAX_SOLUTIONS = 100   # limited to first 100 solutions only

def is_safe(board, row, col):
    """Check if placing queen at (row, col) is safe."""
    for r in range(row):
        c = board[r]
        if c == col:                        # same column
            return False
        if abs(r - row) == abs(c - col):   # same diagonal
            return False
    return True

def solve(board, row, solutions):
    # Stop if limit reached
    if len(solutions) >= MAX_SOLUTIONS:
        return

    if row == N:
        solutions.append(tuple(board))
        return

    for col in range(N):
        if is_safe(board, row, col):
            board[row] = col
            solve(board, row + 1, solutions)
            board[row] = -1  # backtrack

def run_sequential_solver():
    """Run solver, save results to DB, return (solutions, time_taken)."""
    init_db()
    session = get_session()

    # # Check if already solved
    # existing = session.query(Solution).count()
    # if existing > 0:
    #     print(f"Solutions already in DB: {existing}")
    #     session.close()
    #     return existing, 0.0

    print("Running sequential solver... (this may take a while for N=16)")
    board = [-1] * N
    solutions = []

    start = time.time()
    solve(board, 0, solutions)
    elapsed = round(time.time() - start, 4)

    # Save solutions to DB
    for sol in solutions:
        board_str = ",".join(map(str, sol))
        session.add(Solution(board=board_str))

    # Save performance log
    session.add(SolverRun(
        solver_type="sequential",
        time_taken=elapsed,
        solutions_found=len(solutions)
    ))
    session.commit()
    session.close()

    print(f"Sequential done: {len(solutions)} solutions in {elapsed}s")
    return len(solutions), elapsed