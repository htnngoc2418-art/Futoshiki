import os
import time
import importlib
import threading
import customtkinter as ctk

ctk.set_appearance_mode("Light")  

class FutoshikiGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Futoshiki Game")
        
        self.win_width = 900
        self.win_height = 800 
        self.root.geometry(f"{self.win_width}x{self.win_height}")
        self.root.resizable(True, True) 
        
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.inputs_dir = os.path.join(self.base_dir, "inputs")
        self.outputs_dir = os.path.join(self.base_dir, "outputs")
        os.makedirs(self.inputs_dir, exist_ok=True)
        os.makedirs(self.outputs_dir, exist_ok=True)
      
        self.bg_soft_blue = "#F0F9FF"   
        self.card_bg = "#FFFFFF"        
        self.sky_primary = "#38BDF8"    
        self.rose_soft = "#FFF1F2"      
        self.rose_text = "#F43F5E"      
        self.emerald_soft = "#ECFDF5"   
        self.emerald_text = "#10B981"   
        self.cell_pink = "#FDF2F8"      
        self.cell_blue = "#EFF6FF"      
        self.given_gold = "#E6C280"     
        self.col_trying = "#FFF59D"
        self.col_backtrack = "#FFCDD2"
        self.col_win = "#C8E6C9"
        
        self.root.configure(fg_color=self.bg_soft_blue)
        
        self.cells = {}
        self.kb = None
        self.initial_assignment = {}
        self.is_solving = False 
        
        self.title_lbl = ctk.CTkLabel(self.root, text="✨ Futoshiki ✨", 
                                      font=ctk.CTkFont(family="Quicksand", size=40, weight="bold"),
                                      text_color=self.sky_primary) 
        self.title_lbl.pack(pady=(10, 5))
        
        self.setup_controls()
        self.setup_board_frame()
        self.load_board()

    def setup_controls(self):
        self.control_frame = ctk.CTkFrame(self.root, corner_radius=20, fg_color=self.card_bg, border_width=0)
        self.control_frame.pack(pady=5, padx=30, fill="x")

        from knowledge_base import generate_ground_kb_from_file

        raw_files = [f for f in os.listdir(self.inputs_dir) if f.startswith('input') and f.endswith('.txt')]
        raw_files.sort()
        
        difficulty_map = {
            "01": "Dễ", "02": "Dễ", "03": "Dễ", "04": "Dễ", "05": "Dễ",
            "06": "Dễ", "07": "Dễ", "08": "Dễ", "09": "Dễ", "10": "Dễ",
            "11": "Khó", "12": "Khó", "13": "Khó",
            "14": "Vô nghiệm",
            "15": "Trung bình"
        }
        input_files = [f"{f} ({difficulty_map.get(f.split('-')[1].split('.')[0], 'Mới')})" for f in raw_files] if raw_files else ["Chưa có file"]

        algorithms = ["Backward Chaining", "Forward Chaining", "A* Search", "Backtracking", "Brute Force"]

        ctk.CTkLabel(self.control_frame, text="Màn chơi:", font=ctk.CTkFont(size=14, weight="bold"), text_color="#0369A1").grid(row=0, column=0, padx=(15,5), pady=(10, 5), sticky="e")
        self.file_var = ctk.StringVar(value=input_files[0])
        self.file_combo = ctk.CTkOptionMenu(self.control_frame, variable=self.file_var, values=input_files, corner_radius=12, fg_color="#E0F2FE", text_color="#0369A1", button_color="#BAE6FD", button_hover_color="#7DD3FC")
        self.file_combo.grid(row=0, column=1, padx=5, pady=(10, 5), sticky="w")
        self.file_combo.configure(command=self.load_board) 

        ctk.CTkLabel(self.control_frame, text="AI Core:", font=ctk.CTkFont(size=14, weight="bold"), text_color="#0369A1").grid(row=1, column=0, padx=(15,5), pady=(5, 10), sticky="e")
        self.algo_var = ctk.StringVar(value=algorithms[2])
        self.algo_combo = ctk.CTkOptionMenu(self.control_frame, variable=self.algo_var, values=algorithms, corner_radius=12, fg_color="#FEF3C7", text_color="#92400E", button_color="#FDE68A", button_hover_color="#FCD34D")
        self.algo_combo.grid(row=1, column=1, padx=5, pady=(5, 10), sticky="w")

        self.btn_solve = ctk.CTkButton(self.control_frame, text="🚀 START", command=self.start_solving,
                                       font=ctk.CTkFont(size=16, weight="bold"), fg_color=self.sky_primary, hover_color="#0EA5E9", corner_radius=20, width=130, height=40)
        self.btn_solve.grid(row=0, column=2, padx=15, pady=(10, 5))

        self.btn_stop = ctk.CTkButton(self.control_frame, text="🛑 STOP", command=self.stop_solving, state="disabled",
                                      font=ctk.CTkFont(size=15, weight="bold"), fg_color="#F1F5F9", text_color="#94A3B8", corner_radius=20, width=130, height=40)
        self.btn_stop.grid(row=1, column=2, padx=15, pady=(5, 10))

        self.fast_mode_var = ctk.BooleanVar(value=False)
        self.switch_fast = ctk.CTkSwitch(self.control_frame, text="Giải siêu tốc", variable=self.fast_mode_var,
                                         progress_color=self.sky_primary, font=ctk.CTkFont(size=13), text_color="#64748B")
        self.switch_fast.grid(row=2, column=0, columnspan=3, pady=(0, 10))
        
        self.status_label = ctk.CTkLabel(self.root, text="Sẵn sàng ✨", font=ctk.CTkFont(size=16, weight="bold"), text_color="#94A3B8")
        self.status_label.pack(pady=0)

    def setup_board_frame(self):
        self.outer_board = ctk.CTkFrame(self.root, corner_radius=30, fg_color=self.card_bg, border_width=4, border_color="#FFFFFF")
        self.outer_board.pack(padx=20, pady=(10, 20), expand=True, fill="both")
        self.board_frame = None 

    def load_board(self, choice=None):
        from knowledge_base import generate_ground_kb_from_file
        raw_selection = self.file_var.get()
        if raw_selection == "Chưa có file": return
        
        file_name = raw_selection.split(' ')[0]
        file_path = os.path.join(self.inputs_dir, file_name)
        result = generate_ground_kb_from_file(file_path)
        
        if not result: return
        self.kb, self.initial_assignment = result
        self.status_label.configure(text=f"Màn {file_name} ({self.kb.N}x{self.kb.N}) đã sẵn sàng ✨", text_color=self.sky_primary)
        
        if self.board_frame is not None:
            self.board_frame.destroy()
            
        self.board_frame = ctk.CTkFrame(self.outer_board, fg_color="transparent")
        self.board_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.cells.clear()
        
        if self.kb.N <= 4:
            c_size, s_size, f_size, sign_size, radius = 80, 35, 40, 24, 12
        elif self.kb.N <= 6:
            c_size, s_size, f_size, sign_size, radius = 60, 25, 28, 20, 10
        elif self.kb.N <= 7:
            c_size, s_size, f_size, sign_size, radius = 45, 18, 20, 14, 8
        else:
            c_size, s_size, f_size, sign_size, radius = 35, 12, 16, 12, 6

        for i in range(self.kb.N * 2 - 1):
            msize = c_size if i % 2 == 0 else s_size
            self.board_frame.grid_rowconfigure(i, minsize=msize, weight=0)
            self.board_frame.grid_columnconfigure(i, minsize=msize, weight=0)
            
        for r in range(self.kb.N):
            for c in range(self.kb.N):
                val = self.initial_assignment.get((r, c), "")
                is_given = val != ""
                bg_color = self.given_gold if is_given else (self.cell_pink if (r+c)%2==0 else self.cell_blue)
                text_col = "#FFFFFF" if is_given else ("#F472B6" if (r+c)%2==0 else "#60A5FA")
                
                cell_frame = ctk.CTkFrame(self.board_frame, width=c_size, height=c_size, corner_radius=radius, fg_color=bg_color)
                cell_frame.grid(row=r*2, column=c*2, padx=0, pady=0)
                cell_frame.grid_propagate(False) 
                
                label = ctk.CTkLabel(cell_frame, text=str(val), font=ctk.CTkFont(family="Quicksand", size=f_size, weight="bold"), text_color=text_col)
                label.place(relx=0.5, rely=0.5, anchor="center")
                self.cells[(r, c)] = {"frame": cell_frame, "label": label, "is_given": is_given, "base_color": bg_color}

                if c < self.kb.N - 1:
                    sign = "<" if (r, c) in self.kb.facts["LessH"] else (">" if (r, c) in self.kb.facts["GreaterH"] else "")
                    if sign:
                        sign_h_frame = ctk.CTkFrame(self.board_frame, width=s_size, height=c_size, fg_color="transparent")
                        sign_h_frame.grid(row=r*2, column=c*2+1)
                        sign_h_frame.grid_propagate(False)
                        lbl_h = ctk.CTkLabel(sign_h_frame, text=sign, font=ctk.CTkFont(family="Arial", size=sign_size, weight="bold"), text_color="#94A3B8")
                        lbl_h.place(relx=0.5, rely=0.5, anchor="center")

            if r < self.kb.N - 1:
                for c_v in range(self.kb.N):
                    sign_v = "v" if (r, c_v) in self.kb.facts["LessV"] else ("^" if (r, c_v) in self.kb.facts["GreaterV"] else "")
                    if sign_v:
                        sign_v_frame = ctk.CTkFrame(self.board_frame, width=c_size, height=s_size, fg_color="transparent")
                        sign_v_frame.grid(row=r*2+1, column=c_v*2)
                        sign_v_frame.grid_propagate(False)
                        lbl_v = ctk.CTkLabel(sign_v_frame, text=sign_v, font=ctk.CTkFont(family="Arial", size=sign_size, weight="bold"), text_color="#94A3B8")
                        lbl_v.place(relx=0.5, rely=0.5, anchor="center")

    def gui_update_callback(self, r, c, v, status, g=None, h=None, f_val=None):
        if not self.is_solving: raise InterruptedError("STOP")
        
        if status == "TRYING":
            if g is not None:
                print(f"  Cell({r},{c})={v}  g={g}  h={h:.0f}  f={f_val:.0f}")
            else:
                print(f"Assigning Cell({r},{c}) = {v}")
        elif status == "BACKTRACK":
            print(f"Conflict! Backtracking Cell({r},{c})")

       
        self.root.after(0, self._update_cell_ui, r, c, v, status)
        
       
        time.sleep(0.015) 

    def _update_cell_ui(self, r, c, v, status):
        if (r, c) not in self.cells: return 
        cell = self.cells[(r, c)]
        if status == "TRYING":
            cell["label"].configure(text=str(v) if v != 0 else "", text_color="#1E293B")
            cell["frame"].configure(fg_color=self.col_trying) 
        elif status == "BACKTRACK":
            cell["label"].configure(text="", text_color="#FFFFFF")
            cell["frame"].configure(fg_color=self.col_backtrack) 
            self.root.after(35, lambda: cell["frame"].configure(fg_color=cell["base_color"]))

    def start_solving(self):
        if self.file_var.get() == "Chưa có file": return
        self.load_board(); self.is_solving = True
        selected_algo = self.algo_var.get()
        
        self.status_label.configure(text=f"Thuật toán đang chạy... ✨", text_color=self.sky_primary) 
        
        self.btn_solve.configure(state="disabled", fg_color="#E2E8F0", text_color="#94A3B8")
        self.btn_stop.configure(state="normal", fg_color=self.rose_soft, text_color=self.rose_text) 
        
       
        thread = threading.Thread(target=self._solve_in_background, args=(selected_algo, self.fast_mode_var.get()))
        thread.daemon = True; thread.start()

    def stop_solving(self):
        self.is_solving = False
        self.btn_stop.configure(text="Đang dừng...")

    def _solve_in_background(self, selected_algo, is_fast_mode):
        from knowledge_base import format_board
        def dummy_cb(*a, **k):
            if not self.is_solving: raise InterruptedError("STOP")
        cb = dummy_cb if is_fast_mode else self.gui_update_callback
        success = False; solver_instance = None; start_time = time.time()
        try:
            m_map = {"Backtracking":"backtracking","Brute Force":"brute_force","A* Search":"a_star","Forward Chaining":"forward_chaining","Backward Chaining":"backward_chaining"}
            module_name = m_map.get(selected_algo, "a_star")
            method_name = "solve" if "A*" in selected_algo else module_name.replace("_search", "")
            if "chaining" in module_name: method_name = module_name
            
            module = importlib.import_module(module_name)
            solver_instance = module.FutoshikiSolver(self.kb, self.initial_assignment)
            success = getattr(solver_instance, method_name)(on_update=cb)
        except Exception: pass
        self.root.after(0, self._finish, success, time.time()-start_time, solver_instance, selected_algo)

    def _finish(self, success, t, solver, algo):
        self.btn_solve.configure(state="normal", fg_color=self.sky_primary, text_color="#FFFFFF")
        self.btn_stop.configure(state="disabled", fg_color="#F1F5F9", text_color="#94A3B8", text="🛑 STOP")
        self.is_solving = False
        
        if success:
            self.status_label.configure(text=f"Thành công! Giải xong trong {t:.3f}s ✨", text_color=self.emerald_text)
            for (r,c), cell in self.cells.items():
                if not cell["is_given"]:
                    cell["label"].configure(text=str(solver.assignment.get((r,c),"")), text_color="#064E3B")
                    cell["frame"].configure(fg_color=self.col_win)
            
            from knowledge_base import format_board
            raw_selection = self.file_var.get()
            input_name = raw_selection.split(' ')[0]
            output_name = input_name.replace("input", "output")
            output_path = os.path.join(self.outputs_dir, output_name)
           
            board_str = format_board(self.kb, solver.assignment)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(board_str + "\n")
            
        else:
            txt = "❌ Vô nghiệm!"
           
            if "Forward" in algo:
                is_stuck = True 
             
                if hasattr(solver, 'domains'):
                    for dom in solver.domains.values():
                        if len(dom) == 0:
                            is_stuck = False 
                            break
                if is_stuck:
                    txt = "⚠️ Bị kẹt!"

            self.status_label.configure(text=f"{txt} ({t:.3f}s)", text_color=self.rose_text)

if __name__ == "__main__":
    app = ctk.CTk(); gui = FutoshikiGUI(app); app.mainloop()