import streamlit as st
import fitz

from pdf_counter import count_characters


# ============================================================
# PAGE CONFIGURATION
# ============================================================
# Sets the browser tab title and makes the app use the full
# available screen width.

st.set_page_config(
    page_title="PDF Character Counter",
    layout="wide",
)


# ============================================================
# APP TITLE AND DESCRIPTION
# ============================================================
# Displays the main heading and short explanation of the app.

st.title("PDF Character Counter")
st.write(
    "Counts characters including spaces and can automatically remove headers, footers, and page numbers."
)


# ============================================================
# PDF UPLOAD
# ============================================================
# Allows the user to upload a PDF file.

uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"],
)


# ============================================================
# MAIN APP LOGIC
# ============================================================
# Runs only after the user has uploaded a PDF.

if uploaded_file:

    # Read the uploaded PDF as bytes.
    pdf_bytes = uploaded_file.read()

    # Open the PDF with PyMuPDF so we can count the pages.
    doc = fitz.open(
        stream=pdf_bytes,
        filetype="pdf",
    )

    page_count = len(doc)

    # --------------------------------------------------------
    # SETTINGS SECTION
    # --------------------------------------------------------
    # Lets the user choose pages to exclude and whether headers,
    # footers, and page numbers should be removed.

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

    # --------------------------------------------------------
    # CHARACTER COUNTING
    # --------------------------------------------------------
    # Sends the uploaded PDF and selected settings to the
    # counting function in pdf_counter.py.

    result = count_characters(
        pdf_bytes=pdf_bytes,
        excluded_pages=set(excluded_pages),
        remove_headers=remove_headers,
        remove_footers=remove_footers,
        remove_page_numbers=remove_page_numbers,
    )

    st.divider()

    # --------------------------------------------------------
    # TOTAL CHARACTER COUNT
    # --------------------------------------------------------
    # Displays the total number of characters counted.

    st.metric(
        "Characters including spaces",
        f"{result['total_characters']:,}".replace(",", "."),
    )

    st.divider()

    # --------------------------------------------------------
    # REMOVED ELEMENTS SUMMARY
    # --------------------------------------------------------
    # Splits removed elements into headers, footers, and
    # page numbers so they can be shown separately.

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

    # --------------------------------------------------------
    # REMOVED HEADERS TABLE
    # --------------------------------------------------------
    # Shows the specific header elements that were removed.

    with st.expander("Show removed headers"):

        if removed_headers:
            st.dataframe(
                removed_headers,
                use_container_width=True,
            )
        else:
            st.info("No headers were removed.")

    # --------------------------------------------------------
    # REMOVED FOOTERS TABLE
    # --------------------------------------------------------
    # Shows the specific footer elements that were removed.

    with st.expander("Show removed footers"):

        if removed_footers:
            st.dataframe(
                removed_footers,
                use_container_width=True,
            )
        else:
            st.info("No footers were removed.")

    # --------------------------------------------------------
    # REMOVED PAGE NUMBERS TABLE
    # --------------------------------------------------------
    # Shows the specific page numbers that were removed.

    with st.expander("Show removed page numbers"):

        if removed_page_numbers:
            st.dataframe(
                removed_page_numbers,
                use_container_width=True,
            )
        else:
            st.info("No page numbers were removed.")

    st.divider()

    # --------------------------------------------------------
    # PAGE-BY-PAGE RESULTS
    # --------------------------------------------------------
    # Displays the character count for each page.

    st.subheader("Result per page")

    st.dataframe(
        result["page_results"],
        use_container_width=True,
    )

    st.divider()

    # --------------------------------------------------------
    # INCLUDED TEXT PREVIEW
    # --------------------------------------------------------
    # Lets the user inspect the exact text that was included
    # in the final character count.

    with st.expander("View text included in the count"):

        st.text_area(
            "Text",
            result["included_text"],
            height=400,
        )

    # --------------------------------------------------------
    # TEXT DOWNLOAD
    # --------------------------------------------------------
    # Allows the user to download the counted text as a TXT file.

    st.download_button(
        label="Download text as TXT",
        data=result["included_text"],
        file_name="counted_text.txt",
        mime="text/plain",
    )