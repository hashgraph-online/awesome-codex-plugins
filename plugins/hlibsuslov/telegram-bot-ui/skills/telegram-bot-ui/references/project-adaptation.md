# Project adaptation (investigate before you change)

This skill is project-agnostic. Before touching anything, build an accurate map
of how the target project builds its **interface** — screens, keyboards,
navigation — and how it produces and delivers messages. Never assume a specific
language, framework, or SDK.

## Step 1 — Read project instructions

`AGENTS.md`, `CLAUDE.md`, `README`, `CONTRIBUTING`, docs/. Note conventions,
existing formatter utilities, the required test/lint/typecheck commands, and any
"how we send messages" guidance.

## Step 2 — Detect stack and versions

Determine, with evidence from the repo (manifest/lockfiles, imports):

- Language(s) and framework.
- **Telegram SDK and its exact version** (e.g. `aiogram`, `python-telegram-bot`,
  `pyTelegramBotAPI`, `grammY`, `Telegraf`, `node-telegram-bot-api`,
  `Telegram.Bot`, `TelegramBots`, `go-telegram/bot`, or raw HTTP).
- The **Bot API version** that SDK version implements (from its changelog/release
  notes). This bounds which UI and formatting features exist — in particular
  whether `style` and `icon_custom_emoji_id` (Bot API 9.4) are reachable
  (`sdk-compatibility.md`, `ui-changelog.md`).
- Presence of any **raw HTTP** Bot API calls / adapters already in the codebase.

Manifest hints: `requirements*.txt` / `pyproject.toml` / `Pipfile`;
`package.json` + lockfile; `go.mod`; `pom.xml` / `build.gradle`; `*.csproj`;
`composer.json`; `Cargo.toml`.

## Step 3 — Find every UI touchpoint

Search for where the interface is **built, sent, and edited**. Useful patterns
(adapt to the SDK):

**Keyboards and buttons**

- Markup builders: `InlineKeyboardMarkup`, `InlineKeyboardButton`,
  `ReplyKeyboardMarkup`, `KeyboardButton`, `ReplyKeyboardRemove`, `ForceReply`,
  `reply_markup`, `inline_keyboard`, `keyboard=`, `Markup.inlineKeyboard`,
  `.button(`, `.row(`, `InlineKeyboardBuilder`.
- Actions and routing: `callback_data`, `callback_query`, `answerCallbackQuery`,
  `answer_callback_query`, `.callbackQuery(`, callback factories/filters,
  `url=`, `web_app=`, `copy_text`, `switch_inline_query`, `login_url`, `pay`.
- New presentation fields already in use: `style`, `icon_custom_emoji_id`.
- Screen edits: `editMessageText`, `editMessageReplyMarkup`,
  `editMessageCaption`, `edit_text`, `edit_reply_markup`.
- Chat chrome: `setMyCommands`, `BotCommand`, `BotCommandScope`,
  `setChatMenuButton`, `MenuButton`, `/start` payload parsing, deep-link
  builders.
- Conversation state: FSM/state machines, scenes, wizards, conversation
  handlers, session storage — this is the navigation graph.

**Message content**

Search for where messages are **generated, formatted, sent, and edited**:

- Send/edit methods: `sendMessage`, `sendPhoto`, `sendMediaGroup`,
  `editMessageText`, `answerInlineQuery`, `sendRichMessage`,
  `sendRichMessageDraft`, `answer(`, `reply(`, `.send_message`.
- Parse modes: `parse_mode`, `ParseMode`, `HTML`, `MarkdownV2`, `Markdown`.
- Entities: `entities`, `MessageEntity`, `offset`, `length`.
- Rich: `InputRichMessage`, `InputRichBlock`, `rich_message`, `markdown=`,
  `blocks=`, `draft_id`.
- Formatter utilities: files/functions named `format`, `escape`, `render`,
  `markup`, `template`, `md`, `html`.
- Templates & localization: i18n catalogs, `.ftl`/`.po`/`.json`/`.yaml`
  locale files, `gettext`, `_()`, `t(`, Fluent, ICU.
- AI-generated content and **streaming** loops (token/chunk handlers, partial
  edits).
- Inline mode, Web Apps, and business-connection code paths, if present.

## Step 4 — Classify screens and messages

For each touchpoint, label it: entry (`/start`) / menu / form step /
confirmation / result / error / empty state / notification / document /
AI answer / media post / inline result. This drives both the UI treatment
(`navigation-and-flows.md`) and the body format (`format-selection.md`).

## Step 5 — Capture the current state

Record: the `callback_data` scheme and who parses it; which keyboards are built
where and whether a shared builder exists; how navigation/back is implemented;
where conversation state lives; which parse modes are used; whether escaping is
per-format or one universal helper; where limits/magic numbers live; how
splitting is done; how topics/reply context are attached; how strings are
localized; and where tests live.

## Step 6 — Identify real defects only

Real UI defects: ambiguous or duplicated button labels, keyboards with 8+
undifferentiated options, screens with no way back, destructive actions one tap
from a safe one, taps with no feedback, stale messages acting on moved data,
state not reflected after a toggle, missing empty/error variants, hardcoded
strings bypassing i18n, labels that truncate in other locales.

Real rendering defects: `can't parse entities`, user input breaking MarkdownV2,
HTML shown as literal text, code blocks split mid-fence, lost keyboards,
corrupted localized templates, oversized payloads.

Do not "improve" working code that isn't in scope.

## Step 7 — Produce a short screen/UI map

Before implementing, output a concise map: entry points → screens and their
keyboards → `callback_data` scheme → transitions → formatter(s) → transport →
detected defects → proposed minimal change. The per-screen table format is in
`navigation-and-flows.md`. Get this right before writing code.

## What to build only when justified

Create these **only** if the audit proves the need — never by default:

- a custom AST or intermediate representation;
- a universal renderer;
- a separate formatting library;
- a generic "screen framework" or menu DSL;
- a CMS or visual editor;
- a complex message builder;
- a new transport layer.

Prefer extending the project's existing utilities in its existing style — if it
already has a keyboard builder, use it rather than introducing a second one.

## SDK capability gap

If the installed SDK lacks a needed field or type (`style`,
`icon_custom_emoji_id`, Rich Messages), follow the escalation in
`sdk-compatibility.md` (check newer SDK → review breaking changes → safe upgrade
→ else isolated typed Bot API adapter, never raw HTTP in business logic, with a
removal plan).
