// Purpose: P3-3 — the plugin's MCP server, started by Codex for each session. It keeps the engine (local proxy)
// running — at start and every 3 seconds, so a crashed engine comes back, and since v0.1-3 an engine left over from an
// older plugin version is replaced — and serves the panel's data tools:
// the thread's images and their state, check/uncheck, and the images themselves.
// Only the user may check or uncheck: calls the model makes (they carry Codex's turn metadata) are refused.
// P4 — the panel page itself (an MCP App resource). cam_panel declares a "thread" entrypoint, so Codex lists the panel
// under the side panel's New Tab → 插件和 MCP, and the user opens it without the model.
// v0.1-5 — cam_setup: the panel's 启用 / 停用 point Codex at the engine or back to a direct connection (setup.ts).
// v0.1-10 — a panel opened on a new chat before its first message is told which threads the user has just started,
// and switches to one with cam_bind; from then on its calls are about that thread (binding.ts). v0.1-11 — slow calls
// are logged with their duration; pixel fingerprints are shared with the engine through the data directory.
// v0.1-14 — the panel reports Codex's interface language with its calls; it is remembered (language.ts), and the tool
// list (the tab's title), results and refusals speak it (messages.ts). v0.1-20 — Codex's language setting counts too.
// v0.3 — cam_view_image, the one tool for the model: in a thread with automatic selection on, it returns the originals
// of images by id, each after a line naming it (rewrite.ts), so the index knows them as copies. Codex's code mode does
// not list plugin tools to the model; the model learns its name from the context note and looks it up.
// v0.4 — the same service under Claude Code (CAM_HOST=claude, set by the Claude plugin's manifest): it keeps the same
// engine running, and serves the Claude plugin's mod (its panel and its routing, hooks/register.js) and the model's
// cam_view_image for a Claude Code session, read from that session's transcript (claude-index.ts). The session is the
// one the call names (the mod passes it), else the one Claude Code started this service for (CLAUDE_CODE_SESSION_ID).
// Input: MCP JSON-RPC over stdio. Env: CAM_ENGINE_PORT (default 17891), CAM_NO_ENGINE=1 (tests), CAM_DATA_DIR,
// CAM_HOST. Output: tool results; <data dir>/plugin-server.jsonl (events and counts only, no conversation content).

import { appendFileSync, mkdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";
import { codexHome } from "./codexconfig.ts";
import { bindThread, isUserThread, newThreads, resolveThread } from "./binding.ts";
import { loadClaudeIndex } from "./claude-index.ts";
import { DEFAULT_PORT, ensureEngine } from "./engine.ts";
import { isEntryPoint } from "./entry.ts";
import { currentLang, langOf, rememberLang, type Lang } from "./language.ts";
import { say } from "./messages.ts";
import { migrateDataOnce } from "./migrate-data.ts";
import { applySelection, claudeImageFor, imageFor, loadPanelState, type ClaudePanelOptions, type PanelState } from "./panel-state.ts";
import { claudeSelectionDirOf, dataDir, pixelCacheDirOf, selectionDirOf } from "./paths.ts";
import { fetchedLabel, fetchWords } from "./rewrite.ts";
import { effectiveSelection, readSelection } from "./selection.ts";
import { connectDirectly, useEngine, usesEngine } from "./setup.ts";
import { hasRollout, loadThreadIndex, readThreadHistory, sessionMetaOf, setPixelCache } from "./thread-index.ts";
import { threadTitle } from "./thread-names.ts";

type Json = Record<string, any>;
const here = dirname(fileURLToPath(import.meta.url));
// Kept fixed: Codex Desktop on Windows may show a blank panel after a resource URI changes (openai/codex#47512).
export const PANEL_URI = "ui://codex-attachment-manager/panel.html";
export const PANEL_MIME = "text/html;profile=mcp-app";
const APP_ONLY = { ui: { visibility: ["app"] } };
// The tool list speaks the language at the moment Codex starts this service (language.ts). Codex keeps it: desktop 26.924
// shares it between tasks for up to 30 minutes and ignores notifications that it changed, so after the user changes
// Codex's language the tab's title follows once Codex restarts.
export function toolsFor(lang: Lang) {
  const threadArg = { threadId: { type: "string", description: say(lang, "tool.threadId") } };
  const langArg = { lang: { type: "string", description: say(lang, "tool.lang") } };
  const shared = { ...threadArg, ...langArg };
  return [
    {
      name: "cam_panel",
      title: say(lang, "tool.panel.title"),
      description: say(lang, "tool.panel.description"),
      inputSchema: { type: "object", properties: { ...shared, langSource: { type: "string" }, shown: { type: "array", items: { type: "array", items: { type: "number" } }, description: say(lang, "tool.shown") } } },
      _meta: { ui: { resourceUri: PANEL_URI, visibility: ["app"] }, "openai/ui": { entrypoints: [{ type: "thread" }] } },
    },
    {
      name: "cam_set_selection",
      title: say(lang, "tool.select.title"),
      description: say(lang, "tool.select.description"),
      inputSchema: { type: "object", properties: { ...shared, uncheck: { type: "array", items: { type: "string" } }, check: { type: "array", items: { type: "string" } }, checkAll: { type: "boolean" }, auto: { type: "boolean" }, mode: { type: "string", enum: ["manual", "auto"] } } },
      _meta: APP_ONLY,
    },
    {
      name: "cam_image",
      title: say(lang, "tool.image.title"),
      description: say(lang, "tool.image.description"),
      inputSchema: { type: "object", properties: { ...shared, id: { type: "string" }, maxSide: { type: "number" } }, required: ["id"] },
      _meta: APP_ONLY,
    },
    {
      name: "cam_setup",
      title: say(lang, "tool.setup.title"),
      description: say(lang, "tool.setup.description"),
      inputSchema: { type: "object", properties: { ...shared, enable: { type: "boolean" } }, required: ["enable"] },
      _meta: APP_ONLY,
    },
    {
      name: "cam_bind",
      title: say(lang, "tool.bind.title"),
      description: say(lang, "tool.bind.description"),
      inputSchema: { type: "object", properties: { ...shared, target: { type: "string" } }, required: ["target"] },
      _meta: APP_ONLY,
    },
    // For the model (no app-only visibility); its words are text for the model, so they live in rewrite.ts.
    {
      name: "cam_view_image",
      title: fetchWords(lang).title,
      description: fetchWords(lang).description,
      inputSchema: { type: "object", properties: { ids: { type: "array", items: { type: "string" }, description: fetchWords(lang).ids } }, required: ["ids"] },
      annotations: { readOnlyHint: true },
    },
  ];
}
export const TOOLS = toolsFor("zh");

// v0.4: under Claude Code only the model's fetch tool is listed. The Claude panel (the mod) reads and changes a
// session's state through the engine (proxy.ts, claudePanelApi): a mod reaches an MCP server only through Claude Code's
// tool permissions, a prompt for every call, and Claude Code registers no app-only tool at all.
export const HOST: "codex" | "claude" = process.env.CAM_HOST === "claude" ? "claude" : "codex";
export const claudeToolsFor = (lang: Lang) => toolsFor(lang).filter((tool) => tool.name === "cam_view_image");

// A stack of pictures, drawn for light and dark themes (Codex takes https or data URLs only).
const ICON_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="14" height="14" rx="2.5"/><path d="M7 3h10.5A3.5 3.5 0 0 1 21 6.5V16"/><circle cx="8" cy="11" r="1.5"/><path d="m3.5 18 4.5-4.5 3 3 2-2 3.5 3.5"/></svg>';
const icon = (theme: "light" | "dark", color: string) => ({
  src: `data:image/svg+xml;base64,${Buffer.from(ICON_SVG.replace("currentColor", color)).toString("base64")}`,
  mimeType: "image/svg+xml", sizes: ["any"], theme,
});
export const serverInfo = (lang: Lang) => ({ name: "codex-attachment-manager", title: say(lang, "server.title"), version: "0.3.0", icons: [icon("light", "#5d5d5d"), icon("dark", "#cdcdcd")] });

export function readResource(uri: string): Json {
  if (uri !== PANEL_URI) throw new Error(`unknown resource ${uri}`);
  const text = readFileSync(join(here, "panel.html"), "utf8");
  // The page is self-contained: images arrive as data URLs through tool calls, nothing is fetched.
  return { contents: [{ uri, mimeType: PANEL_MIME, text, _meta: { ui: { csp: { connectDomains: [], resourceDomains: [] }, prefersBorder: false } } }] };
}

// Whether this instance last found the engine running; null until the first check (and in tests).
let engineRunning: boolean | null = null;
const enginePort = Number(process.env.CAM_ENGINE_PORT ?? DEFAULT_PORT);
// v0.1-5: whether config.toml points Codex at the engine, and whether that differs from what it said when this instance
// started (about when Codex read it): only a difference waits for a restart, so 停用 then 启用 again needs none.
let setupBaseline: boolean | null = null;
export function resetSetupBaseline(): void { setupBaseline = null; }
function setupState(): { usesEngine: boolean; changed: "enabled" | "disabled" | null } {
  const now = usesEngine();
  if (setupBaseline === null) setupBaseline = now;
  return { usesEngine: now, changed: now === setupBaseline ? null : now ? "enabled" : "disabled" };
}

function log(entry: Json): void {
  const root = dataDir();
  mkdirSync(root, { recursive: true });
  appendFileSync(join(root, "plugin-server.jsonl"), `${JSON.stringify({ at: new Date().toISOString(), pid: process.pid, ...entry })}\n`);
}

// Codex adds turn metadata to calls the model makes; the panel's own calls carry only the thread id.
export function fromModel(meta: Json | undefined): boolean {
  return !!meta && meta["x-codex-turn-metadata"] !== undefined;
}

export function threadOf(args: Json, meta: Json | undefined): string | null {
  return args.threadId ?? meta?.threadId ?? meta?.thread_id ?? meta?.["x-codex-turn-metadata"]?.thread_id ?? null;
}

const summary = (lang: Lang, state: PanelState) => say(lang, "call.summary", { images: state.totals.images, unchecked: state.totals.unchecked });

// A conflict with the user's settings comes with a message key (codexconfig.ts): said in the panel's language.
function localized(error: unknown, lang: Lang): unknown {
  const known = error as { key?: Parameters<typeof say>[1]; vars?: Record<string, string> };
  return known?.key ? new Error(say(lang, known.key, known.vars)) : error;
}
const SLOW_MS = 300;

// What a panel on a thread without a rollout is offered: the threads the user started while the panel was on screen.
function newTasks(sessionsDir: string, shown: unknown): Json[] {
  return newThreads(sessionsDir, shown).map(({ threadId, startedAt }) => {
    let title: string | null = null;
    try { title = threadTitle(sessionsDir, threadId, readThreadHistory(sessionsDir, threadId)); } catch { /* shown by its time */ }
    return { threadId, startedAt, title };
  });
}

export function callTool(name: string, args: Json, meta: Json | undefined, sessionsDir = join(codexHome(), "sessions")): Json {
  // The panel sends the language it shows; calls without one (Codex's first call, the model's) get the remembered one.
  const lang = langOf(args.lang) ?? currentLang();
  if (name === "cam_panel" && langOf(args.lang) && !fromModel(meta)) rememberLang(lang, args.langSource === "codex" ? "codex" : "system");
  const own = threadOf(args, meta);
  if (!own) throw new Error(say(lang, "call.noThread"));
  // A panel switched to a new thread (v0.1-10) keeps sending its own thread id; its calls are about the new one.
  const threadId = resolveThread(own, sessionsDir);
  const options = { sessionsDir };
  const panel = (state: PanelState, extra: Json = {}) => ({ ...state, engineRunning, setup: setupState(), ...(threadId === own ? {} : { switchedFrom: own }), ...extra });
  if (name === "cam_panel") {
    const state = loadPanelState(threadId, options);
    // Only the panel page says when it was on screen; Codex's own first call does not, and gets no list.
    const offer = !state.started && threadId === own && Array.isArray(args.shown) ? { newTasks: newTasks(sessionsDir, args.shown) } : {};
    return { content: [{ type: "text", text: summary(lang, state) }], structuredContent: panel(state, offer) };
  }
  if (name === "cam_set_selection") {
    if (fromModel(meta)) throw new Error(say(lang, "call.modelSelect"));
    const state = applySelection(threadId, { uncheck: args.uncheck, check: args.check, checkAll: args.checkAll, auto: typeof args.auto === "boolean" ? args.auto : undefined, mode: args.mode === "auto" ? "auto" : "manual" }, options);
    return { content: [{ type: "text", text: summary(lang, state) }], structuredContent: panel(state) };
  }
  if (name === "cam_bind") {
    if (fromModel(meta)) throw new Error(say(lang, "call.modelBind"));
    const target = String(args.target ?? "");
    if (hasRollout(sessionsDir, own)) throw new Error(say(lang, "call.started"));
    if (!isUserThread(sessionMetaOf(sessionsDir, target))) throw new Error(say(lang, "call.notUserThread"));
    bindThread(own, target);
    const state = loadPanelState(target, options);
    return { content: [{ type: "text", text: summary(lang, state) }], structuredContent: { ...state, engineRunning, setup: setupState(), switchedFrom: own } };
  }
  if (name === "cam_setup") {
    if (fromModel(meta)) throw new Error(say(lang, "call.modelSetup"));
    setupState(); // the baseline, in case this is the first call
    // A conflict with the user's own settings throws here, before anything is written.
    let plan;
    try { plan = args.enable === true ? useEngine(enginePort) : connectDirectly(); } catch (error) { throw localized(error, lang); }
    const state = loadPanelState(threadId, options);
    return { content: [{ type: "text", text: say(lang, args.enable === true ? "call.enabled" : "call.disabled") }], structuredContent: panel(state, { notes: plan.notes }) };
  }
  if (name === "cam_view_image") {
    const words = fetchWords(lang);
    const ids: string[] = Array.isArray(args.ids) ? args.ids.map(String) : typeof args.id === "string" ? [args.id] : [];
    // Only where the user switched automatic selection on; otherwise images come back only when the user checks them.
    if (!effectiveSelection(threadId, sessionsDir, selectionDirOf(dataDir())).auto) {
      log({ event: "fetch", threadId, ids, refused: "automatic selection is off" });
      return { content: [{ type: "text", text: words.off }], isError: true };
    }
    const index = loadThreadIndex(sessionsDir, threadId);
    const content: Json[] = [];
    const found: string[] = [];
    for (const asked of ids) {
      const id = asked.trim().toUpperCase();
      const image = index.images.find((candidate) => candidate.id === id);
      if (!image) { content.push({ type: "text", text: words.missing(asked) }); continue; }
      const { dataUrl } = imageFor(threadId, id, Number.MAX_SAFE_INTEGER, options);
      const parts = dataUrl ? /^data:([^;,]+);base64,(.*)$/s.exec(dataUrl) : null;
      if (!parts) { content.push({ type: "text", text: words.unavailable(id) }); continue; }
      content.push({ type: "text", text: fetchedLabel(image, lang) }, { type: "image", data: parts[2], mimeType: parts[1] });
      found.push(id);
    }
    log({ event: "fetch", threadId, ids, found });
    return { content, isError: ids.length > 0 && !found.length };
  }
  if (name === "cam_image") {
    const image = imageFor(threadId, String(args.id), Number(args.maxSide ?? 160), options);
    // The image data goes in _meta, which only the panel sees.
    return { content: [{ type: "text", text: say(lang, image.dataUrl ? "call.imageOk" : "call.imageNone") }], structuredContent: { id: image.id, available: image.dataUrl !== null }, _meta: { dataUrl: image.dataUrl } };
  }
  throw new Error(`unknown tool ${name}`);
}

// v0.4: the model's fetch tool under Claude Code. The session is the one the call names (the mod adds it), else the
// one Claude Code started this service for.
const SESSION_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

export function callClaudeTool(name: string, args: Json, options: ClaudePanelOptions = {}, env: NodeJS.ProcessEnv = process.env): Json {
  const lang = langOf(args.lang) ?? currentLang();
  const sessionId = String(args.sessionId ?? env.CLAUDE_CODE_SESSION_ID ?? "");
  if (!SESSION_ID.test(sessionId)) throw new Error(say(lang, "call.noThread"));
  if (name === "cam_view_image") {
    const words = fetchWords(lang);
    const ids: string[] = Array.isArray(args.ids) ? args.ids.map(String) : typeof args.id === "string" ? [args.id] : [];
    if (!readSelection(sessionId, claudeSelectionDirOf(options.dataRoot ?? dataDir())).auto) {
      log({ event: "fetch", host: "claude", sessionId, ids, refused: "automatic selection is off" });
      return { content: [{ type: "text", text: words.off }], isError: true };
    }
    const index = loadClaudeIndex(sessionId, options.home);
    const content: Json[] = [];
    const found: string[] = [];
    for (const asked of ids) {
      const id = asked.trim().toUpperCase();
      const image = index.images.find((candidate) => candidate.id === id);
      if (!image) { content.push({ type: "text", text: words.missing(asked) }); continue; }
      const { dataUrl } = claudeImageFor(sessionId, id, Number.MAX_SAFE_INTEGER, options);
      const parts = dataUrl ? /^data:([^;,]+);base64,(.*)$/s.exec(dataUrl) : null;
      if (!parts) { content.push({ type: "text", text: words.unavailable(id) }); continue; }
      content.push({ type: "text", text: fetchedLabel(image, lang) }, { type: "image", data: parts[2], mimeType: parts[1] });
      found.push(id);
    }
    log({ event: "fetch", host: "claude", sessionId, ids, found });
    return { content, isError: ids.length > 0 && !found.length };
  }
  throw new Error(`unknown tool ${name}`);
}

function main(): void {
  migrateDataOnce(); // v0.1-15: Windows moved the data folder
  const send = (message: Json) => process.stdout.write(`${JSON.stringify({ jsonrpc: "2.0", ...message })}\n`);
  let engineState = "";
  const supervise = async () => {
    if (process.env.CAM_NO_ENGINE === "1") return;
    const result = await ensureEngine({ port: enginePort });
    const replaced = result.replaced ? { replacedPid: result.replaced.pid, replacedBuild: result.replaced.build ?? null } : {};
    if (result.state !== "running" || engineState !== "running") log({ event: "engine", host: HOST, state: result.state, enginePid: result.health?.pid ?? null, build: result.health?.build ?? null, ...replaced });
    engineState = result.state;
    engineRunning = result.state !== "failed";
  };
  log({ event: "start", ppid: process.ppid, host: HOST });
  setupState(); // what Codex read when it started this session
  setPixelCache(pixelCacheDirOf());
  // Codex starts several instances at once; a little jitter keeps them from racing to start the engine.
  setTimeout(supervise, Math.floor(Math.random() * 400));
  // Short enough that a crashed engine is back within Codex's own retry window.
  setInterval(supervise, 3000);
  process.stdin.on("close", () => { log({ event: "stdin-closed" }); process.exit(0); });
  createInterface({ input: process.stdin, crlfDelay: Infinity }).on("line", (line) => {
    if (!line.trim()) return;
    let message: Json;
    try { message = JSON.parse(line); } catch { return; }
    const { id, method, params = {} } = message;
    if (method === "initialize") {
      send({ id, result: { protocolVersion: params.protocolVersion ?? "2025-06-18", capabilities: { tools: {}, resources: {} }, serverInfo: serverInfo(currentLang()) } });
    } else if (method === "tools/list") {
      send({ id, result: { tools: HOST === "claude" ? claudeToolsFor(currentLang()) : toolsFor(currentLang()) } });
    } else if (method === "resources/list") {
      send({ id, result: { resources: [{ uri: PANEL_URI, name: say(currentLang(), "resource.name"), mimeType: PANEL_MIME }] } });
    } else if (method === "resources/templates/list") {
      send({ id, result: { resourceTemplates: [] } });
    } else if (method === "resources/read") {
      try {
        send({ id, result: readResource(params.uri) });
        log({ event: "resources/read" });
      } catch (error) {
        send({ id, error: { code: -32002, message: error instanceof Error ? error.message : String(error) } });
      }
    } else if (method === "tools/call") {
      const started = performance.now();
      try {
        const result = HOST === "claude" ? callClaudeTool(params.name, params.arguments ?? {}) : callTool(params.name, params.arguments ?? {}, params._meta);
        const ms = Math.round(performance.now() - started);
        // The open panel reads its state every few seconds and loads each image once; only changes, and slow calls
        // (v0.1-11), are worth a line.
        if (["cam_set_selection", "cam_setup", "cam_bind"].includes(params.name) || fromModel(params._meta)) log({ event: "tools/call", name: params.name, fromModel: fromModel(params._meta), ms });
        else if (ms >= SLOW_MS) log({ event: "slow", name: params.name, ms });
        send({ id, result });
      } catch (error) {
        log({ event: "tools/call", name: params.name, fromModel: fromModel(params._meta), error: String(error) });
        send({ id, result: { isError: true, content: [{ type: "text", text: error instanceof Error ? error.message : String(error) }] } });
      }
    } else if (method === "ping") {
      send({ id, result: {} });
    } else if (id !== undefined) {
      send({ id, error: { code: -32601, message: `unsupported: ${method}` } });
    }
  });
}

if (isEntryPoint(import.meta.url)) main();
