#!/usr/bin/env python3
"""Render a PPTX to PNGs for QA using Quick Look or LibreOffice."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pymupdf
from PIL import Image


def find_soffice() -> Path:
    configured = os.environ.get("SOFFICE_PATH")
    candidates = [
        Path(configured) if configured else None,
        Path(shutil.which("soffice")) if shutil.which("soffice") else None,
        Path(shutil.which("libreoffice")) if shutil.which("libreoffice") else None,
        Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/soffice",
    ]
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    raise SystemExit(
        "LibreOffice/soffice was not found. Set SOFFICE_PATH to render a preview; "
        "PPTX generation itself does not require LibreOffice."
    )


def render_quicklook(input_pptx: Path, output_dir: Path, tile_count: int) -> bool:
    quicklook = shutil.which("qlmanage")
    if sys.platform != "darwin" or not quicklook:
        return False
    with tempfile.TemporaryDirectory(prefix="pptx-quicklook-") as temporary:
        command = [
            quicklook,
            "-t",
            "-s",
            "5000",
            "-o",
            temporary,
            str(input_pptx.resolve()),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        candidates = sorted(Path(temporary).glob("*.png"))
        if result.returncode != 0 or not candidates:
            return False
        output = output_dir / "slide-001.png"
        shutil.copy2(candidates[0], output)
    print(f"Rendered {output} with macOS Quick Look")
    if tile_count > 1:
        with Image.open(output) as image:
            tile_width = image.width / tile_count
            for tile_index in range(tile_count):
                left = round(tile_index * tile_width)
                right = round((tile_index + 1) * tile_width)
                tile_output = output_dir / f"slide-001-tile-{tile_index + 1:02d}.png"
                image.crop((left, 0, right, image.height)).save(tile_output)
                print(f"Rendered {tile_output}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_pptx", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--dpi", type=int, default=160)
    parser.add_argument(
        "--tile-count",
        type=int,
        default=1,
        help="Also render this many left-to-right detail tiles per slide.",
    )
    args = parser.parse_args()

    if not args.input_pptx.is_file():
        raise SystemExit(f"PPTX not found: {args.input_pptx}")
    if args.dpi < 72:
        raise SystemExit("--dpi must be at least 72")
    if args.tile_count < 1:
        raise SystemExit("--tile-count must be at least 1")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if render_quicklook(args.input_pptx, args.output_dir, args.tile_count):
        return
    soffice = find_soffice()
    with tempfile.TemporaryDirectory(prefix="pptx-preview-") as profile_dir:
        profile_uri = Path(profile_dir).resolve().as_uri()
        command = [
            str(soffice),
            "--headless",
            f"-env:UserInstallation={profile_uri}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(args.output_dir.resolve()),
            str(args.input_pptx.resolve()),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(
            "LibreOffice preview conversion failed:\n"
            + (result.stdout or "")
            + (result.stderr or "")
        )

    pdf_path = args.output_dir / f"{args.input_pptx.stem}.pdf"
    if not pdf_path.is_file():
        raise SystemExit(
            f"LibreOffice did not create {pdf_path}. Output was:\n{result.stdout}{result.stderr}"
        )

    document = pymupdf.open(pdf_path)
    scale = args.dpi / 72
    for index, page in enumerate(document, start=1):
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
        output = args.output_dir / f"slide-{index:03d}.png"
        pixmap.save(output)
        print(f"Rendered {output}")
        if args.tile_count > 1:
            tile_width = page.rect.width / args.tile_count
            for tile_index in range(args.tile_count):
                clip = pymupdf.Rect(
                    page.rect.x0 + tile_index * tile_width,
                    page.rect.y0,
                    page.rect.x0 + (tile_index + 1) * tile_width,
                    page.rect.y1,
                )
                tile = page.get_pixmap(
                    matrix=pymupdf.Matrix(scale, scale), clip=clip, alpha=False
                )
                tile_output = args.output_dir / (
                    f"slide-{index:03d}-tile-{tile_index + 1:02d}.png"
                )
                tile.save(tile_output)
                print(f"Rendered {tile_output}")


if __name__ == "__main__":
    main()
