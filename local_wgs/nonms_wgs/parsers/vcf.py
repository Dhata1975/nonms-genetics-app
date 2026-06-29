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


def resolve_vcf_path(input_path: str | Path) -> Path:
    """
    Accepts either:
    - a direct .vcf / .vcf.gz file path
    - a Sequencing.com export folder that may itself end in .vcf
    - a folder containing a same-named .vcf file

    Returns the actual file path to scan.
    """
    p = Path(str(input_path).strip().strip('"')).expanduser()

    if p.is_file():
        return p

    if p.is_dir():
        # Prefer exact child with same name.
        same_name = p / p.name
        if same_name.is_file():
            return same_name

        # Otherwise locate likely VCF files recursively.
        candidates = []
        for pattern in ("*.vcf", "*.vcf.gz"):
            candidates.extend([x for x in p.rglob(pattern) if x.is_file()])

        if candidates:
            # Prefer largest VCF because the actual genome is usually huge.
            candidates.sort(key=lambda x: x.stat().st_size, reverse=True)
            return candidates[0]

        raise FileNotFoundError(f"No .vcf or .vcf.gz file found inside folder: {p}")

    # If user pasted outer folder path without quotes and it exists as same-name child.
    parent = p.parent
    if parent.exists() and parent.is_dir():
        same_name = parent / p.name / p.name
        if same_name.is_file():
            return same_name

    raise FileNotFoundError(f"VCF path not found: {p}")


def validate_vcf(vcf_path: str | Path) -> dict:
    p = resolve_vcf_path(vcf_path)
    result = {
        "resolved_path": str(p),
        "size_bytes": p.stat().st_size,
        "is_gzip": str(p).lower().endswith(".gz"),
        "is_valid_vcf": False,
        "fileformat": "",
        "reference": "",
        "source": "",
        "first_lines": [],
    }
    opener = gzip.open if result["is_gzip"] else open
    with opener(p, "rt", encoding="utf-8", errors="ignore") as fh:
        for i, raw in enumerate(fh):
            line = raw.rstrip("\n")
            if i < 25:
                result["first_lines"].append(line)
            if line.startswith("##fileformat="):
                result["fileformat"] = line.replace("##fileformat=", "")
                result["is_valid_vcf"] = True
            elif line.startswith("##reference="):
                result["reference"] = line.replace("##reference=", "")
            elif line.startswith("##source="):
                result["source"] = line.replace("##source=", "")
            if i >= 200:
                break
    return result


def open_vcf(path: Path):
    resolved = resolve_vcf_path(path)
    if str(resolved).lower().endswith(".gz"):
        return gzip.open(resolved, "rt", encoding="utf-8", errors="ignore")
    return open(resolved, "rt", encoding="utf-8", errors="ignore")


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
    resolved = resolve_vcf_path(vcf_path)
    hits = []
    stats = {
        "resolved_path": str(resolved),
        "variants": 0,
        "rsid_variants": 0,
        "header_found": False,
        "samples": [],
    }

    with open_vcf(resolved) as fh:
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
    coordinate-based extraction is the next upgrade.
    """
    resolved = resolve_vcf_path(vcf_path)
    genes = {g.upper() for g in gene_symbols}
    hits = []
    stats = {
        "resolved_path": str(resolved),
        "variants": 0,
        "gene_hits": 0,
        "note": "Searches gene symbols in INFO field; requires annotated VCF."
    }

    with open_vcf(resolved) as fh:
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
