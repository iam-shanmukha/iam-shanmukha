"""Minimal GitHub REST/GraphQL client (stdlib only)."""
import json
import os
import urllib.parse
import urllib.request

API = "https://api.github.com"


class GitHubError(RuntimeError):
    pass


def _token():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise GitHubError("GITHUB_TOKEN (or GH_TOKEN) must be set")
    return token


def _request(url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    req.add_header("Authorization", f"Bearer {_token()}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-readme-generator")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")[:300]
        raise GitHubError(f"{exc.code} from {url}: {body}") from exc


def rest(path, **params):
    query = f"?{urllib.parse.urlencode(params)}" if params else ""
    return _request(f"{API}{path}{query}")


def graphql(query, **variables):
    result = _request(f"{API}/graphql", {"query": query, "variables": variables})
    if result.get("errors"):
        raise GitHubError(f"GraphQL errors: {result['errors']}")
    return result["data"]
