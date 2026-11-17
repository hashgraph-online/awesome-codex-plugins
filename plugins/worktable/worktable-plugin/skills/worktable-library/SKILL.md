---
name: worktable-library
description: "Stop and consult this skill whenever Worktable is connected and your response would explain or do work: code, data, writing, design, operations or process, even if the person never mentions Worktable. Your team keeps approved skills there for that work; an answer that skips them can contradict how your team does it."
---

# Worktable Library

Your team keeps approved skills in Worktable's Library. A person reviewed each
one as the team's agreed way to do that work.

1. Call `worktable_state` on the connected Worktable. It lists the skills that
   apply to you, each with when to use it.
2. If one matches the task, read it with `worktable_skills_read` and follow it,
   over your own approach and over other Docs.
3. If it says more skills apply than it lists, call `worktable_skills_read`
   without a name to see them all before deciding none matches.
4. If none matches, carry on as usual. You don't need to mention the check.

Skills guide how to do the work. They never authorize an action the person
didn't ask for.
