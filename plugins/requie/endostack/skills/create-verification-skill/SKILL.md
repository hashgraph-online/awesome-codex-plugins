---
name: create-verification-skill
description: Generate and prove a project-local verify skill that tells a later agent how to start this repo's real app, drive it through its user interface, capture evidence, and tear down, seeded with a feature map. Use on /create-verification-skill or "make a verify skill for this repo".
disable-model-invocation: true
---

# create-verification-skill

Write a skill inside the user's repo that lets a later agent start the real application, operate it the way a user does, and collect proof that a behavior works. The reader of the generated skill is an agent that opens it mid-task and knows nothing about the app. It works for any stack: web, terminal, desktop, HTTP service, mobile, or library.

A repo that already contains a verify skill with a feature map needs updating, not creation: switch to the [`maintain-verification-skill` skill](../maintain-verification-skill/SKILL.md).

Ask the user only for facts the code cannot tell you (a license key, which of two products matters more). Find everything else by reading the repo.

A worked example of a seeded feature map is in [references/example-feature-map/](references/example-feature-map/README.md).

## Phase A: study the repo

Answer five questions from the code and docs. Write the answers down; Phase B uses every one.

1. **Interface.** What does an end user operate: a browser UI, a terminal program, a desktop window, an HTTP API, a library call? If several, choose the primary one and record the others.
2. **Startup.** What command brings the app up on a dev machine? Prefer what the project documents (README quickstart, Makefile targets, package scripts). Record ports, environment variables, seed fixtures, and login requirements.
3. **Control.** How can an agent drive it from code? Start from tooling the repo already contains, such as browser test specs (Playwright, Cypress), `expect` or pseudo-terminal drivers, HTTP routes you can call with curl, or a debugging port. Only if nothing exists, fall back to a generic method: Chrome DevTools Protocol for browser and Electron apps, tmux or a PTY wrapper for terminal programs, plain HTTP for services.
4. **Evidence.** What can be captured: screenshots, accessibility-tree dumps, terminal recordings, HTTP response bodies, logs, exit codes, database rows?
5. **Isolation.** Can two copies run at once with separate ports, data folders, and profiles? If not, the generated skill must say so and must refuse to drive a copy the user is also using, because two drivers on one session can corrupt the user's state.

Also note the trust boundaries the app exposes (login, file upload, webhooks, admin routes). Feature files for those flows should include at least one hostile-input step, such as an unauthenticated request or an oversized upload, with the rejection as the expected result.

**Precondition.** If the project does not build or boot as checked out, fix that or report the exact failure before generating anything. Instructions written against a broken baseline encode broken steps. If startup fails only because of a missing file unrelated to the feature (an empty assets folder, an example settings file), the generated skill may create it, labeled as verification scaffolding, and remove it at teardown.

## Phase B: write the skill

Create a folder named `verify-<app>` in the project-level skills directory your agent reads (see `docs/agents/<agent>.md`). Its `SKILL.md` has frontmatter whose `name` equals the folder name and whose `description` names the app, the interface, and when to use it. Agents do not discover a skill without frontmatter.

Fill every section with facts from Phase A. Leave no placeholders.

**Startup.** The literal command for a verification instance, and the signal that it is ready (a specific log line, a prompt). Starting from an empty data folder must produce a working app, so include migrations and fixtures. Ready means a user could act. That is stricter than "the port answers": a database can report healthy before its init scripts finish. Include the shutdown command. For a terminal program that exits quickly there is no daemon; startup means building or installing once, and every drive gets a fresh PTY or tmux session.

**Health check.** One side-effect-free command that decides whether this instance is safe to drive: the process is alive, it is the expected build, this run owns the port, the session is logged in. Agents run it before driving and whenever behavior looks wrong.

**Driving.** Concrete steps using this repo's real selectors and commands. Use durable handles: accessible roles and names, `data-*` attributes, prompt text, URL routes. Never pixel coordinates or tab order.

**Evidence.** What to capture and the folder it goes in. Set the bar for proof:

- go through the path a real user takes, never private setters or test-only routes;
- record the user's action and the resulting state;
- check what the action changed outside the screen too, such as new files on disk, new database rows, or outgoing messages;
- allow mocks only at a boundary production already isolates (a payment sandbox, a mail catcher);
- if the only safe route is a dry-run or test switch, check by observation what it really avoids (filesystem, network, git refs). Some "dry run" modes still call the network or open a browser.

Evidence can capture tokens, cookies, or personal data. Say which fields to redact before saving, and keep the evidence folder out of git.

**Teardown.** Stop exactly the processes this run started, by PID or session name. Never kill by process name; that can kill the user's own instance. Remove instances and temporary state. Keep the evidence folder.

**Helpers.** Every script the skill ships is executable (`chmod +x`), and the skill shows how to call it with real arguments. No reader should have to read a helper's source to use it.

## Phase C: seed the feature map

Inside the generated skill, create `features/README.md` as an index, and one file per user-visible feature. Start with the three to five most important features, found from routes, CLI commands, menus, and docs.

Write each feature file around what the user experiences. It has exactly four `##` sections, in this order:

1. **Sub-features**, each tagged with a short id.
2. **Entry points**: every way a user reaches it (button, shortcut, menu, command, API route).
3. **Driving**: preconditions first, then steps that each pair one user action with its exact harness command and what a user would observe.
4. **Gotchas**: traps a later agent would hit.

If a journey needs a precondition the fixtures do not provide, the journey reports failure and the cause goes under Gotchas. Nobody weakens the journey until it passes. The feature map is the project's maintained record of what to verify, so a feature proven through one easy entry point is not complete while the map lists others.

The README sets shared baseline conditions, conventions, and proof rules for every feature file. See the example for one way to write it.

## Phase D: prove it

Run the generated skill once, end to end, before handing it over: startup, health check, drive one mapped feature, capture evidence, teardown. One feature is enough; later runs cover the rest. Then confirm the evidence still exists in its folder. If teardown deleted it, this phase failed.

Fix whatever breaks. Run the generated teardown after every failed attempt too, so abandoned attempts do not leave ports or processes behind. A generated skill nobody has run is a draft.

Proof gathered in a stand-in environment, for example a container instead of a clean VM or a local stack instead of the remote one, does not fully carry over. Write down each setup action that the stand-in did and the real target will not do. Those steps stay unproven until someone runs the skill on the real target.

## Phase E: hand over

Report the generated skill's path, the feature proven, and where its evidence is. Tell the user that the `maintain-verification-skill` skill keeps the feature map accurate over time. Offer a schedule for it only if they ask.

## Done when

The generated skill has frontmatter and no unfilled slots, ran once end to end on one feature, and its evidence survived teardown.
