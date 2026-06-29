from __future__ import annotations

import streamlit as st

from nonms_engine.explorer.wgs import render_wgs_explorer

st.set_page_config(
    page_title="NONMS Genetics Engine V10",
    page_icon="🧬",
    layout="wide",
)

def render_home() -> None:
    st.title("NONMS Genetics Engine V10")
    st.subheader("Research Edition")
    st.write(
        "Version 10 separates the original SNP-array workflow from the new WGS/VCF Explorer. "
        "Use the sidebar to choose a mode."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Genetics Engine")
        st.write("Use the Version 9 workflow for AncestryDNA, 23andMe, and MyHeritage reports.")
    with col2:
        st.markdown("### WGS / VCF Explorer")
        st.write("Upload Sequencing.com VCF files and scan for disease-tolerance candidates such as FER rs4957796.")

    st.info("Start with **WGS / VCF Explorer** if your goal is to upload the 974 MB Sequencing.com file.")

def run_legacy_v9() -> None:
    try:
        import legacy_app
        if hasattr(legacy_app, "main"):
            legacy_app.main()
        else:
            st.error("The legacy V9 app was found, but no main() function exists.")
    except Exception as exc:
        st.error("Legacy V9 Genetics Engine could not load.")
        st.exception(exc)

def main() -> None:
    mode = st.sidebar.radio(
        "NONMS Mode",
        ["Home", "WGS / VCF Explorer", "Legacy V9 Genetics Engine"],
        index=0,
    )

    if mode == "Home":
        render_home()
    elif mode == "WGS / VCF Explorer":
        render_wgs_explorer()
    else:
        run_legacy_v9()

if __name__ == "__main__":
    main()
