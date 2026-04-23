"""
Step 7: Visualizations for the report.

Figures:
  1. Stacked bar chart: category exposure distribution pre vs post (per k)
  2. JSD heatmap: query × k
  3. Overlap@k line chart
  4. Entropy distribution pre vs post (boxplot)
"""

import os
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless on Windows
import matplotlib.pyplot as plt
import matplotlib.cm as cm

BASE_DIR     = os.path.dirname(__file__)
ANALYSIS_DIR = os.path.join(BASE_DIR, "analysis")
FIGURES_DIR  = os.path.join(BASE_DIR, "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

ALL_CATS = ["News/External", "Question/Help", "Personal", "Technical"]
K_VALUES = [3, 5, 10]
COLORS   = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]


def load_metrics():
    rows = []
    path = os.path.join(ANALYSIS_DIR, "metrics_summary.csv")
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def fig1_exposure_bars(rows):
    """Stacked bar: average category distribution pre vs post, for each k."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Average Category Exposure Distribution: Pre vs Post ChatGPT Release",
                 fontsize=13, fontweight="bold")

    for ax, k in zip(axes, K_VALUES):
        k_rows = [r for r in rows if int(r["k"]) == k]

        # Compute mean exposure per category from exp_diff
        # We need absolute values; compute from exp_diff and assume post = pre + diff
        # Since we only have diffs, let's reconstruct from the data
        # exp_diff = post - pre  => we need a baseline
        # Workaround: use entropy_pre/post as proxies, but better to recompute here
        # For now, show the difference as a diverging bar
        cats_labels = [c.replace("/", "/\n") for c in ALL_CATS]
        diffs = []
        for cat in ALL_CATS:
            key = f"exp_diff_{cat.replace('/', '_')}"
            vals = [float(r[key]) for r in k_rows if key in r]
            diffs.append(np.mean(vals) if vals else 0)

        bar_colors = [COLORS[i] for i in range(len(ALL_CATS))]
        bars = ax.bar(cats_labels, diffs, color=bar_colors, edgecolor="white")
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax.set_title(f"k = {k}", fontsize=11)
        ax.set_ylabel("Mean Exposure Difference (Post − Pre)")
        ax.set_ylim(-0.5, 0.5)
        ax.tick_params(axis="x", labelsize=8)

        # Annotate bars
        for bar, diff in zip(bars, diffs):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.01 * np.sign(diff),
                    f"{diff:+.3f}", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    out = os.path.join(FIGURES_DIR, "fig1_exposure_bars.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def fig2_jsd_heatmap(rows):
    """Heatmap: JSD values per query × k."""
    qids = sorted(set(r["qid"] for r in rows))
    data = np.zeros((len(qids), len(K_VALUES)))
    qid_idx = {q: i for i, q in enumerate(qids)}

    for r in rows:
        i = qid_idx[r["qid"]]
        j = K_VALUES.index(int(r["k"]))
        data[i, j] = float(r["jsd"])

    fig, ax = plt.subplots(figsize=(6, 10))
    im = ax.imshow(data, cmap="YlOrRd", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(K_VALUES)))
    ax.set_xticklabels([f"k={k}" for k in K_VALUES])
    ax.set_yticks(range(len(qids)))
    ax.set_yticklabels(qids, fontsize=8)
    ax.set_title("Jensen-Shannon Divergence (Pre vs Post)\nper Query × k", fontweight="bold")
    plt.colorbar(im, ax=ax, label="JSD")

    # Annotate cells
    for i in range(len(qids)):
        for j in range(len(K_VALUES)):
            ax.text(j, i, f"{data[i,j]:.2f}", ha="center", va="center", fontsize=7)

    plt.tight_layout()
    out = os.path.join(FIGURES_DIR, "fig2_jsd_heatmap.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def fig3_overlap(rows):
    """Line chart: mean Overlap@k across k values."""
    means = []
    stds  = []
    for k in K_VALUES:
        vals = [float(r["overlap"]) for r in rows if int(r["k"]) == k]
        means.append(np.mean(vals))
        stds.append(np.std(vals))

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.errorbar(K_VALUES, means, yerr=stds, marker="o", color="#4C72B0",
                capsize=5, linewidth=2, markersize=8)
    ax.set_xlabel("k")
    ax.set_ylabel("Mean Jaccard Overlap@k")
    ax.set_title("Document Overlap Between Pre and Post Corpora", fontweight="bold")
    ax.set_xticks(K_VALUES)
    ax.set_ylim(0, 1)
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    out = os.path.join(FIGURES_DIR, "fig3_overlap.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def fig4_entropy_boxplot(rows):
    """Boxplot: entropy distribution pre vs post for each k."""
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    fig.suptitle("Entropy of Top-k Category Distribution: Pre vs Post", fontweight="bold")

    for ax, k in zip(axes, K_VALUES):
        k_rows = [r for r in rows if int(r["k"]) == k]
        ent_pre  = [float(r["entropy_pre"])  for r in k_rows]
        ent_post = [float(r["entropy_post"]) for r in k_rows]
        ax.boxplot([ent_pre, ent_post], labels=["Pre", "Post"],
                   patch_artist=True,
                   boxprops=dict(facecolor="#AEC6E8"),
                   medianprops=dict(color="red", linewidth=2))
        ax.set_title(f"k = {k}")
        ax.set_ylabel("Entropy (bits)")
        ax.set_ylim(0, 2.2)

    plt.tight_layout()
    out = os.path.join(FIGURES_DIR, "fig4_entropy.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def main():
    rows = load_metrics()
    print(f"Loaded {len(rows)} metric rows.")
    fig1_exposure_bars(rows)
    fig2_jsd_heatmap(rows)
    fig3_overlap(rows)
    fig4_entropy_boxplot(rows)
    print("\nAll figures saved to:", FIGURES_DIR)


if __name__ == "__main__":
    main()
