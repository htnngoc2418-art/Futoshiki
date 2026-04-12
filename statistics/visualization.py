import os, warnings
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
})
warnings.filterwarnings("ignore")

_HERE      = os.path.dirname(os.path.abspath(__file__))
HARD_CSV   = os.path.join(_HERE, "results_hard_testcases.csv")
HYBRID_CSV = os.path.join(_HERE, "results_hybrid_algo.csv")
OUT_DIR    = os.path.join(_HERE, "charts")
TIMEOUT    = 120.0

SIZE_ORDER = ["4x4", "5x5", "6x6", "7x7", "9x9"]
COLORS = {
    "brute_force":       "#e74c3c",
    "backtracking":      "#3498db",
    "forward_chaining":  "#2ecc71",
    "backward_chaining": "#f39c12",
    "a_star":            "#9b59b6",
}
LABELS = {
    "brute_force":       "Brute Force",
    "backtracking":      "Backtracking",
    "forward_chaining":  "Forward Chaining",
    "backward_chaining": "Backward Chaining",
    "a_star":            "A*",
}
ALGO_ORDER = list(COLORS.keys())


# ── Load ───────────────────────────────────────────────────────────────────────

def load(path, timeout_fill=False):
    """
    Đọc CSV.
    timeout_fill=True  → 0.0 ở mean_time thay bằng TIMEOUT (dùng cho hard bar chart)
    timeout_fill=False → 0.0 ở các cột số thay bằng NaN (bỏ qua khi vẽ)
    """
    df = pd.read_csv(path)
    num_cols = [c for c in df.select_dtypes(include="number").columns]

    if timeout_fill:
        # Chỉ mean_time được fill = TIMEOUT; các cột khác vẫn NaN
        other_cols = [c for c in num_cols if c != "mean_time"]
        df[other_cols] = df[other_cols].replace(0.0, np.nan)
        df["mean_time"] = df["mean_time"].replace(0.0, TIMEOUT)
    else:
        df[num_cols] = df[num_cols].replace(0.0, np.nan)

    df["size"] = pd.Categorical(df["size"], categories=SIZE_ORDER, ordered=True)
    return df


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_series(df, algo, col, fill_null=np.nan):
    sub = df[df["algorithm"] == algo].set_index("size")
    sizes, vals, errs, is_timeout = [], [], [], []
    err_col = col.replace("mean_", "std_")
    for s in SIZE_ORDER:
        if s not in sub.index:
            continue
        v = sub.loc[s, col]
        original_null = pd.isna(v)
        if original_null and pd.isna(fill_null):
            continue  # bỏ qua hoàn toàn
        actual_v = fill_null if original_null else v
        sizes.append(s)
        vals.append(actual_v)
        is_timeout.append(original_null)
        e = sub.loc[s, err_col] if err_col in sub.columns and not original_null else 0
        errs.append(0 if pd.isna(e) else e)
    return sizes, vals, errs, is_timeout


def save_fig(fig, fname, plotted_algos, timeout_note=False):
    patches = [mpatches.Patch(color=COLORS[a], label=LABELS[a]) for a in plotted_algos]
    if timeout_note:
        patches.append(mpatches.Patch(facecolor="grey", alpha=0.3,
                                      edgecolor="grey", label=f"Timeout (≥{TIMEOUT:.0f}s)"))
    fig.legend(handles=patches, loc="lower center", ncol=len(patches),
               fontsize=9, bbox_to_anchor=(0.5, -0.10), frameon=False)
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, fname)
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out}")

def make_hard_time_bar(df, fname):
    sizes  = [s for s in SIZE_ORDER if s in df["size"].values]
    algos  = [a for a in ALGO_ORDER if a in df["algorithm"].values]
    n      = len(algos)
    x      = np.arange(len(sizes))
    width  = 0.8 / n

    fig, ax = plt.subplots(figsize=(9, 4.5))
    fig.suptitle("Thời gian chạy trung bình — Test khó (4×4 → 7×7)",
                 fontsize=12, fontweight="bold", y=1.01)

    has_timeout = False
    for i, algo in enumerate(algos):
        sub = df[df["algorithm"] == algo].set_index("size")
        for j, s in enumerate(sizes):
            if s not in sub.index:
                continue
            v = sub.loc[s, "mean_time"]
            is_tle = (v >= TIMEOUT)
            color  = COLORS[algo]
            alpha  = 0.3 if is_tle else 0.85
            offset = (i - n / 2 + 0.5) * width
            bar = ax.bar(x[j] + offset, v, width * 0.88,
                         color=color, alpha=alpha, zorder=3)
            if is_tle:
                has_timeout = True
                ax.text(x[j] + offset, v + 1.5, "TLE",
                        ha="center", va="bottom", fontsize=7,
                        color=color, fontweight="bold")
            else:
                std = sub.loc[s, "std_time"] if "std_time" in sub.columns else 0
                if not pd.isna(std):
                    ax.errorbar(x[j] + offset, v, yerr=std,
                                fmt="none", color="black", capsize=3, elinewidth=1, zorder=4)

    ax.set_xticks(x)
    ax.set_xticklabels(sizes)
    ax.set_xlabel("Kích thước bảng", fontsize=10)
    ax.set_ylabel("Thời gian (giây)", fontsize=10)
    ax.axhline(TIMEOUT, color="red", linewidth=0.8, linestyle=":", alpha=0.5,
               label=f"Giới hạn {TIMEOUT:.0f}s")

    save_fig(fig, fname, algos, timeout_note=has_timeout)

def make_hybrid_time_line(df, fname):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.suptitle("Thời gian chạy trung bình(4×4 → 9×9)",
                 fontsize=12, fontweight="bold", y=1.01)

    plotted = []
    for algo in ALGO_ORDER:
        sizes, vals, errs, _ = get_series(df, algo, "mean_time")
        if not vals:
            continue
        ax.errorbar(sizes, vals, yerr=errs, marker="o", color=COLORS[algo],
                    linewidth=2, markersize=5, capsize=3, elinewidth=1)
        plotted.append(algo)

    ax.set_xlabel("Kích thước bảng", fontsize=10)
    ax.set_ylabel("Thời gian (giây)", fontsize=10)
    ax.tick_params(axis="both", labelsize=9)
    save_fig(fig, fname, plotted)

def draw_line_subplot(ax, df, col, ylabel, title, use_log=False):
    plotted = []
    for algo in ALGO_ORDER:
        sizes, vals, errs, _ = get_series(df, algo, col)
        if not vals:
            continue
        ax.errorbar(sizes, vals, yerr=errs, marker="o", color=COLORS[algo],
                    linewidth=2, markersize=5, capsize=3, elinewidth=1)
        plotted.append(algo)
    if use_log:
        ax.set_yscale("log")
        ylabel += " (log scale)"
    ax.set_title(title, fontsize=10, fontweight="bold", pad=6)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_xlabel("Kích thước bảng", fontsize=9)
    ax.tick_params(axis="both", labelsize=8)
    return plotted

def make_mem_exp_figure(df, suptitle, fname):
    """2 subplot ngang: bộ nhớ (trái) + số suy luận (phải)."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    fig.suptitle(suptitle, fontsize=12, fontweight="bold", y=1.01)

    p1 = draw_line_subplot(axes[0], df, "mean_memory",
                           "Bộ nhớ đỉnh (KB)", "Bộ nhớ sử dụng trung bình")
    valid = df["mean_expansions_inferences"].dropna()
    use_log = (not valid.empty) and (valid.max() / (valid.min() + 1e-9) > 100)
    p2 = draw_line_subplot(axes[1], df, "mean_expansions_inferences",
                           "Số suy luận / node mở rộng",
                           "Số lần suy luận / mở rộng node", use_log)

    all_algos = sorted(set(p1 + p2), key=lambda a: ALGO_ORDER.index(a))
    save_fig(fig, fname, all_algos)

def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("Đọc dữ liệu...")
    hard_bar  = load(HARD_CSV, timeout_fill=True)   # mean_time 0.0 → 120s
    hard_line = load(HARD_CSV, timeout_fill=False)   # 0.0 → NaN (mem/exp)
    hybrid    = load(HYBRID_CSV, timeout_fill=False)

    print("\nXuất biểu đồ...")
    make_hard_time_bar   (hard_bar,  "hard_time.png")
    make_hybrid_time_line(hybrid,    "hybrid_time.png")
    make_mem_exp_figure  (hard_line, "Bộ nhớ & Số suy luận — Test khó (4×4 → 7×7)", "hard_mem_exp.png")
    make_mem_exp_figure  (hybrid,    "Bộ nhớ & Số suy luận (4×4 → 9×9)",    "hybrid_mem_exp.png")
    print("\nHoàn tất!")

if __name__ == "__main__":
    main()