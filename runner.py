from core.parser import read_input, write_output
from core.model import Futoshiki

def run_all():
    for i in range(1, 11):
        input_file = f"Inputs/input-{i:02d}.txt"
        output_file = f"Outputs/output-{i:02d}.txt"

        try:
            # Đọc file
            N, grid, H, V = read_input(input_file) 

            # Khởi tạo state
            state = Futoshiki(N, grid, H, V)

            # Ghi kết quả
            write_output(output_file, state.N, state.grid, state.H, state.V)
            
        except Exception as e:
            print(f"Error processing {input_file}: {e}")