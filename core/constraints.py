def is_valid(state, row, col, val):
    N = state.N
    grid = state.grid
    H = state.H  
    V = state.V 

    for i in range(N):
        if grid[row][i] == val or grid[i][col] == val:
            return False

    if col < N - 1: # Kiểm tra ô bên phải
        right = grid[row][col + 1]
        if right != 0:
            if H[row][col] == 1 and not (val < right): return False
            if H[row][col] == -1 and not (val > right): return False

    if col > 0: # Kiểm tra ô bên trái
        left = grid[row][col - 1]
        if left != 0:
            if H[row][col - 1] == 1 and not (left < val): return False
            if H[row][col - 1] == -1 and not (left > val): return False

    if row < N - 1: # Kiểm tra ô dưới
        down = grid[row + 1][col]
        if down != 0:
            if V[row][col] == 1 and not (val < down): return False
            if V[row][col] == -1 and not (val > down): return False

    if row > 0: # Kiểm tra ô trên
        up = grid[row - 1][col]
        if up != 0:
            if V[row - 1][col] == 1 and not (up < val): return False
            if V[row - 1][col] == -1 and not (up > val): return False

    return True 