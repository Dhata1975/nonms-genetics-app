# NONMS V10 Hybrid Platform

This package splits NONMS into two modes:

## 1. Cloud Volunteer Mode

Use Streamlit Cloud for:
- AncestryDNA
- 23andMe
- MyHeritage
- volunteer-friendly reports
- cohort-ready SNP-array workflows

Main entry file:
`app.py`

## 2. Local WGS Mode

Use your own Windows computer for:
- Sequencing.com 30x WGS VCF
- 974 MB+ files
- FER `rs4957796`
- disease-tolerance candidates
- local research scans without upload limits

Folder:
`local_wgs/`

Start local WGS app:
`local_wgs/RUN_LOCAL_WGS_APP.bat`

Run direct target scan:
`local_wgs/RUN_TARGET_SCAN.bat`

## GitHub Upload

Upload the entire package to GitHub. The cloud app will keep running through `app.py`.

## First WGS goal

Run the local target scan and check whether your WGS contains FER `rs4957796`.
