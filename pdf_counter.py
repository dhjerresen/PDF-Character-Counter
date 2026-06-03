import re
from collections import Counter
import fitz

PAGE_NUMBER_RE = re.compile(r"^\s*(side\s*)?\d+\s*(/|af)?\s*\d*\s*$", re.I)

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

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
                    "y0": y0,
                    "y1": y1,
                    "height": page.rect.height,
                })
        pages.append(blocks)

    return pages

def find_repeated_margin_text(pages, top_pct=0.12, bottom_pct=0.12, min_ratio=0.5):
    counter = Counter()

    for blocks in pages:
        seen = set()
        for b in blocks:
            h = b["height"]
            text = normalize(b["text"]).lower()

            in_top = b["y1"] <= h * top_pct
            in_bottom = b["y0"] >= h * (1 - bottom_pct)

            if (in_top or in_bottom) and not PAGE_NUMBER_RE.match(text):
                seen.add(text)

        counter.update(seen)

    min_count = max(2, int(len(pages) * min_ratio))
    return {text for text, count in counter.items() if count >= min_count}

def count_characters(
    pdf_bytes: bytes,
    excluded_pages: set[int] | None = None,
    top_margin_pct: float = 0.08,
    bottom_margin_pct: float = 0.08,
    remove_repeated: bool = True,
):
    excluded_pages = excluded_pages or set()
    pages = extract_pages(pdf_bytes)
    repeated = find_repeated_margin_text(pages) if remove_repeated else set()

    page_results = []
    included_text_parts = []

    for page_no, blocks in enumerate(pages, start=1):
        if page_no in excluded_pages:
            page_results.append({
                "page": page_no,
                "characters": 0,
                "status": "Fravalgt",
            })
            continue

        kept = []

        for b in blocks:
            h = b["height"]
            text = normalize(b["text"])
            text_key = text.lower()

            if b["y1"] <= h * top_margin_pct:
                continue
            if b["y0"] >= h * (1 - bottom_margin_pct):
                continue
            if PAGE_NUMBER_RE.match(text):
                continue
            if text_key in repeated:
                continue

            kept.append(text)

        page_text = " ".join(kept)
        included_text_parts.append(page_text)

        page_results.append({
            "page": page_no,
            "characters": len(page_text),
            "status": "Talt med",
        })

    full_text = " ".join(t for t in included_text_parts if t)

    return {
        "total_characters": len(full_text),
        "page_results": page_results,
        "included_text": full_text,
        "page_count": len(pages),
    }