import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
from typing import Optional, Callable
from knowledge_base import KnowledgeBase, generate_ground_kb_from_file

class FutoshikiSolver:
    def __init__(self, kb: KnowledgeBase, initial_assignment: dict):
        self.kb = kb
        self.assignment = initial_assignment.copy()
        self.attempts = 0
        self.backtracks = 0
        self.start_time = None

    def _is_valid(self, r: int, c: int, v: int) -> bool:
        N = self.kb.N
        assignment = self.assignment

        # Check hàng
        for col in range(N):
            if col != c and assignment.get((r, col)) == v:
                return False

        # Check cột
        for row in range(N):
            if row != r and assignment.get((row, c)) == v:
                return False

        facts = self.kb.facts

        # Horizontal
        if c > 0 and (r, c - 1) in facts["LessH"]:
            left = assignment.get((r, c - 1))
            if left is not None and left >= v:
                return False

        if c > 0 and (r, c - 1) in facts["GreaterH"]:
            left = assignment.get((r, c - 1))
            if left is not None and left <= v:
                return False

        if c < N - 1 and (r, c) in facts["LessH"]:
            right = assignment.get((r, c + 1))
            if right is not None and v >= right:
                return False

        if c < N - 1 and (r, c) in facts["GreaterH"]:
            right = assignment.get((r, c + 1))
            if right is not None and v <= right:
                return False

        # Vertical
        if r > 0 and (r - 1, c) in facts["LessV"]:
            above = assignment.get((r - 1, c))
            if above is not None and above >= v:
                return False

        if r > 0 and (r - 1, c) in facts["GreaterV"]:
            above = assignment.get((r - 1, c))
            if above is not None and above <= v:
                return False

        if r < N - 1 and (r, c) in facts["LessV"]:
            below = assignment.get((r + 1, c))
            if below is not None and v >= below:
                return False

        if r < N - 1 and (r, c) in facts["GreaterV"]:
            below = assignment.get((r + 1, c))
            if below is not None and v <= below:
                return False

        return True

    def _select_mrv(self) -> Optional[tuple]:
        """MRV: chọn ô chưa được gán có ít giá trị hợp lệ nhất (Minimum Remaining Values)."""
        N = self.kb.N
        best_cell = None
        best_count = N + 1

        for r in range(N):
            for c in range(N):
                if (r, c) not in self.assignment:
                    count = sum(1 for v in range(1, N + 1) if self._is_valid(r, c, v))
                    if count < best_count:
                        best_count = count
                        best_cell = (r, c)
                        if count == 0:  # Dead-end sớm, không cần tìm tiếp
                            return None

        return best_cell

    def backtracking(self, r: int = 0, c: int = 0,
                     on_update: Optional[Callable] = None) -> bool:
        if self.start_time is None:
            self.start_time = time.time()

        N = self.kb.N
        assignment = self.assignment

        # Dùng MRV để chọn ô tiếp theo thay vì duyệt tuần tự
        cell = self._select_mrv()

        # Không còn ô nào chưa gán → đã giải xong
        if cell is None and len(assignment) == N * N:
            return True

        # MRV phát hiện dead-end (một ô không còn giá trị hợp lệ)
        if cell is None:
            return False

        r, c = cell

        for v in range(1, N + 1):
            self.attempts += 1

            if self._is_valid(r, c, v):
                assignment[(r, c)] = v

                if on_update:
                    on_update(r, c, v, "TRYING")

                if self.backtracking(r, c, on_update):
                    return True

                # backtrack
                self.backtracks += 1
                del assignment[(r, c)]

                if on_update:
                    on_update(r, c, 0, "BACKTRACK")

        return False


def cli_update_viewer(r: int, c: int, v: int, status: str):
    if status == "TRYING":
        print(f"Trying Cell({r}, {c}) = {v}")
    elif status == "BACKTRACK":
        print(f"Backtrack Cell({r}, {c})")


def main():
    input_file = "Inputs/input-10.txt"
    output_file = "output-01.txt"

    print("=" * 80)
    print("FUTOSHIKI SOLVER - BACKTRACKING + MRV")
    print("=" * 80)

    print(f"\nParsing input file: {input_file}")
    result = generate_ground_kb_from_file(input_file)

    if result:
        kb, initial_assignment = result
        solver = FutoshikiSolver(kb, initial_assignment)

        print(f"Puzzle size: {kb.N}x{kb.N}")
        print(f"Clues given: {len(initial_assignment)}")
        print(f"Empty cells: {kb.N * kb.N - len(initial_assignment)}")
        print(f"\nStarting Backtracking + MRV solver...\n")

        solver.start_time = time.time()
        solver.last_report_time = solver.start_time
        success = solver.backtracking(on_update=None)
        end_time = time.time()
        elapsed = end_time - solver.start_time

        print("\n" + "=" * 80)
        if success:
            print(f"✓ SOLVED in {elapsed:.4f} seconds")
        else:
            print(f"✗ FAILED in {elapsed:.4f} seconds")

        print(f"Total attempts: {solver.attempts:,}")
        print(f"Total backtracks: {solver.backtracks:,}")
        print("=" * 80)

        if success:
            print("\n--- Solution Found ---")
            formatted_output = format_board(kb, solver.assignment)
            print(formatted_output)

            with open(output_file, 'w') as f:
                f.write(formatted_output + "\n")
            print(f"\nSaved to: {output_file}")
        else:
            print("\n[ERROR] No solution found for this puzzle.")
    else:
        print(f"[ERROR] Failed to parse {input_file}")

if __name__ == "__main__":
    main()
