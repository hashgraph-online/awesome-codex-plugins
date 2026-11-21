# 01 — AI assistant with a rich streamed answer and Stop

Registry rows: `10.3-G01`, `10.3-G02` (`recipes/registry.json`). Verified 2026-11-12, Bot API 10.4.

1. **Request and visible result.** “The bot thinks for 20 s and you can't stop it. Make it stream like ChatGPT and let me stop it.” — A private-chat draft that fills in under real stage labels (Searching → Writing), a Stop button on the draft, and one final message: the full answer, or — after Stop — the partial answer marked “stopped, incomplete” with Continue / Try again.
2. **Why the new feature.** 10.3 `can_stop` puts a native Stop on the draft and `stopped_message_generation` tells the bot; before, users had to wait or the bot needed its own Cancel button and a separate message. `keep_on_stop` keeps the partial preview visible until the bot persists it.
3. **Requirements.** Bot API ≥ 10.3 (drafts 9.3+, rich drafts 10.1+). Production. Private chats (with or without topics). `allowed_updates` must include `stopped_message_generation`. SDK must route it (aiogram 3.31 / grammY 1.46: yes).
4. **Payload.** Full request sequence: `examples/payloads/r01-ai-stop-keep-marked.json` (generated from the code); incoming fixture: `examples/fixtures/stopped_message_generation.json`. Key part:
   ```json
   {"chat_id": 111111111, "draft_id": 48127, "can_stop": true, "keep_on_stop": true,
    "rich_message": {"blocks": [{"type": "thinking", "text": "Searching the sources…"},
                                {"type": "paragraph", "text": "Telegram added a Stop button…"}]}}
   ```
5. **Code.** `examples/python/tgkit/generation.py` (state machine, `execute`, `OperationRegistry`), `examples/python/recipes/r01_ai_assistant.py`, TS: `examples/ts/tgkit.ts` (`Generation`) + `examples/ts/recipes.ts::aiAssistant`.
6. **Sequence and state.** start → draft(thinking: Starting) → stage/chunks (coalesced ≥ 1 s) → **Stop update** (chat, thread, draft_id) → cancel upstream → finalize once per policy → late chunks / 2nd Stop / completion = no-ops. State: GENERATING → STOP_REQUESTED → STOPPED.
7. **Result.** Mock-up (not a client screenshot): `[Telegram added a Stop button… keep_on_stop keeps the partial draft…] — Stopped by you — the answer is incomplete. [Continue] [Try again]`
8. **Typical mistake, limits, alternative.** Treating Stop as an error or as success (sending the full answer anyway), relying on `keep_on_stop` to persist the text, letting a sentence end bypass throttling, putting model reasoning into the thinking block. Alternative without drafts (groups, old SDK): status message + throttled `editMessageText` with a Cancel callback.
9. **Run and verify.** py -3 examples/python/recipes/r01_ai_assistant.py · node examples/ts/recipes.ts · tests: tests/test_generation.py (incl. 300 randomized event orders). Evidence: offline contract; not run against Telegram.
10. **Adapt.** Copy `Generation` + `execute` as is; adapt `stage_labels`/texts to your i18n, `stop_policy` per product, `cancel_upstream` to your LLM client. Wire the Stop update into your router and `allowed_updates`. Related: 08 (topics), `streaming-and-editing.md`.
