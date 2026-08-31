#!/usr/bin/env python3
"""Package the plugin's skill as a standalone bundle regular chat can install.

    python3 tools/build_skill_bundle.py                    # dist/cryptic-setter-<version>.zip
    python3 tools/build_skill_bundle.py --expect-version 0.1.0

A Claude Code plugin and an uploadable skill want different shapes. The plugin
keeps SKILL.md under skills/<name>/ and its data beside it under the plugin
root; an uploaded skill is one folder with SKILL.md at the top and everything
it reads underneath. This hoists the first into the second, so `$ROOT` means
the same directory in both installs and no path in SKILL.md has to change.

The zip is byte-identical for identical inputs: entries are sorted and stamped
with a fixed timestamp, so rebuilding a tag reproduces its asset.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(REPO, "plugins", "cryptic-setter")
SKILL_MD = os.path.join(PLUGIN, "skills", "cryptic-setter", "SKILL.md")
MARKETPLACE = os.path.join(REPO, ".claude-plugin", "marketplace.json")
PLUGIN_JSON = os.path.join(PLUGIN, ".claude-plugin", "plugin.json")

# Runtime data the skill reads. Anything not listed here does not ship.
PAYLOAD = ["schema", "scripts", "ui", "fixtures"]
EXCLUDE_DIRS = {"__pycache__", ".claude-plugin"}
EXCLUDE_SUFFIXES = (".pyc",)

# Fixed zip timestamp (the DOS epoch) so the archive is reproducible.
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


def versions():
    """The version as each manifest states it, keyed by where it was found."""
    with open(PLUGIN_JSON) as fh:
        plugin = json.load(fh)
    with open(MARKETPLACE) as fh:
        marketplace = json.load(fh)
    entries = [p for p in marketplace["plugins"] if p["name"] == plugin["name"]]
    if not entries:
        raise SystemExit(
            "marketplace.json lists no plugin named %r" % plugin["name"]
        )
    return {
        "plugin.json": plugin["version"],
        "marketplace.json": entries[0]["version"],
    }


def resolve_version(expected=None):
    """One agreed version, or an error naming every manifest that disagrees."""
    found = versions()
    if expected is not None:
        found["--expect-version"] = expected
    distinct = sorted(set(found.values()))
    if len(distinct) > 1:
        listing = "\n".join("  %s: %s" % (k, v) for k, v in sorted(found.items()))
        raise SystemExit("version mismatch:\n%s" % listing)
    return distinct[0]


def payload_files():
    """Every file that goes in the bundle, as (source path, bundle path)."""
    files = [(SKILL_MD, "SKILL.md")]
    license_path = os.path.join(REPO, "LICENSE")
    if os.path.exists(license_path):
        files.append((license_path, "LICENSE"))
    for top in PAYLOAD:
        root_dir = os.path.join(PLUGIN, top)
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)
            for name in sorted(filenames):
                if name.endswith(EXCLUDE_SUFFIXES):
                    continue
                src = os.path.join(dirpath, name)
                files.append((src, os.path.relpath(src, PLUGIN)))
    return files


def stage(version, staging):
    """Lay the bundle out on disk under staging/cryptic-setter/."""
    root = os.path.join(staging, "cryptic-setter")
    if os.path.exists(staging):
        shutil.rmtree(staging)
    for src, rel in payload_files():
        dst = os.path.join(root, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    with open(os.path.join(root, "VERSION"), "w") as fh:
        fh.write("%s\n" % version)
    return root


def verify(root):
    """Prove the staged copy stands alone: validate a fixture, build a page.

    Runs the staged scripts by absolute path from the staging directory, not
    from the repo root, so a bundle that dropped a file or still reaches back
    into the working tree fails here rather than in someone's chat.
    """
    staging = os.path.dirname(root)
    body = os.path.join(staging, "verify-body.html")
    fixtures = [
        os.path.join(root, "fixtures", "first-light-good.json"),
        os.path.join(root, "fixtures", "behind-bars-good.json"),
    ]
    steps = [
        [sys.executable, os.path.join(root, "scripts", "validate.py")] + fixtures,
        [sys.executable, os.path.join(root, "scripts", "test_fixtures.py")],
        [
            sys.executable,
            os.path.join(root, "scripts", "build_ui.py"),
            fixtures[0],
            "--artifact-body",
            "-o",
            body,
        ],
    ]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    for step in steps:
        result = subprocess.run(
            step, cwd=staging, env=env, capture_output=True, text=True
        )
        if result.returncode != 0:
            sys.stderr.write(result.stdout + result.stderr)
            raise SystemExit(
                "bundle verification failed: %s" % os.path.basename(step[1])
            )
    if not os.path.getsize(body):
        raise SystemExit("bundle verification produced an empty page")
    os.remove(body)


def write_zip(root, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    entries = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)
        for name in sorted(filenames):
            if name.endswith(EXCLUDE_SUFFIXES):
                continue
            src = os.path.join(dirpath, name)
            arc = os.path.join(
                "cryptic-setter", os.path.relpath(src, root)
            ).replace(os.sep, "/")
            entries.append((arc, src))
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for arc, src in sorted(entries):
            info = zipfile.ZipInfo(arc, date_time=ZIP_EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if os.access(src, os.X_OK) else 0o644
            info.external_attr = mode << 16
            with open(src, "rb") as fh:
                zf.writestr(info, fh.read())
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--expect-version",
        help="fail unless the manifests all state this version (used by the "
             "release workflow to hold the git tag and the manifests together)",
    )
    parser.add_argument("--out-dir", default=os.path.join(REPO, "dist"))
    parser.add_argument(
        "--skip-verify", action="store_true",
        help="skip running the staged copy (for debugging the packaging only)",
    )
    args = parser.parse_args()

    version = resolve_version(args.expect_version)
    staging = os.path.join(args.out_dir, "skill")
    root = stage(version, staging)
    if not args.skip_verify:
        verify(root)
    out_path = os.path.join(args.out_dir, "cryptic-setter-%s.zip" % version)
    entries = write_zip(root, out_path)
    print(
        "wrote %s (%d files, %s bytes)"
        % (os.path.relpath(out_path, REPO), len(entries), f"{os.path.getsize(out_path):,}")
    )


if __name__ == "__main__":
    main()
