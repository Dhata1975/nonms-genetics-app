
from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

DATASET_FILES = [
    "MS Attributes.txt",
    "SAM E Vulnerability.txt",
    "Stress Event.txt",
    "Small Vessel Disorder.txt",
    "Autonomic Loop.txt",
    "Molecular Mimicry.txt",
    "CSVD.txt",
    "Homocysteine.txt",
    "Mold Fungus.txt",
    "Tinea Versicolor.txt",
    "H Pylori.txt",
    "Cardiomegaly.txt",
    "Inverted T-waves.txt",
    "Low B12.txt",
    "Periodontal Disease.txt",
    "Methylation.txt",
    "Dysautonomia.txt",
]

DISPLAY_NAMES = {
    "MS Attributes.txt": "MS GWAS",
    "SAM E Vulnerability.txt": "SAM-e Vulnerability",
    "Stress Event.txt": "Stress Nexus Event",
    "Small Vessel Disorder.txt": "Small Vessel Disorder",
    "Autonomic Loop.txt": "Autonomic Loop",
    "Molecular Mimicry.txt": "Molecular Mimicry",
    "CSVD.txt": "CSVD",
    "Homocysteine.txt": "Homocysteine",
    "Mold Fungus.txt": "Mold/Fungus",
    "Tinea Versicolor.txt": "Tinea Versicolor",
    "H Pylori.txt": "H. pylori",
    "Cardiomegaly.txt": "Cardiomegaly",
    "Inverted T-waves.txt": "T-Waves",
    "Low B12.txt": "Low B12",
    "Periodontal Disease.txt": "Periodontal Disease",
    "Methylation.txt": "Methylation",
    "Dysautonomia.txt": "Dysautonomia",
}


@dataclass
class Dataset:
    file_name: str
    category: str
    frame: pd.DataFrame


def normalize_category_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")[:31] or "Sheet"


def parse_marker_token(token: str) -> tuple[Optional[str], Optional[str], str, str]:
    token = str(token).strip()
    if not token:
        return None, None, "blank", "Blank marker"

    if ";" in token:
        rsids = re.findall(r"rs\d+", token)
        if len(rsids) == 1:
            return rsids[0], None, "composite", "Composite marker; manual review needed"
        return None, None, "composite", "Composite marker/haplotype entry; manual review needed"

    if token.startswith("DRB") or token.startswith("A*") or "*" in token:
        return None, None, "hla", "HLA allele entry; not directly testable from standard Ancestry raw SNP export"

    m = re.match(r"^(rs\d+)-([A-Za-z\?]+)$", token)
    if m:
        rsid, allele = m.groups()
        allele = allele.upper()
        if allele == "?":
            return rsid, None, "rsid_unknown_allele", "Marker present but allele unspecified"
        if re.fullmatch(r"[ACGTID]+", allele) and len(allele) == 1:
            return rsid, allele, "rsid_single_allele", "Allele-aware comparison available"
        return rsid, allele, "rsid_multibase_allele", "Non-single-base allele; compare with caution"

    m = re.match(r"^(rs\d+)$", token)
    if m:
        return m.group(1), None, "rsid_only", "Presence/absence comparison available"

    if token.startswith("chr"):
        return None, None, "coordinate_marker", "Coordinate-based marker; not directly matched because raw file is rsID-based"

    return None, None, "other", "Unrecognized marker format"



def normalize_dataset_lines(path: Path) -> list[str]:
    raw_lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    cleaned = []
    i = 0
    marker_hint = re.compile(r"(\s|\\t)(rs\S+|DRB\S+|A\*\S+|chr\S+|kgp\S+)$")
    while i < len(raw_lines):
        line = raw_lines[i].strip()
        if not line:
            i += 1
            continue
        if marker_hint.search(line) or line.startswith("#") or "rsID/SNP" in line or "TRAIT" in line:
            cleaned.append(line)
            i += 1
            continue
        if i + 1 < len(raw_lines):
            nxt = raw_lines[i + 1].strip()
            if marker_hint.search(nxt):
                cleaned.append(f"{line} {nxt}")
                i += 2
                continue
        cleaned.append(line)
        i += 1
    return cleaned

def parse_generic_dataset(path: Path) -> Dataset:
    rows = []
    fixed_category = DISPLAY_NAMES.get(path.name, path.stem)
    for line in normalize_dataset_lines(path):
            line = line.strip()
            if not line:
                continue
            if line.startswith("#") or "rsID/SNP" in line or "TRAIT" in line:
                continue

            entry_id = None
            trait_label = fixed_category
            marker = None

            parts = re.split(r"\t+", line)

            if len(parts) >= 3 and parts[0].strip().isdigit():
                entry_id = int(parts[0].strip())
                trait_label = parts[1].strip() or fixed_category
                marker = parts[2].strip()
            else:
                m = re.match(r"^(\d+)\s+(.+?)\s+(rs\S+|DRB\S+|A\*\S+|chr\S+|kgp\S+)$", line)
                if m:
                    entry_id = int(m.group(1))
                    trait_label = m.group(2).strip() or fixed_category
                    marker = m.group(3).strip()
                else:
                    if len(parts) >= 2:
                        trait_label = parts[0].strip() or fixed_category
                        marker = parts[1].strip()
                    else:
                        marker = line.strip()

            rsid, allele, marker_type, note = parse_marker_token(marker)
            rows.append({
                "entry_id": entry_id,
                "category": fixed_category,
                "trait_label": trait_label,
                "raw_marker": marker,
                "rsid": rsid,
                "listed_allele": allele,
                "marker_type": marker_type,
                "note": note,
            })

    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["entry_id", "category", "trait_label", "raw_marker", "rsid", "listed_allele", "marker_type", "note"])
    return Dataset(path.name, fixed_category, df)

def load_all_datasets() -> list[Dataset]:
    return [parse_generic_dataset(DATA_DIR / name) for name in DATASET_FILES if (DATA_DIR / name).exists()]


def parse_ancestry_file(uploaded_file) -> pd.DataFrame:
    rows = []
    content = uploaded_file.getvalue().decode("utf-8", errors="ignore").splitlines()
    for line in content:
        if not line or line.startswith("#") or line.lower().startswith("rsid\t"):
            continue
        parts = line.split("\t")
        if len(parts) != 5:
            continue
        rsid, chrom, pos, a1, a2 = parts
        try:
            pos = int(pos)
        except ValueError:
            continue
        rows.append((rsid.strip(), chrom.strip(), pos, a1.strip().upper(), a2.strip().upper()))
    df = pd.DataFrame(rows, columns=["rsid", "chromosome", "position", "allele1", "allele2"])
    return df


def compare_dataset(dataset: Dataset, ancestry_df: pd.DataFrame) -> pd.DataFrame:
    df = dataset.frame.copy()
    if ancestry_df.empty:
        return df.assign(
            in_ancestry=False, chromosome=None, position=None, allele1=None, allele2=None,
            genotype=None, listed_allele_copies=None, zygosity=None,
            comparison_status="No ancestry data loaded", manual_review="Yes"
        )

    anc = ancestry_df.drop_duplicates("rsid").set_index("rsid")

    result_rows = []
    for _, row in df.iterrows():
        rsid = row["rsid"]
        allele = row["listed_allele"]
        marker_type = row["marker_type"]

        if not rsid:
            result_rows.append({
                **row.to_dict(),
                "in_ancestry": False,
                "chromosome": None,
                "position": None,
                "allele1": None,
                "allele2": None,
                "genotype": None,
                "listed_allele_copies": None,
                "zygosity": None,
                "comparison_status": "Not directly comparable",
                "manual_review": "Yes",
            })
            continue

        if rsid not in anc.index:
            result_rows.append({
                **row.to_dict(),
                "in_ancestry": False,
                "chromosome": None,
                "position": None,
                "allele1": None,
                "allele2": None,
                "genotype": None,
                "listed_allele_copies": None,
                "zygosity": None,
                "comparison_status": "rsID not present in Ancestry file",
                "manual_review": "Maybe",
            })
            continue

        rec = anc.loc[rsid]
        genotype = f"{rec['allele1']}{rec['allele2']}"

        status = ""
        copies = None
        zygosity = None
        manual_review = "No"

        if marker_type == "rsid_single_allele":
            copies = int(rec["allele1"] == allele) + int(rec["allele2"] == allele)
            if copies == 2:
                status = "Listed allele present"
                zygosity = "Homozygous listed allele"
            elif copies == 1:
                status = "Listed allele present"
                zygosity = "Heterozygous"
            else:
                status = "Listed allele absent"
                zygosity = "Listed allele absent"
        elif marker_type == "rsid_only":
            status = "Marker present"
            zygosity = "Genotype observed"
        elif marker_type == "rsid_unknown_allele":
            status = "Present, but listed allele unspecified"
            manual_review = "Yes"
        elif marker_type == "rsid_multibase_allele":
            copies = int(rec["allele1"] == allele) + int(rec["allele2"] == allele)
            status = "Possible exact multibase match" if copies > 0 else "No exact multibase match"
            zygosity = "Contains multibase allele" if copies > 0 else "Multibase allele not detected"
            manual_review = "Yes"
        else:
            status = "Present, manual review needed"
            manual_review = "Yes"

        result_rows.append({
            **row.to_dict(),
            "in_ancestry": True,
            "chromosome": rec["chromosome"],
            "position": int(rec["position"]),
            "allele1": rec["allele1"],
            "allele2": rec["allele2"],
            "genotype": genotype,
            "listed_allele_copies": copies,
            "zygosity": zygosity,
            "comparison_status": status,
            "manual_review": manual_review,
        })

    return pd.DataFrame(result_rows)


def build_summary(all_results: pd.DataFrame) -> pd.DataFrame:
    summaries = []
    for category, grp in all_results.groupby("category", sort=True):
        total = len(grp)
        directly_comparable = int(grp["marker_type"].isin(["rsid_single_allele", "rsid_only"]).sum())
        found = int(grp["in_ancestry"].fillna(False).sum())
        allele_present = int((grp["comparison_status"] == "Listed allele present").sum())
        marker_present = int((grp["comparison_status"] == "Marker present").sum())
        absent = int((grp["comparison_status"] == "Listed allele absent").sum())
        missing = int((grp["comparison_status"] == "rsID not present in Ancestry file").sum())
        manual = int((grp["manual_review"] != "No").sum())
        comparable_found = int(((grp["marker_type"].isin(["rsid_single_allele", "rsid_only"])) & (grp["in_ancestry"].fillna(False))).sum())
        coverage_pct = round(100 * comparable_found / directly_comparable, 1) if directly_comparable else None
        hit_pct = round(100 * (allele_present + marker_present) / comparable_found, 1) if comparable_found else None

        summaries.append({
            "category": category,
            "rows": total,
            "directly_comparable_rows": directly_comparable,
            "present_in_ancestry": found,
            "listed_allele_present": allele_present,
            "marker_present_no_allele": marker_present,
            "listed_allele_absent": absent,
            "missing_from_ancestry": missing,
            "manual_review_rows": manual,
            "coverage_pct_of_comparable": coverage_pct,
            "match_pct_when_present": hit_pct,
        })

    summary_df = pd.DataFrame(summaries).sort_values(["category"]).reset_index(drop=True)
    return summary_df


def build_overall_metrics(summary_df: pd.DataFrame, all_results: pd.DataFrame) -> dict:
    metrics = {
        "Datasets loaded": int(summary_df["category"].nunique()) if not summary_df.empty else 0,
        "Total marker rows": int(len(all_results)),
        "Directly comparable rows": int(summary_df["directly_comparable_rows"].sum()) if not summary_df.empty else 0,
        "Present in volunteer file": int(summary_df["present_in_ancestry"].sum()) if not summary_df.empty else 0,
        "Allele/marker hits": int((summary_df["listed_allele_present"] + summary_df["marker_present_no_allele"]).sum()) if not summary_df.empty else 0,
        "Manual review rows": int(summary_df["manual_review_rows"].sum()) if not summary_df.empty else 0,
    }
    return metrics


def make_excel_report(summary_df: pd.DataFrame, all_results: pd.DataFrame, ancestry_df: pd.DataFrame) -> bytes:
    wb = Workbook()
    ws0 = wb.active
    ws0.title = "README"

    navy = PatternFill("solid", fgColor="13263A")
    gold = PatternFill("solid", fgColor="D4AF37")
    gray = PatternFill("solid", fgColor="EFEFEF")
    white_bold = Font(color="FFFFFF", bold=True)
    black_bold = Font(color="000000", bold=True)

    ws0.merge_cells("A1:F1")
    ws0["A1"] = "NONMS Genetics Comparison Report"
    ws0["A1"].fill = navy
    ws0["A1"].font = Font(color="FFFFFF", bold=True, size=16)
    ws0["A3"] = "Generated"
    ws0["B3"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    ws0["A5"] = "Important"
    ws0["B5"] = "This workbook is a pattern-comparison tool. It is not a diagnosis, clinical interpretation, or validated polygenic risk score."
    ws0["A7"] = "Input file rows"
    ws0["B7"] = len(ancestry_df)
    ws0["A8"] = "Marker rows reviewed"
    ws0["B8"] = len(all_results)
    ws0.column_dimensions["A"].width = 22
    ws0.column_dimensions["B"].width = 100
    ws0.sheet_view.showGridLines = False

    def add_df_sheet(name: str, df: pd.DataFrame):
        ws = wb.create_sheet(name[:31])
        if df.empty:
            ws["A1"] = "No rows"
            return ws
        for c_idx, col in enumerate(df.columns, 1):
            cell = ws.cell(1, c_idx, col)
            cell.fill = navy
            cell.font = white_bold
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        for r_idx, row in enumerate(df.itertuples(index=False), 2):
            for c_idx, val in enumerate(row, 1):
                ws.cell(r_idx, c_idx, val)
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:{get_column_letter(df.shape[1])}{ws.max_row}"
        ws.sheet_view.showGridLines = False
        for idx, col in enumerate(df.columns, start=1):
            width = max(len(str(col)) + 2, 12)
            sample_vals = df[col].astype(str).head(200).tolist()
            if sample_vals:
                width = max(width, min(42, int(max(len(v) for v in sample_vals) * 0.95) + 2))
            ws.column_dimensions[get_column_letter(idx)].width = min(max(width, 12), 45)
        return ws

    add_df_sheet("Category_Summary", summary_df)
    add_df_sheet("All_Results", all_results)

    matched = all_results[all_results["comparison_status"].isin(["Listed allele present", "Marker present", "Possible exact multibase match"])]
    add_df_sheet("Matched_Only", matched)

    manual = all_results[all_results["manual_review"] != "No"]
    add_df_sheet("Manual_Review", manual)

    for category in summary_df["category"].tolist():
        cat_df = all_results[all_results["category"] == category].copy()
        add_df_sheet(normalize_category_name(category), cat_df)

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def draw_pdf_header(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#0A0A0A"))
    canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#D4AF37"))
    canvas.rect(0.5 * inch, doc.pagesize[1] - 0.8 * inch, doc.pagesize[0] - inch, 0.08 * inch, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawRightString(doc.pagesize[0] - 0.6 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def make_pdf_report(summary_df: pd.DataFrame, all_results: pd.DataFrame, volunteer_filename: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.7 * inch,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleGold", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=colors.HexColor("#D4AF37")))
    styles.add(ParagraphStyle(name="BodyWhite", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.white))
    styles.add(ParagraphStyle(name="HeadingGold", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=colors.HexColor("#D4AF37"), spaceAfter=8, spaceBefore=8))

    story = []
    story.append(Paragraph("NONMS Genetics Comparison Report", styles["TitleGold"]))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph(f"Volunteer file: {volunteer_filename}", styles["BodyWhite"]))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["BodyWhite"]))
    story.append(Spacer(1, 0.18 * inch))
    story.append(Paragraph("This report is a pattern-comparison tool only. It is not a diagnosis, medical interpretation, or validated polygenic risk score.", styles["BodyWhite"]))
    story.append(Spacer(1, 0.18 * inch))

    story.append(Paragraph("Category Summary", styles["HeadingGold"]))
    summary_table_data = [["Category", "Rows", "Comparable", "Present", "Hits", "Missing", "Coverage %"]]
    for _, row in summary_df.iterrows():
        summary_table_data.append([
            str(row["category"]),
            int(row["rows"]),
            int(row["directly_comparable_rows"]),
            int(row["present_in_ancestry"]),
            int(row["listed_allele_present"] + row["marker_present_no_allele"]),
            int(row["missing_from_ancestry"]),
            "-" if pd.isna(row["coverage_pct_of_comparable"]) else f'{row["coverage_pct_of_comparable"]:.1f}',
        ])

    table = Table(summary_table_data, repeatRows=1, colWidths=[2.0 * inch, 0.65 * inch, 0.8 * inch, 0.65 * inch, 0.55 * inch, 0.7 * inch, 0.75 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D4AF37")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#111111")),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#555555")),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)

    story.append(PageBreak())

    for category in summary_df["category"].tolist():
        grp = all_results[all_results["category"] == category].copy()
        grp = grp[["raw_marker", "rsid", "listed_allele", "genotype", "comparison_status"]].head(20)
        story.append(Paragraph(category, styles["HeadingGold"]))
        story.append(Paragraph("Top rows shown below (up to 20). Full details are available in the Excel export.", styles["BodyWhite"]))
        cat_data = [["Marker", "rsID", "Allele", "Genotype", "Status"]]
        for _, r in grp.iterrows():
            cat_data.append([
                str(r["raw_marker"])[:28],
                str(r["rsid"] or ""),
                str(r["listed_allele"] or ""),
                str(r["genotype"] or ""),
                str(r["comparison_status"] or ""),
            ])
        cat_table = Table(cat_data, repeatRows=1, colWidths=[1.7 * inch, 1.1 * inch, 0.55 * inch, 0.75 * inch, 2.5 * inch])
        cat_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D4AF37")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#111111")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#555555")),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("LEADING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(cat_table)
        story.append(Spacer(1, 0.12 * inch))

    doc.build(story, onFirstPage=draw_pdf_header, onLaterPages=draw_pdf_header)
    return buffer.getvalue()


def make_csv_zip(summary_df: pd.DataFrame, all_results: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("category_summary.csv", summary_df.to_csv(index=False))
        zf.writestr("all_results.csv", all_results.to_csv(index=False))
        for category in summary_df["category"].tolist():
            cat_df = all_results[all_results["category"] == category]
            zf.writestr(f"{normalize_category_name(category)}.csv", cat_df.to_csv(index=False))
    return buffer.getvalue()


@st.cache_data
def load_datasets_cached():
    return load_all_datasets()


def main():
    st.set_page_config(page_title="NONMS Genetics Engine", layout="wide")
    st.title("NONMS Genetics Engine")
    st.caption("Upload an AncestryDNA raw file and compare it against the bundled MS and pathway marker sets.")

    with st.expander("What is included in v3?", expanded=False):
        st.write(", ".join(DISPLAY_NAMES.get(name, name) for name in DATASET_FILES))
        st.info("This app performs literal marker comparison. It does not diagnose disease or produce a validated risk score.")

    uploaded = st.file_uploader("Upload AncestryDNA raw .txt file", type=["txt"])
    if not uploaded:
        st.stop()

    ancestry_df = parse_ancestry_file(uploaded)
    if ancestry_df.empty:
        st.error("No genotype rows could be parsed from the uploaded file.")
        st.stop()

    datasets = load_datasets_cached()
    selected_categories = st.multiselect(
        "Datasets to include",
        options=[d.category for d in datasets],
        default=[d.category for d in datasets],
    )
    datasets = [d for d in datasets if d.category in selected_categories]

    result_frames = [compare_dataset(d, ancestry_df) for d in datasets]
    all_results = pd.concat(result_frames, ignore_index=True) if result_frames else pd.DataFrame()
    summary_df = build_summary(all_results) if not all_results.empty else pd.DataFrame()
    metrics = build_overall_metrics(summary_df, all_results) if not all_results.empty else {}

    cols = st.columns(6)
    for i, (label, value) in enumerate(metrics.items()):
        cols[i % 6].metric(label, value)

    tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Category Detail", "Matched Rows", "Downloads"])

    with tab1:
        st.subheader("Category summary")
        st.dataframe(summary_df, use_container_width=True)

        if not summary_df.empty:
            chart_df = summary_df.set_index("category")[["present_in_ancestry", "missing_from_ancestry", "manual_review_rows"]]
            st.bar_chart(chart_df)

    with tab2:
        categories = summary_df["category"].tolist() if not summary_df.empty else []
        chosen = st.selectbox("Choose a category", categories) if categories else None
        if chosen:
            cat_df = all_results[all_results["category"] == chosen].copy()
            st.dataframe(cat_df, use_container_width=True)
            st.caption("Tip: focus on `comparison_status`, `genotype`, and `manual_review` first.")

    with tab3:
        matched_df = all_results[all_results["comparison_status"].isin(["Listed allele present", "Marker present", "Possible exact multibase match"])].copy()
        st.dataframe(matched_df, use_container_width=True)

    with tab4:
        st.subheader("Export report files")
        excel_bytes = make_excel_report(summary_df, all_results, ancestry_df)
        pdf_bytes = make_pdf_report(summary_df, all_results, uploaded.name)
        csv_zip_bytes = make_csv_zip(summary_df, all_results)

        st.download_button(
            "Download Excel report (.xlsx)",
            data=excel_bytes,
            file_name="NONMS_Genetics_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        st.download_button(
            "Download PDF summary (.pdf)",
            data=pdf_bytes,
            file_name="NONMS_Genetics_Report.pdf",
            mime="application/pdf",
        )
        st.download_button(
            "Download CSV bundle (.zip)",
            data=csv_zip_bytes,
            file_name="NONMS_Genetics_CSVs.zip",
            mime="application/zip",
        )

        st.info("The PDF is a concise summary. The Excel export contains the full row-level detail.")

if __name__ == "__main__":
    main()
