import os
import time
import importlib
import threading
import subprocess
import csv
import glob
from tkinter import ttk
from PIL import Image
import customtkinter as ctk

ctk.set_appearance_mode("Light")  

class FutoshikiGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Futoshiki Game")
        
        self.win_width = 1250
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
        
        self.title_lbl = ctk.CTkLabel(self.root, text=" Futoshiki ", 
                                      font=ctk.CTkFont(family="Quicksand", size=40, weight="bold"),
                                      text_color=self.sky_primary) 
        self.title_lbl.pack(pady=(10, 5))
        
        
        self.tabview = ctk.CTkTabview(self.root, corner_radius=20, fg_color=self.card_bg, text_color=self.sky_primary)
        self.tabview.pack(expand=True, fill="both", padx=20, pady=10)
        
        self.tab_solve = self.tabview.add(" Giải Đố")
        self.tab_compare = self.tabview.add(" So Sánh")

        self.setup_controls()
        self.setup_board_frame()
        self.load_board()
        self.setup_compare_tab() 

    def setup_controls(self):
        self.control_frame = ctk.CTkFrame(self.tab_solve, corner_radius=20, fg_color=self.card_bg, border_width=0)
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

        algorithms = [
            "Backward Chaining", "Backward Chaining (Advanced)", 
            "Forward Chaining", "Forward Chaining (Advanced)", 
            "A* Search", "Backtracking", 
            "Brute Force", "Brute Force (Advanced)"
        ]

        ctk.CTkLabel(self.control_frame, text="Màn chơi:", font=ctk.CTkFont(size=14, weight="bold"), text_color="#0369A1").grid(row=0, column=0, padx=(15,5), pady=(10, 5), sticky="e")
        self.file_var = ctk.StringVar(value=input_files[0])
        self.file_combo = ctk.CTkOptionMenu(self.control_frame, variable=self.file_var, values=input_files, corner_radius=12, fg_color="#E0F2FE", text_color="#0369A1", button_color="#BAE6FD", button_hover_color="#7DD3FC")
        self.file_combo.grid(row=0, column=1, padx=5, pady=(10, 5), sticky="w")
        self.file_combo.configure(command=self.load_board) 

        ctk.CTkLabel(self.control_frame, text="AI Core:", font=ctk.CTkFont(size=14, weight="bold"), text_color="#0369A1").grid(row=1, column=0, padx=(15,5), pady=(5, 10), sticky="e")
        self.algo_var = ctk.StringVar(value=algorithms[2])
        self.algo_combo = ctk.CTkOptionMenu(self.control_frame, variable=self.algo_var, values=algorithms, corner_radius=12, fg_color="#FEF3C7", text_color="#92400E", button_color="#FDE68A", button_hover_color="#FCD34D")
        self.algo_combo.grid(row=1, column=1, padx=5, pady=(5, 10), sticky="w")

        self.btn_solve = ctk.CTkButton(self.control_frame, text=" START", command=self.start_solving,
                                       font=ctk.CTkFont(size=16, weight="bold"), fg_color=self.sky_primary, hover_color="#0EA5E9", corner_radius=20, width=130, height=40)
        self.btn_solve.grid(row=0, column=2, padx=15, pady=(10, 5))

        self.btn_stop = ctk.CTkButton(self.control_frame, text=" STOP", command=self.stop_solving, state="disabled",
                                      font=ctk.CTkFont(size=15, weight="bold"), fg_color="#F1F5F9", text_color="#94A3B8", corner_radius=20, width=130, height=40)
        self.btn_stop.grid(row=1, column=2, padx=15, pady=(5, 10))

        self.fast_mode_var = ctk.BooleanVar(value=False)
        self.switch_fast = ctk.CTkSwitch(self.control_frame, text="Giải siêu tốc", variable=self.fast_mode_var,
                                         progress_color=self.sky_primary, font=ctk.CTkFont(size=13), text_color="#64748B")
        self.switch_fast.grid(row=2, column=0, columnspan=3, pady=(0, 10))
        
        self.status_label = ctk.CTkLabel(self.root, text="Sẵn sàng ✨", font=ctk.CTkFont(size=16, weight="bold"), text_color="#94A3B8")
        self.status_label.pack(pady=0)

    def setup_board_frame(self):
        self.main_container = ctk.CTkFrame(self.tab_solve, fg_color="transparent")
        self.main_container.pack(padx=20, pady=(10, 20), expand=True, fill="both")
        self.outer_board = ctk.CTkFrame(self.main_container, corner_radius=30, fg_color=self.card_bg, border_width=4, border_color="#FFFFFF")
        self.outer_board.pack(side="left", expand=True, fill="both", padx=(0, 10))
        self.board_frame = None 

        self.log_frame = ctk.CTkFrame(self.main_container, width=350, corner_radius=20, fg_color=self.card_bg)
        self.log_frame.pack(side="right", fill="y", padx=(10, 0))
        self.log_frame.pack_propagate(False) 
        ctk.CTkLabel(self.log_frame, text=" Tiến trình chạy", font=ctk.CTkFont(family="Quicksand", size=18, weight="bold"), text_color=self.sky_primary).pack(pady=(15, 5))
        
        self.log_box = ctk.CTkTextbox(self.log_frame, font=ctk.CTkFont(family="Consolas", size=13), fg_color="#F8FAFC", text_color="#334155", wrap="word", corner_radius=10)
        self.log_box.pack(padx=15, pady=(5, 15), expand=True, fill="both")
    
        self.log_box.configure(state="disabled") 

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
            c_size, s_size, f_size, sign_size, radius = 70, 30, 32, 22, 12
        elif self.kb.N == 5:
            c_size, s_size, f_size, sign_size, radius = 55, 22, 24, 18, 10
        elif self.kb.N == 6:
            c_size, s_size, f_size, sign_size, radius = 52, 20, 22, 18, 8
        elif self.kb.N == 7:
            c_size, s_size, f_size, sign_size, radius = 42, 16, 18, 14, 6
        else: 
            c_size, s_size, f_size, sign_size, radius = 33, 12, 14, 12, 4
        
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
                    sign_v = "^" if (r, c_v) in self.kb.facts["LessV"] else ("v" if (r, c_v) in self.kb.facts["GreaterV"] else "")
                    if sign_v:
                        sign_v_frame = ctk.CTkFrame(self.board_frame, width=c_size, height=s_size, fg_color="transparent")
                        sign_v_frame.grid(row=r*2+1, column=c_v*2)
                        sign_v_frame.grid_propagate(False)
                        lbl_v = ctk.CTkLabel(sign_v_frame, text=sign_v, font=ctk.CTkFont(family="Arial", size=sign_size, weight="bold"), text_color="#94A3B8")
                        lbl_v.place(relx=0.5, rely=0.5, anchor="center")

    def gui_update_callback(self, r, c, v, status, g=None, h=None, f_val=None):
        if not self.is_solving: raise InterruptedError("STOP")
        
        log_text = ""
        if status == "TRYING":
            if g is not None:
                log_text = f"→ Cell({r},{c})={v} | g={g} h={h:.0f} f={f_val:.0f}"
            else:
                log_text = f"→ Thử Cell({r},{c}) = {v}"
        elif status == "BACKTRACK":
            log_text = f"  × Xung đột! Quay lui Cell({r},{c})"

        if log_text:
            def append_log():
                self.log_box.configure(state="normal") 
                self.log_box.insert("end", log_text + "\n")
                self.log_box.see("end") 
                self.log_box.configure(state="disabled") 
            self.root.after(0, append_log) 

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
        self.log_box.configure(state="normal")
        self.log_box.delete("0.0", "end") 
        self.log_box.configure(state="disabled")
        selected_algo = self.algo_var.get()
        
        self.status_label.configure(text=f"Thuật toán đang chạy... ", text_color=self.sky_primary) 
        
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
           
            m_map = {
                "Backtracking": ("backtracking", "backtracking"),
                "Brute Force": ("brute_force", "brute_force"),
                "Brute Force (Advanced)": ("brute_force_advanced", "brute_force"),
                "A* Search": ("a_star", "solve"),
                "Forward Chaining": ("forward_chaining", "forward_chaining"),
                "Forward Chaining (Advanced)": ("forward_chaining_advanced", "solve"), 
                "Backward Chaining": ("backward_chaining", "backward_chaining"),
                "Backward Chaining (Advanced)": ("backward_chaining_advanced", "backward_chaining")
            }
            
            module_name, method_name = m_map.get(selected_algo, ("a_star", "solve"))
            
            module = importlib.import_module(f"algorithms.{module_name}")
            solver_instance = module.FutoshikiSolver(self.kb, self.initial_assignment)
            success = getattr(solver_instance, method_name)(on_update=cb)
            
        except Exception as e:
            print(f"LỖI NGẦM (Nếu có): {e}") 
            pass
        self.root.after(0, self._finish, success, time.time()-start_time, solver_instance, selected_algo)

    def _finish(self, success, t, solver, algo):
        self.btn_solve.configure(state="normal", fg_color=self.sky_primary, text_color="#FFFFFF")
        self.btn_stop.configure(state="disabled", fg_color="#F1F5F9", text_color="#94A3B8", text=" STOP")
        self.is_solving = False
        
        if success:
            self.status_label.configure(text=f"Thành công! Giải xong trong {t:.3f}s ", text_color=self.emerald_text)
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
            txt = " Vô nghiệm!"
           
            if "Forward" in algo:
                is_stuck = True 
             
                if hasattr(solver, 'domains'):
                    for dom in solver.domains.values():
                        if len(dom) == 0:
                            is_stuck = False 
                            break
                if is_stuck:
                    txt = "Bị kẹt!"

    
            self.status_label.configure(text=f"{txt} ({t:.3f}s)", text_color=self.rose_text)
  
    def setup_compare_tab(self):
        self.compare_btn_frame = ctk.CTkFrame(self.tab_compare, corner_radius=20, fg_color=self.bg_soft_blue)
        self.compare_btn_frame.pack(pady=(10, 15), padx=20, fill="x")

        ctk.CTkLabel(self.compare_btn_frame, text="Khởi chạy các Script Python chạy ngầm và theo dõi kết quả trực tiếp.", 
                     font=ctk.CTkFont(size=14, slant="italic"), text_color="#64748B").pack(pady=10)

        btn_box = ctk.CTkFrame(self.compare_btn_frame, fg_color="transparent")
        btn_box.pack(pady=(0, 15))

        self.btn_run_est = ctk.CTkButton(btn_box, text="Chạy Ước lượng", 
                                         font=ctk.CTkFont(size=14, weight="bold"), fg_color="#10B981", hover_color="#059669", 
                                         corner_radius=15, height=45, command=lambda: self.run_comparison_script("estimated_runtime.py"))
        self.btn_run_est.pack(side="left", padx=15)

        self.btn_run_stat = ctk.CTkButton(btn_box, text=" Chạy Thống kê", 
                                          font=ctk.CTkFont(size=14, weight="bold"), fg_color="#F59E0B", hover_color="#D97706", 
                                          corner_radius=15, height=45, command=lambda: self.run_comparison_script("run_statistics.py"))
        
        self.btn_run_vis = ctk.CTkButton(btn_box, text=" Vẽ Biểu Đồ", 
                                         font=ctk.CTkFont(size=14, weight="bold"), fg_color="#8B5CF6", hover_color="#6D28D9", 
                                         corner_radius=15, height=45, command=lambda: self.run_comparison_script("visualization.py"))
        self.btn_run_vis.pack(side="left", padx=15)
        self.btn_run_stat.pack(side="left", padx=15)

        self.btn_stop_script = ctk.CTkButton(btn_box, text=" Dừng", state="disabled",
                                             font=ctk.CTkFont(size=14, weight="bold"), fg_color="#F1F5F9", text_color="#94A3B8", 
                                             corner_radius=15, height=45, command=self.stop_comparison_script)
        self.btn_stop_script.pack(side="left", padx=15)

        self.inner_tabview = ctk.CTkTabview(self.tab_compare, corner_radius=15, fg_color=self.card_bg, text_color=self.sky_primary)
        self.inner_tabview.pack(expand=True, fill="both", padx=20, pady=(0, 10))

        self.tab_log = self.inner_tabview.add(" Console Log")
        self.tab_table = self.inner_tabview.add(" Xem Bảng CSV")
        self.tab_chart = self.inner_tabview.add(" Xem Biểu Đồ")
      
        self.compare_log_box = ctk.CTkTextbox(self.tab_log, font=ctk.CTkFont(family="Consolas", size=13), 
                                              fg_color="#1E293B", text_color="#38BDF8", wrap="word", corner_radius=10)
        self.compare_log_box.pack(expand=True, fill="both", padx=10, pady=10)
        self.compare_log_box.configure(state="disabled")

       
        self.table_control = ctk.CTkFrame(self.tab_table, fg_color="transparent")
        self.table_control.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.table_control, text="Chọn bảng kết quả:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        self.csv_combo_var = ctk.StringVar(value="Trống")
        self.csv_combo = ctk.CTkOptionMenu(self.table_control, variable=self.csv_combo_var, values=["Trống"], command=self.load_csv_to_table)
        self.csv_combo.pack(side="left", padx=10)

        self.btn_refresh = ctk.CTkButton(self.table_control, text=" Làm mới", width=100, command=self.refresh_csv_list)
        self.btn_refresh.pack(side="left", padx=5)

        self.table_frame = ctk.CTkFrame(self.tab_table, corner_radius=10)
        self.table_frame.pack(expand=True, fill="both", padx=10, pady=10)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#F8FAFC", foreground="#1E293B", rowheight=30, fieldbackground="#F8FAFC", borderwidth=0, font=("Quicksand", 10))
        style.map('Treeview', background=[('selected', self.sky_primary)])
        style.configure("Treeview.Heading", background=self.sky_primary, foreground="white", font=('Quicksand', 11, 'bold'))

        self.tree = ttk.Treeview(self.table_frame, selectmode="browse")
        self.tree_scroll_y = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree_scroll_x = ttk.Scrollbar(self.table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.tree_scroll_y.set, xscrollcommand=self.tree_scroll_x.set)

        self.tree_scroll_y.pack(side="right", fill="y")
        self.tree_scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(side="left", expand=True, fill="both")

        self.current_process = None
        self.refresh_csv_list() 

        self.chart_control = ctk.CTkFrame(self.tab_chart, fg_color="transparent")
        self.chart_control.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.chart_control, text="Chọn biểu đồ:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        self.chart_combo_var = ctk.StringVar(value="Trống")
        self.chart_combo = ctk.CTkOptionMenu(self.chart_control, variable=self.chart_combo_var, values=["Trống"], command=self.load_chart_image)
        self.chart_combo.pack(side="left", padx=10)

        self.btn_refresh_chart = ctk.CTkButton(self.chart_control, text=" Làm mới", width=100, command=self.refresh_chart_list)
        self.btn_refresh_chart.pack(side="left", padx=5)

        self.chart_display = ctk.CTkLabel(self.tab_chart, text="Chưa có biểu đồ. Hãy bấm 'Vẽ Biểu Đồ' trước.")
        self.chart_display.pack(expand=True, fill="both", padx=10, pady=10)

        self.refresh_chart_list()

    def refresh_csv_list(self):
        csv_files = []
        out_dir = os.path.join(self.base_dir, "outputs")
        stat_dir = os.path.join(self.base_dir, "statistics") 
        
        if os.path.exists(out_dir):
            csv_files.extend(glob.glob(os.path.join(out_dir, "*.csv")))
        if os.path.exists(stat_dir):
            csv_files.extend(glob.glob(os.path.join(stat_dir, "*.csv")))

        if csv_files:
            file_names = [os.path.basename(f) for f in csv_files]
            self.csv_path_map = {os.path.basename(f): f for f in csv_files}
            self.csv_combo.configure(values=file_names)
            
           
            if self.csv_combo_var.get() not in file_names:
                self.csv_combo_var.set(file_names[0])
            self.load_csv_to_table(self.csv_combo_var.get())
        else:
            self.csv_combo.configure(values=["Chưa có file CSV"])
            self.csv_combo_var.set("Chưa có file CSV")

    def load_csv_to_table(self, choice=None):
        file_name = self.csv_combo_var.get()
        if file_name == "Chưa có file CSV" or not hasattr(self, 'csv_path_map') or file_name not in self.csv_path_map:
            return

        file_path = self.csv_path_map[file_name]
        self.tree.delete(*self.tree.get_children()) 

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                if not headers: return

                self.tree["columns"] = headers
                self.tree["show"] = "headings"

                for col in headers:
                    self.tree.heading(col, text=col.replace("_", " ").title())
                    self.tree.column(col, width=130, anchor="center")

                for row in reader:
                    self.tree.insert("", "end", values=row)
        except Exception as e:
            self._print_compare_log(f"[LỖI] Không thể đọc file CSV: {e}")

    def refresh_chart_list(self):
        chart_dir = os.path.join(self.base_dir, "statistics", "charts")
        chart_files = glob.glob(os.path.join(chart_dir, "*.png"))
        
        if chart_files:
            file_names = [os.path.basename(f) for f in chart_files]
            file_names.sort()
            self.chart_path_map = {os.path.basename(f): f for f in chart_files}
            self.chart_combo.configure(values=file_names)
            
            if self.chart_combo_var.get() not in file_names:
                self.chart_combo_var.set(file_names[0])
            self.load_chart_image(self.chart_combo_var.get())
        else:
            self.chart_combo.configure(values=["Chưa có biểu đồ"])
            self.chart_combo_var.set("Chưa có biểu đồ")
            self.chart_display.configure(image=None, text="Chưa có biểu đồ. Hãy bấm 'Vẽ Biểu Đồ' trước.")

    def load_chart_image(self, choice=None):
        file_name = self.chart_combo_var.get()
        if file_name == "Chưa có biểu đồ" or not hasattr(self, 'chart_path_map') or file_name not in self.chart_path_map:
            return

        file_path = self.chart_path_map[file_name]
        try:
            img = Image.open(file_path)
          
            max_width = 750
            max_height = 350
           
            ratio = min(max_width / img.width, max_height / img.height)
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            
            my_image = ctk.CTkImage(light_image=img, dark_image=img, size=(new_width, new_height))
            self.chart_display.configure(image=my_image, text="")
            
        except Exception as e:
            self._print_compare_log(f"[LỖI] Không thể tải ảnh: {e}")
    
    def run_comparison_script(self, script_name):
        if self.current_process is not None:
            return
            
        script_path = os.path.join(self.base_dir, "statistics", script_name)
        if not os.path.exists(script_path):
            self._print_compare_log(f"[LỖI] Không tìm thấy file {script_name} trong thư mục.")
            return

        self.btn_run_est.configure(state="disabled")
        self.btn_run_stat.configure(state="disabled")
        self.btn_run_vis.configure(state="disabled")
        self.btn_stop_script.configure(state="normal", fg_color=self.rose_soft, text_color=self.rose_text)
        
        self.compare_log_box.configure(state="normal")
        self.compare_log_box.delete("0.0", "end")
        self.compare_log_box.configure(state="disabled")
        
        self._print_compare_log(f"Bắt đầu chạy: python {script_name}\n{'='*50}")

        thread = threading.Thread(target=self._execute_script_thread, args=(script_path,))
        thread.daemon = True
        thread.start()

    def _execute_script_thread(self, script_path):
        import sys
       
        self.current_process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace'
        )

        for line in self.current_process.stdout:
            self.root.after(0, self._print_compare_log, line.strip())

        self.current_process.wait()
        self.root.after(0, self._on_script_finish)

    def stop_comparison_script(self):
        if self.current_process is not None:
            self.current_process.terminate()
            self.current_process = None  
            self._print_compare_log("\n ĐÃ DỪNG TIẾN TRÌNH ÉP BUỘC!")
            
            self.btn_run_est.configure(state="normal")
            self.btn_run_stat.configure(state="normal")
            self.btn_run_vis.configure(state="normal")
            self.btn_stop_script.configure(state="disabled", fg_color="#F1F5F9", text_color="#94A3B8")

    def _on_script_finish(self):
        self.current_process = None
        self._print_compare_log(f"\n{'='*50}\n HOÀN THÀNH!")
        self.btn_run_est.configure(state="normal")
        self.btn_run_stat.configure(state="normal")
        self.btn_run_vis.configure(state="normal")
        self.btn_stop_script.configure(state="disabled", fg_color="#F1F5F9", text_color="#94A3B8")
        self.refresh_csv_list() 
        self.refresh_chart_list()
        
    def _print_compare_log(self, text):
        self.compare_log_box.configure(state="normal")
        self.compare_log_box.insert("end", text + "\n")
        self.compare_log_box.see("end")
        self.compare_log_box.configure(state="disabled")

if __name__ == "__main__":
    app = ctk.CTk(); gui = FutoshikiGUI(app); app.mainloop()