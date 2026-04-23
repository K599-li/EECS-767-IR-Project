"""
Step 2: Clean raw data and convert to Pyserini-compatible JSON format.
Each document: {"id": "...", "contents": "title + body"}
Outputs: data/pre/ and data/post/ directories ready for indexing.
"""

import json
import os
import re

BASE_DIR = os.path.dirname(__file__)
RAW_DIR  = os.path.join(BASE_DIR, "data", "raw")
DATA_DIR = os.path.join(BASE_DIR, "data")


def clean_text(text: str) -> str:
    if not text:
        return ""
    # Remove URLs
    text = re.sub(r"http\S+", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def process_period(period: str):
    in_path  = os.path.join(RAW_DIR, f"corpus_{period}.jsonl")
    out_dir  = os.path.join(DATA_DIR, period)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"corpus_{period}.json")  # Pyserini wants .json

    docs = []
    skipped = 0

    with open(in_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)

            title = clean_text(raw.get("title", ""))
            body  = clean_text(raw.get("selftext", ""))

            # Skip if body is deleted/removed (already filtered but double-check)
            if body in ("[deleted]", "[removed]"):
                body = ""

            contents = (title + " " + body).strip()
            if not contents or len(contents) < 10:
                skipped += 1
                continue

            # Pyserini format: must have "id" and "contents"
            doc = {
                "id": raw["id"],
                "contents": contents,
                # Keep metadata for later analysis
                "subreddit":    raw.get("subreddit", ""),
                "created_utc":  raw.get("created_utc", 0),
                "score":        raw.get("score", 0),
                "url":          raw.get("url", ""),
                "num_comments": raw.get("num_comments", 0),
                "title":        title,
                "selftext":     body,
            }
            docs.append(doc)

    # Write as a JSON array (Pyserini JsonCollection)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

    print(f"[{period}] {len(docs)} documents written to {out_path}  (skipped {skipped})")
    return docs


def main():
    for period in ["pre", "post"]:
        process_period(period)


if __name__ == "__main__":
    main()
