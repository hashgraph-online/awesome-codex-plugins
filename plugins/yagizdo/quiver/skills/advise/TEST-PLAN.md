# Test Plan -- /advise

**Trigger:** `/advise <question>` (and `/quiver:advise` should also work since `name: advise` enables prefix-free invocation).

**Setup:** Project root. No prerequisites; works in git and non-git directories.

**Expected behavior:**
- Gathers git context via three shell blocks; falls back to "NO_GIT" without aborting.
- Restates question in one sentence; defaults to Quick depth silently.
- Runs code navigation tier only when files/symbols are mentioned.
- Calls context7 only when a library/framework/SDK/CLI is named.
- Calls WebSearch only when user opts in.
- Emits Observation / Risks & Trade-offs / Recommendations / Open Questions inline response in English (default) or the user's language when they write in it.
- Stays armed across turns; exits cleanly on user signal.
- Writes NO files.

**Verification checklist:**
- [ ] Slash menu shows `/advise`.
- [ ] `/advise review this snippet: <paste>` produces an Observation / Risks & Trade-offs / Recommendations / Open Questions response grounded in the pasted code.
- [ ] `/advise React useEffect cleanup` triggers context7 lookup for React.
- [ ] `/advise what do you think?` (no library, no code) responds from general knowledge without unnecessary tool calls.
- [ ] After 2 follow-up questions in a row, both responses stay in shape; on third "ok" the skill exits silently.
- [ ] `ls docs/brainstorms/ .claude/plans/ .claude/handovers/` shows no new files with today's timestamp after a session.
- [ ] WebSearch only appears in tool traces when user said "search" or equivalent.

**Known gotchas:**
- Context7 must be authenticated; if `resolve-library-id` fails, fall back to general knowledge and note "docs not fetched" in Observation.
- The skill's chat-loop nature means it does NOT honor `/clear` mid-session -- a follow-up still triggers Step 2-5 logic.
- Multi-turn arming can produce long sessions; if context grows tight, suggest `/handover` rather than auto-saving.