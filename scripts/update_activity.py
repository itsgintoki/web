#!/usr/bin/env python3
"""Refresh activity.json from the GitHub GraphQL API.

The scheduled workflow supplies GITHUB_TOKEN to this script. The token never
reaches the browser; only the generated activity snapshot is published.
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://api.github.com/graphql"
USER_AGENT = "itsgintoki-portfolio-activity/1.0"
OUTPUT = Path(__file__).resolve().parent.parent / "activity.json"
METRICS = ("Commits", "Pull requests", "Code review", "Issues")

QUERY = """
query PortfolioActivity($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
      commitContributionsByRepository(maxRepositories: 100) {
        repository {
          nameWithOwner
          owner {
            __typename
            login
            avatarUrl
          }
        }
        contributions {
          totalCount
        }
      }
      issueContributionsByRepository(maxRepositories: 100) {
        repository {
          nameWithOwner
          owner {
            __typename
            login
            avatarUrl
          }
        }
        contributions {
          totalCount
        }
      }
      pullRequestContributionsByRepository(maxRepositories: 100) {
        repository {
          nameWithOwner
          owner {
            __typename
            login
            avatarUrl
          }
        }
        contributions {
          totalCount
        }
      }
      pullRequestReviewContributionsByRepository(maxRepositories: 100) {
        repository {
          nameWithOwner
          owner {
            __typename
            login
            avatarUrl
          }
        }
        contributions {
          totalCount
        }
      }
    }
    repositoriesContributedTo(
      first: 10
      contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, PULL_REQUEST_REVIEW]
      includeUserRepositories: true
    ) {
      totalCount
      nodes {
        nameWithOwner
        owner {
          __typename
          login
          avatarUrl
        }
      }
    }
  }
}
"""


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def github_token() -> str:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        fail("set GITHUB_TOKEN (or GH_TOKEN) to a GitHub API token")
    return token.strip()


def fetch_activity(login: str) -> dict:
    payload = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    request = urllib.request.Request(
        API_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {github_token()}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        fail(f"GitHub API returned HTTP {exc.code}: {detail[:600]}")
        raise
    except Exception as exc:  # noqa: BLE001 - surface the real request error
        fail(f"could not query the GitHub API: {exc}")
        raise

    try:
        result = json.loads(body)
    except json.JSONDecodeError as exc:
        fail(f"could not parse the GitHub API response: {exc}")
        raise

    if result.get("errors"):
        messages = "; ".join(
            str(error.get("message", "unknown error"))
            for error in result["errors"]
        )
        fail(f"GitHub API error: {messages}")

    user = result.get("data", {}).get("user")
    if not isinstance(user, dict):
        fail(f"GitHub user {login!r} was not found")

    return user


def percentage_mix(counts: dict[str, int]) -> dict[str, int]:
    """Round percentages with the largest-remainder method so they total 100."""
    total = sum(counts.values())
    if total <= 0:
        return {metric: 0 for metric in METRICS}

    raw = {metric: counts[metric] * 100 / total for metric in METRICS}
    rounded = {metric: math.floor(raw[metric]) for metric in METRICS}
    remainder = 100 - sum(rounded.values())

    ranked = sorted(
        METRICS,
        key=lambda metric: (raw[metric] - rounded[metric], -METRICS.index(metric)),
        reverse=True,
    )
    for metric in ranked[:remainder]:
        rounded[metric] += 1

    return rounded


def collect_repositories(collection: dict) -> dict[str, dict]:
    repositories: dict[str, dict] = {}
    groups = (
        "commitContributionsByRepository",
        "issueContributionsByRepository",
        "pullRequestContributionsByRepository",
        "pullRequestReviewContributionsByRepository",
    )

    for group in groups:
        for entry in collection.get(group) or []:
            repository = entry.get("repository") or {}
            name = repository.get("nameWithOwner")
            owner = repository.get("owner") or {}
            if not isinstance(name, str) or not re.fullmatch(
                r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", name
            ):
                continue

            count = entry.get("contributions", {}).get("totalCount", 0)
            if not isinstance(count, int) or count < 0:
                count = 0

            record = repositories.setdefault(
                name,
                {
                    "name": name,
                    "count": 0,
                    "owner": {
                        "type": owner.get("__typename"),
                        "login": owner.get("login"),
                        "avatar": owner.get("avatarUrl"),
                    },
                },
            )
            record["count"] += count

    return repositories


def fallback_repositories(connection: dict) -> dict[str, dict]:
    repositories: dict[str, dict] = {}
    for node in connection.get("nodes") or []:
        name = node.get("nameWithOwner")
        owner = node.get("owner") or {}
        if not isinstance(name, str) or not re.fullmatch(
            r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", name
        ):
            continue
        repositories[name] = {
            "name": name,
            "count": 0,
            "owner": {
                "type": owner.get("__typename"),
                "login": owner.get("login"),
                "avatar": owner.get("avatarUrl"),
            },
        }
    return repositories


def build_snapshot(login: str, user: dict) -> dict:
    collection = user.get("contributionsCollection")
    if not isinstance(collection, dict):
        fail("GitHub API response did not include a contributions collection")

    counts = {
        "Commits": collection.get("totalCommitContributions", 0),
        "Pull requests": collection.get("totalPullRequestContributions", 0),
        "Code review": collection.get("totalPullRequestReviewContributions", 0),
        "Issues": collection.get("totalIssueContributions", 0),
    }
    for metric, value in counts.items():
        if not isinstance(value, int) or value < 0:
            fail(f"invalid {metric} contribution count from the GitHub API")

    calendar = collection.get("contributionCalendar") or {}
    total_contributions = calendar.get("totalContributions")
    if not isinstance(total_contributions, int) or total_contributions < 0:
        fail("invalid contribution calendar total from the GitHub API")

    days: list[dict[str, object]] = []
    for week in calendar.get("weeks") or []:
        for day in week.get("contributionDays") or []:
            date = day.get("date")
            count = day.get("contributionCount")
            if not isinstance(date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                continue
            if not isinstance(count, int) or count < 0:
                continue
            days.append({"date": date, "count": count})

    if not days:
        fail("GitHub API response did not include contribution calendar days")
    days.sort(key=lambda day: day["date"])

    max_count = max(int(day["count"]) for day in days)
    for day in days:
        count = int(day["count"])
        day["level"] = 0 if max_count == 0 else min(4, math.ceil(count / max_count * 4))

    repositories = collect_repositories(collection)
    contributed_connection = user.get("repositoriesContributedTo") or {}
    if not repositories:
        repositories = fallback_repositories(contributed_connection)

    ordered = sorted(
        repositories.values(),
        key=lambda repository: (-repository["count"], repository["name"].lower()),
    )
    top_repositories = [repository["name"] for repository in ordered[:3]]
    total_repositories = contributed_connection.get("totalCount")
    if not isinstance(total_repositories, int) or total_repositories < 0:
        total_repositories = len(repositories)
    other_repositories = max(0, total_repositories - len(top_repositories))

    organizations: list[dict[str, str]] = []
    seen: set[str] = set()
    for repository in ordered:
        owner = repository["owner"]
        login_name = owner.get("login")
        avatar = owner.get("avatar")
        if owner.get("type") != "Organization":
            continue
        if not isinstance(login_name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", login_name):
            continue
        if not isinstance(avatar, str) or not avatar.startswith("https://"):
            continue
        if login_name in seen:
            continue
        seen.add(login_name)
        organizations.append({"login": login_name, "avatar": avatar})
        if len(organizations) == 3:
            break

    return {
        "percentages": percentage_mix(counts),
        "contributedTo": top_repositories,
        "otherRepositories": other_repositories,
        "organizations": organizations,
        "totalContributions": total_contributions,
        "contributions": days,
    }


def main() -> None:
    login = (os.environ.get("GITHUB_LOGIN") or "itsgintoki").strip()
    if not re.fullmatch(r"[A-Za-z0-9-]+", login):
        fail("GITHUB_LOGIN must be a valid GitHub username")

    snapshot = build_snapshot(login, fetch_activity(login))
    OUTPUT.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {OUTPUT}")
    print(f"  total contributions: {snapshot['totalContributions']}")
    print(f"  percentages: {snapshot['percentages']}")
    print(
        "  contributed to: "
        + ", ".join(snapshot["contributedTo"])
        + f" + {snapshot['otherRepositories']} others"
    )
    print(
        "  organizations: "
        + ", ".join(org["login"] for org in snapshot["organizations"])
    )


if __name__ == "__main__":
    main()
