# PlaceCall: The MCP tools

Part of the PlaceCall skill ([`SKILL.md`](../SKILL.md)). Read it for the MCP path: what the tools cannot do, how to retry a failed `place_call` without a second call, and how to follow a call.

What the MCP tools cannot do. These need the key path:

- Recording and the opening notice. `place_call` takes `target_phone`,
  `brief` and `language`, and three optional arguments: `escalation` (how the
  agent may reach the account holder mid-call, the same object as on
  `POST /calls`), `on_behalf_of` (the client's name; in English and Spanish
  the notice says "calling for <name>" instead of "calling for a client")
  and `items` (the things the call must find out or get done; see
  [Items](items.md)). Every call it places is recorded and opens with the
  default notice, naming the client when `on_behalf_of` is set. If the user
  asks for no recording, a different notice or no notice
  (`record_call`, `disclosure`), do not use `place_call`, and do not try to
  get it through the brief. Tell the user this needs an API key and use
  `POST /calls` once they have one; with no key yet,
  [sign them up by email code](sign-up.md).
- Canceling. There is no cancel tool; a call placed with `place_call` runs to
  its end. If the user may need to stop the call, say so before dialing and
  offer the key path, where `POST /calls/{id}/cancel` works (with no key yet,
  an [email-code sign-up](sign-up.md) first).
- Recovering from a failed `place_call`. A `place_call` that times out, loses
  its connection, or returns `internal_error` or `upstream_unavailable` may
  have placed the call anyway. Repeat it once, unchanged, within two minutes
  of the first attempt; do not reword the brief or change the number or
  language. An identical repeat inside that window is not dialed again: it
  comes back as `duplicate_call`, with the first call's `call_id` when the
  server has it. Follow that call. A `duplicate_call` with no `call_id` means
  the id cannot be read yet: wait a few seconds and repeat once more,
  unchanged. If that also returns no `call_id`, stop and tell the user the
  call may have gone through and that you cannot check it from here. Never
  repeat it after two minutes, even if the server's message suggests it, and
  never place it with `POST /calls` instead: either one can be a second real
  call. (The REST recovery steps do not apply: `GET /calls` lists only the
  key's account, which may not be the account the MCP call went to.)

Following a call with the MCP tools:

- Call `get_call_result` about every 5 s while `in_progress` is true. The call
  agent waits only about 60 s for an answer to a question, so a slower check
  can make the user's answer arrive too late.
- A question the call is waiting on appears in `pending_questions`, with its
  `request_id` and `expires_at`. Ask the user straight away and pass their own
  words to `answer_question` with that `request_id`. Never make up the answer.
  `delivered: false` means the question was no longer waiting (expired, call
  ended, or already answered by an earlier attempt). Do not ask the user
  again; tell them the answer may not have reached the call.
  `pending_questions_unavailable: true` means the list could not be read, not
  that nothing is waiting: check again.
- When the call finishes, report `result`, `ended_by`, `line_kind`,
  `result_reason` and `summary`, say what each record in `items` came to,
  and read the transcript. `items` is `null` until the call is graded; with
  `items_unavailable: true` beside it, the records could not be read this
  time, so ask again. A long transcript is
  shortened (`transcript_truncated`). `transcript_status` reads `live` while
  the post-call check of the recording can still change a turn. It reads
  `final` once that check has run or is no longer expected, usually a minute
  or two after the call ends.
- If a tool says the server needs authentication, tell the user to sign in
  (Claude Code: `/mcp`, pick `placecall`; Codex: `codex mcp login placecall`).
  If they can't finish it, get a key by [email code](sign-up.md).
  The Gemini CLI extension sends the stored API key instead of signing in, so
  an authentication error there means that key is missing or wrong
  (`gemini extensions config placecall`).
