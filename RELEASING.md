# Releasing

A release exists so the skill can be used away from a checkout of this repo:
added to regular chat as a skill, or installed into Claude Code as a plugin.
Everything below runs on Python 3 with no third-party packages.

## What a release is

One artifact: `cryptic-setter-<version>.skill`, attached to a GitHub release.

A `.skill` file is a zip whose root holds one directory named after the skill:

```
cryptic-setter/
  SKILL.md          VERSION      LICENSE
  schema/           scripts/     ui/      fixtures/
```

The plugin keeps `SKILL.md` a level deeper, under `skills/cryptic-setter/`, so
`tools/build_skill_bundle.py` hoists it. Nothing in `SKILL.md` changes between
the two shapes: it resolves paths against `$ROOT`, which is
`${CLAUDE_PLUGIN_ROOT}` in a plugin install and the folder holding `SKILL.md`
in a `.skill` install.

Only the paths in `PAYLOAD` ship, so repository furniture — the README, the CI
config, the packaging script — cannot leak into a published skill. The archive
is reproducible (sorted entries, fixed timestamps), so rebuilding a release
gives back the same bytes as its published asset.

## Cutting one

**Merging to `main` cuts the release.** The workflow reads the version from the
manifests, and if no `v<version>` tag exists yet it runs the checks, builds the
archive, tags, and publishes. A merge that leaves the version alone republishes
nothing, so ordinary changes do not produce a release.

So a release is a version bump:

1. Pick the version. Semantic versioning; while the major is 0 the puzzle
   document schema may still change between minor versions.
2. Set it in **both** manifests — `plugins/cryptic-setter/.claude-plugin/plugin.json`
   and the `cryptic-setter` entry in `.claude-plugin/marketplace.json`. They
   must agree, since the tag comes from them.
3. Add the version's section to `CHANGELOG.md`. The release notes are built
   from it, and a version with no section will not release. CI checks this on
   any pull request that bumps the version, so a missing section fails before
   the merge rather than after it.
4. Run the release checks locally:

   ```bash
   make release-check
   ```

5. Open the pull request, get it green, merge.

The version bump *is* the release, so keep it in its own pull request, or at
least be deliberate about which merge carries it.

If a release run fails partway, fix the cause and re-run the workflow from the
Actions tab — it is idempotent, since it skips any version whose tag already
exists.

## Verifying afterwards

`make bundle` already unpacks the archive it just built and runs the scripts
inside it, so a dropped file fails at build time. What that cannot check is the
install itself:

```bash
unzip cryptic-setter-0.1.0.skill -d /tmp/skill-check
cd /tmp/skill-check
python3 cryptic-setter/scripts/build_ui.py \
    cryptic-setter/fixtures/first-light-good.json -o /tmp/first-light.html
```

Open the page and solve a clue or two. Then add the `.skill` to chat and ask
for a crossword, which is the thing the release is for.

## Installing what you released

**Chat.** Download the `.skill` asset from the release and add it under
Settings -> Capabilities -> Skills.

**Claude Code.** The marketplace tracks `main`, not the release:

```
/plugin marketplace add RolynTrotter/vibe-cryptic
/plugin install cryptic-setter@vibe-cryptic
```
