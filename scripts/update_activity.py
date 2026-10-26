#!/usr/bin/env python3
"""Refresh activity.json from the public GitHub profile activity summary."""

from __future__ import annotations

import html
import json
import re
import sys
import urllib.request
from pathlib import Path

PROFILE_URL = (
    "https://github.com/itsgintoki"
    "?action=show&controller=profiles&tab=contributions&user_id=itsgintoki"
)
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)
OUTPUT = Path(__file__).resolve().parent.parent / "activity.json"
PERCENTAGE_KEYS = ("Commits", "Pull requests", "Code review", "Issues")


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def fetch_profile() -> str:
    request = urllib.request.Request(
        PROFILE_URL,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status != 200:
                fail(f"GitHub returned HTTP {response.status}")
            return response.read().decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001 - surface the real fetch error
        fail(f"could not fetch the GitHub profile: {exc}")
        raise


def parse_percentages(page: str) -> dict[str, int]:
    match = re.search(r'data-percentages="([^"]+)"', page)
    if not match:
        fail("could not find the activity percentage data")

    try:
        raw = json.loads(html.unescape(match.group(1)))
    except json.JSONDecodeError as exc:
        fail(f"could not parse the activity percentage data: {exc}")
        raise

    percentages: dict[str, int] = {}
    for key in PERCENTAGE_KEYS:
        value = raw.get(key) if isinstance(raw, dict) else None
        if not isinstance(value, (int, float)) or not 0 <= value <= 100:
            fail(f"invalid or missing percentage for {key!r}")
        percentages[key] = int(value)

    return percentages


def parse_contributed_to(page: str) -> tuple[list[str], int]:
    start = page.find("Contributed to")
    end = page.find("js-activity-overview-graph-container", start)
    if start == -1 or end == -1:
        fail("could not find the contributed-to summary")

    block = page[start:end]
    repos = re.findall(
        r'<a href="/([^"/]+/[^"/]+)"[^>]*data-hovercard-type="repository"',
        block,
    )
    repos = list(dict.fromkeys(repos))
    if not repos:
        fail("could not find any contributed-to repositories")

    other = re.search(r"and\s+(\d+)\s+other\s+repositor", block)
    if not other:
        normalized = re.sub(r"\s+", " ", block)
        other = re.search(r"and (\d+) other repositor", normalized)
    if not other:
        fail("could not find the count of other repositories")

    return repos, int(other.group(1))


def parse_organizations(page: str) -> list[dict[str, str]]:
    matches = re.findall(
        r'href="/itsgintoki\?tab=overview&amp;org=([^"]+)">\s*'
        r'<img[^>]*src="([^"]+)"',
        page,
    )

    organizations: list[dict[str, str]] = []
    seen: set[str] = set()
    for login, avatar in matches:
        if login in seen:
            continue
        seen.add(login)
        organizations.append(
            {
                "login": html.unescape(login),
                "avatar": html.unescape(avatar),
            }
        )

    return organizations[:3]


def main() -> None:
    page = fetch_profile()
    percentages = parse_percentages(page)
    contributed_to, other_repositories = parse_contributed_to(page)
    organizations = parse_organizations(page)

    snapshot = {
        "percentages": percentages,
        "contributedTo": contributed_to,
        "otherRepositories": other_repositories,
        "organizations": organizations,
    }

    OUTPUT.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    print(f"  percentages: {percentages}")
    print(f"  contributed to: {', '.join(contributed_to)} + {other_repositories} others")
    print(f"  organizations: {', '.join(org['login'] for org in organizations)}")


if __name__ == "__main__":
    main()
