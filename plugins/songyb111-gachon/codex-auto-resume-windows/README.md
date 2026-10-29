<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-motion-dark.png">
    <img src="assets/logo-motion.png" alt="Codex Auto Resume" width="96">
  </picture>
</p>

<h1 align="center">Codex Auto Resume</h1>

<p align="center"><b>Automatically resume the exact same Codex task on Windows after a usage limit resets.</b></p>

<p align="center">
<a href="https://github.com/songyb111-gachon/codex-auto-resume-windows/actions/workflows/test.yml"><img src="https://github.com/songyb111-gachon/codex-auto-resume-windows/actions/workflows/test.yml/badge.svg" alt="tests"></a>
<a href="https://github.com/songyb111-gachon/codex-auto-resume-windows/releases/latest"><img src="https://img.shields.io/github/v/release/songyb111-gachon/codex-auto-resume-windows?label=release" alt="latest release"></a>
<a href="#install"><img src="https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-0078d4" alt="platform: Windows 10/11"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="license: MIT"></a>
<a href="https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/GUIDE.md#languages"><img src="https://img.shields.io/badge/languages-16-0891b2" alt="languages: 16"></a>
</p>

<p align="center"><sub>🇰🇷 <a href="https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/ko/README.md">한국어 README</a> · The app speaks sixteen languages: English · 한국어 · 日本語 · 简体中文 · 繁體中文 · Español · Deutsch · Français · Português (Brasil) · Русский · Italiano · Türkçe · Polski · Українська · Tiếng Việt · Bahasa Indonesia</sub></p>

<p align="center">
<img src="docs/images/readme-motion.png" alt="The Codex Auto Resume Dashboard at work, drawn by the product's own code from synthetic sample data: the Overview with two recoveries waiting; the pointer opens Pending, right-clicks a waiting task to open its menu and closes it, then opens History, Statistics and Diagnostics, opens Settings and scrolls; it changes the interface language to Korean, saves, and the window opens again in Korean" width="750"><br>
<sub>The exact conversation, by UUID · the reset time Codex reports · fails closed · no telemetry · standard and advanced editions</sub>
</p>

Codex stops mid-task and tells you to try again at 6:34 AM. You are asleep at 6:34 AM, and in
the morning the task is exactly where it stopped.

**Typical use:** the Codex desktop app on Windows, left working overnight or on a long task, hits
a usage limit - the "5-hour limit", as many people call it, or the weekly one - and should carry
on in the same conversation once the limit resets.

Codex Auto Resume waits for the reset time Codex itself reports, not a fixed number of hours,
checks that continuing is genuinely safe, and sends one continuation message to **that exact
conversation** through the official `codex queue` command - found by its thread UUID, never
guessed with `--last`, and never by typing into the Codex window.

It also recovers temporary rate limits (HTTP 429), network failures, timeouts, server errors and
interrupted streams - but only a failure it can name, and only where it is safe to retry.
**It deliberately does not retry everything**, and it fails closed: when unsure it waits rather
than sends, and never resends a message that may already have been delivered.

This page is the short version. **[The full guide](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/GUIDE.md)** has everything else: every
setting, the notification, the command line, the safety model and privacy in full.

|  |  |
| --- | --- |
| **Recovers** | Codex usage limits, and - when Codex records a specific error for them - rate limits (HTTP 429), network failures, timeouts, temporary server errors (5xx) and dropped response streams |
| **Never touches** | user cancellation · permission · approval · content policy · invalid requests · context length · permanent authentication failures · anything unclassified |
| **Identity** | the exact conversation UUID only — never `--last`, never "the most recent one", never a title or a folder name |
| **Configure it** | the Dashboard from the Start Menu, a settings panel inside Codex, or the command line |
| **Languages** | English · 한국어 · 日本語 · 简体中文 · 繁體中文 · Español · Deutsch · Français · Português (Brasil) · Русский · Italiano · Türkçe · Polski · Українська · Tiếng Việt · Bahasa Indonesia |
| **Privacy** | no telemetry, no analytics, no automatic update check. Setting it up from Codex downloads the release from GitHub, and *Check for updates* asks GitHub which release is newest, and reads its list of releases on api.github.com for a newer pre-release, only when you press it - and it then also refreshes the Codex compatibility data from raw.githubusercontent.com, sending nothing about your machine; *Install another version...* reads that whole list there when you open it and again when you confirm a version, and downloads only the version you confirmed. The watcher has no network code; the usage check and the resumed turn go to OpenAI through Codex, as Codex's traffic always does |

> [!IMPORTANT]
> **One honest limitation, up front.** Codex has to currently have that conversation open for a
> recovery to be delivered. If the app restarted since, open the conversation once and recovery
> continues on its own. [Why](#please-read-this-limitation-first). In the advanced edition, a capability you
> turn on can [run it here while Codex is closed](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/EDITIONS.md#run-a-conversation-here-while-codex-is-closed) instead.

## Install

**Windows 10/11. No Python needed. No administrator rights.**

It comes in two editions, of which you install one. **Standard**, the default and the one the routes
below install, keeps every one of the project's standards - every promise on this page among them.
**Advanced** adds capabilities that each depart from at least one of those standards on purpose, every
one off until you turn it on in the Dashboard's **Advanced features** page; take the files with
`Advanced` in their name, or ask Codex to set up the advanced edition. An update stays in your edition,
and installing the other one over it switches, keeping your settings and everything waiting.
[docs/EDITIONS.md](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/EDITIONS.md) says what each capability does and risks.

### With the setup program (recommended)

Download `CodexAutoResume-Setup-vX.Y.Z.exe` - the link is at the top of every
[release page](https://github.com/songyb111-gachon/codex-auto-resume-windows/releases/latest) - and double-click it.
A setup window installs it for your Windows account only, with nothing to unzip. Run over an older version it
shows what is new before it updates, then restarts the watcher and reopens any Dashboard you had open; run over
the same version it offers **Repair** or **Remove**. It is not code-signed: if Windows says
*Windows protected your PC*, choose **More info**, then **Run anyway**.
[docs/VERIFY.md](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/VERIFY.md#before-you-run-a-downloaded-setup-program)
shows how to check it first.

<p align="center"><img src="docs/images/install-motion.png" alt="The setup window installing Codex Auto Resume, drawn by the window's own code: the Welcome page, Next, the choices before it installs, Install, the steps of the installation one after another as the bar fills, and the finished page with the watcher running and Open the Dashboard ticked" width="450"></p>

<details>
<summary><b>From Codex</b></summary>

Add the plugin, then ask Codex to **set up auto resume**.

```
codex plugin marketplace add songyb111-gachon/codex-auto-resume-windows
codex plugin add codex-auto-resume@codex-auto-resume-windows
```

The plugin's setup script downloads the matching release from this repository over HTTPS, checks
its SHA-256 against the digest recorded for that version in
[`scripts/release.json`](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/scripts/release.json),
and installs it for your Windows account only.

</details>

<details>
<summary><b>From the release archive</b></summary>

1. Download `CodexAutoResume-vX.Y.Z-win-x64.zip` from the
   [latest release](https://github.com/songyb111-gachon/codex-auto-resume-windows/releases/latest).
2. Check it before you extract it, in PowerShell, in the folder you downloaded it to:

   ```powershell
   (Get-FileHash .\CodexAutoResume-vX.Y.Z-win-x64.zip -Algorithm SHA256).Hash
   ```

   The value must match the `.sha256` file published beside the archive and the digest for that
   version in [`scripts/release.json`](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/scripts/release.json).
   [docs/VERIFY.md](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/VERIFY.md) has the full check.
3. Extract it and run `Install.cmd`.

</details>

### Either way

Every route ends at the same installation, by default in `%USERPROFILE%\.codex-auto-resume`.
Running any of them again upgrades or repairs it, and keeps anything already waiting to resume.

## First steps

- There is nothing to set up: the recommended settings are on from the start.
- When a task stops, a notification names it, as a card beside the notification area (or Windows'
  own notification where a card must not show). Doing nothing resumes it,
  **Don't resume** cancels only that one, and **Open Dashboard** shows what is waiting.
- The notification-area icon shows what the watcher is doing; click it to see what is waiting or
  to pause recovery.
- Change anything from **Start Menu → Codex Auto Resume**, or just ask Codex: "show auto resume
  status", "show pending auto resumes", "open auto resume settings", "turn auto resume off".

## What it looks like

The status light breathes wherever it is shown - on the card, in the Dashboard, in the panel inside
Codex and on the notification-area icon - and the pictures below breathe with it.

<p align="center">
<img src="docs/images/notification-card-motion.png" alt="The notification card as the product shows it, drawn by its own code from sample data: example-project, Codex usage limit reached, this task will resume at 08:42; the card fades out and rises in again beside the notification area" width="388" align="top">
<img src="docs/images/tray-popup-motion.png" alt="The notification-area popup as the product shows it, drawn by its own code from sample data: waiting, with the next check in a minute and a half and three waiting tasks, each with its kind of interruption, when it is next checked and its Auto-resume switch, and Pause recovery and Open Dashboard buttons; its status light breathes, the first task's Auto-resume switch is turned off and on again, and the popup closes and opens again" width="360" align="top"><br>
<sub>Left: the notification card, as the product draws it · right: what opens when you click the notification-area icon</sub>
</p>

<details>
<summary><b>The Dashboard and the icon, still</b></summary>

<p align="center">
<img src="docs/images/notification-card.png" alt="The notification card in the light theme: Codex Auto Resume with a cyan status light and a Usage limit chip, the task example-project, the line Codex usage limit reached. This task will resume at 08:42., the conversation's exact identifier, and the buttons Don't resume and Open Dashboard" width="388">
</p>

The Dashboard from the Start Menu, drawn from synthetic sample data (the conversations in these
pictures are examples, not anybody's work):

<img src="docs/images/dashboard-overview.png" alt="The Codex Auto Resume Dashboard overview: automatic recovery on, the watcher running and the Codex engine compatible, two recoveries waiting with the next check in a minute and a half, the last seven days' interruptions, continuations sent, recoveries and success rate, and the four most recently finished recoveries" width="680">

<img src="docs/images/dashboard-pending.png" alt="The Pending page of the Dashboard: two conversations waiting, one for the usage reset and one with a retry scheduled, each with a state chip and an Auto-resume switch, the Why it is waiting checklist for the selected task, and Retry now, Cancel, Timeline, Turn off for this conversation and Cancel all buttons" width="680">

<img src="docs/images/settings-window.png" alt="The Continuation message section of the Dashboard's Settings page: the continuation language, the four message styles with Standard selected, and a Preview of the message sent for a usage limit" width="680">

The panel inside Codex (folded here, it is used less than the Dashboard), rendered from the exact resource the plugin serves, not a photograph of the Codex window:

<img src="docs/images/settings-panel.png" alt="The Codex Auto Resume panel: a status card saying two recoveries are waiting, the two waiting conversations each with an Auto-resume switch, the interface language, the recovered failure categories, Limits and Notifications folded away, the continuation language and message style, and a Preview of the Standard message for a usage limit" width="388">

The notification-area icon, moving:

<img src="docs/images/icon-motion.png" alt="The notification-area icon's motion, drawn from the icon's own frames, on a light taskbar. From the left: watching, whose bright head breathes and then sweeps clockwise along the ring's white stroke and back, at full brightness; recovering, sweeping out and back all the time; needing attention, amber, breathing slowly in its place; failed, red, sweeping out and back twice as quickly as recovering and blinking as it goes; paused, grey and still" width="360">

</details>

[The full guide](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/GUIDE.md#what-it-looks-like) shows every part in every theme and language.

## Please read this limitation first

This tool can only auto-resume a thread that the Windows ChatGPT/Codex desktop app **currently has
loaded**. After the app restarts, a thread is `notLoaded`, and there is no verified, supported way to
wake an unloaded thread programmatically. Codex may still deliver such a message later, when the
thread next loads. So this tool queues only for a thread it has just confirmed is loaded, and an
unloaded thread is resumed **only after you open that conversation in the app yourself**. It will
not use GUI automation, will not force the conversation open, and will not queue a message on the
off chance. [The full guide](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/GUIDE.md#please-read-this-limitation-first) has the measurement
behind it. This is the standard edition's rule. The advanced edition can, once you turn it on, run that
turn itself while the Codex app is closed, or leave the continuation in Codex's queue for when you open the
conversation - both described in [docs/EDITIONS.md](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/EDITIONS.md#run-a-conversation-here-while-codex-is-closed).

## Safety and privacy

It resumes only the exact conversation that stopped, by its UUID, and only for a failure it can name;
anything unclassified is left alone, and whenever it cannot be sure, it waits rather than sends. It
reads Codex's own state read-only, and never resends a message that may already have been delivered.
The watcher itself has no network code and nothing is sent to this project: the usage check and the
resumed turn go to OpenAI through Codex, and setting it up from Codex downloads the release from
GitHub. [PRIVACY.md](docs/PRIVACY.md) says what is read, stored and sent, and [SECURITY.md](docs/SECURITY.md)
gives the threat model and how to report a vulnerability.

## Requirements

- Windows 10/11 and the official Windows ChatGPT/Codex desktop app, running.
- No Python for either install route; the installation brings its own runtime. Python 3.13 or newer
  is needed only to run it from a source checkout.

## Uninstall

Remove it from Windows **Settings > Apps**, run the setup program again and choose **Remove**, run
`Uninstall.cmd` from a release archive, or ask Codex to uninstall auto resume. By default your
settings and pending recoveries are kept, so reinstalling picks them up; `Uninstall.cmd -Purge`
deletes them too. It removes only what it can prove is its own: directories it can show it owns (by
its provenance marker), and Windows registrations that belong to this installation.

## Learn more

| | |
| --- | --- |
| **[The full guide](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/GUIDE.md)** | Everything above in full, and every setting, the notification, the command line, the safety model, privacy and testing. |
| [docs/VERIFY.md](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/VERIFY.md) | How to check a downloaded archive is the one this project published, and how to rebuild a release. |
| [docs/FEATURE_MATRIX.md](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/FEATURE_MATRIX.md) | Every capability this product claims, beside the evidence it has actually earned. |
| [docs/PLUGIN.md](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/PLUGIN.md) | The Codex plugin layer: what setup fetches and checks, updates and removal. |
| [docs/COMPARISON.md](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/COMPARISON.md) | Other projects in this space, and what each does better than this one. |
| [docs/ROADMAP.md](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/ROADMAP.md) | Where the project is heading, release by release: a planned direction, not a promise. |
| [docs/EDITIONS.md](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/EDITIONS.md) | The standard and the advanced edition: what each is, what each advanced capability does and risks, and how to choose and switch. |
| [docs/STANDARDS.md](https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/STANDARDS.md) | Every rule the product keeps, by id, with how each is held and the tests that hold it. |
| [PRIVACY.md](docs/PRIVACY.md) | What is read, what is stored, and what is sent anywhere. |
| [SECURITY.md](docs/SECURITY.md) | The threat model and how to report a vulnerability. |
| [SUPPORT.md](docs/SUPPORT.md) | Where to report each kind of problem, and what not to paste into a public issue. |
| [CONTRIBUTING.md](docs/CONTRIBUTING.md) | Tests, the release build, and the safety properties a change has to keep. |
| [CHANGELOG.md](docs/CHANGELOG.md) | What each release changed. |
| [CONTRIBUTORS.md](docs/CONTRIBUTORS.md) | Who built it, the tools that helped, and the people who reported, suggested and tested. |
| [codex-compat-reporter](https://github.com/songyb111-gachon/codex-compat-reporter) | A separate tool you can run to report how this product behaved on your machine, with your Codex version. It writes one file of counts, states and times - no conversation text, no identifiers, no paths - which you read before you send it. Such a report is counted under **Reported**, a grade of its own that never raises a version to verified or checked. |

## Credits and license

Built by **songyb111-gachon** with the assistance of two AI development tools, OpenAI Codex and
Anthropic Claude Code; [CONTRIBUTORS.md](docs/CONTRIBUTORS.md) has the full breakdown. Thanks to everyone who
reported a problem, suggested a feature, tested a fix or sent one - [@cervinho](https://github.com/cervinho), [@barkshah2002-pixel](https://github.com/barkshah2002-pixel), [@ZionZhang42](https://github.com/ZionZhang42), [@aca22jy](https://github.com/aca22jy), [@Hunweibyn](https://github.com/Hunweibyn), [@Zephreo](https://github.com/Zephreo), [@Kdevaulo](https://github.com/Kdevaulo), [@weng-wen-jun](https://github.com/weng-wen-jun) and [@kano0222](https://github.com/kano0222) among them;
[CONTRIBUTORS.md](docs/CONTRIBUTORS.md) says what each of them helped with, and the [changelog](docs/CHANGELOG.md)
names them beside the changes it led to.

MIT. See [LICENSE](LICENSE).
