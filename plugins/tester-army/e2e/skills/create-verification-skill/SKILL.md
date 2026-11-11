---
name: create-verification-skill
description: Generate a project-local verify-<app> skill on top of e2e, so any coding agent can launch the app, check it is worth driving, exercise a feature the way a user does, keep evidence, and bug bash it. Writes the skill, a feature map with one explore charter per feature, and proves it once. Use for /create-verification-skill, "make a verification skill for this repo", or when a project has no scripted way to prove UI behavior.
disable-model-invocation: true
metadata:
  openclaw:
    homepage: https://e2e.com
    requires:
      bins:
        - node
        - npx
---

# Create a verification skill

A coding agent that changes an app should be able to prove the change the
way a user would see it. This skill writes that proof recipe for one
project as a skill, `.agents/skills/verify-<app>/`, built on e2e. The
config launches the app, `e2e mcp` drives it live, tests pin what must
hold, `e2e explore` bug bashes it, and `.e2e/` keeps the evidence. Write
the output for the next agent, not for a human. It will be read cold,
mid-task, by an agent that has never seen the app.

The e2e skill is the reference for everything e2e does. Read it first and
link to it rather than restate it. It is the sibling
[e2e skill](../e2e/SKILL.md), wherever this skill was installed from; when
it is missing, `npx skills add e2e-inc/e2e` or `npx e2e init` installs
it. `npx e2e guide <topic>` prints a reference from the project's installed
package; prefer that version when the two differ. Topics
named below (`setup`, `writing-tests`, `mcp`, `explore`, `bug-bash`,
`running`, `debugging`) are its reference files.

## 1. Interview the repo, not the user

Answer these from the codebase and ask the user only what you cannot
observe.

| Question | Where the answer is | What it decides |
| --- | --- | --- |
| Surface | What a user touches. A web UI, an iOS or Android app, an API | One skill per primary surface; name the others for a later run. Web goes through `@e2e-dev/web`, iOS and Android through `@e2e-dev/mobile`. An API with no UI still gets a `web()` target with `app.url` and `app.command` so the runner starts it, and its tests take only `app` and use `fetch` (topic `writing-tests`). A native desktop app has no e2e engine yet, say so and stop. So does a project where no engine has a surface to drive: a CLI, a library, or a batch job, and a desktop frontend whose only browser output is a native-runtime notice. An HTTP service with no UI is not one of those; this row drives it through `web()`. Stop on the observation, not after a write: name the entry point, the engine that cannot drive it, and that no skill was generated |
| Run | The documented dev command, its ports, env vars, seed data, auth | The target's `app.command` (topic `setup`). A dev server that compiles a route on first visit reads as broken to an agent, so prefer a production build command when the repo has one |
| e2e state | `e2e.config.ts`, the `tests` glob, `e2e` in `package.json`, `.agents/skills/e2e/`, the MCP server in `.codex/config.toml`, `.mcp.json`, or `.cursor/mcp.json`, and any Playwright or Cypress suite | Nothing there, once the Surface row found something an engine can drive, means `npx e2e init` first (topic `setup`). Running this skill requests that setup. Init registers MCP for Claude Code, Cursor, and Codex. Codex loads its project entry after the project is trusted and a new session starts (topic `mcp`). Check that the session has the e2e tools before a live drive. An existing Playwright or Cypress suite is the best source of locators, seeds, and sign-in steps; read it. A config with no model runs the deterministic steps and the MCP tools, and nothing else |
| Observe | The trace page, screenshots, video, the report, and what the app leaves behind in files, rows, sent messages, logs | The side-effect stores the Evidence section names. Find them now |
| Isolate | Can two instances run side by side? | Port `0` in `app.url` gives each run its own app; `command.reuseExisting: true` attaches to one already running on the port. A shared instance that cannot be duplicated (one database, one simulator) becomes a rule in the generated skill. Refusing to double-drive it beats corrupting the user's session |
| Name | The package name or the repo name | `<app>` in `verify-<app>`, lowercase, no scope |

If the checkout does not build or start as-is, fix that first or report it
precisely before generating. A skill written against a broken base teaches
wrong steps. An irrelevant missing asset (a static dir the API never
serves, a sample config) may be created by the generated skill, marked as
verification scaffolding and removed in Cleanup.

An existing `verify-<app>/` is read before anything is written. Keep its
SKILL.md and feature files, add the features the map lacks, and change an
existing file only where the app contradicts it.

## 2. Generate the skill

Write `.agents/skills/verify-<app>/SKILL.md` with YAML frontmatter.
`name: verify-<app>` and a `description` naming the app, the surface, and
when to reach for it; without frontmatter the skill never registers. When
the project has `.claude/skills/`, link it the way `e2e init` does, a
relative symlink `.claude/skills/verify-<app>` to
`../../.agents/skills/verify-<app>`. Every section says what the interview
found, no placeholders.

| Section | Holds |
| --- | --- |
| Read first | One line that sends the reader to the e2e skill and names the config file and `tests` glob this skill drives |
| Launch | The exact command that starts the app for verification and how readiness shows. With a target `app.command`, launch is `npx e2e run <smoke file>` or an `open_session` over MCP; the runner starts the app, waits for the URL, and stops it. Without one, a target with `app.url` only, the dev command the user starts by hand, and the line that proves the port answers; or keep the command and set `reuseExisting: true`. Say which ports and env the command needs and what seeds the data |
| Doctor | One read-only check that answers "is this instance worth driving?". `npx e2e list` loads the config and prints every test-target pair without starting anything, so a config error shows here first. Then the smoke test, a model-free test that opens the app and pins one landmark; exit `0` means the app starts, the engine runs, and the landmark renders. No smoke test in the project: write `tests/smoke.e2e.ts` now. A signed-in app's auth doctor is an ordinary signed-in smoke test that consumes a named session: selecting that test runs its setup and checks the restored state, so one command proves the app starts, the session restores, and a signed-in landmark renders. Running the setup file alone selects no test and exits `NO_TESTS`, so it is not the doctor. An agent runs Doctor first whenever anything looks off |
| Drive | Two lanes and when to use each. Live over MCP: `open_session`, `observe`, the verbs, and `locate` before any locator is written (topic `mcp`); list the project tools and credentials the session's catalog offers. Scripted: a test under the `tests` glob, `screen` where the name on screen is known, `agent.act` where the flow varies (topic `writing-tests`). Prefer stable handles, roles and accessible names, labels, test ids, routes. Name the credentials and sessions a signed-in drive starts from |
| Evidence | What a proof keeps and where. Every run writes `.e2e/report.json`; a failed test gets `.e2e/results/<test>/trace.md`, `--trace on` gives one to passing tests too, `--video` records the attempt (topic `running`), `app.screenshot('<name>')` saves a named frame (topic `writing-tests`). The next run clears `.e2e/results/`, Doctor included, so a proof that must outlive it runs with `--output .e2e/proof/<name>` or its attempt directory is copied out before anything else runs. State the proof standards (below) |
| Bug bash | How this app is bashed (topic `bug-bash`): the bug-bash config to write (what the local app cannot do, the postures, the isolation choice from the interview), the accounts to seed, `.e2e/bugbash/` added to `.gitignore`, and the rule that the charters come from the feature map (section 3). The verification bar: a finding is a bug only once `tests/bugbash/<slug>.e2e.ts` fails on the reported defect, as topic `bug-bash` step 6 reads it |
| Cleanup | What to tear down. The runner stops the app it started and `close_session` stops the one a session started; a server the user started stays theirs. Never kill by process name; stop what you started. Cleanup removes instances and scratch state (seeded accounts, scaffolding, charters whose findings were all rejected), never the evidence; name where the evidence is |
| Helpers | Any script the skill ships is executable and its invocation is in the skill body. A helper the reader has to reverse-engineer is not a helper. Most projects need none; the e2e CLI is the helper |

Proof standards, for the Evidence section: exercise the real user path,
not internal setters or test-only endpoints; capture the action and the
resulting state, not only the final screen; verify side effects (files
written, rows inserted, messages sent) in the stores the interview found;
mock only where a production boundary already isolates the external
system. When the safe path is a dry run or a test mode, verify what it
skips by watching files, network, and refs rather than trusting its name.

## 3. Seed the feature map

Create `.agents/skills/verify-<app>/features/README.md` plus one file per
user-facing feature you can identify, the top three to five first, from
routes, navigation, commands, or docs. Follow the example skill this
generator produced and ran for the e2e playground app. Its entry point is
[SKILL.example.md](references/example/verify-playground/SKILL.example.md)
so clients do not discover it as another installable skill, and its feature
map is [features/README.md](references/example/verify-playground/features/README.md)
with [todos.md](references/example/verify-playground/features/todos.md),
[forms.md](references/example/verify-playground/features/forms.md), and
[login.md](references/example/verify-playground/features/login.md). The
index is a table of feature, route, test file, and status (`tested` or
`untested`). Each feature file has these H2s, from the user's point of
view.

| H2 | Holds |
| --- | --- |
| `Sub-features` | What the feature is made of, one line each |
| `How to get to it (user POV)` | Route, navigation, the account it needs |
| `Driving it with e2e` | The test file that pins it, the locators that matter (checked with `locate`), the MCP steps for a live walk |
| `Proof` | The observable end state that means it works, on screen and in the side-effect store |
| `Charters` | One or two `e2e explore` goals for this feature, each one area, one posture, one sentence (topic `bug-bash`, step 2). Written as the fan-out line `slug\|target\|agent\|charter`, so the bug bash pastes them; a charter that starts signed in names its `--session` and runs alone |
| `Gotchas` | What reads as broken but is not; what the local app cannot do |

The map is the project's maintained verification source, and the bug bash
reads its charters. A proof that drives one convenient entry point is
incomplete when the map lists others, and a bug bash that skips a mapped
feature reports the gap. A feature without a test gets one in step 4 or is
marked `untested` in the index.

## 4. Prove the generated skill before handing it over

Run its own instructions end to end once, from a shell in the project.

1. Doctor: the `npx e2e list` call the skill names, then the smoke test;
   both exit `0`.
2. Drive one mapped feature through its test file. One is enough; the map
   exists so later runs cover the rest. A missing test: write it now from
   the feature file, with locators checked over MCP.
3. Bug bash one charter from the map: `npx e2e explore '<charter>'
   --config <bug-bash config> --agent <persona> --max-steps 3 --output
   .e2e/bugbash/<slug>`, plus `--session <name>` when the charter names
   one. Read its `Findings` and triage; do not verify every finding now.
   Then read the run's `run.explore` in `report.json`: an ending of
   `aborted`, or steps that ran a generic survey instead of the mapped
   charter, leaves the bug bash unproven and the handover says so. The
   steps prove the charter ran, not the exit code: `1` is also what a run
   that executed no step exits with. A `--max-steps` ending states the
   coverage the run reached. This
   proves the model, the config, the charter, and the output directory, not
   the app. Without a model, skip this step and say in the handover that
   the bug bash is unproven.
4. Cleanup, then confirm the evidence still exists at the named location.
   A cleanup that eats the proof fails this step.

Fix what fails, and run Cleanup after every failed iteration too, so
broken attempts do not strand ports and processes. A generated skill that
was never executed is a draft, not a deliverable. Leave the project as the
user had it. The generated skill, its feature map, the gitignore line, and
any test you added are the change; `.e2e/` output and the bug-bash config
stay untracked unless the user asks otherwise.

## 5. Hand over

Tell the user what landed. The skill path, the features mapped and which
have tests, the charters, what the proof run showed, and the evidence
paths. Running the map keeps it honest. When a route or label changes and
a test fails, the feature file changes in the same commit. Rerun this skill
when the app grows a feature the map lacks; section 1 says how an existing
map is treated.

A project with no supported surface stops in section 1 instead, and this
handover reports what you observed and that nothing was written.

## Rules

- Generate from what you observed. A section that could apply to any app
  is not finished.
- One sentence from the e2e skill beats a paragraph of your own. Link the
  topic.
- Never put a secret in the generated skill or the map. Name the
  credential (topic `setup`).
- Do not commit on the user's behalf. List what you created.
