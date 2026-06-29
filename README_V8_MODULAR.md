# NONMS Genetics Engine Version 8 - Modular Release

## What changed

- The app now discovers every `.txt` SNP panel inside `/data` automatically.
- Future pathway panels can be added by dropping a new `.txt` file into `/data`; Python edits are no longer required.
- Parser supports AncestryDNA, 23andMe, and MyHeritage MHv1.0 CSV exports.
- New panels included: Immunometabolic Core, MPOA Network, Evolutionary Immune Network, ERAP2 / Ancient Selection, and DIO Thermoregulation.

## Deploy

1. Upload the contents of this ZIP to your GitHub repo.
2. Keep `app.py` at the project root.
3. Keep all SNP panel text files in `/data`.
4. Commit and push.
5. Reboot/redeploy Streamlit Cloud.

## Add future SNP panels

Create a new file in `/data`, for example `New Pathway.txt`, using tab-separated rows:

```
1	Trait or label	rs123456
2	Another label	rs7891011-A
```

The app will load it automatically.

## Guardrail

This is a research and pattern-comparison tool, not a diagnostic tool or validated polygenic risk score.
