#Đọc và xuất file

def read_input(file_path):
    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    idx = 0

    N = int(lines[idx])
    idx += 1

    grid = []
    for _ in range(N):
        row = list(map(int, lines[idx].split(',')))
        if len(row) != N:
            raise ValueError("Invalid grid row length")
        grid.append(row)
        idx += 1

    H = []
    for _ in range(N):
        row = list(map(int, lines[idx].split(',')))
        if len(row) != N - 1:
            raise ValueError("Invalid horizontal constraint row length")
        H.append(row)
        idx += 1

    V = []
    for _ in range(N - 1):
        row = list(map(int, lines[idx].split(',')))
        if len(row) != N:
            raise ValueError("Invalid vertical constraint row length")
        V.append(row)
        idx += 1

    return N, grid, H, V


def write_output(file_path, N, grid, H, V):
    with open(file_path, 'w') as f:
        for i in range(N):
            row_str = ""
            for j in range(N):
                row_str += str(grid[i][j])
                if j < N - 1:
                    row_str += " < " if H[i][j] == 1 else (" > " if H[i][j] == -1 else "   ")
            f.write(row_str + "\n")

            if i < N - 1:
                v_str = ""
                for j in range(N):
                    v_str += "^" if V[i][j] == 1 else ("v" if V[i][j] == -1 else " ")
                    if j < N - 1: v_str += "   "
                f.write(v_str + "\n")