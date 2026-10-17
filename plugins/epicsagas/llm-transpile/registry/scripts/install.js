#!/usr/bin/env node
// llm-transpile plugin bootstrap
// Runs on SessionStart via hooks.json.
// Uses only Node.js built-ins — no npm install needed.

"use strict";

const { spawnSync } = require("child_process");
const { createWriteStream, chmodSync, readFileSync } = require("fs");
const { join } = require("path");
const https = require("https");
const os = require("os");

const REPO = "epicsagas/llm-transpile";
const BINARY = "transpile";
const CARGO_PKG = "llm-transpile";
const INSTALLER_SH = `https://github.com/${REPO}/releases/latest/download/install.sh`;
const INSTALLER_PS1 = `https://github.com/${REPO}/releases/latest/download/install.ps1`;

function log(msg) {
  process.stderr.write(`[transpile plugin] ${msg}\n`);
}

function hasCommand(cmd) {
  const r = spawnSync(cmd, ["--version"], { stdio: "pipe", shell: false });
  return r.status === 0;
}

function getBinaryVersion() {
  try {
    const r = spawnSync(BINARY, ["--version"], { stdio: "pipe", shell: false });
    if (r.status === 0) {
      const output = r.stdout.toString().trim();
      const match = output.match(/(\d+\.\d+\.\d+)/);
      return match ? match[1] : null;
    }
  } catch (_) {}
  return null;
}

function getPluginVersion() {
  const root = process.env.CLAUDE_PLUGIN_ROOT || process.env.PLUGIN_ROOT || "";
  const candidates = [
    join(root, ".claude-plugin", "plugin.json"),
    join(root, ".codex-plugin", "plugin.json"),
  ];
  for (const manifestPath of candidates) {
    try {
      const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
      return manifest.version || null;
    } catch (_) {}
  }
  return null;
}

function semverGt(a, b) {
  const pa = a.split(".").map(Number);
  const pb = b.split(".").map(Number);
  for (let i = 0; i < 3; i++) {
    if (pa[i] > pb[i]) return true;
    if (pa[i] < pb[i]) return false;
  }
  return false;
}

function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = createWriteStream(dest);
    const follow = (u) => {
      https.get(u, (res) => {
        if (res.statusCode === 301 || res.statusCode === 302) {
          follow(res.headers.location);
          res.resume();
          return;
        }
        if (res.statusCode !== 200) {
          reject(new Error(`HTTP ${res.statusCode} for ${u}`));
          return;
        }
        res.pipe(file);
        file.on("finish", () => file.close(resolve));
      }).on("error", reject);
    };
    follow(url);
  });
}

async function install() {
  const platform = os.platform();

  // macOS: prefer Homebrew if available
  if (platform === "darwin") {
    const hasBrew = spawnSync("brew", ["--version"], { stdio: "pipe", shell: false }).status === 0;
    if (hasBrew) {
      log("Homebrew detected — installing via brew tap...");
      const r = spawnSync("brew", ["install", "epicsagas/tap/llm-transpile"], {
        stdio: "inherit",
        shell: false,
      });
      if (r.status === 0) return;
      log("Brew install failed, trying next method...");
    }
  }

  // All platforms: try cargo-binstall (pre-built binary, fast)
  const hasBinstall = spawnSync("cargo", ["binstall", "--version"], { stdio: "pipe", shell: false }).status === 0;
  if (hasBinstall) {
    log("cargo-binstall detected — installing...");
    const r = spawnSync("cargo", ["binstall", CARGO_PKG, "--no-confirm"], {
      stdio: "inherit",
      shell: false,
    });
    if (r.status === 0) return;
    log("cargo-binstall failed, falling back to installer script...");
  }

  // Fallback: download platform-specific installer
  if (platform === "win32") {
    const tmp = join(os.tmpdir(), "transpile-installer.ps1");
    log("Downloading Windows installer...");
    await downloadFile(INSTALLER_PS1, tmp);
    const r = spawnSync(
      "powershell",
      ["-ExecutionPolicy", "Bypass", "-File", tmp],
      { stdio: "inherit" }
    );
    if (r.status !== 0) throw new Error("PowerShell installer failed");
  } else {
    const tmp = join(os.tmpdir(), "transpile-installer.sh");
    log("Downloading installer...");
    await downloadFile(INSTALLER_SH, tmp);
    chmodSync(tmp, 0o755);
    const r = spawnSync("sh", [tmp], { stdio: "inherit" });
    if (r.status !== 0) throw new Error("Shell installer failed");
  }
}

async function main() {
  const pluginVersion = getPluginVersion();
  const isPlugin = !!(process.env.CLAUDE_PLUGIN_ROOT || process.env.PLUGIN_ROOT);

  // 1. Binary not found — fresh install
  if (!hasCommand(BINARY)) {
    log(`${BINARY} not found — installing...`);
    try {
      await install();
    } catch (e) {
      log(`Install failed: ${e.message}`);
      log(`Install manually: https://github.com/${REPO}#installation`);
      process.exit(0);
    }
    return;
  }

  // 2. Binary exists — check version
  if (pluginVersion) {
    const binaryVersion = getBinaryVersion();
    if (binaryVersion && semverGt(pluginVersion, binaryVersion)) {
      log(`Updating ${BINARY} ${binaryVersion} → ${pluginVersion}...`);
      try {
        await install();
        const newVersion = getBinaryVersion();
        if (newVersion) log(`Updated to ${newVersion}`);
      } catch (e) {
        log(`Update failed: ${e.message}`);
        log(`Continuing with ${binaryVersion}`);
      }
    }
  }
}

main().catch((e) => {
  log(`Unexpected error: ${e.message}`);
  process.exit(0);
});
