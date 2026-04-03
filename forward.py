import os
import time
import tracemalloc
from core.parser import read_input, write_output
from core.model import Futoshiki
from knowledge_base import KnowledgeBase

def forward_chaining_solver(input_path: str, output_path: str):
    inferences = 0 
    try:
        # A1, A3
        N, grid, H, V = read_input(input_path)
        state = Futoshiki(N, grid, H, V)
        kb = KnowledgeBase(N)
        
        for r in range(N):
            for c in range(N - 1):
                if state.H[r][c] == 1: kb.add_fact("LessH", r, c)
                elif state.H[r][c] == -1: kb.add_fact("GreaterH", r, c)
        for r in range(N - 1):
            for c in range(N):
                if state.V[r][c] == 1: kb.add_fact("LessV", r, c)
                elif state.V[r][c] == -1: kb.add_fact("GreaterV", r, c)

        domains = {(r, c): set(range(1, N + 1)) for r in range(N) for c in range(N)}
        agenda = []

        def remove_value(r, c, v_to_remove) -> bool:
            nonlocal inferences
            #A2
            if v_to_remove in domains[(r, c)]:
                domains[(r, c)].remove(v_to_remove)
                inferences += 1  
                
                if not domains[(r, c)]: return False 
                if len(domains[(r, c)]) == 1:
                    new_val = list(domains[(r, c)])[0]
                    if ("ASSIGN", r, c, new_val) not in agenda:
                        agenda.append(("ASSIGN", r, c, new_val))
                return True
            return False

        def enforce_less_than(r1, c1, r2, c2) -> bool:
            #A6 - A9
            local_changed = False
            if not domains[(r1, c1)] or not domains[(r2, c2)]: 
                return False
            
            # (r1, c1) < Max of (r2, c2)
            max_v2 = max(domains[(r2, c2)])
            for v in list(domains[(r1, c1)]):
                if v >= max_v2:
                    if remove_value(r1, c1, v): local_changed = True
                    
            # (r2, c2) > Min of (r1, c1)
            min_v1 = min(domains[(r1, c1)])
            for v in list(domains[(r2, c2)]):
                if v <= min_v1:
                    if remove_value(r2, c2, v): local_changed = True
                    
            return local_changed

        # A10
        for r in range(N):
            for c in range(N):
                if state.grid[r][c] != 0:
                    v_given = state.grid[r][c]
                    domains[(r, c)] = {v_given}
                    agenda.append(("ASSIGN", r, c, v_given))

        global_changed = True
        while global_changed or agenda:
            global_changed = False
            
            # A4, A5
            while agenda:
                _, r, c, v = agenda.pop(0)
                inferences += 1
                state.grid[r][c] = v
                for i in range(N):
                    if i != c and remove_value(r, i, v): global_changed = True
                    if i != r and remove_value(i, c, v): global_changed = True

            # A6 - A9
            for r in range(N):
                for c in range(N - 1):
                    if state.H[r][c] == 1: 
                        if enforce_less_than(r, c, r, c + 1): global_changed = True
                    elif state.H[r][c] == -1: 
                        if enforce_less_than(r, c + 1, r, c): global_changed = True

            for r in range(N - 1):
                for c in range(N):
                    if state.V[r][c] == 1: 
                        if enforce_less_than(r, c, r + 1, c): global_changed = True
                    elif state.V[r][c] == -1: 
                        if enforce_less_than(r + 1, c, r, c): global_changed = True

            if not agenda:
                # Row
                for r in range(N):
                    for v in range(1, N + 1):
                        cells = [c for c in range(N) if v in domains[(r, c)]]
                        if len(cells) == 1 and len(domains[(r, cells[0])]) > 1:
                            domains[(r, cells[0])] = {v}
                            agenda.append(("ASSIGN", r, cells[0], v))
                            global_changed = True
                # Col
                for c in range(N):
                    for v in range(1, N + 1):
                        cells = [r for r in range(N) if v in domains[(r, c)]]
                        if len(cells) == 1 and len(domains[(cells[0], c)]) > 1:
                            domains[(cells[0], c)] = {v}
                            agenda.append(("ASSIGN", cells[0], c, v))
                            global_changed = True

            if not agenda and not global_changed:
                # Row
                for r in range(N):
                    for c1 in range(N):
                        if len(domains[(r, c1)]) == 2:
                            for c2 in range(c1 + 1, N):
                                if domains[(r, c1)] == domains[(r, c2)]:
                                    pair_vals = domains[(r, c1)]
                                    for c3 in range(N):
                                        if c3 != c1 and c3 != c2:
                                            for val in pair_vals:
                                                if remove_value(r, c3, val): global_changed = True
                    
                    for c1 in range(N):
                        for c2 in range(c1 + 1, N):
                            for c3 in range(c2 + 1, N):
                                union_vals = domains[(r, c1)] | domains[(r, c2)] | domains[(r, c3)]
                                if len(union_vals) == 3:
                                    for c_other in range(N):
                                        if c_other not in (c1, c2, c3):
                                            for val in union_vals:
                                                if remove_value(r, c_other, val): global_changed = True

                # Col
                for c in range(N):
                    for r1 in range(N):
                        if len(domains[(r1, c)]) == 2:
                            for r2 in range(r1 + 1, N):
                                if domains[(r1, c)] == domains[(r2, c)]:
                                    pair_vals = domains[(r1, c)]
                                    for r3 in range(N):
                                        if r3 != r1 and r3 != r2:
                                            for val in pair_vals:
                                                if remove_value(r3, c, val): global_changed = True
                  
                    for r1 in range(N):
                        for r2 in range(r1 + 1, N):
                            for r3 in range(r2 + 1, N):
                                union_vals = domains[(r1, c)] | domains[(r2, c)] | domains[(r3, c)]
                                if len(union_vals) == 3:
                                    for r_other in range(N):
                                        if r_other not in (r1, r2, r3):
                                            for val in union_vals:
                                                if remove_value(r_other, c, val): global_changed = True

            if not agenda and not global_changed:
                # Row 
                for r in range(N):
                    for v1 in range(1, N + 1):
                        for v2 in range(v1 + 1, N + 1):
                            cells_v1 = [c for c in range(N) if v1 in domains[(r, c)]]
                            cells_v2 = [c for c in range(N) if v2 in domains[(r, c)]]
                            union_cells = list(set(cells_v1 + cells_v2))
                            if len(union_cells) == 2 and len(cells_v1) >= 1 and len(cells_v2) >= 1:
                                c1, c2 = union_cells[0], union_cells[1]
                                for val in list(domains[(r, c1)]):
                                    if val not in (v1, v2) and remove_value(r, c1, val): global_changed = True
                                for val in list(domains[(r, c2)]):
                                    if val not in (v1, v2) and remove_value(r, c2, val): global_changed = True
                                    
                # Col 
                for c in range(N):
                    for v1 in range(1, N + 1):
                        for v2 in range(v1 + 1, N + 1):
                            cells_v1 = [r for r in range(N) if v1 in domains[(r, c)]]
                            cells_v2 = [r for r in range(N) if v2 in domains[(r, c)]]
                            union_cells = list(set(cells_v1 + cells_v2))
                            if len(union_cells) == 2 and len(cells_v1) >= 1 and len(cells_v2) >= 1:
                                r1, r2 = union_cells[0], union_cells[1]
                                for val in list(domains[(r1, c)]):
                                    if val not in (v1, v2) and remove_value(r1, c, val): global_changed = True
                                for val in list(domains[(r2, c)]):
                                    if val not in (v1, v2) and remove_value(r2, c, val): global_changed = True

        
        write_output(output_path, state.N, state.grid, state.H, state.V)
        
        is_full = (state.find_empty() is None)
        return True, is_full, inferences

    except Exception as e:
        return False, False, inferences


if __name__ == "__main__":
    if not os.path.exists("Outputs"): os.makedirs("Outputs")
    
    print(f"{'TEST CASE':<12} | {'STATUS':<20} | {'TIME (s)':<10} | {'PEAK MEMORY (KB)':<18} | {'INFERENCES'}")
    print("-" * 80)
    
    total_time = 0.0
    total_inferences = 0
    max_memory_all = 0
    
    for i in range(1, 11):
        in_f, out_f = f"Inputs/input-{i:02d}.txt", f"Outputs/output-{i:02d}.txt"
        if os.path.exists(in_f):
            
            tracemalloc.start()
            start_time = time.perf_counter()
            
            ok, full, inferences = forward_chaining_solver(in_f, out_f)
            
            end_time = time.perf_counter()
            _, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            elapsed_time = end_time - start_time
            peak_memory_kb = peak_memory / 1024
            
            total_time += elapsed_time
            total_inferences += inferences
            if peak_memory_kb > max_memory_all:
                max_memory_all = peak_memory_kb
            
            if not ok: 
                status = "Logic Error"
            elif full: 
                status = "Solved"
            else: 
                status = "Unsolved"
                
            print(f"input-{i:02d}.txt | {status:<20} | {elapsed_time:<10.4f} | {peak_memory_kb:<18.2f} | {inferences}")
            
    print("-" * 80)
    print(f"TOTAL TIME: {total_time:.4f} seconds")
    print(f"TOTAL INFERENCES: {total_inferences}")
    print(f"MAX PEAK MEMORY ACROSS ALL TESTS: {max_memory_all:.2f} KB")