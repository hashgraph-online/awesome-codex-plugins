#!/usr/bin/env node
import { spawn } from "node:child_process";
import readline from "node:readline";
import {
  credentialStatus,
  DEFAULT_COOLIFY_BASE_URL,
  normalizeBaseUrl,
  saveCredentials
} from "../src/credentials.js";

const args = new Set(process.argv.slice(2));
const positional = process.argv.slice(2).filter((arg) => !arg.startsWith("--"));

function usage() {
  console.log(`Coolify Codex Plugin setup

Usage:
  npm run setup
  npm run setup -- --save
  npm run setup -- --no-open
  npm run setup -- https://coolify.example.com

This helper opens the Coolify API token page and can save a local plugin
connection. Coolify does not currently document a browser OAuth flow for API
clients, so the token still has to be created in Coolify.
Without a URL argument, setup uses Coolify Cloud (${DEFAULT_COOLIFY_BASE_URL}).`);
}

function browserCommand(url) {
  if (process.platform === "darwin") {
    return { command: "open", args: [url] };
  }
  if (process.platform === "win32") {
    return { command: "cmd", args: ["/c", "start", "", url] };
  }
  return { command: "xdg-open", args: [url] };
}

function openBrowser(url) {
  const { command, args: commandArgs } = browserCommand(url);
  const child = spawn(command, commandArgs, {
    detached: true,
    stdio: "ignore"
  });
  child.unref();
}

if (args.has("--help") || args.has("-h")) {
  usage();
  process.exit(0);
}

const current = credentialStatus();
const rawBaseUrl = positional[0] || current.baseUrl || DEFAULT_COOLIFY_BASE_URL;
const baseUrl = normalizeBaseUrl(rawBaseUrl).rootBase;
const tokenUrl = `${baseUrl}/security/api-tokens`;
const apiSettingsUrl = `${baseUrl}/settings/advanced`;

console.log("\nCoolify setup URLs:");
console.log(`  API token page: ${tokenUrl}`);
console.log(`  API settings:   ${apiSettingsUrl}`);

if (!args.has("--no-open")) {
  openBrowser(tokenUrl);
  console.log("\nOpened the API token page in your browser.");
}

if (args.has("--save")) {
  const apiToken = await askHidden("\nPaste the scoped Coolify API token: ");
  const status = saveCredentials({ baseUrl, apiToken });
  console.log(`\nSaved the Coolify connection for ${status.baseUrl}.`);
  console.log(`Token storage: ${status.storage || status.tokenSource || "local"}`);
  console.log(`Config path: ${status.configPath}`);
} else {
  console.log(`
After creating a scoped token, save it by asking Codex to configure Coolify, or run:

  npm run setup -- --save "${baseUrl}"

The plugin stores the token in the operating system credential store when
available, otherwise in a local config file with owner-only permissions.
Environment variables remain supported for automation, but are not required
for normal use.

Use the least-privileged token that can perform the work you want Codex to do.
`);
}

function askHidden(prompt) {
  return new Promise((resolveInput) => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      terminal: true
    });

    const stdin = process.stdin;
    const wasRaw = stdin.isRaw;
    if (stdin.isTTY) {
      stdin.setRawMode(true);
    }
    process.stdout.write(prompt);

    let value = "";
    stdin.on("data", onData);

    function onData(buffer) {
      const text = buffer.toString("utf8");
      for (const char of text) {
        if (char === "\n" || char === "\r" || char === "\u0004") {
          cleanup();
          process.stdout.write("\n");
          resolveInput(value.trim());
          return;
        }
        if (char === "\u0003") {
          cleanup();
          process.stdout.write("\n");
          process.exit(130);
        }
        if (char === "\b" || char === "\u007f") {
          value = value.slice(0, -1);
          continue;
        }
        value += char;
      }
    }

    function cleanup() {
      stdin.off("data", onData);
      if (stdin.isTTY) {
        stdin.setRawMode(wasRaw);
      }
      rl.close();
    }
  });
}
