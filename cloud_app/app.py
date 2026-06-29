from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="NONMS Genetics Engine Cloud",
    page_icon="🧬",
    layout="wide",
)

def main() -> None:
    st.sidebar.title("NONMS")
    mode = st.sidebar.radio("Mode", ["Volunteer Genetics Engine"], index=0)
    if mode == "Volunteer Genetics Engine":
        try:
            import legacy_app
            legacy_app.main()
        except Exception as exc:
            st.error("The volunteer genetics engine could not load.")
            st.exception(exc)

if __name__ == "__main__":
    main()
