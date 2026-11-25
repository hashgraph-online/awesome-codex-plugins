---
summary: "The command menu over its whole life: what a command is for, naming and descriptions, scopes and languages, auditing code against setMyCommands, planning and applying the update safely."
verified: "2026-11-25"
bot_api: "10.5"
---

# Bot commands: design, audit and sync

Commands are the bot's table of contents: the Menu button and the `/` list in the composer show
them, and they are the one entry a returning user can find without scrolling. Checked against
Bot API 10.5 on 2026-11-25 (core.telegram.org/bots/api#setmycommands,
#determining-list-of-commands, #botcommand). Labels: **[API]** spec, **[Heuristic]** this skill.

## Contents

- [What belongs in the menu](#what-belongs-in-the-menu)
- [Names and descriptions](#names-and-descriptions)
- [Scopes and languages](#scopes-and-languages)
- [The lifecycle: audit, plan, apply, verify](#the-lifecycle-audit-plan-apply-verify)
- [The declaration file](#the-declaration-file)
- [Commands, menus, rich messages and Mini Apps together](#commands-menus-rich-messages-and-mini-apps-together)
- [Mistakes](#mistakes)

## What belongs in the menu

**[Heuristic]** A command earns a place when a user would come back for it from any state:
`/start` (home), the two or three jobs the bot exists for (`/new`, `/orders`, `/balance`),
`/settings`, `/help`. Three to seven entries; more turns the list into a second menu nobody reads.
Flow steps ("/confirm", "/next") are buttons, not commands. Admin and debug commands live in a
narrower scope (administrators, one chat) or stay unlisted (`"hidden": true` in the declaration),
and their handlers check rights on every call: being unlisted is not protection.

`/start` reaches every user through the Start button and deep links; list it when "back to the
beginning" is useful, otherwise it may stay out. In groups a command can be addressed as `/command@botname`:
with privacy mode on, the bot still receives commands explicitly meant for it, and a bare `/start`
only if it was the last bot to post in the group **[Official, Bot Features]**.

## Names and descriptions

**[API]** `command`: 1-32 characters, lowercase English letters, digits and underscores only.
`description`: 1-256 characters. At most 100 commands per list. `is_ephemeral: true` marks a
command whose answer is an ephemeral message (only the sender sees it).

**[Heuristic]** Names are short verbs or nouns users would type (`/orders`, not `/my_orders_list`);
never rename one users know without keeping the old handler for a release. Descriptions say what
happens in four to six words, in the user's language, one style for the whole list (capital first
letter, no final period), and don't repeat the name ("Orders: your orders" adds nothing).

## Scopes and languages

**[API]** Telegram shows the **first list that is set**, in this order, and never merges lists:

| Where | Order |
|---|---|
| Private chat | Chat + language → Chat → AllPrivateChats + language → AllPrivateChats → Default + language → Default |
| Group, supergroup | ChatMember + language → ChatMember → ChatAdministrators + language → ChatAdministrators → Chat + language → Chat → AllChatAdministrators + language → AllChatAdministrators → AllGroupChats + language → AllGroupChats → Default + language → Default |

So a narrower list must repeat every command the user there should still see: a Russian
private-chat list with only `/start` hides `/help` from Russian speakers even though the default
list has it (`SCOPE_SHADOWED`). `language_code` is two-letter ISO 639-1; an empty one is the
fallback for languages with no list of their own. Keep the same commands in every language list
of one scope (`LOCALE_MISSING`); only the descriptions change.

## The lifecycle: audit, plan, apply, verify

1. **Audit** (read-only): `py -3 <skill>/scripts/tgui.py commands audit --root <project>` (MCP:
   `commands_audit`). It reads handlers in code (aiogram, python-telegram-bot, pyTelegramBotAPI,
   grammY, Telegraf, raw text checks) and registrations (`setMyCommands` / `set_my_commands`
   calls, `BotCommand(...)`, `bot-ui/commands.json`) and reports: `COMMAND_NO_HANDLER` (listed,
   nothing answers: error), `COMMAND_NOT_REGISTERED` (answered, not listed), `COMMAND_NAME_INVALID`,
   `DESCRIPTION_LENGTH`, `COMMAND_DUPLICATE`, `TOO_MANY_COMMANDS`, `LOCALE_MISSING`,
   `SCOPE_SHADOWED`, `DESCRIPTION_STYLE`. Telethon, Pyrogram and node-telegram-bot-api handlers
   are not detected; for those bots read `COMMAND_NO_HANDLER` by hand. `scan` lists what it found
   with file:line.
2. **Declare** the intended menu in `bot-ui/commands.json` (below), reviewed like code.
3. **Plan**: `tgui.py commands plan --root <project>` (MCP: `commands_plan`) prints one
   `setMyCommands` per scope and language and the `deleteMyCommands` for lists to remove, each
   checked against the catalog. Nothing is sent.
4. **Apply** from the bot's own deploy step or startup, with the bot's token from the environment:
   send the planned requests in order (they are idempotent, so a retry is safe). Never apply from
   the agent's machine with a production token.
5. **Verify**: save `getMyCommands` answers for the scopes you changed and run
   `tgui.py commands diff --root <project> --live-json <file>`; clients cache the menu, so
   reopen the chat before judging what users see.

## The declaration file

`bot-ui/commands.json`, format `bot-ui-commands/v1` (full schema in the docstring of
`scripts/bot_commands.py`):

```json
{"format": "bot-ui-commands/v1", "default_language": "en",
 "lists": [{"scope": {"type": "default"}, "language_code": "",
            "commands": [{"command": "orders", "description": {"en": "Your orders", "ru": "Ваши заказы"}},
                         {"command": "admin", "description": "Admin tools", "hidden": true}]}],
 "remove": [{"scope": {"type": "all_group_chats"}, "language_code": "de"}]}
```

A description given as a map becomes one list per language; `hidden` commands keep their handler
but are never sent.

## Commands, menus, rich messages and Mini Apps together

- The Menu button shows the command list by default; `setChatMenuButton` can turn it into a Mini
  App launcher instead (`MenuButtonWebApp`). Choose one per bot: a Mini App bot keeps `/start` and
  `/help` as commands and puts the rest in the app. **[API]** (method), **[Heuristic]** (choice)
- Every command lands on a screen that has the same name in the bot-ui map (`entryPoints` with
  `"type": "command"`), so `/orders` and the Orders button lead to the same place.
- A command that answers with a long structured result sends a rich message; one whose answer is
  private in a group can be `is_ephemeral`.

## Mistakes

| Mistake | Fix |
|---|---|
| `setMyCommands` on every start with a different order | one planned list, sent from deploy |
| A narrower scope list with only the new command | repeat the inherited commands in it |
| `language_code: "eng"` or `"en-US"` | two letters: `"en"` |
| A listed command whose handler was deleted | remove it from the list in the same change |
| Admin command in the default list | `all_chat_administrators` scope plus a rights check in the handler |
