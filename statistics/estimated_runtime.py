import argparse
import csv
import glob
import os
import sys
import math

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from knowledge_base import generate_ground_kb_from_file

ALGORITHMS = [
    "brute_force",
    "backtracking",
    "forward_chaining",
    "backward_chaining",
    "a_star",
]

INPUT_FILE_NAMES = [f"input-{i:02}.txt" for i in range(1, 16)]
CSV_HEADERS = [f"input{i}" for i in range(1, 16)]

# ============================================================
# ANCHOR TIMES (giây) — Thời gian kỳ vọng THỰC CHẤT
#
# CÁCH TÍNH (không đơn giản dùng mean_time từ CSV):
#
#   mean_time trong CSV = trung bình của các test THÀNH CÔNG (timeout bị loại)
#   → KHÔNG phản ánh đúng khi có test timeout (>120s)
#
#   Công thức real expected time:
#     E[T] = success_rate × mean_success + (1 - success_rate) × T_timeout_lower
#
#   Nguồn dữ liệu: stats_small_board.csv, stats_big_board.csv
#
#   brute_force:
#     4x4: sr=1.0 → E=0.092s
#     5x5: sr=1.0 → E=0.123s
#     6x6: sr=1.0, mean=21.76s → E=21.76s
#     7x7: sr=0.7, mean_success=0.58s → E=0.7×0.58 + 0.3×120 = 36.4s
#     9x9: sr=0.0 → ALL timeout → E >> 120s (dùng 600s làm lower bound)
#
#   backtracking (MRV):
#     4x4: sr=1.0 → E=0.089s
#     5x5: sr=1.0 → E=0.128s
#     6x6: sr=0.7, mean_success=8.91s → E=0.7×8.91 + 0.3×120 = 42.2s
#     7x7: sr=1.0, mean=3.926s → E=3.926s
#          NOTE: sample bias — bộ test 7x7 là những puzzle tương đối dễ.
#          Để đảm bảo monotone và phản ánh đúng worst-case behavior:
#          dùng max(6x6 × 1.5, 7x7_mean) = max(63.3, 3.926) = 63.3s
#     9x9: sr=0.0 → ALL timeout → E >> 120s (dùng 600s)
#
#   backward_chaining (SLD Resolution):
#     4x4: sr=1.0 → E=0.102s
#     5x5: sr=1.0 → E=0.276s
#     6x6: sr=0.7, mean_success=18.16s → E=0.7×18.16 + 0.3×120 = 48.7s
#     7x7: sr=0.3, mean_success=4.81s  → E=0.3×4.81 + 0.7×120 = 85.4s
#     9x9: sr=0.0 → ALL timeout → E >> 120s (dùng 600s)
#
#   forward_chaining (constraint propagation):
#     Tất cả kích thước sr=1.0, dùng mean trực tiếp
#     4x4→0.127s, 5x5→0.165s, 6x6→0.468s, 7x7→0.764s, 9x9→2.54s
#
#   a_star (A* + AC-3):
#     Tất cả kích thước sr=1.0, dùng mean trực tiếp
#     4x4→0.146s, 5x5→0.295s, 6x6→1.865s, 7x7→2.808s, 9x9→39.13s
# ============================================================
_ANCHORS = {
    "brute_force": {
        4: 0.092,
        5: 0.123,
        6: 21.76,
        7: 36.4,   # E[T] kể timeout: 0.7×0.58 + 0.3×120
        9: 600.0,  # sr=0.0 → ALL timeout, lower bound estimate
    },
    "backtracking": {
        4: 0.089,
        5: 0.128,
        6: 42.2,   # E[T] kể timeout: 0.7×8.91 + 0.3×120
        7: 63.3,   # monotone fix: max(6x6×1.5, mean_7x7) do sample bias
        9: 600.0,  # sr=0.0 → ALL timeout
    },
    "backward_chaining": {
        4: 0.102,
        5: 0.276,
        6: 48.7,   # E[T] kể timeout: 0.7×18.16 + 0.3×120
        7: 85.4,   # E[T] kể timeout: 0.3×4.81 + 0.7×120
        9: 600.0,  # sr=0.0 → ALL timeout
    },
    "forward_chaining": {
        4: 0.127,
        5: 0.165,
        6: 0.468,
        7: 0.764,
        9: 2.540,
    },
    "a_star": {
        4: 0.146,
        5: 0.295,
        6: 1.865,
        7: 2.808,
        9: 39.13,
    },
}

# ============================================================
# DENSITY CORRECTION
#
# Mỗi puzzle cụ thể có thể khó/dễ hơn puzzle "trung bình"
# do mật độ ô trống và ràng buộc khác nhau.
#
# correction = (empty_ratio / empty_ref)^e_sens
#            × (constraint_density / constraint_ref)^c_sens
#
# Mật độ trống tham chiếu (empty / N²) từ các input thực nghiệm:
#   4x4: ~0.78,  5x5: ~0.90,  6x6: ~0.90,  7x7: ~0.91,  9x9: ~0.83
#
# Mật độ ràng buộc tham chiếu (constraints / N²) ≈ 0.30
#
# Độ nhạy empty (e_sens > 0): nhiều ô trống hơn → chậm hơn
#   brute_force cao nhất vì search space ~ N^empty
#   forward_chaining thấp nhất vì inference mạnh
#
# Độ nhạy constraint (c_sens < 0): nhiều ràng buộc → pruning tốt → nhanh hơn
#   backtracking hưởng lợi nhiều nhất từ constraint
#   forward_chaining hưởng lợi ít nhất (đã dùng constraint nội tại)
# ============================================================
_EMPTY_REF = {4: 0.78, 5: 0.90, 6: 0.90, 7: 0.91, 9: 0.83}
_CONSTRAINT_REF = 0.30

_EMPTY_SENSITIVITY = {
    "brute_force":       2.0,
    "backtracking":      1.5,
    "forward_chaining":  0.5,
    "backward_chaining": 1.2,
    "a_star":            1.0,
}
_CONSTRAINT_SENSITIVITY = {
    "brute_force":      -0.5,
    "backtracking":     -0.8,
    "forward_chaining": -0.3,
    "backward_chaining":-0.4,
    "a_star":           -0.6,
}

# Giới hạn correction tổng để tránh ước lượng quá xa thực tế
_CORRECTION_MIN = 0.05
_CORRECTION_MAX = 20.0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Ước lượng thời gian chạy cho mỗi thuật toán trên mỗi file input"
    )
    parser.add_argument(
        "--inputs",
        default=os.path.join(ROOT_DIR, "Inputs"),
        help="Thư mục chứa file input",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(ROOT_DIR, "statistics", "estimated_runtime.csv"),
        help="Đường dẫn file CSV xuất",
    )
    return parser.parse_args()


def collect_input_paths(inputs_dir):
    input_paths = {
        os.path.basename(path): path
        for path in glob.glob(os.path.join(inputs_dir, "input-*.txt"))
    }
    ordered_paths = []
    for name in INPUT_FILE_NAMES:
        if name not in input_paths:
            raise FileNotFoundError(f"Missing expected input file: {name}")
        ordered_paths.append(input_paths[name])
    return ordered_paths


def extract_puzzle_metrics(file_path):
    """
    Trích xuất các chỉ số của puzzle:
    - N              : kích thước bảng NxN
    - clues          : số ô đã cho sẵn
    - empty_cells    : số ô cần điền (N² − clues)
    - constraints_h  : số ràng buộc ngang (LessH + GreaterH)
    - constraints_v  : số ràng buộc dọc  (LessV + GreaterV)
    - total_constraints
    """
    loaded = generate_ground_kb_from_file(file_path)
    if loaded is None:
        raise ValueError(f"Cannot parse: {file_path}")

    kb, assignment = loaded
    N = kb.N
    clues = len(assignment)
    empty_cells = N * N - clues

    facts = kb.facts
    constraints_h = len(facts["LessH"]) + len(facts["GreaterH"])
    constraints_v = len(facts["LessV"]) + len(facts["GreaterV"])
    total_constraints = constraints_h + constraints_v

    return {
        "N": N,
        "clues": clues,
        "empty_cells": empty_cells,
        "constraints_h": constraints_h,
        "constraints_v": constraints_v,
        "total_constraints": total_constraints,
    }


# ============================================================
# CORE ESTIMATION ENGINE
# ============================================================

def _interp_anchor_time(algo: str, N: int) -> float:
    """
    Nội/ngoại suy thời gian kỳ vọng theo N từ bảng _ANCHORS.
    Dùng log-linear interpolation (tuyến tính trong log-space).

    Ưu điểm so với công thức lý thuyết:
    - Không bùng nổ số học
    - Phản ánh đúng tốc độ tăng từ dữ liệu thực nghiệm (kể timeout)
    - Extrapolation log-linear giữ đúng xu hướng tăng
    """
    anchors = _ANCHORS[algo]
    sizes = sorted(anchors.keys())

    if N <= sizes[0]:
        n1, n2 = sizes[0], sizes[1]
        k = (math.log(anchors[n2]) - math.log(anchors[n1])) / (n2 - n1)
        return anchors[n1] * math.exp(k * (N - n1))

    if N >= sizes[-1]:
        n1, n2 = sizes[-2], sizes[-1]
        k = (math.log(anchors[n2]) - math.log(anchors[n1])) / (n2 - n1)
        return anchors[n2] * math.exp(k * (N - n2))

    for i in range(len(sizes) - 1):
        if sizes[i] <= N <= sizes[i + 1]:
            n1, n2 = sizes[i], sizes[i + 1]
            t1, t2 = anchors[n1], anchors[n2]
            alpha = (N - n1) / (n2 - n1)
            return math.exp((1 - alpha) * math.log(t1) + alpha * math.log(t2))

    return anchors[sizes[-1]]


def _density_correction(algo: str, N: int, empty: int, constraints: int) -> float:
    """
    Hệ số điều chỉnh theo đặc trưng riêng của puzzle.

    So sánh puzzle này với puzzle "trung bình" trong thực nghiệm:
    - Nhiều ô trống hơn → khó hơn → correction > 1
    - Nhiều ràng buộc hơn → pruning tốt hơn → correction < 1
    """
    ref_sizes = sorted(_EMPTY_REF.keys())
    closest = min(ref_sizes, key=lambda s: abs(s - N))
    empty_ref = _EMPTY_REF[closest]

    actual_empty_ratio = empty / (N * N)
    actual_c_density   = constraints / (N * N) if constraints > 0 else _CONSTRAINT_REF

    e_sens = _EMPTY_SENSITIVITY[algo]
    c_sens = _CONSTRAINT_SENSITIVITY[algo]

    e_factor = max(0.1, min(10.0, actual_empty_ratio / empty_ref)) ** e_sens
    c_factor = max(0.3, min(5.0, actual_c_density / _CONSTRAINT_REF)) ** c_sens

    return max(_CORRECTION_MIN, min(_CORRECTION_MAX, e_factor * c_factor))


def _estimate(algo: str, metrics: dict) -> float:
    """
    Ước lượng thời gian kỳ vọng (giây) = T_anchor(N) × correction(puzzle).

    T_anchor phản ánh thời gian thực nghiệm ĐÃ TÍNH timeout:
      E[T] = sr × mean_success + (1−sr) × T_timeout
    correction điều chỉnh theo mật độ ô trống / ràng buộc của puzzle cụ thể.
    """
    N = metrics["N"]
    empty = metrics["empty_cells"]
    constraints = metrics["total_constraints"]

    if empty == 0:
        return 0.001  # bảng đã đầy, chỉ cần verify

    t_anchor   = _interp_anchor_time(algo, N)
    correction = _density_correction(algo, N, empty, constraints)
    return t_anchor * correction


# ============================================================
# PUBLIC ESTIMATOR FUNCTIONS (một hàm riêng cho từng thuật toán
# để docstring giải thích rõ đặc điểm complexity)
# ============================================================

def estimate_brute_force(metrics):
    """
    Brute Force: duyệt tuần tự (0,0)→(N-1,N-1) với _is_valid() pruning.

    Complexity thực tế: gần O(N^empty) với pruning không ổn định.
    - 4x4, 5x5: đủ nhanh (<0.13s) nhờ pruning hiệu quả trên puzzle nhỏ.
    - 6x6: success=1.0, mean=21.76s.
    - 7x7: success=0.7 → E[T]=36.4s (kể 30% timeout).
    - 9x9: success=0.0 → tất cả timeout (>120s), không thể hoàn thành.
    """
    return _estimate("brute_force", metrics)


def estimate_backtracking(metrics):
    """
    Backtracking + MRV: _select_mrv() O(N²) mỗi recursion level.

    MRV giảm branching factor nhưng không tránh được worst-case exponential.
    - 4x4, 5x5: nhanh (<0.13s).
    - 6x6: success=0.7 → E[T]=42.2s (kể 30% timeout).
    - 7x7: sample test set bias (success=1.0, mean=3.93s) nhưng anchor
            điều chỉnh lên 63.3s để phản ánh behavior thực khi gặp puzzle khó.
    - 9x9: success=0.0 → tất cả timeout.
    """
    return _estimate("backtracking", metrics)


def estimate_forward_chaining(metrics):
    """
    Forward Chaining: constraint propagation + naked pairs/triples + pointing pairs.

    Mạnh nhất trong nhóm — có thể giải nhiều puzzle chỉ bằng inference.
    Có backtrack tích hợp khi propagation không đủ.
    - Tất cả kích thước (4→9): success=1.0.
    - Tăng đều: 0.13s → 0.17s → 0.47s → 0.76s → 2.54s.
    """
    return _estimate("forward_chaining", metrics)


def estimate_backward_chaining(metrics):
    """
    Backward Chaining (SLD Resolution): prove() đệ quy qua KB.

    Goals tăng theo N² × số ràng buộc → rất tốn kém ở puzzle lớn.
    - 4x4, 5x5: success=1.0, nhưng đã chậm hơn các algo khác.
    - 6x6: success=0.7 → E[T]=48.7s.
    - 7x7: success=0.3 → E[T]=85.4s (70% timeout).
    - 9x9: success=0.0 → tất cả timeout.
    """
    return _estimate("backward_chaining", metrics)


def estimate_a_star(metrics):
    """
    A* + AC-3 Heuristic: heap-based search với AC-3 constraint propagation.

    AC-3 (O(N^4)) pruning rất mạnh → ít nodes cần expand (96 nodes ở 7x7, 477 ở 9x9).
    - Tất cả kích thước: success=1.0.
    - 9x9: 39.13s do AC-3 overhead tăng mạnh theo N.
    """
    return _estimate("a_star", metrics)


# ============================================================
# CSV OUTPUT
# ============================================================

def write_csv(output_path, rows, fieldnames):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def format_time_estimate(seconds):
    """Format thời gian ước lượng thành chuỗi dễ đọc."""
    if seconds < 1e-6:
        return f"{seconds * 1e9:.2f}ns"
    elif seconds < 1e-3:
        return f"{seconds * 1e6:.2f}µs"
    elif seconds < 1:
        return f"{seconds * 1e3:.2f}ms"
    elif seconds < 3600:
        return f"{seconds:.2f}s"
    elif seconds < 86400:
        return f"{seconds / 3600:.2f}h"
    else:
        return f"{seconds / 86400:.2f}d"


# ============================================================
# MAIN
# ============================================================

def main():
    args = parse_args()
    input_paths = collect_input_paths(args.inputs)

    output_path = args.output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    estimators = {
        "brute_force":       estimate_brute_force,
        "backtracking":      estimate_backtracking,
        "forward_chaining":  estimate_forward_chaining,
        "backward_chaining": estimate_backward_chaining,
        "a_star":            estimate_a_star,
    }

    rows = []
    for algo_name in ALGORITHMS:
        print(f"\nEstimating runtime for: {algo_name}")
        row = {"algorithm": algo_name}
        estimator = estimators[algo_name]

        for idx, input_path in enumerate(input_paths):
            try:
                metrics = extract_puzzle_metrics(input_path)
                time_est = estimator(metrics)
                time_str = format_time_estimate(time_est)
                row[f"input{idx + 1}"] = time_str

                print(
                    f"  {os.path.basename(input_path)}: "
                    f"N={metrics['N']}, "
                    f"empty={metrics['empty_cells']}, "
                    f"constraints={metrics['total_constraints']}, "
                    f"est={time_str}"
                )
            except Exception as e:
                print(f"  {os.path.basename(input_path)}: ERROR - {e}")
                row[f"input{idx + 1}"] = "ERROR"

        rows.append(row)

    write_csv(output_path, rows, ["algorithm"] + CSV_HEADERS)
    print(f"\n✓ Saved estimated runtime CSV to: {output_path}")


if __name__ == "__main__":
    main()