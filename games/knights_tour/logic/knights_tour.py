from logic.moves import MOVES

def is_valid(x, y, board, size):
    return 0 <= x < size and 0 <= y < size and board[x][y] == -1

def count_moves(x, y, board, size):
    count = 0
    for dx, dy in MOVES:
        if is_valid(x + dx, y + dy, board, size):
            count += 1
    return count

def knights_tour(size, start=(0, 0), visited_path=None):
    board = [[-1 for _ in range(size)] for _ in range(size)]

    if visited_path is None:
        visited_path = []

    # Initialize the board with the player's visited path
    for step, (px, py) in enumerate(visited_path):
        board[px][py] = step

    if visited_path:
        x, y = visited_path[-1]
        start_step = len(visited_path)
        path = list(visited_path)
    else:
        x, y = start
        board[x][y] = 0
        path = [(x, y)]
        start_step = 1

    for step in range(start_step, size * size):
        next_moves = []

        for dx, dy in MOVES:
            nx, ny = x + dx, y + dy
            if is_valid(nx, ny, board, size):
                c = count_moves(nx, ny, board, size)
                next_moves.append((c, nx, ny))

        if not next_moves:
            return None

        next_moves.sort()
        _, x, y = next_moves[0]

        board[x][y] = step
        path.append((x, y))

    return path


def knights_tour_backtracking(size, start=(0, 0)):
    """
    Solves the Knight's Tour problem using backtracking algorithm.
    
    Args:
        size: Board size (e.g., 8 for 8x8 board)
        start: Starting position as tuple (row, col)
    
    Returns:
        Path as list of tuples if solution found, None otherwise
    """
    board = [[-1 for _ in range(size)] for _ in range(size)]
    path = []
    
    def backtrack(x, y, step):
        # Mark current position as visited with step number
        board[x][y] = step
        path.append((x, y))
        
        # Base case: all squares visited
        if step == size * size - 1:
            return True
        
        # Try all possible knight moves from current position
        for dx, dy in MOVES:
            nx, ny = x + dx, y + dy
            if is_valid(nx, ny, board, size):
                if backtrack(nx, ny, step + 1):
                    return True
        
        # Backtrack: unmark current position and remove from path
        board[x][y] = -1
        path.pop()
        return False
    
    x, y = start
    board[x][y] = 0
    path.append((x, y))
    
    if backtrack(x, y, 1):
        return path
    else:
        return None