# Pause safely

Stop current work so a fresh agent with none of this session's memory can resume it. [Session pickup](session-pickup.md) is the other half.

Run this only on an explicit pause: the user asks you to stop for now, leaves without asking you to continue, the host is about to restart, or context compaction is imminent. "Keep working", "carry on while I sleep", and "don't stop" grant continuation, so this playbook does not apply to them.

1. **Reach a clean stopping point.** Finish or undo the indivisible step underway. Start nothing new. Cancel nested helpers still running.
2. **Do nothing irreversible.** Do not push or open a PR, unless a PR was already open.
3. **Commit everything uncommitted** as one `WIP:` commit on the checked-out branch. If the code fails to build or test, add a body line saying so. Check the staged diff for secrets and credential files first; unstage and list any you find.
4. **Write a resume note** to a file: the task's intent, what you were in the middle of, what is done and confirmed, current state, the next step, key files, and traps. On the compaction trigger, use a temp file named after the task. Link an existing `show-me-your-work` trail ([../../show-me-your-work/SKILL.md](../../show-me-your-work/SKILL.md)) instead of copying it.

Done means nothing is uncommitted, nothing irreversible happened, and the note alone lets a cold-start agent resume.

**Reply** in a way that reads as a pause and not as finished work. Say which step of the loop you stopped at, which work is saved to disk and which exists only in this session's context (give paths, never diffs), the commits you created and whether any uncommitted changes remain, the path to the note, and what the resuming agent should do first.
