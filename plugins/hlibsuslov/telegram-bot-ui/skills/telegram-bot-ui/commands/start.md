# start: what to do next in this project

**When:** the skill was called with no request, with "what can you do", or "continue where we
left off". Runs nothing by itself.

## Steps

1. `tgui.py next --json --root <project>` (after `context`). It returns up to three
   suggestions, each with a command and a reason, and the full menu.
2. Answer in the user's language, plain words, no internal names:
   - up to three lines, best first: what, why (the signal in everyday words), and what to say
     ("say: tidy up the checkout screens");
   - then the short menu: review the bot · make it nicer or add a screen · fix a bug · build a
     new bot or feature (shop, payments, booking) · post to a channel · a widget in a message ·
     a Mini App · premium emoji · let an agent report through the bot · open the screen map or
     do Studio requests · answer a Bot API question.
3. If `NO_TELEGRAM_CODE`: ask one question, "What should the bot do?", and offer three examples
   from `tgui.py examples --query ""` (the first three families).
4. Never start a suggestion yourself; wait for the user's choice.

## Without scripts

Read `bot-ui/context/findings.json` and `bot-ui/context/requests/*.json` if they exist; suggest
queued requests first, then open P0/P1 findings, else `audit`. If nothing exists, say "no saved
context yet" and show the menu.

## Done

The user sees at most three concrete next steps and the menu; nothing was changed.
