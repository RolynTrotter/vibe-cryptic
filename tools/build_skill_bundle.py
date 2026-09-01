#!/usr/bin/env python3
"""Package the plugin's skill as a .skill archive regular chat can install.

    python3 tools/build_skill_bundle.py            # dist/cryptic-setter-<version>.skill
    python3 tools/build_skill_bundle.py --print-version

A Claude Code plugin and an uploadable skill want different shapes. The plugin
keeps SKILL.md under skills/<name>/ and its data beside it under the plugin
root; an uploaded skill is one folder with SKILL.md at the top and everything
it reads underneath. This hoists the first into the second, so `$ROOT` means
the same directory in both installs and no path in SKILL.md has to change.

The version comes from plugin.json and must agree with marketplace.json, since
those are what the plugin install reads. Only PAYLOAD ships, so repository
furniture — CI config, the README, this script — cannot leak into a published
skill. The archive is byte-identical for identical inputs: entries sorted,
timestamps fixed, so rebuilding a release reproduces its asset.
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
NAME = "cryptic-setter"
SKILL_MD = os.path.join(PLUGIN, "skills", NAME, "SKILL.md")
MARKETPLACE = os.path.join(REPO, ".claude-plugin", "marketplace.json")
PLUGIN_JSON = os.path.join(PLUGIN, ".claude-plugin", "plugin.json")

# Runtime data the skill reads. Anything not listed here does not ship.
PAYLOAD = ["schema", "scripts", "ui", "fixtures", "references", "data"]
EXCLUDE_DIRS = {"__pycache__", ".claude-plugin"}
EXCLUDE_SUFFIXES = (".pyc",)

# Fixed zip timestamp (the DOS epoch) so the archive is reproducible.
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


def resolve_version():
    """The one version both manifests state, or an error naming the disagreement."""
    with open(PLUGIN_JSON) as fh:
        plugin = json.load(fh)
    with open(MARKETPLACE) as fh:
        marketplace = json.load(fh)
    listed = [p for p in marketplace["plugins"] if p["name"] == plugin["name"]]
    if not listed:
        raise SystemExit("marketplace.json lists no plugin named %r" % plugin["name"])
    found = {
        "plugin.json": plugin["version"],
        "marketplace.json": listed[0]["version"],
    }
    if len(set(found.values())) > 1:
        raise SystemExit(
            "version mismatch:\n%s"
            % "\n".join("  %s: %s" % kv for kv in sorted(found.items()))
        )
    version = found["plugin.json"]
    if not all(part.isdigit() for part in version.split(".")) or version.count(".") != 2:
        raise SystemExit("version %r is not MAJOR.MINOR.PATCH" % version)
    return version


def payload_files():
    """Every file that goes in the archive, as (source path, path within it)."""
    files = [(SKILL_MD, "SKILL.md")]
    license_path = os.path.join(REPO, "LICENSE")
    if os.path.exists(license_path):
        files.append((license_path, "LICENSE"))
    for top in PAYLOAD:
        root_dir = os.path.join(PLUGIN, top)
        if not os.path.isdir(root_dir):
            raise SystemExit("missing from the plugin: %s" % top)
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)
            for name in sorted(filenames):
                if name.endswith(EXCLUDE_SUFFIXES):
                    continue
                src = os.path.join(dirpath, name)
                files.append((src, os.path.relpath(src, PLUGIN)))
    return files


def stage(version, staging):
    """Lay the skill out on disk under staging/<name>/, the shape it ships in."""
    if os.path.exists(staging):
        shutil.rmtree(staging)
    root = os.path.join(staging, NAME)
    for src, rel in payload_files():
        dst = os.path.join(root, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    with open(os.path.join(root, "VERSION"), "w") as fh:
        fh.write("%s\n" % version)
    return root


def write_archive(root, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    entries = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)
        for name in sorted(filenames):
            if name.endswith(EXCLUDE_SUFFIXES):
                continue
            src = os.path.join(dirpath, name)
            arc = "%s/%s" % (NAME, os.path.relpath(src, root).replace(os.sep, "/"))
            entries.append((arc, src))
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for arc, src in sorted(entries):
            info = zipfile.ZipInfo(arc, date_time=ZIP_EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if os.access(src, os.X_OK) else 0o644) << 16
            with open(src, "rb") as fh:
                zf.writestr(info, fh.read())
    return entries


def verify(archive, workdir):
    """Unpack what was just built and run it, the way an install would.

    Checking the archive rather than the tree it was built from is the point: a
    file left out of PAYLOAD, or a script still reaching back into the working
    tree, fails here rather than in someone's chat.
    """
    if os.path.exists(workdir):
        shutil.rmtree(workdir)
    os.makedirs(workdir)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(workdir)
    root = os.path.join(workdir, NAME)
    if not os.path.isfile(os.path.join(root, "SKILL.md")):
        raise SystemExit("archive has no %s/SKILL.md at its root" % NAME)

    fixtures = [
        os.path.join(root, "fixtures", "first-light-good.json"),
        os.path.join(root, "fixtures", "behind-bars-good.json"),
    ]
    body = os.path.join(workdir, "verify-body.html")
    steps = [
        [sys.executable, os.path.join(root, "scripts", "validate.py")] + fixtures,
        [sys.executable, os.path.join(root, "scripts", "test_fixtures.py")],
        [sys.executable, os.path.join(root, "scripts", "build_ui.py"),
         fixtures[0], "--artifact-body", "-o", body],
    ]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    for step in steps:
        result = subprocess.run(
            step, cwd=workdir, env=env, capture_output=True, text=True
        )
        if result.returncode != 0:
            sys.stderr.write(result.stdout + result.stderr)
            raise SystemExit(
                "archive verification failed: %s" % os.path.basename(step[1])
            )
    if not os.path.getsize(body):
        raise SystemExit("archive verification produced an empty page")
    shutil.rmtree(workdir)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--print-version", action="store_true",
        help="print the version the manifests agree on and exit",
    )
    parser.add_argument("--out", default=os.path.join(REPO, "dist"))
    parser.add_argument(
        "--skip-verify", action="store_true",
        help="do not run the built archive (for debugging the packaging only)",
    )
    args = parser.parse_args()

    version = resolve_version()
    if args.print_version:
        print(version)
        return

    root = stage(version, os.path.join(args.out, "stage"))
    out_path = os.path.join(args.out, "%s-%s.skill" % (NAME, version))
    entries = write_archive(root, out_path)
    if not args.skip_verify:
        verify(out_path, os.path.join(args.out, "verify"))
    shutil.rmtree(os.path.join(args.out, "stage"))
    print(
        "%s  (%d files, %s bytes)"
        % (os.path.relpath(out_path, REPO), len(entries),
           format(os.path.getsize(out_path), ","))
    )


if __name__ == "__main__":
    main()
