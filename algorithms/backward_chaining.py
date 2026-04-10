import time
import sys
from typing import List, Dict, Tuple
from knowledge_base import KnowledgeBase, format_board

sys.setrecursionlimit(5000)

class SLDResolutionEngine:
    def __init__(self, kb: KnowledgeBase, initial_assignment: dict):
        self.kb = kb
        self.N = kb.N
        self.val_facts = {}

        for r in range(self.N):
            for c in range(self.N):
                if (r, c) in initial_assignment:
                    self.val_facts[(r, c)] = [initial_assignment[(r, c)]]
                else:
                    self.val_facts[(r, c)] = list(range(1, self.N + 1))

    def resolve_term(self, term, env: dict):
        if isinstance(term, str) and term.startswith("?"):
            return env.get(term, term)
        return term

    def prove(self, goals: list, env: dict, on_update=None):
       
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
            facts = self.val_facts.get((r, c), [])

            for val in facts:
              
                new_env = env.copy()
                new_env[var_name] = val

                
                if on_update and len(facts) > 1:
                    on_update(r, c, val, "TRYING")

                
                yield from self.prove(rest_goals, new_env, on_update)

           
            if on_update and len(facts) > 1:
                on_update(r, c, 0, "BACKTRACK")


class FutoshikiSolver:
    def __init__(self, kb: KnowledgeBase, initial_assignment: dict):
        self.kb = kb
        self.N = kb.N
        self.initial_assignment = initial_assignment
        self.assignment = initial_assignment.copy()
        self.engine = SLDResolutionEngine(kb, initial_assignment)

    def build_horn_clause_query(self) -> List[Tuple]:
        
        goals = []
        for r in range(self.N):
            for c in range(self.N):
                var = f"?V_{r}_{c}"
               
                goals.append(("Val", r, c, var))

             
                for c_prev in range(c):
                    goals.append(("Diff", f"?V_{r}_{c_prev}", var))
                for r_prev in range(r):
                    goals.append(("Diff", f"?V_{r_prev}_{c}", var))

                if c > 0 and (r, c-1) in self.kb.facts["LessH"]:
                    goals.append(("Less", f"?V_{r}_{c-1}", var))
                if c > 0 and (r, c-1) in self.kb.facts["GreaterH"]:
                    goals.append(("Greater", f"?V_{r}_{c-1}", var))

                if r > 0 and (r-1, c) in self.kb.facts["LessV"]:
                    goals.append(("Less", f"?V_{r-1}_{c}", var))
                if r > 0 and (r-1, c) in self.kb.facts["GreaterV"]:
                    goals.append(("Greater", f"?V_{r-1}_{c}", var))

        return goals

    def backward_chaining(self, on_update=None) -> bool:
      
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
            if (r, c-1) in self.kb.facts["LessH"]:    
                goals.append(("Greater", target_var, self.initial_assignment[(r, c-1)]))
            if (r, c-1) in self.kb.facts["GreaterH"]: 
                goals.append(("Less", target_var, self.initial_assignment[(r, c-1)]))

        
        if c < self.N - 1 and (r, c+1) in self.initial_assignment:
            if (r, c) in self.kb.facts["LessH"]:     
                goals.append(("Less", target_var, self.initial_assignment[(r, c+1)]))
            if (r, c) in self.kb.facts["GreaterH"]:  
                goals.append(("Greater", target_var, self.initial_assignment[(r, c+1)]))

        
        if r > 0 and (r-1, c) in self.initial_assignment:
            if (r-1, c) in self.kb.facts["LessV"]:    
                goals.append(("Greater", target_var, self.initial_assignment[(r-1, c)]))
            if (r-1, c) in self.kb.facts["GreaterV"]:
                goals.append(("Less", target_var, self.initial_assignment[(r-1, c)]))

       
        if r < self.N - 1 and (r+1, c) in self.initial_assignment:
            if (r, c) in self.kb.facts["LessV"]:      
                goals.append(("Less", target_var, self.initial_assignment[(r+1, c)]))
            if (r, c) in self.kb.facts["GreaterV"]:   
                goals.append(("Greater", target_var, self.initial_assignment[(r+1, c)]))

        return goals

    def prolog_query_deep(self, r: int, c: int) -> List[int]:
       
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
    print("FUTOSHIKI SOLVER - PURE PROLOG-STYLE BACKWARD CHAINING (SLD RESOLUTION)")
    print("=" * 75)

    result = generate_ground_kb_from_file(input_file)
    if not result:
        print("Cannot load input!")
        return

    kb, initial = result
    solver = FutoshikiSolver(kb, initial)

    print("\n[Prolog-style Query] ?- Val(0, 1, X)")
    answers = solver.prolog_query_deep(0, 1)
    print(f"Proven value for X via SLD Resolution: {answers}\n")

    print("Starting Logical Proof...\n")
    start = time.time()
    
    solver = FutoshikiSolver(kb, initial)
    success = solver.backward_chaining(on_update=cli_update_viewer)
    end = time.time()

    if success:
        print(f"\nProof Completed successfully in {end-start:.4f} seconds")
        print(format_board(kb, solver.assignment))
        with open(output_file, 'w') as f:
            f.write(format_board(kb, solver.assignment) + "\n")
        print(f"\nSaved to {output_file}")
    else:
        print(f"\nProof Failed: No logical solution found ({end-start:.4f}s)")

if __name__ == "__main__":
    main()
