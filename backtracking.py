import time
from typing import List, Callable, Optional
from knowledge_base import KnowledgeBase, generate_full_ground_kb, generate_ground_kb_from_file, format_board

class BacktrackingSolver:
    def __init__(self, kb: KnowledgeBase, initial_assignment: dict):
        self.kb = kb
        self.assignment = initial_assignment.copy()

    def prolog_query_deep(self, r: int, c: int) -> List[int]:
        valid_answers = []
        if (r, c) in self.assignment:
            return [self.assignment[(r, c)]]

        backup_assignment = self.assignment.copy()

        for v in range(1, self.kb.N + 1):
            if self.kb.is_consistent_with_rules(r, c, v, self.assignment):
                self.assignment[(r, c)] = v

                if self.backtracking(0, 0, on_update=None):
                    valid_answers.append(v)
                self.assignment = backup_assignment.copy()

        return valid_answers

    def backtracking(self, r: int = 0, c: int = 0,
                     on_update: Optional[Callable[[int, int, int, str], None]] = None) -> bool:
        if r == self.kb.N:
            return True

        if c == self.kb.N:
            return self.backtracking(r + 1, 0, on_update)

        if (r, c) in self.assignment:
            return self.backtracking(r, c + 1, on_update)

        for v in range(1, self.kb.N + 1):
            if self.kb.is_consistent_with_rules(r, c, v, self.assignment):
                self.assignment[(r, c)] = v

                if on_update: on_update(r, c, v, "TRYING")

                if self.backtracking(r, c + 1, on_update):
                    return True

                del self.assignment[(r, c)]

                if on_update: on_update(r, c, 0, "BACKTRACK")

        return False


def cli_update_viewer(r: int, c: int, v: int, status: str):
    if status == "TRYING":
        print(f"Assigning Cell({r}, {c}) = {v}")
    elif status == "BACKTRACK":
        print(f"Conflict! Backtracking Cell({r}, {c})")

def main():
    input_file = "input-01.txt"
    output_file = "output-01.txt"

    print("=" * 65)
    print("FUTOSHIKI SOLVER - BACKTRACKING")
    print("=" * 65)

    cnf_kb = generate_full_ground_kb(N=4, output_file="ground_kb_4x4.txt")
    print(f"-> Generated {len(cnf_kb)} complete CNF clauses (including inequalities).")
    print("-" * 65)

    print(f"Parsing Input File '{input_file}'...")
    result = generate_ground_kb_from_file(input_file)

    if result:
        kb, initial_assignment = result
        solver = BacktrackingSolver(kb, initial_assignment)

        print("\n[Deep Backtracking Demo] Querying empty cell (0, 0): ?- Val(0, 0, X)")
        deep_answers = solver.prolog_query_deep(0, 0)
        print(f"-> Backtracking Engine proven answers (leads to solution): X = {deep_answers}")
        print("-" * 65)

        print("\nStarting full Backtracking...\n")
        start_time = time.time()
        success = solver.backtracking(on_update=cli_update_viewer)
        end_time = time.time()

        if success:
            print(f"\nExecution time: {end_time - start_time:.4f} seconds")
            print("\n--- Solved Successfully! ---")
            formatted_output = format_board(kb, solver.assignment)
            print(formatted_output)

            with open(output_file, 'w') as f:
                f.write(formatted_output + "\n")
            print(f"\nSaved to {output_file}")
        else:
            print(f"\nExecution time: {end_time - start_time:.4f} seconds")
            print("\n[!] ERROR: No solution exists for this puzzle.")
            print("Current partial assignment state before total failure:")
            print(format_board(kb, solver.assignment))

if __name__ == "__main__":
    main()
