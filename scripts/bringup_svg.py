"""Animated 'ros2 launch' terminal SVG built from contribution groups."""
import re
from html import escape

WIDTH = 920
LINE_H = 21
FONT = 13.5
CHAR_W = 8.1  # approx advance for 13.5px monospace
PAD_X = 22
TOP = 58
TEXT_COLS = 94
COMMAND = "ros2 launch shanmukha bringup.launch.py"

COLORS = {
    "text": "#c9d1d9", "dim": "#8b949e", "info": "#3fb950", "warn": "#d29922",
    "node": "#58a6ff", "ok": "#3fb950", "pending": "#d29922", "prompt": "#bc8cff",
}

PREFIX_RE = re.compile(r"^(fix|feat|docs|chore|refactor|perf|test)(\([^)]*\))?\s*:\s*", re.I)


def _clean_title(title):
    return PREFIX_RE.sub("", title).rstrip(".")


def _status_line(level, node, body, status, status_color):
    """Build a list of (text, color) spans padded so status is right-aligned."""
    head = f"[{level}] [{node}]: "
    room = TEXT_COLS - len(head) - len(status) - 2
    body = body if len(body) <= room - 2 else body[: room - 3] + "…"
    dots = " " + "." * max(2, room - len(body)) + " "
    level_color = COLORS["warn"] if level == "WARN" else COLORS["info"]
    return [(f"[{level}] ", level_color), (f"[{node}]", COLORS["node"]), (": " + body, COLORS["text"]),
            (dots, COLORS["dim"]), (status, status_color)]


def _plain(level, node, body):
    level_color = COLORS["warn"] if level == "WARN" else COLORS["info"]
    return [(f"[{level}] ", level_color), (f"[{node}]", COLORS["node"]), (": " + body, COLORS["text"])]


def build_lines(groups, max_prs):
    lines = [_plain("INFO", "shanmukha", "Robotics Engineer · ROS 2 · Nav2 · C++ · Python")]
    for g, p in [(g, p) for g in groups for p in g.merged][:max_prs]:
        lines.append(_status_line("INFO", g.label, f"#{p.number} {_clean_title(p.title)}", "MERGED ✓", COLORS["ok"]))
    for g in groups:
        for p in g.open:
            lines.append(_status_line("INFO", g.label, f"#{p.number} {_clean_title(p.title)}",
                                      "IN REVIEW", COLORS["pending"]))
    lines.append([("[INFO] ", COLORS["info"]), ("[lifecycle_manager]", COLORS["node"]),
                  (": Managed nodes are active ", COLORS["text"]), ("●", COLORS["ok"])])
    return lines


def _spans(spans):
    return "".join(f'<tspan fill="{c}">{escape(t)}</tspan>' for t, c in spans)


def render(groups, max_prs=7):
    lines = build_lines(groups, max_prs)
    height = TOP + LINE_H * (len(lines) + 2) + 18
    type_secs = 1.6
    cmd_w = len(COMMAND) * CHAR_W
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" '
        f'role="img" aria-label="ros2 launch shanmukha bringup: profile boot log">',
        "<style>",
        f"text{{font-family:ui-monospace,SFMono-Regular,'JetBrains Mono',Menlo,Consolas,monospace;font-size:{FONT}px;"
        "white-space:pre}",
        ".l{opacity:0;animation:show .01s linear forwards}",
        "@keyframes show{to{opacity:1}}",
        f"@keyframes type{{from{{width:0}}to{{width:{cmd_w + 4:.0f}px}}}}",
        f"#typer{{animation:type {type_secs}s steps({len(COMMAND)}) .4s forwards}}",
        ".cur{animation:blink 1s step-end infinite}@keyframes blink{50%{opacity:0}}",
        "</style>",
        f'<rect width="{WIDTH}" height="{height}" rx="12" fill="#0d1117" stroke="#30363d"/>',
        f'<rect width="{WIDTH}" height="34" rx="12" fill="#161b22"/><rect y="22" width="{WIDTH}" height="12" fill="#161b22"/>',
        '<circle cx="22" cy="17" r="6" fill="#ff5f56"/><circle cx="42" cy="17" r="6" fill="#ffbd2e"/>'
        '<circle cx="62" cy="17" r="6" fill="#27c93f"/>',
        f'<text x="{WIDTH / 2}" y="22" text-anchor="middle" fill="{COLORS["dim"]}">shanmukha@robot: ~/ros2_ws</text>',
        f'<clipPath id="cmdclip"><rect id="typer" x="{PAD_X + 2 * CHAR_W}" y="{TOP - 16}" width="0" height="22"/></clipPath>',
        f'<text x="{PAD_X}" y="{TOP}"><tspan fill="{COLORS["prompt"]}">$ </tspan></text>',
        f'<text x="{PAD_X + 2 * CHAR_W}" y="{TOP}" fill="{COLORS["text"]}" clip-path="url(#cmdclip)">{COMMAND}</text>',
    ]
    start = 0.4 + type_secs + 0.5
    for i, spans in enumerate(lines):
        y = TOP + LINE_H * (i + 1)
        out.append(f'<text class="l" x="{PAD_X}" y="{y}" style="animation-delay:{start + i * 0.28:.2f}s">'
                   f"{_spans(spans)}</text>")
    y = TOP + LINE_H * (len(lines) + 1)
    end = start + len(lines) * 0.28
    out.append(f'<g class="l" style="animation-delay:{end:.2f}s"><text x="{PAD_X}" y="{y}">'
               f'<tspan fill="{COLORS["prompt"]}">$ </tspan></text>'
               f'<rect class="cur" x="{PAD_X + 2 * CHAR_W}" y="{y - 13}" width="8" height="16" fill="{COLORS["text"]}"/></g>')
    out.append("</svg>")
    return "\n".join(out)
