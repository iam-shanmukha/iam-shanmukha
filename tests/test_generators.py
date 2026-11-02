import sys
import unittest
import xml.dom.minidom
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import bringup_svg  # noqa: E402
import generate  # noqa: E402
import planner  # noqa: E402
import planner_svg  # noqa: E402
import rqt_graph  # noqa: E402
from data import Group, PullRequest  # noqa: E402


def _weeks(counts_by_cell, cols=10):
    return [[(f"d{c}{r}", r, counts_by_cell.get((c, r), 0)) for r in range(7)] for c in range(cols)]


def _group(node, n_merged, n_open=0):
    pr = lambda i, m: PullRequest("o/r", i, "fix: thing <&>", f"https://x/{i}", m, "2026-01-01")  # noqa: E731
    return Group(node, node.strip("/"), "blurb", "/t", 5000,
                 tuple(pr(i, True) for i in range(n_merged)), tuple(pr(100 + i, False) for i in range(n_open)))


class PlannerTest(unittest.TestCase):
    def test_patrol_starts_mid_left_and_ends_today(self):
        _, _, path, waypoints = planner.plan(_weeks({}))
        self.assertEqual(path[0], (0, 3))
        self.assertEqual(path[-1], (9, 6))
        self.assertEqual(path, waypoints)  # empty map: each leg is a straight line

    def test_path_avoids_lethal_wall_with_gap(self):
        wall = {(5, r): 10 for r in range(6)}  # gap at row 6
        cost, lethal, path, _ = planner.plan(_weeks(wall))
        cells = {c for a, b in zip(path, path[1:]) for c in planner._line(a, b)}
        self.assertFalse(cells & lethal)

    def test_fully_blocked_falls_back(self):
        wall = {(5, r): 10 for r in range(7)}
        _, _, path, _ = planner.plan(_weeks(wall))
        self.assertIsNotNone(path)


class RenderTest(unittest.TestCase):
    def test_svgs_are_well_formed_and_escaped(self):
        groups = [_group("/navigation2", 3, 1), _group("/docsgpt", 1)]
        weeks = _weeks({(3, 3): 5})
        cost, lethal, path, wps = planner.plan(weeks)
        for svg in (bringup_svg.render(groups), planner_svg.render(weeks, 5, cost, lethal, path, wps)):
            xml.dom.minidom.parseString(svg)
        self.assertIn("IN REVIEW", bringup_svg.render(groups))

    def test_graph_has_one_arrow_per_group(self):
        for n in (1, 2, 3, 5):
            graph = rqt_graph.render_graph([_group(f"/g{i}", 1) for i in range(n)])
            self.assertEqual(graph.count("▶"), n)

    def test_long_node_names_stay_inside_box(self):
        graph = rqt_graph.render_graph([_group("/a_really_long_repository_name_here", 12)])
        widths = {len(line.split("▶")[1][:rqt_graph.BOX_W + 2]) for line in graph.splitlines() if "▶" in line}
        self.assertIn("×12 merged │", graph)
        self.assertEqual(widths, {rqt_graph.BOX_W + 2})

    def test_replace_block_requires_markers(self):
        with self.assertRaises(ValueError):
            generate.replace_block("no markers", "x")
        out = generate.replace_block(f"a{generate.MARK_START}old{generate.MARK_END}b", "new")
        self.assertIn("new", out)
        self.assertNotIn("old", out)


if __name__ == "__main__":
    unittest.main()
