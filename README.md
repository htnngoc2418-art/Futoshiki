# Đồ Án 2: Futoshiki 

## Thông Tin Chung

- **Môn học:** CSC14003 - Cơ sở Trí tuệ Nhân tạo
- **Khoa:** Công nghệ Thông tin - Trường Đại học Khoa học Tự nhiên, ĐHQG-HCM
- **Học kỳ:** II - Năm học: 2025-2026

---

## Mô Tả Đồ án

Đồ án triển khai, phân tích và so sánh các thuật toán giải bài toán **Futoshiki** - dạng bài toán thỏa mãn ràng buộc (CSP). Futoshiki là trò chơi logic trên lưới n×n, trong đó mỗi hàng và mỗi cột chứa các số từ 1 đến n không trùng lặp, đồng thời thỏa mãn các ràng buộc bất đẳng thức giữa các ô kề nhau.

---
 
## Danh Sách Thuật Toán
 
Hầu hết các thuật toán đều được triển khai thành **2 phiên bản**:
- **Original:** Cài đặt thuần túy theo lý thuyết cơ bản
- **Advanced:** Bản nâng cao có tích hợp thêm các kỹ thuật tối ưu như **MRV** , **Forward Checking**, **AC-3**, hoặc kết hợp nhiều chiến lược suy luận để tăng tốc độ và giảm không gian tìm kiếm
 
### Các thuật toán triển khai
 
 - **Forward Chaining** *(Original & Advanced)*
- **Backward Chaining** *(Original & Advanced)*
- **Brute Force** *(Original & Advanced)*
- **Backtracking** *(Original & Advanced)*
- **A\* Search** *(tích hợp sẵn MRV & AC-3)*
 
---

## Cấu Trúc Thư Mục

```text
└── FUTOSHIKI/
    ├── algorithms/                            # Các thuật toán giải Futoshiki
    │   ├── __init__.py
    │   ├── a_star.py                          
    │   ├── backtracking_advanced.py           
    │   ├── backtracking.py                    
    │   ├── backward_chaining_advanced.py      
    │   ├── backward_chaining.py               
    │   ├── brute_force_advanced.py            
    │   ├── brute_force.py                     
    │   ├── forward_chaining_advanced.py       
    │   └── forward_chaining.py                
    ├── core/                                  # Lõi xử lý
    │   ├── constraints.py                     # Định nghĩa các ràng buộc CSP
    │   ├── model.py                           # Mô hình bài toán Futoshiki
    │   └── parser.py                          # Đọc & phân tích file input
    ├── Inputs/                                
    ├── Outputs/                               
    ├── statistics/                            # Thống kê & trực quan hóa kết quả
    │   ├── charts/                            # Biểu đồ so sánh hiệu năng
    │   ├── estimated_runtime.py               # Ước lượng thời gian chạy
    │   ├── note.txt                           # Ghi chú thống kê
    │   ├── results_hard_testcases.csv         # Kết quả test case khó
    │   ├── results_hybrid_algo.csv            # Kết quả thuật toán kết hợp
    │   ├── results_original_algo.csv          # Kết quả thuật toán gốc
    │   ├── run_statistics.py                  # Chạy thống kê tổng hợp
    │   └── visualization.py                   # Trực quan hóa biểu đồ
    ├── knowledge_base.py                      # Cơ sở tri thức cho logic-based
    ├── main_gui.py                            # Giao diện đồ họa chính (GUI)
    └── README.md
```

---

## Cài Đặt & Chạy

### Clone Repository

```bash
git clone https://github.com/htnngoc2418-art/Futoshiki.git
cd Futoshiki
```

### Cài đặt Dependencies

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
pip install customtkinter pillow
```

### Chạy chương trình

**Chạy giao diện đồ họa chính:**

```bash
python main_gui.py
```

---

## Giao Diện Chương Trình

Chương trình cung cấp giao diện đồ họa (GUI) với 2 tab chức năng chính:

### Tab 1 - Giải Đố

Giao diện trực quan cho phép:

- **Chọn màn chơi:** Chọn file input với độ khó tùy chọn
- **Chọn AI Core:** Lựa chọn thuật toán giải 
- **Tùy chọn Giải siêu tốc:** Bật/tắt chế độ giải nhanh (bỏ qua animation từng bước)
- **Nút START / STOP:** Khởi chạy hoặc dừng quá trình giải
- **Tiến trình chạy:** Hiển thị log từng bước giải
- **Lưới Futoshiki:** Trực quan hóa bảng số và các ràng buộc bất đẳng thức (`<`, `>`, `v`, `^`)

### Tab 2 - So Sánh

Giao diện cho phép chạy và so sánh hiệu năng các thuật toán:

- **Chạy Ước lượng:** Chạy ngầm script ước tính thời gian thực thi của từng thuật toán trên toàn bộ test case, kết quả lưu vào file CSV
- **Vẽ Biểu Đồ:** Trực quan hóa kết quả dưới dạng biểu đồ so sánh (thời gian chạy, bộ nhớ sử dụng trung bình, số lần suy luận/mở rộng node theo log scale) cho từng kích thước lưới
- **Chạy Thống kê:** Chạy toàn bộ thống kê chi tiết và lưu kết quả ra CSV
- **Dừng:** Dừng script đang chạy ngầm
 
Kết quả được xem qua 3 tab con:
- **Console Log:** Theo dõi output trực tiếp từ script
- **Xem Bảng CSV:** Hiển thị bảng kết quả thời gian chạy của từng thuật toán trên từng input
- **Xem Biểu Đồ:** Chọn biểu đồ và làm mới để xem:
  - `hard_mem_exp.png` — Bộ nhớ & số suy luận trên test case khó (Original algorithms)
  - `hard_time.png` — Thời gian chạy trên test case khó (Original algorithms)
  - `hybrid_mem_exp.png` — Bộ nhớ & số suy luận (Advanced algorithms)
  - `hybrid_time.png` — Thời gian chạy (Advanced algorithms)

---  

## Test Cases
 
Tổng cộng **15 test case** với kích thước lưới từ 4×4 đến 9×9, được phân loại theo độ khó:
 
| File | Độ khó |
|---|---|
| input-01.txt → input-10.txt | Dễ |
| input-11.txt → input-13.txt | Khó |
| input-14.txt | Vô nghiệm |
| input-15.txt | Trung bình |
 
---

## Tác Giả

**Nhóm sinh viên - Đồ án 2**

| STT | MSSV | Họ và Tên |
|---|---|---|
| 1 | 24127089 | Hồ Thị Như Ngọc |
| 2 | 24127194 | Hoàng Trung Kiên |
| 3 | 24127586 | Trần Tường Vi |
| 4 | 24127595 | Lê Thị Như Ý |

**Môn học:** CSC14003 - Cơ sở Trí tuệ Nhân tạo

**Khoa:** Công nghệ Thông tin - ĐHKHTN TPHCM

**Năm học:** 2025-2026

---
