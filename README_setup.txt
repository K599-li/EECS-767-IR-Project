==================================================
EECS 767 Project Setup Instructions
==================================================

STEP 0: Install Java (required for Pyserini)
--------------------------------------------
Pyserini uses Apache Lucene which needs Java 11+.

Option A (recommended): Install from Microsoft OpenJDK
  https://learn.microsoft.com/en-us/java/openjdk/download
  Download "OpenJDK 21 LTS" -> .msi installer for Windows x64
  Run the installer, then open a NEW terminal and verify:
    java -version

Option B: Chocolatey (if installed)
  choco install temurin21

After installing Java, verify:
  java -version   # should show version 21 or 11+


STEP 0b: Install Pyserini
--------------------------
  pip install pyserini


STEP 0c: Install other dependencies (already done)
---------------------------------------------------
  pip install pandas numpy scipy matplotlib requests


==================================================
INDEXING COMMANDS (run after step2_build_corpus.py)
==================================================

Run these in your terminal from the project/ directory:

# Index pre corpus
python -m pyserini.index.lucene \
  --collection JsonCollection \
  --input data/pre \
  --index indexes/pre \
  --generator DefaultLuceneDocumentGenerator \
  --threads 4 \
  --storeRaw

# Index post corpus
python -m pyserini.index.lucene \
  --collection JsonCollection \
  --input data/post \
  --index indexes/post \
  --generator DefaultLuceneDocumentGenerator \
  --threads 4 \
  --storeRaw

Note: On Windows, replace backslashes with forward slashes if needed,
or use the Python wrapper below if the CLI fails.


==================================================
FULL PIPELINE (run in order)
==================================================

1. python step1_download_data.py      # Download Reddit data (~30-60 min)
2. python step2_build_corpus.py       # Clean and format for Pyserini
3. python step3_build_queries.py      # Generate queries.tsv
   [run indexing commands above]      # Build BM25 indexes
4. python step4_retrieve.py           # BM25 retrieval
5. python step5_categorize.py         # Label doc categories
6. python step6_metrics.py            # Compute metrics + stats
7. python step7_visualize.py          # Generate figures
8. python step8_relevance_ndcg.py --prepare
   # Manually fill analysis/relevance/annotation_template.tsv (relevance column: 0/1/2)
   python step8_relevance_ndcg.py --evaluate

==================================================
DATA NOTES
==================================================

Arctic Shift API: https://arctic-shift.photon-reddit.com/
  - Free access to historical Reddit data via API
  - No authentication needed for basic queries
  - Rate limit: ~1 req/sec, be polite

If Arctic Shift is slow or unavailable:
  - Try: https://the-eye.eu/redarcs/ (raw Pushshift dumps)
  - Or manually download from Academic Torrents: search "Pushshift Reddit"
