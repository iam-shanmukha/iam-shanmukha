"""Plain markdown list of upstream contributions for the README."""
from bringup_svg import _clean_title as clean


def fmt_stars(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def render_block(groups):
    out = []
    for g in groups:
        out.append(f"**[{g.name}]({g.url})** · {g.blurb} · ⭐ {fmt_stars(g.stars)}")
        for p in g.merged:
            out.append(f"- [#{p.number}]({p.url}) {clean(p.title)[:1].upper()}{clean(p.title)[1:]}")
        for p in g.open:
            out.append(f"- [#{p.number}]({p.url}) {clean(p.title)[:1].upper()}{clean(p.title)[1:]} *(in review)*")
        out.append("")
    return "\n".join(out).rstrip()
