# Test Plan -- /brainstorm

**Trigger:** `/brainstorm <idea>` (and `/quiver:brainstorm` should also work)

**Setup:** Project root with optional `docs/brainstorms/` directory.

**Expected behavior:**
1. Silently gathers project context and runs three git shell blocks.
2. Restates the idea, picks depth silently, asks 0-4 clarifying questions via `AskUserQuestion`.
3. Presents 2-3 approaches with a recommendation; user selects via `AskUserQuestion`.
4. Prints Executive Summary; user approves/adjusts/restarts via `AskUserQuestion`.
5. Writes spec to `docs/brainstorms/YYYY-MM-DD-<name>.md` (English), reads it back, self-reviews.
6. Final `AskUserQuestion` offering `Looks good / Let me review first / Save and stop`; first option invokes `plan` with the spec path.

**Verification checklist:**
- [ ] Slash menu shows `/brainstorm`; spec file written under `docs/brainstorms/` with date-prefixed filename.
- [ ] All clarifying / approach / approval / next-step prompts use `AskUserQuestion`, not plain text; spec has no raw `{placeholder}` text.
- [ ] Visual companion offer appears only for visual topics; spec language is English unless user explicitly requested otherwise.

**Known gotchas:**
- Visual companion falls back to text-only if its server cannot start -- the brainstorm must not abort.
- Decomposition check fires at 3+ subsystems or 20+ estimated files; these thresholds control when the split prompt appears.
