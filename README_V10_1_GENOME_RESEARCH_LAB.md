# NONMS V10.1 Genome Research Lab

This package updates the local WGS tool to fix the Sequencing.com nested-folder issue.

## What changed

- Accepts either a VCF file path or a folder path.
- Automatically finds the actual `.vcf` / `.vcf.gz` file inside a Sequencing.com export folder.
- Adds **Validate genome path** before scanning.
- Confirms file format, size, source, and reference genome.
- Keeps cloud volunteer mode separate from local WGS mode.

## What to do

1. Replace your current package with this version.
2. Go to `local_wgs`.
3. Double-click `RUN_LOCAL_WGS_APP.bat`.
4. Click **Validate genome path**.
5. Click **Scan target rsIDs**.

## Goal

First scan: determine whether your WGS contains target disease-tolerance candidates, especially FER `rs4957796`.
