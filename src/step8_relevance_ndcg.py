"""
Step 8: Relevance subset annotation + nDCG@10 sanity check.

This script is intentionally standalone, so it does not change Steps 1-7.

Usage:
  1) Prepare annotation template:
     python step8_relevance_ndcg.py --prepare

  2) Manually fill the "relevance" column in:
     analysis/relevance/annotation_template.tsv
     Recommended labels: 0 (not relevant), 1 (partly), 2 (highly relevant)

  3) Compute nDCG@10:
     python step8_relevance_ndcg.py --evaluate
"""

import argparse
import csv
import json
import math
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(BASE_DIR, "results")
DATA_DIR = os.path.join(BASE_DIR, "data")
ANALYSIS_DIR = os.path.join(BASE_DIR, "analysis")
RELEVANCE_DIR = os.path.join(ANALYSIS_DIR, "relevance")

QUERIES_FILE = os.path.join(BASE_DIR, "queries.tsv")
RESULTS_PRE = os.path.join(RESULTS_DIR, "results_pre.tsv")
RESULTS_POST = os.path.join(RESULTS_DIR, "results_post.tsv")
CORPUS_PRE = os.path.join(DATA_DIR, "pre", "corpus_pre.json")
CORPUS_POST = os.path.join(DATA_DIR, "post", "corpus_post.json")

ANNOTATION_FILE = os.path.join(RELEVANCE_DIR, "annotation_template.tsv")
SELECTED_QUERIES_FILE = os.path.join(RELEVANCE_DIR, "selected_queries.txt")
NDCG_SUMMARY_CSV = os.path.join(RELEVANCE_DIR, "ndcg_summary.csv")
NDCG_REPORT_TXT = os.path.join(RELEVANCE_DIR, "ndcg_report.txt")

TOP_K = 10
DEFAULT_SUBSET_SIZE = 10
QUERY_GROUP_PREFIXES = ["E", "I", "S"]  # Entity / Issue / Scenario


def load_queries(path):
    queries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            qid, text = line.split("\t", 1)
            queries.append((qid, text))
    return queries


def load_results(path):
    """
    Returns:
      dict[qid] = list of dict rows sorted by rank.
    """
    rows_by_qid = defaultdict(list)
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            row["rank"] = int(row["rank"])
            row["score"] = float(row["score"])
            rows_by_qid[row["qid"]].append(row)

    for qid in rows_by_qid:
        rows_by_qid[qid].sort(key=lambda x: x["rank"])
    return rows_by_qid


def load_corpus(path):
    """
    Returns:
      dict[docid] = {"title": ..., "selftext": ..., "contents": ...}
    """
    with open(path, encoding="utf-8") as f:
        docs = json.load(f)
    out = {}
    for d in docs:
        docid = d.get("id")
        if not docid:
            continue
        out[docid] = {
            "title": (d.get("title") or "").replace("\t", " ").replace("\n", " ").strip(),
            "selftext": (d.get("selftext") or "").replace("\t", " ").replace("\n", " ").strip(),
            "contents": (d.get("contents") or "").replace("\t", " ").replace("\n", " ").strip(),
        }
    return out


def choose_subset_qids(queries, results_pre, results_post, subset_size):
    """
    Deterministic balanced selection across E/I/S query groups.
    Only keep queries that have at least TOP_K hits in both periods.
    """
    eligible = []
    for qid, qtext in queries:
        if len(results_pre.get(qid, [])) >= TOP_K and len(results_post.get(qid, [])) >= TOP_K:
            eligible.append((qid, qtext))

    grouped = {p: [] for p in QUERY_GROUP_PREFIXES}
    extras = []
    for item in eligible:
        qid = item[0]
        prefix = qid[0]
        if prefix in grouped:
            grouped[prefix].append(item)
        else:
            extras.append(item)

    for k in grouped:
        grouped[k].sort(key=lambda x: x[0])
    extras.sort(key=lambda x: x[0])

    # Round-robin among E/I/S to stay close to proposal's three query types.
    selected = []
    while len(selected) < subset_size:
        made_progress = False
        for p in QUERY_GROUP_PREFIXES:
            if grouped[p]:
                selected.append(grouped[p].pop(0))
                made_progress = True
                if len(selected) == subset_size:
                    break
        if not made_progress:
            break

    if len(selected) < subset_size and extras:
        need = subset_size - len(selected)
        selected.extend(extras[:need])

    return selected


def make_snippet(doc, max_len=240):
    snippet = doc.get("selftext") or doc.get("contents") or ""
    if len(snippet) <= max_len:
        return snippet
    return snippet[: max_len - 3] + "..."


def prepare_annotation_file(subset_size):
    os.makedirs(RELEVANCE_DIR, exist_ok=True)

    queries = load_queries(QUERIES_FILE)
    results_pre = load_results(RESULTS_PRE)
    results_post = load_results(RESULTS_POST)
    corpus_pre = load_corpus(CORPUS_PRE)
    corpus_post = load_corpus(CORPUS_POST)

    selected = choose_subset_qids(queries, results_pre, results_post, subset_size)
    if not selected:
        raise RuntimeError("No eligible queries found with >=10 hits in both pre and post.")

    # Save selected qids for reproducibility.
    with open(SELECTED_QUERIES_FILE, "w", encoding="utf-8") as f:
        for qid, qtext in selected:
            f.write(f"{qid}\t{qtext}\n")

    fields = [
        "qid",
        "query",
        "period",
        "rank",
        "docid",
        "score",
        "title",
        "snippet",
        "relevance",  # to be manually filled (0 / 1 / 2)
    ]

    with open(ANNOTATION_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()

        for qid, qtext in selected:
            for period, results, corpus in [
                ("pre", results_pre, corpus_pre),
                ("post", results_post, corpus_post),
            ]:
                for hit in results[qid][:TOP_K]:
                    docid = hit["docid"]
                    doc = corpus.get(docid, {})
                    writer.writerow(
                        {
                            "qid": qid,
                            "query": qtext,
                            "period": period,
                            "rank": hit["rank"],
                            "docid": docid,
                            "score": f"{hit['score']:.4f}",
                            "title": doc.get("title", ""),
                            "snippet": make_snippet(doc),
                            "relevance": "",
                        }
                    )

    print(f"Selected {len(selected)} queries. Saved to: {SELECTED_QUERIES_FILE}")
    print(f"Annotation template saved to: {ANNOTATION_FILE}")
    print("Fill the 'relevance' column manually with 0/1/2, then run --evaluate.")


def dcg_at_k(rels, k=10):
    score = 0.0
    for i, rel in enumerate(rels[:k], start=1):
        score += (2**rel - 1) / math.log2(i + 1)
    return score


def ndcg_at_k(rels, k=10):
    dcg = dcg_at_k(rels, k)
    ideal = sorted(rels, reverse=True)
    idcg = dcg_at_k(ideal, k)
    if idcg == 0:
        return 0.0
    return dcg / idcg


def evaluate_ndcg(annotation_path):
    if not os.path.exists(annotation_path):
        raise FileNotFoundError(
            f"Annotation file not found: {annotation_path}\nRun --prepare first."
        )

    groups = defaultdict(list)  # key: (period, qid), val: list[(rank, rel)]
    missing = []

    with open(annotation_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            qid = row["qid"].strip()
            period = row["period"].strip()
            rank = int(row["rank"])
            rel_raw = row.get("relevance", "").strip()
            if rel_raw == "":
                missing.append((period, qid, rank, row.get("docid", "")))
                continue
            try:
                rel = float(rel_raw)
            except ValueError:
                missing.append((period, qid, rank, row.get("docid", "")))
                continue
            groups[(period, qid)].append((rank, rel))

    if missing:
        print(f"Found {len(missing)} rows with missing/invalid relevance labels.")
        print("Please complete labels before evaluation. Example missing rows:")
        for item in missing[:10]:
            print("  ", item)
        return

    rows = []
    by_period = defaultdict(list)
    for (period, qid), pairs in sorted(groups.items()):
        pairs.sort(key=lambda x: x[0])
        rels = [rel for _, rel in pairs]
        ndcg = ndcg_at_k(rels, k=TOP_K)
        rows.append({"period": period, "qid": qid, f"nDCG@{TOP_K}": round(ndcg, 4)})
        by_period[period].append(ndcg)

    os.makedirs(RELEVANCE_DIR, exist_ok=True)
    with open(NDCG_SUMMARY_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["period", "qid", f"nDCG@{TOP_K}"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with open(NDCG_REPORT_TXT, "w", encoding="utf-8") as f:
        f.write("nDCG@10 sanity check report\n")
        f.write("=" * 40 + "\n\n")
        for period in sorted(by_period):
            vals = by_period[period]
            mean = sum(vals) / len(vals) if vals else 0.0
            f.write(f"{period}: mean nDCG@10 = {mean:.4f} (n={len(vals)} queries)\n")
        f.write("\nPer-query values are in ndcg_summary.csv\n")

    print(f"Saved per-query nDCG to: {NDCG_SUMMARY_CSV}")
    print(f"Saved summary report to: {NDCG_REPORT_TXT}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Step 8: relevance annotation subset and nDCG@10 sanity check."
    )
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="Create annotation template for manual relevance labeling.",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Compute nDCG@10 from filled annotation file.",
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=DEFAULT_SUBSET_SIZE,
        help="Number of queries to include in the annotation subset (default: 10).",
    )
    parser.add_argument(
        "--annotation-file",
        default=ANNOTATION_FILE,
        help="Path to annotation TSV file (default: analysis/relevance/annotation_template.tsv).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    # If no mode is explicitly chosen, run full flow convenience:
    # prepare first, then ask user to annotate before evaluate.
    if not args.prepare and not args.evaluate:
        args.prepare = True

    if args.prepare:
        prepare_annotation_file(args.subset_size)
    if args.evaluate:
        evaluate_ndcg(args.annotation_file)


if __name__ == "__main__":
    main()
