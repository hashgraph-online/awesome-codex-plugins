# Test Plan -- /load-handover

**Trigger:** `/load-handover` (and `/quiver:load-handover` should also work)

**Setup:**
- `.claude/handovers/` exists in the project root with at least one `<timestamp>.md` file written by `/handover`.

**Expected behavior:**
1. Skill globs `.claude/handovers/*.md`, sorts descending, picks the newest filename.
2. With no files (or directory missing), skill prints `No handover files found for this project.` and exits.
3. With at least one file, skill reads the most recent and prints the output template (`Session loaded`, `Date`, `Top Priority`).
4. Skill lists every Next Steps item with a one-line explanation and asks the user which one to work on.
5. With a malformed file (no headings), skill warns once and continues with the available content.

**Verification checklist:**
- [ ] Slash menu shows `/load-handover`.
- [ ] Output uses the exact template wording for `Session loaded`, `Date`, `Top Priority`.
- [ ] When more than one handover exists, the skill appends `{count} older handover(s) also available.`
- [ ] No raw `{placeholder}` text remains in the printed summary.
- [ ] Older handovers are not read unless the user explicitly asks.

**Known gotchas:**
- Lexicographic sort relies on the `YYYY-MM-DD_HH-MM-SS.md` filename convention; manually-renamed handovers can break ordering.
- "Top Priority" comes from the first `Next Steps` bullet; if the section is missing, the skill must fall back gracefully rather than emit a placeholder.
