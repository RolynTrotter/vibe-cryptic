#!/usr/bin/env python3
"""Print the release notes for one version, ready to hand to `gh release`.

    python3 tools/release_notes.py 0.1.0

The notes are the version's CHANGELOG section, then how to install the asset,
then the commits since the previous tag. Fails if CHANGELOG.md has no section
for the version, so a release cannot go out undocumented — CI checks the same
thing on any pull request that bumps the version, where it can still be fixed.
"""

import argparse
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHANGELOG = os.path.join(REPO, "CHANGELOG.md")
HEADING = re.compile(r"^## \[?(\d+\.\d+\.\d+[^\]\s]*)\]?")

INSTALL = """
## Installing

**In chat** — download `cryptic-setter-{version}.skill` below and add it as a
skill under Settings -> Capabilities -> Skills. Then ask for a cryptic crossword.

**In Claude Code** — install the plugin, which tracks `main` rather than this
release:

```
/plugin marketplace add RolynTrotter/vibe-cryptic
/plugin install cryptic-setter@vibe-cryptic
```
"""


def section(version):
    """The CHANGELOG body under the heading for this version."""
    with open(CHANGELOG) as fh:
        lines = fh.read().splitlines()
    body, collecting = [], False
    for line in lines:
        match = HEADING.match(line)
        if match:
            if collecting:
                break
            collecting = match.group(1) == version
            continue
        if collecting:
            body.append(line)
    if not body:
        raise SystemExit(
            "CHANGELOG.md has no section for %s — add one before releasing"
            % version
        )
    return "\n".join(body).strip()


def git(*args):
    result = subprocess.run(
        ("git",) + args, cwd=REPO, capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def commits():
    """The one-line log since the previous release, if the history is there.

    Shallow clones and a first release both leave this empty, which is fine —
    the CHANGELOG section is what the notes are actually built on.
    """
    previous = git("describe", "--tags", "--abbrev=0", "--match", "v*")
    log = git("log", "--no-merges", "--pretty=- %s", "%s..HEAD" % previous) \
        if previous else git("log", "--no-merges", "--pretty=- %s")
    if not log:
        return ""
    since = "since %s" % previous if previous else "in this release"
    return "\n## Commits %s\n\n%s\n" % (since, log)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("version")
    parser.add_argument(
        "--check", action="store_true",
        help="only check that the version has a CHANGELOG section; print nothing",
    )
    args = parser.parse_args()
    version = args.version.lstrip("v")
    body = section(version)
    if args.check:
        print("CHANGELOG.md documents %s" % version)
        return
    sys.stdout.write(
        body + "\n" + INSTALL.format(version=version) + commits()
    )


if __name__ == "__main__":
    main()
