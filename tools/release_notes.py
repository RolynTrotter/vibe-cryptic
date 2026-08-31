#!/usr/bin/env python3
"""Print the release notes for one version: its CHANGELOG section, plus install.

    python3 tools/release_notes.py 0.1.0

Fails if CHANGELOG.md has no section for the version, so a release cannot go
out undocumented.
"""

import argparse
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHANGELOG = os.path.join(REPO, "CHANGELOG.md")
HEADING = re.compile(r"^## \[?(\d+\.\d+\.\d+[^\]\s]*)\]?")

INSTALL = """
## Installing

**In chat** — download `cryptic-setter-{version}.zip` below and upload it as a
skill in Settings -> Capabilities -> Skills. Then ask for a cryptic crossword.

**In Claude Code** — install the plugin, which tracks `main` rather than this tag:

```
/plugin marketplace add RolynTrotter/vibe-cryptic
/plugin install cryptic-setter@vibe-cryptic
```
"""


def section(version):
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
    if not collecting and not body:
        raise SystemExit(
            "CHANGELOG.md has no section for %s — add one before tagging" % version
        )
    return "\n".join(body).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("version")
    args = parser.parse_args()
    version = args.version.lstrip("v")
    sys.stdout.write(section(version) + "\n" + INSTALL.format(version=version))


if __name__ == "__main__":
    main()
