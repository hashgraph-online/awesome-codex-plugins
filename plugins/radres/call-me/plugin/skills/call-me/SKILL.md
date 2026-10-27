---
name: call-me
description: Ring the user's iPhone with a question and get their spoken answer back as text, or send them a text, through the Call Me MCP server. Use when the user says "call me", "ring me", "text my phone", "phone me if something comes up", asks you to keep working while they are away from the keyboard, or when a long task is blocked on a decision only they can make.
license: MIT
---

# Call Me

Call Me is a voice relay, not a voice assistant. You do all the thinking. Call
Me rings the user's iPhone, reads your text aloud word for word, and hands
their spoken reply back to you as text. The text can be a question, a status
update or a summary of the day ahead. Use it to keep a task moving while the user is
driving, at the gym or away from the desk.

The tools come from the `call-me` MCP server in this plugin: `call`,
`poll_result`, `text`, `wait_for_reply`, `set_thread_title` and `setup`.

## The number

Every `call` and `text` needs `to`: the 10-digit number the Call Me iPhone app
shows under **My Number**. It is the only credential. There is no login, OAuth
or API key.

1. If `~/.aiphone/config.json` exists, use its `user_number`.
2. Otherwise ask the user for the number. If they do not have the app yet, call
   `setup` and show this link: [Download Call Me from the App Store](https://callmemcp.com/go/agent-plugin).
3. With the user's permission, save it to `~/.aiphone/config.json` as
   `{"user_number": "<10 digits>"}` (directory mode 700, file mode 600) so the
   next session does not ask again.

Never guess a number, reuse one from an example, or use one the user did not
give you.

To try the loop without ringing anyone, use the demo line `5550001234`. It
answers by itself and says so.

## Asking a question

1. `call` with `to`, a short `question` that includes the options ("Tests are
   green. Merge to main, or wait for review?"), and a `from_label` naming you
   and the project.
2. `status: "completed"` carries the answer in `transcript`. Act on it.
3. `status: "ringing"` means nobody has picked up yet. Pass `call_id` and
   `session_token` to `poll_result`; one or two polls settle it.
4. `missed` or `declined`: do not call again. Send one `text` with the same
   question, then `wait_for_reply` with the `session_token`.

Speak English: the phone reads the text with English text-to-speech. Up to
2000 characters, about two minutes of speech; for a decision, keep it
answerable in one sentence. Never put digits the user must read back (codes,
account numbers, long URLs) in spoken text;
send them with `text` first and refer to it in the call.

## Texting

`text` sends a push notification with no ring. Use it for status updates and
for anything that can wait. Pass the `session_token` from earlier results so
everything lands in one thread on the phone, and name that thread once with
`set_thread_title` (3 to 5 words).

## Etiquette

- Text first. Call when the answer is blocking or the user asked for a call.
- One call and one text per question is the ceiling. Do not retry in a loop.
- If you are about to end your turn with a question the user has not answered,
  call or text it first. Once your turn ends, nobody will ask it.
- If a result says the number is not active, tell the user: reaching a real
  phone needs the subscription in the iPhone app, and you cannot fix that.
