"""Build assets/portrait.svg from a photo. Run locally (needs Pillow + numpy):

    python3 scripts/portrait.py images/shanmukha_vishnu.jpg --crop 504,0,1872,1249

The photo never changes, so this is not part of the daily workflow.
"""
import argparse
import sys
from pathlib import Path

import portrait_svg

ROOT = Path(__file__).resolve().parent.parent


def to_grid(path, crop, cols, threshold, edge_gain):
    """Photo → grid of (density, colour) cells, None where there is no return.

    Density (which ASCII glyph) comes from darkness plus an edge boost, so
    outlines like sunglasses and folds stay crisp. Colour follows height,
    like rviz's AxisColor transformer on the z axis (top = red, bottom = blue).
    """
    import numpy as np
    from PIL import Image, ImageFilter, ImageOps

    img = Image.open(path).convert("L")
    if crop:
        img = img.crop(crop)
    img = ImageOps.autocontrast(img, cutoff=1)
    # Monospace cells are ~2x taller than wide; scale rows accordingly.
    rows = max(1, round(cols * img.height / img.width * (portrait_svg.CHAR_W / portrait_svg.LINE_H)))
    small = img.resize((cols, rows), Image.LANCZOS)
    darkness = 1.0 - np.asarray(small, dtype=float) / 255.0
    edges = np.asarray(small.filter(ImageFilter.FIND_EDGES), dtype=float) / 255.0
    signal = np.clip((darkness - threshold) / (1 - threshold) + edge_gain * edges, 0, 1)
    n_ramp, n_pal = len(portrait_svg.RAMP), len(portrait_svg.PALETTE)
    grid = []
    for r in range(rows):
        colour = n_pal - 1 - int(r / rows * n_pal)
        grid.append([
            (min(n_ramp - 1, int(signal[r, c] * n_ramp)), colour) if darkness[r, c] >= threshold else None
            for c in range(cols)
        ])
    return grid


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("photo")
    ap.add_argument("--crop", help="left,top,right,bottom in pixels")
    ap.add_argument("--cols", type=int, default=140)
    ap.add_argument("--threshold", type=float, default=0.18)
    ap.add_argument("--edge-gain", type=float, default=0.8)
    ap.add_argument("--out", default=str(ROOT / "assets" / "portrait.svg"))
    args = ap.parse_args()
    try:
        crop = tuple(int(v) for v in args.crop.split(",")) if args.crop else None
        if crop and len(crop) != 4:
            raise ValueError("--crop needs four integers")
        grid = to_grid(args.photo, crop, args.cols, args.threshold, args.edge_gain)
    except (OSError, ValueError, ImportError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    Path(args.out).write_text(portrait_svg.render(grid))
    print(f"wrote {args.out}: {len(grid)}x{len(grid[0])}")


if __name__ == "__main__":
    main()
