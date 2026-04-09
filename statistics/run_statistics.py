import argparse
import csv
import glob
import multiprocessing
import os
import sys
import time
import tracemalloc
from statistics import mean, stdev

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from knowledge_base import generate_ground_kb_from_file
from algorithms.brute_force import FutoshikiSolver as BruteForceSolver
from algorithms.backtracking import FutoshikiSolver as BacktrackingSolver
from algorithms.forward_chaining import FutoshikiSolver as ForwardChainingSolver
from algorithms.backward_chaining import FutoshikiSolver as BackwardChainingSolver
from algorithms.a_star import FutoshikiSolver as AStarSolver

ALGORITHMS = {
    "brute_force": (BruteForceSolver, "brute_force"),
    "backtracking": (BacktrackingSolver, "backtracking"),
    "forward_chaining": (ForwardChainingSolver, "solve"),
    "backward_chaining": (BackwardChainingSolver, "backward_chaining"),
    "a_star": (AStarSolver, "solve"),
}

TIME_LIMIT = 120.0
SMALL_INPUTS = [
    ("4x4", ["input-01.txt", "input-02.txt", "input-03.txt", "input-11.txt"]),
    ("5x5", ["input-04.txt", "input-05.txt", "input-12.txt"]),
]
BIG_INPUTS = [
    ("6x6", ["input-06.txt", "input-07.txt", "input-13.txt"]),
    ("7x7", ["input-08.txt", "input-09.txt", "input-15.txt"]),
    ("9x9", ["input-10.txt"]),
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run Futoshiki algorithms on input files and export timing statistics to CSV."
    )
    parser.add_argument(
        "--inputs",
        default=os.path.join(ROOT_DIR, "Inputs"),
        help="Input folder containing .txt puzzles.",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(ROOT_DIR, "statistics", "results"),
        help="Base output file path or folder.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=20,
        help="Number of repetitions per algorithm + input file.",
    )
    parser.add_argument(
        "--algorithms",
        default=",".join(ALGORITHMS.keys()),
        help="Comma-separated list of algorithm keys to run. Available: %s" % ", ".join(ALGORITHMS.keys()),
    )
    return parser.parse_args()


def collect_input_files(inputs_dir):
    pattern = os.path.join(inputs_dir, "*.txt")
    files = sorted(glob.glob(pattern))
    return files


def _solver_process(queue, solver_cls, method_name, kb, assignment):
    try:
        tracemalloc.start()
        solver = solver_cls(kb, assignment)
        method = getattr(solver, method_name)
        success = bool(method())
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    except Exception:
        success = False
        peak = 0
    counter = 0
    if hasattr(solver, "inferences"):
        counter = getattr(solver, "inferences")
    elif hasattr(solver, "nodes_expanded"):
        counter = getattr(solver, "nodes_expanded")
    elif hasattr(solver, "attempts"):
        counter = getattr(solver, "attempts")
    elif hasattr(solver, "engine") and hasattr(solver.engine, "steps"):
        counter = getattr(solver.engine, "steps")
    queue.put((success, peak, counter))


def run_solver(solver_cls, method_name, file_path, timeout=TIME_LIMIT):
    loaded = generate_ground_kb_from_file(file_path)
    if loaded is None:
        raise FileNotFoundError(f"Unable to parse input file: {file_path}")

    kb, assignment = loaded
    queue = multiprocessing.Queue()
    ctx = multiprocessing.get_context("spawn")
    process = ctx.Process(target=_solver_process, args=(queue, solver_cls, method_name, kb, assignment))
    start = time.perf_counter()
    process.start()
    process.join(timeout)
    elapsed = time.perf_counter() - start
    if process.is_alive():
        process.terminate()
        process.join()
        return False, timeout, 0.0, 0

    try:
        success, peak_memory, counter = queue.get_nowait()
    except Exception:
        success = False
        peak_memory = 0.0
        counter = 0

    return success, min(elapsed, timeout), peak_memory / 1024.0, counter


def aggregate_results(values, successes):
    if not values:
        return None
    stats = {
        "runs": len(values),
        "mean": mean(values),
        "std": stdev(values) if len(values) > 1 else 0.0,
        "best": min(values),
        "worst": max(values),
        "success_rate": sum(1 for s in successes if s) / len(successes) if successes else 0.0,
        "success_count": sum(1 for s in successes if s),
        "failure_count": len(successes) - sum(1 for s in successes if s),
    }
    return stats


def write_csv(output_path, rows, fieldnames):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    args = parse_args()
    selected_names = [name.strip() for name in args.algorithms.split(",") if name.strip()]
    for algo in ["backtracking", "brute_force"]:
        if algo in selected_names:
            selected_names = [name for name in selected_names if name != algo] + [algo]
    missing = [name for name in selected_names if name not in ALGORITHMS]
    if missing:
        raise ValueError(f"Unknown algorithms: {', '.join(missing)}")

    input_files = collect_input_files(args.inputs)
    if not input_files:
        raise FileNotFoundError(f"No input files found in {args.inputs}")

    input_files_by_name = {os.path.basename(path): path for path in input_files}
    grouped_inputs = []
    for group_label, file_names in SMALL_INPUTS + BIG_INPUTS:
        group_paths = [input_files_by_name[name] for name in file_names if name in input_files_by_name]
        if group_paths:
            grouped_inputs.append((group_label, group_paths))

    grouped_results = {group_label: [] for group_label, _ in grouped_inputs}

    for algorithm_name in selected_names:
        solver_cls, method_name = ALGORITHMS[algorithm_name]
        print(f"Running grouped test for {algorithm_name} algorithm...")
        for group_label, group_paths in grouped_inputs:
            runs = 20 if group_label in ["4x4", "5x5"] else 10
            print(f"  Group {group_label}: {', '.join(os.path.basename(p) for p in group_paths)} ({runs} runs)")
            time_values = []
            memory_values = []
            counter_values = []
            successes = []
            for run_i in range(runs):
                input_path = group_paths[run_i % len(group_paths)]
                input_name = os.path.basename(input_path)
                try:
                    success, elapsed, peak_memory, counter = run_solver(solver_cls, method_name, input_path)
                except Exception:
                    success = False
                    elapsed = 0.0
                    peak_memory = 0.0
                    counter = 0
                time_values.append(elapsed)
                memory_values.append(peak_memory)
                counter_values.append(counter)
                successes.append(success)
                print(f"    Run {run_i + 1}/{runs} -> {input_name}: {'OK' if success else 'FAIL'} {elapsed:.6f}s | memory={peak_memory:.6f}KB | count={counter}")

            # Filter values for successful runs only
            success_time_values = [t for t, s in zip(time_values, successes) if s]
            success_memory_values = [m for m, s in zip(memory_values, successes) if s]
            success_counter_values = [c for c, s in zip(counter_values, successes) if s]

            time_stats = aggregate_results(success_time_values, successes)
            memory_stats = aggregate_results(success_memory_values, successes)
            counter_stats = aggregate_results(success_counter_values, successes)
            row = {
                "algorithm": algorithm_name,
                "size": group_label,
                "mean_time": str(time_stats["mean"] if time_stats else 0.0),
                "std_time": str(time_stats["std"] if time_stats else 0.0),
                "best_time": str(time_stats["best"] if time_stats else 0.0),
                "worst_time": str(time_stats["worst"] if time_stats else 0.0),
                "success_rate": "0.00" if time_stats and time_stats["success_count"] == 0 else str(time_stats["success_rate"] if time_stats else 0.0),
                "mean_memory": str(memory_stats["mean"] if memory_stats else 0.0),
                "std_memory": str(memory_stats["std"] if memory_stats else 0.0),
                "mean_expansions_inferences": str(counter_stats["mean"] if counter_stats else 0.0),
                "std_expansions_inferences": str(counter_stats["std"] if counter_stats else 0.0),
            }
            grouped_results[group_label].append(row)

    output_folder = args.output
    if os.path.isdir(output_folder):
        output_dir = output_folder
    else:
        output_dir = os.path.dirname(output_folder) or ROOT_DIR

    os.makedirs(output_dir, exist_ok=True)

    for group_label, rows in grouped_results.items():
        output_path = os.path.join(output_dir, f"{group_label}.csv")
        write_csv(output_path, rows, [
            "algorithm",
            "size",
            "mean_time",
            "std_time",
            "best_time",
            "worst_time",
            "mean_memory",
            "std_memory",
            "mean_expansions_inferences",
            "std_expansions_inferences",
            "success_rate",
        ])
        print(f"Saved results for {group_label} to: {output_path}")


if __name__ == "__main__":
    main()
