#!/usr/bin/env python3
"""
crop_tables.py — Crop tables and figures from rasterized PDF page images.

Usage:
    # Crop with percentage-based coordinates
    python crop_tables.py --input page.jpg --output table_I.png --crop "5%,8%,95%,70%"

    # Crop with pixel coordinates
    python crop_tables.py --input page.jpg --output table_I.png --crop "50,100,2400,1800" --pixels

    # Auto-detect content bounds (trims whitespace)
    python crop_tables.py --input page.jpg --output table_I.png --auto --padding 30

    # Batch mode: crop multiple regions from the same image
    python crop_tables.py --input page.jpg --batch regions.json

    # Downscale output to reduce file size
    python crop_tables.py --input page.jpg --output table_I.png --crop "5%,8%,95%,70%" --max-width 2000

Arguments:
    --input       Path to the source image (rasterized PDF page)
    --output      Path for the cropped output image
    --crop        Crop region as "left,top,right,bottom"
                  With %: percentages of image dimensions (default)
                  Without % and --pixels: absolute pixel coordinates
    --pixels      Interpret --crop values as pixel coordinates
    --auto        Auto-detect content bounds by trimming whitespace
    --padding     Pixels of padding to add around auto-detected bounds (default: 20)
    --max-width   Maximum output width in pixels (downscales proportionally)
    --batch       Path to a JSON file defining multiple crops (see below)
    --quality     JPEG quality 1-100 when saving as .jpg (default: 95)

Batch JSON format:
    [
        {"output": "table_II.png",  "crop": "5%,10%,95%,68%"},
        {"output": "table_III.png", "crop": "5%,8%,95%,65%"}
    ]
    When using --batch, all crops come from the same --input image.
    To crop from different source images, run the script multiple times
    or extend the JSON with an "input" field per entry.
"""

import argparse
import json
import os
import sys

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)


def parse_crop_string(crop_str: str, img_width: int, img_height: int, pixels: bool = False) -> tuple:
    """Parse a crop string into pixel coordinates (left, top, right, bottom)."""
    parts = [p.strip() for p in crop_str.split(",")]
    if len(parts) != 4:
        raise ValueError(f"Crop must have 4 values (left,top,right,bottom), got {len(parts)}: {crop_str}")

    if pixels:
        return tuple(int(float(p.rstrip("%"))) for p in parts)

    # Percentage mode
    values = []
    for p in parts:
        v = float(p.rstrip("%"))
        if v > 1 and not p.endswith("%"):
            # Ambiguous: large number without %. Assume percentage if all < 100
            pass
        values.append(v / 100.0 if v > 1 else v)

    # If values look like they're already 0-1 fractions, use as-is
    # If they look like percentages (> 1), divide by 100
    coords = []
    for i, v in enumerate(values):
        raw = float(parts[i].rstrip("%"))
        frac = raw / 100.0 if raw > 1 else raw
        dim = img_width if i % 2 == 0 else img_height
        coords.append(int(frac * dim))

    return tuple(coords)


def auto_crop(img: Image.Image, padding: int = 20) -> tuple:
    """Auto-detect content bounds by trimming near-white borders."""
    import numpy as np

    arr = np.array(img.convert("L"))  # Grayscale
    # Threshold: pixels darker than 240 are "content"
    mask = arr < 240

    # Find bounding box of content
    rows = mask.any(axis=1)
    cols = mask.any(axis=0)

    if not rows.any() or not cols.any():
        # All white — return full image
        return (0, 0, img.width, img.height)

    top = rows.argmax()
    bottom = len(rows) - rows[::-1].argmax()
    left = cols.argmax()
    right = len(cols) - cols[::-1].argmax()

    # Add padding
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(img.width, right + padding)
    bottom = min(img.height, bottom + padding)

    return (left, top, right, bottom)


def crop_image(
    input_path: str,
    output_path: str,
    crop_str: str = None,
    pixels: bool = False,
    auto: bool = False,
    padding: int = 20,
    max_width: int = None,
    quality: int = 95,
) -> None:
    """Crop an image and save the result."""
    img = Image.open(input_path)
    w, h = img.size

    if auto:
        box = auto_crop(img, padding)
        print(f"  Auto-detected bounds: left={box[0]}, top={box[1]}, right={box[2]}, bottom={box[3]}")
    elif crop_str:
        box = parse_crop_string(crop_str, w, h, pixels)
    else:
        raise ValueError("Provide either --crop or --auto")

    cropped = img.crop(box)

    # Downscale if requested
    if max_width and cropped.width > max_width:
        ratio = max_width / cropped.width
        new_h = int(cropped.height * ratio)
        cropped = cropped.resize((max_width, new_h), Image.LANCZOS)
        print(f"  Downscaled to {max_width}x{new_h}")

    # Save
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        cropped.save(output_path, "JPEG", quality=quality)
    else:
        cropped.save(output_path)

    crop_w, crop_h = cropped.size
    size_kb = os.path.getsize(output_path) / 1024
    print(f"  Saved: {output_path} ({crop_w}x{crop_h}, {size_kb:.0f} KB)")


def main():
    parser = argparse.ArgumentParser(
        description="Crop tables and figures from rasterized PDF pages."
    )
    parser.add_argument("--input", "-i", required=True, help="Source image path")
    parser.add_argument("--output", "-o", help="Output image path")
    parser.add_argument("--crop", "-c", help="Crop region: left,top,right,bottom (%%)")
    parser.add_argument("--pixels", action="store_true", help="Interpret crop as pixels")
    parser.add_argument("--auto", action="store_true", help="Auto-detect content bounds")
    parser.add_argument("--padding", type=int, default=20, help="Padding for auto mode (px)")
    parser.add_argument("--max-width", type=int, help="Max output width (downscale)")
    parser.add_argument("--batch", help="JSON file with multiple crop definitions")
    parser.add_argument("--quality", type=int, default=95, help="JPEG quality (1-100)")

    args = parser.parse_args()

    if args.batch:
        with open(args.batch) as f:
            regions = json.load(f)
        print(f"Batch mode: {len(regions)} crops from {args.input}")
        for i, region in enumerate(regions):
            inp = region.get("input", args.input)
            out = region["output"]
            crop = region.get("crop")
            is_auto = region.get("auto", False)
            pad = region.get("padding", args.padding)
            print(f"\n[{i+1}/{len(regions)}] → {out}")
            crop_image(
                input_path=inp,
                output_path=out,
                crop_str=crop,
                pixels=args.pixels,
                auto=is_auto,
                padding=pad,
                max_width=args.max_width,
                quality=args.quality,
            )
    else:
        if not args.output:
            parser.error("--output is required unless using --batch")
        if not args.crop and not args.auto:
            parser.error("Provide --crop or --auto")
        print(f"Cropping: {args.input} → {args.output}")
        crop_image(
            input_path=args.input,
            output_path=args.output,
            crop_str=args.crop,
            pixels=args.pixels,
            auto=args.auto,
            padding=args.padding,
            max_width=args.max_width,
            quality=args.quality,
        )

    print("\nDone.")


if __name__ == "__main__":
    main()
