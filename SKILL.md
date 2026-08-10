---
name: shareholder-pdf-to-pptx
description: Rebuild a shareholder, equity-penetration, ownership, or corporate-control chart from a PDF into a native editable PowerPoint (.pptx). Use when the input is a PDF, including a rasterized screenshot with no selectable text, and the requested result needs individually editable nodes, labels, percentages, and connectors rather than a pasted image.
---

# Editable ownership chart from PDF

Produce one PowerPoint slide containing native shapes and connectors. Treat the PDF as evidence for the relationship graph, not as artwork to trace.

## Workflow

1. Create a temporary working directory and run `scripts/extract_pdf.py INPUT.pdf --output-dir WORK/extraction`. It creates a PNG for every PDF page and `extraction.json` with any embedded text and coordinates.
2. Inspect the rendered PNGs. When `embedded_text_characters` is zero, the PDF is a raster screenshot: use visual reading of the PNG; do not invent unreadable company names or percentages.
3. Create `graph.json` using `references/graph-schema.md`. Encode each direct holding from shareholder (`from`) to investee (`to`), with the holding percentage in `holding`. Preserve uncertainty in `confidence` and `notes` rather than silently guessing.
4. Run `scripts/validate_graph.py graph.json`. Resolve every error; review holding-sum warnings against the PDF before rendering.
5. Use the bundled Codex presentation runtime. Set `PRESENTATIONS_SKILL_DIR` to the installed `presentations` skill directory, then run:

```bash
node "$PRESENTATIONS_SKILL_DIR/container_tools/setup_artifact_tool_workspace.mjs" \
  --workspace "$WORK/render-workspace"
cp "$SKILL_DIR/scripts/render_pptx.mjs" "$WORK/render-workspace/"
node "$WORK/render-workspace/render_pptx.mjs" \
  --input "$WORK/graph.json" \
  --output "$OUTPUT_PPTX" \
  --preview "$WORK/preview.png" \
  --audit "$WORK/render-audit.ndjson"
```

6. Inspect the preview at full size. Check text wrapping, each percentage, connector direction, and that no relationship line crosses a node label. Correct `graph.json` and rerun when needed.

## Output contract

- Use a clean, black-and-white legal/financing style by default.
- Use native rectangles, text boxes, and PowerPoint connectors. Do not insert the PDF page or a flattened SVG as the chart.
- Keep the arrow direction as `shareholder → investee`.
- Use `tag` for short labels such as `GP` and `LP`; it remains an independently editable text box.
- Use `level` and `order` only to fix a deliberate layout decision. Otherwise let the renderer create a top-down layout.
- Do not claim that a raster-only PDF was text-extracted. Flag low-confidence transcription items in `notes`.

## Local Python environment

The extractor requires `PyMuPDF`. Create an isolated environment with `conda env create -f environment.yml`, or install `PyMuPDF` in an existing Conda environment. The renderer uses Codex's bundled `@oai/artifact-tool`; do not replace it with a screenshot, SVG, or image-generating library.

## Resources

- `scripts/extract_pdf.py` renders pages and extracts embedded PDF text.
- `scripts/validate_graph.py` validates graph data before rendering.
- `scripts/render_pptx.mjs` creates the editable PowerPoint slide.
- `references/graph-schema.md` defines the handoff JSON and a minimal example.
