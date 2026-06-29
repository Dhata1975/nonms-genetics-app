from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

from nonms_wgs.parsers.vcf import (
    DEFAULT_TARGETS,
    resolve_vcf_path,
    scan_gene_symbols_from_info,
    scan_targets,
    validate_vcf,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="NONMS Local WGS Explorer")
    parser.add_argument("--vcf", required=True, help="Path to .vcf/.vcf.gz file OR Sequencing.com export folder")
    parser.add_argument("--out", default="output", help="Output folder")
    parser.add_argument("--genes", nargs="*", default=[], help="Optional gene symbols to search in annotated VCF INFO field")
    args = parser.parse_args()

    vcf_input = Path(args.vcf).expanduser()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    resolved = resolve_vcf_path(vcf_input)
    print(f"Resolved VCF: {resolved}")

    validation = validate_vcf(resolved)
    pd.DataFrame([validation]).drop(columns=["first_lines"], errors="ignore").to_csv(out_dir / "NONMS_WGS_Validation.csv", index=False)

    print("Scanning target rsIDs...")
    hits, stats = scan_targets(resolved, DEFAULT_TARGETS.keys())
    hits_df = pd.DataFrame(hits)
    stats_df = pd.DataFrame([stats])

    target_out = out_dir / "NONMS_WGS_Target_rsID_Hits.csv"
    stats_out = out_dir / "NONMS_WGS_Scan_Stats.csv"
    hits_df.to_csv(target_out, index=False)
    stats_df.to_csv(stats_out, index=False)

    print(f"Variants scanned: {stats['variants']:,}")
    print(f"Target hits found: {len(hits_df):,}")
    print(f"Wrote: {target_out}")
    print(f"Wrote: {stats_out}")

    if args.genes:
        print(f"Scanning gene symbols in INFO field: {', '.join(args.genes)}")
        gene_hits, gene_stats = scan_gene_symbols_from_info(resolved, args.genes)
        gene_df = pd.DataFrame(gene_hits)
        gene_out = out_dir / "NONMS_WGS_Gene_INFO_Hits.csv"
        gene_df.to_csv(gene_out, index=False)
        pd.DataFrame([gene_stats]).to_csv(out_dir / "NONMS_WGS_Gene_Search_Stats.csv", index=False)
        print(f"Gene hits found: {len(gene_df):,}")
        print(f"Wrote: {gene_out}")


if __name__ == "__main__":
    main()
