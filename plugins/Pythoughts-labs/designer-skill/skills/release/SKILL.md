---
name: release
description: Release designer-skill-mcp to npm with a git tag and GitHub release. Use when the user asks to ship, publish, cut a release, bump version, push tags, or run npm publish for designer-skill-mcp.
---

# release

Ship **designer-skill-mcp** in one ordered sequence: version bump → build/test → commit → tag → push → npm → GitHub release.

## Default version bump

**Every release bumps the minor version by 0.1.0 and resets patch to 0**, unless you pass an explicit semver to the script.

| Current | Next (default) |
|---------|----------------|
| `0.10.0` | `0.11.0` |
| `0.11.0` | `0.12.0` |
| `0.9.1` | `0.10.0` |

Rule: `{major}.{minor + 1}.0` — never auto-bump patch. Use an explicit version only for hotfixes (e.g. `./scripts/release.sh 0.11.1 "hotfix"`).

## Preflight

1. **Commit and push all feature work first.** The release script only commits version bump files.
2. Working tree must be clean except intentional release edits.
3. `npm whoami` must succeed (logged in as a publisher for `designer-skill-mcp`).
4. `gh auth status` must succeed (active account: **`elkaix`** — branch protection on `main`).
5. After release, update doc pins in `README.md` and `commands/designer-setup.md` (`@latest` → `@<new-version>`).

## Version touchpoints (keep in sync)

| File | Field |
|---|---|
| `designer-skill-mcp/package.json` | `"version"` |
| `designer-skill-mcp/package-lock.json` | top-level `"version"` |
| `designer-skill-mcp/server.json` | `"version"` + `packages[0].version` |
| `.claude-plugin/plugin.json` | `"version"` |
| `.codex-plugin/plugin.json` | `"version"` |
| `.cursor-plugin/plugin.json` | `"version"` |
| `README.md` | pin example (`@0.11.0`) |
| `commands/designer-setup.md` | pin example (`@0.11.0`) |

Tag format: `v{semver}` (e.g. `v0.11.0`).

## Automated (preferred)

From repo root:

```bash
chmod +x scripts/release.sh

# Default: auto-bump minor (+0.1.0), e.g. 0.10.0 → 0.11.0
./scripts/release.sh "Short release notes for GitHub and the tag body."

# Override only when you need a patch or major bump
./scripts/release.sh 0.11.1 "Hotfix: …"
./scripts/release.sh 1.0.0 "Breaking: …"
```

The script runs this sequence:

1. Resolve version (auto minor bump, or use explicit semver)
2. `npm version <semver> --no-git-tag-version` in `designer-skill-mcp/`
3. Sync plugin manifests + `server.json`
4. `npm run build` + `npm test`
5. Commit version files with a release message
6. Annotated tag `v<semver>`
7. `git push origin HEAD` + `git push origin v<semver>`
8. `npm publish --access public` from `designer-skill-mcp/`
9. `mcp-publisher publish` from `designer-skill-mcp/` (if installed and logged in)
10. `gh release create v<semver>`
11. Update `README.md` and `commands/designer-setup.md` pin examples, commit, push

## Manual sequence (when not using the script)

```bash
cd designer-skill-mcp
npm version 0.11.0 --no-git-tag-version --allow-same-version
# Sync plugin.json + server.json versions (see table above)
npm run build && npm test
cd ..
git add designer-skill-mcp/package.json designer-skill-mcp/package-lock.json \
  designer-skill-mcp/server.json \
  .claude-plugin/plugin.json .codex-plugin/plugin.json .cursor-plugin/plugin.json
git commit -m "Release designer-skill-mcp v0.11.0."
git tag -a v0.11.0 -m "designer-skill-mcp v0.11.0"
git push origin HEAD && git push origin v0.11.0
cd designer-skill-mcp && npm publish --access public
(cd designer-skill-mcp && mcp-publisher publish) 2>/dev/null || true
gh release create v0.11.0 --title "designer-skill-mcp v0.11.0" --notes "Release notes."
```

## Verify

```bash
git tag -l 'v0.1*'
npm view designer-skill-mcp version
gh release view v0.11.0
cd designer-skill-mcp && npm test
```

## Do not

- Skip `npm test` or `npm run build` before publish (`prepublishOnly` also runs them, but verify locally first).
- Publish from a dirty tree or without committing version bumps.
- Use `--force` on npm publish unless explicitly recovering a failed release.
- Add `Co-authored-by` or agent attribution lines to commit or tag messages.
- Auto-bump patch for routine releases — default is always **+0.1.0 minor**.
