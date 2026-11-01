#!/usr/bin/env python3
"""Regenerate the 主要项目 table in README.md from the repos' own descriptions.

The table used to be hand-written, so it went stale the moment a repo's
description changed (it drifted within minutes). Now the repo description is the
single source of truth and this table is derived from it.

    python scripts/update_projects.py            # rewrite README.md
    python scripts/update_projects.py --check    # exit 1 if README is stale

Run by .github/workflows/update-projects.yml daily and on demand.
"""
import argparse
import json
import os
import pathlib
import sys
import urllib.request

OWNER = "70asunflower"

# Display order of the pinned repos.
REPOS = [
    "ai-learning-journey",
    "ic-chip-design-learning",
    "ChatShot",
    "70asunflower-skills",
]

START, END = "<!-- PROJECTS:START -->", "<!-- PROJECTS:END -->"
README = pathlib.Path(__file__).resolve().parent.parent / "README.md"


def fetch(repo: str) -> dict:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{OWNER}/{repo}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "update-projects",
            **({"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}
               if os.environ.get("GITHUB_TOKEN") else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def render() -> str:
    rows = ["| 项目 | 介绍 |", "| :--- | :--- |"]
    for repo in REPOS:
        d = fetch(repo)
        desc = (d.get("description") or "").replace("|", "\\|").strip()
        if not desc:
            desc = "_（仓库还没有 Description）_"
        rows.append(f'| [**{d["name"]}**]({d["html_url"]}) | {desc} |')
    return "\n".join(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    text = README.read_text(encoding="utf-8")
    i, j = text.find(START), text.find(END)
    if i < 0 or j < 0:
        raise SystemExit(f"README.md: missing {START} / {END}")

    table = render()
    new = text[:i + len(START)] + "\n" + table + "\n" + text[j:]
    if new == text:
        print("projects table already up to date")
        return 0
    if args.check:
        print("projects table is stale — run scripts/update_projects.py")
        return 1
    README.write_text(new, encoding="utf-8", newline="\n")
    print(f"rewrote projects table ({len(REPOS)} repos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
