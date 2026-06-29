# NONMS Genetics Engine V10 — Professional WGS Build

This build fixes the previous `from __future__` import error by separating the app into a clean V10 shell and a preserved V9 legacy module.

## Modes

- **Home**
- **WGS / VCF Explorer**
- **Legacy V9 Genetics Engine**

## WGS / VCF Explorer

Supports:
- `.vcf`
- `.vcf.gz`
- Sequencing.com WGS VCF files

First target scan includes:
- FER `rs4957796`
- DIO2 `rs225014`
- ERAP2 markers
- NOD2 `rs2066847`
- IL10 / TNFAIP3 / CTLA4 / TLR markers

## Deploy

1. Unzip this package.
2. Replace your GitHub repo files with this package.
3. Make sure the `.streamlit/config.toml` folder/file is uploaded.
4. Commit and push.
5. Reboot Streamlit Cloud.
6. Open the app.
7. Select **WGS / VCF Explorer** in the sidebar.
8. Upload your Sequencing.com VCF.

## Note

A 974 MB file may take several minutes. If Streamlit Cloud times out, run the app locally with:

```bash
pip install -r requirements.txt
streamlit run app.py
```
