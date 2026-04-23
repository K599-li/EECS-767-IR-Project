# Information Exposure Shift Around the ChatGPT Launch: A BM25 Retrieval Study on Reddit

**EECS 767 – Information Retrieval**

---

## 1. Introduction

On November 30, 2022, OpenAI released ChatGPT, triggering an unprecedented surge of public discussion about artificial intelligence. This study investigates whether this event caused a measurable shift in *information exposure* — the types of content that an information retrieval system surfaces in response to AI-related queries.

**Research question:** Did the ChatGPT launch change the category distribution and retrieval quality of top-ranked documents for AI-related queries on Reddit?

---

## 2. Data Collection

Reddit posts were collected from five AI-focused subreddits (r/ChatGPT, r/artificial, r/MachineLearning, r/technology, r/OpenAI) via the Arctic Shift API. Only posts containing AI-related keywords were retained. Two non-overlapping eight-week windows were defined:

| Period | Date Range | Unique Posts |
|--------|-----------|-------------|
| Pre | Oct 5 – Nov 29, 2022 | 4,278 |
| Post | Nov 30, 2022 – Jan 24, 2023 | 20,245 |

The five-fold increase in corpus size from pre to post reflects the explosive growth in AI discussion following the ChatGPT launch. Notably, the query "ChatGPT" (E01) returned zero hits in the pre-period corpus, confirming a clean pre/post split.

---

## 3. Methodology

### 3.1 Indexing and Retrieval

Both corpora were indexed independently using Pyserini's BM25 implementation (Apache Lucene, k₁ = 0.9, b = 0.4). A query set of 30 queries was constructed across three types:

- **Entity** (E01–E10): e.g., "ChatGPT", "GPT-4", "DALL-E"
- **Issue** (I01–I10): e.g., "AI regulation", "AI bias", "AI safety"
- **Scenario** (S01–S10): e.g., "how to detect AI writing", "AI replace jobs"

Top-10 documents were retrieved for each query from each corpus.

### 3.2 Document Categorization

Each document was assigned one of four categories using rule-based pattern matching:

| Category | Description |
|----------|-------------|
| News/External | Contains external URLs; news sharing |
| Question/Help | Question words or "?" in title/body |
| Personal | First-person experience ("I tried", "I built") |
| Technical | Tutorials, code, model/algorithm discussion |

### 3.3 Exposure Metrics

For each query at k ∈ {3, 5, 10}:

- **Jensen-Shannon Divergence (JSD):** measures distributional shift in category exposure between pre and post top-k results
- **Entropy:** measures diversity of the top-k category distribution
- **Overlap (Jaccard):** measures document-level overlap between pre and post results

Statistical significance was assessed with a one-sample t-test and 2,000-iteration bootstrap confidence intervals.

### 3.4 Relevance Assessment

A 10-query subset (balanced across E/I/S types) was manually annotated with graded relevance labels (0 = not relevant, 1 = partially relevant, 2 = highly relevant) for all 200 document–query pairs (10 queries × 2 periods × top-10). nDCG@10 was computed as a sanity check on retrieval quality.

---

## 4. Results

### 4.1 Category Distribution

Both periods are dominated by News/External content. However, the post-period shows a slight increase in this category at the expense of Technical content:

| Category | Pre | Post | Δ (Post − Pre) |
|----------|-----|------|----------------|
| News/External | 80.6% | 82.0% | +1.4% |
| Technical | 15.7% | 13.7% | −2.0% |
| Question/Help | 3.5% | 3.7% | +0.2% |
| Personal | 0.3% | 0.6% | +0.3% |

At the retrieval level (exposure diff averaged across all 30 queries at k = 10), News/External exposure increased by **+0.093** while Technical decreased by **−0.050**, suggesting that ChatGPT's launch shifted public discourse toward news and sharing rather than technical depth.

### 4.2 Jensen-Shannon Divergence

JSD was significantly greater than zero across all values of k, indicating that the category distribution of top-ranked results shifted systematically after the ChatGPT launch:

| k | Mean JSD | 95% CI | t | p |
|---|----------|--------|---|---|
| 3 | 0.065 | [0.037, 0.099] | 4.113 | **0.0003** |
| 5 | 0.062 | [0.038, 0.095] | 4.306 | **0.0002** |
| 10 | 0.057 | [0.034, 0.088] | 4.085 | **0.0003** |

### 4.3 Entropy

Post-period retrieval results show lower entropy (less diversity in category distribution), consistent with the observation that post-period results are more heavily concentrated in News/External content. The entropy reduction reaches statistical significance at k = 10:

| k | Mean Entropy Diff (Post − Pre) | 95% CI | p |
|---|-------------------------------|--------|---|
| 3 | −0.153 | [−0.337, 0.031] | 0.134 |
| 5 | −0.161 | [−0.368, 0.056] | 0.159 |
| 10 | **−0.210** | [**−0.374, −0.028**] | **0.027** |

### 4.4 Document Overlap

Jaccard overlap between pre and post retrieved document sets is 0.00 at all k. This is expected by design: the two corpora cover non-overlapping time windows, so no document can appear in both. This confirms that any similarity in category distributions across periods must arise from genuine thematic alignment rather than shared documents.

### 4.5 Retrieval Quality (nDCG@10)

Manual relevance annotation on the 10-query subset yields consistently high nDCG@10, validating that BM25 retrieves relevant content in both periods:

| Period | Mean nDCG@10 |
|--------|-------------|
| Post | **0.981** |
| Pre | **0.873** |

The lower pre-period score is driven primarily by two scenario queries — "how to use ChatGPT" (nDCG = 0.41) and "how to detect AI writing" (nDCG = 0.70) — for which truly relevant documents did not yet exist before the ChatGPT launch. This lower nDCG in the pre-period is itself substantive evidence of the exposure shift: the retrieval system cannot return high-quality results for post-launch concepts when queried against a pre-launch corpus.

---

## 5. Discussion

The results collectively support the hypothesis that the ChatGPT launch caused a significant and measurable shift in information exposure for AI-related queries:

1. **Volume shift:** The post-period corpus is five times larger than the pre-period, reflecting a surge in AI discussion.
2. **Distributional shift:** JSD is significantly positive at all k (p < 0.001), confirming that the category composition of top-ranked results changed.
3. **Diversity reduction:** Post-period results are less categorically diverse (lower entropy at k = 10, p = 0.027), trending toward news/sharing content over technical discussion.
4. **Concept availability:** Scenario queries around ChatGPT-specific tasks had no relevant pre-period documents, producing near-zero nDCG — a form of "information unavailability" that itself quantifies the exposure shift.

One limitation is the rule-based categorizer, which tends to over-assign documents to News/External (any URL triggers this category). A learned classifier would likely redistribute some documents into more specific categories. Additionally, the 30-query set, while balanced across types, is not exhaustive.

---

## 6. Conclusion

This study demonstrates that the ChatGPT launch on November 30, 2022 produced a statistically significant shift in the information landscape on AI-focused Reddit communities. BM25 retrieval results for the same queries differ significantly in their category distribution (JSD p < 0.001) and diversity (entropy p = 0.027) before and after the launch. Post-launch retrieval quality is higher (mean nDCG 0.981 vs. 0.873), but the pre-period gap reflects genuine information unavailability rather than retrieval failure. These findings suggest that major AI product releases can rapidly reshape the informational environment to which users are exposed through search and retrieval systems.

---

## Appendix: Query List

| ID | Type | Query |
|----|------|-------|
| E01–E10 | Entity | ChatGPT, OpenAI, GPT-4, DALL-E, Stable Diffusion, Google Bard, Midjourney, large language model, RLHF, GPT-3 |
| I01–I10 | Issue | AI regulation, AI bias, AI safety, AI ethics, AI copyright, misinformation AI, AI surveillance, deepfake detection, AI hallucination, AI alignment |
| S01–S10 | Scenario | how to detect AI writing, AI replace jobs, how to use ChatGPT, AI in education, AI art controversy, AI cheating on homework, prompt engineering, AI girlfriend chatbot, AI coding assistant, ChatGPT banned |
