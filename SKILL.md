---
name: shareholder-pdf-to-pptx
description: Rebuild a shareholder, equity-penetration, ownership, or corporate-control chart from a PDF into a native editable PowerPoint (.pptx). Use when the input is a PDF, including a rasterized screenshot with no selectable text, and the requested result needs individually editable nodes, labels, percentages, and connectors rather than a pasted image.
---

# Editable multi-level ownership chart from PDF

Produce a PowerPoint containing native, individually editable shapes, text boxes, percentage labels, buses, and connectors. Treat the PDF as evidence for the complete visible relationship graph, not as artwork to trace or flatten.

This skill is self-contained. Use only the Python programs shipped in this skill for extraction, validation, PowerPoint generation, and preview rendering. Do not load or call another PowerPoint/presentation skill, Node.js, `@oai/artifact-tool`, ImageGen, or an image-to-slide converter.

## Workflow

1. Create a temporary working directory and run `scripts/extract_pdf.py INPUT.pdf --output-dir WORK/extraction`. It creates a full-page PNG for every PDF page and `extraction.json` with any embedded text and coordinates.
2. Inspect every rendered PNG at full resolution. When `embedded_text_characters` is zero, the PDF is a raster screenshot: read it visually and do not claim OCR/text extraction. Crop or zoom the PNG when small labels cannot be read confidently.
3. Create `graph.json` using `references/graph-schema.md`. Capture every visible level, node, direct relationship, percentage, actual-controller badge, and collapsed `+` marker. Never flatten a penetration chart to only the shareholders directly above the final company.
4. When the same legal person/entity is drawn separately in multiple branches, create separate display-node IDs with the same `entity_key` and label. This preserves the PDF's branch structure and prevents cross-chart connector lines. Do not invent entities hidden behind a collapsed `+` marker.
5. Run `scripts/validate_graph.py graph.json`. Resolve every error; review holding-sum and structural warnings against the PDF before rendering.
6. Generate the PowerPoint with this skill's Python renderer:

```bash
python "$SKILL_DIR/scripts/render_pptx.py" \
  --input "$WORK/graph.json" \
  --output "$OUTPUT_PPTX"

python "$SKILL_DIR/scripts/render_preview.py" "$OUTPUT_PPTX" \
  --output-dir "$WORK/preview"
```

7. Inspect every preview PNG at full size. Check that all visible PDF levels and repeated branch nodes exist, every percentage is attached to the correct branch, connectors point from shareholder to investee, long names are readable, and no line crosses a node label. Correct `graph.json` and rerun the same Python scripts when needed.

## Output contract

- Reproduce the PDF's visible hierarchy completely; omission of an upstream level is a failed conversion.
- Use native rectangles/ellipses, text boxes, lines, buses, and PowerPoint connectors. Do not insert the PDF page, a screenshot, or a flattened SVG as the chart.
- Keep the arrow direction as `shareholder → investee`.
- Use `tag` for editable labels such as `GP`, `LP`, or the actual-controller/beneficial-owner badge.
- Use `collapsed: true` only when the source explicitly shows a collapsed `+` marker.
- Use `entity_key` to associate repeated display nodes representing the same subject; keep their `id` values unique.
- Prefer explicit `level` and `order` copied from the source. The renderer also computes top-down levels when they are omitted.
- Do not claim that a raster-only PDF was text-extracted. Flag low-confidence transcription items in `notes`.

## Local Python environment

Create the isolated environment with `conda env create -f environment.yml`, or install the listed packages in an existing Conda environment. In mainland-China environments, use the Tsinghua PyPI mirror (`https://pypi.tuna.tsinghua.edu.cn/simple`) for pip packages. On macOS, `render_preview.py` uses Quick Look so Chinese fonts match the local Office view; on other platforms it falls back to LibreOffice/`soffice`. Generation of the editable PPTX itself needs neither preview backend.

## Resources

- `scripts/extract_pdf.py` renders pages and extracts embedded PDF text.
- `scripts/validate_graph.py` validates multi-level graph data, level direction, and cycles.
- `scripts/render_pptx.py` creates the editable PowerPoint using only `python-pptx`.
- `scripts/render_preview.py` renders the generated PPTX through macOS Quick Look or LibreOffice/PyMuPDF for visual QA.
- `references/graph-schema.md` defines the complete multi-level handoff JSON.
