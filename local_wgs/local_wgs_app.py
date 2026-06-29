from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from nonms_wgs.parsers.vcf import DEFAULT_TARGETS, GENE_MODULES, scan_gene_symbols_from_info, scan_targets

st.set_page_config(page_title="NONMS Local WGS Explorer", page_icon="🧬", layout="wide")

st.title("NONMS Local WGS Explorer")
st.write("Use this app on your own computer for large Sequencing.com WGS files. No browser upload required.")

vcf_path = st.text_input(
    "Path to your VCF file",
    value=r"C:\Users\dhata\Downloads\DhataHarris-SQV32F23-30x-WGS-Sequencing_com-02-02-26.snp-indel.genome.vcf",
)

with st.expander("Target rsIDs"):
    st.dataframe(pd.DataFrame([{"rsID": k, "Note": v} for k, v in DEFAULT_TARGETS.items()]), use_container_width=True)

if st.button("Scan target rsIDs"):
    p = Path(vcf_path)
    if not p.exists():
        st.error("VCF path not found. Check the path and try again.")
    else:
        with st.spinner("Scanning WGS file locally. This may take several minutes..."):
            hits, stats = scan_targets(p)
        st.success(f"Scan complete: {stats['variants']:,} variants scanned.")
        st.write(stats)
        df = pd.DataFrame(hits)
        if df.empty:
            st.warning("No target rsIDs found in the VCF.")
        else:
            st.dataframe(df, use_container_width=True)
            st.download_button("Download target hits CSV", df.to_csv(index=False), "NONMS_WGS_Target_rsID_Hits.csv")

st.markdown("---")
st.subheader("Optional: gene-symbol search")
st.caption("This only works if your VCF INFO field contains gene annotations. If it does not, we will add coordinate-based gene extraction next.")
module = st.selectbox("Gene module", list(GENE_MODULES.keys()))
genes = st.multiselect("Genes to search", GENE_MODULES[module], default=GENE_MODULES[module][:3])

if st.button("Search selected genes in INFO field"):
    p = Path(vcf_path)
    if not p.exists():
        st.error("VCF path not found.")
    else:
        with st.spinner("Searching INFO annotations..."):
            hits, stats = scan_gene_symbols_from_info(p, genes)
        st.write(stats)
        df = pd.DataFrame(hits)
        if df.empty:
            st.warning("No gene-symbol hits found. Your VCF may not be gene-annotated.")
        else:
            st.dataframe(df, use_container_width=True)
            st.download_button("Download gene hits CSV", df.to_csv(index=False), "NONMS_WGS_Gene_INFO_Hits.csv")
