"""
Step 5: Rule-based document categorization into 4 categories:
  1. News/External link
  2. Question/Help-seeking
  3. Personal experience
  4. Technical/Explanatory

Reads pre/post corpus JSON files, assigns a category to each doc.
Outputs: data/categories.json  {docid: category}
"""

import json
import os
import re

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")

# Category labels
CAT_NEWS     = "News/External"
CAT_QUESTION = "Question/Help"
CAT_PERSONAL = "Personal"
CAT_TECH     = "Technical"

# Patterns
URL_RE          = re.compile(r"https?://|www\.", re.I)
QUESTION_RE     = re.compile(
    r"\b(how|why|what|when|where|who|should i|can i|is it|does it|will it)\b|"
    r"\?$", re.I)
PERSONAL_RE     = re.compile(
    r"\b(i tried|i tested|my experience|i found|i used|i built|i made|"
    r"i am|i have|i was|i feel|i think)\b", re.I)
TECHNICAL_RE    = re.compile(
    r"\b(tutorial|guide|how to|step by step|explain|explanation|"
    r"documentation|api|code|implementation|algorithm|model|training|"
    r"fine.?tun|parameter|prompt|token|embed|vector|architecture)\b", re.I)


def categorize(doc: dict) -> str:
    title = doc.get("title", "") or ""
    body  = doc.get("selftext", "") or ""
    url   = doc.get("url", "") or ""
    combined = title + " " + body

    # Priority order: News > Question > Personal > Technical
    if URL_RE.search(url) or URL_RE.search(combined):
        return CAT_NEWS
    if QUESTION_RE.search(combined):
        return CAT_QUESTION
    if PERSONAL_RE.search(combined):
        return CAT_PERSONAL
    if TECHNICAL_RE.search(combined):
        return CAT_TECH
    # Default fallback: assign based on strongest signal
    return CAT_TECH  # most Reddit AI posts are explanatory by nature


def main():
    categories = {}

    for period in ["pre", "post"]:
        corpus_path = os.path.join(DATA_DIR, period, f"corpus_{period}.json")
        if not os.path.exists(corpus_path):
            print(f"Missing: {corpus_path}. Run step2 first.")
            continue

        with open(corpus_path, encoding="utf-8") as f:
            docs = json.load(f)

        counts = {CAT_NEWS: 0, CAT_QUESTION: 0, CAT_PERSONAL: 0, CAT_TECH: 0}
        for doc in docs:
            cat = categorize(doc)
            categories[doc["id"]] = cat
            counts[cat] += 1

        print(f"[{period}] {len(docs)} docs categorized:")
        for cat, cnt in counts.items():
            print(f"  {cat}: {cnt} ({cnt/len(docs)*100:.1f}%)")

    out_path = os.path.join(BASE_DIR, "data", "categories.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(categories)} category labels to {out_path}")


if __name__ == "__main__":
    main()
