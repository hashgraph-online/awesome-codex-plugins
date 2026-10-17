// Starts Self-Starter when the plugin comes from the marketplace in its repository
// (`codex plugin marketplace add hyprh/self-starter`, or `/plugin install
// self-starter --marketplace hyprh/self-starter` in Claude Code). The first start
// installs the runtime of this plugin's version, with its background service and
// deno, into ~/.self-starter/runtime/<version>; later starts need no network.
// SELF_STARTER_RUNTIME installs from somewhere else, such as a tarball in tests.
//
// The same file is the launcher of both plugins (plugin/ for Codex, cc-plugin/ for
// Claude Code); a test keeps the two copies identical.

import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, openSync, readdirSync, readFileSync, renameSync, rmSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const REPOSITORY = "github:hyprh/self-starter";

function fail(message) {
  process.stderr.write(`self-starter: ${message}\n`);
  process.exit(1);
}

if (Number(process.versions.node.split(".")[0]) < 20) fail(`Node.js 20 or newer is required (this is ${process.version})`);

const pluginRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const manifest = [".codex-plugin", ".claude-plugin"].map((dir) => join(pluginRoot, dir, "plugin.json")).find((path) => existsSync(path));
if (!manifest) fail(`no plugin manifest in ${pluginRoot}`);
const { version } = JSON.parse(readFileSync(manifest, "utf8"));
const home = resolve(process.env.SELF_STARTER_HOME || join(homedir(), ".self-starter"));
const runtime = join(home, "runtime", version);
const cli = join(runtime, "node_modules", "self-starter", "dist", "src", "cli", "main.js");
const source = process.env.SELF_STARTER_RUNTIME || `${REPOSITORY}#v${version}`;

/** Installs the runtime beside its final folder and moves it into place, so that no start ever sees half of one. */
function install() {
  const staging = `${runtime}.${process.pid}.partial`;
  mkdirSync(staging, { recursive: true });
  // What an install that was stopped left behind.
  for (const name of readdirSync(dirname(runtime))) {
    const path = join(dirname(runtime), name);
    if (name.endsWith(".partial") && path !== staging && Date.now() - statSync(path).mtimeMs > 15 * 60_000) rmSync(path, { recursive: true, force: true });
  }
  const npm = spawnSync("npm", ["install", "--prefix", staging, "--no-audit", "--no-fund", "--loglevel=error", source], { stdio: ["ignore", 2, 2] });
  if (npm.status !== 0) {
    rmSync(staging, { recursive: true, force: true });
    fail(`could not install ${source}: ${npm.error ? npm.error.message : `npm exited with code ${npm.status}`}`);
  }
  try {
    renameSync(staging, runtime);
  } catch {
    rmSync(staging, { recursive: true, force: true }); // another start finished first
  }
  if (!existsSync(cli)) fail(`the runtime in ${runtime} has no ${cli}`);
}

/**
 * Runs install() in a process of its own, which outlives this one: a host that gives up on a slow
 * first start and stops this process does not stop the install, and the next start finds the
 * runtime ready. Resolves once it is installed; exits with the reason when it could not be.
 */
async function installInBackground() {
  process.stderr.write(`self-starter: installing ${source} into ${runtime}, once for this version\n`);
  const logs = join(home, "logs");
  mkdirSync(logs, { recursive: true, mode: 0o700 });
  const log = join(logs, "install.log");
  const out = openSync(log, "w", 0o600);
  const installer = spawn(process.execPath, [fileURLToPath(import.meta.url)], {
    detached: true,
    stdio: ["ignore", out, out],
    env: { ...process.env, SELF_STARTER_INSTALL_ONLY: "1" },
  });
  const code = await new Promise((done) => {
    installer.on("error", () => done(-1));
    installer.on("exit", (exitCode) => done(exitCode));
  });
  if (code !== 0 || !existsSync(cli)) {
    const reason = readFileSync(log, "utf8").trim().split("\n").reverse().find((line) => line.startsWith("self-starter: "));
    fail(reason ? reason.slice("self-starter: ".length) : `could not install ${source}; see ${log}`);
  }
}

const INSTALLING =
  "Self-Starter is finishing its first start: it is installing its runtime, which takes a minute or two. " +
  "Its tools appear here when it is ready; until then, tell the user it is getting ready.";

/** What the launcher answers in the runtime's place while it installs: no tools yet. */
function answerWhileInstalling({ method, params }) {
  switch (method) {
    case "initialize":
      return {
        result: {
          protocolVersion: params?.protocolVersion ?? "2025-06-18",
          capabilities: { tools: { listChanged: true } },
          serverInfo: { name: "self-starter", version },
          instructions: INSTALLING,
        },
      };
    case "ping":
      return { result: {} };
    case "tools/list":
      return { result: { tools: [] } };
    case "tools/call":
      return { result: { content: [{ type: "text", text: INSTALLING }], isError: true } };
    case "resources/list":
      return { result: { resources: [] } };
    case "resources/templates/list":
      return { result: { resourceTemplates: [] } };
    case "prompts/list":
      return { result: { prompts: [] } };
    default:
      return { error: { code: -32601, message: `Method not found: ${method}` } };
  }
}

/**
 * The MCP server's requests wait for the runtime, unless the host would give up waiting first:
 * Claude Code stops waiting for a server after MCP_TIMEOUT (30 seconds by default). A little before
 * that, the launcher answers in the runtime's place. Resolves once the runtime is installed, with what
 * the runtime's server has to know: whether the host was answered (it then says that its tools changed).
 */
async function serveWhileInstalling(installed) {
  const send = (message) => process.stdout.write(`${JSON.stringify(message)}\n`);
  let unread = "";
  let answering = false;
  const answerLines = () => {
    for (let newline = unread.indexOf("\n"); newline >= 0; newline = unread.indexOf("\n")) {
      const line = unread.slice(0, newline);
      unread = unread.slice(newline + 1);
      let message;
      try {
        message = JSON.parse(line);
      } catch {
        continue;
      }
      if (message.id !== undefined && message.method !== undefined) send({ jsonrpc: "2.0", id: message.id, ...answerWhileInstalling(message) });
    }
  };
  const onData = (chunk) => {
    unread += chunk;
    if (answering) answerLines();
  };
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", onData);
  const hostWaitsMs = Number(process.env.MCP_TIMEOUT) || 30_000;
  const timer = setTimeout(() => {
    answering = true;
    answerLines();
  }, Math.max(2_000, hostWaitsMs - 8_000));
  await installed;
  clearTimeout(timer);
  process.stdin.off("data", onData);
  process.stdin.pause();
  if (unread) process.stdin.unshift(unread); // for the runtime's server, as if it had been there all along
  return answering;
}

if (process.env.SELF_STARTER_INSTALL_ONLY === "1") {
  install();
  process.exit(0);
}

const args = process.argv.slice(2);
if (!existsSync(cli)) {
  const installed = installInBackground();
  // Claude Code sets CLAUDE_CODE_SESSION_ID for its MCP servers; Codex waits as long as the plugin's .mcp.json says.
  if (args[0] === "mcp" && process.env.CLAUDE_CODE_SESSION_ID) {
    if (await serveWhileInstalling(installed)) args.push("--tools-changed");
  } else {
    await installed;
  }
}

process.argv = [process.argv[0], cli, ...args];
await import(pathToFileURL(cli).href);
