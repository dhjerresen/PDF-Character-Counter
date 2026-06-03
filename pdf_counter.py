# pdf_counter.py
import re
from collections import Counter
import fitz


# ============================================================
# REGEX PATTERNS
# ============================================================
# These patterns are used to identify page numbers and
# running headers that should not be counted as content.

PAGE_NUMBER_RE = re.compile(
    r"^\s*(side\s*)?\d+\s*(/|af|-)?\s*\d*\s*$",
    re.IGNORECASE,
)

RUNNING_HEADER_RE = re.compile(
    r"^\d+(\.\d+)+\.?\s+.+\s+([ivxlcdm]+|\d+)$",
    re.IGNORECASE,
)


# ============================================================
# TEXT NORMALIZATION
# ============================================================
# Cleans extracted text by replacing multiple whitespace
# characters (spaces, tabs, line breaks) with a single space.
# This ensures consistent comparison and character counting.

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# ============================================================
# PDF EXTRACTION
# ============================================================
# Reads the PDF and extracts all text blocks from each page.
#
# For every block we store:
# - Page number
# - Original text
# - Lowercase version for comparisons
# - Vertical coordinates on the page
# - Page height
#
# The position data is later used to detect headers/footers.

def extract_pages(pdf_bytes: bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []

    for page_no, page in enumerate(doc, start=1):
        blocks = []

        for block in page.get_text("blocks", sort=True):
            x0, y0, x1, y1, text, *_ = block

            text = normalize(text)

            if text:
                blocks.append({
                    "page": page_no,
                    "text": text,
                    "text_key": text.lower(),
                    "y0": y0,
                    "y1": y1,
                    "height": page.rect.height,
                })

        pages.append(blocks)

    return pages


# ============================================================
# PAGE NUMBER DETECTION
# ============================================================
# Checks whether a text block looks like a page number.

def is_page_number(text: str) -> bool:
    return PAGE_NUMBER_RE.match(text) is not None


# ============================================================
# PAGE POSITION HELPERS
# ============================================================
# Determines whether a text block is located near the top
# or bottom of the page.
#
# Top area  = top 15%
# Bottom area = bottom 15%
#
# These areas are where headers and footers are expected.

def is_top_area(block: dict) -> bool:
    return block["y1"] <= block["height"] * 0.15


def is_bottom_area(block: dict) -> bool:
    return block["y0"] >= block["height"] * 0.85


# ============================================================
# RUNNING HEADER DETECTION
# ============================================================
# Identifies chapter-style running headers such as:
#
#   2.1 Methods 12
#   4.3 Results iv
#
# They typically appear near the top of each page and
# follow a numbering pattern.
#
# "Chapter X" headings are excluded because they are often
# actual content rather than page headers.

def is_running_header(block: dict) -> bool:
    text = block["text"]

    if text.lower().startswith("chapter "):
        return False

    return is_top_area(block) and RUNNING_HEADER_RE.match(text) is not None


# ============================================================
# HEADER / FOOTER DETECTION
# ============================================================
# Finds text that appears repeatedly in the top or bottom
# regions of many pages.
#
# Repeated top text   -> header candidate
# Repeated bottom text -> footer candidate
#
# A text must appear on at least min_ratio of pages before
# it is classified as a header/footer.
#
# Default: 50% of pages.

def detect_headers_and_footers(pages, min_ratio=0.5):
    header_counter = Counter()
    footer_counter = Counter()

    running_headers = set()
    page_numbers = set()

    for blocks in pages:
        headers_seen = set()
        footers_seen = set()

        for block in blocks:
            text = block["text"]
            text_key = block["text_key"]

            # Collect page numbers separately
            if is_page_number(text):
                page_numbers.add(text)
                continue

            # Collect running headers separately
            if is_running_header(block):
                running_headers.add(text)
                continue

            # Potential header candidate
            if is_top_area(block):
                headers_seen.add(text_key)

            # Potential footer candidate
            if is_bottom_area(block):
                footers_seen.add(text_key)

        # Count once per page
        header_counter.update(headers_seen)
        footer_counter.update(footers_seen)

    min_count = max(2, int(len(pages) * min_ratio))

    detected_headers = {
        text for text, count in header_counter.items()
        if count >= min_count
    }

    detected_footers = {
        text for text, count in footer_counter.items()
        if count >= min_count
    }

    return (
        detected_headers,
        detected_footers,
        running_headers,
        page_numbers,
    )


# ============================================================
# CHARACTER COUNTING ENGINE
# ============================================================
# Main workflow:
#
# 1. Extract all text blocks from the PDF.
# 2. Detect repeated headers and footers.
# 3. Detect page numbers.
# 4. Remove unwanted elements.
# 5. Count characters in remaining content.
# 6. Return detailed results and diagnostics.

def count_characters(
    pdf_bytes: bytes,
    excluded_pages: set[int] | None = None,
    remove_headers: bool = True,
    remove_footers: bool = True,
    remove_page_numbers: bool = True,
):
    excluded_pages = excluded_pages or set()

    # Extract all page data
    pages = extract_pages(pdf_bytes)

    # Detect recurring elements
    (
        detected_headers,
        detected_footers,
        running_headers,
        detected_page_numbers,
    ) = detect_headers_and_footers(pages)

    included_text_parts = []
    page_results = []
    removed_items = []

    # Process each page individually
    for page_no, blocks in enumerate(pages, start=1):

        # Skip pages excluded by the user
        if page_no in excluded_pages:
            page_results.append({
                "Side": page_no,
                "Tegn": 0,
                "Status": "Fravalgt",
            })
            continue

        kept_text = []

        # Evaluate every text block
        for block in blocks:
            text = block["text"]
            text_key = block["text_key"]

            # Remove page numbers
            if remove_page_numbers and is_page_number(text):
                removed_items.append({
                    "Side": page_no,
                    "Type": "Sidetal",
                    "Tekst": text,
                })
                continue

            # Remove repeated headers
            if remove_headers and text_key in detected_headers:
                removed_items.append({
                    "Side": page_no,
                    "Type": "Sidehoved",
                    "Tekst": text,
                })
                continue

            # Remove running chapter headers
            if remove_headers and is_running_header(block):
                removed_items.append({
                    "Side": page_no,
                    "Type": "Løbende sidehoved",
                    "Tekst": text,
                })
                continue

            # Remove repeated footers
            if remove_footers and text_key in detected_footers:
                removed_items.append({
                    "Side": page_no,
                    "Type": "Sidefod",
                    "Tekst": text,
                })
                continue

            # Keep everything else
            kept_text.append(text)

        # Combine all remaining text on the page
        page_text = " ".join(kept_text)

        included_text_parts.append(page_text)

        # Store page statistics
        page_results.append({
            "Side": page_no,
            "Tegn": len(page_text),
            "Status": "Talt med",
        })

    # Combine text from all included pages
    full_text = " ".join(
        t for t in included_text_parts if t
    )

    # Return complete result package
    return {
        "total_characters": len(full_text),
        "page_results": page_results,
        "included_text": full_text,

        # Diagnostic information
        "detected_headers": sorted(detected_headers),
        "detected_footers": sorted(detected_footers),
        "detected_running_headers": sorted(running_headers),
        "detected_page_numbers": sorted(detected_page_numbers),

        # Log of removed items
        "removed_items": removed_items,

        # Total pages in document
        "page_count": len(pages),
    }