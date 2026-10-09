# The shapes of a note

One entry per shape: what it is for, the fastest way to make one, the file,
and how it behaves on the board. `stickypane kinds` lists the shapes and
`stickypane kinds <shape>` prints the full example of one.

## Note

For anything to read: an explanation, a decision, a summary.
`echo "check env before deploy" | stickypane write deploy-notes --open`

```markdown
---
title: Why the cache
---
Any Markdown. A ```mermaid block (graph, flowchart, sequence, erDiagram) is drawn.
```

A one-line file is a complete note. A diagram that cannot be drawn keeps
its source.

## Board

For work in columns. `stickypane card work add "login API" --to Doing`

```markdown
---
type: board
---
## To do
- payments
## Doing
- login API
  - refresh tokens come later
```

Each `## Heading` is a column and each top-level `- item` a card; indented
lines are the card's details. The user moves cards with keys and the file
changes. `stickypane card work move login --to Done` moves one.

## Checklist

For a list of steps. `stickypane todo plan add "write tests"`

```markdown
---
type: checklist
---
- [x] add endpoint
- [ ] write tests
```

Shown with a progress bar, open items first and done ones below, newest
first. The user ticks items with `space`; `stickypane todo plan check tests`
ticks one from your side. Do not write times: the board writes
`✅ 2026-10-03 14:02` after a ticked item by itself, even one you ticked by
editing the file, and `created:` into a note it makes.

## Log

For what happened, in order. `stickypane log worklog --time "tests passed"`

A note with `type: log`, one line per entry, or any `.log`, `.txt` or
`.out` file. The view follows the end as the file grows until the user
scrolls up. `stickypane show logs/app.log` follows a log of the project.

## Chat

For talking with the user on the board. `stickypane say chat "41/41 pass" --as claude`

A note with `type: chat`: `@name HH:MM text` lines under a `## YYYY-MM-DD`
heading. The user presses n to answer, as themselves. To wait for the
answer: `stickypane watch --once --note chat --type message.added`.

## Chart

For numbers. `stickypane chart tokens add input 1200`

```markdown
---
type: chart
view: heat
---
2026-10-01: 41,200
2026-10-02: 8,900
```

Each `label: number` line is a value; other lines are text above it.
`view: bar` (default) draws bars, `spark` a one-line trend, `heat` a
calendar when the labels are dates.

## Form

For a decision that is the user's. Write it, show it, wait:
`stickypane wait deploy --timeout 10m`

```markdown
---
type: form
title: Deploy now?
---
## Target
- ( ) staging
- ( ) production

[ Deploy ] [ Cancel ]
```

`- ( )` is one choice, `- [ ]` any number, `> ` a line to type into, and
the last line the buttons. A press writes `submitted:` into the front
matter and `wait` prints the answers, which the form then shows under its
buttons. To show what you did with them, log it next to the form:
`stickypane log deploy.log --time "deployed to production"` appears in the
form's pane as its output. See the `asking-the-user` skill.

## Script

For a command the user should run, not you: `deploy.sh` in `.sticky/`, or
`deploy.ps1` for PowerShell. `enter` asks first, then runs it with `sh` or
PowerShell in the project folder; the output
goes to `deploy.log`, which opens and follows. It never runs without a yes.

## API requests (exp)

Experimental: the format and the commands may still change. For HTTP requests to try and check: `api.http` in `.sticky/`, written as
resterm and the VS Code REST Client write it. Use resterm's words for checks
and captures, so the same file runs in resterm too.

```http
@base = {{host}}/v1

### Log in
# @pre ./scripts/make-user.sh
POST {{base}}/login
Content-Type: application/json

{"user": "min"}
# @capture file token {{response.json.token}}
# @assert response.statusCode == 200
# @assert response.json("user") == "min"

### Me
GET {{base}}/me
Authorization: Bearer {{token}}
# @assert "json" in response.header("Content-Type")
```

- Variables: `@name = value`, `{{name}}`; `env:NAME` or `{{$processEnv NAME}}`
  reads the environment or the project's `.env`. Environments live in
  `rest-client.env.json` (or `resterm.env.json`); `# @env prod` chooses one.
- `# @assert`: `response.statusCode`, `response.json("a.b[0]")`,
  `response.header("Name")`, `response.text()`, with
  `== != < > <= >= in contains exists`; `time < 500` works on the board only.
- `# @capture file name {{response.json.path}}` keeps a value for the
  requests after it.
- Read on the board only (resterm skips them): `# @pre cmd`, whose
  `name=value` lines become variables, and `# @post cmd`, which reads the
  response as JSON on standard input.
- WebSocket: a `ws://` URL, or `# @websocket timeout=5s idle-timeout=1s
  subprotocols=chat.v2`, with steps `# @ws send <text>`, `send-json`,
  `send-base64`, `ping`, `pong`, `wait 500ms`, `close 1000 bye`. The log is
  the transcript (`→` sent, `←` received); `response.received` counts the
  messages and `response.json("[0].type")` reads them.
- gRPC: `GRPC host:port` with `# @grpc package.Service/Method`,
  `# @grpc-plaintext true` (HTTP/2 without TLS), `# @grpc-metadata k: v` and a
  JSON body. Descriptors come from `# @grpc-descriptor api.protoset`, else
  server reflection, else fields go by number (`{"1": 7}`).
  `response.grpc.status == "OK"`; unary and server-streaming calls.
- `stickypane api api "Log in"` sends one (`--all` every one, `--env prod`)
  and prints the response, checks and captures; it is in `api.log` too, with
  credentials hidden and a last line that says how it ended:
  `[200 OK · 38ms · Log in · 2/2 ✔]`. On the board, `enter` sends after the
  user's yes.

## Tab

For a separate screen: a folder of `.sticky/`, such as `deploy/`. Its
files are the tab's notes. `stickypane mv plan deploy/` moves a note there;
`stickypane show deploy/plan` switches to the tab and shows it. Linking a
folder of the project (`stickypane show docs/`) makes it a tab.

## Book

For pages read in order: a folder inside a tab, such as `deploy/guide/`.
It is one note whose pages are its files, by name; `,` and `.` turn pages.
