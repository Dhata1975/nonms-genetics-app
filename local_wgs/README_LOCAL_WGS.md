# NONMS Local WGS Mode

Use this folder on your own Windows computer for the 974 MB Sequencing.com WGS VCF.

## Option A: Local Streamlit Explorer

1. Open this `local_wgs` folder.
2. Double-click `RUN_LOCAL_WGS_APP.bat`.
3. Your browser will open a local NONMS WGS Explorer.
4. Confirm the VCF path.
5. Click **Scan target rsIDs**.

## Option B: Direct target scan

1. Open `RUN_TARGET_SCAN.bat` in Notepad.
2. Confirm the `VCF_PATH` line matches your file path.
3. Save it.
4. Double-click `RUN_TARGET_SCAN.bat`.

Outputs will appear in:

`local_wgs/output/`

## First target scan includes

- FER `rs4957796`
- DIO2 `rs225014`
- ERAP2 markers
- NOD2 `rs2066847`
- IL10 / TNFAIP3 / CTLA4 / TLR markers

## Important

The first scan is rsID-based. If the VCF is not annotated with gene names, gene-symbol search may return no rows. That is normal. The next upgrade will add coordinate-based gene extraction.
