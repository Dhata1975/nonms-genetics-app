# NONMS V10 WGS / VCF Support

This upgrade adds a WGS/VCF Explorer to the existing V9 app.

## What changed

- Adds support for `.vcf` and `.vcf.gz` uploads.
- Adds Streamlit upload limit config: `.streamlit/config.toml` with `maxUploadSize = 2000`.
- Adds a sidebar mode selector:
  - Genetics Engine
  - WGS / VCF Explorer
- Streams large VCF files from disk instead of loading the full file into memory.
- First target panel checks key candidate rsIDs, including FER `rs4957796`.

## Deploy

1. Unzip this package.
2. Upload/replace the files in GitHub.
3. Make sure `.streamlit/config.toml` is included in the repo.
4. Commit and push.
5. Reboot Streamlit Cloud.
6. Open the app and select **WGS / VCF Explorer** from the sidebar.
7. Upload your Sequencing.com VCF file.

## Important

A 974 MB VCF may still take several minutes to upload and scan in Streamlit Cloud.
If Streamlit Cloud times out, the next step is to run this app locally on your machine and upload the VCF there.
