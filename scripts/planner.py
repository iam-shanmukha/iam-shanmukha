"""Theta* any-angle planner over a contribution-calendar costmap.

Grid cells are (col, row) = (week, weekday). Cell cost is 0..1; cells marked
lethal are impassable.
"""
import heapq
import math


INFLATION_RADIUS = 2.5
INFLATION_DECAY = 1.2


def build_costmap(weeks):
    """Nav2-style costmap: contribution days are lethal obstacles, and free
    cells near them get an exponentially decaying inflation cost.

    Returns (cost, lethal) where cost is keyed by (col, row) for existing days.
    """
    counts = {(c, wd): n for c, week in enumerate(weeks) for (_, wd, n) in week}
    lethal = frozenset(k for k, n in counts.items() if n > 0)
    cost = {}
    for cell in counts:
        if cell in lethal:
            cost[cell] = 1.0
            continue
        near = min((math.dist(cell, o) for o in lethal), default=math.inf)
        cost[cell] = math.exp(-INFLATION_DECAY * (near - 1)) if near <= INFLATION_RADIUS else 0.0
    return cost, lethal


def _line(a, b):
    """Bresenham cells between a and b inclusive."""
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err, cells = dx + dy, []
    while True:
        cells.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return cells
        e2 = 2 * err
        if e2 >= dy:
            err, x0 = err + dy, x0 + sx
        if e2 <= dx:
            err, y0 = err + dx, y0 + sy


def _segment_cost(a, b, cost, blocked, weight):
    cells = _line(a, b)
    if any(c not in cost or c in blocked for c in cells):
        return None
    mean = sum(cost[c] for c in cells) / len(cells)
    return math.dist(a, b) * (1 + weight * mean)


NEIGHBOURS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]


def theta_star(cost, blocked, start, goal, weight=4.0):
    """Return list of waypoints from start to goal, or None if unreachable."""
    g = {start: 0.0}
    parent = {start: start}
    frontier = [(math.dist(start, goal), start)]
    closed = set()
    while frontier:
        _, node = heapq.heappop(frontier)
        if node == goal:
            path = [node]
            while parent[path[-1]] != path[-1]:
                path.append(parent[path[-1]])
            return path[::-1]
        if node in closed:
            continue
        closed.add(node)
        for dx, dy in NEIGHBOURS:
            nb = (node[0] + dx, node[1] + dy)
            if nb not in cost or nb in blocked or nb in closed:
                continue
            # Theta*: try connecting straight from the grandparent first.
            via = parent[node]
            seg = _segment_cost(via, nb, cost, blocked, weight)
            if seg is None:
                via = node
                seg = _segment_cost(node, nb, cost, blocked, weight)
            new_g = g[via] + seg
            if new_g < g.get(nb, math.inf):
                g[nb], parent[nb] = new_g, via
                heapq.heappush(frontier, (new_g + math.dist(nb, goal), nb))
    return None


PATROL_STRIDE = 4  # weeks between patrol waypoints


def _free_near(col, row, cost, lethal):
    """Closest existing non-lethal cell in the column, searching from row."""
    for r in sorted(range(7), key=lambda r: abs(r - row)):
        if (col, r) in cost and (col, r) not in lethal:
            return (col, r)
    return None


def patrol_waypoints(weeks, cost, lethal):
    """Zig-zag waypoints top/bottom every PATROL_STRIDE weeks, ending today."""
    last = len(weeks) - 1
    points = [_free_near(0, 3, cost, lethal)]
    for i, col in enumerate(range(PATROL_STRIDE // 2, last, PATROL_STRIDE)):
        points.append(_free_near(col, 0 if i % 2 == 0 else 6, cost, lethal))
    points.append((last, weeks[-1][-1][1]))
    return [p for p in points if p is not None]


def plan(weeks):
    """Follow the patrol waypoints, planning each leg with Theta*.

    Legs with no collision-free path fall back to ignoring obstacles.
    Returns (cost, lethal, path, waypoints).
    """
    cost, lethal = build_costmap(weeks)
    waypoints = patrol_waypoints(weeks, cost, lethal)
    path = [waypoints[0]]
    for a, b in zip(waypoints, waypoints[1:]):
        leg = theta_star(cost, lethal - {a, b}, a, b) or theta_star(cost, frozenset(), a, b)
        path += leg[1:]
    return cost, lethal, path, waypoints
