#!/usr/bin/env python3
"""
PDF Reader — extracts text and renders scanned pages as images.
Usage: python3 pdf_reader.py <path_to_pdf>
Output goes to ~/.openclaw/workspace/pdf_inbox/<pdf_name>/
"""

import sys
import os
import fitz  # PyMuPDF

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
INBOX = os.path.join(WORKSPACE, "pdf_inbox")

MIN_TEXT_LENGTH = 50  # pages with fewer chars are treated as scanned


def process_pdf(pdf_path):
    pdf_path = os.path.abspath(pdf_path)
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        sys.exit(1)

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_dir = os.path.join(INBOX, pdf_name)
    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    text_pages = 0
    image_pages = 0
    all_text = []

    for i, page in enumerate(doc):
        page_num = i + 1
        text = page.get_text().strip()

        if len(text) >= MIN_TEXT_LENGTH:
            all_text.append(f"--- Page {page_num} ---\n{text}\n")
            text_pages += 1
        else:
            # Render as image (scanned or image-heavy page)
            pix = page.get_pixmap(dpi=200)
            img_path = os.path.join(output_dir, f"page_{page_num}.png")
            pix.save(img_path)
            all_text.append(f"--- Page {page_num} --- [Rendered as image: page_{page_num}.png]\n")
            image_pages += 1

    # Save extracted text
    txt_path = os.path.join(output_dir, f"{pdf_name}.txt")
    with open(txt_path, "w") as f:
        f.write("\n".join(all_text))

    # Also copy original PDF to inbox
    import shutil
    dest_pdf = os.path.join(output_dir, os.path.basename(pdf_path))
    if os.path.abspath(pdf_path) != os.path.abspath(dest_pdf):
        shutil.copy2(pdf_path, dest_pdf)

    print(f"✅ PDF processed: {os.path.basename(pdf_path)}")
    print(f"   Pages: {total_pages} total, {text_pages} text, {image_pages} rendered as images")
    print(f"   Output: {output_dir}")
    return output_dir


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 pdf_reader.py <path_to_pdf>")
        sys.exit(1)
    process_pdf(sys.argv[1])
