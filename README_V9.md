# NONMS Genetics Engine V9 — Volunteer Experience

This package updates the working modular app with a new volunteer-friendly layer while preserving the technical report.

## What changed
- Adds a new **Volunteer Summary** tab in the app.
- Adds plain-English introductory pages to the PDF report.
- Keeps all existing technical tables, exports, matched rows, manual review rows, and category summaries.
- Keeps AncestryDNA, 23andMe, and MyHeritage support.
- Keeps modular `/data/*.txt` panel discovery.

## Deploy
1. Replace your current `app.py` with this `app.py`.
2. Keep your existing `/data` folder as-is.
3. Commit and push to GitHub.
4. Reboot Streamlit Cloud.

## Note
This version does not remove any data. It adds an educational layer before the detailed report.
