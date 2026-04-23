"""
Step 6: Compute exposure metrics for each query at k=3, 5, 10.

Metrics:
  - Exposure@k difference (per category)
  - Jensen-Shannon Divergence of top-k category distributions
  - Overlap@k (Jaccard similarity of top-k doc sets)
  - Entropy of top-k category distribution

Outputs:
  analysis/metrics_summary.csv   — per-query per-k metrics
  analysis/stats.txt             — paired t-test + bootstrap CI results
"""

import json
import os
import csv
import math
import numpy as np
from scipy.stats import ttest_1samp
from scipy.spatial.distance import jensenshannon

BASE_DIR     = os.path.dirname(__file__)
RESULTS_DIR  = os.path.join(BASE_DIR, "results")
DATA_DIR     = os.path.join(BASE_DIR, "data")
ANALYSIS_DIR = os.path.join(BASE_DIR, "analysis")
os.makedirs(ANALYSIS_DIR, exist_ok=True)

ALL_CATS = ["News/External", "Question/Help", "Personal", "Technical"]
K_VALUES = [3, 5, 10]


def load_results(period):
    """Returns dict: {qid: [(rank, docid, score), ...]}"""
    path = os.path.join(RESULTS_DIR, f"results_{period}.tsv")
    results = {}
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            qid = row["qid"]
            if qid not in results:
                results[qid] = []
            results[qid].append((int(row["rank"]), row["docid"], float(row["score"])))
    # Sort by rank
    for qid in results:
        results[qid].sort(key=lambda x: x[0])
    return results


def load_categories():
    path = os.path.join(DATA_DIR, "categories.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def category_dist(docids, categories):
    """Return normalized category distribution dict over given docids."""
    counts = {c: 0 for c in ALL_CATS}
    for did in docids:
        cat = categories.get(did, "Technical")
        counts[cat] = counts.get(cat, 0) + 1
    n = len(docids)
    if n == 0:
        return {c: 0.0 for c in ALL_CATS}
    return {c: counts[c] / n for c in ALL_CATS}


def jsd(p_dict, q_dict):
    p = np.array([p_dict[c] for c in ALL_CATS])
    q = np.array([q_dict[c] for c in ALL_CATS])
    # Add small epsilon to avoid log(0)
    p = p + 1e-9
    q = q + 1e-9
    p /= p.sum()
    q /= q.sum()
    return float(jensenshannon(p, q) ** 2)


def entropy(dist_dict):
    vals = np.array([dist_dict[c] for c in ALL_CATS])
    vals = vals[vals > 0]
    return float(-np.sum(vals * np.log2(vals))) if len(vals) > 0 else 0.0


def jaccard(set_a, set_b):
    if not set_a and not set_b:
        return 1.0
    return len(set_a & set_b) / len(set_a | set_b)


def bootstrap_ci(diffs, n_boot=2000, ci=0.95):
    diffs = np.array(diffs)
    boot_means = [np.mean(np.random.choice(diffs, size=len(diffs), replace=True))
                  for _ in range(n_boot)]
    lo = np.percentile(boot_means, (1 - ci) / 2 * 100)
    hi = np.percentile(boot_means, (1 + ci) / 2 * 100)
    return float(np.mean(diffs)), lo, hi


def main():
    results_pre  = load_results("pre")
    results_post = load_results("post")
    categories   = load_categories()

    all_qids = sorted(set(results_pre.keys()) | set(results_post.keys()))
    print(f"Queries: {len(all_qids)}")

    rows = []  # for CSV output
    # Collect JSD diffs per k for statistical testing
    jsd_diffs   = {k: [] for k in K_VALUES}
    entropy_pre  = {k: [] for k in K_VALUES}
    entropy_post = {k: [] for k in K_VALUES}

    for qid in all_qids:
        hits_pre  = results_pre.get(qid, [])
        hits_post = results_post.get(qid, [])

        for k in K_VALUES:
            docs_pre  = [h[1] for h in hits_pre[:k]]
            docs_post = [h[1] for h in hits_post[:k]]

            dist_pre  = category_dist(docs_pre,  categories)
            dist_post = category_dist(docs_post, categories)

            jsd_val     = jsd(dist_pre, dist_post)
            overlap_val = jaccard(set(docs_pre), set(docs_post))
            ent_pre     = entropy(dist_pre)
            ent_post    = entropy(dist_post)
            ent_diff    = ent_post - ent_pre

            # Exposure@k per category
            exp_diffs = {c: dist_post[c] - dist_pre[c] for c in ALL_CATS}

            row = {
                "qid": qid,
                "k": k,
                "jsd": round(jsd_val, 4),
                "overlap": round(overlap_val, 4),
                "entropy_pre":  round(ent_pre,  4),
                "entropy_post": round(ent_post, 4),
                "entropy_diff": round(ent_diff, 4),
            }
            for c in ALL_CATS:
                row[f"exp_diff_{c.replace('/','_')}"] = round(exp_diffs[c], 4)

            rows.append(row)
            jsd_diffs[k].append(jsd_val)
            entropy_pre[k].append(ent_pre)
            entropy_post[k].append(ent_post)

    # Write CSV
    csv_path = os.path.join(ANALYSIS_DIR, "metrics_summary.csv")
    fieldnames = list(rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Metrics saved to {csv_path}")

    # Statistical tests
    stats_path = os.path.join(ANALYSIS_DIR, "stats.txt")
    with open(stats_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("Statistical Analysis: Exposure Shift Pre vs Post ChatGPT\n")
        f.write("=" * 60 + "\n\n")

        for k in K_VALUES:
            f.write(f"--- k = {k} ---\n")

            # JSD: is it significantly > 0?
            jsds = np.array(jsd_diffs[k])
            t, p = ttest_1samp(jsds, 0)
            mean, lo, hi = bootstrap_ci(jsds)
            f.write(f"JSD@{k}: mean={mean:.4f}, 95% CI=[{lo:.4f}, {hi:.4f}], "
                    f"t={t:.3f}, p={p:.4f}\n")

            # Entropy difference
            ent_diffs = np.array(entropy_post[k]) - np.array(entropy_pre[k])
            t2, p2 = ttest_1samp(ent_diffs, 0)
            mean2, lo2, hi2 = bootstrap_ci(list(ent_diffs))
            f.write(f"Entropy diff@{k}: mean={mean2:.4f}, 95% CI=[{lo2:.4f}, {hi2:.4f}], "
                    f"t={t2:.3f}, p={p2:.4f}\n")
            f.write("\n")

    print(f"Stats saved to {stats_path}")
    # Print to console too
    with open(stats_path) as f:
        print(f.read())


if __name__ == "__main__":
    np.random.seed(42)
    main()
