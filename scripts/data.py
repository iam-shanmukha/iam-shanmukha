"""Fetch contribution data and organise it into display groups."""
from dataclasses import dataclass, field
from fnmatch import fnmatch

import gh_api

CALENDAR_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date weekday } }
      }
    }
  }
}
"""


@dataclass(frozen=True)
class PullRequest:
    repo: str
    number: int
    title: str
    url: str
    merged: bool
    date: str


@dataclass(frozen=True)
class Group:
    node: str
    label: str
    blurb: str
    topics: str
    stars: int
    merged: tuple = field(default_factory=tuple)
    open: tuple = field(default_factory=tuple)


def fetch_calendar(login):
    data = gh_api.graphql(CALENDAR_QUERY, login=login)
    cal = data["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [
        [(d["date"], d["weekday"], d["contributionCount"]) for d in w["contributionDays"]]
        for w in cal["weeks"]
    ]
    return cal["totalContributions"], weeks


def _search_prs(login, state):
    query = f"author:{login} type:pr is:public " + ("is:merged" if state == "merged" else "is:open")
    items = gh_api.rest("/search/issues", q=query, per_page=100, sort="created", order="desc")["items"]
    prs = []
    for item in items:
        repo = item["repository_url"].split("/repos/", 1)[1]
        prs.append(PullRequest(
            repo=repo,
            number=item["number"],
            title=item["title"].strip(),
            url=item["html_url"],
            merged=state == "merged",
            date=(item.get("closed_at") or item["created_at"])[:10],
        ))
    return prs


def _stars(repo, cache):
    if repo not in cache:
        cache[repo] = gh_api.rest(f"/repos/{repo}")["stargazers_count"]
    return cache[repo]


def _matches(repo, patterns):
    return any(fnmatch(repo.lower(), p.lower()) for p in patterns)


def build_groups(config):
    login = config["login"]
    skip = [f"{login}/*", *config.get("exclude", [])]
    merged = [p for p in _search_prs(login, "merged") if not _matches(p.repo, skip)]
    opened = [p for p in _search_prs(login, "open") if not _matches(p.repo, skip)]
    cache = {}
    groups, claimed = [], set()

    for spec in config["groups"]:
        g_merged = tuple(p for p in merged if _matches(p.repo, spec["match"]))
        g_open = tuple(p for p in opened if _matches(p.repo, spec["match"]))
        claimed.update(p.repo for p in g_merged)
        if g_merged:
            groups.append(Group(spec["node"], spec["label"], spec["blurb"], spec["topics"],
                                _stars(spec["star_repo"], cache), g_merged, g_open))

    # Auto-promote any new big repo that isn't configured yet.
    for repo in dict.fromkeys(p.repo for p in merged if p.repo not in claimed):
        stars = _stars(repo, cache)
        if stars >= config["auto_include_min_stars"]:
            name = repo.split("/")[1].lower().replace("-", "_")
            groups.append(Group(f"/{name}", name, repo, "/contributions", stars,
                                tuple(p for p in merged if p.repo == repo),
                                tuple(p for p in opened if p.repo == repo)))
    return groups
