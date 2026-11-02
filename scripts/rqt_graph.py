"""ASCII rqt_graph of contribution groups + markdown PR list for the README."""

CENTER = ["/shanmukha_vishnu", "[robotics_engineer]"]
CENTER_W = 24
BUS_X = CENTER_W + 6
BOX_W = 34


def fmt_stars(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def _box(label, inner_w):
    return ["┌" + "─" * inner_w + "┐", "│" + label.ljust(inner_w)[:inner_w] + "│", "└" + "─" * inner_w + "┘"]


def render_graph(groups):
    rows = []  # (left_part, bus_char, right_part)
    mids = []
    for g in groups:
        merged = f"×{len(g.merged)} merged"
        name = g.node if len(g.node) <= BOX_W - len(merged) - 3 else g.node[: BOX_W - len(merged) - 4] + "…"
        label = f" {name}".ljust(BOX_W - len(merged) - 1) + merged + " "
        box = _box(label, BOX_W)
        star = f"  ⭐ {fmt_stars(g.stars)}"
        topics = f"  ◀ {g.topics}"
        mids.append(len(rows) + 1)
        rows += [(box[0], ""), (box[1], star), (box[2], topics)]

    first, last = mids[0], mids[-1]
    center_mid = mids[len(mids) // 2] if len(mids) % 2 else (first + last) // 2
    center_box = _box(f" {CENTER[0]}".ljust(CENTER_W), CENTER_W)
    center_box[1:2] = ["│" + f" {CENTER[0]}".ljust(CENTER_W) + "│", "│" + f" {CENTER[1]}".ljust(CENTER_W) + "│"]
    center_top = center_mid - 1

    lines = []
    for i, (box, tail) in enumerate(rows):
        ci = i - center_top
        left = center_box[ci] if 0 <= ci < len(center_box) else " " * (CENTER_W + 2)
        if i == center_mid:
            left += "─" * (BUS_X - len(left))
        else:
            left = left.ljust(BUS_X)
        on_bus = first <= i <= last
        if i in mids:
            bus = {first: "┌", last: "└"}.get(i, "├")
            if i == center_mid:
                bus = {first: "┬", last: "┴"}.get(i, "┼")
            right = "───▶" + box
        else:
            bus = ("┤" if i == center_mid else "│") if on_bus else " "
            right = "    " + box
        if len(mids) == 1:
            bus = "─"
        lines.append((left + bus + right + tail).rstrip())
    return "\n".join(lines)


def render_list(groups):
    out = []
    for g in groups:
        out.append(f"**`{g.node}`** — {g.blurb} · ⭐ {fmt_stars(g.stars)}\n")
        for p in g.merged:
            out.append(f"- ✅ [{p.repo.split('/')[1]}#{p.number}]({p.url}) — {p.title}")
        for p in g.open:
            out.append(f"- 🟡 [{p.repo.split('/')[1]}#{p.number}]({p.url}) — {p.title} *(in review)*")
        out.append("")
    return "\n".join(out)


def render_block(groups):
    total = sum(len(g.merged) for g in groups)
    return "\n".join([
        "```console",
        "$ ros2 run rqt_graph rqt_graph --headless",
        "",
        render_graph(groups),
        "```",
        "",
        "<details>",
        f"<summary><code>$ ros2 topic echo /merged_prs</code> — {total} merged upstream (click)</summary>",
        "",
        render_list(groups),
        "</details>",
    ])
