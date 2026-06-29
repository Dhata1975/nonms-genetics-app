from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from nonms_wgs.parsers.vcf import (
    DEFAULT_TARGETS,
    GENE_MODULES,
    resolve_vcf_path,
    scan_gene_symbols_from_info,
    scan_targets,
    validate_vcf,
)

st.set_page_config(page_title="NONMS Genome Research Lab", page_icon="🧬", layout="wide")

st.title("NONMS Genome Research Lab")
st.write("Local whole-genome explorer for Sequencing.com WGS files. No browser upload required.")

default_path = r"C:\Users\dhata\Downloads\DhataHarris-SQV32F23-30x-WGS-Sequencing_com-02-02-26.snp-indel.genome.vcf"

vcf_path = st.text_input(
    "Path to your VCF file OR Sequencing.com export folder",
    value=default_path,
    help="You may paste the outer Sequencing.com folder path. The app will automatically locate the real .vcf file inside.",
)

col_a, col_b, col_c = st.columns(3)

if col_a.button("Validate genome path"):
    try:
        info = validate_vcf(vcf_path)
        st.success("Genome path validated.")
        st.write({
            "Resolved path": info["resolved_path"],
            "Size MB": round(info["size_bytes"] / 1024 / 1024, 2),
            "File format": info["fileformat"],
            "Reference": info["reference"],
            "Source": info["source"],
        })
        with st.expander("First VCF header lines"):
            st.text("\n".join(info["first_lines"][:25]))
    except Exception as exc:
        st.error("Could not validate this path.")
        st.exception(exc)

with st.expander("Target rsIDs"):
    st.dataframe(pd.DataFrame([{"rsID": k, "Note": v} for k, v in DEFAULT_TARGETS.items()]), use_container_width=True)

if col_b.button("Scan target rsIDs"):
    try:
        resolved = resolve_vcf_path(vcf_path)
        with st.spinner(f"Scanning {resolved}. This may take several minutes..."):
            hits, stats = scan_targets(resolved)
        st.success(f"Scan complete: {stats['variants']:,} variants scanned.")
        st.write(stats)
        df = pd.DataFrame(hits)
        if df.empty:
            st.warning("No target rsIDs found in the VCF. This may mean those sites were reference calls not listed as variants, or IDs are absent.")
        else:
            st.subheader("Target rsID hits")
            st.dataframe(df, use_container_width=True)
            st.download_button("Download target hits CSV", df.to_csv(index=False), "NONMS_WGS_Target_rsID_Hits.csv")
    except Exception as exc:
        st.error("Target scan failed.")
        st.exception(exc)

if col_c.button("Show resolved file"):
    try:
        st.info(str(resolve_vcf_path(vcf_path)))
    except Exception as exc:
        st.error("Could not resolve file.")
        st.exception(exc)

st.markdown("---")
st.subheader("Gene / pathway search")
st.caption("This first version searches gene symbols in the VCF INFO field. If your VCF is not gene-annotated, the next upgrade will add coordinate-based extraction.")

module = st.selectbox("Gene module", list(GENE_MODULES.keys()))
genes = st.multiselect("Genes to search", GENE_MODULES[module], default=GENE_MODULES[module][:3])

if st.button("Search selected genes in INFO field"):
    try:
        resolved = resolve_vcf_path(vcf_path)
        with st.spinner("Searching INFO annotations..."):
            hits, stats = scan_gene_symbols_from_info(resolved, genes)
        st.write(stats)
        df = pd.DataFrame(hits)
        if df.empty:
            st.warning("No gene-symbol hits found. Your VCF may not be gene-annotated. That is normal for many raw VCFs.")
        else:
            st.dataframe(df, use_container_width=True)
            st.download_button("Download gene hits CSV", df.to_csv(index=False), "NONMS_WGS_Gene_INFO_Hits.csv")
    except Exception as exc:
        st.error("Gene search failed.")
        st.exception(exc)
