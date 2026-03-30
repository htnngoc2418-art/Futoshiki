class Futoshiki:
    def __init__(self, N, grid, H, V):
        self.N = N
        self.grid = grid
        self.H = H
        self.V = V

    def find_empty(self):
        for i in range(self.N):
            for j in range(self.N):
                if self.grid[i][j] == 0:
                    return i, j
        return None

    def __str__(self):
        return f"Futoshiki Grid {self.N}x{self.N}"
