"""
Step 4: BM25 retrieval using Pyserini.
Retrieves top-10 results for each query from both pre and post corpora.
Outputs: results/results_pre.tsv and results/results_post.tsv
Format: qid  rank  docid  score

Run AFTER indexing (see README_index.txt for indexing commands).
"""

import os
import csv

try:
    from pyserini.search.lucene import LuceneSearcher
except ImportError:
    print("ERROR: Pyserini not installed. See README_index.txt for setup instructions.")
    raise

BASE_DIR    = os.path.dirname(__file__)
INDEX_DIR   = os.path.join(BASE_DIR, "indexes")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

QUERIES_FILE = os.path.join(BASE_DIR, "queries.tsv")
TOP_K = 10


def load_queries(path):
    queries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                qid, text = line.split("\t", 1)
                queries.append((qid, text))
    return queries


def retrieve(searcher, queries, out_path, period):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["qid", "rank", "docid", "score"])
        for qid, query in queries:
            hits = searcher.search(query, k=TOP_K)
            for rank, hit in enumerate(hits, start=1):
                writer.writerow([qid, rank, hit.docid, f"{hit.score:.4f}"])
            print(f"  [{period}] {qid}: {len(hits)} hits")
    print(f"Saved to {out_path}")


def main():
    queries = load_queries(QUERIES_FILE)
    print(f"Loaded {len(queries)} queries.")

    for period in ["pre", "post"]:
        index_path = os.path.join(INDEX_DIR, period)
        out_path   = os.path.join(RESULTS_DIR, f"results_{period}.tsv")

        print(f"\nSearching [{period}] corpus...")
        searcher = LuceneSearcher(index_path)
        # Use BM25 with default parameters (k1=0.9, b=0.4 are Pyserini defaults)
        searcher.set_bm25(k1=0.9, b=0.4)
        retrieve(searcher, queries, out_path, period)


if __name__ == "__main__":
    main()
