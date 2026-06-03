# app.py
import streamlit as st
import fitz

from pdf_counter import count_characters


st.set_page_config(
    page_title="PDF Character Counter",
    layout="wide",
)

st.title("PDF Character Counter")
st.write(
    "Counts characters including spaces and can automatically remove headers, footers, and page numbers."
)

uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"],
)

if uploaded_file:
    pdf_bytes = uploaded_file.read()

    doc = fitz.open(
        stream=pdf_bytes,
        filetype="pdf",
    )

    page_count = len(doc)

    st.subheader("Settings")

    excluded_pages = st.multiselect(
        "Exclude pages",
        options=list(range(1, page_count + 1)),
        default=[],
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        remove_headers = st.checkbox(
            "Remove headers",
            value=True,
        )

    with col2:
        remove_footers = st.checkbox(
            "Remove footers",
            value=True,
        )

    with col3:
        remove_page_numbers = st.checkbox(
            "Remove page numbers",
            value=True,
        )

    characters_per_normal_page = st.number_input(
        "Tegn pr. normalside",
        min_value=1,
        value=2400,
        step=100,
    )

    result = count_characters(
        pdf_bytes=pdf_bytes,
        excluded_pages=set(excluded_pages),
        remove_headers=remove_headers,
        remove_footers=remove_footers,
        remove_page_numbers=remove_page_numbers,
    )

    normal_pages = result["total_characters"] / characters_per_normal_page

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Characters including spaces",
            f"{result['total_characters']:,}".replace(",", "."),
        )

    with col2:
        st.metric(
            "Normalsider",
            f"{normal_pages:.2f}".replace(".", ","),
        )

    st.divider()

    st.subheader("Elements removed from the count")

    removed_items = result["removed_items"]

    removed_headers = [
        item
        for item in removed_items
        if item["Type"] in ["Sidehoved", "Løbende sidehoved"]
    ]

    removed_footers = [
        item
        for item in removed_items
        if item["Type"] == "Sidefod"
    ]

    removed_page_numbers = [
        item
        for item in removed_items
        if item["Type"] == "Sidetal"
    ]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Headers removed",
            len(removed_headers),
        )

    with col2:
        st.metric(
            "Footers removed",
            len(removed_footers),
        )

    with col3:
        st.metric(
            "Page numbers removed",
            len(removed_page_numbers),
        )

    with st.expander("Show removed headers"):
        if removed_headers:
            st.dataframe(
                removed_headers,
                use_container_width=True,
            )
        else:
            st.info("No headers were removed.")

    with st.expander("Show removed footers"):
        if removed_footers:
            st.dataframe(
                removed_footers,
                use_container_width=True,
            )
        else:
            st.info("No footers were removed.")

    with st.expander("Show removed page numbers"):
        if removed_page_numbers:
            st.dataframe(
                removed_page_numbers,
                use_container_width=True,
            )
        else:
            st.info("No page numbers were removed.")

    st.divider()

    st.subheader("Result per page")

    st.dataframe(
        result["page_results"],
        use_container_width=True,
    )

    st.divider()

    with st.expander("View text included in the count"):
        st.text_area(
            "Text",
            result["included_text"],
            height=400,
        )

    st.download_button(
        label="Download text as TXT",
        data=result["included_text"],
        file_name="counted_text.txt",
        mime="text/plain",
    )