"""Regenerate assets/bringup.svg and the README contributions list.

Usage: GITHUB_TOKEN=... python3 scripts/generate.py
"""
import json
import re
import sys
from pathlib import Path

import bringup_svg
import contrib_list
import data
import gh_api

ROOT = Path(__file__).resolve().parent.parent
MARK_START, MARK_END = "<!-- CONTRIB:START -->", "<!-- CONTRIB:END -->"


def replace_block(readme, block):
    pattern = re.compile(re.escape(MARK_START) + r".*?" + re.escape(MARK_END), re.S)
    if not pattern.search(readme):
        raise ValueError("README is missing CONTRIB markers")
    return pattern.sub(lambda _: f"{MARK_START}\n{block}\n{MARK_END}", readme)


def main():
    config = json.loads((ROOT / "scripts" / "config.json").read_text())
    groups = data.build_groups(config)
    if not groups:
        raise RuntimeError("no contribution groups found; refusing to overwrite assets")
    (ROOT / "assets" / "bringup.svg").write_text(bringup_svg.render(groups, config["max_bringup_prs"]))
    readme = ROOT / "README.md"
    readme.write_text(replace_block(readme.read_text(), contrib_list.render_block(groups)))
    print(f"groups={len(groups)} merged={sum(len(g.merged) for g in groups)}")


if __name__ == "__main__":
    try:
        main()
    except (gh_api.GitHubError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
