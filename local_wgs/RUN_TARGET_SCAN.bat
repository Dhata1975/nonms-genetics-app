@echo off
set VCF_PATH=C:\Users\dhata\Downloads\DhataHarris-SQV32F23-30x-WGS-Sequencing_com-02-02-26.snp-indel.genome.vcf
python -m pip install -r requirements_local.txt
python run_wgs_scan.py --vcf "%VCF_PATH%" --out output
pause
