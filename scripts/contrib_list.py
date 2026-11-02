"""Markdown list of upstream contributions for the README."""
from bringup_svg import _clean_title


def fmt_stars(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def _title(title):
    t = _clean_title(title)
    return t[:1].upper() + t[1:]


def _counts(g):
    parts = [f"{len(g.merged)} merged"]
    if g.open:
        parts.append(f"{len(g.open)} in review")
    return " + ".join(parts)


def render_block(groups):
    out = []
    for g in groups:
        parts = g.url.rstrip("/").split("/")
        logo = (f'<img src="https://github.com/{parts[3]}.png?size=40" width="20" height="20" align="top" /> '
                if len(parts) > 3 else "")
        out.append(f"{logo}**[{g.name}]({g.url})** · {g.blurb} · ⭐ {fmt_stars(g.stars)} · {_counts(g)}")
        out.append("")
        for p in g.merged:
            out.append(f"- [#{p.number}]({p.url}) {_title(p.title)}")
        for p in g.open:
            out.append(f"- [#{p.number}]({p.url}) {_title(p.title)} *(in review)*")
        out.append("")
    return "\n".join(out).rstrip()
