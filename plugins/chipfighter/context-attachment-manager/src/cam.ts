// Purpose: the tool's command line. install / uninstall / status set up and remove every managed setting at once;
// list / uncheck / check / check-all work on one thread from the terminal.
// P5: install registers this repository as a plugin marketplace and installs the plugin with Codex's own command line
// (Codex copies it into its plugin cache and starts its MCP server, which keeps the engine running), checks that the
// installed copy starts, and only then points Codex at the engine. uninstall goes the other way round. Either way
// Codex is never left pointed at an engine that nothing would start.
// v0.1-5: setup, run from the copy Codex installed (the install scripts do this after Codex's own command line added
// the plugin), points Codex at the engine and starts it. The settings themselves are switched in setup.ts.
// v0.1-14: it speaks the system language (messages.ts); status shows the language the panel reported.
// v0.11: connect <platform> [--base-url URL], for a platform using the core alone (ADAPTERS.md).
// Input: install [--port N] | setup [--port N] | uninstall | status | connect <platform> [--base-url URL] |
// list|uncheck|check|check-all <thread id> [IMG-…].
// Output: config.toml (copied to <data dir>/config-backup/ before every change), ~/.codex/.env (never copied or
// printed: it may hold credentials), the plugin cache (through Codex's command line), the selection files, and a
// summary on stdout. Rollouts are only read.

import { execFileSync, spawn } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { findCodexCli, runCodex } from "./adapters/codex/codexcli.ts";
import { codexHome, MCP_BEGIN, noProxyStatus, proxyStatus } from "./adapters/codex/codexconfig.ts";
import { buildOf, DEFAULT_PORT, engineHealth, ensureEngine } from "./engine.ts";
import { isEntryPoint } from "./core/entry.ts";
import { codexUiLocale, currentLang } from "./adapters/codex/language.ts";
import { storedLang, systemLang } from "./core/language.ts";
import { say, type MessageKey } from "./core/messages.ts";
import { migrateDataOnce } from "./core/migrate-data.ts";
import { MARKETPLACE, PLUGIN, PLUGIN_ID, pluginStatus } from "./adapters/codex/install.ts";
import { applySelection, loadPanelState } from "./adapters/codex/panel.ts";
import type { PanelState } from "./panel/panel-state.ts";
import { dataDir, selectionDirOf } from "./core/paths.ts";
import { preservingPluginCache } from "./adapters/codex/plugin-cache.ts";
import { backupConfig, connectDirectly, planEngine, readConfig, readEnv, useEngine } from "./adapters/codex/setup.ts";
import { readRoute, registerRoute, routeBaseUrl, validateBaseUrl } from "./core/routes.ts";
import { applyEdits, undoEdits } from "./core/config-edit.ts";
import { CORE_PLATFORMS, corePlatformOf, detectPlatform } from "./platforms.ts";

type Json = Record<string, any>;
const lang = systemLang();
const t = (key: MessageKey, vars?: Record<string, string | number>) => say(lang, key, vars);
// A conflict with the user's settings (codexconfig.ts) comes with a message key.
const localized = (error: unknown) => {
  const known = error as { key?: MessageKey; vars?: Record<string, string> };
  return known?.key ? new Error(t(known.key, known.vars)) : error;
};
// This file lives in <repository>/plugin/src; the repository root is the marketplace.
const repository = resolve(import.meta.dirname, "..", "..");
const pluginVersion = (): string => JSON.parse(readFileSync(resolve(import.meta.dirname, "..", ".codex-plugin", "plugin.json"), "utf8")).version;
export const pluginCacheDir = (version: string) => join(codexHome(), "plugins", "cache", MARKETPLACE, PLUGIN, version);

function table(state: PanelState): string {
  const rows = state.images.map((image) => [
    image.id,
    t(!image.replaceable ? "cli.state.locked" : image.checked ? "cli.state.checked" : "cli.state.unchecked"),
    ["upload", "view", "generated", "tool"].includes(image.kind) ? t(`cli.kind.${image.kind}` as MessageKey) : image.kind,
    image.name ?? "—",
    image.turn ?? "—",
    image.width && image.height ? `${image.width}×${image.height}` : "—",
    `${(image.bytes / 1024).toFixed(0)} KB`,
    image.sameAs.join(",") || "—",
    image.requested ? t("cli.requested") : "",
  ].join(" | "));
  const mb = (bytes: number) => (bytes / 1e6).toFixed(2);
  return [
    t("cli.table.title", { thread: state.threadId, images: state.totals.images, turns: state.turns, unchecked: state.totals.unchecked, checkedMb: mb(state.totals.checkedBytes), allMb: mb(state.totals.allBytes) }),
    t("cli.table.header"),
    ...rows,
  ].join("\n");
}

// Codex may store the marketplace path with the \\?\ prefix; compare the plain paths, ignoring case on Windows.
const samePath = (a: string, b: string) => {
  const plain = (path: string) => resolve(path.replace(/^\\\\\?\\/, ""));
  return process.platform === "win32" ? plain(a).toLowerCase() === plain(b).toLowerCase() : plain(a) === plain(b);
};

function codex(cli: string, args: string[]): string {
  const { ok, output } = runCodex(cli, args);
  if (!ok) throw new Error(t("cli.codexFailed", { args: args.join(" "), output: output || t("cli.noOutput") }));
  return output;
}

// How Codex starts the plugin's MCP server (.mcp.json: ./scripts/launch in the plugin folder): on Windows it finds
// launch.cmd, which only cmd.exe runs; on macOS and Linux it runs the shell script itself (so it must be executable).
export const launcher = (script: string, platform: NodeJS.Platform = process.platform): [string, string[]] =>
  platform === "win32" ? ["cmd.exe", ["/d", "/s", "/c", "call", "./scripts/launch.cmd", script]] : ["./scripts/launch", [script]];

// Start the installed copy the way Codex will (its launcher, its folder) and ask it for its tools and its page.
export function selfTest(dir: string, timeoutMs = 20_000): Promise<{ ok: boolean; tools: string[]; error: string | null }> {
  return new Promise((done) => {
    const scratch = mkdtempSync(join(tmpdir(), "cam-selftest-"));
    const [command, args] = launcher("./src/plugin-server.ts");
    const child = spawn(command, args, {
      cwd: dir, windowsHide: true, stdio: ["pipe", "pipe", "pipe"],
      env: { ...process.env, CAM_NO_ENGINE: "1", CAM_DATA_DIR: scratch },
    });
    const replies = new Map<number, Json>();
    let buffer = "";
    let errors = "";
    const finish = (result: { ok: boolean; tools: string[]; error: string | null }) => {
      clearTimeout(timer);
      child.stdin.end();
      done(result);
    };
    const timer = setTimeout(() => finish({ ok: false, tools: [], error: t("cli.selfTest.timeout", { seconds: timeoutMs / 1000, errors: errors.trim() }) }), timeoutMs);
    child.stderr.on("data", (chunk: Buffer) => { errors += chunk.toString("utf8"); });
    child.on("error", (error) => finish({ ok: false, tools: [], error: String(error) }));
    child.stdout.on("data", (chunk: Buffer) => {
      buffer += chunk.toString("utf8");
      for (let end = buffer.indexOf("\n"); end >= 0; end = buffer.indexOf("\n")) {
        const line = buffer.slice(0, end).trim();
        buffer = buffer.slice(end + 1);
        if (!line) continue;
        try { const message = JSON.parse(line); if (typeof message.id === "number") replies.set(message.id, message); } catch { /* not ours */ }
      }
      if (replies.has(3)) {
        const tools = (replies.get(2)?.result?.tools ?? []).map((tool: Json) => tool.name);
        const page = replies.get(3)?.result?.contents?.[0]?.text ?? "";
        finish(tools.includes("cam_panel") && page.includes("<title>") ? { ok: true, tools, error: null } : { ok: false, tools, error: t("cli.selfTest.incomplete") });
      }
    });
    const send = (message: Json) => child.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", ...message })}\n`);
    send({ id: 1, method: "initialize", params: { protocolVersion: "2025-06-18", capabilities: {}, clientInfo: { name: "cam-install-selftest" } } });
    send({ method: "notifications/initialized" });
    send({ id: 2, method: "tools/list" });
    send({ id: 3, method: "resources/read", params: { uri: "ui://codex-attachment-manager/panel.html" } });
  });
}

// v0.11: the Node a platform's MCP service is started with: the one on PATH when it is 24 or later (it stays where it is),
// else this one (the cam script may run Codex's own Node, whose folder changes with each Codex update).
function stableNode(): string {
  try {
    const found = execFileSync("node", ["-p", "Number(process.versions.node.split('.')[0]) >= 24 ? process.execPath : ''"], { encoding: "utf8", windowsHide: true, timeout: 5000 }).trim();
    if (found) return found;
  } catch { /* no node on PATH */ }
  return process.execPath;
}

// Selections made before P5 lived in the repository's local/ folder; they move along once, never overwriting.
function migrateSelections(): number {
  const legacy = join(repository, "local", "selection");
  const target = selectionDirOf();
  if (!existsSync(legacy) || resolve(legacy) === resolve(target)) return 0;
  mkdirSync(target, { recursive: true });
  let moved = 0;
  for (const name of readdirSync(legacy).filter((file) => file.endsWith(".json"))) {
    if (existsSync(join(target, name))) continue;
    copyFileSync(join(legacy, name), join(target, name));
    moved++;
  }
  return moved;
}

async function main(): Promise<void> {
  migrateDataOnce(); // v0.1-15: Windows moved the data folder
  const [command, threadId, ...ids] = process.argv.slice(2);
  // The same port the plugin's MCP server uses: --port, else CAM_ENGINE_PORT, else the default.
  const port = Number(process.argv.includes("--port") ? process.argv[process.argv.indexOf("--port") + 1] : process.env.CAM_ENGINE_PORT ?? DEFAULT_PORT);

  if (command === "install") {
    if (!existsSync(join(repository, ".agents", "plugins", "marketplace.json"))) throw new Error(t("cli.runInRepo"));
    const cli = findCodexCli();
    if (!cli) throw new Error(t("cli.noCli"));
    // A conflict with the user's own settings stops everything before anything changes.
    try { planEngine(port); } catch (error) { throw localized(error); }
    backupConfig();
    const steps: string[] = [];
    // Install the target version first. Removing first can partially delete a Windows runtime still in use.
    const cacheRoot = join(codexHome(), "plugins", "cache", MARKETPLACE, PLUGIN);
    preservingPluginCache(cacheRoot, pluginVersion(), () => {
      const registered = pluginStatus(readConfig()).marketplace;
      if (registered && !samePath(registered, repository)) { codex(cli, ["plugin", "marketplace", "remove", MARKETPLACE]); steps.push(t("cli.step.oldMarketplace")); }
      if (!registered || !samePath(registered, repository)) { codex(cli, ["plugin", "marketplace", "add", repository]); steps.push(t("cli.step.addMarketplace")); }
      codex(cli, ["plugin", "add", PLUGIN_ID]);
    });
    steps.push(t("cli.step.install"));
    const installed = pluginCacheDir(pluginVersion());
    const test = await selfTest(installed);
    if (!test.ok) throw new Error(t("cli.selfTest.failed", { error: test.error ?? "" }));
    steps.push(t("cli.step.selfTest", { tools: test.tools.join(t("cli.list")) }));
    const plan = useEngine(port);
    const migrated = migrateSelections();
    // The installed copy runs the engine, as it will when Codex starts it; an engine of other code still running is
    // replaced (v0.4: also one of the same version, which a plugin service alone leaves running).
    const engine = await ensureEngine({ port, dir: join(installed, "src"), force: true });
    console.log(JSON.stringify({ command, steps, configChanged: plan.configChanged, envChanged: plan.envChanged, notes: plan.notes, migratedSelections: migrated, dataDir: dataDir(), engine: engine.state, enginePid: engine.health?.pid ?? null, next: t("cli.next.install") }, null, 2));
    return;
  }
  if (command === "setup") {
    // Only once Codex has the plugin: otherwise nothing would start the engine after Codex restarts.
    if (!pluginStatus(readConfig()).installed || !existsSync(pluginCacheDir(pluginVersion()))) throw new Error(t("cli.notInstalled"));
    let plan;
    try { plan = useEngine(port); } catch (error) { throw localized(error); }
    // Started from this copy, which is the installed one when the install scripts run it.
    const engine = await ensureEngine({ port });
    console.log(JSON.stringify({ command, configChanged: plan.configChanged, envChanged: plan.envChanged, notes: plan.notes, dataDir: dataDir(), engine: engine.state, enginePid: engine.health?.pid ?? null, next: t("cli.next.install") }, null, 2));
    return;
  }
  if (command === "uninstall") {
    // Codex goes back to connecting directly first; only then is the plugin that starts the engine removed.
    let plan;
    try { plan = connectDirectly(); } catch (error) { throw localized(error); }
    const steps = [t(plan.envChanged ? "cli.step.directEnv" : "cli.step.direct")];
    const cli = findCodexCli();
    const status = pluginStatus(readConfig());
    if (!cli && (status.installed || status.marketplace)) steps.push(t("cli.step.noCli"));
    if (cli && status.installed) { codex(cli, ["plugin", "remove", PLUGIN_ID]); steps.push(t("cli.step.removePlugin")); }
    if (cli && status.marketplace) { codex(cli, ["plugin", "marketplace", "remove", MARKETPLACE]); steps.push(t("cli.step.removeMarketplace")); }
    console.log(JSON.stringify({ command, steps, configChanged: plan.configChanged, envChanged: plan.envChanged, dataDir: dataDir(), next: t("cli.next.uninstall") }, null, 2));
    return;
  }
  if (command === "status") {
    const config = readConfig();
    const health = await engineHealth(port);
    const version = pluginVersion();
    console.log(JSON.stringify({
      command,
      proxy: proxyStatus(config),
      plugin: { ...pluginStatus(config), version, cached: existsSync(pluginCacheDir(version)) },
      legacyMcpServer: config.split(/\r?\n/).some((line) => line.trim() === MCP_BEGIN),
      dotenv: noProxyStatus(readEnv() ?? ""),
      engine: health ? { running: true, pid: health.pid, startedAt: health.startedAt, version: health.version ?? null, build: health.build ?? null, sameAsInstalled: health.build === buildOf(join(pluginCacheDir(version), "src")) } : { running: false },
      codexCli: findCodexCli(),
      // The language the tab's title and the text for the model use, from Codex's language setting and the panel's last
      // report (language.ts).
      language: { speaks: currentLang(), codexSetting: codexUiLocale(), panelReport: storedLang() },
      dataDir: dataDir(),
    }, null, 2));
    return;
  }
  // v0.11 (user 2026-11-02: an AI reading this repository installs for the platform it runs in, and never the wrong
  // one): which platform this shell runs in (platforms.ts), and what to run next.
  if (command === "detect") {
    const found = detectPlatform();
    const next = !found.platform ? (found.matches.includes("codebuddy") ? `CodeBuddy's agent, without WorkBuddy's marks. In WorkBuddy: node "${join(import.meta.dirname, "cam.ts")}" connect workbuddy --apply. The CodeBuddy CLI on its own has no adapter yet; ask the user which it is.` : "Not sure which agent this is: ask the user, then follow that agent's section of INSTALL.md.")
      : found.platform === "codex" ? "Follow the Codex section of INSTALL.md."
      : found.platform === "claude" ? "Follow the Claude Desktop section of INSTALL.md."
      : found.platform === "dsh" ? `dsh plugin --profile ${process.env.DSH_PROFILE || "<your profile>"} add "${join(import.meta.dirname, "adapters", "dsh")}"`
      : `node "${join(import.meta.dirname, "cam.ts")}" connect ${found.platform} --apply`;
    console.log(JSON.stringify({ command, platform: found.platform, matches: found.matches, next }, null, 2));
    return;
  }
  // v0.11: a platform using the core alone (platforms.ts, ADAPTERS.md): registers the route from the engine to where its
  // requests go now, and prints what to set in the platform; with --apply, sets it (each setting's earlier value recorded for
  // `disconnect`). --base-url names that address; --provider the provider, for a platform with one per provider.
  if (command === "connect" || command === "disconnect") {
    const platform = corePlatformOf(threadId);
    if (!platform) throw new Error(`usage: cam.ts ${command} <${CORE_PLATFORMS.map((one) => one.name).join("|")}> [--apply] [--provider NAME] [--base-url URL]`);
    if (command === "disconnect") {
      const undone = undoEdits(platform.name, dataDir());
      console.log([`${platform.title}: settings put back in ${undone.files.length ? undone.files.join(", ") : "no file (nothing was applied)"}.`, ...undone.kept.map((setting) => `Left as you changed it: ${setting}`), `Restart ${platform.title}.`].join("\n"));
      return;
    }
    const flag = (name: string) => (process.argv.includes(name) ? process.argv[process.argv.indexOf(name) + 1] ?? null : null);
    const apply = process.argv.includes("--apply");
    const plan = apply || platform.setup ? platform.setup?.({ home: homedir(), env: process.env, provider: flag("--provider") }) ?? null : null;
    // Connected before: the address stays where that route goes.
    const ours = plan?.current ? /^http:\/\/(?:127\.0\.0\.1|localhost):\d+\/__cam\/routes\/([a-f0-9]{32})/.exec(plan.current) : null;
    const baseUrl = flag("--base-url") ?? (ours ? readRoute(ours[1])?.baseUrl ?? null : plan?.current) ?? plan?.fallback ?? platform.upstream;
    if (!baseUrl) throw new Error(`${platform.title}: give the address its requests go to now, with --base-url (e.g. https://api.anthropic.com/v1)`);
    try { validateBaseUrl(baseUrl, port); } catch (error) { throw localized(error); }
    const route = registerRoute({ platform: platform.name, baseUrl });
    const url = routeBaseUrl(port, route.id).replace("localhost", "127.0.0.1");
    const mcp = { command: stableNode(), args: [join(import.meta.dirname, "plugin-server.ts")], env: { CAM_HOST: platform.name } };
    if (apply && plan?.manual) {
      console.log([`${platform.title}: ${plan.manual}.`, `${url} -> ${baseUrl}`, ...platform.connect({ url, mcp }).map((step, at) => `${at + 1}. ${step}`)].join("\n"));
      return;
    }
    if (apply) {
      if (!plan) throw new Error(`${platform.title}: its settings are not in a file this command writes; set them by hand: cam connect ${platform.name}`);
      const files = applyEdits(platform.name, plan.edits({ url, mcp }), dataDir());
      console.log([`${platform.title}: requests go through the engine to ${baseUrl}.`, `Changed: ${files.join(", ")}`, ...(plan.note ? [plan.note] : []), `Restart ${platform.title}. To undo: cam disconnect ${platform.name}`].join("\n"));
      return;
    }
    // Plain lines, to copy from: inside JSON the paths' backslashes would be escaped twice.
    console.log([`${platform.title}: ${url} -> ${baseUrl}`, ...platform.connect({ url, mcp }).map((step, at) => `${at + 1}. ${step}`)].join("\n"));
    return;
  }
  if (!command || !threadId) throw new Error("usage: cam.ts install [--port N] | setup [--port N] | uninstall | status | detect | connect|disconnect <platform> [--apply] [--provider NAME] [--base-url URL] | list|uncheck|check|check-all <thread id> [IMG-…]");
  const options = { sessionsDir: join(codexHome(), "sessions") };
  if (command === "list") console.log(table(loadPanelState(threadId, options)));
  else if (command === "uncheck") console.log(table(applySelection(threadId, { uncheck: ids }, options)));
  else if (command === "check") console.log(table(applySelection(threadId, { check: ids }, options)));
  else if (command === "check-all") console.log(table(applySelection(threadId, { checkAll: true }, options)));
  else throw new Error(`unknown command ${command}`);
}

if (isEntryPoint(import.meta.url)) await main();
