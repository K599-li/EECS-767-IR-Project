"""
Step 3: Build the query set (~30 AI-related queries).
Three types: Entity, Issue, Scenario.
Saves to: queries.tsv  (qid<TAB>query_text)
"""

import os

BASE_DIR = os.path.dirname(__file__)

QUERIES = [
    # --- Entity queries ---
    ("E01", "ChatGPT"),
    ("E02", "OpenAI"),
    ("E03", "GPT-4"),
    ("E04", "DALL-E"),
    ("E05", "Stable Diffusion"),
    ("E06", "Google Bard"),
    ("E07", "Midjourney"),
    ("E08", "large language model"),
    ("E09", "reinforcement learning from human feedback"),
    ("E10", "GPT-3"),

    # --- Issue queries ---
    ("I01", "AI regulation"),
    ("I02", "AI bias"),
    ("I03", "AI safety"),
    ("I04", "AI ethics"),
    ("I05", "AI copyright"),
    ("I06", "misinformation AI"),
    ("I07", "AI surveillance"),
    ("I08", "deepfake detection"),
    ("I09", "AI hallucination"),
    ("I10", "AI alignment"),

    # --- Scenario queries ---
    ("S01", "how to detect AI writing"),
    ("S02", "AI replace jobs"),
    ("S03", "how to use ChatGPT"),
    ("S04", "AI in education"),
    ("S05", "AI art controversy"),
    ("S06", "AI cheating on homework"),
    ("S07", "prompt engineering"),
    ("S08", "AI girlfriend chatbot"),
    ("S09", "AI coding assistant"),
    ("S10", "ChatGPT banned"),
]

out_path = os.path.join(BASE_DIR, "queries.tsv")
with open(out_path, "w", encoding="utf-8") as f:
    for qid, text in QUERIES:
        f.write(f"{qid}\t{text}\n")

print(f"Saved {len(QUERIES)} queries to {out_path}")
