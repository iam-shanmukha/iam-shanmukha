"""Render the contribution costmap + animated Theta* robot as SVG."""
import math

PITCH = 16
CELL = 13
LEFT = 44
TOP = 70
CYCLE = 12.0      # seconds per loop
DRIVE = 0.6       # fraction of the cycle spent driving

FREE = "#161b22"
GRID_TXT = "#8b949e"
PATH = "#3fb950"
DAYS = {1: "Mon", 3: "Wed", 5: "Fri"}


def _mix(a, b, t):
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))


def _cell_color(cost, count, peak):
    """rviz-style palette: lethal obstacles magenta (brighter = busier day),
    inflation fades from blue into the free-space background."""
    if count > 0:
        return _mix("#7e22ce", "#f0abfc", min(1.0, count / max(peak, 1)))
    if cost <= 0:
        return FREE
    return _mix(FREE, "#2563eb", cost * 0.85)


def _center(cell):
    col, row = cell
    return LEFT + col * PITCH + CELL / 2, TOP + row * PITCH + CELL / 2


def _path_length(points):
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def render(weeks, total, cost, lethal, path, waypoints):
    cols = len(weeks)
    width = LEFT + cols * PITCH + 24
    height = TOP + 7 * PITCH + 70
    pts = [_center(c) for c in path]
    length = _path_length(pts)
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    key = f"0;{DRIVE};1"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="A robot plans a Theta* path across the contribution costmap">',
        "<style>text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px}"
        f".p{{stroke-dasharray:{length:.0f};stroke-dashoffset:{length:.0f};animation:draw {CYCLE}s linear infinite}}"
        f"@keyframes draw{{0%{{stroke-dashoffset:{length:.0f}}}{DRIVE * 100:.0f}%,100%{{stroke-dashoffset:0}}}}"
        "</style>",
        f'<rect width="{width}" height="{height}" rx="12" fill="#0d1117" stroke="#30363d"/>',
        f'<text x="{LEFT}" y="28" fill="#c9d1d9">$ ros2 action send_goal /follow_waypoints today '
        f'<tspan fill="{GRID_TXT}">--planner theta_star</tspan></text>',
        f'<text x="{LEFT}" y="50" fill="{GRID_TXT}">costmap: last {cols} weeks · {total} contributions · '
        f'<tspan fill="#d946ef">■</tspan> obstacle = a day I shipped code <tspan fill="#2563eb">■</tspan> inflation · ○ waypoint</text>',
    ]
    for row, name in DAYS.items():
        out.append(f'<text x="4" y="{TOP + row * PITCH + 10}" fill="{GRID_TXT}" font-size="9">{name}</text>')
    peak = max((n for week in weeks for (_, _, n) in week), default=1)
    for col, week in enumerate(weeks):
        for _, row, n in week:
            out.append(f'<rect x="{LEFT + col * PITCH}" y="{TOP + row * PITCH}" width="{CELL}" height="{CELL}" '
                       f'rx="2" fill="{_cell_color(cost.get((col, row), 0), n, peak)}"/>')
    for wx, wy in (_center(w) for w in waypoints[1:-1]):
        out.append(f'<circle cx="{wx:.1f}" cy="{wy:.1f}" r="3" fill="none" stroke="#f0f6fc" stroke-opacity=".7"/>')
    gx, gy = pts[-1]
    out += [
        f'<path class="p" d="{d}" fill="none" stroke="{PATH}" stroke-width="3" stroke-linecap="round" '
        'stroke-linejoin="round" opacity=".9"/>',
        f'<g transform="translate({gx:.1f},{gy:.1f})"><circle r="9" fill="none" stroke="#f0f6fc" stroke-width="1.5">'
        '<animate attributeName="r" values="5;11;5" dur="1.6s" repeatCount="indefinite"/></circle>'
        '<circle r="3" fill="#f0f6fc"/></g>',
        "<g>",
        # LiDAR sweep wedge + range ring, rotating independently of heading.
        '<g><path d="M0,0 L34,-10 A35,35 0 0,1 34,10 Z" fill="#3fb950" opacity=".25"/>'
        '<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="1.2s" '
        'repeatCount="indefinite"/></g>',
        '<circle r="34" fill="none" stroke="#3fb950" stroke-opacity=".25" stroke-dasharray="2 4"/>',
        f'<animateMotion dur="{CYCLE}s" repeatCount="indefinite" keyPoints="{key}" keyTimes="{key}" '
        f'calcMode="linear" path="{d}"/>',
        "</g>",
        '<g><rect x="-8" y="-6" width="16" height="12" rx="3" fill="#58a6ff" stroke="#f0f6fc" stroke-width="1.2"/>'
        '<path d="M8,-4 L13,0 L8,4 Z" fill="#f0f6fc"/>'
        f'<animateMotion dur="{CYCLE}s" repeatCount="indefinite" rotate="auto" keyPoints="{key}" '
        f'keyTimes="{key}" calcMode="linear" path="{d}"/></g>',
        f'<text x="{LEFT}" y="{height - 20}" fill="{GRID_TXT}">[INFO] [waypoint_follower]: {len(waypoints)} waypoints · '
        f'Theta* any-angle legs: {len(path)} poses · [INFO] [bt_navigator]: <tspan fill="{PATH}">Goal succeeded</tspan></text>',
        "</svg>",
    ]
    return "\n".join(out)
