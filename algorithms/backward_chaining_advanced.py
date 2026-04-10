import time
import sys
from typing import List, Tuple
from knowledge_base import KnowledgeBase, format_board

sys.setrecursionlimit(5000)

class SLDResolutionEngine:
    def __init__(self, kb: KnowledgeBase, initial_assignment: dict, val_domains: dict, solver_ref=None):
        self.kb = kb
        self.N = kb.N
        self.solver_ref = solver_ref
        self.val_domains = val_domains 
    def resolve_term(self, term, env: dict):
        if isinstance(term, str) and term.startswith("?"):
            return env.get(term, term)
        return term

    def prove(self, goals: list, env: dict, on_update=None):
        if self.solver_ref:
            self.solver_ref.inferences += 1 

        if not goals:
            yield env
            return

        goal = goals[0]
        pred = goal[0]
        rest_goals = goals[1:]

        
        if pred == "Diff":
            v1 = self.resolve_term(goal[1], env)
            v2 = self.resolve_term(goal[2], env)
            if isinstance(v1, int) and isinstance(v2, int) and v1 != v2:
                yield from self.prove(rest_goals, env, on_update)

        
        elif pred == "Less":
            v1 = self.resolve_term(goal[1], env)
            v2 = self.resolve_term(goal[2], env)
            if isinstance(v1, int) and isinstance(v2, int) and v1 < v2:
                yield from self.prove(rest_goals, env, on_update)

       
        elif pred == "Greater":
            v1 = self.resolve_term(goal[1], env)
            v2 = self.resolve_term(goal[2], env)
            if isinstance(v1, int) and isinstance(v2, int) and v1 > v2:
                yield from self.prove(rest_goals, env, on_update)

        elif pred == "Val":
            r, c, var_name = goal[1], goal[2], goal[3]
            
            
            available_vals = self.val_domains.get((r, c), [])

            for val in available_vals:
                new_env = env.copy()
                new_env[var_name] = val
                
                if on_update and len(available_vals) > 1:
                    on_update(r, c, val, "TRYING")
                
                yield from self.prove(rest_goals, new_env, on_update)
                
            if on_update and len(available_vals) > 1:
                on_update(r, c, 0, "BACKTRACK")


class FutoshikiSolver:
    def __init__(self, kb: KnowledgeBase, initial_assignment: dict):
        self.kb = kb
        self.N = kb.N
        self.initial_assignment = initial_assignment
        self.assignment = initial_assignment.copy()
        self.inferences = 0 
        
        self.domains = {}
        for r in range(self.N):
            for c in range(self.N):
                if (r, c) in initial_assignment:
                    self.domains[(r, c)] = [initial_assignment[(r, c)]]
                else:
                    valid_nums = list(range(1, self.N + 1))
                    
                    
                    if (r, c) in self.kb.facts["LessH"] or (r, c) in self.kb.facts["LessV"]:
                        if self.N in valid_nums: valid_nums.remove(self.N) 
                    if (r, c) in self.kb.facts["GreaterH"] or (r, c) in self.kb.facts["GreaterV"]:
                        if 1 in valid_nums: valid_nums.remove(1) 
                    for i in range(self.N):
                        if (r, i) in initial_assignment and initial_assignment[(r, i)] in valid_nums:
                            valid_nums.remove(initial_assignment[(r, i)])
                        if (i, c) in initial_assignment and initial_assignment[(i, c)] in valid_nums:
                            valid_nums.remove(initial_assignment[(i, c)])

                    self.domains[(r, c)] = valid_nums

        self.engine = SLDResolutionEngine(kb, initial_assignment, self.domains, solver_ref=self)

    def build_horn_clause_query(self) -> List[Tuple]:
      
        cell_scores = {}
        for r in range(self.N):
            for c in range(self.N):
                if (r, c) in self.initial_assignment:
                    cell_scores[(r, c)] = -9999 
                else:
                    
                    domain_size = len(self.domains[(r, c)])
                    
                   
                    degree = sum(1 for i in range(self.N) if (r, i) not in self.initial_assignment)
                    degree += sum(1 for i in range(self.N) if (i, c) not in self.initial_assignment)
                    
                    
                    if (r, c) in self.kb.facts["LessH"] or (r, c) in self.kb.facts["GreaterH"]: degree += 3
                    if (r, c) in self.kb.facts["LessV"] or (r, c) in self.kb.facts["GreaterV"]: degree += 3
                    
                   
                    cell_scores[(r, c)] = (domain_size * 100) - degree

        ordered_cells = sorted(cell_scores.keys(), key=lambda k: cell_scores[k])

        goals = []
        bound_vars = set()

        for r, c in ordered_cells:
            var = f"?V_{r}_{c}"
            goals.append(("Val", r, c, var))
            bound_vars.add((r, c))

           
            for r_prev, c_prev in bound_vars:
                if (r_prev == r and c_prev != c) or (c_prev == c and r_prev != r):
                    goals.append(("Diff", f"?V_{r_prev}_{c_prev}", var))

          
            if c > 0 and (r, c-1) in bound_vars:
                if (r, c-1) in self.kb.facts["LessH"]: goals.append(("Less", f"?V_{r}_{c-1}", var))
                if (r, c-1) in self.kb.facts["GreaterH"]: goals.append(("Greater", f"?V_{r}_{c-1}", var))
            if c < self.N - 1 and (r, c+1) in bound_vars:
                if (r, c) in self.kb.facts["LessH"]: goals.append(("Less", var, f"?V_{r}_{c+1}"))
                if (r, c) in self.kb.facts["GreaterH"]: goals.append(("Greater", var, f"?V_{r}_{c+1}"))
            if r > 0 and (r-1, c) in bound_vars:
                if (r-1, c) in self.kb.facts["LessV"]: goals.append(("Less", f"?V_{r-1}_{c}", var))
                if (r-1, c) in self.kb.facts["GreaterV"]: goals.append(("Greater", f"?V_{r-1}_{c}", var))
            if r < self.N - 1 and (r+1, c) in bound_vars:
                if (r, c) in self.kb.facts["LessV"]: goals.append(("Less", var, f"?V_{r+1}_{c}"))
                if (r, c) in self.kb.facts["GreaterV"]: goals.append(("Greater", var, f"?V_{r+1}_{c}"))

        return goals

    def backward_chaining(self, on_update=None) -> bool:
        self.inferences = 0
        query_goals = self.build_horn_clause_query()

        for solution_env in self.engine.prove(query_goals, {}, on_update):
            for r in range(self.N):
                for c in range(self.N):
                    self.assignment[(r, c)] = solution_env[f"?V_{r}_{c}"]
            return True 
            
        return False

    def build_single_cell_query(self, r: int, c: int) -> List[Tuple]:
        target_var = "?X"
        goals = [("Val", r, c, target_var)]

        for i in range(self.N):
            if i != c and (r, i) in self.initial_assignment:
                goals.append(("Diff", target_var, self.initial_assignment[(r, i)]))
            if i != r and (i, c) in self.initial_assignment:
                goals.append(("Diff", target_var, self.initial_assignment[(i, c)]))

        if c > 0 and (r, c-1) in self.initial_assignment:
            if (r, c-1) in self.kb.facts["LessH"]: goals.append(("Greater", target_var, self.initial_assignment[(r, c-1)]))
            if (r, c-1) in self.kb.facts["GreaterH"]: goals.append(("Less", target_var, self.initial_assignment[(r, c-1)]))
        if c < self.N - 1 and (r, c+1) in self.initial_assignment:
            if (r, c) in self.kb.facts["LessH"]: goals.append(("Less", target_var, self.initial_assignment[(r, c+1)]))
            if (r, c) in self.kb.facts["GreaterH"]: goals.append(("Greater", target_var, self.initial_assignment[(r, c+1)]))
        if r > 0 and (r-1, c) in self.initial_assignment:
            if (r-1, c) in self.kb.facts["LessV"]: goals.append(("Greater", target_var, self.initial_assignment[(r-1, c)]))
            if (r-1, c) in self.kb.facts["GreaterV"]: goals.append(("Less", target_var, self.initial_assignment[(r-1, c)]))
        if r < self.N - 1 and (r+1, c) in self.initial_assignment:
            if (r, c) in self.kb.facts["LessV"]: goals.append(("Less", target_var, self.initial_assignment[(r+1, c)]))
            if (r, c) in self.kb.facts["GreaterV"]: goals.append(("Greater", target_var, self.initial_assignment[(r+1, c)]))

        return goals

    def prolog_query_deep(self, r: int, c: int) -> List[int]:
        self.inferences = 0
        query_goals = self.build_single_cell_query(r, c)
        valid_answers = []

        for solution_env in self.engine.prove(query_goals, {}):
            valid_answers.append(solution_env["?X"])
            
        return sorted(list(set(valid_answers)))

def cli_update_viewer(r: int, c: int, v: int, status: str):
    if status == "TRYING":
        print(f"→ Goal ?- Val({r},{c},{v})")
    elif status == "BACKTRACK":
        print(f"  × Unification failed. SLD Backtracking...")

def main():
    input_file = "input-01.txt"
    output_file = "output-01.txt"

    print("=" * 75)
    print("FUTOSHIKI SOLVER - GOD TIER BACKWARD CHAINING (SLD + NC + MRV + DEGREE)")
    print("=" * 75)

    from knowledge_base import generate_ground_kb_from_file
    result = generate_ground_kb_from_file(input_file)
    if not result:
        print("Cannot load input!")
        return

    kb, initial = result
    solver = FutoshikiSolver(kb, initial)

    print("\n[Prolog-style Query] ?- Val(0, 1, X)")
    answers = solver.prolog_query_deep(0, 1)
    print(f"Proven value for X via SLD Resolution: {answers} (Inferences: {solver.inferences})\n")

    print("Starting Logical Proof...\n")
    start = time.time()
    
    solver = FutoshikiSolver(kb, initial)
    success = solver.backward_chaining(on_update=cli_update_viewer)
    end = time.time()

    if success:
        print(f"\nProof Completed successfully in {end-start:.4f} seconds")
        print(f"Total Logical Inferences: {solver.inferences}")
        print(format_board(kb, solver.assignment))
        with open(output_file, 'w') as f:
            f.write(format_board(kb, solver.assignment) + "\n")
        print(f"\nSaved to {output_file}")
    else:
        print(f"\nProof Failed: No logical solution found ({end-start:.4f}s)")

if __name__ == "__main__":
    main()
