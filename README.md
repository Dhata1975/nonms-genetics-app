# NONMS Genetics Engine v3

## What this version includes
- Full integrated marker sets bundled inside the app
- MS GWAS marker list
- SAM-e vulnerability
- Stress nexus event
- Small vessel disorder
- Autonomic loop
- Molecular mimicry
- CSVD
- Homocysteine
- Mold/Fungus
- Tinea versicolor
- H. pylori
- Cardiomegaly
- T-Waves
- Low B12
- Periodontal disease
- Methylation
- Dysautonomia

## Main features
- Upload an AncestryDNA raw `.txt` file
- Compare against all bundled datasets automatically
- Filter included datasets from the UI
- Review category summaries and row-level matches
- Export:
  - Excel report
  - PDF summary report
  - ZIP of CSV files

## Local run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud deploy
1. Create a GitHub repo.
2. Upload all files from this ZIP.
3. Sign in to Streamlit Community Cloud.
4. Deploy the repo and set `app.py` as the entry point.

## Embed on nonms.com
Use an iframe on your site:
```html
<iframe
  src="https://YOUR-APP.streamlit.app/?embed=true"
  width="100%"
  height="1100"
  style="border:0;"
></iframe>
```

## Cleaner branded deployment
For a cleaner URL such as `genetics.nonms.com`, self-host Streamlit and put it behind Cloudflare or Cloudflare Tunnel.

## Important note
This is a pattern comparison tool. It does not diagnose disease, provide medical advice, or produce a validated polygenic risk score.


## v4 UI refresh
This package includes an Area 76 style command-center UI refresh:
- hero command header
- privacy and mission guardrails panels
- cleaned metric cards
- command summary tab
- manual review tab
- stronger dark/gold visual system


## v5 export fix
- hardened Excel export against duplicate sheet names and illegal characters
- separated Excel, PDF, and CSV export generation so one failure does not crash the app
