---
name: from-zcode
description: Continue, in this conversation, a task that was being worked on in ZCode. The first time it imports and links the ZCode session; after that it only brings over new progress. Use when the user says $from-zcode, "continue from zcode", "import the … session from zcode", "sync with zcode", "what did zcode get done", 接着 zcode 继续, 从 zcode 把…导入, or shares a screenshot of an ZCode session and asks to continue it.
---

# Continue from ZCode

This skill uses the `ccx` command from the ccx app (github.com/aaronwong1999/ccx). If `~/.local/bin/ccx` doesn't exist, tell the user to install ccx with `curl -fsSL https://raw.githubusercontent.com/aaronwong1999/ccx/main/install.sh | sh` and stop. Run every `ccx` command below with `--app zcode -C "<current working directory>"`; it reads local session files, so if the sandbox blocks it, ask to run it outside the sandbox.

1. **The user named the session** (a title, some words from it, or a screenshot): run `~/.local/bin/ccx call codex continue_here --query "<name>"`. Every project is searched.
   - Pick the candidate whose title matches best and run `~/.local/bin/ccx call codex continue_here --session-id <id>`.
   - If several look equally likely, list up to 5 (number, title, updated, folder if different) and let the user choose.
2. **The user did not name one** ("continue from zcode", "sync"): run `~/.local/bin/ccx call codex continue_here`.
   - Already linked: you get ZCode's new progress.
   - Not linked yet: you get candidates; choose as in step 1.
3. With the `<ccx-sync>` block in hand, tell the user in one sentence what came over, then **carry on with their task right here**. Treat the block as work you did yourself; the files on disk are the source of truth.
   - If it shows a **task list**, continue from its first unfinished item.
   - If it says the other side **stopped in the middle of a step**, first check whether that step finished, then continue.
4. **Different folder**: if the block has a "NOTE: … folder" line, tell the user and ask whether to continue in that folder or use the progress only as reference. Never edit the other folder on your own.
5. To get ZCode's newer progress later, run step 2 again. (With the full ccx install, new progress also arrives on its own with each message.)

If the user says "unlink", "stop syncing", 取消关联 or 不要同步了, run `~/.local/bin/ccx call codex unlink --app zcode -C "<current working directory>"`. It forgets the link to the ZCode conversation, so neither side gets the other's progress any more; both conversations are kept, and handing over again links them afresh.
