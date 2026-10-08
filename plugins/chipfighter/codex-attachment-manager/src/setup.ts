// Purpose: v0.1-5 — switch Codex between going through the engine and connecting directly. Shared by the command line
// (cam install / setup / uninstall), the panel's 启用 / 停用 buttons, and the engine's own check after the plugin was
// removed without 停用. Every change backs up config.toml first and replaces the file whole (write, then rename), so
// Codex never reads half a file. .env may hold credentials: it is never copied or printed.
// Input: ~/.codex/config.toml and ~/.codex/.env; the proxy variables Codex inherits; the plugin's folder in Codex's
// cache. Output: the same two files, and a backup under <data dir>/config-backup/.

import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { codexHome, persistedEnv, proxyStatus } from "./codexconfig.ts";
import { MARKETPLACE, PLUGIN, planInstall, planUninstall, pluginStatus, type Plan, type UserProxyEnv } from "./install.ts";
import { dataDir } from "./paths.ts";

export const codexFiles = () => ({ configFile: join(codexHome(), "config.toml"), envFile: join(codexHome(), ".env") });
export const readConfig = (): string => (existsSync(codexFiles().configFile) ? readFileSync(codexFiles().configFile, "utf8") : "");
export const readEnv = (): string | null => (existsSync(codexFiles().envFile) ? readFileSync(codexFiles().envFile, "utf8") : null);

// The proxy variables Codex will start with (the Windows registry; elsewhere the current environment).
export const userProxyEnv = (): UserProxyEnv => ({ httpProxy: persistedEnv("HTTPS_PROXY") ?? persistedEnv("HTTP_PROXY") ?? persistedEnv("ALL_PROXY"), noProxy: persistedEnv("NO_PROXY") });

export function backupConfig(): void {
  const { configFile } = codexFiles();
  if (!existsSync(configFile)) return;
  const backups = join(dataDir(), "config-backup");
  mkdirSync(backups, { recursive: true });
  copyFileSync(configFile, join(backups, `config.toml.${new Date().toISOString().replaceAll(":", "-")}`));
}

function replaceFile(file: string, text: string): void {
  writeFileSync(`${file}.cam-tmp`, text, "utf8");
  try {
    renameSync(`${file}.cam-tmp`, file);
  } catch {
    // Windows refuses the rename while another program has the file open; write it in place then.
    writeFileSync(file, text, "utf8");
    rmSync(`${file}.cam-tmp`, { force: true });
  }
}

export function applyPlan(plan: Plan): void {
  const { configFile, envFile } = codexFiles();
  if (plan.configChanged) {
    backupConfig();
    replaceFile(configFile, plan.configText);
  }
  if (plan.envChanged) {
    if (plan.envText === null) rmSync(envFile, { force: true });
    else replaceFile(envFile, plan.envText);
  }
}

// Codex goes through the engine from its next start. Throws, changing nothing, when the user's own settings conflict.
export function useEngine(port: number): Plan {
  const plan = planInstall({ configText: readConfig(), envText: readEnv(), env: userProxyEnv(), port });
  applyPlan(plan);
  return plan;
}

// Codex connects directly again from its next start; only what this tool wrote is removed.
export function connectDirectly(): Plan {
  const plan = planUninstall({ configText: readConfig(), envText: readEnv() });
  applyPlan(plan);
  return plan;
}

export const usesEngine = (): boolean => proxyStatus(readConfig()).enabled;

// Whether Codex no longer runs the plugin, judged only from clear signs: its folder in Codex's cache is gone
// (uninstalled), or config.toml turns it off. An entry Codex may some day write differently is not taken as a removal.
export function pluginGone(): "removed" | "disabled" | null {
  const root = join(codexHome(), "plugins", "cache", MARKETPLACE, PLUGIN);
  if (!existsSync(root) || !readdirSync(root).length) return "removed";
  const status = pluginStatus(readConfig());
  return status.installed && !status.enabled ? "disabled" : null;
}
