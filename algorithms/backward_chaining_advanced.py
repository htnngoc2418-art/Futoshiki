import time
import sys
from typing import List, Dict, Tuple, Optional
from knowledge_base import KnowledgeBase, format_board, generate_ground_kb_from_file

sys.setrecursionlimit(10000)


class HornClause:
    def __init__(self, head: tuple, body: list = None):
        self.head = head
        self.body = body or []

    def __repr__(self):
        if not self.body:
            return f"FACT: {self.head}"
        body_str = ", ".join(str(b) for b in self.body)
        return f"RULE: {self.head} :- {body_str}"


class HornClauseKB:
    
    def __init__(self):
        self.rules: Dict[str, List[HornClause]] = {}

    def add_clause(self, clause: HornClause):
        pred = clause.head[0]
        if pred not in self.rules:
            self.rules[pred] = []
        self.rules[pred].append(clause)

    def get_clauses(self, pred_name: str) -> List[HornClause]:
        return self.rules.get(pred_name, [])

    def __len__(self):
        return sum(len(v) for v in self.rules.values())


def is_var(term) -> bool:
    return isinstance(term, str) and term.startswith("?")

def walk(term, env: dict):

    while is_var(term) and term in env:
        term = env[term]
    return term

def unify(t1, t2, env: dict) -> Optional[dict]:
   
    t1 = walk(t1, env)
    t2 = walk(t2, env)

    if t1 == t2:
        return env

    if is_var(t1):
        new_env = env.copy()
        new_env[t1] = t2
        return new_env

    if is_var(t2):
        new_env = env.copy()
        new_env[t2] = t1
        return new_env

    if isinstance(t1, tuple) and isinstance(t2, tuple):
        if len(t1) != len(t2):
            return None
        for a, b in zip(t1, t2):
            env = unify(a, b, env)
            if env is None:
                return None
        return env

    return None

def substitute(term, env: dict):
    
    term = walk(term, env)
    if isinstance(term, tuple):
        return tuple(substitute(t, env) for t in term)
    return term


class FutoshikiHornClauseBuilder:
    
    def __init__(self, kb: KnowledgeBase, initial_assignment: dict, domains: dict):
        self.kb = kb
        self.N = kb.N
        self.initial_assignment = initial_assignment
        self.domains = domains  
        self.horn_kb = HornClauseKB()
        self._build()

    def _build(self):
        self._add_domain_facts()
        self._add_constraint_facts()
        self._add_val_rules()

    def _add_domain_facts(self):
       
        for r in range(self.N):
            for c in range(self.N):
                for v in self.domains[(r, c)]:
                    self.horn_kb.add_clause(
                        HornClause(head=("ValDomain", r, c, v), body=[])
                    )

    def _add_constraint_facts(self):
        
        for (r, c) in self.kb.facts["LessH"]:
            self.horn_kb.add_clause(HornClause(head=("LessH", r, c), body=[]))
        for (r, c) in self.kb.facts["GreaterH"]:
            self.horn_kb.add_clause(HornClause(head=("GreaterH", r, c), body=[]))
        for (r, c) in self.kb.facts["LessV"]:
            self.horn_kb.add_clause(HornClause(head=("LessV", r, c), body=[]))
        for (r, c) in self.kb.facts["GreaterV"]:
            self.horn_kb.add_clause(HornClause(head=("GreaterV", r, c), body=[]))

    def _add_val_rules(self):
        for r in range(self.N):
            for c in range(self.N):
                var = "?V"
                body = [("ValDomain", r, c, var)]
                
                self.horn_kb.add_clause(
                    HornClause(head=("Val", r, c, var), body=body)
                )

class SLDResolutionEngine:
    

    BUILTINS = {"Less", "Greater", "Diff"}

    def __init__(self, horn_kb: HornClauseKB, solver_ref=None):
        self.horn_kb = horn_kb
        self.solver_ref = solver_ref

    def prove(self, goals: list, env: dict, on_update=None, depth: int = 0):
        if self.solver_ref:
            self.solver_ref.inferences += 1

        if not goals:
            yield env
            return

        goal = goals[0]
        rest = goals[1:]
        pred = goal[0]

        
        if pred in self.BUILTINS:
            yield from self._prove_builtin(goal, rest, env, on_update, depth)
            return

        
        clauses = self.horn_kb.get_clauses(pred)

        for clause in clauses:
            
            renamed = self._rename_clause(clause, depth)

            
            new_env = unify(goal, renamed.head, env)
            if new_env is None:
                continue  
            if on_update and pred == "Val":
                v = substitute(renamed.head[3], new_env)
                if isinstance(v, int):
                    on_update(renamed.head[1], renamed.head[2], v, "TRYING")

            
            new_goals = list(renamed.body) + rest
            yield from self.prove(new_goals, new_env, on_update, depth + 1)

        if on_update and pred == "Val":
            on_update(None, None, None, "BACKTRACK")

    def _prove_builtin(self, goal, rest, env, on_update, depth):
        pred = goal[0]
        v1 = substitute(goal[1], env)
        v2 = substitute(goal[2], env)

        if not isinstance(v1, int) or not isinstance(v2, int):
            yield from self.prove(rest, env, on_update, depth)
            return

        success = False
        if pred == "Less":    success = v1 < v2
        elif pred == "Greater": success = v1 > v2
        elif pred == "Diff":    success = v1 != v2

        if success:
            yield from self.prove(rest, env, on_update, depth)

    def _rename_clause(self, clause: HornClause, depth: int) -> HornClause:
        suffix = f"_d{depth}"

        def rename(t):
            if is_var(t):
                
                if t in ("?V", "?X"):
                    return t + suffix
                return t
            if isinstance(t, tuple):
                return tuple(rename(x) for x in t)
            return t

        return HornClause(
            head=rename(clause.head),
            body=[rename(b) for b in clause.body]
        )



class FutoshikiSolver:
    

    def __init__(self, kb: KnowledgeBase, initial_assignment: dict):
        self.kb = kb
        self.N = kb.N
        self.initial_assignment = initial_assignment
        self.assignment = initial_assignment.copy()
        self.inferences = 0

        
        self.domains = self._build_pruned_domains()

        
        self.ordered_cells = self._mrv_degree_ordering()

    
        builder = FutoshikiHornClauseBuilder(kb, initial_assignment, self.domains)
        self.horn_kb = builder.horn_kb

       
        self.engine = SLDResolutionEngine(self.horn_kb, solver_ref=self)

        print(f"\n[Horn Clause KB] Total clauses: {len(self.horn_kb)}")
        self._print_sample_clauses()

    def _build_pruned_domains(self) -> dict:
        
        domains = {}
        for r in range(self.N):
            for c in range(self.N):
                if (r, c) in self.initial_assignment:
                    domains[(r, c)] = [self.initial_assignment[(r, c)]]
                else:
                    valid = list(range(1, self.N + 1))

                    
                    if (r, c) in self.kb.facts["LessH"] or (r, c) in self.kb.facts["LessV"]:
                        if self.N in valid: valid.remove(self.N)
                    if (r, c) in self.kb.facts["GreaterH"] or (r, c) in self.kb.facts["GreaterV"]:
                        if 1 in valid: valid.remove(1)

                    
                    for i in range(self.N):
                        if (r, i) in self.initial_assignment:
                            v = self.initial_assignment[(r, i)]
                            if v in valid: valid.remove(v)
                        if (i, c) in self.initial_assignment:
                            v = self.initial_assignment[(i, c)]
                            if v in valid: valid.remove(v)

                    domains[(r, c)] = valid
        return domains

    def _mrv_degree_ordering(self) -> list:
        
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

        return sorted(cell_scores.keys(), key=lambda k: cell_scores[k])

    def _build_top_level_query(self) -> list:
        
        goals = []
        bound_vars = set() 

        for r, c in self.ordered_cells:
            var = f"?V_{r}_{c}"

            
            goals.append(("Val", r, c, var))

            for r_prev, c_prev in bound_vars:
                if r_prev == r and c_prev != c:  
                    goals.append(("Diff", f"?V_{r_prev}_{c_prev}", var))
                elif c_prev == c and r_prev != r:  
                    goals.append(("Diff", f"?V_{r_prev}_{c_prev}", var))

            
            if c > 0 and (r, c-1) in bound_vars:
                if (r, c-1) in self.kb.facts["LessH"]:
                    goals.append(("Less", f"?V_{r}_{c-1}", var))
                if (r, c-1) in self.kb.facts["GreaterH"]:
                    goals.append(("Greater", f"?V_{r}_{c-1}", var))
            if c < self.N-1 and (r, c+1) in bound_vars:
                if (r, c) in self.kb.facts["LessH"]:
                    goals.append(("Less", var, f"?V_{r}_{c+1}"))
                if (r, c) in self.kb.facts["GreaterH"]:
                    goals.append(("Greater", var, f"?V_{r}_{c+1}"))
            if r > 0 and (r-1, c) in bound_vars:
                if (r-1, c) in self.kb.facts["LessV"]:
                    goals.append(("Less", f"?V_{r-1}_{c}", var))
                if (r-1, c) in self.kb.facts["GreaterV"]:
                    goals.append(("Greater", f"?V_{r-1}_{c}", var))
            if r < self.N-1 and (r+1, c) in bound_vars:
                if (r, c) in self.kb.facts["LessV"]:
                    goals.append(("Less", var, f"?V_{r+1}_{c}"))
                if (r, c) in self.kb.facts["GreaterV"]:
                    goals.append(("Greater", var, f"?V_{r+1}_{c}"))

            
            bound_vars.add((r, c))

        return goals

    def backward_chaining(self, on_update=None) -> bool:
        """Chạy SLD Resolution. Trả về True nếu tìm được solution."""
        self.inferences = 0
        query = self._build_top_level_query()

        for solution_env in self.engine.prove(query, {}, on_update):
            for r in range(self.N):
                for c in range(self.N):
                    var = f"?V_{r}_{c}"
                    val = substitute(var, solution_env)
                    if isinstance(val, int):
                        self.assignment[(r, c)] = val
            return True

        return False

    def prolog_query_single_cell(self, r: int, c: int) -> List[int]:
        """Query đơn: ?- Val(r, c, ?X). Trả về tất cả giá trị hợp lệ."""
        self.inferences = 0
        query = [("Val", r, c, "?X")]
        results = []
        for env in self.engine.prove(query, {}):
            val = substitute("?X", env)
            if isinstance(val, int):
                results.append(val)
        return sorted(set(results))

    def _print_sample_clauses(self):
        print("\n[Sample Horn Clauses]")
        shown = 0
        for pred, clauses in self.horn_kb.rules.items():
            if shown >= 6: break
            for clause in clauses[:2]:
                print(f"  {clause}")
                shown += 1
        print("  ...")


def cli_update_viewer(r, c, v, status: str):
    if status == "TRYING" and r is not None:
        print(f"  → SLD Resolving: Val({r},{c},{v})")
    elif status == "BACKTRACK":
        print(f"  × Unification failed → Backtracking...")


def main():
    input_file  = "input-01.txt"
    output_file = "output-01.txt"

    print("=" * 75)
    print("FUTOSHIKI — HORN CLAUSE + SLD RESOLUTION + MRV/DEGREE + DOMAIN PRUNING")
    print("=" * 75)

    result = generate_ground_kb_from_file(input_file)
    if not result:
        print("Cannot load input!")
        return

    kb, initial = result
    solver = FutoshikiSolver(kb, initial)

    print("\n[Prolog Query] ?- Val(0, 1, X).")
    answers = solver.prolog_query_single_cell(0, 1)
    print(f"  X ∈ {answers}  (inferences: {solver.inferences})")

    print("\n[Starting SLD Resolution...]\n")
    start = time.time()
    success = solver.backward_chaining(on_update=cli_update_viewer)
    elapsed = time.time() - start

    if success:
        print(f"\n✓ Proof completed in {elapsed:.4f}s")
        print(f"  Total inferences: {solver.inferences}")
        board_str = format_board(kb, solver.assignment)
        print(board_str)
        with open(output_file, 'w') as f:
            f.write(board_str + "\n")
        print(f"\nSaved to {output_file}")
    else:
        print(f"\n✗ No solution found ({elapsed:.4f}s)")
        print(f"  Total inferences: {solver.inferences}")


if __name__ == "__main__":
    main()