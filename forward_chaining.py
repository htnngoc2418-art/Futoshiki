import time
from typing import Optional, Callable
from knowledge_base import KnowledgeBase, generate_ground_kb_from_file, format_board

class FutoshikiSolver:
    
    def __init__(self, kb: KnowledgeBase, initial_assignment: dict):
        self.kb = kb
        self.N = kb.N
        self.initial_assignment = initial_assignment.copy()
        self.assignment = initial_assignment.copy()
        self.domains = {(r, c): set(range(1, self.N + 1)) for r in range(self.N) for c in range(self.N)}
        self.agenda = []
        self.inferences = 0

    def remove_value(self, r, c, v_to_remove) -> bool:
        if v_to_remove in self.domains[(r, c)]:
            self.domains[(r, c)].remove(v_to_remove)
            self.inferences += 1  
            
            if not self.domains[(r, c)]: 
                return False 
                
            if len(self.domains[(r, c)]) == 1:
                new_val = list(self.domains[(r, c)])[0]
                if ("ASSIGN", r, c, new_val) not in self.agenda:
                    self.agenda.append(("ASSIGN", r, c, new_val))
            return True
        return False

    def enforce_less_than(self, r1, c1, r2, c2) -> bool:
        local_changed = False
        if not self.domains[(r1, c1)] or not self.domains[(r2, c2)]: 
            return False
        
        max_v2 = max(self.domains[(r2, c2)])
        for v in list(self.domains[(r1, c1)]):
            if v >= max_v2:
                if self.remove_value(r1, c1, v): local_changed = True
                
        min_v1 = min(self.domains[(r1, c1)])
        for v in list(self.domains[(r2, c2)]):
            if v <= min_v1:
                if self.remove_value(r2, c2, v): local_changed = True
                
        return local_changed

    def forward_chaining(self, on_update: Optional[Callable[[int, int, int, str], None]] = None) -> bool:
        for r in range(self.N):
            for c in range(self.N):
                if (r, c) in self.initial_assignment:
                    v_given = self.initial_assignment[(r, c)]
                    self.domains[(r, c)] = {v_given}
                    self.agenda.append(("ASSIGN", r, c, v_given))

        global_changed = True
        
        while global_changed or self.agenda:
            global_changed = False
            
            
            while self.agenda:
                _, r, c, v = self.agenda.pop(0)
                
                if (r, c) not in self.assignment or self.assignment[(r, c)] != v:
                    self.assignment[(r, c)] = v
                    if on_update: on_update(r, c, v, "TRYING")
                
                for i in range(self.N):
                    if i != c and self.remove_value(r, i, v): global_changed = True
                    if i != r and self.remove_value(i, c, v): global_changed = True

            
            for (r, c) in self.kb.facts["LessH"]:
                if self.enforce_less_than(r, c, r, c + 1): global_changed = True
            for (r, c) in self.kb.facts["GreaterH"]:
                if self.enforce_less_than(r, c + 1, r, c): global_changed = True
            for (r, c) in self.kb.facts["LessV"]:
                if self.enforce_less_than(r, c, r + 1, c): global_changed = True
            for (r, c) in self.kb.facts["GreaterV"]:
                if self.enforce_less_than(r + 1, c, r, c): global_changed = True

            
            if not self.agenda:
                for r in range(self.N):
                    for v in range(1, self.N + 1):
                        cells = [c for c in range(self.N) if v in self.domains[(r, c)]]
                        if len(cells) == 1 and len(self.domains[(r, cells[0])]) > 1:
                            self.domains[(r, cells[0])] = {v}
                            self.agenda.append(("ASSIGN", r, cells[0], v))
                            global_changed = True
                for c in range(self.N):
                    for v in range(1, self.N + 1):
                        cells = [r for r in range(self.N) if v in self.domains[(r, c)]]
                        if len(cells) == 1 and len(self.domains[(cells[0], c)]) > 1:
                            self.domains[(cells[0], c)] = {v}
                            self.agenda.append(("ASSIGN", cells[0], c, v))
                            global_changed = True

            
            if not self.agenda and not global_changed:
                
                for r in range(self.N):
                    
                    for c1 in range(self.N):
                        if len(self.domains[(r, c1)]) == 2:
                            for c2 in range(c1 + 1, self.N):
                                if self.domains[(r, c1)] == self.domains[(r, c2)]:
                                    pair_vals = self.domains[(r, c1)]
                                    for c3 in range(self.N):
                                        if c3 != c1 and c3 != c2:
                                            for val in pair_vals:
                                                if self.remove_value(r, c3, val): global_changed = True
                   
                    for c1 in range(self.N):
                        for c2 in range(c1 + 1, self.N):
                            for c3 in range(c2 + 1, self.N):
                                union_vals = self.domains[(r, c1)] | self.domains[(r, c2)] | self.domains[(r, c3)]
                                if len(union_vals) == 3:
                                    for c_other in range(self.N):
                                        if c_other not in (c1, c2, c3):
                                            for val in union_vals:
                                                if self.remove_value(r, c_other, val): global_changed = True

                
                for c in range(self.N):
                    
                    for r1 in range(self.N):
                        if len(self.domains[(r1, c)]) == 2:
                            for r2 in range(r1 + 1, self.N):
                                if self.domains[(r1, c)] == self.domains[(r2, c)]:
                                    pair_vals = self.domains[(r1, c)]
                                    for r3 in range(self.N):
                                        if r3 != r1 and r3 != r2:
                                            for val in pair_vals:
                                                if self.remove_value(r3, c, val): global_changed = True
                    
                    for r1 in range(self.N):
                        for r2 in range(r1 + 1, self.N):
                            for r3 in range(r2 + 1, self.N):
                                union_vals = self.domains[(r1, c)] | self.domains[(r2, c)] | self.domains[(r3, c)]
                                if len(union_vals) == 3:
                                    for r_other in range(self.N):
                                        if r_other not in (r1, r2, r3):
                                            for val in union_vals:
                                                if self.remove_value(r_other, c, val): global_changed = True

            
            if not self.agenda and not global_changed:
              
                for r in range(self.N):
                    for v1 in range(1, self.N + 1):
                        for v2 in range(v1 + 1, self.N + 1):
                            cells_v1 = [c for c in range(self.N) if v1 in self.domains[(r, c)]]
                            cells_v2 = [c for c in range(self.N) if v2 in self.domains[(r, c)]]
                            union_cells = list(set(cells_v1 + cells_v2))
                            if len(union_cells) == 2 and len(cells_v1) >= 1 and len(cells_v2) >= 1:
                                c1, c2 = union_cells[0], union_cells[1]
                                for val in list(self.domains[(r, c1)]):
                                    if val not in (v1, v2) and self.remove_value(r, c1, val): global_changed = True
                                for val in list(self.domains[(r, c2)]):
                                    if val not in (v1, v2) and self.remove_value(r, c2, val): global_changed = True
                                    
                
                for c in range(self.N):
                    for v1 in range(1, self.N + 1):
                        for v2 in range(v1 + 1, self.N + 1):
                            cells_v1 = [r for r in range(self.N) if v1 in self.domains[(r, c)]]
                            cells_v2 = [r for r in range(self.N) if v2 in self.domains[(r, c)]]
                            union_cells = list(set(cells_v1 + cells_v2))
                            if len(union_cells) == 2 and len(cells_v1) >= 1 and len(cells_v2) >= 1:
                                r1, r2 = union_cells[0], union_cells[1]
                                for val in list(self.domains[(r1, c)]):
                                    if val not in (v1, v2) and self.remove_value(r1, c, val): global_changed = True
                                for val in list(self.domains[(r2, c)]):
                                    if val not in (v1, v2) and self.remove_value(r2, c, val): global_changed = True

        return len(self.assignment) == self.N * self.N

def cli_update_viewer(r: int, c: int, v: int, status: str):
    if status == "TRYING":
        print(f"-> Logic suy ra: Cell({r}, {c}) = {v}")

def main():
    input_file = "input-01.txt"
    print("=" * 65)
    print("FUTOSHIKI SOLVER - FORWARD CHAINING (RULE-BASED INFERENCE)")
    print("=" * 65)

    result = generate_ground_kb_from_file(input_file)
    if result:
        kb, initial_assignment = result
        solver = FutoshikiSolver(kb, initial_assignment)

        print("\nStarting Forward Chaining...\n")
        start_time = time.time()
        success = solver.forward_chaining(on_update=cli_update_viewer)
        end_time = time.time()

        if success:
            print(f"\nExecution time: {end_time - start_time:.4f} seconds")
            print(f"Total Inferences: {solver.inferences}")
            print("\n--- Solved Successfully! ---")
            print(format_board(kb, solver.assignment))
        else:
            print("\n[!] ERROR/STUCK: Forward Chaining không thể giải hết bảng chỉ bằng luật logic.")
            print(format_board(kb, solver.assignment))

if __name__ == "__main__":
    main()