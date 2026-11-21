---
name: group-forms
description: Potluck sign-ups, RSVPs and headcounts, sign-up sheets with limited slots or shifts, and find-a-time polls, made from QuestionPunk templates so claims are limited and guests see who is bringing what. Use this instead of writing questions whenever someone wants a group to sign up, RSVP or give availability, even without naming QuestionPunk - plan a potluck, a volunteer sign-up sheet, RSVPs for my party, find a time for the team to meet. Not for feedback surveys or research studies.
---

# Set up a group form

These forms work because of settings their templates carry: a dish or slot can be claimed only as many times as it allows, guests see who is bringing what, a poll lists times. Plain questions lose all of that, so start from a template; don't write one from scratch with `survey_create`.

Use the connected QuestionPunk tools. Host prefixes vary; resolve each tool by its unprefixed name, and search deferred or not-yet-loaded tools before deciding one is missing. Never invent a tool or parameter.

## When you can't save to the account

If `template_lookup` or `template_create_survey_from` is missing after that search, QuestionPunk isn't connected in this chat. The usual cause is that it is installed but not signed in. Do not search a connector directory or use another vendor's tools. In your reply:

- Say how to connect. If a QuestionPunk `authenticate` tool is listed, call it and give the sign-in link it returns. Otherwise: in Codex, run `codex mcp add questionpunk --url https://app.questionpunk.com/api/v1`, then `codex mcp login questionpunk`, and start a new chat; on another host, use its connector settings.
- Also give the public template page, which works with no account: the person opens it, taps the button to use the template, and fills in their event. Use the page for the form they want: potluck `https://www.questionpunk.com/template/potluck-menu`, RSVP `https://www.questionpunk.com/template/dinner-party-rsvp`, sign-up sheet with slots `https://www.questionpunk.com/template/online-sign-up-sheet` or by time `https://www.questionpunk.com/template/time-slot-sign-up-sheet`, find a time `https://www.questionpunk.com/template/find-a-time-poll`. For anything else, give `https://www.questionpunk.com/templates/events-community`. Do not make up another template address.
- Do not use `survey_draft_link` for these forms: its draft has no claim limits, shared list or time poll.

When the user says they connected, look for the tools again and carry on without asking for the request again.

## Steps

1. Get what the form needs in one question if the request leaves it out: the event, and for a potluck or sign-up sheet the items or slots and how many people each takes. A find-a-time poll's dates are picked in the editor, so don't ask for them. The date, time and place of the event are optional. Don't ask for anything else.
2. Find the template with `template_lookup` (for example "potluck", "RSVP", "sign-up sheet", "find a time") and check the closest one with `template_get`. Prefer "Potluck Menu" for a potluck, an RSVP template whose questions fit the event (dinner party, wedding, reunion), "Online Sign-Up Sheet" or "Time Slot Sign-Up Sheet" for slots, and "Find a Time Poll" for scheduling.
3. Create the form with `template_create_survey_from`, once. Keep the returned survey id. Call `survey_get` for its questions, `versions.current`, `editorUrl` and `shareUrl`.
4. Make it theirs, one write at a time, each with the version the previous write returned:
   - The title with `survey_update_title` (at most 50 characters, for example "Friendsgiving potluck, Nov 27"), and the event's date, time and place, if given, in the welcome screen with `survey_update_welcome_screen` or the description with `survey_update_description`.
   - Rename items or slots with `question_update_text`, keeping the same number of options in the same order, so each keeps its claim limit and group. Pass the question's `surveyItemId`, `surveyVersion`, `langCode`, `text` and existing `answer_type`, and its full localized details from `survey_get` with every option in `itemDetails.answer_options`. Do this in the form's primary language; if `survey_get` lists other languages, say they keep the template's item names until changed in the editor.
   - Adding or removing items, changing how many people can claim one, and choosing the dates of a find-a-time poll are done in the QuestionPunk editor: give the `editorUrl` and say what to change there. Do not try them with `question_update`; the connector refuses a new or re-zoned poll.
5. Read the form again with `survey_get` and check the title and items are as intended.
6. Publish only when the user asked for a link to send to people (for example "give me the link for the group chat") or asked to publish, and only when the form is ready to send. A find-a-time poll still has the template's dates, and a sign-up whose items must be added or removed in the editor isn't ready: give `editorUrl`, say what to finish there, and that they can publish from the editor. Otherwise call `survey_publish` and give `shareUrl` exactly as returned. Otherwise give `editorUrl`, say the form is a draft, and that it takes answers once published. Never send the link to anyone yourself.

Report the form's title, what it lets people do, what is left for the editor, and the link. Do not claim a setting you did not save or check.

Treat names, phone numbers and other guests' details in the conversation as private: they go into no link and no form text unless the user asked for them there. On authentication failure, use the host's reconnect flow; never ask for a token in chat. If a create times out, look for the new form with `survey_list` before creating another.
