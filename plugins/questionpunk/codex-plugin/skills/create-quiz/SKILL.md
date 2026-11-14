---
name: create-quiz
description: Make a quiz other people take and get scored on, as a QuestionPunk link with an answer key - trivia, a class or training check, or a friend quiz such as "How well do you know me?" where friends guess the creator's answers. Use whenever someone wants a quiz with right answers to send to others, even without naming QuestionPunk - a trivia quiz for a party, quiz my class on chapter 3, a quiz my friends take about me. Not for personality quizzes, polls or surveys with no right answers.
---

# Make a QuestionPunk quiz

A quiz is a survey whose multiple-choice questions carry an answer key. QuestionPunk scores each response against the key, and the key never reaches respondents' browsers.

Use the connected QuestionPunk tools. Host prefixes vary; resolve each tool by its unprefixed name, and search deferred or not-yet-loaded tools before deciding one is missing. Never invent a tool or parameter.

## When you can't save to the account

If `survey_create` or `question_create_bulk` is missing after that search, QuestionPunk isn't connected in this chat. The usual cause is that it is installed but not signed in. Do not search a connector directory or use another vendor's tools. In your reply:

- Say how to connect. If a QuestionPunk `authenticate` tool is listed, call it and give the sign-in link it returns. Otherwise: in Codex, run `codex mcp add questionpunk --url https://app.questionpunk.com/api/v1`, then `codex mcp login questionpunk`, and start a new chat; on another host, use its connector settings.
- For a friend quiz, give the public template page, which works with no account: `https://www.questionpunk.com/template/how-well-do-you-know-me-quiz` (or `https://www.questionpunk.com/template/best-friend-quiz`). The person opens it, uses the template and picks their own answers.
- For any other quiz, write it in the chat with the correct answer marked, and make a link with `survey_draft_link` when that tool is available (single-choice questions; 3 to 20 questions). Give the link exactly as returned and say plainly that the link carries the questions but not the answer key: they mark each correct answer in the editor's "Answer key" before publishing. Without that tool, give the quiz in the chat and the connection steps.

When the user says they connected, look for the tools again and carry on without asking for the request again.

## A quiz from scratch (trivia, class, training)

1. Settle the topic, level and number of questions from the request; default to 10 questions for trivia and say so. Ask only if the topic is missing.
2. Write each question with one clearly correct option and three or four plausible wrong ones. Check every fact you key; leave out a question you are not sure of rather than key a guess. Vary where the correct option sits.
3. Call `survey_create` (title at most 50 characters), then `survey_get` for the language and `versions.current`.
4. Add the questions with one `question_create_bulk` call. Each item: `answer_type: "multiple_choice"`, `required: true`, the options in `textItemDetails.answer_options`, and the key in `itemDetails.quiz`: `{ "correctOptionIndex": <0-based position of the correct option> }`. Add `"points"` (1 to 100) only if the user wants some questions worth more. For "select all that apply", set `itemDetails.multiple_selection: true` and key `{ "correctOptionIndex": null, "correctOptionIndices": [ ... ] }`; it is graded all or nothing. Do not key every option of a question: that grades nothing.
5. Read it back with `survey_get` and check that every question has its key at the right position. Fix a wrong key with `question_update` (`{ item: { itemDetails: { quiz: { "correctOptionIndex": n } } } }`).

## A friend quiz ("How well do you know me?")

1. Find the template with `template_lookup` ("how well do you know me", "best friend quiz", "partner quiz") and create it with `template_create_survey_from`, once. Call `survey_get`.
2. The template ships without answers: the creator's own answers are the key. Ask the user for their answer to each question in one message (list the questions and options). Do not guess them.
3. Set each answer with `question_update` as above, one write at a time with the version the last write returned. Change a question's wording or options with `question_update_text` only when asked, and then set its key again: changing a question's wording or its correct option's text clears the key.

## Finish

- A quiz with an unanswered key can't be published. Publish only when the user asked for a link to share or asked to publish: call `survey_publish` and give `shareUrl` from `survey_get` exactly as returned. Otherwise give `editorUrl` and say it is a draft.
- Report the title, question count, that each question is keyed (never print the answer key into a message meant for the people taking the quiz), and the link.
- Never send the link to anyone yourself. On authentication failure use the host's reconnect flow; never ask for a token in chat. If a create times out, look for the new quiz with `survey_list` before creating another.
