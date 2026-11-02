import sys
import unittest
import xml.dom.minidom
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import bringup_svg  # noqa: E402
import contrib_list  # noqa: E402
import generate  # noqa: E402
from data import Group, PullRequest  # noqa: E402


def _group(name, n_merged, n_open=0):
    pr = lambda i, m: PullRequest("o/r", i, "fix: thing <&>", f"https://x/{i}", m, "2026-01-01")  # noqa: E731
    return Group(name, name.lower(), "https://x", "blurb", 5000,
                 tuple(pr(i, True) for i in range(n_merged)), tuple(pr(100 + i, False) for i in range(n_open)))


class BringupTest(unittest.TestCase):
    def test_svg_is_well_formed_and_escaped(self):
        svg = bringup_svg.render([_group("Navigation2", 3, 1), _group("DocsGPT", 1)])
        xml.dom.minidom.parseString(svg)
        self.assertIn("IN REVIEW", svg)
        self.assertNotIn("fix:", svg)

    def test_merged_lines_are_capped(self):
        lines = bringup_svg.build_lines([_group("A", 10)], max_prs=7)
        self.assertEqual(sum("MERGED ✓" in "".join(t for t, _ in l) for l in lines), 7)

    def test_status_column_is_aligned(self):
        g = Group("A", "a", "u", "b", 1, (PullRequest("o/r", 1, "x" * 200, "u", True, "d"),
                                          PullRequest("o/r", 2, "short", "u", True, "d")), ())
        widths = {len("".join(t for t, _ in l)) for l in bringup_svg.build_lines([g], 7) if "MERGED" in l[-1][0]}
        self.assertEqual(widths, {bringup_svg.TEXT_COLS})


class ReadmeTest(unittest.TestCase):
    def test_list_has_one_line_per_pr(self):
        block = contrib_list.render_block([_group("Navigation2", 3, 1)])
        self.assertEqual(block.count("\n- "), 4)
        self.assertIn("*(in review)*", block)

    def test_replace_block_requires_markers(self):
        with self.assertRaises(ValueError):
            generate.replace_block("no markers", "x")
        out = generate.replace_block(f"a{generate.MARK_START}old{generate.MARK_END}b", "new")
        self.assertIn("new", out)
        self.assertNotIn("old", out)


if __name__ == "__main__":
    unittest.main()
