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