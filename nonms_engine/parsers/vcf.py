from __future__ import annotations

import gzip
import os
import tempfile
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass
class VCFHit:
    rsid: str
    note: str
    chrom: str
    pos: str
    ref: str
    alt: str
    genotype_code: str
    genotype_alleles: str
    filt: str
    info_preview: str


TARGET_RSIDS = {
    "rs4957796": "FER candidate linked to sepsis-survival / vascular-barrier disease-tolerance literature",
    "rs225014": "DIO2 Thr92Ala thermoregulation / tissue thyroid signaling marker",
    "rs2549794": "ERAP2 ancient-selection / antigen-processing marker",
    "rs2248374": "ERAP2 splice / expression marker",
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
    "rs4143094": "TLR4 innate immune marker",
    "rs4986790": "TLR4 innate immune marker",
    "rs4986791": "TLR4 innate immune marker",
}


GENE_MODULES = {
    "Disease Tolerance / Sepsis Tradeoff": [
        "FER", "HMOX1", "HP", "HFE", "SLC40A1", "CISH", "IL10", "TGFB1",
        "TNFAIP3", "SOCS1", "SOCS3", "CTLA4", "PDCD1", "FOXO1", "FOXO3"
    ],
    "Thermoregulation / Thyroid Switch": [
        "DIO2", "DIO3", "THRA", "THRB", "SLC16A2", "SLC16A10",
        "TSHR", "TRH", "TRHR", "SECISBP2", "TPO", "TG", "TSHB"
    ],
    "Antigen Presentation / Ancient Selection": [
        "ERAP1", "ERAP2", "HLA-A", "HLA-B", "HLA-C", "HLA-DRA",
        "HLA-DRB1", "HLA-DQA1", "HLA-DQB1", "TAP1", "TAP2"
    ],
    "Innate Pathogen Recognition": [
        "NOD2", "TLR1", "TLR2", "TLR4", "TLR6", "TLR9", "MYD88",
        "CARD9", "CLEC7A", "NLRP3"
    ],
    "B-cell / Memory Immune Loop": [
        "TNFSF13B", "TNFSF13", "TNFRSF13B", "TNFRSF13C", "CR2",
        "CD40", "CD40LG", "IL7R", "IL2RA", "MS4A1"
    ],
    "Vascular / BBB Containment": [
        "FER", "ICAM1", "VCAM1", "SELE", "CLDN5", "OCLN", "MMP9",
        "NOS3", "VEGFA", "AQP4"
    ],
}


def _parse_gt(sample_value: str, format_value: str) -> str:
    if not sample_value or not format_value:
        return ""
    keys = format_value.split(":")
    vals = sample_value.split(":")
    if "GT" not in keys:
        return ""
    idx = keys.index("GT")
    return vals[idx] if idx < len(vals) else ""


def _gt_to_alleles(gt: str, ref: str, alt: str) -> str:
    if not gt:
        return ""
    alts = alt.split(",") if alt else []
    allele_map = {"0": ref}
    for i, a in enumerate(alts, start=1):
        allele_map[str(i)] = a
    parts = gt.replace("|", "/").split("/")
    if any(p == "." for p in parts):
        return gt
    return "/".join(allele_map.get(p, p) for p in parts)


def save_upload_to_temp(uploaded_file, suffix: Optional[str] = None) -> str:
    name = uploaded_file.name.lower()
    if suffix is None:
        suffix = ".vcf.gz" if name.endswith(".gz") else ".vcf"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        uploaded_file.seek(0)
        while True:
            chunk = uploaded_file.read(1024 * 1024)
            if not chunk:
                break
            tmp.write(chunk)
    finally:
        tmp.close()
    return tmp.name


def scan_vcf_path(path: str, target_rsids: Optional[Iterable[str]] = None, preview_limit: int = 100) -> dict:
    targets = set(target_rsids or TARGET_RSIDS.keys())
    is_gz = path.lower().endswith(".gz")
    opener = gzip.open if is_gz else open

    total_variants = 0
    rsid_variants = 0
    hits: list[VCFHit] = []
    preview: list[dict] = []
    sample_names: list[str] = []
    found_header = False

    with opener(path, "rt", encoding="utf-8", errors="ignore") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line:
                continue
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                found_header = True
                header = line.lstrip("#").split("\t")
                if len(header) > 9:
                    sample_names = header[9:]
                continue
            if line.startswith("#"):
                continue

            parts = line.split("\t")
            if len(parts) < 8:
                continue

            total_variants += 1
            chrom, pos, vid, ref, alt, qual, filt, info = parts[:8]
            fmt = parts[8] if len(parts) > 8 else ""
            sample_val = parts[9] if len(parts) > 9 else ""
            gt = _parse_gt(sample_val, fmt)
            gt_alleles = _gt_to_alleles(gt, ref, alt)

            if vid.startswith("rs"):
                rsid_variants += 1

            if len(preview) < preview_limit:
                preview.append({
                    "CHROM": chrom,
                    "POS": pos,
                    "ID": vid,
                    "REF": ref,
                    "ALT": alt,
                    "GT": gt,
                    "Alleles": gt_alleles,
                    "FILTER": filt,
                })

            ids = set(str(vid).split(";"))
            for rsid in ids.intersection(targets):
                hits.append(VCFHit(
                    rsid=rsid,
                    note=TARGET_RSIDS.get(rsid, ""),
                    chrom=chrom,
                    pos=pos,
                    ref=ref,
                    alt=alt,
                    genotype_code=gt,
                    genotype_alleles=gt_alleles,
                    filt=filt,
                    info_preview=info[:240],
                ))

    return {
        "found_header": found_header,
        "sample_names": sample_names,
        "total_variants_scanned": total_variants,
        "rsid_variants_scanned": rsid_variants,
        "hits": [h.__dict__ for h in hits],
        "preview": preview,
    }


def scan_uploaded_vcf(uploaded_file, target_rsids: Optional[Iterable[str]] = None) -> dict:
    path = save_upload_to_temp(uploaded_file)
    try:
        result = scan_vcf_path(path, target_rsids=target_rsids)
        result["file_name"] = uploaded_file.name
        return result
    finally:
        try:
            os.remove(path)
        except Exception:
            pass
