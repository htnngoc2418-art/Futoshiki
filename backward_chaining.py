import time
from typing import List, Dict, Tuple, Optional, Callable, Set

from knowledge_base import KnowledgeBase, generate_ground_kb_from_file, format_board

class FutoshikiSolver:
   
    def __init__(self, kb: KnowledgeBase, initial_assignment: dict):
        self.kb = kb
        self.N = kb.N
       
        self.assignment: Dict[Tuple[int,int], int] = initial_assignment.copy()
       
        self.domains: Dict[Tuple[int,int], Set[int]] = {}
        self._initialize_domains()

    def _initialize_domains(self):
        for r in range(self.N):
            for c in range(self.N):
                key = (r, c)
                if key in self.assignment:
                    self.domains[key] = {self.assignment[key]}
                else:
                    self.domains[key] = set(range(1, self.N + 1))

    def select_most_constrained(self) -> Optional[Tuple[int, int]]:
       
        min_size = float('inf')
        best = None
        for r in range(self.N):
            for c in range(self.N):
                key = (r, c)
                if key not in self.assignment and len(self.domains[key]) < min_size:
                    min_size = len(self.domains[key])
                    best = key
        return best

    def propagate_constraints(self, r: int, c: int, value: int) -> bool:
        
        key = (r, c)
        self.domains[key] = {value}

        for i in range(self.N):
            if i != c and (r, i) not in self.assignment:
                self.domains[(r, i)].discard(value)
                if not self.domains[(r, i)]:
                    return False
            if i != r and (i, c) not in self.assignment:
                self.domains[(i, c)].discard(value)
                if not self.domains[(i, c)]:
                    return False

    
        if not self.kb.is_consistent_with_rules(r, c, value, self.assignment):
            return False
            
        return True

    def backward_chain(self, goal: str = "solve_board", on_update=None) -> bool:
        """Core Backward Chaining"""
        if goal == "solve_board":
            var = self.select_most_constrained()
            if var is None:
             
                return len(self.assignment) == self.N * self.N

            r, c = var
            possible_values = sorted(self.domains[(r, c)])  

            for v in possible_values:
                if on_update:
                    on_update(r, c, v, "TRYING")

         
                backup_assign = self.assignment.copy()
                backup_domains = {k: s.copy() for k, s in self.domains.items()}

                self.assignment[(r, c)] = v

                if self.propagate_constraints(r, c, v):
                 
                    if self.backward_chain("solve_board", on_update): 
                        return True
      
                self.assignment = backup_assign
                self.domains = backup_domains
                if on_update:
                    on_update(r, c, 0, "BACKTRACK")

            return False

        return False

    def prolog_query_deep(self, r: int, c: int) -> List[int]:
    
        valid = []
        backup_assign = self.assignment.copy()
        backup_domains = {k: s.copy() for k, s in self.domains.items()}

        for v in range(1, self.N + 1):
            if v not in self.domains[(r, c)]:
                continue

            self.assignment[(r, c)] = v
            if self.propagate_constraints(r, c, v):
                if self.backward_chain("solve_board", on_update=None):
                    valid.append(v)

            self.assignment = backup_assign.copy()
            self.domains = {k: s.copy() for k, s in backup_domains.items()}

        return valid

    
    def backward_chaining(self, on_update=None) -> bool:
        return self.backward_chain("solve_board", on_update)

    def solve(self, on_update=None) -> bool:
        return self.backward_chain("solve_board", on_update)



def cli_update_viewer(r: int, c: int, v: int, status: str):
    if status == "TRYING":
        print(f"→ Trying Cell({r},{c}) = {v}")
    elif status == "BACKTRACK":
        print(f"  × Backtrack Cell({r},{c})")



def main():
    input_file = "input-01.txt"
    output_file = "output-01.txt"

    print("=" * 75)
    print("FUTOSHIKI SOLVER - REAL BACKWARD CHAINING (Goal-Driven + Propagation)")
    print("=" * 75)

    result = generate_ground_kb_from_file(input_file)
    if not result:
        print("Cannot load input!")
        return

    kb, initial = result
    solver = FutoshikiSolver(kb, initial)

    print("\n[Prolog-style Query] ?- Val(0, 0, X)")
    answers = solver.prolog_query_deep(0, 0)
    print(f"Proven values for (0,0) that lead to solution: {answers}\n")

    print("Starting solve...\n")
    start = time.time()
    success = solver.backward_chaining(on_update=cli_update_viewer)
    end = time.time()

    if success:
        print(f"\nSolved in {end-start:.4f} seconds")
        print(format_board(kb, solver.assignment))
        with open(output_file, 'w') as f:
            f.write(format_board(kb, solver.assignment) + "\n")
        print(f"\nSaved to {output_file}")
    else:
        print(f"\nNo solution found ({end-start:.4f}s)")


if __name__ == "__main__":
    main()