# NONMS Genome Research Lab — Local WGS Mode

This version fixes the Sequencing.com nested-folder issue.

You can paste either:

1. The outer folder path:

`C:\Users\dhata\Downloads\DhataHarris-SQV32F23-30x-WGS-Sequencing_com-02-02-26.snp-indel.genome.vcf`

or

2. The actual inner file path:

`C:\Users\dhata\Downloads\DhataHarris-SQV32F23-30x-WGS-Sequencing_com-02-02-26.snp-indel.genome.vcf\DhataHarris-SQV32F23-30x-WGS-Sequencing_com-02-02-26.snp-indel.genome.vcf`

The app will automatically resolve the real VCF file.

## Run local app

Double-click:

`RUN_LOCAL_WGS_APP.bat`

Then click:

1. **Validate genome path**
2. **Scan target rsIDs**

## Direct command-line scan

Double-click:

`RUN_TARGET_SCAN.bat`

Outputs appear in:

`local_wgs/output/`

## First target scan includes

- FER `rs4957796`
- DIO2 `rs225014`
- ERAP2 markers
- NOD2 `rs2066847`
- IL10 / TNFAIP3 / CTLA4 / TLR markers

## Note

If no target rsID is found, that can mean the person is reference at that site and the VCF only lists non-reference variants, or the VCF IDs differ. The next upgrade will add coordinate-based checks for reference/no-call status.
