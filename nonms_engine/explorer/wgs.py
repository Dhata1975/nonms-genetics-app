from __future__ import annotations

import pandas as pd
import streamlit as st

from nonms_engine.parsers.vcf import GENE_MODULES, TARGET_RSIDS, scan_uploaded_vcf


def render_wgs_explorer() -> None:
    st.title("NONMS WGS / VCF Explorer")
    st.write(
        "Upload a Sequencing.com `.vcf` or `.vcf.gz` file. "
        "This tool streams the file and checks selected NONMS target rsIDs without loading the entire genome into memory."
    )
    st.warning(
        "Research/education only. This is not medical interpretation. "
        "A ~1 GB VCF can take several minutes to upload and scan."
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Supported", ".vcf / .vcf.gz")
    col2.metric("First target", "FER rs4957796")
    col3.metric("Mode", "streaming scan")

    with st.expander("Target rsIDs currently checked", expanded=False):
        st.dataframe(
            pd.DataFrame([{"rsID": k, "Why included": v} for k, v in TARGET_RSIDS.items()]),
            use_container_width=True,
        )

    with st.expander("Disease-tolerance gene modules planned for full gene extraction", expanded=False):
        rows = []
        for module, genes in GENE_MODULES.items():
            for gene in genes:
                rows.append({"Module": module, "Gene": gene})
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

    uploaded = st.file_uploader(
        "Upload Sequencing.com / WGS VCF file",
        type=["vcf", "gz"],
        key="v10_wgs_vcf_upload",
    )

    if not uploaded:
        st.info("Upload your Sequencing.com VCF to begin. Start by scanning for FER rs4957796 and the first NONMS target set.")
        return

    st.caption(f"Selected file: {uploaded.name}")

    if st.button("Scan VCF for NONMS target rsIDs", type="primary"):
        with st.spinner("Scanning VCF. Please wait — large WGS files can take several minutes."):
            result = scan_uploaded_vcf(uploaded)

        st.success(f"Scan complete: {result['total_variants_scanned']:,} variants scanned.")
        st.caption(f"rsID-bearing variants scanned: {result['rsid_variants_scanned']:,}")

        hits = pd.DataFrame(result["hits"])
        if hits.empty:
            st.warning(
                "No target rsID hits found. This may mean the VCF lacks rsIDs for these sites, "
                "uses different IDs, or does not include those variants as non-reference calls."
            )
        else:
            st.subheader("Target rsID hits")
            st.dataframe(hits, use_container_width=True)
            st.download_button(
                "Download VCF target hits CSV",
                data=hits.to_csv(index=False).encode("utf-8"),
                file_name="NONMS_VCF_Target_rsID_Hits.csv",
                mime="text/csv",
            )

        preview = pd.DataFrame(result["preview"])
        with st.expander("VCF preview rows", expanded=False):
            st.dataframe(preview, use_container_width=True)
