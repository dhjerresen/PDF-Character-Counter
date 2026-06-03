import streamlit as st
import fitz
from pdf_counter import count_characters

st.set_page_config(page_title="PDF tegntæller", layout="centered")

st.title("PDF tegntæller")

uploaded = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded:
    pdf_bytes = uploaded.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = len(doc)

    excluded_pages = st.multiselect(
        "Fravælg sider",
        options=list(range(1, page_count + 1)),
    )

    top_margin_pct = st.slider("Ignorér topområde (%)", 0, 25, 8) / 100
    bottom_margin_pct = st.slider("Ignorér bundområde (%)", 0, 25, 8) / 100

    remove_repeated = st.checkbox(
        "Fjern gentagne sidehoveder/sidefødder",
        value=True,
    )

    result = count_characters(
        pdf_bytes=pdf_bytes,
        excluded_pages=set(excluded_pages),
        top_margin_pct=top_margin_pct,
        bottom_margin_pct=bottom_margin_pct,
        remove_repeated=remove_repeated,
    )

    st.metric(
        "Antal tegn inkl. mellemrum",
        f"{result['total_characters']:,}".replace(",", "."),
    )

    st.dataframe(result["page_results"], use_container_width=True)

    with st.expander("Se tekst der er talt med"):
        st.text_area("Tekst", result["included_text"], height=300)