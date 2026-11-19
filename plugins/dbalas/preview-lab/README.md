<p align="center">
  <img src="docs/logo.svg" width="72" height="72" alt="">
</p>

<h1 align="center">Preview Lab</h1>

<p align="center">
  <b>Review the UI your coding agent builds, screen by screen, and send the feedback straight back.</b><br>
  An <a href="https://agentskills.io">Agent Skill</a> for Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot and 60+ more.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-4f46e5" alt="MIT license">
  <img src="https://img.shields.io/badge/dependencies-0-4f46e5" alt="Zero dependencies">
  <img src="https://img.shields.io/badge/node-%E2%89%A518-4f46e5" alt="Node 18 or newer">
</p>

![A review round: screens grouped by flow, each with its tips](docs/grid.png)

Your agent captures the screens it changed and opens them in a review page styled like your project. You approve them or mark what to change, right on the screenshot. Press **Send**, and the agent gets short, structured feedback it can act on. Approved screens leave; the rest come back next round, with every change tagged.

## Quick start

```bash
npx skills add dbalas/preview-lab
```

Then ask your agent:

```
let me review the new checkout screens
```

That's it. The agent captures the screens, opens the lab in your browser, and waits for you to press **Send**.

## Why Preview Lab

- **Fast to review.** Screens are grouped by flow. `←` `→` to move, `A` to approve, `C` for changes, drag on a screenshot to mark the exact area.
- **Feedback agents can act on.** Statuses, areas in percent of the screenshot, comments and notes arrive as a few lines of markdown, not a wall of prose.
- **Rounds, not restarts.** Approved screens leave. After a code change only the screens whose pixels changed are tagged **Updated**. Past rounds stay one click away, read-only.
- **Expert tips (beta).** Ask for a *complete review* and the agent adds measured UX, UI, accessibility, responsive and consistency tips, pinned to the screenshot. You tick the ones to apply.
- **Built-in screenshots.** Viewports, dark mode, full pages, single components, and states reached by clicking or typing, using the Chrome, Edge or Chromium you already have.
- **Your brand, not ours.** The lab takes your colors, font, logo and language.
- **Works everywhere.** Local, remote or cloud sessions; light, dark or system theme; desktop or phone.
- **Leaves nothing behind.** Zero dependencies. One lab per checkout, kept in `~/.preview-lab/`, cleaned automatically.

<p>
  <img src="docs/detail-dark.png" alt="One screen with tips pinned to it, dark theme" width="72%">
  <img src="docs/mobile.png" alt="Reviewing on a phone" width="25%">
</p>

## Install

| Agent | Command |
|---|---|
| Any of the [60+ supported agents](https://github.com/vercel-labs/skills/blob/main/docs/agents.md) | `npx skills add dbalas/preview-lab` |
| Claude Code (plugin) | `/plugin marketplace add dbalas/preview-lab`, then `/plugin install preview-lab@preview-lab` |
| Gemini CLI (extension) | `gemini extensions install https://github.com/dbalas/preview-lab` |
| Anything else | Copy `skills/preview-lab/` into the agent's skills folder |

The repo also ships an [Agent Plugins](https://agent-plugins.org) manifest (`plugin.json`) for tools that install plugins from a repository. For agents without skills support, add one line to `AGENTS.md`: *"For UI reviews, follow `<path>/preview-lab/SKILL.md`."*

**Requirements:** Node 18+ (22+ for full-page, component and state screenshots), and Chrome, Edge or Chromium for built-in screenshots.

## Use

Talk to your agent in plain words, or call the skill directly (`/preview-lab` in most agents):

| You say | What happens |
|---|---|
| *let me review the onboarding screens* | Visual review: you give the feedback. |
| *complete review of the checkout* | The agent adds tips for every screen. |
| *only the settings modal, mobile and dark, in Spanish* | Anything you add overrides the defaults. |

## How a round works

```
 agent                          you
 ─────                          ───
 captures screens  ──────────▶  review in the lab
                                approve · changes · areas · notes
 reads the feedback ◀─────────  Send
 fixes the code
 next round        ──────────▶  only what changed comes back
```

The agent receives something like this:

```markdown
# Preview Lab feedback: shop · round 2 (complete)
1 approved · 1 changes · 0 unreviewed
**General:** Next round, show me the error state of payment.
**Approved:** Settings

## Order confirmed [done] — changes
- Area 1 (mobile @ x 8.5%, y 48.7%, 85.3×22.5%): Show item thumbnails
- Apply rec r1 [a11y/high]: The order number is 13px … raise it to 16px.
- Declined recs: r2, r3
```

## Remote and cloud sessions

The lab is served on `127.0.0.1:4747` of the machine the agent runs on. If your browser can't reach it, either forward that port, or let the agent run `pl.mjs export`: the round becomes one self-contained HTML file you open anywhere, and **Copy feedback** gives you the text to paste back into the chat.

## Commands

Your agent runs these; you never have to. They live in `skills/preview-lab/scripts/pl.mjs`.

| Command | What it does |
|---|---|
| `init [--in-project]` | Create or find this checkout's lab. |
| `brand [file]` | Read or set colors, font, logo, language and texts. |
| `add <items.json>` | Check, capture and add items. If anything fails, nothing changes. |
| `recapture [id…]` | Retake stored screenshots. Only changed screens are flagged. |
| `remove <id…>` | Remove items and their screenshots. |
| `serve [--detach]` | Serve the lab and print the feedback when it is sent. |
| `feedback` / `stop` | Print the last feedback, or stop the server. |
| `export [file]` | Save the round as one self-contained HTML file. |
| `round [--keep N]` | Archive the round, drop approved items, start the next one. |
| `contrast <fg> <bg>` | WCAG contrast ratio of two colors. |
| `upgrade` / `clean` / `reset` | Update the lab code, delete unused files, or start over. |

The agent's instructions are in [SKILL.md](skills/preview-lab/SKILL.md), the review guide in [complete-mode.md](skills/preview-lab/references/complete-mode.md), and the lab's design contract in [lab-spec.md](skills/preview-lab/references/lab-spec.md).

## Troubleshooting

| Problem | Fix |
|---|---|
| No screenshots, `NO_BROWSER` | Install Chrome, Edge or Chromium, or set `PREVIEW_LAB_CHROME` to its path. |
| Full-page or component shots fail | They need Node 22+. Older Node still takes viewport shots. |
| The lab page doesn't open | Open the `PREVIEW_LAB_URL` the agent printed. In a remote session, forward port 4747 or ask for an export. |
| **Send** says the agent is unreachable | The feedback was copied: paste it into the chat. |
| Labs in an odd place | Set `PREVIEW_LAB_HOME`, or ask for the lab inside the project. |

## Develop

No install step. Run the tests (they also open the lab in a real browser when one is installed):

```bash
npm test
```

## License

MIT · Made with ♥ by [dbalas](https://github.com/dbalas)
