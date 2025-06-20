EndNote‑Toolkit

Convert in‑text cross‑references into EndNote‑style citations.

Key Features

Script

Purpose

Key Fields

Data Source

quick_refs2ris_v2.py

Convert the refs.txt reference list from Word into a RIS file refs.ris

AU / TI / JO / PY / DOI / ISBN

Local regex parsing

enrich_with_crossref.py

Complete missing metadata in refs.ris and output refs_full.ris

DOI · volume/issue/pages · publisher

Online API

renumber_by_title.py

Re‑order <rec-number> according to the reference list in Word

rec‑number

Local matching algorithm

Installation & Dependencies

# Clone the repository
$ git clone https://github.com/<you>/CQP-EndNote-Toolkit.git
$ cd CQP-EndNote-Toolkit

# Install Python dependencies
$ pip install -r requirements.txt  # requests, rapidfuzz, rich, lxml ...

Environment: Python ≥ 3.8; internet access to Crossref / OpenLibrary.

One‑click Pipeline

python scripts/quick_refs2ris_v2.py  refs.txt  refs.ris
python scripts/enrich_with_crossref.py  refs.ris  refs_full.ris
python scripts/renumber_by_title.py  CQP.xml  refs.txt  CQP_renum.xml

After completion, import CQP_renum.xml into EndNote / Cite While You Write to align with the golden numbering.

Directory Structure

EndNote-Toolkit/
│─ quick_refs2ris_v2.py
│─ enrich_with_crossref.py
│─ renumber_by_title.py
└─ README.md

Issue

Solution

Crossref 429 rate limit

Increase --sleep or enable a VPN; you can also adjust MAX_RETRY in scripts/enrich_with_crossref.py.

rec-number conflicts in XML

Ensure no duplicate numbers in the golden list, or first bulk‑clear rec-number in EndNote before running the script.

Non‑English journal matching fails

Standardize translations in the golden list and XML, or manually resolve spelling differences.

Word

Press Ctrl + H in Word.

Field

Value (half‑width characters)

Find what

\[([0-9]{1,4}),[ ]*([0-9]{1,4})\]

Replace with

[\1] [\2]

After running Replace All, for example:

[100, 101]   →   [100] [101]

Field

Value

Find what

\[([0-9]{1,4})\]

Replace with

{#\1}

Run Replace All again:

[57]  →  {#57}
[201] → {#201}

In the Word ribbon, click EndNote ► Update Citations and Bibliography.
