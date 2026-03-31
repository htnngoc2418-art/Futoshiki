import time
from typing import List, Callable, Optional
from knowledge_base import KnowledgeBase, generate_full_ground_kb, generate_ground_kb_from_file, format_board

class FutoshikiSolver:
    """Thuật toán SLD Resolution / Backward Chaining cho Futoshiki."""
    def __init__(self, kb: KnowledgeBase, initial_assignment: dict):
        self.kb = kb
        self.assignment = initial_assignment.copy()

    def prolog_query_deep(self, r: int, c: int) -> List[int]:
        """
        Deep SLD Resolution Query: ?- Val(r, c, X).
        Thử gán X và gọi đệ quy backward_chaining để chứng minh toàn bộ nhánh.
        Trả về danh sách các giá trị X thực sự dẫn đến đích.
        """
        valid_answers = []
        if (r, c) in self.assignment:
            return [self.assignment[(r, c)]]

        # Sao lưu trạng thái GỐC trước khi thử nghiệm
        backup_assignment = self.assignment.copy()

        for v in range(1, self.kb.N + 1):
            if self.kb.is_consistent_with_rules(r, c, v, self.assignment):
                # Thử gán giá trị (Assume goal)
                self.assignment[(r, c)] = v
                
                # Chạy deep resolution thử xem nhánh này có khả thi để giải hết bảng không
                # Truyền on_update=None để ẩn log trong quá trình query ngầm
                if self.backward_chaining(0, 0, on_update=None):
                    valid_answers.append(v)
                    
                # Phục hồi nguyên trạng từ bản sao lưu (Không dùng del)
                self.assignment = backup_assignment.copy()
                
        return valid_answers

    def backward_chaining(self, r: int = 0, c: int = 0, 
                          on_update: Optional[Callable[[int, int, int, str], None]] = None) -> bool:
        """Thuật toán đệ quy mô phỏng cây SLD Resolution giải toàn bộ bảng."""
        if r == self.kb.N:
            return True
            
        if c == self.kb.N:
            return self.backward_chaining(r + 1, 0, on_update)
            
        if (r, c) in self.assignment:
            return self.backward_chaining(r, c + 1, on_update)
            
        for v in range(1, self.kb.N + 1):
            if self.kb.is_consistent_with_rules(r, c, v, self.assignment):
                self.assignment[(r, c)] = v
                
                if on_update: on_update(r, c, v, "TRYING")
                    
                if self.backward_chaining(r, c + 1, on_update):
                    return True
                    
                del self.assignment[(r, c)]
                
                if on_update: on_update(r, c, 0, "BACKTRACK")
                    
        return False


def cli_update_viewer(r: int, c: int, v: int, status: str):
    """Giao diện dòng lệnh cập nhật log."""
    if status == "TRYING":
        print(f"Assigning Cell({r}, {c}) = {v}")
    elif status == "BACKTRACK":
        print(f"Conflict! Backtracking Cell({r}, {c})")
    # time.sleep(0.01) # Mở ra khi quay video để chạy chậm

def main():
    input_file = "input-01.txt"
    output_file = "output-01.txt"
    
    print("=" * 65)
    print("FUTOSHIKI SOLVER - BACKWARD CHAINING (SLD RESOLUTION)")
    print("=" * 65)
    
    # --- DEMO 1: Sinh Ground KB tự động ---
    cnf_kb = generate_full_ground_kb(N=4, output_file="ground_kb_4x4.txt")
    print(f"-> Generated {len(cnf_kb)} complete CNF clauses (including inequalities).")
    print("-" * 65)
    
    print(f"Parsing Input File '{input_file}'...")
    result = generate_ground_kb_from_file(input_file)
    
    if result:
        kb, initial_assignment = result
        solver = FutoshikiSolver(kb, initial_assignment)
        
        # --- DEMO 2: Deep Prolog Query ---
        print("\n[Deep Resolution Demo] Querying empty cell (0, 0): ?- Val(0, 0, X)")
        deep_answers = solver.prolog_query_deep(0, 0)
        print(f"-> Prolog Engine proven answers (leads to solution): X = {deep_answers}")
        print("-" * 65)
        
        # --- DEMO 3: Giải toàn bộ và Đo thời gian ---
        print("\nStarting full Backward Chaining...\n")
        
        # Để test thời gian chuẩn, thay cli_update_viewer bằng None 
        # (việc in log ra màn hình sẽ làm chậm thời gian tính toán thật của AI)
        start_time = time.time()
        success = solver.backward_chaining(on_update=cli_update_viewer) 
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