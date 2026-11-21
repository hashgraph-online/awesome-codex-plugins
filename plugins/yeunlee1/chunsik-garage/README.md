# Chunsik's Garage

![Chunsik the otter and Chunsam the axolotl holding a big wrench together](https://raw.githubusercontent.com/yeunlee1/chunsik-garage/develop/docs/images/hero.png)

AQ checkup for Claude Code and Codex, with Gemini CLI records and ChatGPT and Claude.ai chats counted too. A program on your own PC reads your local Claude Code, Codex, and Gemini CLI records and the chat export files you add, scores how well you set up and use these AI tools, and writes a one-page report.

![AQ report page made from synthetic records](https://raw.githubusercontent.com/yeunlee1/chunsik-garage/develop/docs/images/report-en.png)

## Install

Node.js 22 or later is required. The `#main` and `@main` parts install the released version; without them you get the development branch.

| Tool | Install | Run |
|---|---|---|
| Claude Code | `claude plugin marketplace add yeunlee1/chunsik-garage#main`, then `claude plugin install chunsik-garage@chunsik-garage` | Say "Run an AQ checkup", or use `/chunsik-garage:aq` |
| Codex | `codex plugin marketplace add yeunlee1/chunsik-garage@main`, then `codex plugin add chunsik-garage@chunsik-garage` | Say "Run an AQ checkup", or pick the skill in `/skills` |

To update, run `claude plugin marketplace update chunsik-garage`, then `claude plugin update chunsik-garage@chunsik-garage` for Claude Code, and start a new session. For Codex, run `codex plugin marketplace upgrade chunsik-garage` and restart Codex.

## What it does

- **Checkup.** Scores four axes from your records and settings, opens the report page in your browser, and gives a short summary in the terminal. Every item shows how it was measured. The report shows how to reach the next grade step by step (what to change, the value now and the target) and explains how the score and the grades are worked out. It also points out API keys or tokens written as they are in your settings.
- **Tune-up.** Turns off skills, plugins, and MCP servers you have not used for a while. It changes only the items you approve, writes a record first, and can undo each change.
- **Deep checkup.** Reads the instruction files you pick and points out lines that overlap, conflict, or would be better moved. The score does not change.
- **Session start notices (Claude Code).** One line when a session starts, if 7 days have passed since the last checkup or something new is installed. Ask to turn them on.
- **Leaving an item as you chose.** If you keep a setting on purpose, such as a high reasoning effort, ask to leave that item as it is. It still counts in the score and leaves what to fix first and the next-grade steps.
- **AQ badge.** A small picture with your AQ and grade for your README or GitHub profile, made on your PC from your latest checkup. Ask for an AQ badge.
- **Web chats.** Download your data export from ChatGPT (Settings, Data controls, Export data) or Claude.ai (Settings, Privacy, Export data) and give the AI the path of the zip (or of the folder you unzipped it to), for example "Add my ChatGPT export: C:\Users\me\Downloads\export.zip". From then on the checkup also counts on which days you used those chats and how many requests you sent. It keeps only where the file is, so if you delete the file, it drops out.

## Privacy

The program and the report page make no network requests. What the program prints goes to the AI in your current session. For a checkup, that is the scores, the counts, the paths of the report and result files, and the names of what to fix, such as MCP servers that failed to connect and where API keys are written. For a tune-up, it is also the names of what to tune up, the paths of the settings files, and the keys and values it proposes to change. The values of API keys, your conversations, and the text of your instructions are not sent. If you ask for a deep checkup, the AI reads only the instruction files you pick.

The checkup looks for API keys or tokens written as they are in your MCP settings and in the `env` of your Claude Code settings. It looks at a value only to tell its shape, and never shows or saves it. The report page and the AI receive where they are (the server, the field, and the key name) so you can move them, never the values.

If you add a ChatGPT or Claude.ai export, the program reads it on your PC and keeps only dates and counts (and model names when the export has them). It does not keep a copy of the export (a compressed zip inside the export is unpacked to a temporary folder only while it is read, then deleted), and conversation text, titles, and attachment names go nowhere: not to the cache, the report, or the AI.

The report file contains the names of your skills and project folders. Share the score card instead of the file.

What runs on your PC: the skill runs `skills/aq/scripts/aq.mjs` with Node.js, and Claude Code runs `hooks/session-start.mjs` when a session starts. The hook stays quiet unless you turned the notices on. Neither program makes network requests.

## Supported

- Node.js 22 or later. Tested on 22 and 24.
- Built and tested on Windows 11. macOS and Linux are covered only by tests with temporary home folders.
- Made for Claude Code and Codex on your own PC. The checkup reads the records these tools keep on your PC. ChatGPT and Claude.ai chats count only through the export file you add, and it is not made for Cowork.
- Claude Code record formats checked on 2.1.220 to 2.1.322, and the settings a tune-up changes on 2.1.220 to 2.1.325. Codex record formats checked on records of 0.166.0 (and the older format of 0.140 to 0.142), and up to 0.169.0 by comparing the public source of the record shapes the checkup reads.
- Gemini CLI records and settings are read when they are on your PC. Run the checkup from Claude Code or Codex; there is no Gemini CLI extension. The record formats were checked only against the public source of Gemini CLI 0.68.0, not yet on real records, and the records do not say which version wrote them. For Gemini CLI the checkup does not measure skills, unused MCP servers, MCP connection failures and hooks, reasoning effort, or compaction, and it does not tune anything up. Settings of folders you have not trusted in Gemini CLI are left out, as Gemini CLI does.
- ChatGPT and Claude.ai exports are read when you add them: the zip from the service, the folder you unzipped it to, or the `conversations.json` in it. Split files such as `conversations-000.json` are read too. The formats were checked against public tools that read these exports, not yet on a real export. The checkup does not measure settings or token use for web chats, so they count only toward the days of use and the requests per day, and an export covers chats up to the day it was made. If only web chats were used in the last 30 days, no AQ is given.

## What it leaves and how to remove it

Everything lives in `~/.chunsik-garage/`: the cache, the reports, the score history, the state, the notice markers, the tune-up records, the badge, and the list of web chat exports you added (only where each file is). Removing the plugin does not remove this folder.

The only exception is a checkup run without saving. Its report page and result file (`chunsik-garage-report-<time>.html`, `chunsik-garage-result-<time>.json`) go to your OS temp folder, and this tool does not delete them. The result file lists the names of your skills, MCP servers, and projects, so delete it yourself when you no longer need it.

- Ask "where does the AQ checkup keep its files" to see the folder and its size.
- Ask to clean up: the cache and older reports are removed, and the latest report stays.
- Ask to remove everything: the history, the state, the tune-up records, and the list of added exports are removed too. The export files themselves stay. After that, tune-ups can no longer be undone with this tool.
- Cleaning checks each path right before deleting it, but it cannot stop another program that swaps a folder inside `~/.chunsik-garage/` for a link at that very moment, which could delete files outside. Leave that folder alone while it is being cleaned.

## Using it in the Codex sandbox

In Codex's default sandbox (workspace-write with approval on request), writing to `~/.chunsik-garage/` needs your approval. To allow it for good, add the folder to `writable_roots` in `~/.codex/config.toml`:

```toml
[sandbox_workspace_write]
writable_roots = ["/absolute/path/to/your/home/.chunsik-garage"]
```

Without approval the checkup still runs without saving (no cache, no history). A tune-up always needs permission to write the settings file it changes.

## What a tune-up cannot prevent

- The lock works only among this tool's own runs. While a tune-up runs, do not install plugins or change settings in other Claude Code or Codex sessions. A change another program writes in the instant between the last check and the file replacement can be overwritten. The tune-up record still lets you undo what this tool changed.
- Open Claude Code sessions may not pick up a change. Check in a new session. Codex needs a restart.

## License

The code is MIT licensed (`LICENSE`). The character art in `skills/aq/assets/` is not covered by the MIT license; see `skills/aq/assets/ART-LICENSE.md`. You may share the art as it appears in the cards, result pages, and screenshots that this tool makes. You may not take the art out of them and use it elsewhere.

[한국어](README.ko.md)
