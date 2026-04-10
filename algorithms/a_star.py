import heapq
import time
from typing import Optional, Set
from knowledge_base import KnowledgeBase, generate_ground_kb_from_file, format_board

INF = float('inf')


#AC-3

def compute_domains(kb: KnowledgeBase, assignment: dict) -> dict:
    N = kb.N
    domains = {}
    for r in range(N):
        for c in range(N):
            if (r, c) in assignment:
                domains[(r, c)] = {assignment[(r, c)]}
            else:
                used = {assignment[r, j] for j in range(N) if (r, j) in assignment and j != c} | \
                       {assignment[i, c] for i in range(N) if (i, c) in assignment and i != r}
                domains[(r, c)] = set(range(1, N + 1)) - used
    return domains


def _revise(domains: dict, xi: tuple, xj: tuple, ctype: str) -> bool:
    removed = set()
    for vi in list(domains[xi]):
        satisfiable = any(
            (ctype in ("LessH", "LessV") and vi < vj) or
            (ctype in ("GreaterH", "GreaterV") and vi > vj) or
            (ctype in ("RowUniq", "ColUniq") and vi != vj)
            for vj in domains[xj]
        )
        if not satisfiable:
            removed.add(vi)
    domains[xi] -= removed
    return bool(removed)


def ac3(kb: KnowledgeBase, domains: dict) -> bool:
    N = kb.N
    queue = []

    for r in range(N):
        for c1 in range(N):
            for c2 in range(N):
                if c1 != c2: queue.append(((r, c1), (r, c2), "RowUniq"))
    for c in range(N):
        for r1 in range(N):
            for r2 in range(N):
                if r1 != r2: queue.append(((r1, c), (r2, c), "ColUniq"))
    for r in range(N):
        for c in range(N - 1):
            if (r, c) in kb.facts["LessH"]:
                queue += [((r, c), (r, c+1), "LessH"), ((r, c+1), (r, c), "GreaterH")]
            if (r, c) in kb.facts["GreaterH"]:
                queue += [((r, c), (r, c+1), "GreaterH"), ((r, c+1), (r, c), "LessH")]
    for r in range(N - 1):
        for c in range(N):
            if (r, c) in kb.facts["LessV"]:
                queue += [((r, c), (r+1, c), "LessV"), ((r+1, c), (r, c), "GreaterV")]
            if (r, c) in kb.facts["GreaterV"]:
                queue += [((r, c), (r+1, c), "GreaterV"), ((r+1, c), (r, c), "LessV")]

    while queue:
        xi, xj, ctype = queue.pop(0)
        if _revise(domains, xi, xj, ctype):
            if not domains[xi]:
                return False
            r_i, c_i = xi
            for c2 in range(N):
                if c2 != c_i: queue.append(((r_i, c2), xi, "RowUniq"))
            for r2 in range(N):
                if r2 != r_i: queue.append(((r2, c_i), xi, "ColUniq"))
            if c_i > 0:
                if (r_i, c_i-1) in kb.facts["LessH"]:   queue.append(((r_i, c_i-1), xi, "LessH"))
                if (r_i, c_i-1) in kb.facts["GreaterH"]: queue.append(((r_i, c_i-1), xi, "GreaterH"))
            if c_i < N - 1:
                if (r_i, c_i) in kb.facts["LessH"]:   queue.append(((r_i, c_i+1), xi, "GreaterH"))
                if (r_i, c_i) in kb.facts["GreaterH"]: queue.append(((r_i, c_i+1), xi, "LessH"))
            if r_i > 0:
                if (r_i-1, c_i) in kb.facts["LessV"]:   queue.append(((r_i-1, c_i), xi, "LessV"))
                if (r_i-1, c_i) in kb.facts["GreaterV"]: queue.append(((r_i-1, c_i), xi, "GreaterV"))
            if r_i < N - 1:
                if (r_i, c_i) in kb.facts["LessV"]:   queue.append(((r_i+1, c_i), xi, "GreaterV"))
                if (r_i, c_i) in kb.facts["GreaterV"]: queue.append(((r_i+1, c_i), xi, "LessV"))
    return True


#Heuristic h(s)

def heuristic(kb: KnowledgeBase, assignment: dict) -> float:
    """
    h(s) = số ô chưa gán sau khi AC-3 lan truyền ràng buộc.
    Nếu AC-3 phát hiện domain rỗng => h(s) = INF (dead-end).
    Admissible: mỗi ô chưa gán cần ít nhất 1 bước => h(s) <= h*(s).
    """
    domains = compute_domains(kb, assignment)
    if not ac3(kb, domains):
        return INF
    return sum(1 for r in range(kb.N) for c in range(kb.N) if (r, c) not in assignment)


#A*

class Node:
    def __init__(self, assignment: dict, g: int, h: float):
        self.assignment = assignment
        self.g = g
        self.h = h
        self.f = g + h

    def __lt__(self, other):
        return self.f < other.f or (self.f == other.f and self.g > other.g)


class FutoshikiSolver: # ĐÃ ĐỔI TÊN THÀNH FutoshikiSolver ĐỂ KHỚP VỚI GUI
    def __init__(self, kb: KnowledgeBase, initial_assignment: dict):
        self.kb = kb
        self.initial_assignment = initial_assignment.copy()
        self.assignment = initial_assignment.copy() # THÊM DÒNG NÀY CHO GUI ĐỌC KẾT QUẢ
        self.nodes_expanded = 0

    def _mrv(self, assignment: dict, domains: dict) -> Optional[tuple]:
        cells = [(r, c) for r in range(self.kb.N) for c in range(self.kb.N)
                 if (r, c) not in assignment]
        return min(cells, key=lambda cell: len(domains[cell]), default=None)

    def solve(self, on_update=None) -> bool: # ĐỔI RETURN TYPE THÀNH BOOL
        kb = self.kb
        total = kb.N * kb.N
        h0 = heuristic(kb, self.initial_assignment)
        start = Node(self.initial_assignment, len(self.initial_assignment), h0)

        heap = [(start.f, start)]
        visited: Set[frozenset] = set()
        self.nodes_expanded = 0

        while heap:
            _, cur = heapq.heappop(heap)
            key = frozenset(cur.assignment.items())
            if key in visited:
                continue
            visited.add(key)
            self.nodes_expanded += 1

            if len(cur.assignment) == total:
                self.assignment = cur.assignment # LƯU KẾT QUẢ VÀO SELF ĐỂ GUI LẤY ĐƯỢC
                return True # TRẢ VỀ TRUE KHI THÀNH CÔNG

            domains = compute_domains(kb, cur.assignment)
            if not ac3(kb, domains):
                continue

            cell = self._mrv(cur.assignment, domains)
            if cell is None:
                continue

            r, c = cell
            for v in sorted(domains[(r, c)]):
                if not kb.is_consistent_with_rules(r, c, v, cur.assignment):
                    continue
                new_assign = {**cur.assignment, (r, c): v}
                new_h = heuristic(kb, new_assign)
                if new_h == INF:
                    continue
                node = Node(new_assign, cur.g + 1, new_h)
                if frozenset(new_assign.items()) not in visited:
                    heapq.heappush(heap, (node.f, node))
                    
                    if on_update:
                        # KIỂM TRA ĐỂ TƯƠNG THÍCH CẢ TERMINAL (6 THAM SỐ) LẪN GUI (4 THAM SỐ)
                        try:
                            on_update(r, c, v, "TRYING") 
                        except TypeError:
                            on_update(r, c, v, node.g, new_h, node.f)

        return False


def main():
    input_file  = "input.txt"
    output_file = "output-01-astar.txt"

    print("=" * 55)
    print("FUTOSHIKI SOLVER — A* + AC-3 HEURISTIC")
    print("=" * 55)

    result = generate_ground_kb_from_file(input_file)
    if not result:
        print(f"Cannot read: {input_file}"); return

    kb, init = result
    solver = FutoshikiSolver(kb, init)

    start = time.time()
    solution_found = solver.solve(
        on_update=lambda r, c, v, g, h, f:
            print(f"  Cell({r},{c})={v}  g={g}  h={h:.0f}  f={f:.0f}")
    )
    elapsed = time.time() - start

    print(f"\nTime: {elapsed:.4f}s  |  Nodes expanded: {solver.nodes_expanded}")

    # Thay đổi biến 'solution' thành 'solver.assignment' khi truyền vào format_board
    if solution_found:
        # Lấy kết quả từ solver.assignment thay vì biến solution (vốn là True/False)
        board = format_board(kb, solver.assignment) 
        print("\n--- Solved! ---\n" + board)
        with open(output_file, 'w') as f:
            f.write(board + "\n")
        print(f"\nSaved to {output_file}")
    else:
        print("No solution found.")


if __name__ == "__main__":
    main()
