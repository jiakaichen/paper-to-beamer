#!/usr/bin/env python3
"""
inspect_pdf.py — Quick content inventory for an academic PDF.

Usage:
    python inspect_pdf.py <path-to-pdf>

Prints:
    - Page count and file size
    - Whether text is extractable (or scanned)
    - First-page text sample
    - List of embedded raster images
    - Suggested pages likely containing tables/figures
"""

import subprocess
import sys
import os
import re


def run(cmd: list[str], fallback: str = "") -> str:
    """Run a command and return stdout, or fallback on error."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return fallback


def inspect_pdf(pdf_path: str) -> None:
    if not os.path.isfile(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)

    size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
    print(f"{'=' * 60}")
    print(f"PDF Inspection: {os.path.basename(pdf_path)}")
    print(f"File size: {size_mb:.2f} MB")
    print(f"{'=' * 60}")

    # --- Page count and metadata ---
    info = run(["pdfinfo", pdf_path])
    if info:
        print(f"\n--- PDF Info ---")
        for line in info.splitlines():
            if any(k in line.lower() for k in ["pages", "page size", "title", "author", "creator"]):
                print(f"  {line.strip()}")

    # --- Text extractability check ---
    sample = run(["pdftotext", "-f", "1", "-l", "1", pdf_path, "-"])
    print(f"\n--- Text Extractability ---")
    if len(sample.strip()) > 50:
        print("  ✓ Text is extractable")
        # Show first 200 chars
        preview = sample.strip()[:200].replace("\n", " ")
        print(f"  Preview: {preview}...")
    else:
        print("  ✗ Little or no extractable text (possibly scanned)")
        print("  → Rasterize pages and use visual inspection")

    # --- Embedded images ---
    img_list = run(["pdfimages", "-list", pdf_path])
    if img_list:
        lines = img_list.strip().splitlines()
        # Count actual image entries (skip header lines)
        img_entries = [l for l in lines[2:] if l.strip()]
        print(f"\n--- Embedded Images ---")
        print(f"  Total embedded raster images: {len(img_entries)}")
        if len(img_entries) > 0 and len(img_entries) <= 20:
            print("  (Detailed list)")
            for l in lines[:2]:  # Header
                print(f"  {l}")
            for l in img_entries[:15]:
                print(f"  {l}")
            if len(img_entries) > 15:
                print(f"  ... and {len(img_entries) - 15} more")

    # --- Scan for table / figure references ---
    print(f"\n--- Table / Figure Detection ---")
    full_text = run(["pdftotext", "-layout", pdf_path, "-"])
    if full_text:
        # Detect by page using form feeds
        pages = full_text.split("\f")
        table_pages = []
        figure_pages = []

        table_pattern = re.compile(
            r"\b(?:TABLE|Table|Tab\.)\s+[IVXLCDM0-9]+\b"
        )
        figure_pattern = re.compile(
            r"\b(?:FIGURE|Figure|Fig\.)\s+[IVXLCDM0-9]+\b"
        )

        for i, page_text in enumerate(pages, start=1):
            tables = table_pattern.findall(page_text)
            figures = figure_pattern.findall(page_text)
            if tables:
                # Check if this looks like a table header (not just a reference)
                # Heuristic: table is "on" this page if label appears near the top
                for t in set(tables):
                    table_pages.append((i, t))
            if figures:
                for f in set(figures):
                    figure_pages.append((i, f))

        if table_pages:
            print("  Tables found (page, label):")
            seen = set()
            for pg, label in table_pages:
                key = (pg, label)
                if key not in seen:
                    print(f"    Page {pg}: {label}")
                    seen.add(key)
        else:
            print("  No table labels detected (try visual inspection)")

        if figure_pages:
            print("  Figures found (page, label):")
            seen = set()
            for pg, label in figure_pages:
                key = (pg, label)
                if key not in seen:
                    print(f"    Page {pg}: {label}")
                    seen.add(key)
        else:
            print("  No figure labels detected")

        # Suggest rasterization range
        all_visual_pages = sorted(set(
            pg for pg, _ in table_pages + figure_pages
        ))
        if all_visual_pages:
            lo, hi = min(all_visual_pages), max(all_visual_pages)
            print(f"\n  Suggested rasterization range: pages {lo}–{hi}")
            print(f"  Command:")
            print(f"    pdftoppm -jpeg -r 300 -f {lo} -l {hi} \"{pdf_path}\" /tmp/pages")
    else:
        print("  Could not extract text for scanning.")

    print(f"\n{'=' * 60}")
    print("Inspection complete.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_pdf.py <path-to-pdf>")
        sys.exit(1)
    inspect_pdf(sys.argv[1])
