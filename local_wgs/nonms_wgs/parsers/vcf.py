from __future__ import annotations

import gzip
from pathlib import Path
from typing import Iterable, Optional


DEFAULT_TARGETS = {
    "rs4957796": "FER sepsis-survival / vascular-barrier disease-tolerance candidate",
    "rs225014": "DIO2 Thr92Ala thermoregulation / tissue thyroid marker",
    "rs2549794": "ERAP2 ancient-selection / antigen-processing marker",
    "rs2248374": "ERAP2 expression/splice marker",
    "rs2548538": "ERAP2 linked marker",
    "rs2066847": "NOD2 1007fs innate immune recognition marker",
    "rs1800896": "IL10 immune-resolution cytokine marker",
    "rs1800871": "IL10 promoter marker",
    "rs1800872": "IL10 promoter marker",
    "rs2230926": "TNFAIP3 / A20 immune-brake marker",
    "rs231775": "CTLA4 immune-checkpoint marker",
    "rs1024611": "CCL2 inflammatory recruitment marker",
    "rs1800629": "TNF inflammatory signaling marker",
    "rs1800795": "IL6 inflammatory signaling marker",
    "rs4986790": "TLR4 innate immune marker",
    "rs4986791": "TLR4 innate immune marker",
}

GENE_MODULES = {
    "Disease_Tolerance_Sepsis_Tradeoff": [
        "FER", "HMOX1", "HP", "HFE", "SLC40A1", "CISH", "IL10", "TGFB1",
        "TNFAIP3", "SOCS1", "SOCS3", "CTLA4", "PDCD1", "FOXO1", "FOXO3"
    ],
    "Thermoregulation_Thyroid_Switch": [
        "DIO2", "DIO3", "THRA", "THRB", "SLC16A2", "SLC16A10",
        "TSHR", "TRH", "TRHR", "SECISBP2", "TPO", "TG", "TSHB"
    ],
    "Antigen_Presentation_Ancient_Selection": [
        "ERAP1", "ERAP2", "HLA-A", "HLA-B", "HLA-C", "HLA-DRA",
        "HLA-DRB1", "HLA-DQA1", "HLA-DQB1", "TAP1", "TAP2"
    ],
    "Innate_Pathogen_Recognition": [
        "NOD2", "TLR1", "TLR2", "TLR4", "TLR6", "TLR9", "MYD88",
        "CARD9", "CLEC7A", "NLRP3"
    ],
    "B_Cell_Memory_Immune_Loop": [
        "TNFSF13B", "TNFSF13", "TNFRSF13B", "TNFRSF13C", "CR2",
        "CD40", "CD40LG", "IL7R", "IL2RA", "MS4A1"
    ],
    "Vascular_BBB_Containment": [
        "FER", "ICAM1", "VCAM1", "SELE", "CLDN5", "OCLN", "MMP9",
        "NOS3", "VEGFA", "AQP4"
    ],
}


def open_vcf(path: Path):
    if str(path).lower().endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="ignore")
    return open(path, "rt", encoding="utf-8", errors="ignore")


def parse_gt(sample_value: str, format_value: str) -> str:
    if not sample_value or not format_value:
        return ""
    keys = format_value.split(":")
    vals = sample_value.split(":")
    if "GT" not in keys:
        return ""
    idx = keys.index("GT")
    return vals[idx] if idx < len(vals) else ""


def gt_to_alleles(gt: str, ref: str, alt: str) -> str:
    if not gt:
        return ""
    alts = alt.split(",") if alt else []
    mapping = {"0": ref}
    for idx, allele in enumerate(alts, start=1):
        mapping[str(idx)] = allele
    parts = gt.replace("|", "/").split("/")
    if any(p == "." for p in parts):
        return gt
    return "/".join(mapping.get(p, p) for p in parts)


def scan_targets(vcf_path: Path, targets: Optional[Iterable[str]] = None) -> tuple[list[dict], dict]:
    target_set = set(targets or DEFAULT_TARGETS.keys())
    hits = []
    stats = {"variants": 0, "rsid_variants": 0, "header_found": False, "samples": []}

    with open_vcf(vcf_path) as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line:
                continue
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                stats["header_found"] = True
                header = line.lstrip("#").split("\t")
                stats["samples"] = header[9:] if len(header) > 9 else []
                continue
            if line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 8:
                continue

            stats["variants"] += 1
            chrom, pos, vid, ref, alt, qual, filt, info = parts[:8]
            fmt = parts[8] if len(parts) > 8 else ""
            sample = parts[9] if len(parts) > 9 else ""
            gt = parse_gt(sample, fmt)
            alleles = gt_to_alleles(gt, ref, alt)

            ids = set(str(vid).split(";"))
            if any(x.startswith("rs") for x in ids):
                stats["rsid_variants"] += 1

            for rsid in ids.intersection(target_set):
                hits.append({
                    "rsID": rsid,
                    "Note": DEFAULT_TARGETS.get(rsid, ""),
                    "CHROM": chrom,
                    "POS": pos,
                    "REF": ref,
                    "ALT": alt,
                    "GT": gt,
                    "Genotype_Alleles": alleles,
                    "FILTER": filt,
                    "INFO_preview": info[:250],
                })

    return hits, stats


def scan_gene_symbols_from_info(vcf_path: Path, gene_symbols: Iterable[str], max_hits: int = 20000) -> tuple[list[dict], dict]:
    """
    Opportunistic gene extraction using gene symbols in the VCF INFO field.
    This works only if the VCF is annotated with gene names. If not annotated,
    use the target-rsID scan first or annotate the VCF with external tools.
    """
    genes = {g.upper() for g in gene_symbols}
    hits = []
    stats = {"variants": 0, "gene_hits": 0, "note": "Searches gene symbols in INFO field; requires annotated VCF."}

    with open_vcf(vcf_path) as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 8:
                continue
            stats["variants"] += 1
            chrom, pos, vid, ref, alt, qual, filt, info = parts[:8]
            info_upper = info.upper()
            if any(g in info_upper for g in genes):
                fmt = parts[8] if len(parts) > 8 else ""
                sample = parts[9] if len(parts) > 9 else ""
                gt = parse_gt(sample, fmt)
                hits.append({
                    "CHROM": chrom, "POS": pos, "ID": vid, "REF": ref, "ALT": alt,
                    "GT": gt, "Alleles": gt_to_alleles(gt, ref, alt),
                    "FILTER": filt, "INFO_preview": info[:500],
                })
                stats["gene_hits"] += 1
                if len(hits) >= max_hits:
                    break
    return hits, stats
