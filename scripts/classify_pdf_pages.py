#!/usr/bin/env python3
"""
Classifies PDF pages as "image" (portrait/illustration, little to no
extractable text) or "text" (article/narrative content) using pdftotext
alone - no page rendering, no vision-model image reads.

Why this exists: manually reading every candidate page as an image to
figure out which ones are portraits costs a full vision-token read per
page. For a book-scale PDF (100+ pages) that adds up fast in both tokens
and wall-clock time. A text-only pass is nearly free and, for atlas-style
PDFs where portrait pages carry a decorative frame but no body text, it's
a reliable signal: pages with substantial extracted text are article
pages, pages with near-empty extraction are the illustration pages.

Usage:
    python3 scripts/classify_pdf_pages.py <pdf_path> <first_page> <last_page> [--threshold N]

Output: one line per page, e.g.:
    5   IMAGE   (12 chars)
    6   TEXT    (3184 chars)

Only render/read the pages classified as IMAGE when doing visual
verification or cropping - skip full-image reads for TEXT pages entirely.
"""
import argparse
import subprocess


def extracted_text_length(pdf_path: str, page: int) -> int:
    out = subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(page), pdf_path, "-"],
        capture_output=True, text=True,
    ).stdout
    return len(out.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf_path")
    ap.add_argument("first_page", type=int)
    ap.add_argument("last_page", type=int)
    ap.add_argument("--threshold", type=int, default=150,
                     help="Pages with fewer extracted characters than this are classified IMAGE.")
    args = ap.parse_args()

    for page in range(args.first_page, args.last_page + 1):
        n = extracted_text_length(args.pdf_path, page)
        label = "IMAGE" if n < args.threshold else "TEXT"
        print(f"{page:4d}  {label:5s}  ({n} chars)")


if __name__ == "__main__":
    main()
