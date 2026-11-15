# 27 — Assistant as a product: modes, streamed answer with Stop, feedback, regenerate, history, files

Product recipe (combines mechanisms; no registry row of its own). Builds the product screens around
`recipes/01-ai-assistant.md` (the generation state machine). Uses 10.3 drafts with Stop,
`InlineKeyboardMarkup.force_reply`, `disabled` buttons and 9.4 button `style`. Verified 2026-11-15
against Bot API 10.4 (newest release on that date, 2026-11-09). Index of all product recipes:
`references/use-case-playbooks.md`. Tags: **[API]** = API requirement, **[official]** = official
recommendation, **[heuristic]** = design heuristic of this skill.

1. **Request and visible result.** “Make an assistant bot with three modes, a live answer I can
   stop, thumbs up or down on the result, a way to regenerate, a short history, and the ability to
   send a PDF.” — A modes screen (the current mode is a disabled “✓” button), a draft that shows
   real stages and a Stop button, a final rich answer with a footer, 👍 👎 and *Regenerate*, a
   history of the last five conversations, an acknowledgement for an accepted file and a clear
   refusal for a file that is too large or of an unsupported type.
2. **Why these features.**
   - `sendRichMessageDraft` with `can_stop` and `keep_on_stop`; the user's Stop arrives as
     `stopped_message_generation {chat, message_thread_id?, draft_id}` **[API, 10.3]**. The
     `thinking` block carries only real stage labels (“Reading your question…”, “Writing the
     answer…”), never model reasoning, and exists only in drafts **[API: thinking blocks only in
     drafts; labels: heuristic]**. Labels and the stop texts come from the user's language.
   - One running answer per chat: `OperationRegistry.add` refuses a second one, so a new question
     during a stream gets “wait for it, or press Stop under the draft” instead of two parallel
     streams **[heuristic]**.
   - Final answer = new `sendRichMessage` with a `footer` block (what mode, “answers can be
     inaccurate”) and `reply_markup`; a draft is a temporary 30-second preview and has no `reply_markup` parameter, so
     the buttons belong to the final message **[API]**.
   - Thumbs-down asks why with `force_reply: true` on an inline keyboard (10.3): reason buttons
     *and* the reply field open together **[API, 10.3]**; the flag is fixed for the keyboard's
     lifetime, so the prompt is never edited **[API: can't change on edit]**.
   - A vote becomes a `disabled` button (“👍 ✓”) and a retired answer shows one disabled
     “Replaced by a newer answer” **[heuristic; `disabled` is 10.3 API]**. Disabled does not stop
     crafted callbacks: the server keeps the vote and “retired” flags **[API: the check is yours]**.
   - Modes: the current one is `disabled` with a ✓ prefix (a state, not an action); the others are
     buttons **[heuristic]**. `style: "primary"` is left for the single Add/Send-type action and
     is not used here because nothing on the modes screen is a main action **[heuristic]**.
   - History uses `paginate` and `pager_row`: arrows are *disabled*, not removed, so the row keeps
     its shape **[heuristic]**.
3. **Requirements.** Bot API ≥ 10.3 (drafts with Stop, `force_reply`, `disabled`). `allowed_updates`
   must include `stopped_message_generation`: SDKs that compute the list from handlers may drop it
   (see `references/specialized-updates.md`). Production, private chat. File limits: bots can
   download files up to 20 MB through `getFile` **[API]**; the recipe's own limit is 10 MB and three
   types (PDF, plain text, Markdown) **[heuristic]**. A product that charges per answer should say
   so in the footer and handle `/paysupport` (`recipes/20-shop.md`).
4. **Payload.** Full request sequence: `examples/payloads/r27-ai-assistant-product.json`. Incoming
   fixtures: `examples/fixtures/stopped_message_generation.json` (existing, draft 48127),
   `examples/fixtures/usecase_ai_document_pdf.json` (2 MB PDF),
   `examples/fixtures/usecase_ai_document_zip.json` (unsupported type); the too-large case is the
   PDF fixture with `file_size` set to 30 MB in code.

   | Screen | Message | Buttons (row by row) | Leaves to |
   |---|---|---|---|
   | modes | “Assistant … Mode: Chat” | `✓ Chat` (disabled) `Translate` `Summarize` · `History` | modes, history |
   | draft | `thinking` stage label + text so far (drafts) | Stop (client-drawn, `can_stop`) | final / stopped |
   | final answer | rich: paragraphs, footer | `👍` `👎` · `↻ Regenerate` | feedback, regenerate |
   | stopped answer | kept partial text + “Stopped by you…” footer | `↻ Regenerate` | regenerate |
   | feedback prompt | “What was wrong…?” (`force_reply`) | `Incorrect` `Too long` `Off topic` | reason saved |
   | history | last 5, 2 per page | `← 1/3 →` (arrows disabled at the ends) · `← Back` | modes |
   | file ack / refusal | one message, replies to the file | — | question |

   Key parts:
   ```json
   {"method": "sendRichMessageDraft", "params": {"chat_id": 111111111, "draft_id": 48120, "can_stop": true, "keep_on_stop": true, "rich_message": {"blocks": [{"type": "thinking", "text": "Reading your question…"}]}}}
   {"method": "sendMessage", "params": {"chat_id": 111111111, "text": "What was wrong with the answer? Tap a reason or reply with your own words.", "parse_mode": "HTML", "reply_markup": {"inline_keyboard": [[{"text": "Incorrect", "callback_data": "ai:3:rs:0"}, {"text": "Too long", "callback_data": "ai:3:rs:1"}, {"text": "Off topic", "callback_data": "ai:3:rs:2"}]], "force_reply": true}}}
   {"method": "editMessageReplyMarkup", "params": {"chat_id": 111111111, "message_id": 1005, "reply_markup": {"inline_keyboard": [[{"text": "Replaced by a newer answer", "disabled": {}}]]}}}
   ```
5. **Code.** `examples/python/recipes/r27_ai_assistant_product.py` (`Assistant.begin`, `advance`, `pump`,
   `decorate`, `on_answer_button`, `regenerate`, `on_document`) on top of
   `examples/python/tgkit/generation.py` (`Generation`, `GenerationConfig`, `OperationRegistry`,
   `execute`) and `examples/python/tgkit/flows.py` (`ScreenFlow`, `paginate`, `pager_row`,
   `UpdateDedup`). `decorate` adds the footer and buttons to the *final* effect only; stopped,
   failed and timed-out endings keep a single *Regenerate*. Copy: en, ru. No TypeScript twin.
6. **Sequence and state.**
   ```mermaid
   stateDiagram-v2
     [*] --> modes: /start
     modes --> draft: question (registry.add)
     draft --> draft: second question → "wait or Stop"
     draft --> final: model done (one finalization)
     draft --> stopped: stopped_message_generation (keep_marked)
     final --> voted: 👍 / 👎 (once)
     voted --> reason: 👎 asks why (force_reply)
     final --> draft: Regenerate (new draft_id, old buttons retired)
     stopped --> draft: Regenerate
   ```
   Answer record: `{id, user, chat, message_id, mode, question, status, retired, feedback, reason,
   prompt_id}`. `callback_data` is `ai:<answer id>:<up|dn|re|rs:<n>>`; flow screens use
   `as:<ver>:<action>`. Draft ids come from the bot and must be non-zero; each Regenerate takes a
   new one, because the old draft's Stop must never address the new run. A finished answer never
   changes: Stop after completion and late chunks after Stop are no-ops in the state machine.
7. **Result.** Mock-ups (not client screenshots), English / Russian:
   ```
   Short answer first. can_stop adds a       Сначала коротко. can_stop добавляет
   Stop button under the draft.              кнопку «Стоп» под черновиком.
   keep_on_stop keeps the partial text…      keep_on_stop оставляет частичный текст…
   Chat · Answers can be inaccurate.         Чат · Ответ может быть неточным.
   Check important facts.                    Проверяйте важные факты.
   [ 👍 ] [ 👎 ]                             [ 👍 ] [ 👎 ]
   [ ↻ Regenerate ]                          [ ↻ Заново ]
   ```
8. **Typical mistake, limits, alternative.** Mistakes: letting the user start a second stream in the
   same chat; one draft id for every run (Stop hits the wrong run); counting a vote twice because
   the client showed the old keyboard; leaving the old answer's buttons live after Regenerate;
   feeding model reasoning into the `thinking` block; accepting any file and finding out later it
   is too big; HTML-escaping model output (rich text strings are plain text, so the model's output
   can never become markup). Limits **[API]**: `callback_data` ≤ 64 bytes; rich message ≤ 32768
   characters; `getFile` downloads ≤ 20 MB. Failure paths in the run: second question while
   generating → “I'm still writing…”; Stop (fixture) → one final with a footer and the model call
   cancelled; Regenerate from a stopped answer → new draft; second Regenerate on the retired one →
   “screen has changed”; another user's tap → “belongs to someone else”; second vote →
   “You already rated this answer.”; 30 MB PDF and a zip → refusal in the sender's language.
   Alternative: a plain `sendMessageDraft` stream when you do not need rich blocks.
9. **Run and verify.** `py -3 examples/python/recipes/r27_ai_assistant_product.py` (12 self-checks) ·
   `cd tests && py -3 -m unittest test_usecases` (drafts are validated with the draft rules, every
   other rich message and keyboard with the normal ones; copy in en/ru; payload drift) ·
   `py -3 scripts/validate_rich.py payload.json --draft` on an extracted draft. Evidence: offline
   contract with a scripted model stream; no real model, no real files.
10. **Adapt.** Keep: one stream per chat, a fresh draft id per run, the footer and buttons added only
    to the final effect, vote/reason stored on the answer record, refusals before spending tokens.
    Replace: `ANSWER` and the scripted stream with your model client (stage events from real work:
    retrieval, reading, writing), the mode list and prompts, `SEED_HISTORY` with a database read,
    the allowed types and size limit. Add per-mode system prompts, a usage counter in the footer,
    document text extraction after the acknowledgement. Related: `recipes/01-ai-assistant.md`,
    `recipes/20-shop.md` (charging), `references/streaming-and-editing.md`,
    `references/dynamic-feedback-and-streaming.md`, `references/inline-keyboards.md`.
