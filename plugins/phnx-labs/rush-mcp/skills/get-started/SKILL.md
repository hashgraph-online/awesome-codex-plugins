---
name: get-started
description: First run with Rush. Use right after the plugin is installed, or when someone asks what Rush is, how to start, or how to hand it their first task.
---

# Get started with Rush

Take the person from install to one finished task in three short turns. Never
ask for a password, token or API key in chat, and never invent a result.

1. **Check the connection and ask.** Call `list_repositories`. If the client
   asks the person to sign in, tell them to finish signing in to Rush (in
   Claude Code: `/mcp`, then Rush) and stop until they have. Then say in one
   sentence what Rush is: an agent that does a task in its own cloud computer
   and hands back the result with a record of what it did. Ask one question:
   "What would you like done? It can be on one of your repositories, or need
   none." If the list is empty, add that a task on code needs the Rush GitHub
   App on that repository
   (https://cloud.getrush.ai/console/settings/?section=connections), or, for a
   gitlab.com project, a GitLab sign-in (`connect_account` with `type` `app`
   and `name` `gitlab`).
2. **Start it.** Confirm the repository against the list when the task names
   one. Then follow the `hand-off-a-task` skill: write the task with everything
   the agent needs, start it, say it takes a few minutes, and wait until it
   settles.
3. **Report and close.** Give the answer, the pull request link if there is
   one, and any files it made. Then say how to continue: ask for the next task
   in plain words, reply to this one to keep going in the same computer for 7
   days, and see every run at https://cloud.getrush.ai.

Runs use the Claude or ChatGPT account the person connected to Rush; without
one, Rush's models cover a first try. If the start is refused, use the table in
`hand-off-a-task` under "When Rush refuses".
