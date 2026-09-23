# Test Plan -- /create-agents-md

**Trigger:** `/create-agents-md` (and `/quiver:create-agents-md` should also work)

**Setup:**
- A project directory containing recognizable source / manifest files (e.g., `package.json`, `Cargo.toml`, `pubspec.yaml`).

**Expected behavior:**
1. Skill silently gathers project structure (Glob), reads existing `AGENTS.md`, `README.md`, `CLAUDE.md`, and detects CI / linter configs.
2. Skill chooses Branch A (no project), Branch B (existing AGENTS.md → rewrite mode), or Branch C (create from scratch) without showing the label to the user.
3. Skill writes a final `AGENTS.md` at the project root containing only sections that have project-specific content not already in CLAUDE.md or README.md.
4. Skill enforces imperative language, omits empty sections, and stays under 80 lines (warns if not).
5. Final output reports `created`/`rewritten`, section count, line count, and a `pass`/`warnings` signal check.

**Verification checklist:**
- [ ] Slash menu shows `/create-agents-md`.
- [ ] On a directory with no source files, skill exits with the "doesn't appear to be a project" message and writes nothing.
- [ ] Generated `AGENTS.md` contains no bullet copy-pasted verbatim from `CLAUDE.md` or `README.md`.
- [ ] All bullets use imperative language (no "consider", "might", "you may want").
- [ ] Existing `AGENTS.md` content is overwritten, not appended.
- [ ] File is read back after writing to confirm contents.

**Known gotchas:**
- The Glob max-depth-2 scan can miss deeper-nested projects (e.g., monorepos with nested manifests); deeper exploration is the user's responsibility for now.
- The 80-line "warning" threshold is advisory -- the skill must still write the file even if length triggers the warning.
