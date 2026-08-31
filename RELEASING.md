# Releasing

A release exists so the skill can be used away from a checkout of this repo:
uploaded into regular chat as a skill bundle, or installed into Claude Code as
a plugin. Everything below runs on Python 3 with no third-party packages.

## What a release is

One artifact: `cryptic-setter-<version>.zip`, attached to a GitHub release.

Inside it is a single folder, `cryptic-setter/`, with `SKILL.md` at the top and
the schema, scripts, solver UI and fixtures underneath — the shape an uploaded
skill has to have. The plugin keeps `SKILL.md` one level deeper, under
`skills/cryptic-setter/`, so `tools/build_skill_bundle.py` hoists it. Nothing
in `SKILL.md` changes between the two: it resolves paths against `$ROOT`, which
is `${CLAUDE_PLUGIN_ROOT}` in a plugin install and the folder holding `SKILL.md`
in a bundle install.

The zip is reproducible — sorted entries, fixed timestamps — so rebuilding a
tag gives back the same bytes as the asset that tag published.

## Cutting one

1. Pick the version. Semantic versioning; while the major is 0 the puzzle
   document schema may still change between minor versions.
2. Set it in **both** manifests — `plugins/cryptic-setter/.claude-plugin/plugin.json`
   and the `cryptic-setter` entry in `.claude-plugin/marketplace.json`. They
   must agree with each other and with the tag, or the release fails.
3. Add the version's section to `CHANGELOG.md`. The release notes are read from
   it, and a version with no section will not release.
4. Run the release checks locally:

   ```bash
   make release-check
   ```

5. Merge to `main`, then tag it and push:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

The `release` workflow then re-runs the calibration tests, rebuilds the bundle
with `--expect-version` bound to the tag, and publishes the release with the
zip attached. If a tag was pushed before the workflow existed, or a run needs
repeating, run the workflow by hand from the Actions tab with the tag as its
input — it updates an existing release in place rather than failing.

A tag with a suffix (`v0.2.0-rc1`) publishes as a prerelease.

## Verifying afterwards

Download the asset, unzip it somewhere outside this repo, and run it as an
installed skill would:

```bash
unzip cryptic-setter-0.1.0.zip -d /tmp/skill-check
cd /tmp/skill-check
python3 cryptic-setter/scripts/validate.py cryptic-setter/fixtures/first-light-good.json
python3 cryptic-setter/scripts/build_ui.py \
    cryptic-setter/fixtures/first-light-good.json -o /tmp/first-light.html
```

Then open the page and solve a clue or two. `make bundle` already runs those
scripts against the staged copy before zipping it; this is the same check
against what actually shipped.

## Installing what you released

**Chat.** Download the zip from the release and upload it under
Settings -> Capabilities -> Skills. Then ask for a cryptic crossword.

**Claude Code.** The marketplace tracks `main`, not the tag:

```
/plugin marketplace add RolynTrotter/vibe-cryptic
/plugin install cryptic-setter@vibe-cryptic
```
