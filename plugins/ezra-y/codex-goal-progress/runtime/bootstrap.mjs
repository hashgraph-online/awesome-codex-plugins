#!/usr/bin/env node
import { spawn, spawnSync } from "node:child_process";
import { createHash, randomUUID } from "node:crypto";
import {
  accessSync,
  constants,
  cpSync,
  existsSync,
  mkdirSync,
  readFileSync,
  realpathSync,
  renameSync,
  rmSync,
  statSync,
} from "node:fs";
import { appendFile, mkdir, rm } from "node:fs/promises";
import { createConnection } from "node:net";
import { homedir } from "node:os";
import { basename, dirname, isAbsolute, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { acquireRuntimeLock } from "./runtime-lock.mjs";

const runtimeRoot = resolve(dirname(fileURLToPath(import.meta.url)));
const pluginRoot = resolve(runtimeRoot, "..");
const mode = process.argv[2] ?? "prepare";
const minimumNode = [22, 12, 0];
const requiredPnpmMajor = 11;
const buildWaitMs = 20 * 60 * 1000;

function errorCode(error) {
  if (error instanceof Error && error.message.trim()) {
    return error.message.split("\n", 1)[0].slice(0, 500);
  }
  return String(error).slice(0, 500);
}

function readJson(path, code) {
  try {
    return JSON.parse(readFileSync(path, "utf8"));
  } catch (error) {
    throw new Error(`${code}: ${errorCode(error)}`);
  }
}

const pluginManifest = readJson(
  resolve(pluginRoot, ".codex-plugin/plugin.json"),
  "GOAL_PROGRESS_PLUGIN_MANIFEST_INVALID",
);
const version = String(pluginManifest.version ?? "").trim();
if (
  pluginManifest.name !== "codex-goal-progress" ||
  !/^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/u.test(version)
) {
  throw new Error("GOAL_PROGRESS_PLUGIN_MANIFEST_INVALID");
}

function assertSupportedNode() {
  const values = process.versions.node.split(".").map(Number);
  const supported = minimumNode.every((value, index) => {
    const current = values[index] ?? 0;
    const previousEqual = minimumNode.slice(0, index).every((part, partIndex) => {
      return (values[partIndex] ?? 0) === part;
    });
    return !previousEqual || current >= value;
  });
  if (!supported) {
    throw new Error(
      `GOAL_PROGRESS_NODE_VERSION_UNSUPPORTED: requires Node.js >= ${minimumNode.join(".")}; received ${process.versions.node}`,
    );
  }
}

function derivePluginContext() {
  let inferred = null;
  try {
    const canonicalRoot = realpathSync.native(pluginRoot);
    const versionDirectory = canonicalRoot;
    const pluginDirectory = dirname(versionDirectory);
    const marketplaceDirectory = dirname(pluginDirectory);
    const cacheDirectory = dirname(marketplaceDirectory);
    const pluginsDirectory = dirname(cacheDirectory);
    const codexHome = dirname(pluginsDirectory);
    if (
      basename(cacheDirectory) === "cache" &&
      basename(pluginsDirectory) === "plugins" &&
      basename(pluginDirectory) === "codex-goal-progress" &&
      basename(marketplaceDirectory) &&
      basename(versionDirectory)
    ) {
      inferred = {
        codexHome,
        marketplaceName: basename(marketplaceDirectory),
      };
    }
  } catch {
    // A repository checkout can use explicit Plugin data while remaining outside the Codex cache.
  }

  let pluginDataRoot = null;
  for (const value of [process.env.GOAL_PROGRESS_PLUGIN_DATA, process.env.PLUGIN_DATA]) {
    // biome-ignore lint/suspicious/noTemplateCurlyInString: This is the literal Codex placeholder.
    if (value && value !== "${PLUGIN_DATA}") {
      if (!isAbsolute(value)) {
        throw new Error("GOAL_PROGRESS_PLUGIN_DATA_MUST_BE_ABSOLUTE");
      }
      pluginDataRoot = resolve(value);
      break;
    }
  }
  if (!pluginDataRoot && inferred) {
    pluginDataRoot = resolve(
      inferred.codexHome,
      "plugins/data",
      `codex-goal-progress-${inferred.marketplaceName}`,
    );
  }
  if (!pluginDataRoot) {
    throw new Error("GOAL_PROGRESS_PLUGIN_DATA_UNRESOLVED");
  }

  let codexHome = process.env.GOAL_PROGRESS_CODEX_HOME?.trim() || inferred?.codexHome || null;
  const dataDirectory = dirname(pluginDataRoot);
  const pluginsDirectory = dirname(dataDirectory);
  if (
    !codexHome &&
    basename(dataDirectory) === "data" &&
    basename(pluginsDirectory) === "plugins"
  ) {
    codexHome = dirname(pluginsDirectory);
  }
  if (!codexHome) {
    codexHome = resolve(homedir(), ".codex");
  }
  if (!isAbsolute(codexHome)) {
    throw new Error("GOAL_PROGRESS_CODEX_HOME_MUST_BE_ABSOLUTE");
  }

  const marketplaceName =
    process.env.GOAL_PROGRESS_PLUGIN_MARKETPLACE?.trim() || inferred?.marketplaceName || null;
  return {
    pluginDataRoot,
    codexHome: resolve(codexHome),
    marketplaceName,
  };
}

assertSupportedNode();
const pluginContext = derivePluginContext();
const pluginDataRoot = pluginContext.pluginDataRoot;
const sourceRuntimeRoot = resolve(pluginDataRoot, "source-runtime");
const versionsRoot = resolve(sourceRuntimeRoot, "versions");
const versionRoot = resolve(versionsRoot, version);
const buildLockPath = resolve(sourceRuntimeRoot, "build.lock");
const setupLockPath = resolve(sourceRuntimeRoot, "setup.lock");
const bootstrapLogPath = resolve(sourceRuntimeRoot, "bootstrap.log");
const helperLauncherPath = resolve(versionRoot, "bin/goal-progress");
const helperBundlePath = resolve(versionRoot, "bin/goal-progress.cjs");
const legacyBinary = resolve(
  homedir(),
  "Library/Application Support/CodexGoalProgress/install/current/bin/goal-progress",
);

async function log(event, details = {}) {
  await mkdir(sourceRuntimeRoot, { recursive: true, mode: 0o700 });
  await appendFile(
    bootstrapLogPath,
    `${JSON.stringify({ at: new Date().toISOString(), event, version, ...details })}\n`,
    { encoding: "utf8", mode: 0o600 },
  ).catch(() => undefined);
}

function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function runtimeIsReady(root = versionRoot) {
  const manifestPath = resolve(root, "manifest.json");
  if (!existsSync(manifestPath)) {
    return false;
  }
  let manifest;
  try {
    manifest = readJson(manifestPath, "GOAL_PROGRESS_SOURCE_RUNTIME_MANIFEST_INVALID");
  } catch {
    return false;
  }
  if (
    manifest.schemaVersion !== 1 ||
    manifest.releaseVersion !== version ||
    !manifest.files ||
    typeof manifest.files !== "object"
  ) {
    return false;
  }
  for (const record of Object.values(manifest.files)) {
    if (
      !record ||
      typeof record !== "object" ||
      typeof record.path !== "string" ||
      typeof record.bytes !== "number" ||
      typeof record.sha256 !== "string"
    ) {
      return false;
    }
    if (isAbsolute(record.path) || record.path.split(/[\\/]/u).includes("..")) {
      return false;
    }
    const path = resolve(root, record.path);
    if (path !== root && !path.startsWith(`${root}/`)) {
      return false;
    }
    try {
      const metadata = statSync(path);
      if (!metadata.isFile() || metadata.size !== record.bytes || sha256(path) !== record.sha256) {
        return false;
      }
    } catch {
      return false;
    }
  }
  return (
    existsSync(resolve(root, "bin/goal-progress")) &&
    existsSync(resolve(root, "bin/goal-progress.cjs")) &&
    existsSync(resolve(root, "bin/goal-progress-startup-listener"))
  );
}

function executable(path) {
  try {
    accessSync(path, constants.X_OK);
    return true;
  } catch {
    return false;
  }
}

function commandVersion(command, prefix = []) {
  const result = spawnSync(command, [...prefix, "--version"], {
    encoding: "utf8",
    timeout: 10_000,
    maxBuffer: 1024 * 1024,
  });
  return result.status === 0 ? String(result.stdout).trim() : null;
}

function resolvePnpm() {
  const candidates = [];
  if (process.env.GOAL_PROGRESS_PNPM && isAbsolute(process.env.GOAL_PROGRESS_PNPM)) {
    candidates.push({ command: process.env.GOAL_PROGRESS_PNPM, prefix: [] });
  }
  const pnpmHome = process.env.PNPM_HOME?.trim();
  if (pnpmHome && isAbsolute(pnpmHome)) {
    candidates.push({ command: resolve(pnpmHome, "pnpm"), prefix: [] });
  }
  candidates.push(
    { command: resolve(dirname(process.execPath), "pnpm"), prefix: [] },
    { command: resolve(homedir(), ".local/share/pnpm/pnpm"), prefix: [] },
    { command: resolve(homedir(), ".local/bin/pnpm"), prefix: [] },
    { command: "/opt/homebrew/bin/pnpm", prefix: [] },
    { command: "/usr/local/bin/pnpm", prefix: [] },
    { command: "pnpm", prefix: [] },
    { command: resolve(dirname(process.execPath), "corepack"), prefix: ["pnpm"] },
    { command: "/opt/homebrew/bin/corepack", prefix: ["pnpm"] },
    { command: "/usr/local/bin/corepack", prefix: ["pnpm"] },
    { command: "corepack", prefix: ["pnpm"] },
    {
      command: "/bin/zsh",
      prefix: ["-lc", 'exec pnpm "$@"', "goal-progress-pnpm"],
    },
  );
  for (const candidate of candidates) {
    const value = commandVersion(candidate.command, candidate.prefix);
    if (!value) {
      continue;
    }
    const major = Number.parseInt(value.split(".")[0] ?? "", 10);
    if (major === requiredPnpmMajor) {
      return candidate;
    }
  }
  throw new Error(`GOAL_PROGRESS_PNPM_VERSION_UNSUPPORTED: requires pnpm ${requiredPnpmMajor}.x`);
}

function runChecked(command, args, cwd, code) {
  const result = spawnSync(command, args, {
    cwd,
    encoding: "utf8",
    env: {
      ...process.env,
      CI: "1",
      COREPACK_ENABLE_DOWNLOAD_PROMPT: "0",
    },
    timeout: 15 * 60 * 1000,
    maxBuffer: 16 * 1024 * 1024,
  });
  if (result.status !== 0) {
    const detail = `${result.stderr ?? ""}\n${result.stdout ?? ""}`.trim().slice(-8_000);
    throw new Error(`${code}${detail ? `: ${detail}` : ""}`);
  }
}

function copyBuildInputs(stagingRoot) {
  for (const file of [
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "build-runtime.mjs",
    "node-runtime.sh",
    "helper-launcher.sh",
    "startup-listener-launcher.sh",
    "startup-listener-bridge.mjs",
    "startup-listener.mjs",
    "startup-listener.jxa",
  ]) {
    cpSync(resolve(runtimeRoot, file), resolve(stagingRoot, file));
  }
  const packagedSource = resolve(runtimeRoot, "source");
  const destinationSource = resolve(stagingRoot, "source");
  if (existsSync(resolve(packagedSource, "packages"))) {
    cpSync(packagedSource, destinationSource, { recursive: true });
    return;
  }
  mkdirSync(destinationSource, { recursive: true, mode: 0o700 });
  const sourceCandidates = [pluginRoot, resolve(pluginRoot, "../..")];
  const repositoryRoot = sourceCandidates.find(
    (candidate) =>
      existsSync(resolve(candidate, "packages")) &&
      existsSync(resolve(candidate, "platform")) &&
      existsSync(resolve(candidate, "hooks/src")),
  );
  if (!repositoryRoot) {
    throw new Error("GOAL_PROGRESS_SOURCE_TREE_MISSING");
  }
  for (const directory of ["packages", "platform", "hooks"]) {
    cpSync(resolve(repositoryRoot, directory), resolve(destinationSource, directory), {
      recursive: true,
    });
  }
}

async function buildRuntime() {
  if (runtimeIsReady()) {
    return versionRoot;
  }
  const releaseLock = await acquireRuntimeLock(buildLockPath, {
    timeoutMs: buildWaitMs,
    timeoutCode: "GOAL_PROGRESS_SOURCE_BUILD_LOCK_TIMEOUT",
    ready: () => runtimeIsReady(),
  });
  if (!releaseLock) {
    return versionRoot;
  }
  const stagingRoot = resolve(sourceRuntimeRoot, `.staging-${process.pid}-${randomUUID()}`);
  try {
    if (runtimeIsReady()) {
      return versionRoot;
    }
    await log("build-started", { node: process.version });
    mkdirSync(stagingRoot, { recursive: true, mode: 0o700 });
    copyBuildInputs(stagingRoot);
    const pnpm = resolvePnpm();
    runChecked(
      pnpm.command,
      [...pnpm.prefix, "install", "--frozen-lockfile", "--prefer-offline"],
      stagingRoot,
      "GOAL_PROGRESS_SOURCE_DEPENDENCY_INSTALL_FAILED",
    );
    runChecked(
      process.execPath,
      [
        resolve(stagingRoot, "build-runtime.mjs"),
        "--source",
        resolve(stagingRoot, "source"),
        "--output",
        resolve(stagingRoot, "output"),
      ],
      stagingRoot,
      "GOAL_PROGRESS_SOURCE_BUILD_FAILED",
    );
    if (!runtimeIsReady(resolve(stagingRoot, "output"))) {
      throw new Error("GOAL_PROGRESS_SOURCE_BUILD_OUTPUT_INVALID");
    }
    mkdirSync(versionsRoot, { recursive: true, mode: 0o700 });
    if (existsSync(versionRoot)) {
      rmSync(versionRoot, { recursive: true, force: true });
    }
    renameSync(resolve(stagingRoot, "output"), versionRoot);
    if (!runtimeIsReady()) {
      throw new Error("GOAL_PROGRESS_SOURCE_RUNTIME_ACTIVATION_FAILED");
    }
    await log("build-completed", {
      helperBytes: statSync(helperBundlePath).size,
    });
    return versionRoot;
  } catch (error) {
    await log("build-failed", { code: errorCode(error) });
    throw error;
  } finally {
    await rm(stagingRoot, { recursive: true, force: true }).catch(() => undefined);
    releaseLock();
  }
}

function runtimeEnvironment(root = versionRoot) {
  return {
    ...process.env,
    GOAL_PROGRESS_ROOT: pluginDataRoot,
    GOAL_PROGRESS_PLUGIN_DATA: pluginDataRoot,
    GOAL_PROGRESS_CODEX_HOME: pluginContext.codexHome,
    ...(pluginContext.marketplaceName
      ? { GOAL_PROGRESS_PLUGIN_MARKETPLACE: pluginContext.marketplaceName }
      : {}),
    GOAL_PROGRESS_PLUGIN_ROOT: pluginRoot,
    GOAL_PROGRESS_SOURCE_RUNTIME: "1",
    GOAL_PROGRESS_SOURCE_RUNTIME_ROOT: root,
    GOAL_PROGRESS_SOURCE_LAUNCHER: resolve(root, "bin/goal-progress"),
    GOAL_PROGRESS_SOURCE_BUNDLE: resolve(root, "bin/goal-progress.cjs"),
    GOAL_PROGRESS_RENDERER_BUNDLE_DIR: resolve(root, "renderer"),
    GOAL_PROGRESS_STARTUP_LISTENER: resolve(root, "bin/goal-progress-startup-listener"),
  };
}

function runAttached(command, args, environment = process.env) {
  const child = spawn(command, args, {
    stdio: "inherit",
    env: environment,
  });
  child.on("error", (error) => {
    process.stderr.write(`${errorCode(error)}\n`);
    process.exitCode = 1;
  });
  child.on("exit", (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
      return;
    }
    process.exitCode = code ?? 1;
  });
}

function spawnPrepare() {
  const child = spawn("/bin/sh", [resolve(runtimeRoot, "run-bootstrap.sh"), "prepare"], {
    detached: true,
    stdio: "ignore",
    env: {
      ...process.env,
      GOAL_PROGRESS_PLUGIN_DATA: pluginDataRoot,
    },
  });
  child.unref();
}

function sourceHelperReachable(timeoutMs = 150) {
  const socketPath = resolve(pluginDataRoot, "runtime/helper.sock");
  return new Promise((resolveReachable) => {
    const socket = createConnection(socketPath);
    let settled = false;
    const finish = (reachable) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timer);
      socket.destroy();
      resolveReachable(reachable);
    };
    const timer = setTimeout(() => finish(false), timeoutMs);
    timer.unref?.();
    socket.once("connect", () => finish(true));
    socket.once("error", () => finish(false));
    socket.once("close", () => finish(false));
  });
}

function fallbackLegacy(targetMode) {
  if (!executable(legacyBinary)) {
    return false;
  }
  runAttached(legacyBinary, [targetMode], process.env);
  return true;
}

async function ensureSourceSetup(root) {
  if (process.env.GOAL_PROGRESS_SOURCE_SKIP_SETUP === "1") {
    return;
  }
  const releaseLock = await acquireRuntimeLock(setupLockPath, {
    timeoutMs: 180_000,
    timeoutCode: "GOAL_PROGRESS_SOURCE_SETUP_LOCK_TIMEOUT",
  });
  try {
    const result = spawnSync(resolve(root, "bin/goal-progress"), ["__source-runtime-ensure"], {
      encoding: "utf8",
      env: runtimeEnvironment(root),
      timeout: 120_000,
      maxBuffer: 4 * 1024 * 1024,
    });
    if (result.status !== 0) {
      const detail = `${result.stderr ?? ""}
${result.stdout ?? ""}`
        .trim()
        .slice(-4_000);
      throw new Error(`GOAL_PROGRESS_SOURCE_SETUP_FAILED${detail ? `: ${detail}` : ""}`);
    }
  } finally {
    releaseLock?.();
  }
}

async function main() {
  if (mode === "hook") {
    if (!runtimeIsReady()) {
      spawnPrepare();
      fallbackLegacy("hook");
      return;
    }
    if (!(await sourceHelperReachable())) {
      spawnPrepare();
      fallbackLegacy("hook");
      return;
    }
    runAttached(helperLauncherPath, ["hook"], runtimeEnvironment());
    return;
  }

  if (mode === "mcp-server") {
    try {
      const root = await buildRuntime();
      await ensureSourceSetup(root);
      runAttached(resolve(root, "bin/goal-progress"), ["mcp-server"], runtimeEnvironment(root));
    } catch (error) {
      await log("mcp-start-failed", { code: errorCode(error) });
      if (!fallbackLegacy("mcp-server")) {
        process.stderr.write(`${errorCode(error)}\n`);
        process.exitCode = 1;
      }
    }
    return;
  }

  if (mode === "prepare") {
    try {
      const root = await buildRuntime();
      await ensureSourceSetup(root);
      await log("prepare-completed");
    } catch (error) {
      await log("prepare-failed", { code: errorCode(error) });
      process.stderr.write(`${errorCode(error)}\n`);
      process.exitCode = 1;
    }
    return;
  }

  if (mode === "doctor" || mode === "verify" || mode === "upgrade") {
    const root = await buildRuntime();
    runAttached(resolve(root, "bin/goal-progress"), [mode, "--json"], runtimeEnvironment(root));
    return;
  }

  if (mode === "uninstall") {
    if (!runtimeIsReady()) throw new Error("GOAL_PROGRESS_SOURCE_RUNTIME_NOT_READY");
    // Uninstall never builds, runs Setup, or starts a Helper.
    runAttached(
      helperLauncherPath,
      ["uninstall", "--json", "--delete-history"],
      runtimeEnvironment(),
    );
    return;
  }

  if (mode === "repair") {
    const root = await buildRuntime();
    await ensureSourceSetup(root);
    runAttached(resolve(root, "bin/goal-progress"), ["verify", "--json"], runtimeEnvironment(root));
    return;
  }

  throw new Error(`GOAL_PROGRESS_SOURCE_BOOTSTRAP_MODE_INVALID: ${mode}`);
}

main().catch(async (error) => {
  await log("bootstrap-failed", { mode, code: errorCode(error) });
  process.stderr.write(`${errorCode(error)}\n`);
  process.exitCode = 1;
});
