import time
from typing import Optional, Callable
from core.knowledge_base import KnowledgeBase, generate_full_ground_kb, generate_ground_kb_from_file, format_board

class FutoshikiSolver:
    def __init__(self, kb: KnowledgeBase, initial_assignment: dict):
        self.kb = kb
        self.assignment = initial_assignment.copy()
        # Thống kê
        self.attempts = 0
        self.backtracks = 0
        self.max_depth = 0
        self.start_time = None
        self.last_report_time = None

    def _validate_full_board(self) -> bool:
        for row in range(self.kb.N):
            for col in range(self.kb.N):
                v = self.assignment.get((row, col))
                if v is None:
                    return False
                tmp = self.assignment.copy()
                del tmp[(row, col)]
                if not self.kb.is_consistent_with_rules(row, col, v, tmp):
                    return False
        return True
    
    def _report_progress(self):
        current_time = time.time()
        if self.last_report_time is None or (current_time - self.last_report_time) >= 1.0:
            elapsed = current_time - self.start_time
            print(f"[{elapsed:6.1f}s] Attempts: {self.attempts:,}")
            self.last_report_time = current_time

    def brute_force(self, r: int = 0, c: int = 0,
                    on_update: Optional[Callable[[int, int, int, str], None]] = None) -> bool:

        depth = r * self.kb.N + c
        self.max_depth = max(self.max_depth, depth)
        
        self._report_progress()
        
        if r == self.kb.N:
            return self._validate_full_board()

        if c == self.kb.N:
            return self.brute_force(r + 1, 0, on_update)

        if (r, c) in self.assignment:
            return self.brute_force(r, c + 1, on_update)

        for v in range(1, self.kb.N + 1):
            self.attempts += 1
            self.assignment[(r, c)] = v
            if on_update: 
                on_update(r, c, v, "TRYING")

            # Đệ quy sang ô tiếp theo
            if self.brute_force(r, c + 1, on_update):
                return True
            
            # Backtrack: xóa giá trị vừa thử
            self.backtracks += 1
            del self.assignment[(r, c)]
            if on_update: 
                on_update(r, c, 0, "BACKTRACK")
        return False

def cli_update_viewer(r: int, c: int, v: int, status: str):
    if status == "TRYING":
        print(f"Trying Cell({r}, {c}) = {v}")
    elif status == "BACKTRACK":
        print(f"Backtrack Cell({r}, {c})")


def main():
    input_file = "input-01.txt"
    output_file = "output-01.txt"

    print("=" * 80)
    print("FUTOSHIKI SOLVER - BRUTE FORCE (PURE)")
    print("=" * 80)

    print(f"\nParsing input file: {input_file}")
    result = generate_ground_kb_from_file(input_file)

    if result:
        kb, initial_assignment = result
        solver = FutoshikiSolver(kb, initial_assignment)

        print(f"Puzzle size: {kb.N}x{kb.N}")
        print(f"Clues given: {len(initial_assignment)}")
        print(f"Empty cells: {kb.N * kb.N - len(initial_assignment)}")
        print(f"\nStarting Brute Force solver...\n")
        
        solver.start_time = time.time()
        solver.last_report_time = solver.start_time
        success = solver.brute_force(on_update=None)
        end_time = time.time()
        elapsed = end_time - solver.start_time

        print("\n" + "=" * 80)
        if success:
            print(f"✓ SOLVED in {elapsed:.4f} seconds")
        else:
            print(f"✗ FAILED in {elapsed:.4f} seconds")
        
        print(f"Total attempts: {solver.attempts:,}")
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
