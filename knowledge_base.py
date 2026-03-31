import os
from typing import List, Tuple, Dict, Optional, Set

class KnowledgeBase:
    """
    Lớp lưu trữ Ground KB động (từ input) và xử lý logic kiểm tra ràng buộc.
    Dùng chung cho cả nhóm (Forward Chaining, Backward Chaining, A*).
    """
    def __init__(self, N: int):
        self.N = N
        self.facts: Dict[str, Set[Tuple]] = {
            "Given": set(), "LessH": set(), "GreaterH": set(),
            "LessV": set(), "GreaterV": set(),
        }
        
    def add_fact(self, predicate: str, *args) -> None:
        if predicate in self.facts:
            self.facts[predicate].add(args)

    def is_consistent_with_rules(self, r: int, c: int, v: int, current_assignment: Dict[Tuple[int, int], int]) -> bool:
        """Hàm kiểm tra nhất quán dùng chung cho mọi thuật toán."""
        
        # 0. Domain check (1 <= v <= N)
        if v < 1 or v > self.N: return False
            
        # 1. Enforce Given clues
        if (r, c) in current_assignment and current_assignment[(r, c)] != v: return False

        # 2. Row & Col uniqueness
        for other in range(self.N):
            if other != c and current_assignment.get((r, other)) == v: return False
            if other != r and current_assignment.get((other, c)) == v: return False

        # 3. Horizontal Constraints
        if c > 0 and (r, c - 1) in current_assignment:
            v_left = current_assignment[(r, c - 1)]
            if (r, c - 1) in self.facts["LessH"] and not (v_left < v): return False
            if (r, c - 1) in self.facts["GreaterH"] and not (v_left > v): return False
                
        if c < self.N - 1 and (r, c + 1) in current_assignment:
            v_right = current_assignment[(r, c + 1)]
            if (r, c) in self.facts["LessH"] and not (v < v_right): return False
            if (r, c) in self.facts["GreaterH"] and not (v > v_right): return False

        # 4. Vertical Constraints
        if r > 0 and (r - 1, c) in current_assignment:
            v_top = current_assignment[(r - 1, c)]
            if (r - 1, c) in self.facts["LessV"] and not (v_top < v): return False
            if (r - 1, c) in self.facts["GreaterV"] and not (v_top > v): return False
                
        if r < self.N - 1 and (r + 1, c) in current_assignment:
            v_bottom = current_assignment[(r + 1, c)]
            if (r, c) in self.facts["LessV"] and not (v < v_bottom): return False
            if (r, c) in self.facts["GreaterV"] and not (v > v_bottom): return False

        return True


def generate_full_ground_kb(N: int, output_file: str = "ground_kb.txt") -> List[List[Tuple]]:
    """
    Sinh toàn bộ Ground KB (CNF) bao gồm cả các ràng buộc bất đẳng thức có điều kiện.
    """
    print(f"Generating full structured Ground KB (CNF) for N={N}...")
    cnf_clauses = []
    text_lines = [] 
    
    # [A1] - [A4]: Domain, Row, Col uniqueness
    for r in range(N):
        for c in range(N):
            cnf_clauses.append([(True, r, c, v) for v in range(1, N + 1)])
            text_lines.append(f"[A1] Cell({r},{c}) >= 1 value: " + " OR ".join([f"Val({r},{c},{v})" for v in range(1, N + 1)]))
            for v1 in range(1, N + 1):
                for v2 in range(v1 + 1, N + 1):
                    cnf_clauses.append([(False, r, c, v1), (False, r, c, v2)])
                    text_lines.append(f"[A2] Cell({r},{c}) <= 1 value: ~Val({r},{c},{v1}) OR ~Val({r},{c},{v2})")
                    
    for r in range(N):
        for v in range(1, N + 1):
            for c1 in range(N):
                for c2 in range(c1 + 1, N):
                    cnf_clauses.append([(False, r, c1, v), (False, r, c2, v)])
                    text_lines.append(f"[A3] Row {r} unique {v}: ~Val({r},{c1},{v}) OR ~Val({r},{c2},{v})")

    for c in range(N):
        for v in range(1, N + 1):
            for r1 in range(N):
                for r2 in range(r1 + 1, N):
                    cnf_clauses.append([(False, r1, c, v), (False, r2, c, v)])
                    text_lines.append(f"[A4] Col {c} unique {v}: ~Val({r1},{c},{v}) OR ~Val({r2},{c},{v})")

    # [A5] - [A8]: Các Ràng buộc Bất đẳng thức (Inequalities)
    for r in range(N):
        for c in range(N - 1):
            for v1 in range(1, N + 1):
                for v2 in range(1, N + 1):
                    if v1 >= v2:
                        cnf_clauses.append([("NOT_LessH", r, c), (False, r, c, v1), (False, r, c + 1, v2)])
                        text_lines.append(f"[A5] ~LessH({r},{c}) OR ~Val({r},{c},{v1}) OR ~Val({r},{c+1},{v2})")
                    if v1 <= v2:
                        cnf_clauses.append([("NOT_GreaterH", r, c), (False, r, c, v1), (False, r, c + 1, v2)])
                        text_lines.append(f"[A6] ~GreaterH({r},{c}) OR ~Val({r},{c},{v1}) OR ~Val({r},{c+1},{v2})")

    for r in range(N - 1):
        for c in range(N):
            for v1 in range(1, N + 1):
                for v2 in range(1, N + 1):
                    if v1 >= v2:
                        cnf_clauses.append([("NOT_LessV", r, c), (False, r, c, v1), (False, r + 1, c, v2)])
                        text_lines.append(f"[A7] ~LessV({r},{c}) OR ~Val({r},{c},{v1}) OR ~Val({r+1},{c},{v2})")
                    if v1 <= v2:
                        cnf_clauses.append([("NOT_GreaterV", r, c), (False, r, c, v1), (False, r + 1, c, v2)])
                        text_lines.append(f"[A8] ~GreaterV({r},{c}) OR ~Val({r},{c},{v1}) OR ~Val({r+1},{c},{v2})")

    try:
        with open(output_file, 'w') as f:
            for line in text_lines: f.write(line + "\n")
        print(f"-> Saved {len(text_lines)} rigorous ground axioms to {output_file}")
    except Exception as e:
        print(f"Error writing Ground KB text to file: {e}")
        
    return cnf_clauses


def generate_ground_kb_from_file(file_path: str) -> Optional[Tuple[KnowledgeBase, Dict[Tuple[int, int], int]]]:
    """Khởi tạo KB và nạp Facts từ file input."""
    if not os.path.exists(file_path): return None
    try:
        with open(file_path, 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        N = len(lines[0].split(','))
        kb, assignment, line_idx = KnowledgeBase(N), {}, 0
        
        for r in range(N):
            values = list(map(int, lines[line_idx].split(',')))
            for c in range(N):
                if values[c] != 0:
                    kb.add_fact("Given", r, c, values[c])
                    assignment[(r, c)] = values[c]
            line_idx += 1
            
        for r in range(N):
            constraints = list(map(int, lines[line_idx].split(',')))
            for c in range(N - 1):
                if constraints[c] == 1: kb.add_fact("LessH", r, c)
                elif constraints[c] == -1: kb.add_fact("GreaterH", r, c)
            line_idx += 1
            
        for r in range(N - 1):
            constraints = list(map(int, lines[line_idx].split(',')))
            for c in range(N):
                if constraints[c] == 1: kb.add_fact("LessV", r, c)
                elif constraints[c] == -1: kb.add_fact("GreaterV", r, c)
            line_idx += 1
            
        return kb, assignment
    except Exception as e:
        print(f"Error parsing file: {e}")
        return None

def format_board(kb: KnowledgeBase, assignment: Dict[Tuple[int, int], int]) -> str:
    """Format bảng đẹp mắt."""
    lines = []
    for r in range(kb.N):
        row_str = ""
        for c in range(kb.N):
            val = assignment.get((r, c), 0)
            row_str += str(val) if val != 0 else "0"
            if c < kb.N - 1:
                if (r, c) in kb.facts["LessH"]: row_str += " < "
                elif (r, c) in kb.facts["GreaterH"]: row_str += " > "
                else: row_str += "   "
        lines.append(row_str)
        if r < kb.N - 1:
            vert_str = ""
            for c in range(kb.N):
                if (r, c) in kb.facts["LessV"]: vert_str += "^"
                elif (r, c) in kb.facts["GreaterV"]: vert_str += "v"
                else: vert_str += " "
                if c < kb.N - 1: vert_str += "   "
            lines.append(vert_str)
    return "\n".join(lines)