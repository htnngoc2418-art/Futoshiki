import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os

# ── 1. Load & merge ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
big   = pd.read_csv(os.path.join(BASE_DIR, "stats_big_board.csv"))
small = pd.read_csv(os.path.join(BASE_DIR, "stats_small_board.csv"))
df    = pd.concat([big, small], ignore_index=True)

size_order = ["4x4", "5x5", "6x6", "7x7", "9x9"]
df["size"] = pd.Categorical(df["size"], categories=size_order, ordered=True)
df = df.sort_values(["size", "algorithm"])

algorithms = df["algorithm"].unique()
sizes      = size_order

COLORS = {
    "a_star":           "#2196F3",
    "backtracking":     "#4CAF50",
    "backward_chaining":"#FF9800",
    "brute_force":      "#F44336",
    "forward_chaining": "#9C27B0",
}

OUTPUT_DIR = os.path.join(BASE_DIR, "charts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def base_fig(title):
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#F7F9FC")
    ax.set_facecolor("#FFFFFF")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    return fig, ax

def save(fig, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved: {path}")

# ── 2. Chart 1: Grouped Bar + Error Bar ──────────────────────────────────────
fig, ax = base_fig("Mean Execution Time ± Std Dev")

x       = np.arange(len(sizes))
n_alg   = len(algorithms)
width   = 0.15
offsets = np.linspace(-(n_alg-1)/2 * width, (n_alg-1)/2 * width, n_alg)

for i, alg in enumerate(algorithms):
    sub = df[df["algorithm"] == alg].set_index("size").reindex(sizes)
    ax.bar(
        x + offsets[i], sub["mean_time"], width,
        yerr=sub["std_time"],
        label=alg.replace("_", " ").title(),
        color=COLORS[alg],
        error_kw=dict(elinewidth=1, capsize=3, ecolor="#555"),
        alpha=0.88,
    )

ax.set_xticks(x)
ax.set_xticklabels(sizes)
ax.set_xlabel("Board Size")
ax.set_ylabel("Time (s)")
ax.legend(fontsize=9, framealpha=0.5)
ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.1f"))
save(fig, "1_mean_time_bar.png")

# ── 3. Chart 2: Line Chart ────────────────────────────────────────────────────
fig, ax = base_fig("Execution Time Trend by Board Size")

for alg in algorithms:
    sub = df[df["algorithm"] == alg].set_index("size").reindex(sizes)
    ax.plot(sizes, sub["mean_time"], marker="o",
            label=alg.replace("_", " ").title(),
            color=COLORS[alg], linewidth=2, markersize=7)
    ax.fill_between(sizes,
        sub["mean_time"] - sub["std_time"],
        sub["mean_time"] + sub["std_time"],
        color=COLORS[alg], alpha=0.12)

ax.set_xlabel("Board Size")
ax.set_ylabel("Time (s)")
ax.set_yscale("symlog", linthresh=1)
ax.yaxis.set_minor_formatter(ticker.NullFormatter())
ax.legend(fontsize=9, framealpha=0.5)
save(fig, "2_time_trend_line.png")

# ── 4. Chart 3: Heatmap — Success Rate ───────────────────────────────────────
fig, ax = base_fig("Success Rate Heatmap")

pivot = df.pivot_table(index="algorithm", columns="size", values="success_rate")[sizes]
pivot.index = [a.replace("_", " ").title() for a in pivot.index]

im = ax.imshow(pivot.values, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(len(sizes)))
ax.set_xticklabels(sizes)
ax.set_yticks(range(len(pivot)))
ax.set_yticklabels(pivot.index, fontsize=10)

for i in range(len(pivot)):
    for j in range(len(sizes)):
        val = pivot.values[i, j]
        txt = f"{val:.0%}" if not np.isnan(val) else "N/A"
        ax.text(j, i, txt, ha="center", va="center",
                fontsize=10, color="black", fontweight="bold")

plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04).set_label("Success Rate")
save(fig, "3_success_rate_heatmap.png")

# ── 5. Chart 4: Scatter — Memory vs Time ─────────────────────────────────────
fig, ax = base_fig("Memory Usage vs. Execution Time")

for alg in algorithms:
    sub = df[df["algorithm"] == alg]
    ax.scatter(sub["mean_time"], sub["mean_memory"],
               c=COLORS[alg], s=90,
               label=alg.replace("_", " ").title(),
               alpha=0.85, edgecolors="white", linewidth=0.5)
    for _, row in sub.iterrows():
        ax.annotate(row["size"], (row["mean_time"], row["mean_memory"]),
                    textcoords="offset points", xytext=(6, 3),
                    fontsize=8, color="#444")

ax.set_xlabel("Mean Time (s)")
ax.set_ylabel("Mean Memory (MB)")
ax.set_xscale("symlog", linthresh=0.5)
ax.legend(fontsize=9, framealpha=0.5)
save(fig, "4_memory_vs_time_scatter.png")

print("\nDone! 4 charts saved to:", OUTPUT_DIR)