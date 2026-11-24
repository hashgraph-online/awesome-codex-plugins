---
name: to-zcode
description: Hand this conversation to ZCode so the user can keep going there. The first time it is imported and linked; after that the linked ZCode conversation is opened. Use when the user says $to-zcode, "switch to zcode", "continue in zcode", 切到 zcode, 转给 zcode, or is running out of Codex usage. Also when the user says "unlink", "stop syncing" or 取消关联.
---

# Continue in ZCode

This skill uses the `ccx` command from the ccx app (github.com/aaronwong1999/ccx). If `~/.local/bin/ccx` doesn't exist, tell the user to install ccx with `curl -fsSL https://raw.githubusercontent.com/aaronwong1999/ccx/main/install.sh | sh` and stop.

1. If a change is half-written, finish or stop it cleanly first. Don't leave broken files.
2. If you have a task list, make sure it's up to date: it travels with the conversation.
3. Run `~/.local/bin/ccx call codex send_current_session --app zcode -C "<current working directory>"`. It reads ZCode's and Codex's local session data and opens the ZCode app, so if the sandbox blocks it, ask to run it outside the sandbox.
4. Reply with one sentence about the result. Then stop editing, so the two apps don't change files at the same time. When the user sends a message on the ZCode side, this side's progress goes with it.

If the user says "unlink", "stop syncing", 取消关联 or 不要同步了, run `~/.local/bin/ccx call codex unlink --app zcode -C "<current working directory>"`. It forgets the link to the ZCode conversation, so neither side gets the other's progress any more; both conversations are kept, and handing over again links them afresh.

ZCode opens at the app level: tell the user which project and conversation ccx reports, so they can select it in the task list.
