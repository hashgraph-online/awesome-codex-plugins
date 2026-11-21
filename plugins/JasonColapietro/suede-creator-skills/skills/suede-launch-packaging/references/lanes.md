# Launch Packaging Lanes

The two lane playbooks. A run executes one. Evidence boundaries and the Suede S mark rules in SKILL.md apply to both.

## Lane A: Package the launch

Use this lane when Suede work is ready to leave the local machine and needs a clean public package.

### Package steps

1. Run the Step 0 inventory: name every launch surface in play.
2. Confirm the source truth: current branch, remote, commit, live build status, and exact public URLs.
3. Write the public explanation around the outcome, not the implementation.
4. Add proof links: source files, docs pages, scripts, MCP tools, screenshots, build output, live route, or raw GitHub URL.
5. Check install commands from a temporary destination, not only the local repo. (This is the handoff into Lane B: see Install support.)
6. Run copy, SEO, link, and evidence-boundary checks before publishing.
7. Write a short handoff when another agent or computer may need the result.
8. End meaningful launches with a simple non-coder explanation (the simple explanation below), the usual breakdown, and `Cue Suede` so the operator can request a change, preserve what worked, or say nothing to keep it as-is.

### Lane A output

```text
Launch surface:
Reader:
Primary action:
Public copy:
Install or access path:
Proof links:
Simple explanation:
Usual breakdown:
Verification:
Caveats:
Status: ship | ship-with-caveats | hold
Cue Suede:
```

Never claim a public launch is live until the live URL or public artifact was checked.

---

## Lane B: Install support

Use this lane to make Suede install instructions accurate, public, and easy to explain, and to fix them when they fail. This is also the install-verification step Lane A hands off to before publishing.

### Rules

- Lead with public GitHub skill installs.
- Treat `@personal` as a local operator note only: keep it out of public docs, READMEs, MCP catalog output, and public explainer copy.
- Explain that GitHub skill installs need a repo and path because one repo can contain many skills.
- Test installer commands from a temporary destination after pushing.
- For multiple paths, use one `--path` flag followed by all skill paths.
- Restart Codex after installing new skills.

### Workflow

1. Identify the target installer: Codex GitHub skill installer, Claude skill folder copy, local plugin alias, or MCP server.
2. Check whether the target skill folder exists publicly at `main`.
3. Run the exact install command from a temporary directory.
4. Diagnose failures with the table below. Name the failure cause exactly: "it didn't work" is not a diagnosis.
5. Fix docs, MCP catalog output, README commands, and public explainer copy together.
6. Keep local plugin commands available only under local operator setup.

### Install failure table

| Symptom | Likely cause | Fix |
|---|---|---|
| Install command 404s | Skill folder not pushed to `main`, or path is wrong | Push, re-derive the path from the repo root, re-run from a clean temp dir |
| Installer reports skill not found | Missing `--path`, or the repo hosts many skills | Add the repo-relative skill path after `--path` |
| Multiple skills requested, only one installs | Repeated `--path` flags instead of one | Use one `--path` flag followed by all skill paths |
| Raw-URL command returns HTML, not the file | GitHub blob URL used instead of the raw URL | Swap to the `raw.githubusercontent.com` form and re-fetch |
| Install succeeds but the skill never triggers | Frontmatter `name` mismatch or vague description | Fix SKILL.md frontmatter, push, reinstall, restart |
| Works locally, fails for a public user | Command references `@personal` or a local plugin alias | Replace with the public GitHub repo-and-path route |
| New skill invisible after install (Codex) | Session has not reloaded skills | Restart Codex, then confirm the skill lists |
| Catalog lists a skill the install cannot find | MCP catalog drifted from the repo | Diff the server's live `tools/list` against the catalog; fix catalog and docs together |

### Lane B output

```text
Public install:
Advanced installs:
Local-only notes:
What was tested:
Failure cause:
Corrected copy:
```

---
