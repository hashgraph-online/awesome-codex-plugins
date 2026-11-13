# phonedriver plugin

This plugin lets an agent see and operate Android phones, Android emulators, the iOS Simulator and iPhones. It adds two things: the phonedriver MCP server and the skill that tells the agent how to use it.

## Install

Claude Code:

```sh
claude plugin marketplace add hridaya423/phonedriver
claude plugin install phonedriver@phonedriver
```

Codex:

```sh
codex plugin marketplace add hridaya423/phonedriver
codex plugin add phonedriver@phonedriver
```

If you already added the server with `mcp add`, remove it first. If you keep both, the tools are listed twice.

## What it needs

- Node.js 18 or later. The plugin starts the server with `npx -y phonedriver@<version> mcp`, at the version the plugin was released with. That downloads the phonedriver binary for your system from GitHub Releases on its first run.
- A device: an Android emulator, an Android phone with USB debugging on, or the iOS Simulator. iOS needs a Mac with Xcode.

## Use

Ask for a job that needs a phone, for example "Open Settings on the phone and turn on dark mode." The agent reads the screen as a numbered text list and taps by number.

## Safety

- A tap that pays, orders, transfers money or deletes an account is held until you approve it.
- phonedriver sends no telemetry. It connects to the device and, for iOS developer disk images, to Apple.
- The server runs on your computer with your user's rights. The `shell` tool runs commands on the Android device over adb. For the iOS Simulator it runs `simctl` commands.

Full documentation: https://phonedriver.dev. Source and issues: https://github.com/hridaya423/phonedriver. License: AGPL-3.0-only.
