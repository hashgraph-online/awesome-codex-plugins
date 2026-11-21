---
name: runheed-fix-production-errors
description: Find, fix and close the production errors Runheed recorded for this app. Use when the user asks "what broke in production", "fix the top error", "check errors after the deploy", "is anything failing", pastes a Runheed error link or ID, or wants errors resolved with the commit that fixed them. Needs the Runheed MCP server connected (runheed_* tools).
---

# Fix production errors with Runheed

Runheed groups each production error (same type, message and code location) into one error with a count, the stack trace, the breadcrumbs before it and the request it failed on. These steps turn that into a fix and a closed error.

If no runheed_* tools are available, the MCP server isn't connected. In Claude Code: `claude mcp add --transport http runheed https://runheed.com/api/mcp`, then `/mcp` > runheed > Authenticate. To try the tools on sample errors first: `claude mcp add --transport http runheed-demo https://runheed.com/api/mcp/demo`.

## 1. Decide what to fix first
1. Call `runheed_get_project_health` (pass `projectId` if the user named a project). It ranks what to fix first and says which errors came back after being resolved.
2. For "what changed since the deploy", call `runheed_get_trends` with `period: "24h"`.
3. To find a specific error, call `runheed_search_errors` with `status: "unresolved"` and a `query` (a route, a file name or part of the message). `runheed_get_recent` lists the newest.

Pick one error. Prefer, in order: errors that came back, then the highest count in the last 24 hours, then errors on checkout, sign-in or other paths that lose users.

## 2. Read it fully before touching code
1. `runheed_get_error` with the `errorId`: type, message, count, first and last seen, environment, release, the stack trace and any note from an earlier fix.
2. `runheed_get_error_context` with the same ID: the breadcrumbs (what happened just before), the request (method, route, safe headers) and extra data.
3. Open the first stack frame that is in the user's code, not in node_modules or site-packages. Read the function and its callers.
4. State the cause in one sentence before editing. If the breadcrumbs or request don't support it, keep reading.

## 3. Fix
1. Fix the cause, not the symptom: no try/catch that swallows the error, no optional chaining that hides missing data the code needs.
2. Add a test that reproduces the failing input from the context (the request body, the parameters, the state in the breadcrumbs).
3. Run the tests. Commit with a message that names the error.

## 4. Close the loop
1. After the fix is committed (and deployed, if the user deploys separately), call `runheed_resolve_error` with the `errorId` and a `comment` like `Fixed in <short commit hash>: <what changed>`.
2. If it happens again, Runheed reopens it and `runheed_get_error` shows your note. Read it and work out what the fix missed.
3. Expected noise the user agrees to ignore (a bot probing a route, a known third-party outage): `runheed_ignore_error` with a `reason`. `runheed_unignore_error` undoes it.

## Rules
- One error per fix and per commit, so the resolve note points at the right change.
- Never resolve an error you didn't fix. Ask the user if unsure.
- Don't paste secrets from the request or extra data into code, commits or chat. Runheed redacts common secret fields, but check.
- Report back: which error, the cause in one sentence, the commit, and that it's resolved.
