def get_center(row, col, cell_size):
    x = col * cell_size + cell_size // 2
    y = row * cell_size + cell_size // 2
    return x, y