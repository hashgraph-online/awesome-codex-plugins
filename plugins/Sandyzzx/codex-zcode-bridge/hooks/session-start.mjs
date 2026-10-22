import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import path from "node:path";
import { stdin, stdout } from "node:process";

let input = "";
for await (const chunk of stdin) input += chunk;

const nodeVersion = process.versions.node.split(".").map(Number);
const nodeSupported = nodeVersion[0] > 22 || (nodeVersion[0] === 22 && (nodeVersion[1] > 18 || (nodeVersion[1] === 18 && nodeVersion[2] >= 0)));
const git = spawnSync("git", ["--version"], { encoding: "utf8", windowsHide: true });
const parts = [`Node.js ${process.versions.node}${nodeSupported ? " (supported)" : " (requires 22.18+)"}`];
if (git.status === 0) parts.push("Git detected");
else parts.push("Git is missing");

if (process.platform === "win32") {
  const pluginRoot = process.env.PLUGIN_ROOT ?? process.env.CLAUDE_PLUGIN_ROOT;
  const setupScript = pluginRoot ? path.join(pluginRoot, "hooks", "configure-runtime.ps1") : null;
  if (!setupScript || !existsSync(setupScript)) {
    parts.push("ZCode runtime setup script is unavailable; reinstall the plugin");
  } else {
    const setup = spawnSync(
      "powershell.exe",
      ["-NoLogo", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", setupScript],
      { encoding: "utf8", windowsHide: true, timeout: 15_000 },
    );
    const setupText = [setup.stdout, setup.stderr]
      .filter((value) => typeof value === "string" && value.trim())
      .join("\n")
      .trim();
    if (setup.status === 0) parts.push(setupText || "ZCode runtime and provider configs validated");
    else parts.push(`ZCode setup needs attention${setupText ? `: ${setupText}` : ""}`);
  }
} else {
  parts.push("Automatic runtime path validation currently supports Windows; Bridge will use its built-in discovery on this platform");
}

try {
  const session = JSON.parse(input);
  if (typeof session.cwd === "string" && existsSync(session.cwd)) {
    parts.push(`workspace: ${session.cwd}`);
  }
} catch {
  // Keep the hook advisory if the host adds or changes optional session fields.
}

let mode = process.env.ZCODE_BRIDGE_MODE || "yolo";
try {
  const runtimeConfigPath = path.join(homedir(), ".codex", "codex-zcode-bridge", "runtime-config.json");
  const runtimeConfig = JSON.parse(readFileSync(runtimeConfigPath, "utf8"));
  if (typeof runtimeConfig.ZCODE_BRIDGE_MODE === "string" && runtimeConfig.ZCODE_BRIDGE_MODE.trim()) {
    mode = runtimeConfig.ZCODE_BRIDGE_MODE.trim();
  }
} catch {
  // The hook remains advisory when runtime settings have not been created.
}
parts.push(`ZCode tasks use ${mode} mode with the current account's permissions. Git worktrees and allowed/forbidden path instructions are not an OS sandbox.`);
if (mode === "yolo") {
  parts.push("WARNING: yolo allows ordinary tool operations without approval and uses the current OS account's permissions. Set ZCODE_BRIDGE_MODE to build in runtime-config.json to use ZCode's approval rules.");
}

stdout.write(`Codex ZCode Bridge setup check: ${parts.join("; ")}\n`);
