# Jetformat for Claude, ChatGPT, and Codex

Jetformat converts Word, Excel, and PowerPoint files to PDF, turns PDF back into Word, extracts text, validates files, and merges, splits, and renders PDFs. This plugin adds one skill that tells the agent to call the local `jetformat` command line tool instead of unzipping Office files or writing PDF bytes itself.

## Install the CLI first

```bash
npm install -g jetformat
# or
brew install jetformat/tap/jetformat
jetformat login
```

## Install the plugin

Claude Code:

```bash
claude plugin marketplace add jetformat/jetformat-agent
claude plugin install jetformat@jetformat
```

Codex:

```bash
codex plugin marketplace add jetformat/jetformat-agent
```

## What it runs and sends

The skill runs only the `jetformat` binary on your machine. Files never leave the machine. The CLI contacts jetformat.com to sign in, to check and deduct credits for paid commands, and to send one anonymous usage ping per command (command name, file type, duration, result, version, OS). It never sends paths, file names, or contents. Turn the ping off with `jetformat telemetry off`.

Reading files is free. Converting, rendering, and writing files use credits; see https://jetformat.com/pricing.

## License

The skill text in this repository is MIT licensed. The Jetformat CLI is closed-source and has its own terms: https://jetformat.com/terms
