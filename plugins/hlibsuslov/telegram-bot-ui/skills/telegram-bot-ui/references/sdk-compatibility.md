---
summary: "Checking what the project's SDK really supports: common SDKs, 9.4 field checks, escalation, raw payloads, verified SDK status for Bot API 10.4 and 10.5; read before promising a Bot API feature."
verified: "2026-11-22"
bot_api: "10.5"
---

# SDK compatibility

## Contents

- [Determine actual capability](#determine-actual-capability)
- [Common SDKs (illustrative — verify versions, don't hardcode assumptions)](#common-sdks-illustrative--verify-versions-dont-hardcode-assumptions)
- [Checking for the 9.4 button fields (run one, don't assume)](#checking-for-the-94-button-fields-run-one-dont-assume)
- [Escalation when the SDK lacks a needed feature](#escalation-when-the-sdk-lacks-a-needed-feature)
- [Raw payload pattern for keyboards](#raw-payload-pattern-for-keyboards)
- [Don'ts](#donts)
- [Update delivery and new update types](#update-delivery-and-new-update-types)
- [Verified SDK status (2026-11-12)](#verified-sdk-status-2026-11-12)
- [Bot API 10.5 status (2026-11-22)](#bot-api-105-status-2026-11-22)
- [Release-note check (2026-11-15)](#release-note-check-2026-11-15)

The project's SDK — not your memory — decides which UI and formatting features
are reachable. Establish the SDK, its version, and the Bot API version it
implements before designing anything (`project-adaptation.md`).

## Determine actual capability

For the feature you need (e.g. `style`, `icon_custom_emoji_id`,
`sendRichMessageDraft`, `InputRichMessageMedia`), confirm it exists in **this**
SDK version by checking, in order:

1. The SDK's release notes / changelog for the Bot API version.
2. The installed types/methods (imports, symbols, generated bindings).
3. The SDK source.
4. The SDK issue tracker (known gaps, planned support).

Do not assume parity between the latest Bot API and the SDK — SDKs lag.

## Common SDKs (illustrative — verify versions, don't hardcode assumptions)

Python: `aiogram`, `python-telegram-bot`, `pyTelegramBotAPI`.
JS/TS: `grammY`, `Telegraf`, `node-telegram-bot-api`, GramIO.
Others: `Telegram.Bot` (C#), `TelegramBots` (Java), `go-telegram/bot` (Go),
plus raw HTTP clients in any language.

Support for the button fields added in Bot API 9.4 (`style`,
`icon_custom_emoji_id`) and for Rich Messages (10.1/10.2) varies by SDK and
version — check each, every time. Do not infer support from the SDK's release
date.

## Checking for the 9.4 button fields (run one, don't assume)

Adapt paths to the project; these are detection recipes, not version claims.

| Stack | Check |
|---|---|
| aiogram (Python) | `python -c "from aiogram.types import InlineKeyboardButton as B; print('style' in B.model_fields, 'icon_custom_emoji_id' in B.model_fields)"` |
| python-telegram-bot | `python -c "import inspect, telegram; p=inspect.signature(telegram.InlineKeyboardButton.__init__).parameters; print('style' in p, 'icon_custom_emoji_id' in p)"` |
| pyTelegramBotAPI | `python -c "import inspect, telebot; print(inspect.signature(telebot.types.InlineKeyboardButton.__init__))"` |
| grammY / Telegraf (TS) | `grep -rn "icon_custom_emoji_id" node_modules/@grammyjs/types node_modules/typegram` |
| node-telegram-bot-api | Untyped JSON objects usually pass through — verify a real send, not the types |
| Telegram.Bot (C#) | Look for `Style` / `IconCustomEmojiId` on `InlineKeyboardButton`; check the release notes for Bot API 9.4 |
| Go / Java / other | Search the generated types for `icon_custom_emoji_id`; check the changelog for 9.4 |
| Raw HTTP | Always available — you control the JSON |

Three possible outcomes, three different responses:

1. **Field present** → use it normally.
2. **Field absent, SDK is permissive** (untyped dicts/objects reach the wire
   unchanged) → you may pass it through, but **prove it** with a real send and a
   captured request payload before claiming it works.
3. **Field absent, SDK is strict** (pydantic/dataclass/typed builders drop or
   reject unknown fields) → the field never reaches Telegram. Silent dropping is
   the dangerous case: the code looks right and nothing is colored.

## Escalation when the SDK lacks a needed feature

1. **Check for a newer stable SDK version** that adds it.
2. **Review breaking changes** between current and target versions.
3. **Assess a safe upgrade** (compat with the rest of the project, tests).
4. If upgrading isn't safe/possible, build an **isolated, typed Bot API
   adapter** for just the missing method(s):
   - typed request/response models for that endpoint;
   - one place, clearly named as a temporary shim;
   - reuse the project's existing HTTP/transport layer.
5. **Never place raw HTTP calls in business logic** — keep them behind the
   adapter.
6. **Plan removal:** note the adapter is temporary and to be deleted once the SDK
   supports the feature natively.

## Raw payload pattern for keyboards

`reply_markup` is a JSON-serialized object in the Bot API, so a raw path needs no
new types — only correct serialization:

```python
markup = {"inline_keyboard": [[
    {"text": "Confirm", "callback_data": "order:confirm", "style": "success"},
    {"text": "← Back", "callback_data": "order:menu"},
]]}
await bot_api_raw("sendMessage", {              # the project's existing transport
    "chat_id": chat_id,
    "text": text,
    "parse_mode": "HTML",
    "reply_markup": json.dumps(markup),
})
```

Constraints for this path:

- Build the markup in **one** helper so the rest of the code stays SDK-native.
- Validate it before sending (`scripts/validate_keyboard.py` encodes the rules:
  one action field per inline button, `style` value set, `callback_data` ≤64
  bytes).
- Keep the same `callback_data` scheme the SDK-native path uses, so handlers are
  untouched.
- Mark it as temporary with the removal condition ("delete once <SDK> ≥ <version
  implementing Bot API 9.4> is in the lockfile").

**Never** claim a field shipped when the SDK dropped it. If neither an upgrade
nor a raw path is acceptable, ship without the field and report it as deferred.

## Don'ts

- Don't upgrade an SDK without analyzing breaking changes.
- Don't scatter raw `POST`/`fetch` Bot API calls across the codebase.
- Don't claim a feature works because the Bot API has it — verify the SDK path
  and **test** it (`testing-playbook.md`).
- Don't assume a strict SDK forwards unknown keys; assume it drops them until
  you've seen the outgoing payload.
- Don't gate a whole redesign on one unsupported presentation field — ship the
  structural improvements and report the gap.

## Update delivery and new update types

New features arrive as new **update types** too: `stopped_message_generation` (10.3),
`widget_query` and `shared_widget_query` (10.4). Raw HTTP sends any method but does not add
handlers for incoming types. Check all four layers:

1. **Subscription:** pass `allowed_updates` explicitly on every `getUpdates`/`setWebhook` — when
   omitted, Telegram keeps the *previous* list. SDK defaults computed from registered handlers omit
   types the SDK doesn't know.
2. **Parsing:** does the SDK's `Update` model keep unknown keys or drop them?
3. **Routing:** can a handler be registered for the type, or does the dispatcher discard it?
4. **Serialization:** does the outgoing request contain the new fields (inspect the captured payload)?

## Verified SDK status (2026-11-12)

| SDK (latest on the registry) | Bot API | 10.3 | 10.4 widgets | Evidence |
|---|---|---|---|---|
| aiogram 3.31.0 | 10.3 | `disabled`, `force_reply`, `stopped_message_generation` present | `widget_query` kept as model extra, then **dropped with a RuntimeWarning** by `Dispatcher.feed_update`; never requested by `resolve_used_update_types` | `tests/test_sdk_aiogram.py` (real package) |
| grammY 1.46.0 / @grammyjs/types 5.0.0 | 10.3 | typed | not typed; `DEFAULT_UPDATE_TYPES` omits widget updates; raw middleware and the `api.raw` Proxy pass them | `examples/ts/sdk-grammy/adapter.test.ts` (real package) |
| python-telegram-bot 22.8 | 10.0 (README) | not checked | not checked | PyPI metadata only |

Adapters: `examples/python/sdk_aiogram/adapter.py`, `examples/ts/sdk-grammy/adapter.ts` — isolated,
each with a REMOVE WHEN condition. SDK status changes quickly: re-run the checks before relying on
this table.

## Bot API 10.5 status (2026-11-22)

Checked on the release day on the package registries and GitHub: **no SDK declares 10.5 yet**.
aiogram 3.33.0 (2026-11-19) declares 10.4; grammY 1.46.0 (2026-08-26) is on 10.3;
node-telegram-bot-api 2.4.1 (2026-11-21) predates the release. tdlib/telegram-bot-api
committed "Update version to 10.5." on 2026-11-21: a self-hosted server built after that serves
10.5. What breaks or is missing until an SDK catches up:

- `setMySettings`: call it raw (`bot.session`/`api.raw`, or the adapters below).
- `getMe` now returns `BotFullInfo`. A typed SDK that parses it as `User` may drop
  `active_usernames`, `inline_query_placeholder`, `needs_inline_query_location` and
  `has_topic_sidebar`; read the raw result when you need them.
- `callback_query_mode` `auto` / `inline`: SDK filters and helpers that assume
  `callback_query.message` (e.g. `query.message.chat.id`, `message.edit_text`) fail on callbacks
  that carry only `inline_message_id`. Keep `default` until every handler uses
  `bot-settings.md#callback-query-mode`.
- Expandable quotes: SDK models of `InputRichBlockExpandableBlockQuotation` with `text` produce
  payloads 10.5 rejects; send `blocks` as a raw dict.

## Release-note check (2026-11-15)

Read from each project's GitHub releases / README and the package registries on
2026-11-15 (Bot API 10.4 was released 2026-11-09). "Declared" = what the project says
it supports; it was **not** re-tested here unless the table above has a test.

| SDK | Latest release (date) | Declared Bot API | 10.3 | 10.4 | Source |
|---|---|---|---|---|---|
| aiogram (Python) | 3.32.0 (2026-11-15) | 10.4 | yes | **yes**: `bot.send_widget` … `edit_shared_widget_data`, `Update.widget_query` / `shared_widget_query`, router observers `widget_query` / `shared_widget_query` | PyPI wheel inspected 2026-11-15 (PR #2004); not routing-tested here — the pinned contract test is still 3.31.0 |
| python-telegram-bot (Python) | 22.8 (2026-06-12) | 10.0 | no | no | README badge, PyPI |
| pyTelegramBotAPI (Python) | 4.37.1 (2026-10-17); 4.37.0 notes "Bot API support bumped up to v.10.3" | 10.3 | yes (declared) | no | GitHub release notes, PyPI |
| grammY (TypeScript) | 1.46.0 (2026-08-26) | 10.3 | yes | **no release yet** | GitHub release notes, npm |
| Telegraf (TypeScript) | 4.16.3 (2024-02-29) | 7.1 | no | no | README, npm — unmaintained for new API versions |
| node-telegram-bot-api (TypeScript) | 2.4.0 (2026-11-09) | 10.4 | not checked | yes (declared): `sendWidget`, `sendSharedWidget`, `answerWidgetQuery`, `editSharedWidgetData` in the published build | npm tarball inspected 2026-11-15; not tested here |
| go-telegram/bot (Go) | 1.28.0 (2026-11-09) | 10.4 | yes (declared) | yes (declared) | README, GitHub release notes; not tested here |
| tdlib/telegram-bot-api (server) | commit "Update version to 10.4." (2026-11-09) | 10.4 | yes | yes | GitHub commits |

Consequences:

- aiogram ≥ 3.32.0 and node-telegram-bot-api ≥ 2.4.0 ship the widget methods: use them
  natively and still list `widget_query` / `shared_widget_query` in `allowed_updates` if you
  pass that list by hand. On every other Python/TypeScript SDK above (and aiogram ≤ 3.31), 10.4 features (widgets, `widget_query`,
  `getUniqueGift`, chat share themes, TON wallet types, ephemeral callback replies
  without `receiver_user_id`) need the raw-call adapters
  (`examples/python/sdk_aiogram/adapter.py`, `examples/ts/sdk-grammy/adapter.ts`) and
  an explicit `allowed_updates` list.
- python-telegram-bot and Telegraf also lack 10.1-10.3 (rich messages, ephemeral
  messages, Stop for drafts): use raw requests for them and check payloads with
  `py -3 scripts/validate_payload.py`.
- A self-hosted Bot API server built from tdlib/telegram-bot-api after 2026-11-09
  speaks 10.4; older builds reject the new methods.
- To find exactly which methods/fields a given SDK version lacks, compare its
  generated types with `data/bot-api/catalog.json` (`py -3 scripts/tg_api_lookup.py
  version 10.4` lists the new symbols).
