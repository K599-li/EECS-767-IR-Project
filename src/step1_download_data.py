"""
Step 1: Download Reddit posts from Arctic Shift API
Covers 8 weeks pre and post ChatGPT release (2022-11-30)

Pre period:  2022-10-05 to 2022-11-29
Post period: 2022-11-30 to 2023-01-24

Subreddits: r/ChatGPT, r/artificial, r/MachineLearning, r/technology, r/OpenAI
"""

import requests
import json
import time
import os
from datetime import datetime, timezone

# Time windows (Unix timestamps)
PRE_START  = int(datetime(2022, 10, 5).timestamp())
PRE_END    = int(datetime(2022, 11, 29, 23, 59, 59).timestamp())
POST_START = int(datetime(2022, 11, 30).timestamp())
POST_END   = int(datetime(2023, 1, 24, 23, 59, 59).timestamp())

SUBREDDITS = ["ChatGPT", "artificial", "MachineLearning", "technology", "OpenAI"]

AI_KEYWORDS = {"ai", "chatgpt", "gpt", "openai", "llm", "generative ai", "deepfake",
               "gpt-3", "gpt-4", "language model", "neural network", "machine learning",
               "artificial intelligence"}

BASE_URL = "https://arctic-shift.photon-reddit.com/api/posts/search"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def has_ai_keyword(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in AI_KEYWORDS)


def fetch_posts(subreddit: str, after: int, before: int, period_name: str):
    """Fetch all posts from a subreddit in the given time window using Arctic Shift API.
    API returns newest-first; paginate backwards by updating 'before' each page.
    """
    posts = []
    # API accepts date strings; convert unix timestamps
    after_str  = datetime.fromtimestamp(after, timezone.utc).strftime("%Y-%m-%d")
    before_str = datetime.fromtimestamp(before, timezone.utc).strftime("%Y-%m-%d")

    current_before = before_str
    page = 0
    while True:
        params = {
            "subreddit": subreddit,
            "after":  after_str,
            "before": current_before,
            "limit":  100,
        }
        try:
            resp = requests.get(BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  Error fetching page {page}: {e}")
            time.sleep(5)
            continue

        items = data.get("data", [])
        if not items:
            break

        for item in items:
            title = item.get("title", "") or ""
            body  = item.get("selftext", "") or ""
            combined = title + " " + body

            if body in ("[deleted]", "[removed]"):
                body = ""
            if not title:
                continue

            if has_ai_keyword(combined):
                posts.append({
                    "id": item.get("id"),
                    "title": title,
                    "selftext": body,
                    "subreddit": item.get("subreddit"),
                    "created_utc": item.get("created_utc"),
                    "score": item.get("score", 0),
                    "url": item.get("url", ""),
                    "num_comments": item.get("num_comments", 0),
                })

        page += 1
        print(f"  r/{subreddit} [{period_name}] page {page}: got {len(items)} posts, kept {len(posts)} so far")

        if len(items) < 100:
            break

        # Paginate backwards: oldest item in this batch becomes new upper bound
        oldest_ts = min(item.get("created_utc", after) for item in items)
        current_before = datetime.fromtimestamp(oldest_ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        time.sleep(1)  # be polite to the API

    return posts


def main():
    for period_name, after, before in [
        ("pre",  PRE_START,  PRE_END),
        ("post", POST_START, POST_END),
    ]:
        all_posts = []
        for sub in SUBREDDITS:
            print(f"\nFetching r/{sub} [{period_name}]...")
            posts = fetch_posts(sub, after, before, period_name)
            all_posts.extend(posts)
            print(f"  -> {len(posts)} posts collected")

        # Deduplicate by id
        seen = set()
        unique_posts = []
        for p in all_posts:
            if p["id"] not in seen:
                seen.add(p["id"])
                unique_posts.append(p)

        out_path = os.path.join(OUTPUT_DIR, f"corpus_{period_name}.jsonl")
        with open(out_path, "w", encoding="utf-8") as f:
            for p in unique_posts:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

        print(f"\n[{period_name}] Total unique posts: {len(unique_posts)}")
        print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()
