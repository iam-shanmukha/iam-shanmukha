"""LiDAR-style ASCII point-cloud portrait SVG (pure renderer, stdlib only).

Input is a grid of cells: None (no return) or (density, colour) where density
indexes RAMP and colour indexes PALETTE.
"""
from html import escape

RAMP = ".:-=+*#%@"
# rviz-style rainbow (low z → high z), skipping near-black tones.
PALETTE = ["#4662d7", "#36aaf9", "#1ae4b6", "#72fe5e", "#c8ef34", "#faba39", "#f66b19", "#e4460a", "#ca2a04"]

FONT = 9.0
CHAR_W = 5.4
LINE_H = 9.0
PAD = 22
HEADER = 26
FOOTER = 44
CYCLE = 10.0     # seconds per scan loop
SWEEP = 0.45     # fraction of cycle spent sweeping in


def _row_spans(row):
    """Group consecutive cells with the same level into (text, level) runs."""
    runs = []
    for cell in row:
        ch = " " if cell is None else RAMP[min(cell[0], len(RAMP) - 1)]
        colour = None if cell is None else cell[1]
        if runs and runs[-1][1] == colour:
            runs[-1][0].append(ch)
        else:
            runs.append(([ch], colour))
    return [("".join(chars), level) for chars, level in runs]


def render(grid, title="shanmukha_vishnu"):
    rows, cols = len(grid), len(grid[0])
    art_w, art_h = cols * CHAR_W, rows * LINE_H
    width, height = art_w + 2 * PAD, art_h + HEADER + FOOTER
    points = sum(1 for row in grid for v in row if v is not None)
    sweep_pct = SWEEP * 100
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-label="LiDAR ASCII point-cloud portrait of {escape(title)}">',
        "<style>",
        "text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;white-space:pre}",
        f".a{{font-size:{FONT}px;font-weight:700}}",
        f"#reveal{{animation:sweep {CYCLE}s linear infinite}}",
        f"@keyframes sweep{{0%{{width:0}}{sweep_pct:.0f}%,92%{{width:{art_w + 4:.0f}px}}100%{{width:{art_w + 4:.0f}px}}}}",
        f"#beam{{animation:beam {CYCLE}s linear infinite}}",
        f"@keyframes beam{{0%{{transform:translateX(0);opacity:1}}{sweep_pct:.0f}%{{transform:translateX({art_w:.0f}px);"
        f"opacity:1}}{sweep_pct + 3:.0f}%,100%{{transform:translateX({art_w:.0f}px);opacity:0}}}}",
        f"#cloud{{animation:fade {CYCLE}s linear infinite}}",
        "@keyframes fade{0%,92%{opacity:1}100%{opacity:0}}",
        "</style>",
        f'<rect width="{width:.0f}" height="{height:.0f}" rx="12" fill="#0d1117" stroke="#30363d"/>',
        f'<clipPath id="clip"><rect id="reveal" x="{PAD - 2}" y="{HEADER - LINE_H}" width="0" '
        f'height="{art_h + LINE_H}"/></clipPath>',
        f'<g id="cloud" clip-path="url(#clip)">',
    ]
    for r, row in enumerate(grid):
        y = HEADER + r * LINE_H
        spans = "".join(
            f'<tspan fill="{PALETTE[min(lvl, len(PALETTE) - 1)]}">{escape(txt)}</tspan>' if lvl is not None else escape(txt)
            for txt, lvl in _row_spans(row)
        )
        out.append(f'<text class="a" x="{PAD}" y="{y:.1f}" textLength="{art_w:.1f}" '
                   f'lengthAdjust="spacing">{spans}</text>')
    out += [
        "</g>",
        f'<g id="beam"><rect x="{PAD - 1}" y="{HEADER - LINE_H}" width="2" height="{art_h + LINE_H}" fill="#72fe5e"/>'
        f'<rect x="{PAD - 9}" y="{HEADER - LINE_H}" width="10" height="{art_h + LINE_H}" fill="#72fe5e" opacity=".15"/></g>',
        f'<text x="{width / 2:.0f}" y="{height - 16:.0f}" font-size="20" text-anchor="middle" fill="#8b949e">'
        f'<tspan fill="#58a6ff">/scan</tspan> · {points:,} pts · <tspan fill="#3fb950">●</tspan></text>',
        "</svg>",
    ]
    return "\n".join(out)
