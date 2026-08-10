#!/usr/bin/env python3
"""Render PDF pages and extract any embedded text into a reviewable JSON file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf


def clean_text(value: str) -> str:
    return " ".join(value.replace("\u00a0", " ").split())


def page_blocks(page: pymupdf.Page) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        lines = []
        for line in block.get("lines", []):
            value = clean_text("".join(span.get("text", "") for span in line.get("spans", [])))
            if value:
                lines.append(value)
        text = "\n".join(lines)
        if text:
            result.append(
                {
                    "bbox": [round(value, 2) for value in block["bbox"]],
                    "text": text,
                }
            )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_pdf", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--max-pixels-wide", type=int, default=12000)
    args = parser.parse_args()

    if not args.input_pdf.is_file():
        raise SystemExit(f"PDF not found: {args.input_pdf}")
    if args.dpi < 72:
        raise SystemExit("--dpi must be at least 72")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    document = pymupdf.open(args.input_pdf)
    pages: list[dict[str, object]] = []
    total_chars = 0

    for index, page in enumerate(document, start=1):
        blocks = page_blocks(page)
        embedded_text = "\n".join(block["text"] for block in blocks)
        total_chars += len(embedded_text)
        nominal_scale = args.dpi / 72
        scale = min(nominal_scale, args.max_pixels_wide / page.rect.width)
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
        image_name = f"page-{index:03d}.png"
        pixmap.save(args.output_dir / image_name)
        pages.append(
            {
                "page": index,
                "pdf_size_points": [round(page.rect.width, 2), round(page.rect.height, 2)],
                "rendered_image": image_name,
                "embedded_text_characters": len(embedded_text),
                "blocks": blocks,
            }
        )

    payload = {
        "input_pdf": str(args.input_pdf.resolve()),
        "page_count": document.page_count,
        "embedded_text_characters": total_chars,
        "pages": pages,
    }
    output_json = args.output_dir / "extraction.json"
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mode = "embedded text found" if total_chars else "raster-only; inspect rendered PNGs visually"
    print(f"Wrote {output_json}")
    print(f"Rendered {document.page_count} page(s): {mode}")


if __name__ == "__main__":
    main()
