#!/usr/bin/env node
var __defProp = Object.defineProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};

// src/web/main.ts
import { randomUUID as randomUUID11 } from "node:crypto";
import path26 from "node:path";
import process2 from "node:process";
import { fileURLToPath as fileURLToPath10 } from "node:url";

// src/runtime/host-profile.ts
import { homedir } from "node:os";
import path from "node:path";
function codexHostProfile(homeDirectory = homedir()) {
  return {
    name: "codex-zcode-bridge",
    settingsDirectory: path.join(homeDirectory, ".codex", "codex-zcode-bridge")
  };
}
function validateHostProfile(host) {
  if (!host || typeof host.name !== "string" || !host.name.trim() || typeof host.settingsDirectory !== "string" || !path.isAbsolute(host.settingsDirectory)) {
    throw new Error("invalid Bridge host profile");
  }
  if (host.legacySettingsDirectories !== void 0 && (!Array.isArray(host.legacySettingsDirectories) || host.legacySettingsDirectories.some((directory) => typeof directory !== "string" || !path.isAbsolute(directory)))) {
    throw new Error("host migration directories must be absolute");
  }
  if (host.workerEntryPath !== void 0 && (typeof host.workerEntryPath !== "string" || !path.isAbsolute(host.workerEntryPath))) {
    throw new Error("host worker entry must be absolute");
  }
  if (host.instructions !== void 0 && typeof host.instructions !== "string") {
    throw new Error("host instructions must be text");
  }
  if (host.defaultDataRoot !== void 0 && (typeof host.defaultDataRoot !== "string" || !path.isAbsolute(host.defaultDataRoot))) {
    throw new Error("host default data root must be absolute");
  }
  return host;
}

// src/runtime/process-probe.ts
import { readFile } from "node:fs/promises";
import { spawn } from "node:child_process";
var PROCESS_IDENTITY_VERSION = 1;
var DEFAULT_PROBE_TIMEOUT_MS = 5e3;
var DEFAULT_MAX_CONCURRENT = 2;
function identityOfFingerprint(pid, fingerprint, precision, now) {
  return {
    pid,
    fingerprint,
    fingerprint_precision: precision,
    identity_version: PROCESS_IDENTITY_VERSION,
    platform: process.platform,
    captured_at: new Date(now()).toISOString()
  };
}
function verdict(state, reason, now) {
  return { state, reason_code: reason, observed_at: new Date(now()).toISOString() };
}
function failedQuery(reason) {
  return { ok: false, reason, fingerprints: /* @__PURE__ */ new Map() };
}
function windowsPowerShellExecutable() {
  const systemRoot = Object.entries(process.env).find(([key]) => key.toLowerCase() === "systemroot")?.[1];
  return systemRoot ? `${systemRoot}\\System32\\WindowsPowerShell\\v1.0\\powershell.exe` : "powershell.exe";
}
function windowsBatchQuery(pids, timeoutMs, onFailure) {
  return new Promise((resolve) => {
    const script = `$ErrorActionPreference = 'Stop'; foreach ($id in @(${pids.join(",")})) { $target = $null; try { try { $target = [System.Diagnostics.Process]::GetProcessById($id) } catch [System.ArgumentException] { continue }; try { [Console]::Out.WriteLine(("{0}|{1}" -f $id, $target.StartTime.Ticks)) } catch [System.InvalidOperationException] { continue } } finally { if ($null -ne $target) { $target.Dispose() } } }; [Console]::Out.WriteLine('bridge_probe_complete_v1')`;
    const child = spawn(windowsPowerShellExecutable(), ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script], {
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
      shell: false
    });
    let stdout = "";
    let settled = false;
    const fail2 = (reason) => {
      if (settled) return;
      try {
        onFailure?.(reason);
      } catch {
      }
      finish(failedQuery(reason));
    };
    const finish = (query) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(query);
    };
    const timer = setTimeout(() => {
      try {
        child.kill("SIGKILL");
      } catch {
      }
      fail2("timeout");
    }, timeoutMs);
    timer.unref();
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    let stderrBytes = 0;
    child.stderr.on("data", (chunk) => {
      stderrBytes = Math.min(64e3, stderrBytes + chunk.length);
    });
    child.stdout.on("data", (chunk) => {
      if (stdout.length < 1e6) stdout += chunk;
    });
    child.on("error", () => fail2("spawn_error"));
    child.on("close", (code) => {
      const map = /* @__PURE__ */ new Map();
      const lines = stdout.trim().split(/\r?\n/u);
      if (code !== 0) {
        fail2("nonzero_exit");
        return;
      }
      if (stderrBytes > 0) {
        fail2("stderr");
        return;
      }
      if (lines.pop() !== "bridge_probe_complete_v1") {
        fail2("missing_completion_marker");
        return;
      }
      for (const line of lines) {
        if (!line.trim()) continue;
        const match = /^(\d+)\|(\d+)$/u.exec(line.trim());
        if (!match || !pids.includes(Number(match[1])) || map.has(Number(match[1]))) {
          fail2("malformed_output");
          return;
        }
        map.set(Number(match[1]), match[2]);
      }
      finish({ ok: true, reason: "ok", fingerprints: map });
    });
  });
}
async function darwinQuery(pids, timeoutMs) {
  return new Promise((resolve) => {
    const child = spawn("ps", ["-o", "pid=,lstart=", "-p", pids.join(",")], {
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
      shell: false
    });
    let stdout = "";
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      try {
        child.kill("SIGKILL");
      } catch {
      }
      resolve(failedQuery("timeout"));
    }, timeoutMs);
    timer.unref();
    child.stdout.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      if (stdout.length < 1e6) stdout += chunk;
    });
    child.on("error", () => {
      if (!settled) {
        settled = true;
        clearTimeout(timer);
        resolve(failedQuery("spawn_error"));
      }
    });
    child.on("close", () => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      const map = /* @__PURE__ */ new Map();
      for (const line of stdout.split(/\r?\n/u)) {
        const match = /^\s*(\d+)\s+(.+)$/u.exec(line);
        if (match) map.set(Number(match[1]), match[2].trim());
      }
      resolve({ ok: true, reason: "ok", fingerprints: map });
    });
  });
}
function createPlatformProbe(options = {}) {
  const timeoutMs = options.timeoutMs ?? DEFAULT_PROBE_TIMEOUT_MS;
  const maxConcurrent = options.maxConcurrent ?? DEFAULT_MAX_CONCURRENT;
  const now = options.now ?? Date.now;
  let chain = Promise.resolve();
  let inFlight = 0;
  let waiters = [];
  const schedule = async (operation) => {
    if (inFlight >= maxConcurrent) {
      await new Promise((resolve) => waiters.push(resolve));
    }
    inFlight += 1;
    try {
      return await operation();
    } finally {
      inFlight -= 1;
      const next = waiters.shift();
      if (next) next();
    }
  };
  const probe = async (requests) => {
    if (requests.length === 0) return [];
    const distinct = [...new Set(requests.map((request) => request.pid).filter((pid) => Number.isInteger(pid) && pid > 0))];
    const query = await schedule(async () => {
      if (process.platform === "win32") return windowsBatchQuery(distinct, timeoutMs, options.onWindowsQueryFailure);
      if (process.platform === "darwin") return darwinQuery(distinct, timeoutMs);
      if (process.platform === "linux") {
        const map = /* @__PURE__ */ new Map();
        for (const pid of distinct) {
          try {
            const stat5 = await readFile(`/proc/${pid}/stat`, "utf8");
            const afterComm = stat5.slice(stat5.lastIndexOf(")") + 2);
            const fields = afterComm.split(" ");
            const starttime = fields[19];
            if (starttime) map.set(pid, starttime.trim());
          } catch (error2) {
            if (error2.code === "ENOENT") continue;
            return failedQuery("proc_read_error");
          }
        }
        return { ok: true, reason: "ok", fingerprints: map };
      }
      return failedQuery("unsupported_platform");
    });
    return requests.map((request) => {
      if (!Number.isInteger(request.pid) || request.pid <= 0) return verdict("unknown", "invalid_pid", now);
      if (!query.ok) return verdict("unknown", `query_${query.reason}`, now);
      const fingerprint = query.fingerprints.get(request.pid);
      if (fingerprint === void 0) {
        return verdict("exited", "pid_absent", now);
      }
      if (!request.identity || request.identity.fingerprint === null) {
        return verdict("unknown", "live_pid_no_fingerprint", now);
      }
      if (request.identity.fingerprint_precision === "coarse") {
        return request.identity.fingerprint === fingerprint ? verdict("unknown", "coarse_fingerprint_match", now) : verdict("exited", "pid_reused_coarse", now);
      }
      if (request.identity.fingerprint !== fingerprint) {
        return verdict("exited", "pid_reused", now);
      }
      return verdict("alive", "pid_and_fingerprint_match", now);
    });
  };
  const fingerprintOfPid = async (pid) => {
    const query = await schedule(async () => {
      if (process.platform === "win32") return windowsBatchQuery([pid], timeoutMs, options.onWindowsQueryFailure);
      if (process.platform === "darwin") return darwinQuery([pid], timeoutMs);
      if (process.platform === "linux") {
        const map = /* @__PURE__ */ new Map();
        try {
          const stat5 = await readFile(`/proc/${pid}/stat`, "utf8");
          const afterComm = stat5.slice(stat5.lastIndexOf(")") + 2);
          const starttime = afterComm.split(" ")[19];
          if (starttime) map.set(pid, starttime.trim());
        } catch {
        }
        return { ok: true, reason: "ok", fingerprints: map };
      }
      return failedQuery("unsupported_platform");
    });
    const fingerprint = query.fingerprints.get(pid);
    if (!query.ok || !fingerprint) return identityOfFingerprint(pid, null, "unknown", now);
    const precision = process.platform === "darwin" ? "coarse" : "exact";
    return identityOfFingerprint(pid, fingerprint, precision, now);
  };
  return {
    platform: process.platform,
    identityOf: fingerprintOfPid,
    selfIdentity: () => fingerprintOfPid(process.pid),
    probe
  };
}

// src/runtime/sqlite-install-config.ts
import { existsSync as existsSync3, lstatSync, mkdirSync, readFileSync as readFileSync3, realpathSync } from "node:fs";
import os from "node:os";
import path7 from "node:path";
import { fileURLToPath as fileURLToPath2 } from "node:url";

// src/runtime/resolver.ts
import { accessSync, existsSync as existsSync2, readFileSync as readFileSync2, statSync } from "node:fs";
import { homedir as homedir2 } from "node:os";
import path6 from "node:path";
import { fileURLToPath } from "node:url";

// src/runtime/account-provider.ts
import path2 from "node:path";
function zcodeDataBaseDir(personalProviderConfigFile) {
  const dataDir = zcodeV2DataDir(personalProviderConfigFile);
  return dataDir ? path2.dirname(path2.dirname(dataDir)) : null;
}
function zcodeV2DataDir(personalProviderConfigFile) {
  const absolute = path2.resolve(personalProviderConfigFile);
  if (path2.basename(absolute).toLowerCase() !== "provider_config.json") return null;
  const v2Dir = path2.dirname(absolute);
  if (path2.basename(v2Dir).toLowerCase() !== "v2") return null;
  const zcodeDir = path2.dirname(v2Dir);
  if (path2.basename(zcodeDir).toLowerCase() !== ".zcode") return null;
  return v2Dir;
}

// src/runtime/errors.ts
var BridgeError = class extends Error {
  code;
  memberPids;
  /** ADR-066: redacted official RPC rejections observed before this failure. */
  rpcDiagnostics;
  /** ADR-066: the Session bound to the rejected RPC, kept as execution evidence. */
  sessionId;
  constructor(code, message, options) {
    super(message, options);
    this.name = "BridgeError";
    this.code = code;
    if (options?.memberPids?.length) this.memberPids = [...new Set(options.memberPids.filter((pid) => Number.isSafeInteger(pid) && pid > 0))];
    if (options?.rpcDiagnostics?.length) this.rpcDiagnostics = options.rpcDiagnostics;
    if (typeof options?.sessionId === "string" && options.sessionId) this.sessionId = options.sessionId;
  }
};

// src/runtime/official-builtin-registry.ts
import { createHash } from "node:crypto";
import { lstat as nodeLstat, readFile as nodeReadFile } from "node:fs/promises";
import { realpath as nodeRealpath } from "node:fs/promises";
import path5 from "node:path";

// src/runtime/desktop-host-launch.ts
import { closeSync, openSync, readSync } from "node:fs";
import path3 from "node:path";
var ZCODE_APP_VERSION_ENV = "ZCODE_APP_VERSION";
var ZCODE_BUILD_COMMIT_ID_ENV = "ZCODE_BUILD_COMMIT_ID";
var APP_SERVER_ARGS = ["app-server", "--stdio", "--surface", "desktop"];
var BUILD_METADATA_PATH = ["out", "metadata", "build-meta.json"];
var MAX_ASAR_HEADER_BYTES = 32 * 1024 * 1024;
var MAX_METADATA_BYTES = 64 * 1024;
var VERSION_PATTERN = /^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/u;
var BUILD_COMMIT_PATTERN = /^[0-9a-f]{8}$/u;
function buildZCodeAppServerLaunch(zcodeEntrypoint, baseEnv) {
  const metadata = readDesktopMetadata(zcodeEntrypoint);
  return {
    args: [...APP_SERVER_ARGS],
    env: metadata === null ? { ...baseEnv } : {
      ...baseEnv,
      [ZCODE_APP_VERSION_ENV]: metadata.appVersion,
      [ZCODE_BUILD_COMMIT_ID_ENV]: metadata.buildCommitId
    }
  };
}
function readDesktopMetadata(zcodeEntrypoint) {
  const archivePath = path3.resolve(path3.dirname(zcodeEntrypoint), "..", "app.asar");
  let archive;
  try {
    archive = readAsarMetadataFiles(archivePath);
  } catch (error2) {
    if (isMissingFile(error2)) return null;
    throw invalidMetadata("could not be read");
  }
  const packageJson = parseObject(archive.packageJson, "package.json");
  const buildMetadata = parseObject(archive.buildMetadata, "build-meta.json");
  const packageVersion = packageJson["version"];
  const appVersion = buildMetadata["appVersion"];
  const buildCommitId = buildMetadata["buildCommitId"];
  if (typeof packageVersion !== "string" || typeof appVersion !== "string" || typeof buildCommitId !== "string") {
    throw invalidMetadata("is missing required fields");
  }
  if (!VERSION_PATTERN.test(packageVersion) || !VERSION_PATTERN.test(appVersion) || !BUILD_COMMIT_PATTERN.test(buildCommitId)) {
    throw invalidMetadata("uses an unsupported version or build commit format");
  }
  if (packageVersion !== appVersion) {
    throw invalidMetadata("contains conflicting application versions");
  }
  return { appVersion, buildCommitId };
}
function readAsarMetadataFiles(archivePath) {
  const fd = openSync(archivePath, "r");
  try {
    const sizeHeader = Buffer.alloc(16);
    readExact(fd, sizeHeader, 16, 0);
    if (sizeHeader.readUInt32LE(0) !== 4) throw new Error("invalid asar header");
    const headerPayloadBytes = sizeHeader.readUInt32LE(4);
    const headerBytes = sizeHeader.readUInt32LE(12);
    if (headerBytes === 0 || headerBytes > MAX_ASAR_HEADER_BYTES || headerPayloadBytes < headerBytes) {
      throw new Error("invalid asar header size");
    }
    const headerBuffer = Buffer.alloc(headerBytes);
    readExact(fd, headerBuffer, headerBytes, 16);
    const root = parseObject(headerBuffer, "asar header");
    if (!isRecord(root.files)) throw new Error("asar header file table is not an object");
    const buildEntry = findEntry(root.files, BUILD_METADATA_PATH);
    if (buildEntry === null) throw new Error("asar build metadata is missing");
    const packageEntry = findEntry(root.files, ["package.json"]);
    if (packageEntry === null) throw new Error("asar package.json is missing");
    return {
      packageJson: readEntry(fd, packageEntry, 8 + headerPayloadBytes),
      buildMetadata: readEntry(fd, buildEntry, 8 + headerPayloadBytes)
    };
  } finally {
    closeSync(fd);
  }
}
function findEntry(root, parts) {
  let files = root;
  for (let index = 0; index < parts.length; index += 1) {
    const part = parts[index];
    if (!Object.hasOwn(files, part)) return null;
    const current = files[part];
    if (!isRecord(current)) throw new Error(`asar ${part} entry is not an object`);
    if (index === parts.length - 1) return current;
    if (!isRecord(current.files)) throw new Error(`asar ${part} entry is not a directory`);
    files = current.files;
  }
  return null;
}
function readEntry(fd, entry, contentOffset) {
  const offset = asNonNegativeSafeInteger(entry.offset);
  const size = asNonNegativeSafeInteger(entry.size);
  if (entry.files || entry.unpacked || entry.link || offset === null || size === null || size > MAX_METADATA_BYTES || !Number.isSafeInteger(contentOffset + offset)) {
    throw new Error("invalid asar metadata entry");
  }
  const output = Buffer.alloc(size);
  readExact(fd, output, output.length, contentOffset + offset);
  return output;
}
function asNonNegativeSafeInteger(value) {
  if (typeof value === "number") {
    return Number.isSafeInteger(value) && value >= 0 ? value : null;
  }
  if (typeof value !== "string" || !/^(?:0|[1-9]\d*)$/u.test(value)) return null;
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) ? parsed : null;
}
function readExact(fd, target, length, position) {
  let offset = 0;
  while (offset < length) {
    const read = readSync(fd, target, offset, length - offset, position + offset);
    if (read === 0) throw new Error("unexpected end of asar file");
    offset += read;
  }
}
function parseObject(buffer, label) {
  let parsed;
  try {
    parsed = JSON.parse(buffer.toString("utf8"));
  } catch {
    throw invalidMetadata(`${label} is not valid JSON`);
  }
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    throw invalidMetadata(`${label} is not an object`);
  }
  return parsed;
}
function invalidMetadata(reason) {
  return new BridgeError(
    "provider_config_invalid",
    `Installed ZCode Desktop metadata ${reason}; refusing to invent a Desktop identity.`
  );
}
function isMissingFile(error2) {
  return typeof error2 === "object" && error2 !== null && "code" in error2 && error2.code === "ENOENT";
}
function isRecord(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

// src/runtime/paths.ts
import { existsSync, readFileSync } from "node:fs";
import path4 from "node:path";
function resolveUserHome(env, options = {}) {
  const platform = options.platform ?? process.platform;
  const pathImpl = platform === "win32" ? path4.win32 : path4.posix;
  const homeRaw = env["HOME"]?.trim() || null;
  const userProfileRaw = env["USERPROFILE"]?.trim() || null;
  if (platform !== "win32") {
    if (homeRaw) {
      return { userHome: pathImpl.resolve(homeRaw), source: "HOME", homeRaw, homeConflict: null };
    }
    const fallback2 = userProfileRaw ?? options.fallbackHomeDir ?? "";
    if (!fallback2) {
      throw new Error("no user home directory available (HOME is empty and no fallback provided)");
    }
    return { userHome: pathImpl.resolve(fallback2), source: userProfileRaw ? "USERPROFILE" : "FALLBACK", homeRaw: null, homeConflict: null };
  }
  if (homeRaw) {
    const rooted = isWindowsAbsolutePath(homeRaw);
    const matchesUserProfile = userProfileRaw !== null && sameCleanPath(homeRaw, userProfileRaw, pathImpl, true);
    if (rooted && matchesUserProfile) {
      return { userHome: pathImpl.resolve(homeRaw), source: "HOME", homeRaw, homeConflict: null };
    }
    const conflict = !rooted ? "HOME is set but is not an absolute path" : userProfileRaw === null ? "HOME is set but USERPROFILE is not, so HOME cannot be verified as the current Windows user directory" : "HOME is set but does not match USERPROFILE (test or WSL directories must not override the Windows user directory)";
    if (userProfileRaw) {
      return { userHome: pathImpl.resolve(userProfileRaw), source: "USERPROFILE", homeRaw, homeConflict: conflict };
    }
    const fallback2 = options.fallbackHomeDir;
    if (!fallback2) {
      throw new Error("no Windows user directory available (HOME is invalid and no USERPROFILE or fallback provided)");
    }
    return { userHome: pathImpl.resolve(fallback2), source: "FALLBACK", homeRaw, homeConflict: conflict };
  }
  if (userProfileRaw) {
    return { userHome: pathImpl.resolve(userProfileRaw), source: "USERPROFILE", homeRaw: null, homeConflict: null };
  }
  const fallback = options.fallbackHomeDir;
  if (!fallback) {
    throw new Error("no Windows user directory available (HOME and USERPROFILE are unset and no fallback provided)");
  }
  return { userHome: pathImpl.resolve(fallback), source: "FALLBACK", homeRaw: null, homeConflict: null };
}
function discoverZCodeData(env, options = {}) {
  const platform = options.platform ?? process.platform;
  const pathImpl = platform === "win32" ? path4.win32 : path4.posix;
  const readFile7 = options.readFile ?? ((filePath) => readFileSync(filePath, "utf8"));
  const fileExists = options.fileExists ?? existsSync;
  const home = resolveUserHome(env, options);
  const settingFile = pathImpl.join(home.userHome, ".zcode", "v2", "setting.json");
  let settingStatus = "ok";
  let settingError = null;
  let configuredDataBaseDir = null;
  if (!fileExists(settingFile)) {
    settingStatus = "absent";
  } else {
    let text;
    try {
      text = readFile7(settingFile);
    } catch (error2) {
      settingStatus = isPermissionDeniedCode(error2) ? "permission_denied" : "unreadable";
      settingError = error2 instanceof Error ? error2.message : String(error2);
      text = "";
    }
    if (settingStatus === "ok") {
      let parsed;
      try {
        parsed = JSON.parse(text);
      } catch (error2) {
        settingStatus = "invalid_json";
        settingError = error2 instanceof Error ? error2.message : String(error2);
      }
      if (settingStatus === "ok") {
        if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
          settingStatus = "invalid_shape";
          settingError = "setting.json must contain a JSON object";
        } else {
          const raw = parsed["dataBaseDir"];
          if (raw === void 0 || raw === null) {
          } else if (typeof raw !== "string") {
            settingStatus = "invalid_shape";
            settingError = "dataBaseDir must be a string when present";
          } else {
            const trimmed = raw.trim();
            if (trimmed && isAbsolutePathForPlatform(trimmed, platform)) {
              configuredDataBaseDir = pathImpl.resolve(trimmed);
            } else if (trimmed) {
              settingError = "dataBaseDir is a relative path and was ignored";
            }
          }
        }
      }
    }
  }
  const dataBaseDir = configuredDataBaseDir ?? home.userHome;
  return {
    userHome: home.userHome,
    settingFile,
    settingStatus,
    settingError,
    configuredDataBaseDir,
    dataBaseDir,
    dataBaseDirSource: configuredDataBaseDir ? "setting.json" : "default",
    zcodeDataDir: pathImpl.join(dataBaseDir, ".zcode"),
    zcodeV2Dir: pathImpl.join(dataBaseDir, ".zcode", "v2"),
    migrated: configuredDataBaseDir !== null
  };
}
function isWindowsAbsolutePath(value) {
  return /^[A-Za-z]:[\\/]/u.test(value) || /^\/\/[^\\/]+[\\/][^\\/]+(?:[\\/].*)?$/u.test(value) || /^\\\\[^\\/]+[\\/][^\\/]+(?:[\\/].*)?$/u.test(value);
}
function isAbsolutePathForPlatform(value, platform = process.platform) {
  return platform === "win32" ? isWindowsAbsolutePath(value) : path4.isAbsolute(value);
}
function isPermissionDeniedCode(error2) {
  const code = error2?.code;
  return code === "EACCES" || code === "EPERM";
}
function discoverZCodeInstall(env, options = {}) {
  const platform = options.platform ?? process.platform;
  const pathImpl = platform === "win32" ? path4.win32 : path4.posix;
  const fileExists = options.fileExists ?? existsSync;
  const requireBuiltin = options.requireBuiltin ?? true;
  const roots = [];
  const explicit = env["ZCODE_WINDOWS_APP_INSTALL_DIR"]?.trim();
  if (explicit) roots.push({ root: explicit, source: "ZCODE_WINDOWS_APP_INSTALL_DIR" });
  const localAppData = env["LOCALAPPDATA"]?.trim();
  if (localAppData) roots.push({ root: pathImpl.join(localAppData, "Programs", "ZCode"), source: "LOCALAPPDATA" });
  const programFiles = env["ProgramFiles"]?.trim() ?? env["PROGRAMFILES"]?.trim();
  if (programFiles) roots.push({ root: pathImpl.join(programFiles, "ZCode"), source: "ProgramFiles" });
  const candidates = roots.map(({ root, source }) => ({
    root,
    source,
    runtimeExists: fileExists(pathImpl.join(root, "resources", "glm", "zcode.cjs")),
    builtinExists: fileExists(pathImpl.join(root, "resources", "config", "provider", "zcode-builtin.json"))
  }));
  for (const candidate of candidates) {
    if (!candidate.runtimeExists) continue;
    if (requireBuiltin && !candidate.builtinExists) continue;
    return {
      installDir: candidate.root,
      source: candidate.source,
      zcodeEntrypoint: pathImpl.join(candidate.root, "resources", "glm", "zcode.cjs"),
      builtinConfigFile: requireBuiltin || candidate.builtinExists ? pathImpl.join(candidate.root, "resources", "config", "provider", "zcode-builtin.json") : null,
      candidates
    };
  }
  return { installDir: null, source: null, zcodeEntrypoint: null, builtinConfigFile: null, candidates };
}
function builtinConfigForRuntime(zcodeEntrypoint, platform = process.platform) {
  const pathImpl = platform === "win32" ? path4.win32 : path4.posix;
  const resourcesDir = pathImpl.dirname(pathImpl.dirname(zcodeEntrypoint));
  return pathImpl.join(resourcesDir, "config", "provider", "zcode-builtin.json");
}
function sameFileSystemPath(left, right, platform = process.platform) {
  const pathImpl = platform === "win32" ? path4.win32 : path4.posix;
  return sameCleanPath(left, right, pathImpl, platform === "win32");
}
function sameCleanPath(left, right, pathImpl, caseInsensitive) {
  const cleanLeft = pathImpl.normalize(left);
  const cleanRight = pathImpl.normalize(right);
  return caseInsensitive ? cleanLeft.toLowerCase() === cleanRight.toLowerCase() : cleanLeft === cleanRight;
}

// src/runtime/official-builtin-registry.ts
var OFFICIAL_PRODUCTION_ENDPOINT_ORIGIN = "https://zcode.z.ai";
var OFFICIAL_TEST_ENDPOINT_ORIGIN = "https://zcode.chatglm.site";
var OFFICIAL_ENDPOINT_ENV_KEYS = Object.freeze([
  "ZCODE_ENV",
  "ZCODE_BASE_URL",
  "ZCODE_ENDPOINT_ORIGIN",
  "ZCODE_PRODUCTION_BASE_URL",
  "ZCODE_TEST_BASE_URL"
]);
async function isOfficialBuiltinRegistryPin(explicitBuiltin, bundledPath) {
  const explicit = explicitBuiltin?.trim() || null;
  if (!explicit || !bundledPath) return false;
  const [explicitCanonical, bundledCanonical] = await Promise.all([canonicalPath(explicit), canonicalPath(bundledPath)]);
  return !sameFileSystemPath(explicitCanonical, bundledCanonical);
}
async function canonicalPath(filePath) {
  try {
    return await nodeRealpath(filePath);
  } catch {
    return path5.resolve(filePath);
  }
}
var MAX_REGISTRY_BYTES = 8 * 1024 * 1024;
var OBSERVED_RETIRED_PROVIDER_ID = "builtin:zapi";
function officialEndpointOrigin(env = process.env) {
  const configured = (key) => {
    const value = env[key]?.trim();
    return value || void 0;
  };
  const test = env["ZCODE_ENV"]?.trim().toLowerCase() === "test";
  const base = configured("ZCODE_BASE_URL") ?? configured("ZCODE_ENDPOINT_ORIGIN") ?? (test ? configured("ZCODE_TEST_BASE_URL") : configured("ZCODE_PRODUCTION_BASE_URL"));
  if (!base) return test ? OFFICIAL_TEST_ENDPOINT_ORIGIN : OFFICIAL_PRODUCTION_ENDPOINT_ORIGIN;
  const url = new URL(base);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error("ZCode endpoint origin must use http or https");
  }
  return url.origin;
}
function officialClientPlatform(platform = process.platform, architecture = process.arch) {
  const operatingSystem = platform === "win32" ? "windows" : platform;
  const arch = architecture === "arm64" ? "aarch64" : architecture === "x64" ? "x86_64" : architecture;
  return `${operatingSystem}-${arch}`;
}
function officialDesktopAppVersion(zcodeEntrypoint) {
  try {
    return buildZCodeAppServerLaunch(zcodeEntrypoint, {}).env["ZCODE_APP_VERSION"] ?? null;
  } catch {
    return null;
  }
}
function officialRuntimeRegistryPath(input) {
  const appVersion = input.appVersion?.trim() || null;
  if (!appVersion || !path5.isAbsolute(input.dataBaseDir)) return null;
  try {
    registrySegment(appVersion, "appVersion");
    const platform = registrySegment(
      officialClientPlatform(input.platform, input.architecture),
      "platform"
    );
    const origin = officialEndpointOrigin(input.env);
    const endpointKey = `endpoint-${createHash("sha256").update(origin).digest("hex").slice(0, 32)}`;
    return path5.join(
      input.dataBaseDir,
      ".zcode",
      "v2",
      "runtime",
      "provider",
      platform,
      appVersion,
      endpointKey,
      "zcode-builtin.json"
    );
  } catch {
    return null;
  }
}
async function selectOfficialBuiltinRegistry(input) {
  const readFile7 = input.readFile ?? ((filePath) => nodeReadFile(filePath, "utf8"));
  const lstat4 = input.lstat ?? ((filePath) => nodeLstat(filePath));
  const bundled = (status, revision = null) => ({
    path: input.bundledPath,
    source: "bundled",
    bundledPath: input.bundledPath,
    revision,
    runtimePath: input.runtimePath,
    runtimeStatus: status
  });
  if (!input.runtimePath) return bundled("unresolved");
  let stat5;
  try {
    stat5 = await lstat4(input.runtimePath);
  } catch {
    return bundled("not_found");
  }
  if (!stat5.isFile() || stat5.isSymbolicLink()) return bundled("invalid");
  let runtime;
  try {
    runtime = decodeRegistry(await readFile7(input.runtimePath));
  } catch {
    runtime = null;
  }
  if (!runtime) return bundled("invalid");
  return runtimeSelected();
  function runtimeSelected() {
    return {
      path: input.runtimePath,
      source: "runtime",
      bundledPath: input.bundledPath,
      revision: runtime.revision,
      runtimePath: input.runtimePath,
      runtimeStatus: "selected"
    };
  }
}
function registrySegment(value, label) {
  if (!value || value === "." || value === ".." || /[\\/]/u.test(value)) {
    throw new Error(`ZCode Built-in ${label} is not a valid path segment`);
  }
  return value;
}
function decodeRegistry(text) {
  if (Buffer.byteLength(text, "utf8") > MAX_REGISTRY_BYTES) throw new Error("registry too large");
  const value = JSON.parse(text);
  if (!isRecord2(value) || !hasExactKeys(value, ["schemaVersion", "revision", "config"]) || value.schemaVersion !== 1) {
    throw new Error("unsupported registry schema");
  }
  const revision = value.revision;
  if (typeof revision !== "number" || !Number.isSafeInteger(revision) || revision < 0) {
    throw new Error("invalid registry revision");
  }
  const config2 = value.config;
  if (!isRecord2(config2) || !hasExactKeys(config2, ["providerConfigRules", "modelConfigRules"]) || !isRecord2(config2.providerConfigRules) || !isRecord2(config2.modelConfigRules)) {
    throw new Error("invalid registry config");
  }
  const providerRules = config2.providerConfigRules.providerRules;
  if (Array.isArray(providerRules) && providerRules.some((rule) => isRecord2(rule) && rule.providerId === OBSERVED_RETIRED_PROVIDER_ID)) {
    throw new Error("registry contains a retired provider");
  }
  if (isRecord2(providerRules) && Object.hasOwn(providerRules, OBSERVED_RETIRED_PROVIDER_ID)) {
    throw new Error("registry contains a retired provider");
  }
  return { revision };
}
function hasExactKeys(value, expected) {
  const keys = Object.keys(value);
  return keys.length === expected.length && expected.every((key) => Object.hasOwn(value, key));
}
function isRecord2(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

// src/runtime/resolver.ts
var PERSISTED_RUNTIME_KEYS = [
  "ZCODE_BRIDGE_NODE",
  "ZCODE_BRIDGE_ZCODE_CJS",
  "ZCODE_BRIDGE_DATA_DIR",
  "ZCODE_BUILTIN_PROVIDER_CONFIG_FILE",
  "ZCODE_PERSONAL_PROVIDER_CONFIG_FILE",
  "ZCODE_HOME",
  "ZCODE_DATA_BASE_DIR",
  "ZCODE_WINDOWS_APP_INSTALL_DIR",
  "ZCODE_BRIDGE_DEFAULT_PROVIDER_ID",
  "ZCODE_BRIDGE_DEFAULT_MODEL_ID",
  "ZCODE_BRIDGE_DEFAULT_REASONING_LEVEL",
  "ZCODE_BRIDGE_PREFER_STARTPLAN",
  "ZCODE_BRIDGE_MODE",
  "ZCODE_BRIDGE_MAX_CONCURRENT_WORKERS",
  "ZCODE_BRIDGE_TIMEOUT_MS",
  "ZCODE_BRIDGE_BROWSER_USE",
  "ZCODE_BRIDGE_BROWSER_EXECUTABLE",
  "ZCODE_BRIDGE_AUTO_WAKE",
  "ZCODE_BRIDGE_TASK_CONSOLE"
];
function loadPersistedRuntimeEnvironment(source, homeDir = homedir2(), host = codexHostProfile(homeDir)) {
  validateHostProfile(host);
  const settingsPaths = [host.settingsDirectory, ...host.legacySettingsDirectories ?? []].map((directory) => path6.join(directory, "runtime-config.json"));
  const legacyDataRoot = source["ZCODE_BRIDGE_DATA_DIR"]?.trim();
  if (legacyDataRoot && path6.isAbsolute(legacyDataRoot)) {
    settingsPaths.push(path6.join(legacyDataRoot, "runtime-config.json"));
  }
  let parsed = null;
  const seenPaths = /* @__PURE__ */ new Set();
  for (const settingsPath of settingsPaths) {
    const normalized = path6.resolve(settingsPath);
    const identity = process.platform === "win32" ? normalized.toLocaleLowerCase("en-US") : normalized;
    if (seenPaths.has(identity)) continue;
    seenPaths.add(identity);
    try {
      if (statSync(normalized).size > 64 * 1024) throw new Error("runtime settings exceed 64 KB");
      const candidate = JSON.parse(readFileSync2(normalized, "utf8"));
      if (isPlainObject(candidate)) {
        parsed = candidate;
        break;
      }
      throw new Error("runtime settings must be an object");
    } catch (error2) {
      if (error2.code === "ENOENT") continue;
      throw new BridgeError("provider_config_invalid", `invalid Bridge runtime settings: ${normalized}`, { cause: error2 });
    }
  }
  if (!parsed) return { ...source };
  const env = { ...source };
  for (const key of PERSISTED_RUNTIME_KEYS) {
    if (!Object.prototype.hasOwnProperty.call(parsed, key)) continue;
    const value = parsed[key];
    if (typeof value === "string") env[key] = value.trim();
    else if (value === null) env[key] = "";
    else throw new BridgeError("provider_config_invalid", `Bridge runtime setting ${key} must be a string or null`);
  }
  return env;
}
var NodeRuntimeResolver = class {
  #env;
  #homeDir;
  #packageRoot;
  #host;
  #onBuiltinRegistrySelection;
  constructor(options = {}) {
    this.#env = options.env ?? process.env;
    this.#homeDir = options.homeDir ?? homedir2();
    this.#packageRoot = options.packageRoot ?? null;
    this.#host = validateHostProfile(options.host ?? codexHostProfile(this.#homeDir));
    this.#onBuiltinRegistrySelection = options.onBuiltinRegistrySelection;
  }
  async resolve() {
    const env = loadPersistedRuntimeEnvironment(this.#env, this.#homeDir, this.#host);
    const data = discoverZCodeData(env, { fallbackHomeDir: this.#homeDir });
    const zcodeHome = resolveZcodeHome(env);
    const explicitDataBaseDir = env["ZCODE_DATA_BASE_DIR"]?.trim() || null;
    if (explicitDataBaseDir && !isAbsolutePathForPlatform(explicitDataBaseDir)) {
      throw new BridgeError("provider_config_invalid", "ZCODE_DATA_BASE_DIR must be an absolute path");
    }
    if (zcodeHome && explicitDataBaseDir && !sameFileSystemPath(path6.dirname(zcodeHome), explicitDataBaseDir)) {
      throw new BridgeError(
        "provider_config_invalid",
        `ZCODE_HOME (${zcodeHome}) and ZCODE_DATA_BASE_DIR (${explicitDataBaseDir}) conflict; ZCODE_HOME must name <ZCODE_DATA_BASE_DIR>/.zcode. Fix one of them instead of relying on silent selection.`
      );
    }
    let nodeExecutable = "node";
    const nodeOverride = env["ZCODE_BRIDGE_NODE"]?.trim();
    if (nodeOverride) {
      this.#assertReadableFile(
        nodeOverride,
        "ZCODE_BRIDGE_NODE is set but is not a readable file"
      );
      nodeExecutable = nodeOverride;
    }
    const builtinEnv = env["ZCODE_BUILTIN_PROVIDER_CONFIG_FILE"]?.trim() || null;
    const personalEnv = env["ZCODE_PERSONAL_PROVIDER_CONFIG_FILE"]?.trim() || null;
    let zcodeEntrypoint;
    let explicitRuntime = false;
    const entryOverride = env["ZCODE_BRIDGE_ZCODE_CJS"]?.trim();
    if (entryOverride) {
      this.#assertReadableFile(
        entryOverride,
        "ZCODE_BRIDGE_ZCODE_CJS is set but is not a readable file"
      );
      zcodeEntrypoint = entryOverride;
      explicitRuntime = true;
    } else {
      const install = discoverZCodeInstall(env, { requireBuiltin: !builtinEnv });
      if (!install.zcodeEntrypoint) {
        throw new BridgeError(
          "runtime_not_found",
          `zcode.cjs${builtinEnv ? "" : " with a same-install zcode-builtin.json"} was not found; searched: ` + (install.candidates.map((candidate) => `${candidate.root} (runtime: ${candidate.runtimeExists}, builtin: ${candidate.builtinExists})`).join(", ") || "(no installation roots available)")
        );
      }
      zcodeEntrypoint = install.zcodeEntrypoint;
    }
    let builtinConfigFile;
    let personalConfigFile;
    if (builtinEnv && personalEnv) {
      this.#validateBuiltinConfig(builtinEnv);
      this.#validatePersonalConfig(personalEnv);
      builtinConfigFile = builtinEnv;
      personalConfigFile = personalEnv;
    } else {
      if (builtinEnv) {
        this.#validateBuiltinConfig(builtinEnv);
        builtinConfigFile = builtinEnv;
      } else if (explicitRuntime) {
        const derived2 = builtinConfigForRuntime(zcodeEntrypoint);
        if (!isReadableFile(derived2)) {
          throw new BridgeError(
            "provider_config_missing",
            `ZCODE_BUILTIN_PROVIDER_CONFIG_FILE is not set and the builtin config was not found next to the configured runtime; expected: ${derived2}`
          );
        }
        this.#validateBuiltinConfig(derived2);
        builtinConfigFile = derived2;
      } else {
        const install = discoverZCodeInstall(env, { requireBuiltin: true });
        if (!install.builtinConfigFile) {
          throw new BridgeError(
            "provider_config_missing",
            "ZCODE_BUILTIN_PROVIDER_CONFIG_FILE is not set and no builtin provider config was found in the ZCode installation; searched: " + (install.candidates.map((candidate) => `${candidate.root} (runtime: ${candidate.runtimeExists}, builtin: ${candidate.builtinExists})`).join(", ") || "(no installation roots available)")
          );
        }
        this.#validateBuiltinConfig(install.builtinConfigFile);
        builtinConfigFile = install.builtinConfigFile;
      }
      if (personalEnv) {
        this.#validatePersonalConfig(personalEnv);
        personalConfigFile = personalEnv;
      } else {
        const candidates = zcodeHome ? [path6.join(zcodeHome, "v2", "provider_config.json")] : [
          explicitDataBaseDir,
          data.configuredDataBaseDir,
          data.userHome
        ].filter((base) => Boolean(base)).filter((base, index, values) => values.indexOf(base) === index).map((base) => path6.join(base, ".zcode", "v2", "provider_config.json"));
        const existing = candidates.filter((candidate) => existsSync2(candidate));
        if (existing.length === 0) {
          throw new BridgeError(
            "provider_config_missing",
            "ZCODE_PERSONAL_PROVIDER_CONFIG_FILE is not set and no personal provider config exists at any of: " + candidates.join(", ")
          );
        }
        let accepted = null;
        let lastError = null;
        for (const candidate of existing) {
          try {
            this.#validatePersonalConfig(candidate);
            accepted = candidate;
            break;
          } catch (error2) {
            lastError = error2 instanceof Error ? error2.message : String(error2);
          }
        }
        if (!accepted) {
          throw new BridgeError(
            "provider_config_invalid",
            `No usable personal provider config among: ${existing.join(", ")}; last validation failure: ${lastError ?? "unknown"}`
          );
        }
        personalConfigFile = accepted;
      }
    }
    if (zcodeHome && !samePath(personalConfigFile, path6.join(zcodeHome, "v2", "provider_config.json"))) {
      throw new BridgeError(
        "provider_config_invalid",
        `ZCODE_PERSONAL_PROVIDER_CONFIG_FILE must be ZCODE_HOME/v2/provider_config.json (${zcodeHome})`
      );
    }
    builtinConfigFile = await this.#selectBuiltinRegistry(
      builtinConfigFile,
      zcodeEntrypoint,
      personalConfigFile,
      env
    );
    const dataOverride = env["ZCODE_BRIDGE_DATA_DIR"]?.trim();
    let dataRoot;
    if (dataOverride) {
      if (!path6.isAbsolute(dataOverride)) {
        throw new Error(
          `ZCODE_BRIDGE_DATA_DIR must be an absolute path when set, got: ${dataOverride}`
        );
      }
      dataRoot = path6.normalize(dataOverride);
    } else {
      dataRoot = this.#packageRoot ?? findPackageRoot();
    }
    return {
      nodeExecutable,
      zcodeEntrypoint,
      providerBuiltinConfigFile: builtinConfigFile,
      providerPersonalConfigFile: personalConfigFile,
      zcodeDataRoot: data.zcodeDataDir,
      dataRoot
    };
  }
  #assertReadableFile(filePath, label) {
    if (!isReadableFile(filePath)) {
      throw new BridgeError("runtime_not_found", `${label}: ${filePath}`);
    }
  }
  /**
   * ADR-066: the installation's own bundled file is the default, not a pin.
   * Values left by older installers therefore follow the official runtime
   * registry; any other explicit path stays untouched.
   */
  async #selectBuiltinRegistry(builtinConfigFile, zcodeEntrypoint, personalConfigFile, env) {
    if (await isOfficialBuiltinRegistryPin(builtinConfigFile, builtinConfigForRuntime(zcodeEntrypoint))) {
      return builtinConfigFile;
    }
    const dataBaseDir = zcodeDataBaseDir(personalConfigFile);
    const appVersion = dataBaseDir ? officialDesktopAppVersion(zcodeEntrypoint) : null;
    const runtimePath = dataBaseDir && appVersion ? officialRuntimeRegistryPath({ dataBaseDir, appVersion, env }) : null;
    const selection = await selectOfficialBuiltinRegistry({ bundledPath: builtinConfigFile, runtimePath });
    try {
      this.#onBuiltinRegistrySelection?.(selection);
    } catch {
    }
    if (selection.source !== "runtime") return builtinConfigFile;
    this.#validateBuiltinConfig(selection.path);
    return selection.path;
  }
  /**
   * Structure validation only. The verified differential signal for the
   * CLI-created stub is an empty providerRules map (see docs/ZCODE_RUNTIME.md);
   * rejecting it implements "never silently select a known stub".
   */
  #validatePersonalConfig(filePath) {
    const parsed = this.#readJsonConfig(filePath, "personal provider config");
    const config2 = parsed["config"];
    if (!isPlainObject(config2)) {
      throw new BridgeError(
        "provider_config_invalid",
        `Personal provider config has no config object: ${filePath}`
      );
    }
    const providerConfigRules = config2["providerConfigRules"];
    const rules = isPlainObject(providerConfigRules) ? providerConfigRules["providerRules"] : void 0;
    if (!isNonEmptyCollection(rules)) {
      throw new BridgeError(
        "provider_config_invalid",
        `Personal provider config contains no provider rules (this matches the known CLI-created stub shape): ${filePath}`
      );
    }
  }
  #validateBuiltinConfig(filePath) {
    const parsed = this.#readJsonConfig(filePath, "builtin provider config");
    if (!isPlainObject(parsed["config"])) {
      throw new BridgeError(
        "provider_config_invalid",
        `Builtin provider config has no config object: ${filePath}`
      );
    }
  }
  #readJsonConfig(filePath, label) {
    if (!isReadableFile(filePath)) {
      throw new BridgeError("provider_config_missing", `${label} not found: ${filePath}`);
    }
    let text;
    try {
      text = readFileSync2(filePath, "utf8");
    } catch (error2) {
      throw new BridgeError(
        "provider_config_invalid",
        `${label} is not readable: ${filePath} (${errorText(error2)})`
      );
    }
    let parsed;
    try {
      parsed = JSON.parse(text);
    } catch (error2) {
      throw new BridgeError(
        "provider_config_invalid",
        `${label} is not valid JSON: ${filePath}`
      );
    }
    if (!isPlainObject(parsed)) {
      throw new BridgeError("provider_config_invalid", `${label} is not a JSON object: ${filePath}`);
    }
    return parsed;
  }
};
function resolveZcodeHome(env) {
  const configured = env["ZCODE_HOME"]?.trim();
  if (!configured) return null;
  if (!isAbsolutePathForPlatform(configured)) {
    throw new BridgeError("provider_config_invalid", "ZCODE_HOME must be an absolute path");
  }
  const resolved = path6.normalize(configured);
  if (path6.basename(resolved).toLowerCase() !== ".zcode") {
    throw new BridgeError(
      "provider_config_invalid",
      "ZCODE_HOME must name a .zcode directory so app-server can use the same data root"
    );
  }
  try {
    if (!statSync(resolved).isDirectory()) {
      throw new BridgeError("provider_config_invalid", `ZCODE_HOME is not a directory: ${resolved}`);
    }
  } catch (error2) {
    if (error2 instanceof BridgeError) throw error2;
    throw new BridgeError("provider_config_missing", `ZCODE_HOME directory does not exist: ${resolved}`);
  }
  return resolved;
}
function samePath(left, right) {
  const resolvedLeft = path6.resolve(left);
  const resolvedRight = path6.resolve(right);
  return process.platform === "win32" ? resolvedLeft.toLowerCase() === resolvedRight.toLowerCase() : resolvedLeft === resolvedRight;
}
function isReadableFile(filePath) {
  try {
    if (!existsSync2(filePath) || !statSync(filePath).isFile()) return false;
    accessSync(filePath);
    return true;
  } catch {
    return false;
  }
}
function findPackageRoot(startDir) {
  let current = startDir ?? path6.dirname(fileURLToPath(import.meta.url));
  for (let depth = 0; depth < 10; depth++) {
    if (existsSync2(path6.join(current, "package.json")) || existsSync2(path6.join(current, "plugin.json")) && existsSync2(path6.join(current, "dist")) && existsSync2(path6.join(current, "worker"))) {
      return current;
    }
    const parent = path6.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  throw new Error(
    `Cannot locate the Bridge package root (no package.json or installed plugin markers above ${startDir ?? "module directory"})`
  );
}
function isPlainObject(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
function isNonEmptyCollection(value) {
  if (Array.isArray(value)) return value.length > 0;
  if (isPlainObject(value)) return Object.keys(value).length > 0;
  return false;
}
function errorText(error2) {
  const message = error2 instanceof Error ? error2.message : String(error2);
  return message.length > 300 ? `${message.slice(0, 300)}\u2026` : message;
}

// src/runtime/sqlite-install-config.ts
var CONFIG_FILE = "authority.json";
var CONFIG_LIMIT = 8 * 1024;
var FRESH_SQLITE_DATABASE_FILE = "bridge.sqlite";
var SqliteInstallConfigurationError = class extends Error {
  constructor(code, message = code) {
    super(message);
    this.code = code;
    this.name = "SqliteInstallConfigurationError";
  }
  code;
};
function loadInstallAuthoritySelection(host) {
  validateHostProfile(host);
  const configPath = path7.join(host.settingsDirectory, CONFIG_FILE);
  try {
    const stat5 = lstatSync(configPath);
    if (!stat5.isFile() || stat5.isSymbolicLink()) throw new SqliteInstallConfigurationError("authority_config_not_regular_file");
    if (stat5.size > CONFIG_LIMIT) throw new SqliteInstallConfigurationError("authority_config_too_large");
    const parsed = JSON.parse(readFileSync3(configPath, "utf8"));
    if (!isRecord3(parsed)) throw new SqliteInstallConfigurationError("authority_config_invalid_shape");
    const keys = Object.keys(parsed).sort().join("|");
    if (parsed.schema_version !== 1) throw new SqliteInstallConfigurationError("authority_config_version_unsupported");
    if (parsed.authority === "json" && keys === "authority|schema_version") {
      throw new SqliteInstallConfigurationError("authority_config_json_unsupported");
    }
    if (parsed.authority !== "sqlite" || keys !== "authority|schema_version" && keys !== "authority|data_root|schema_version") {
      throw new SqliteInstallConfigurationError("authority_config_invalid_contract");
    }
    const configuredDataRoot = parsed.data_root === void 0 ? "" : parsed.data_root;
    if (typeof configuredDataRoot !== "string" || configuredDataRoot && !isLocalAbsolutePath(configuredDataRoot)) {
      throw new SqliteInstallConfigurationError("authority_config_data_root_invalid");
    }
    return { state: "sqlite", configPath, configuredDataRoot };
  } catch (error2) {
    if (error2.code === "ENOENT") return { state: "sqlite", configPath, configuredDataRoot: "" };
    if (error2 instanceof SqliteInstallConfigurationError) throw error2;
    throw new SqliteInstallConfigurationError("authority_config_unreadable_or_invalid", error2 instanceof Error ? error2.message : "authority config failed");
  }
}
function sqliteInstallationRoot(env) {
  const modulePath = fileURLToPath2(import.meta.url);
  const dist = path7.dirname(modulePath);
  const entry = path7.basename(modulePath);
  const pluginEntry = entry === "wait-task.mjs" || entry === "bridge.mjs" && env["ZCODE_BRIDGE_PLUGIN_MODE"] === "1";
  if (pluginEntry && path7.basename(dist) === "dist") {
    const pluginRoot = path7.dirname(dist);
    if (!existsSync3(path7.join(pluginRoot, ".codex-plugin", "plugin.json")) || !existsSync3(path7.join(pluginRoot, "launch-node24.mjs"))) {
      throw new SqliteInstallConfigurationError("sqlite_plugin_layout_invalid");
    }
    return pluginRoot;
  }
  return findPackageRoot();
}
function resolveSqliteStateDirectory(selection, env) {
  return resolveStateDirectory(selection, env, sqliteInstallationRoot(env), os.tmpdir());
}
function resolveStateDirectory(selection, env, packageRootValue, tempRootValue) {
  const appRoot = selection.configuredDataRoot || defaultDataRoot(env);
  if (!isLocalAbsolutePath(appRoot)) throw new SqliteInstallConfigurationError("sqlite_data_root_not_local_absolute");
  const normalizedRoot = path7.resolve(appRoot);
  const stateDirectory = path7.join(normalizedRoot, "state");
  const packageRoot = path7.resolve(packageRootValue);
  const tempRoot = path7.resolve(tempRootValue);
  if (within(packageRoot, normalizedRoot) || within(tempRoot, normalizedRoot) || within(packageRoot, stateDirectory) || within(tempRoot, stateDirectory)) {
    throw new SqliteInstallConfigurationError("sqlite_data_root_reserved_location");
  }
  return { dataRoot: stateDirectory, databaseFileName: FRESH_SQLITE_DATABASE_FILE };
}
function defaultDataRoot(env) {
  const localAppData = env["LOCALAPPDATA"]?.trim();
  if (!localAppData || !isLocalAbsolutePath(localAppData)) throw new SqliteInstallConfigurationError("local_app_data_unavailable");
  return path7.join(localAppData, "CodexZCodeBridge");
}
function isLocalAbsolutePath(value) {
  if (process.platform === "win32") return /^[A-Za-z]:\\/u.test(value) && path7.win32.isAbsolute(value) && !value.startsWith("\\\\");
  return path7.isAbsolute(value) && !value.startsWith("/proc/") && !value.startsWith("/sys/") && !value.startsWith("/dev/");
}
function within(root, candidate) {
  const relative = path7.relative(root, candidate);
  return relative === "" || relative !== ".." && !relative.startsWith(`..${path7.sep}`) && !path7.isAbsolute(relative);
}
function isRecord3(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value) && (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null);
}

// src/executor/lease.ts
import path8 from "node:path";
import { createHash as createHash2, randomUUID } from "node:crypto";
var LEASE_LIMIT_BYTES = 64 * 1024;
function authorityRootDigest(root) {
  return createHash2("sha256").update(path8.resolve(root).toLowerCase(), "utf8").digest("hex");
}

// src/executor/pipe.ts
function executorPipeName(root) {
  return `\\\\.\\pipe\\codex-zcode-bridge-executor-v1-${authorityRootDigest(root)}`;
}

// src/executor/control-client.ts
import net from "node:net";
import { randomUUID as randomUUID2 } from "node:crypto";

// src/executor/frame.ts
import { Transform } from "node:stream";

// node_modules/zod/v4/core/util.js
var util_exports = {};
__export(util_exports, {
  BIGINT_FORMAT_RANGES: () => BIGINT_FORMAT_RANGES,
  CONSTANT_CATCH: () => CONSTANT_CATCH,
  Class: () => Class,
  NUMBER_FORMAT_RANGES: () => NUMBER_FORMAT_RANGES,
  aborted: () => aborted,
  allowsEval: () => allowsEval,
  assert: () => assert,
  assertEqual: () => assertEqual,
  assertIs: () => assertIs,
  assertNever: () => assertNever,
  assertNotEqual: () => assertNotEqual,
  assignProp: () => assignProp,
  attachSchema: () => attachSchema,
  base64ToUint8Array: () => base64ToUint8Array,
  base64urlToUint8Array: () => base64urlToUint8Array,
  cached: () => cached,
  captureStackTrace: () => captureStackTrace,
  cleanEnum: () => cleanEnum,
  cleanRegex: () => cleanRegex,
  clone: () => clone,
  cloneDef: () => cloneDef,
  codePointLength: () => codePointLength,
  constantCatch: () => constantCatch,
  createTransparentProxy: () => createTransparentProxy,
  defineLazy: () => defineLazy,
  defineLazyInternal: () => defineLazyInternal,
  derived: () => derived,
  esc: () => esc,
  escapeRegex: () => escapeRegex,
  explicitlyAborted: () => explicitlyAborted,
  extend: () => extend,
  finalizeIssue: () => finalizeIssue,
  floatSafeRemainder: () => floatSafeRemainder,
  getElementAtPath: () => getElementAtPath,
  getEnumValues: () => getEnumValues,
  getLengthableOrigin: () => getLengthableOrigin,
  getParsedType: () => getParsedType,
  getSizableOrigin: () => getSizableOrigin,
  hexToUint8Array: () => hexToUint8Array,
  hide: () => hide,
  installLazyProp: () => installLazyProp,
  isObject: () => isObject,
  isPlainObject: () => isPlainObject2,
  issue: () => issue,
  joinValues: () => joinValues,
  jsonStringifyReplacer: () => jsonStringifyReplacer,
  members: () => members,
  merge: () => merge,
  mergeDefs: () => mergeDefs,
  normalizeParams: () => normalizeParams,
  nullish: () => nullish,
  numKeys: () => numKeys,
  objectClone: () => objectClone,
  omit: () => omit,
  optionalKeys: () => optionalKeys,
  own: () => own,
  parsedType: () => parsedType,
  partial: () => partial,
  pick: () => pick,
  prefixIssues: () => prefixIssues,
  primitiveTypes: () => primitiveTypes,
  promiseAllObject: () => promiseAllObject,
  propertyKeyTypes: () => propertyKeyTypes,
  randomString: () => randomString,
  rawShape: () => rawShape,
  required: () => required,
  safeExtend: () => safeExtend,
  shallowClone: () => shallowClone,
  slugify: () => slugify,
  stringifyPrimitive: () => stringifyPrimitive,
  toZod: () => toZod,
  uint8ArrayToBase64: () => uint8ArrayToBase64,
  uint8ArrayToBase64url: () => uint8ArrayToBase64url,
  uint8ArrayToHex: () => uint8ArrayToHex,
  unwrapMessage: () => unwrapMessage
});
function assertEqual(val) {
  return val;
}
function assertNotEqual(val) {
  return val;
}
function toZod() {
  return (schema) => schema;
}
function assertIs(_arg) {
}
function assertNever(_x) {
  throw new Error("Unexpected value in exhaustive check");
}
function assert(_) {
}
function getEnumValues(entries) {
  const numericValues = Object.values(entries).filter((v) => typeof v === "number");
  const values = Object.entries(entries).filter(([k, _]) => numericValues.indexOf(+k) === -1).map(([_, v]) => v);
  return values;
}
function joinValues(array2, separator = "|") {
  return array2.map((val) => stringifyPrimitive(val)).join(separator);
}
function jsonStringifyReplacer(_, value) {
  if (typeof value === "bigint")
    return value.toString();
  return value;
}
var Cached = class {
  constructor(getter) {
    this._getter = getter;
    this._value = void 0;
  }
  get value() {
    const getter = this._getter;
    if (getter !== void 0) {
      this._value = getter();
      this._getter = void 0;
    }
    return this._value;
  }
};
function cached(getter) {
  return new Cached(getter);
}
function nullish(input) {
  return input === null || input === void 0;
}
function cleanRegex(source) {
  const start = source.startsWith("^") ? 1 : 0;
  const end = source.endsWith("$") ? source.length - 1 : source.length;
  return source.slice(start, end);
}
function floatSafeRemainder(val, step) {
  const ratio = val / step;
  const roundedRatio = Math.round(ratio);
  const tolerance = 4 * Number.EPSILON * Math.max(Math.abs(ratio), 1);
  if (Math.abs(ratio - roundedRatio) < tolerance)
    return 0;
  return ratio - roundedRatio;
}
var EVALUATING = /* @__PURE__ */ Symbol("evaluating");
function defineLazy(object, key, getter) {
  let value = void 0;
  Object.defineProperty(object, key, {
    get() {
      if (value === EVALUATING) {
        return void 0;
      }
      if (value === void 0) {
        value = EVALUATING;
        value = getter();
      }
      return value;
    },
    set(v) {
      Object.defineProperty(object, key, {
        value: v
        // configurable: true,
      });
    },
    configurable: true
  });
}
function objectClone(obj) {
  return Object.create(Object.getPrototypeOf(obj), Object.getOwnPropertyDescriptors(obj));
}
function assignProp(target, prop, value) {
  Object.defineProperty(target, prop, {
    value,
    writable: true,
    enumerable: true,
    configurable: true
  });
}
function rawShape(def) {
  const desc = Object.getOwnPropertyDescriptor(def, "shape");
  return desc?.get ? desc.get.raw : desc?.value;
}
function sourceShape(schema) {
  return rawShape(schema._zod.def) ?? schema._zod.def.shape;
}
function deferProp(target, key, getter) {
  Object.defineProperty(target, key, {
    get() {
      const value = getter();
      assignProp(this, key, value);
      return value;
    },
    enumerable: true,
    configurable: true
  });
}
function putProp(target, key, value) {
  if (key in target)
    assignProp(target, key, value);
  else
    target[key] = value;
}
function mirrorShape(target, source, keys, wrap) {
  const raw = sourceShape(source);
  for (const key of keys) {
    const desc = Object.getOwnPropertyDescriptor(raw, key);
    if (!desc.enumerable)
      continue;
    if (desc.get) {
      deferProp(target, key, () => {
        const value = source._zod.def.shape[key];
        return wrap ? wrap(value, key) : value;
      });
    } else
      putProp(target, key, wrap ? wrap(desc.value, key) : desc.value);
  }
}
function mirrorProps(target, source) {
  for (const key of Reflect.ownKeys(source)) {
    const desc = Object.getOwnPropertyDescriptor(source, key);
    if (!desc.enumerable)
      continue;
    if (desc.get)
      deferProp(target, key, () => source[key]);
    else
      putProp(target, key, desc.value);
  }
}
function mergeDefs(...defs) {
  const mergedDescriptors = {};
  for (const def of defs) {
    const descriptors = Object.getOwnPropertyDescriptors(def);
    Object.assign(mergedDescriptors, descriptors);
  }
  return Object.defineProperties({}, mergedDescriptors);
}
function cloneDef(schema) {
  return mergeDefs(schema._zod.def);
}
function getElementAtPath(obj, path27) {
  if (!path27)
    return obj;
  return path27.reduce((acc, key) => acc?.[key], obj);
}
function promiseAllObject(promisesObj) {
  const keys = Object.keys(promisesObj);
  const promises = keys.map((key) => promisesObj[key]);
  return Promise.all(promises).then((results) => {
    const resolvedObj = {};
    for (let i = 0; i < keys.length; i++) {
      resolvedObj[keys[i]] = results[i];
    }
    return resolvedObj;
  });
}
function randomString(length = 10) {
  const chars = "abcdefghijklmnopqrstuvwxyz";
  let str = "";
  for (let i = 0; i < length; i++) {
    str += chars[Math.floor(Math.random() * chars.length)];
  }
  return str;
}
function esc(str) {
  return JSON.stringify(str);
}
function slugify(input) {
  return input.toLowerCase().trim().replace(/[^\w\s-]/g, "").replace(/[\s_-]+/g, "-").replace(/^-+|-+$/g, "");
}
var captureStackTrace = "captureStackTrace" in Error ? Error.captureStackTrace : (..._args) => {
};
function isObject(data) {
  return typeof data === "object" && data !== null && !Array.isArray(data);
}
var allowsEval = /* @__PURE__ */ cached(() => {
  if (globalConfig.jitless) {
    return false;
  }
  if (typeof navigator !== "undefined" && navigator?.userAgent?.includes("Cloudflare")) {
    return false;
  }
  try {
    const F = Function;
    new F("");
    return true;
  } catch (_) {
    return false;
  }
});
function isPlainObject2(o) {
  if (isObject(o) === false)
    return false;
  const ctor = o.constructor;
  if (ctor === void 0)
    return true;
  if (typeof ctor !== "function")
    return true;
  const prot = ctor.prototype;
  if (isObject(prot) === false)
    return false;
  if (Object.prototype.hasOwnProperty.call(prot, "isPrototypeOf") === false) {
    return false;
  }
  return true;
}
function shallowClone(o) {
  if (isPlainObject2(o))
    return { ...o };
  if (Array.isArray(o))
    return [...o];
  if (o instanceof Map)
    return new Map(o);
  if (o instanceof Set)
    return new Set(o);
  return o;
}
function numKeys(data) {
  let keyCount = 0;
  for (const key in data) {
    if (Object.prototype.hasOwnProperty.call(data, key)) {
      keyCount++;
    }
  }
  return keyCount;
}
var getParsedType = (data) => {
  const t = typeof data;
  switch (t) {
    case "undefined":
      return "undefined";
    case "string":
      return "string";
    case "number":
      return Number.isNaN(data) ? "nan" : "number";
    case "boolean":
      return "boolean";
    case "function":
      return "function";
    case "bigint":
      return "bigint";
    case "symbol":
      return "symbol";
    case "object":
      if (Array.isArray(data)) {
        return "array";
      }
      if (data === null) {
        return "null";
      }
      if (data.then && typeof data.then === "function" && data.catch && typeof data.catch === "function") {
        return "promise";
      }
      if (typeof Map !== "undefined" && data instanceof Map) {
        return "map";
      }
      if (typeof Set !== "undefined" && data instanceof Set) {
        return "set";
      }
      if (typeof Date !== "undefined" && data instanceof Date) {
        return "date";
      }
      if (typeof File !== "undefined" && data instanceof File) {
        return "file";
      }
      return "object";
    default:
      throw new Error(`Unknown data type: ${t}`);
  }
};
var propertyKeyTypes = /* @__PURE__ */ new Set(["string", "number", "symbol"]);
var primitiveTypes = /* @__PURE__ */ new Set([
  "string",
  "number",
  "bigint",
  "boolean",
  "symbol",
  "undefined"
]);
function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
function clone(inst, def, params) {
  const cl = new inst._zod.constr(def ?? inst._zod.def);
  if (!def || params?.parent)
    cl._zod.parent = inst;
  return cl;
}
function normalizeParams(_params) {
  const params = _params;
  if (!params)
    return {};
  if (typeof params === "string")
    return { error: () => params };
  if (params?.message !== void 0) {
    if (params?.error !== void 0)
      throw new Error("Cannot specify both `message` and `error` params");
    params.error = params.message;
  }
  delete params.message;
  if (typeof params.error === "string")
    return { ...params, error: () => params.error };
  return params;
}
function createTransparentProxy(getter) {
  let target;
  return new Proxy({}, {
    get(_, prop, receiver) {
      target ?? (target = getter());
      return Reflect.get(target, prop, receiver);
    },
    set(_, prop, value, receiver) {
      target ?? (target = getter());
      return Reflect.set(target, prop, value, receiver);
    },
    has(_, prop) {
      target ?? (target = getter());
      return Reflect.has(target, prop);
    },
    deleteProperty(_, prop) {
      target ?? (target = getter());
      return Reflect.deleteProperty(target, prop);
    },
    ownKeys(_) {
      target ?? (target = getter());
      return Reflect.ownKeys(target);
    },
    getOwnPropertyDescriptor(_, prop) {
      target ?? (target = getter());
      return Reflect.getOwnPropertyDescriptor(target, prop);
    },
    defineProperty(_, prop, descriptor) {
      target ?? (target = getter());
      return Reflect.defineProperty(target, prop, descriptor);
    }
  });
}
function stringifyPrimitive(value) {
  if (typeof value === "bigint")
    return value.toString() + "n";
  if (typeof value === "string")
    return `"${value}"`;
  return `${value}`;
}
function optionalKeys(shape) {
  return Object.keys(shape).filter((k) => {
    return shape[k]._zod.optin !== void 0 && shape[k]._zod.optout === "optional";
  });
}
var NUMBER_FORMAT_RANGES = /* @__PURE__ */ (() => ({
  safeint: [Number.MIN_SAFE_INTEGER, Number.MAX_SAFE_INTEGER],
  int32: [-2147483648, 2147483647],
  uint32: [0, 4294967295],
  float32: [-34028234663852886e22, 34028234663852886e22],
  float64: [-Number.MAX_VALUE, Number.MAX_VALUE]
}))();
var BIGINT_FORMAT_RANGES = {
  int64: [/* @__PURE__ */ BigInt("-9223372036854775808"), /* @__PURE__ */ BigInt("9223372036854775807")],
  uint64: [/* @__PURE__ */ BigInt(0), /* @__PURE__ */ BigInt("18446744073709551615")]
};
function pick(schema, mask) {
  const currDef = schema._zod.def;
  const checks = currDef.checks;
  const hasChecks = checks && checks.length > 0;
  if (hasChecks) {
    throw new Error(".pick() cannot be used on object schemas containing refinements");
  }
  const newShape = {};
  mirrorShape(newShape, schema, maskedKeys(schema, mask));
  return clone(schema, mergeDefs(currDef, { shape: newShape, checks: [] }));
}
function maskedKeys(schema, mask) {
  const raw = sourceShape(schema);
  const keys = [];
  for (const key of Reflect.ownKeys(mask)) {
    if (!Object.getOwnPropertyDescriptor(raw, key)?.enumerable) {
      throw new Error(`Unrecognized key: "${String(key)}"`);
    }
    if (mask[key])
      keys.push(key);
  }
  return keys;
}
function omit(schema, mask) {
  const currDef = schema._zod.def;
  const checks = currDef.checks;
  const hasChecks = checks && checks.length > 0;
  if (hasChecks) {
    throw new Error(".omit() cannot be used on object schemas containing refinements");
  }
  const omitted = new Set(maskedKeys(schema, mask));
  const newShape = {};
  mirrorShape(newShape, schema, Reflect.ownKeys(sourceShape(schema)).filter((key) => !omitted.has(key)));
  return clone(schema, mergeDefs(currDef, { shape: newShape, checks: [] }));
}
function extend(schema, shape) {
  if (!isPlainObject2(shape)) {
    throw new Error("Invalid input to extend: expected a plain object");
  }
  const checks = schema._zod.def.checks;
  const hasChecks = checks && checks.length > 0;
  if (hasChecks) {
    const existingShape = sourceShape(schema);
    for (const key of Reflect.ownKeys(shape)) {
      if (Object.getOwnPropertyDescriptor(existingShape, key) !== void 0) {
        throw new Error("Cannot overwrite keys on object schemas containing refinements. Use `.safeExtend()` instead.");
      }
    }
  }
  return clone(schema, mergeDefs(schema._zod.def, { shape: extended(schema, shape) }));
}
function extended(schema, shape) {
  const newShape = {};
  mirrorShape(newShape, schema, Reflect.ownKeys(sourceShape(schema)));
  mirrorProps(newShape, shape);
  return newShape;
}
function safeExtend(schema, shape) {
  if (!isPlainObject2(shape)) {
    throw new Error("Invalid input to safeExtend: expected a plain object");
  }
  return clone(schema, mergeDefs(schema._zod.def, { shape: extended(schema, shape) }));
}
function merge(a, b) {
  if (!b?._zod?.def) {
    throw new Error("Invalid input to merge: expected an object schema. To merge a plain shape, use `.extend()`.");
  }
  if (a._zod.def.checks?.length) {
    throw new Error(".merge() cannot be used on object schemas containing refinements. Use .safeExtend() instead.");
  }
  const newShape = {};
  mirrorShape(newShape, a, Reflect.ownKeys(sourceShape(a)));
  mirrorShape(newShape, b, Reflect.ownKeys(sourceShape(b)));
  const def = mergeDefs(a._zod.def, {
    shape: newShape,
    get catchall() {
      return b._zod.def.catchall;
    },
    checks: b._zod.def.checks ?? []
  });
  return clone(a, def);
}
function partial(Class2, schema, mask, name = "partial") {
  const currDef = schema._zod.def;
  const checks = currDef.checks;
  const hasChecks = checks && checks.length > 0;
  if (hasChecks) {
    throw new Error(`.${name}() cannot be used on object schemas containing refinements`);
  }
  const selected = mask ? new Set(maskedKeys(schema, mask)) : void 0;
  const newShape = {};
  mirrorShape(newShape, schema, Reflect.ownKeys(sourceShape(schema)), Class2 && ((value, key) => selected && !selected.has(key) ? value : new Class2({ type: "optional", innerType: value })));
  return clone(schema, mergeDefs(schema._zod.def, { shape: newShape, checks: [] }));
}
function required(Class2, schema, mask) {
  const selected = mask ? new Set(maskedKeys(schema, mask)) : void 0;
  const newShape = {};
  mirrorShape(newShape, schema, Reflect.ownKeys(sourceShape(schema)), (value, key) => (
    // overwrite with non-optional
    selected && !selected.has(key) ? value : new Class2({ type: "nonoptional", innerType: value })
  ));
  return clone(schema, mergeDefs(schema._zod.def, { shape: newShape }));
}
function aborted(x, startIndex = 0) {
  if (x.aborted === true)
    return true;
  for (let i = startIndex; i < x.issues.length; i++) {
    if (x.issues[i]?.continue !== true) {
      return true;
    }
  }
  return false;
}
function explicitlyAborted(x, startIndex = 0) {
  if (x.aborted === true)
    return true;
  for (let i = startIndex; i < x.issues.length; i++) {
    if (x.issues[i]?.continue === false) {
      return true;
    }
  }
  return false;
}
function prefixIssues(path27, issues) {
  return issues.map((iss) => {
    var _a3;
    (_a3 = iss).path ?? (_a3.path = []);
    iss.path.unshift(path27);
    return iss;
  });
}
function unwrapMessage(message) {
  return typeof message === "string" ? message : message?.message;
}
function attachSchema(issues, start, inst) {
  var _a3;
  for (let i = start; i < issues.length; i++) {
    (_a3 = issues[i]).schema ?? (_a3.schema = inst);
  }
}
function finalizeIssue(iss, ctx, config2) {
  var _a3;
  const traits = iss.inst?._zod?.traits;
  if (traits?.has("$ZodType")) {
    if (traits.has("$ZodCheck"))
      (_a3 = iss).schema ?? (_a3.schema = iss.inst);
    else
      iss.schema = iss.inst;
  }
  const schemaError = iss.schema !== iss.inst ? iss.schema?._zod.def?.error : void 0;
  const message = iss.message ? iss.message : unwrapMessage(iss.inst?._zod.def?.error?.(iss)) ?? unwrapMessage(schemaError?.(iss)) ?? unwrapMessage(ctx?.error?.(iss)) ?? unwrapMessage(config2.customError?.(iss)) ?? unwrapMessage(config2.localeError?.(iss)) ?? "Invalid input";
  const full = {};
  for (const k of Object.keys(iss)) {
    if (k === "inst" || k === "schema" || k === "continue" || k === "input" || k === "__proto__")
      continue;
    full[k] = iss[k];
  }
  full.path ?? (full.path = []);
  full.message = message;
  if (ctx?.reportInput) {
    full.input = iss.input;
  }
  return full;
}
function getSizableOrigin(input) {
  if (input instanceof Set)
    return "set";
  if (input instanceof Map)
    return "map";
  if (input instanceof File)
    return "file";
  return "unknown";
}
var highSurrogate = /[\uD800-\uDBFF]/;
function codePointLength(str) {
  const units = str.length;
  if (!highSurrogate.test(str))
    return units;
  let count = units;
  for (let i = 0; i < units - 1; i++) {
    if ((str.charCodeAt(i) & 64512) === 55296 && (str.charCodeAt(i + 1) & 64512) === 56320) {
      count--;
      i++;
    }
  }
  return count;
}
function getLengthableOrigin(input) {
  if (Array.isArray(input))
    return "array";
  if (typeof input === "string")
    return "string";
  return "unknown";
}
function parsedType(data) {
  const t = typeof data;
  switch (t) {
    case "number": {
      return Number.isNaN(data) ? "nan" : "number";
    }
    case "object": {
      if (data === null) {
        return "null";
      }
      if (Array.isArray(data)) {
        return "array";
      }
      const obj = data;
      if (obj && Object.getPrototypeOf(obj) !== Object.prototype && "constructor" in obj && obj.constructor) {
        return obj.constructor.name;
      }
    }
  }
  return t;
}
function issue(...args) {
  const [iss, input, inst] = args;
  if (typeof iss === "string") {
    return {
      message: iss,
      code: "custom",
      input,
      inst
    };
  }
  return { ...iss };
}
function cleanEnum(obj) {
  return Object.entries(obj).filter(([k, _]) => {
    return Number.isNaN(Number.parseInt(k, 10));
  }).map((el) => el[1]);
}
function base64ToUint8Array(base642) {
  const binaryString = atob(base642);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}
function uint8ArrayToBase64(bytes) {
  let binaryString = "";
  for (let i = 0; i < bytes.length; i++) {
    binaryString += String.fromCharCode(bytes[i]);
  }
  return btoa(binaryString);
}
function base64urlToUint8Array(base64url2) {
  const base642 = base64url2.replace(/-/g, "+").replace(/_/g, "/");
  const padding = "=".repeat((4 - base642.length % 4) % 4);
  return base64ToUint8Array(base642 + padding);
}
function uint8ArrayToBase64url(bytes) {
  return uint8ArrayToBase64(bytes).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
}
function hexToUint8Array(hex) {
  const cleanHex = hex.replace(/^0x/, "");
  if (cleanHex.length % 2 !== 0) {
    throw new Error("Invalid hex string length");
  }
  const bytes = new Uint8Array(cleanHex.length / 2);
  for (let i = 0; i < cleanHex.length; i += 2) {
    bytes[i / 2] = Number.parseInt(cleanHex.slice(i, i + 2), 16);
  }
  return bytes;
}
function uint8ArrayToHex(bytes) {
  return Array.from(bytes).map((b) => b.toString(16).padStart(2, "0")).join("");
}
var Class = class {
  constructor(..._args) {
  }
};
function members(proto, table) {
  for (const key in table) {
    const desc = Object.getOwnPropertyDescriptor(table, key);
    if (desc.get)
      Object.defineProperty(proto, key, { ...desc, enumerable: false });
    else
      defineBound(proto, key, desc.value);
  }
}
function own(inst, key, value, enumerable = true) {
  Object.defineProperty(inst, key, { configurable: true, writable: true, enumerable, value });
  return value;
}
function hide(inst, key, value) {
  return own(inst, key, value, false);
}
// @__NO_SIDE_EFFECTS__
function derived(computes, table) {
  for (const key in computes) {
    const compute = computes[key];
    Object.defineProperty(table, key, {
      configurable: true,
      enumerable: true,
      get() {
        return own(this, key, compute(this));
      },
      set(value) {
        own(this, key, value);
      }
    });
  }
  return table;
}
function defineBound(proto, key, fn) {
  Object.defineProperty(proto, key, {
    configurable: true,
    get() {
      return this == null ? fn : own(this, key, fn.bind(this));
    },
    set(value) {
      own(this, key, value);
    }
  });
}
function claim(inst, sentinel) {
  const proto = Object.getPrototypeOf(inst);
  return sentinel in proto ? void 0 : proto;
}
var installing;
var broke = false;
var breaker = {
  configurable: true,
  get() {
    broke = true;
    return void 0;
  }
};
function defineLazyInternal(inst, key, compute) {
  const proto = Object.getPrototypeOf(inst._zod);
  if (key in proto && installing !== inst._zod) {
    installing = void 0;
    return;
  }
  installing = inst._zod;
  Object.defineProperty(proto, key, {
    configurable: true,
    get() {
      Object.defineProperty(this, key, breaker);
      const outer = broke;
      broke = false;
      try {
        const value = compute(this);
        if (broke)
          delete this[key];
        else
          Object.defineProperty(this, key, { configurable: true, writable: true, value });
        broke = broke || outer;
        return value;
      } catch (err) {
        delete this[key];
        broke = broke || outer;
        throw err;
      }
    },
    set(value) {
      Object.defineProperty(this, key, { configurable: true, writable: true, value });
    }
  });
}
function installLazyProp(inst, key, make, enumerable) {
  const proto = claim(inst, key);
  if (!proto)
    return;
  Object.defineProperty(proto, key, {
    configurable: true,
    get() {
      const desc = { configurable: true, writable: true, enumerable, value: void 0 };
      Object.defineProperty(this, key, desc);
      desc.value = make(this);
      Object.defineProperty(this, key, desc);
      return desc.value;
    },
    set(value) {
      Object.defineProperty(this, key, { configurable: true, writable: true, enumerable, value });
    }
  });
}
var CONSTANT_CATCH = "~constantCatch";
function constantCatch(value) {
  const fn = () => value;
  fn[CONSTANT_CATCH] = true;
  return fn;
}

// node_modules/zod/v4/core/core.js
var _a;
var _zodDesc = { value: void 0, enumerable: false };
var _E = "captureStackTrace" in Error ? Error : null;
function newError(Definition) {
  const E = _E;
  if (E) {
    const saved = E.stackTraceLimit;
    if (typeof saved === "number") {
      try {
        E.stackTraceLimit = 0;
      } catch {
        _E = null;
        return new Definition();
      }
      try {
        return new Definition();
      } finally {
        E.stackTraceLimit = saved;
      }
    }
  }
  return new Definition();
}
// @__NO_SIDE_EFFECTS__
function $constructor(name, initializer3, proto, params) {
  const zodProto = {};
  function Internals(def) {
    this.def = def;
    this.constr = _;
    this.traits = /* @__PURE__ */ new Set();
  }
  Internals.prototype = zodProto;
  const protoMembers = proto;
  const initialized = protoMembers && /* @__PURE__ */ new WeakSet();
  function init(inst, def) {
    if (!inst._zod) {
      _zodDesc.value = new Internals(def);
      try {
        Object.defineProperty(inst, "_zod", _zodDesc);
      } finally {
        _zodDesc.value = void 0;
      }
    } else if (inst._zod.traits.has(name)) {
      return;
    }
    inst._zod.traits.add(name);
    initializer3(inst, def);
    if (initialized) {
      const own2 = Object.getPrototypeOf(inst);
      const ctorProto = inst._zod.constr.prototype;
      let up = own2;
      while (up && up !== ctorProto)
        up = Object.getPrototypeOf(up);
      const target = up ?? own2;
      if (!initialized.has(target)) {
        initialized.add(target);
        members(target, protoMembers);
      }
    }
    const proto2 = _.prototype;
    for (const k in proto2) {
      if (!Object.prototype.hasOwnProperty.call(proto2, k))
        continue;
      if (!(k in inst)) {
        inst[k] = proto2[k].bind(inst);
      }
    }
  }
  const Parent = params?.Parent ?? Object;
  class Definition extends Parent {
  }
  Object.defineProperty(Definition, "name", { value: name });
  function _(def) {
    const inst = params?.Parent ? newError(Definition) : this;
    init(inst, def);
    const deferred = inst._zod.deferred;
    if (deferred) {
      for (const fn of deferred) {
        fn();
      }
      inst._zod.deferred = void 0;
    }
    const pp = globalThis.__zod_globalConfig?.postProcessor;
    if (pp)
      pp(inst);
    return inst;
  }
  Object.defineProperty(_, "init", { value: init });
  Object.defineProperty(_, Symbol.hasInstance, {
    value: (inst) => {
      if (params?.Parent && inst instanceof params.Parent)
        return true;
      return inst?._zod?.traits?.has(name);
    }
  });
  Object.defineProperty(_, "name", { value: name });
  return _;
}
var $ZodAsyncError = class extends Error {
  constructor() {
    super(`Encountered Promise during synchronous parse. Use .parseAsync() instead.`);
  }
};
var $ZodEncodeError = class extends Error {
  constructor(name) {
    super(`Encountered unidirectional transform during encode: ${name}`);
    this.name = "ZodEncodeError";
  }
};
(_a = globalThis).__zod_globalConfig ?? (_a.__zod_globalConfig = {});
var globalConfig = globalThis.__zod_globalConfig;
function config(newConfig) {
  if (newConfig)
    Object.assign(globalConfig, newConfig);
  return globalConfig;
}

// node_modules/zod/v4/core/errors.js
function _getMessage() {
  const internals = this._zod;
  internals.message ?? (internals.message = JSON.stringify(internals.def, jsonStringifyReplacer, 2));
  return internals.message;
}
function _setMessage(value) {
  this._zod.message = value;
}
var _messageDesc = {
  get: _getMessage,
  set: _setMessage,
  enumerable: true,
  configurable: true
};
var _issuesDesc = { value: void 0, enumerable: false };
var _installedToString = /* @__PURE__ */ new WeakSet([Object.prototype, Error.prototype]);
var initializer = (inst, def) => {
  inst.name = "$ZodError";
  _issuesDesc.value = def;
  Object.defineProperty(inst, "issues", _issuesDesc);
  _issuesDesc.value = void 0;
  Object.defineProperty(inst, "message", _messageDesc);
  const proto = Object.getPrototypeOf(inst);
  if (!_installedToString.has(proto)) {
    _installedToString.add(proto);
    Object.defineProperty(proto, "toString", {
      configurable: true,
      enumerable: false,
      get() {
        const value = () => this.message;
        Object.defineProperty(this, "toString", { value, configurable: true, writable: true });
        return value;
      },
      set(value) {
        Object.defineProperty(this, "toString", { value, configurable: true, writable: true });
      }
    });
  }
};
var $ZodError = $constructor("$ZodError", initializer);
var $ZodRealError = $constructor("$ZodError", initializer, void 0, {
  Parent: Error
});
function node(obj, key, make) {
  if (!Object.prototype.hasOwnProperty.call(obj, key)) {
    if (key === "__proto__") {
      Object.defineProperty(obj, key, { value: make(), writable: true, enumerable: true, configurable: true });
    } else {
      obj[key] = make();
    }
  }
  return obj[key];
}
function flattenError(error2, mapper = (issue2) => issue2.message) {
  const fieldErrors = {};
  const formErrors = [];
  for (const sub of error2.issues) {
    if (sub.path.length > 0) {
      node(fieldErrors, sub.path[0], () => []).push(mapper(sub));
    } else {
      formErrors.push(mapper(sub));
    }
  }
  return { formErrors, fieldErrors };
}
function formatError(error2, mapper = (issue2) => issue2.message) {
  const fieldErrors = { _errors: [] };
  const processError = (error3, path27 = []) => {
    for (const issue2 of error3.issues) {
      if (issue2.code === "invalid_union" && issue2.errors.length) {
        issue2.errors.map((issues) => processError({ issues }, [...path27, ...issue2.path]));
      } else if (issue2.code === "invalid_key") {
        processError({ issues: issue2.issues }, [...path27, ...issue2.path]);
      } else if (issue2.code === "invalid_element") {
        processError({ issues: issue2.issues }, [...path27, ...issue2.path]);
      } else {
        const fullpath = [...path27, ...issue2.path];
        if (fullpath.length === 0) {
          fieldErrors._errors.push(mapper(issue2));
        } else {
          let curr = fieldErrors;
          let i = 0;
          while (i < fullpath.length) {
            const el = fullpath[i];
            const terminal = i === fullpath.length - 1;
            if (el === "_errors") {
              if (terminal)
                curr._errors.push(mapper(issue2));
              i++;
              continue;
            }
            if (!Object.prototype.hasOwnProperty.call(curr, el)) {
              Object.defineProperty(curr, el, {
                value: { _errors: [] },
                enumerable: true,
                writable: true,
                configurable: true
              });
            }
            const node2 = curr[el];
            if (terminal) {
              node2._errors.push(mapper(issue2));
            }
            curr = node2;
            i++;
          }
        }
      }
    }
  };
  processError(error2);
  return fieldErrors;
}

// node_modules/zod/v4/core/parse.js
function finalizeParams(callee, params) {
  return { callee: params?.callee ?? callee, Err: params?.Err };
}
var _parse = (_Err) => {
  const fn = (schema, value, _ctx, _params) => {
    const ctx = _ctx ? { ..._ctx, async: false } : { async: false };
    const result = schema._zod.run({ value, issues: [] }, ctx);
    if (result instanceof Promise) {
      throw new $ZodAsyncError();
    }
    if (result.issues.length) {
      const e = new (_params?.Err ?? _Err)(result.issues.map((iss) => finalizeIssue(iss, ctx, config())));
      captureStackTrace(e, _params?.callee ?? fn);
      throw e;
    }
    return result.value;
  };
  return fn;
};
var _parseAsync = (_Err) => {
  const fn = async (schema, value, _ctx, params) => {
    const ctx = _ctx ? { ..._ctx, async: true } : { async: true };
    let result = schema._zod.run({ value, issues: [] }, ctx);
    if (result instanceof Promise)
      result = await result;
    if (result.issues.length) {
      const e = new (params?.Err ?? _Err)(result.issues.map((iss) => finalizeIssue(iss, ctx, config())));
      captureStackTrace(e, params?.callee ?? fn);
      throw e;
    }
    return result.value;
  };
  return fn;
};
var _safeParse = (_Err) => (schema, value, _ctx) => {
  const ctx = _ctx ? { ..._ctx, async: false } : { async: false };
  const result = schema._zod.run({ value, issues: [] }, ctx);
  if (result instanceof Promise) {
    throw new $ZodAsyncError();
  }
  return result.issues.length ? failure(_Err, result.issues, ctx) : { success: true, data: result.value };
};
function failure(Err, issues, ctx) {
  let error2;
  return {
    success: false,
    get error() {
      if (!error2) {
        error2 = new Err(issues.map((iss) => finalizeIssue(iss, ctx, config())));
        issues = void 0;
        ctx = void 0;
      }
      return error2;
    },
    set error(e) {
      error2 = e;
      issues = void 0;
      ctx = void 0;
    }
  };
}
var _safeParseAsync = (_Err) => async (schema, value, _ctx) => {
  const ctx = _ctx ? { ..._ctx, async: true } : { async: true };
  let result = schema._zod.run({ value, issues: [] }, ctx);
  if (result instanceof Promise)
    result = await result;
  return result.issues.length ? failure(_Err, result.issues, ctx) : { success: true, data: result.value };
};
var COMPILE_INVALID = /* @__PURE__ */ Symbol.for("zod.compile.invalid");
var COMPILE_FALLBACK = /* @__PURE__ */ Symbol.for("zod.compile.fallback");
var validate = ((schema, value, _ctx) => {
  const validator = schema._zod.bag.validator;
  if (validator !== void 0) {
    if (validator(value) !== COMPILE_INVALID)
      return true;
    if (validator.definite === true && _ctx === void 0)
      return false;
  }
  return validateFallback(schema, value, _ctx);
});
function validateFallback(schema, value, _ctx) {
  const ctx = _ctx ? { ..._ctx, async: false, abortEarly: true } : { async: false, abortEarly: true };
  const fallbackRun = schema._zod.bag.fallbackRun;
  let result;
  if (fallbackRun) {
    ctx[COMPILE_FALLBACK] = true;
    result = fallbackRun({ value, issues: [] }, ctx);
  } else {
    result = schema._zod.run({ value, issues: [] }, ctx);
  }
  if (result instanceof Promise) {
    throw new $ZodAsyncError();
  }
  return result.issues.length === 0;
}
var validateAsync = async (schema, value, _ctx) => {
  const ctx = _ctx ? { ..._ctx, async: true, abortEarly: true } : { async: true, abortEarly: true };
  let result = schema._zod.run({ value, issues: [] }, ctx);
  if (result instanceof Promise)
    result = await result;
  return result.issues.length === 0;
};
var _encode = (_Err) => {
  const parse2 = _parse(_Err);
  const fn = (schema, value, _ctx, _params) => {
    const ctx = _ctx ? { ..._ctx, direction: "backward" } : { direction: "backward" };
    return parse2(schema, value, ctx, finalizeParams(fn, _params));
  };
  return fn;
};
var _decode = (_Err) => {
  const parse2 = _parse(_Err);
  const fn = (schema, value, _ctx, _params) => {
    return parse2(schema, value, _ctx, finalizeParams(fn, _params));
  };
  return fn;
};
var _encodeAsync = (_Err) => {
  const parseAsync2 = _parseAsync(_Err);
  const fn = async (schema, value, _ctx, _params) => {
    const ctx = _ctx ? { ..._ctx, direction: "backward" } : { direction: "backward" };
    return await parseAsync2(schema, value, ctx, finalizeParams(fn, _params));
  };
  return fn;
};
var _decodeAsync = (_Err) => {
  const parseAsync2 = _parseAsync(_Err);
  const fn = async (schema, value, _ctx, _params) => {
    return await parseAsync2(schema, value, _ctx, finalizeParams(fn, _params));
  };
  return fn;
};
var _safeEncode = (_Err) => (schema, value, _ctx) => {
  const ctx = _ctx ? { ..._ctx, direction: "backward" } : { direction: "backward" };
  return _safeParse(_Err)(schema, value, ctx);
};
var _safeDecode = (_Err) => (schema, value, _ctx) => {
  return _safeParse(_Err)(schema, value, _ctx);
};
var _safeEncodeAsync = (_Err) => async (schema, value, _ctx) => {
  const ctx = _ctx ? { ..._ctx, direction: "backward" } : { direction: "backward" };
  return _safeParseAsync(_Err)(schema, value, ctx);
};
var _safeDecodeAsync = (_Err) => async (schema, value, _ctx) => {
  return _safeParseAsync(_Err)(schema, value, _ctx);
};

// node_modules/zod/v4/core/regexes.js
var cuid = /^[cC][0-9a-z]{6,}$/;
var cuid2 = /^[0-9a-z]+$/;
var ulid = /^[0-7][0-9A-HJKMNP-TV-Za-hjkmnp-tv-z]{25}$/;
var xid = /^[0-9a-vA-V]{20}$/;
var ksuid = /^[A-Za-z0-9]{27}$/;
var nanoid = /^[a-zA-Z0-9_-]{21}$/;
function nanoidOfLength(length) {
  return new RegExp(`^[a-zA-Z0-9_-]{${length}}$`);
}
var duration = /^P(?:(\d+W)|(?!.*W)(?=\d|T\d)(\d+Y)?(\d+M)?(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+([.,]\d+)?S)?)?)$/;
var guid = /^([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$/;
var uuid = (version2) => {
  if (!version2)
    return /^([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}|00000000-0000-0000-0000-000000000000|ffffffff-ffff-ffff-ffff-ffffffffffff)$/;
  return new RegExp(`^([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-${version2}[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12})$`);
};
var email = /^(?:[A-Za-z0-9_'+\-]+\.)*[A-Za-z0-9_'+\-]*[A-Za-z0-9_+-]@(?:[A-Za-z0-9][A-Za-z0-9\-]*\.)+[A-Za-z]{2,}$/;
var _emoji = `^(?=[\\s\\S]*[\\p{Extended_Pictographic}\\p{Regional_Indicator}\\u20E3])[\\p{Extended_Pictographic}\\p{Emoji_Component}]+$`;
function emoji() {
  return new RegExp(_emoji, "u");
}
var ipv4 = /^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])$/;
var ipv6 = /^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:))$/;
var cidrv4 = /^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\/([0-9]|[1-2][0-9]|3[0-2])$/;
var cidrv6 = /^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:))\/(12[0-8]|1[01][0-9]|[1-9]?[0-9])$/;
var base64 = /^$|^(?:[0-9a-zA-Z+/]{4})*(?:(?:[0-9a-zA-Z+/]{2}==)|(?:[0-9a-zA-Z+/]{3}=))?$/;
var base64url = /^(?:[A-Za-z0-9_-]{4})*(?:[A-Za-z0-9_-]{2,3})?$/;
var httpProtocol = /^https?$/;
var e164 = /^\+[1-9]\d{6,14}$/;
var dateSource = `(?:(?:\\d\\d[2468][048]|\\d\\d[13579][26]|\\d\\d0[48]|[02468][048]00|[13579][26]00)-02-29|\\d{4}-(?:(?:0[13578]|1[02])-(?:0[1-9]|[12]\\d|3[01])|(?:0[469]|11)-(?:0[1-9]|[12]\\d|30)|(?:02)-(?:0[1-9]|1\\d|2[0-8])))`;
function anchor(source) {
  return new RegExp(`^${source}$`);
}
var date = /* @__PURE__ */ anchor(dateSource);
function timeSource(args) {
  const hhmm = `(?:[01]\\d|2[0-3]):[0-5]\\d`;
  const regex = typeof args.precision === "number" ? args.precision === -1 ? `${hhmm}` : args.precision === 0 ? `${hhmm}:[0-5]\\d` : `${hhmm}:[0-5]\\d\\.\\d{${args.precision}}` : args.seconds ? `${hhmm}:[0-5]\\d(?:\\.\\d+)?` : `${hhmm}(?::[0-5]\\d(?:\\.\\d+)?)?`;
  return regex;
}
function time(args) {
  return new RegExp(`^${timeSource(args)}$`);
}
function datetime(args) {
  const opts = ["Z"];
  if (args.offset)
    opts.push(`([+-](?:[01]\\d|2[0-3]):[0-5]\\d)`);
  const qualified = `${timeSource({ precision: args.precision, seconds: true })}(?:${opts.join("|")})`;
  const timeRegex = args.local ? `${qualified}|${timeSource({ precision: args.precision })}` : qualified;
  return new RegExp(`^${dateSource}T(?:${timeRegex})$`);
}
var anyString = /^[\s\S]{0,}$/;
var integer = /^-?\d+$/;
var number = /^-?\d+(?:\.\d+)?$/;
var boolean = /^(?:true|false)$/i;
var lowercase = /^[^A-Z]*$/;
var uppercase = /^[^a-z]*$/;

// node_modules/zod/v4/core/checks.js
var $ZodCheck = /* @__PURE__ */ $constructor("$ZodCheck", (inst, def) => {
  var _a3;
  inst._zod ?? (inst._zod = {});
  inst._zod.def = def;
  (_a3 = inst._zod).onattach ?? (_a3.onattach = []);
});
var _whenHasLength = (payload) => {
  const val = payload.value;
  return !nullish(val) && val.length !== void 0;
};
var numericOriginMap = {
  number: "number",
  bigint: "bigint",
  object: "date"
};
var $ZodCheckLessThan = /* @__PURE__ */ $constructor("$ZodCheckLessThan", (inst, def) => {
  $ZodCheck.init(inst, def);
  const origin = numericOriginMap[typeof def.value];
  inst._zod.check = (payload) => {
    if (def.inclusive ? payload.value <= def.value : payload.value < def.value) {
      return;
    }
    payload.issues.push({
      origin: numericOriginMap[typeof payload.value] ?? origin,
      code: "too_big",
      maximum: typeof def.value === "object" ? def.value.getTime() : def.value,
      input: payload.value,
      inclusive: def.inclusive,
      inst,
      continue: !def.abort
    });
  };
});
var $ZodCheckGreaterThan = /* @__PURE__ */ $constructor("$ZodCheckGreaterThan", (inst, def) => {
  $ZodCheck.init(inst, def);
  const origin = numericOriginMap[typeof def.value];
  inst._zod.check = (payload) => {
    if (def.inclusive ? payload.value >= def.value : payload.value > def.value) {
      return;
    }
    payload.issues.push({
      origin: numericOriginMap[typeof payload.value] ?? origin,
      code: "too_small",
      minimum: typeof def.value === "object" ? def.value.getTime() : def.value,
      input: payload.value,
      inclusive: def.inclusive,
      inst,
      continue: !def.abort
    });
  };
});
var $ZodCheckMultipleOf = /* @__PURE__ */ $constructor("$ZodCheckMultipleOf", (inst, def) => {
  $ZodCheck.init(inst, def);
  inst._zod.check = (payload) => {
    if (typeof payload.value !== typeof def.value)
      throw new Error("Cannot mix number and bigint in multiple_of check.");
    const isMultiple = typeof payload.value === "bigint" ? (
      // `value % 0n` throws, and nothing is a multiple of zero — the number branch already fails this way via NaN
      def.value !== BigInt(0) && payload.value % def.value === BigInt(0)
    ) : floatSafeRemainder(payload.value, def.value) === 0;
    if (isMultiple)
      return;
    payload.issues.push({
      origin: typeof payload.value,
      code: "not_multiple_of",
      divisor: def.value,
      input: payload.value,
      inst,
      continue: !def.abort
    });
  };
});
var $ZodCheckNumberFormat = /* @__PURE__ */ $constructor("$ZodCheckNumberFormat", (inst, def) => {
  $ZodCheck.init(inst, def);
  def.format = def.format || "float64";
  const isInt = def.format?.includes("int");
  const origin = isInt ? "int" : "number";
  const [minimum, maximum] = NUMBER_FORMAT_RANGES[def.format];
  inst._zod.check = (payload) => {
    const input = payload.value;
    if (isInt) {
      if (!Number.isInteger(input)) {
        payload.issues.push({
          expected: origin,
          format: def.format,
          code: "invalid_type",
          continue: false,
          input,
          inst
        });
        return;
      }
      if (!Number.isSafeInteger(input)) {
        if (input > 0) {
          payload.issues.push({
            input,
            code: "too_big",
            maximum: Number.MAX_SAFE_INTEGER,
            note: "Integers must be within the safe integer range.",
            inst,
            origin,
            inclusive: true,
            continue: !def.abort
          });
        } else {
          payload.issues.push({
            input,
            code: "too_small",
            minimum: Number.MIN_SAFE_INTEGER,
            note: "Integers must be within the safe integer range.",
            inst,
            origin,
            inclusive: true,
            continue: !def.abort
          });
        }
        return;
      }
    }
    if (input < minimum) {
      payload.issues.push({
        origin: "number",
        input,
        code: "too_small",
        minimum,
        inclusive: true,
        inst,
        continue: !def.abort
      });
    }
    if (input > maximum) {
      payload.issues.push({
        origin: "number",
        input,
        code: "too_big",
        maximum,
        inclusive: true,
        inst,
        continue: !def.abort
      });
    }
  };
});
var $ZodCheckMaxLength = /* @__PURE__ */ $constructor("$ZodCheckMaxLength", (inst, def) => {
  var _a3;
  $ZodCheck.init(inst, def);
  (_a3 = inst._zod.def).when ?? (_a3.when = _whenHasLength);
  inst._zod.check = (payload) => {
    const input = payload.value;
    const units = input.length;
    const length = typeof input === "string" && units > def.maximum ? codePointLength(input) : units;
    if (length <= def.maximum)
      return;
    const origin = getLengthableOrigin(input);
    payload.issues.push({
      origin,
      code: "too_big",
      maximum: def.maximum,
      inclusive: true,
      input,
      inst,
      continue: !def.abort
    });
  };
});
var $ZodCheckMinLength = /* @__PURE__ */ $constructor("$ZodCheckMinLength", (inst, def) => {
  var _a3;
  $ZodCheck.init(inst, def);
  (_a3 = inst._zod.def).when ?? (_a3.when = _whenHasLength);
  inst._zod.check = (payload) => {
    const input = payload.value;
    const units = input.length;
    const length = typeof input === "string" && units >= def.minimum && units < def.minimum * 2 ? codePointLength(input) : units;
    if (length >= def.minimum)
      return;
    const origin = getLengthableOrigin(input);
    payload.issues.push({
      origin,
      code: "too_small",
      minimum: def.minimum,
      inclusive: true,
      input,
      inst,
      continue: !def.abort
    });
  };
});
var $ZodCheckLengthEquals = /* @__PURE__ */ $constructor("$ZodCheckLengthEquals", (inst, def) => {
  var _a3;
  $ZodCheck.init(inst, def);
  (_a3 = inst._zod.def).when ?? (_a3.when = _whenHasLength);
  inst._zod.check = (payload) => {
    const input = payload.value;
    const units = input.length;
    const length = typeof input === "string" && units >= def.length && units <= def.length * 2 ? codePointLength(input) : units;
    if (length === def.length)
      return;
    const origin = getLengthableOrigin(input);
    const tooBig = length > def.length;
    payload.issues.push({
      origin,
      ...tooBig ? { code: "too_big", maximum: def.length } : { code: "too_small", minimum: def.length },
      inclusive: true,
      exact: true,
      input: payload.value,
      inst,
      continue: !def.abort
    });
  };
});
var $ZodCheckStringFormat = /* @__PURE__ */ $constructor("$ZodCheckStringFormat", (inst, def) => {
  var _a3, _b;
  $ZodCheck.init(inst, def);
  if (def.pattern)
    (_a3 = inst._zod).check ?? (_a3.check = (payload) => {
      def.pattern.lastIndex = 0;
      if (def.pattern.test(payload.value))
        return;
      payload.issues.push({
        origin: "string",
        code: "invalid_format",
        format: def.format,
        input: payload.value,
        ...def.pattern ? { pattern: def.pattern.toString() } : {},
        inst,
        continue: !def.abort
      });
    });
  else
    (_b = inst._zod).check ?? (_b.check = () => {
    });
});
var $ZodCheckRegex = /* @__PURE__ */ $constructor("$ZodCheckRegex", (inst, def) => {
  $ZodCheckStringFormat.init(inst, def);
  inst._zod.check = (payload) => {
    def.pattern.lastIndex = 0;
    if (def.pattern.test(payload.value))
      return;
    payload.issues.push({
      origin: "string",
      code: "invalid_format",
      format: "regex",
      input: payload.value,
      pattern: def.pattern.toString(),
      inst,
      continue: !def.abort
    });
  };
});
var $ZodCheckLowerCase = /* @__PURE__ */ $constructor("$ZodCheckLowerCase", (inst, def) => {
  def.pattern ?? (def.pattern = lowercase);
  $ZodCheckStringFormat.init(inst, def);
});
var $ZodCheckUpperCase = /* @__PURE__ */ $constructor("$ZodCheckUpperCase", (inst, def) => {
  def.pattern ?? (def.pattern = uppercase);
  $ZodCheckStringFormat.init(inst, def);
});
var $ZodCheckIncludes = /* @__PURE__ */ $constructor("$ZodCheckIncludes", (inst, def) => {
  $ZodCheck.init(inst, def);
  const escapedRegex = escapeRegex(def.includes);
  const pattern = new RegExp(typeof def.position === "number" ? `^.{${def.position},}${escapedRegex}` : escapedRegex);
  def.pattern = pattern;
  inst._zod.check = (payload) => {
    if (payload.value.includes(def.includes, def.position))
      return;
    payload.issues.push({
      origin: "string",
      code: "invalid_format",
      format: "includes",
      includes: def.includes,
      input: payload.value,
      inst,
      continue: !def.abort
    });
  };
});
var $ZodCheckStartsWith = /* @__PURE__ */ $constructor("$ZodCheckStartsWith", (inst, def) => {
  $ZodCheck.init(inst, def);
  const pattern = new RegExp(`^${escapeRegex(def.prefix)}.*`);
  def.pattern ?? (def.pattern = pattern);
  inst._zod.check = (payload) => {
    if (payload.value.startsWith(def.prefix))
      return;
    payload.issues.push({
      origin: "string",
      code: "invalid_format",
      format: "starts_with",
      prefix: def.prefix,
      input: payload.value,
      inst,
      continue: !def.abort
    });
  };
});
var $ZodCheckEndsWith = /* @__PURE__ */ $constructor("$ZodCheckEndsWith", (inst, def) => {
  $ZodCheck.init(inst, def);
  const pattern = new RegExp(`.*${escapeRegex(def.suffix)}$`);
  def.pattern ?? (def.pattern = pattern);
  inst._zod.check = (payload) => {
    if (payload.value.endsWith(def.suffix))
      return;
    payload.issues.push({
      origin: "string",
      code: "invalid_format",
      format: "ends_with",
      suffix: def.suffix,
      input: payload.value,
      inst,
      continue: !def.abort
    });
  };
});
var $ZodCheckOverwrite = /* @__PURE__ */ $constructor("$ZodCheckOverwrite", (inst, def) => {
  $ZodCheck.init(inst, def);
  inst._zod.check = (payload) => {
    payload.value = def.tx(payload.value);
  };
});

// node_modules/zod/v4/core/doc.js
var Doc = class {
  constructor(args = [], closed = {}) {
    this.content = [];
    this.indent = 0;
    this.args = args;
    this.closed = closed;
  }
  // the compiler catches a child's throw and keeps writing into this doc, so the indent has to unwind with it
  indented(fn) {
    this.indent += 1;
    try {
      fn(this);
    } finally {
      this.indent -= 1;
    }
  }
  write(arg) {
    if (typeof arg === "function") {
      arg(this, { execution: "sync" });
      arg(this, { execution: "async" });
      return;
    }
    const content = arg;
    const lines = content.split("\n").filter((x) => x);
    const minIndent = Math.min(...lines.map((x) => x.length - x.trimStart().length));
    const dedented = lines.map((x) => x.slice(minIndent)).map((x) => " ".repeat(this.indent * 2) + x);
    for (const line of dedented) {
      this.content.push(line);
    }
  }
  compile() {
    const F = Function;
    const content = this?.content ?? [``];
    const factory = new F(...Object.keys(this.closed), `return function (${this.args.join(", ")}) {
${content.join("\n")}
};`);
    return factory(...Object.values(this.closed));
  }
};

// node_modules/zod/v4/core/versions.js
var version = {
  major: 4,
  minor: 6,
  patch: 5
};

// node_modules/zod/v4/core/schemas.js
var $ZodType = /* @__PURE__ */ $constructor("$ZodType", (inst, def) => {
  var _a3;
  inst ?? (inst = {});
  inst._zod.def = def;
  inst._zod.bag = inst._zod.bag || {};
  inst._zod.version = version;
  const defChecks = inst._zod.def.checks;
  const checks = inst._zod.traits.has("$ZodCheck") ? [inst, ...defChecks ?? []] : defChecks?.length ? [...defChecks] : [];
  for (const ch of checks) {
    for (const fn of ch._zod.onattach) {
      fn(inst);
    }
  }
  if (checks.length === 0) {
    (_a3 = inst._zod).deferred ?? (_a3.deferred = []);
    inst._zod.deferred?.push(() => {
      inst._zod.run = inst._zod.parse;
    });
  } else {
    const runChecks = (payload, checks2, ctx) => {
      if (payload.memo)
        return payload;
      let isAborted = aborted(payload);
      let asyncResult;
      for (const ch of checks2) {
        if (ch._zod.def.when) {
          if (explicitlyAborted(payload))
            continue;
          const shouldRun = ch._zod.def.when(payload);
          if (!shouldRun)
            continue;
        } else if (isAborted) {
          continue;
        }
        const currLen = payload.issues.length;
        const _ = ch._zod.check(payload);
        if (_ instanceof Promise && ctx?.async === false) {
          throw new $ZodAsyncError();
        }
        if (asyncResult || _ instanceof Promise) {
          asyncResult = (asyncResult ?? Promise.resolve()).then(async () => {
            await _;
            const nextLen = payload.issues.length;
            if (nextLen === currLen)
              return;
            attachSchema(payload.issues, currLen, inst);
            if (!isAborted)
              isAborted = aborted(payload, currLen);
          });
        } else {
          const nextLen = payload.issues.length;
          if (nextLen === currLen)
            continue;
          attachSchema(payload.issues, currLen, inst);
          if (!isAborted)
            isAborted = aborted(payload, currLen);
        }
      }
      if (asyncResult) {
        return asyncResult.then(() => {
          return payload;
        });
      }
      return payload;
    };
    const handleCanaryResult = (canary, payload, ctx) => {
      if (aborted(canary)) {
        canary.aborted = true;
        return canary;
      }
      const checkResult = runChecks(payload, checks, ctx);
      if (checkResult instanceof Promise) {
        if (ctx.async === false)
          throw new $ZodAsyncError();
        return checkResult.then((checkResult2) => inst._zod.parse(checkResult2, ctx));
      }
      return inst._zod.parse(checkResult, ctx);
    };
    inst._zod.run = (payload, ctx) => {
      if (ctx.skipChecks) {
        return inst._zod.parse(payload, ctx);
      }
      if (ctx.direction === "backward") {
        const canary = inst._zod.parse({ value: payload.value, issues: [] }, { ...ctx, skipChecks: true });
        if (canary instanceof Promise) {
          return canary.then((canary2) => {
            return handleCanaryResult(canary2, payload, ctx);
          });
        }
        return handleCanaryResult(canary, payload, ctx);
      }
      const result = inst._zod.parse(payload, ctx);
      if (result instanceof Promise) {
        if (ctx.async === false)
          throw new $ZodAsyncError();
        return result.then((result2) => runChecks(result2, checks, ctx));
      }
      return runChecks(result, checks, ctx);
    };
  }
}, {
  // Wrappers extend this by installing a richer factory over it; reading it eagerly would defeat the laziness.
  get "~standard"() {
    return hide(this, "~standard", standardProps(this));
  },
  set "~standard"(value) {
    own(this, "~standard", value);
  }
});
var toStandardResult = (r, ctx) => r.issues.length ? { issues: r.issues.map((iss) => finalizeIssue(iss, ctx, config())) } : { value: r.value };
async function validateAsync2(inst, value) {
  const ctx = { async: true };
  return toStandardResult(await inst._zod.run({ value, issues: [] }, ctx), ctx);
}
function standardProps(inst) {
  return {
    validate: (value) => {
      const ctx = { async: false };
      try {
        const r = inst._zod.run({ value, issues: [] }, ctx);
        if (!(r instanceof Promise))
          return toStandardResult(r, ctx);
      } catch (_) {
      }
      return validateAsync2(inst, value);
    },
    vendor: "zod",
    version: 1
  };
}
var $ZodString = /* @__PURE__ */ $constructor("$ZodString", (inst, def) => {
  $ZodType.init(inst, def);
  inst._zod.pattern = def.pattern ?? anyString;
  inst._zod.parse = (payload, _) => {
    if (def.coerce)
      try {
        payload.value = String(payload.value);
      } catch (_2) {
      }
    if (typeof payload.value === "string")
      return payload;
    payload.issues.push({
      expected: "string",
      code: "invalid_type",
      input: payload.value,
      inst
    });
    return payload;
  };
});
var $ZodStringFormat = /* @__PURE__ */ $constructor("$ZodStringFormat", (inst, def) => {
  $ZodCheckStringFormat.init(inst, def);
  $ZodString.init(inst, def);
});
var $ZodGUID = /* @__PURE__ */ $constructor("$ZodGUID", (inst, def) => {
  def.pattern ?? (def.pattern = guid);
  $ZodStringFormat.init(inst, def);
});
var $ZodUUID = /* @__PURE__ */ $constructor("$ZodUUID", (inst, def) => {
  if (def.version) {
    const versionMap = {
      v1: 1,
      v2: 2,
      v3: 3,
      v4: 4,
      v5: 5,
      v6: 6,
      v7: 7,
      v8: 8
    };
    const v = versionMap[def.version];
    if (v === void 0)
      throw new Error(`Invalid UUID version: "${def.version}"`);
    def.pattern ?? (def.pattern = uuid(v));
  } else
    def.pattern ?? (def.pattern = uuid());
  $ZodStringFormat.init(inst, def);
});
var $ZodEmail = /* @__PURE__ */ $constructor("$ZodEmail", (inst, def) => {
  def.pattern ?? (def.pattern = email);
  $ZodStringFormat.init(inst, def);
});
var URL_BAD_FORMAT = 1;
var URL_UNPARSEABLE = 2;
function canParseURL(input) {
  try {
    if (typeof URL !== "undefined" && typeof URL.canParse === "function")
      return URL.canParse(input);
    new URL(input);
    return true;
  } catch {
    return false;
  }
}
function validateURL(trimmed, def) {
  if (!("normalize" in def) && !("hostname" in def) && !("protocol" in def)) {
    return canParseURL(trimmed) || URL_UNPARSEABLE;
  }
  return parseURLObject(trimmed, def);
}
function parseURLObject(trimmed, def) {
  if (!def.normalize && def.protocol?.source === httpProtocol.source && !/^https?:\/\//i.test(trimmed)) {
    return URL_BAD_FORMAT;
  }
  try {
    if (typeof URL !== "undefined") {
      const URLStatic = URL;
      if (typeof URLStatic.parse === "function")
        return URLStatic.parse(trimmed) ?? URL_UNPARSEABLE;
    }
    return new URL(trimmed);
  } catch {
    return URL_UNPARSEABLE;
  }
}
var asciiTabOrNewline = /[\t\n\r]/g;
function stripTabAndNewline(value) {
  return value.replace(asciiTabOrNewline, "");
}
function urlHostnameOk(url, hostname) {
  hostname.lastIndex = 0;
  return hostname.test(url.hostname);
}
function urlProtocolOk(url, protocol) {
  protocol.lastIndex = 0;
  return protocol.test(url.protocol.endsWith(":") ? url.protocol.slice(0, -1) : url.protocol);
}
var $ZodURL = /* @__PURE__ */ $constructor("$ZodURL", (inst, def) => {
  $ZodStringFormat.init(inst, def);
  inst._zod.check = (payload) => {
    try {
      const trimmed = payload.value.trim();
      const url = validateURL(trimmed, def);
      if (url === URL_BAD_FORMAT) {
        payload.issues.push({
          code: "invalid_format",
          format: "url",
          note: "Invalid URL format",
          input: payload.value,
          inst,
          continue: !def.abort
        });
        return;
      }
      if (url === URL_UNPARSEABLE) {
        payload.issues.push({
          code: "invalid_format",
          format: "url",
          input: payload.value,
          inst,
          continue: !def.abort
        });
        return;
      }
      if (url === true) {
        payload.value = stripTabAndNewline(trimmed);
        return;
      }
      if (def.hostname && !urlHostnameOk(url, def.hostname)) {
        payload.issues.push({
          code: "invalid_format",
          format: "url",
          note: "Invalid hostname",
          pattern: def.hostname.source,
          input: payload.value,
          inst,
          continue: !def.abort
        });
      }
      if (def.protocol && !urlProtocolOk(url, def.protocol)) {
        payload.issues.push({
          code: "invalid_format",
          format: "url",
          note: "Invalid protocol",
          pattern: def.protocol.source,
          input: payload.value,
          inst,
          continue: !def.abort
        });
      }
      payload.value = def.normalize ? url.href : stripTabAndNewline(trimmed);
      return;
    } catch (_) {
      payload.issues.push({
        code: "invalid_format",
        format: "url",
        input: payload.value,
        inst,
        continue: !def.abort
      });
    }
  };
});
var $ZodEmoji = /* @__PURE__ */ $constructor("$ZodEmoji", (inst, def) => {
  def.pattern ?? (def.pattern = emoji());
  $ZodStringFormat.init(inst, def);
});
var $ZodNanoID = /* @__PURE__ */ $constructor("$ZodNanoID", (inst, def) => {
  if (def.length !== void 0 && (!Number.isInteger(def.length) || def.length < 1))
    throw new Error(`Invalid nanoid length: ${def.length}`);
  def.pattern ?? (def.pattern = def.length === void 0 ? nanoid : nanoidOfLength(def.length));
  $ZodStringFormat.init(inst, def);
});
var $ZodCUID = /* @__PURE__ */ $constructor("$ZodCUID", (inst, def) => {
  def.pattern ?? (def.pattern = cuid);
  $ZodStringFormat.init(inst, def);
});
var $ZodCUID2 = /* @__PURE__ */ $constructor("$ZodCUID2", (inst, def) => {
  def.pattern ?? (def.pattern = cuid2);
  $ZodStringFormat.init(inst, def);
});
var $ZodULID = /* @__PURE__ */ $constructor("$ZodULID", (inst, def) => {
  def.pattern ?? (def.pattern = ulid);
  $ZodStringFormat.init(inst, def);
});
var $ZodXID = /* @__PURE__ */ $constructor("$ZodXID", (inst, def) => {
  def.pattern ?? (def.pattern = xid);
  $ZodStringFormat.init(inst, def);
});
var $ZodKSUID = /* @__PURE__ */ $constructor("$ZodKSUID", (inst, def) => {
  def.pattern ?? (def.pattern = ksuid);
  $ZodStringFormat.init(inst, def);
});
var $ZodISODateTime = /* @__PURE__ */ $constructor("$ZodISODateTime", (inst, def) => {
  def.pattern ?? (def.pattern = datetime(def));
  $ZodStringFormat.init(inst, def);
});
var $ZodISODate = /* @__PURE__ */ $constructor("$ZodISODate", (inst, def) => {
  def.pattern ?? (def.pattern = date);
  $ZodStringFormat.init(inst, def);
});
var $ZodISOTime = /* @__PURE__ */ $constructor("$ZodISOTime", (inst, def) => {
  def.pattern ?? (def.pattern = time(def));
  $ZodStringFormat.init(inst, def);
});
var $ZodISODuration = /* @__PURE__ */ $constructor("$ZodISODuration", (inst, def) => {
  def.pattern ?? (def.pattern = duration);
  $ZodStringFormat.init(inst, def);
});
var $ZodIPv4 = /* @__PURE__ */ $constructor("$ZodIPv4", (inst, def) => {
  def.pattern ?? (def.pattern = ipv4);
  $ZodStringFormat.init(inst, def);
});
var ipv6Alphabet = /^[0-9a-fA-F:.]+$/;
function isValidIPv6(value) {
  if (!ipv6Alphabet.test(value))
    return false;
  return canParseURL(`http://[${value}]`);
}
var $ZodIPv6 = /* @__PURE__ */ $constructor("$ZodIPv6", (inst, def) => {
  def.pattern ?? (def.pattern = ipv6);
  $ZodStringFormat.init(inst, def);
  inst._zod.check = (payload) => {
    if (!isValidIPv6(payload.value)) {
      payload.issues.push({
        code: "invalid_format",
        format: "ipv6",
        input: payload.value,
        inst,
        continue: !def.abort
      });
    }
  };
});
var $ZodCIDRv4 = /* @__PURE__ */ $constructor("$ZodCIDRv4", (inst, def) => {
  def.pattern ?? (def.pattern = cidrv4);
  $ZodStringFormat.init(inst, def);
});
function isValidCIDRv6(value) {
  const parts = value.split("/");
  if (parts.length !== 2)
    return false;
  const [address, prefix] = parts;
  if (!prefix)
    return false;
  const prefixNum = Number(prefix);
  if (`${prefixNum}` !== prefix)
    return false;
  if (prefixNum < 0 || prefixNum > 128)
    return false;
  return isValidIPv6(address);
}
var $ZodCIDRv6 = /* @__PURE__ */ $constructor("$ZodCIDRv6", (inst, def) => {
  def.pattern ?? (def.pattern = cidrv6);
  $ZodStringFormat.init(inst, def);
  inst._zod.check = (payload) => {
    if (!isValidCIDRv6(payload.value)) {
      payload.issues.push({
        code: "invalid_format",
        format: "cidrv6",
        input: payload.value,
        inst,
        continue: !def.abort
      });
    }
  };
});
function isValidBase64(data) {
  if (data === "")
    return true;
  if (/\s/.test(data))
    return false;
  if (data.length % 4 !== 0)
    return false;
  try {
    atob(data);
    return true;
  } catch {
    return false;
  }
}
var base64Charset = /^[0-9a-zA-Z+/]*={0,2}$/;
var $ZodBase64 = /* @__PURE__ */ $constructor("$ZodBase64", (inst, def) => {
  def.pattern ?? (def.pattern = base64Charset);
  $ZodStringFormat.init(inst, def);
  inst._zod.check = (payload) => {
    if (isValidBase64(payload.value))
      return;
    payload.issues.push({
      code: "invalid_format",
      format: "base64",
      input: payload.value,
      inst,
      continue: !def.abort
    });
  };
});
var base64urlCharset = /^[A-Za-z0-9_-]*$/;
function isValidBase64URL(data) {
  if (!base64urlCharset.test(data))
    return false;
  const base642 = data.replace(/[-_]/g, (c) => c === "-" ? "+" : "/");
  const padded = base642.padEnd(Math.ceil(base642.length / 4) * 4, "=");
  return isValidBase64(padded);
}
var $ZodBase64URL = /* @__PURE__ */ $constructor("$ZodBase64URL", (inst, def) => {
  def.pattern ?? (def.pattern = base64urlCharset);
  $ZodStringFormat.init(inst, def);
  inst._zod.check = (payload) => {
    if (isValidBase64URL(payload.value))
      return;
    payload.issues.push({
      code: "invalid_format",
      format: "base64url",
      input: payload.value,
      inst,
      continue: !def.abort
    });
  };
});
var $ZodE164 = /* @__PURE__ */ $constructor("$ZodE164", (inst, def) => {
  def.pattern ?? (def.pattern = e164);
  $ZodStringFormat.init(inst, def);
});
function isValidJWT(token, algorithm = null) {
  try {
    const tokensParts = token.split(".");
    if (tokensParts.length !== 3)
      return false;
    const [header] = tokensParts;
    if (!header)
      return false;
    const parsedHeader = JSON.parse(atob(header));
    if ("typ" in parsedHeader && parsedHeader?.typ !== "JWT")
      return false;
    if (!parsedHeader.alg)
      return false;
    if (algorithm && (!("alg" in parsedHeader) || parsedHeader.alg !== algorithm))
      return false;
    return true;
  } catch {
    return false;
  }
}
var $ZodJWT = /* @__PURE__ */ $constructor("$ZodJWT", (inst, def) => {
  $ZodStringFormat.init(inst, def);
  inst._zod.check = (payload) => {
    if (isValidJWT(payload.value, def.alg))
      return;
    payload.issues.push({
      code: "invalid_format",
      format: "jwt",
      input: payload.value,
      inst,
      continue: !def.abort
    });
  };
});
var $ZodNumber = /* @__PURE__ */ $constructor("$ZodNumber", (inst, def) => {
  $ZodType.init(inst, def);
  inst._zod.pattern = number;
  inst._zod.parse = (payload, _ctx) => {
    if (def.coerce)
      try {
        payload.value = Number(payload.value);
      } catch (_) {
      }
    const input = payload.value;
    if (typeof input === "number" && !Number.isNaN(input) && Number.isFinite(input)) {
      return payload;
    }
    const received = typeof input === "number" ? Number.isNaN(input) ? "NaN" : !Number.isFinite(input) ? String(input) : void 0 : void 0;
    payload.issues.push({
      expected: "number",
      code: "invalid_type",
      input,
      inst,
      ...received ? { received } : {}
    });
    return payload;
  };
});
var $ZodNumberFormat = /* @__PURE__ */ $constructor("$ZodNumberFormat", (inst, def) => {
  $ZodCheckNumberFormat.init(inst, def);
  $ZodNumber.init(inst, def);
});
var $ZodBoolean = /* @__PURE__ */ $constructor("$ZodBoolean", (inst, def) => {
  $ZodType.init(inst, def);
  inst._zod.pattern = boolean;
  inst._zod.parse = (payload, _ctx) => {
    if (def.coerce)
      try {
        payload.value = Boolean(payload.value);
      } catch (_) {
      }
    const input = payload.value;
    if (typeof input === "boolean")
      return payload;
    payload.issues.push({
      expected: "boolean",
      code: "invalid_type",
      input,
      inst
    });
    return payload;
  };
});
var $ZodUnknown = /* @__PURE__ */ $constructor("$ZodUnknown", (inst, def) => {
  $ZodType.init(inst, def);
  inst._zod.parse = (payload) => payload;
});
var $ZodNever = /* @__PURE__ */ $constructor("$ZodNever", (inst, def) => {
  $ZodType.init(inst, def);
  inst._zod.parse = (payload, _ctx) => {
    payload.issues.push({
      expected: "never",
      code: "invalid_type",
      input: payload.value,
      inst
    });
    return payload;
  };
});
function handleArrayResult(result, final, index) {
  if (result.issues.length) {
    final.issues.push(...prefixIssues(index, result.issues));
  }
  final.value[index] = result.value;
}
var $ZodArray = /* @__PURE__ */ $constructor("$ZodArray", (inst, def) => {
  $ZodType.init(inst, def);
  const memo2 = globalConfig.memoizer;
  memo2?.attach(inst);
  inst._zod.parse = (payload, ctx) => {
    const input = payload.value;
    if (!Array.isArray(input)) {
      payload.issues.push({
        expected: "array",
        code: "invalid_type",
        input,
        inst
      });
      return payload;
    }
    payload.value = memo2 ? memo2.alloc(inst, payload, Array(input.length), ctx) : Array(input.length);
    const proms = [];
    const abortEarly = ctx?.abortEarly;
    for (let i = 0; i < input.length; i++) {
      const item = input[i];
      const result = def.element._zod.run({
        value: item,
        issues: []
      }, ctx);
      if (result instanceof Promise) {
        proms.push(result.then((result2) => handleArrayResult(result2, payload, i)));
      } else {
        handleArrayResult(result, payload, i);
        if (abortEarly && result.issues.length !== 0 && aborted(result))
          break;
      }
    }
    if (proms.length) {
      return Promise.all(proms).then(() => payload);
    }
    return payload;
  };
});
function handlePropertyResult(result, final, key, input, optin, optout) {
  const isPresent = key in input;
  const isOptionalOut = optout === "optional";
  if (!isPresent && isOptionalOut && optin === "optional") {
    return;
  }
  if (result.issues.length) {
    if (optin !== void 0 && isOptionalOut && !isPresent) {
      return;
    }
    final.issues.push(...prefixIssues(key, result.issues));
  }
  if (!isPresent && optin === void 0) {
    if (!result.issues.length) {
      final.issues.push({
        code: "invalid_type",
        expected: "nonoptional",
        input: void 0,
        path: [key]
      });
    }
    return;
  }
  if (result.value === void 0) {
    if (isPresent || optin === "defaulted" && !isOptionalOut) {
      final.value[key] = void 0;
    }
  } else {
    final.value[key] = result.value;
  }
}
var NO_SYMBOL_KEYS = [];
function normalizeDef(def) {
  const keys = Object.keys(def.shape);
  const ownSymbols = Object.getOwnPropertySymbols(def.shape);
  const symbolKeys = ownSymbols.length ? ownSymbols : NO_SYMBOL_KEYS;
  const allKeys = symbolKeys.length ? [...keys, ...symbolKeys] : keys;
  for (const k of allKeys) {
    if (!def.shape?.[k]?._zod?.traits?.has("$ZodType")) {
      throw new Error(`Invalid element at key "${String(k)}": expected a Zod schema`);
    }
  }
  const okeys = optionalKeys(def.shape);
  return {
    ...def,
    allKeys,
    symbolKeys,
    // string-only: handleCatchall matches it against `for...in`, which never yields a symbol
    keySet: new Set(keys),
    numKeys: keys.length,
    optionalKeys: new Set(okeys)
  };
}
function handleCatchall(proms, input, payload, ctx, def, inst, abortEarly) {
  const unrecognized = [];
  const keySet = def.keySet;
  const _catchall = def.catchall._zod;
  const t = _catchall.def.type;
  const optin = _catchall.optin;
  const optout = _catchall.optout;
  let seen = 0;
  for (const key in input) {
    if (abortEarly && payload.issues.length !== seen) {
      if (aborted(payload, seen))
        break;
      seen = payload.issues.length;
    }
    if (keySet.has(key))
      continue;
    if (key === "__proto__") {
      if (t === "never")
        unrecognized.push(key);
      continue;
    }
    if (t === "never") {
      unrecognized.push(key);
      continue;
    }
    const r = _catchall.run({ value: input[key], issues: [] }, ctx);
    if (r instanceof Promise) {
      proms.push(r.then((r2) => handlePropertyResult(r2, payload, key, input, optin, optout)));
    } else {
      handlePropertyResult(r, payload, key, input, optin, optout);
    }
  }
  if (unrecognized.length) {
    payload.issues.push({
      code: "unrecognized_keys",
      keys: unrecognized,
      input,
      inst,
      // Describes the shape of the input, not the validity of the parsed value, so it never aborts. The parse still fails; the schema's own checks just get to run first, and an enclosing intersection can reconcile the key against a sibling operand.
      continue: true
    });
  }
  if (!proms.length)
    return payload;
  return Promise.all(proms).then(() => {
    return payload;
  });
}
var $ZodObject = /* @__PURE__ */ $constructor("$ZodObject", (inst, def) => {
  $ZodType.init(inst, def);
  const desc = Object.getOwnPropertyDescriptor(def, "shape");
  const sh = desc?.get ? desc.get.raw : def.shape ?? {};
  if (sh) {
    const get = () => {
      const newSh = { ...sh };
      Object.defineProperty(def, "shape", { value: newSh });
      get.raw = newSh;
      return newSh;
    };
    get.raw = sh;
    Object.defineProperty(def, "shape", { get });
  }
  const _normalized = cached(() => normalizeDef(def));
  defineLazyInternal(inst, "propValues", (zod) => {
    const shape = zod.def.shape;
    const propValues = {};
    for (const key in shape) {
      const field = shape[key]._zod;
      if (field.values) {
        if (!Object.prototype.hasOwnProperty.call(propValues, key)) {
          assignProp(propValues, key, /* @__PURE__ */ new Set());
        }
        for (const v of field.values)
          propValues[key].add(v);
        if (field.optin !== void 0)
          propValues[key].add(void 0);
      }
    }
    return propValues;
  });
  const isObject2 = isObject;
  const catchall = def.catchall;
  let value;
  const memo2 = globalConfig.memoizer;
  memo2?.attach(inst);
  inst._zod.parse = (payload, ctx) => {
    value ?? (value = _normalized.value);
    const input = payload.value;
    if (!isObject2(input)) {
      payload.issues.push({
        expected: "object",
        code: "invalid_type",
        input,
        inst
      });
      return payload;
    }
    payload.value = memo2 ? memo2.alloc(inst, payload, {}, ctx) : {};
    const proms = [];
    const shape = value.shape;
    const abortEarly = ctx?.abortEarly;
    let seen = payload.issues.length;
    for (const key of value.allKeys) {
      if (abortEarly && payload.issues.length !== seen) {
        if (aborted(payload, seen))
          break;
        seen = payload.issues.length;
      }
      if (key === "__proto__")
        continue;
      const el = shape[key];
      const optin = el._zod.optin;
      const optout = el._zod.optout;
      const r = el._zod.run({ value: input[key], issues: [] }, ctx);
      if (r instanceof Promise) {
        proms.push(r.then((r2) => handlePropertyResult(r2, payload, key, input, optin, optout)));
      } else {
        handlePropertyResult(r, payload, key, input, optin, optout);
      }
    }
    if (!catchall) {
      return proms.length ? Promise.all(proms).then(() => payload) : payload;
    }
    return handleCatchall(proms, input, payload, ctx, _normalized.value, inst, abortEarly === true);
  };
});
var $ZodObjectJIT = /* @__PURE__ */ $constructor("$ZodObjectJIT", (inst, def) => {
  $ZodObject.init(inst, def);
  const superParse = inst._zod.parse;
  const _normalized = cached(() => normalizeDef(def));
  const memo2 = globalConfig.memoizer;
  const generateFastpass = (shape) => {
    const normalized = _normalized.value;
    const syms = normalized.symbolKeys;
    const doc = new Doc(["payload", "ctx"], { shape, inst, memo: memo2, syms });
    const parseStr = (k) => `shape[${k}]._zod.run({ value: input[${k}], issues: [] }, ctx)`;
    const prefixStr = (id, k) => `
          let ${id}_ab = false;
          for (let i = 0; i < ${id}.issues.length; i++) {
            const iss = ${id}.issues[i];
            iss.path = iss.path ? [${k}, ...iss.path] : [${k}];
            payload.issues.push(iss);
            if (iss.continue !== true) ${id}_ab = true;
          }
          if (${id}_ab && ctx && ctx.abortEarly) {
            payload.value = newResult;
            return payload;
          }`;
    doc.write(`const input = payload.value;`);
    const ids = /* @__PURE__ */ Object.create(null);
    let counter = 0;
    for (const key of normalized.allKeys) {
      ids[key] = `key_${counter++}`;
    }
    doc.write(memo2 ? `const newResult = memo.alloc(inst, payload, {}, ctx);` : `const newResult = {};`);
    for (const key of normalized.allKeys) {
      if (key === "__proto__")
        continue;
      const id = ids[key];
      const k = typeof key === "symbol" ? `syms[${syms.indexOf(key)}]` : esc(key);
      const isPresent = `${k} in input`;
      const schema = shape[key];
      const optin = schema?._zod?.optin;
      const isOptionalIn = optin !== void 0;
      const isOptionalOut = schema?._zod?.optout === "optional";
      doc.write(`const ${id} = ${parseStr(k)};`);
      if (isOptionalIn && isOptionalOut) {
        const assign = optin === "optional" ? `${id}_present` : `${id}.value !== undefined || ${id}_present`;
        doc.write(`
        const ${id}_present = ${isPresent};
        if (!${id}.issues.length || ${id}_present) {
          if (${id}.issues.length) {${prefixStr(id, k)}
          }

          if (${assign}) {
            newResult[${k}] = ${id}.value;
          }
        }

      `);
      } else if (!isOptionalIn) {
        doc.write(`
        const ${id}_present = ${isPresent};
        if (${id}.issues.length) {${prefixStr(id, k)}
        }
        if (!${id}_present && !${id}.issues.length) {
          payload.issues.push({
            code: "invalid_type",
            expected: "nonoptional",
            input: undefined,
            path: [${k}]
          });
          if (ctx && ctx.abortEarly) {
            payload.value = newResult;
            return payload;
          }
        }

        if (${id}_present) {
          newResult[${k}] = ${id}.value;
        }

      `);
      } else {
        doc.write(`
        if (${id}.issues.length) {${prefixStr(id, k)}
        }
      `);
        if (optin === "defaulted") {
          doc.write(`newResult[${k}] = ${id}.value;`);
        } else {
          doc.write(`
        if (${id}.value !== undefined || ${isPresent}) {
          newResult[${k}] = ${id}.value;
        }
      `);
        }
      }
    }
    doc.write(`payload.value = newResult;`);
    doc.write(`return payload;`);
    return doc.compile();
  };
  let fastpass;
  const isObject2 = isObject;
  const jit = !globalConfig.jitless;
  const allowsEval2 = allowsEval;
  const fastEnabled = jit && allowsEval2.value;
  const catchall = def.catchall;
  let value;
  inst._zod.parse = (payload, ctx) => {
    value ?? (value = _normalized.value);
    const input = payload.value;
    if (!isObject2(input)) {
      payload.issues.push({
        expected: "object",
        code: "invalid_type",
        input,
        inst
      });
      return payload;
    }
    if (jit && fastEnabled && ctx?.async === false && ctx.jitless !== true) {
      if (!fastpass)
        fastpass = generateFastpass(def.shape);
      payload = fastpass(payload, ctx);
      if (!catchall)
        return payload;
      return handleCatchall([], input, payload, ctx, value, inst, ctx?.abortEarly === true);
    }
    return superParse(payload, ctx);
  };
});
function handleUnionResults(results, final, inst, ctx) {
  for (const result of results) {
    if (result.issues.length === 0) {
      final.value = result.value;
      return final;
    }
  }
  const nonaborted = results.filter((r) => !aborted(r));
  if (nonaborted.length === 1) {
    final.value = nonaborted[0].value;
    return nonaborted[0];
  }
  final.issues.push({
    code: "invalid_union",
    input: final.value,
    inst,
    errors: results.map((result) => result.issues.map((iss) => finalizeIssue(iss, ctx, config())))
  });
  return final;
}
var $ZodUnion = /* @__PURE__ */ $constructor("$ZodUnion", (inst, def) => {
  $ZodType.init(inst, def);
  defineLazyInternal(inst, "optin", (zod) => zod.def.options.some((o) => o._zod.optin === "defaulted") ? "defaulted" : zod.def.options.some((o) => o._zod.optin !== void 0) ? "optional" : void 0);
  defineLazyInternal(inst, "optout", (zod) => zod.def.options.some((o) => o._zod.optout === "optional") ? "optional" : void 0);
  defineLazyInternal(inst, "values", (zod) => {
    if (zod.def.options.every((o) => o._zod.values)) {
      return new Set(zod.def.options.flatMap((option) => Array.from(option._zod.values)));
    }
    return void 0;
  });
  defineLazyInternal(inst, "pattern", (zod) => {
    if (zod.def.options.every((o) => o._zod.pattern)) {
      const patterns = zod.def.options.map((o) => o._zod.pattern);
      return new RegExp(`^(${patterns.map((p) => cleanRegex(p.source)).join("|")})$`);
    }
    return void 0;
  });
  const first = def.options.length === 1 ? def.options[0]._zod.run : null;
  inst._zod.parse = (payload, ctx) => {
    if (first) {
      return first(payload, ctx);
    }
    let async = false;
    const results = [];
    for (const option of def.options) {
      const result = option._zod.run({
        value: payload.value,
        issues: []
      }, ctx);
      if (result instanceof Promise) {
        results.push(result);
        async = true;
      } else {
        if (result.issues.length === 0)
          return result;
        results.push(result);
      }
    }
    if (!async)
      return handleUnionResults(results, payload, inst, ctx);
    return Promise.all(results).then((results2) => {
      return handleUnionResults(results2, payload, inst, ctx);
    });
  };
});
var $ZodIntersection = /* @__PURE__ */ $constructor("$ZodIntersection", (inst, def) => {
  $ZodType.init(inst, def);
  inst._zod.parse = (payload, ctx) => {
    const input = payload.value;
    const left = def.left._zod.run({ value: input, issues: [] }, ctx);
    const right = def.right._zod.run({ value: input, issues: [] }, ctx);
    const async = left instanceof Promise || right instanceof Promise;
    if (async) {
      return Promise.all([left, right]).then(([left2, right2]) => {
        return handleIntersectionResults(payload, left2, right2);
      });
    }
    return handleIntersectionResults(payload, left, right);
  };
});
function mergeValues(a, b) {
  if (a === b) {
    return { valid: true, data: a };
  }
  if (a instanceof Date && b instanceof Date && +a === +b) {
    return { valid: true, data: a };
  }
  if (isPlainObject2(a) && isPlainObject2(b)) {
    const bKeys = Object.keys(b);
    const sharedKeys = Object.keys(a).filter((key) => bKeys.indexOf(key) !== -1);
    const newObj = { ...a, ...b };
    if (Object.prototype.hasOwnProperty.call(newObj, "__proto__"))
      delete newObj.__proto__;
    for (const key of sharedKeys) {
      if (key === "__proto__")
        continue;
      const sharedValue = mergeValues(a[key], b[key]);
      if (!sharedValue.valid) {
        return {
          valid: false,
          mergeErrorPath: [key, ...sharedValue.mergeErrorPath]
        };
      }
      newObj[key] = sharedValue.data;
    }
    return { valid: true, data: newObj };
  }
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) {
      return { valid: false, mergeErrorPath: [] };
    }
    const newArray = [];
    for (let index = 0; index < a.length; index++) {
      const itemA = a[index];
      const itemB = b[index];
      const sharedValue = mergeValues(itemA, itemB);
      if (!sharedValue.valid) {
        return {
          valid: false,
          mergeErrorPath: [index, ...sharedValue.mergeErrorPath]
        };
      }
      newArray.push(sharedValue.data);
    }
    return { valid: true, data: newArray };
  }
  return { valid: false, mergeErrorPath: [] };
}
function handleIntersectionResults(result, left, right) {
  const unrecKeys = /* @__PURE__ */ new Map();
  let unrecIssue;
  const keyIssues = /* @__PURE__ */ new Map();
  const collect = (iss, side) => {
    let keys;
    if (iss.code === "unrecognized_keys" && !iss.path?.length) {
      unrecIssue ?? (unrecIssue = iss);
      keys = iss.keys;
    } else if (iss.code === "invalid_key" && iss.origin === "record" && iss.path?.length === 1) {
      const k = String(iss.path[0]);
      if (!keyIssues.has(k))
        keyIssues.set(k, iss);
      keys = [k];
    } else {
      return false;
    }
    for (const k of keys) {
      if (!unrecKeys.has(k))
        unrecKeys.set(k, {});
      unrecKeys.get(k)[side] = true;
    }
    return true;
  };
  for (const iss of left.issues) {
    if (!collect(iss, "l"))
      result.issues.push(iss);
  }
  for (const iss of right.issues) {
    if (!collect(iss, "r"))
      result.issues.push(iss);
  }
  const bothKeys = [...unrecKeys].filter(([, f]) => f.l && f.r).map(([k]) => k);
  if (bothKeys.length) {
    const aggregated = unrecIssue ? bothKeys.filter((k) => unrecIssue.keys.includes(k)) : [];
    if (aggregated.length)
      result.issues.push({ ...unrecIssue, keys: aggregated });
    for (const k of bothKeys) {
      if (!aggregated.includes(k) && keyIssues.has(k))
        result.issues.push(keyIssues.get(k));
    }
  }
  const merged = mergeValues(left.value, right.value);
  if (!merged.valid) {
    if (aborted(result))
      return result;
    throw new Error(`Unmergable intersection. Error path: ${JSON.stringify(merged.mergeErrorPath)}`);
  }
  result.value = merged.data;
  return result;
}
var $ZodRecord = /* @__PURE__ */ $constructor("$ZodRecord", (inst, def) => {
  $ZodType.init(inst, def);
  const memo2 = globalConfig.memoizer;
  memo2?.attach(inst);
  inst._zod.parse = (payload, ctx) => {
    const input = payload.value;
    if (!isPlainObject2(input)) {
      payload.issues.push({
        expected: "record",
        code: "invalid_type",
        input,
        inst
      });
      return payload;
    }
    const proms = [];
    const values = def.keyType._zod.values;
    if (values && !def.partial) {
      payload.value = memo2 ? memo2.alloc(inst, payload, {}, ctx) : {};
      const recordKeys = /* @__PURE__ */ new Set();
      for (const key of values) {
        if (typeof key === "string" || typeof key === "number" || typeof key === "symbol") {
          recordKeys.add(typeof key === "number" ? key.toString() : key);
          if (key === "__proto__")
            continue;
          const keyResult = def.keyType._zod.run({ value: key, issues: [] }, ctx);
          if (keyResult instanceof Promise) {
            throw new Error("Async schemas not supported in object keys currently");
          }
          if (keyResult.issues.length) {
            payload.issues.push({
              code: "invalid_key",
              origin: "record",
              issues: keyResult.issues.map((iss) => finalizeIssue(iss, ctx, config())),
              input: key,
              path: [key],
              inst
            });
            continue;
          }
          const outKey = keyResult.value;
          if (outKey === "__proto__")
            continue;
          const result = def.valueType._zod.run({ value: input[key], issues: [] }, ctx);
          if (result instanceof Promise) {
            proms.push(result.then((result2) => {
              if (result2.issues.length) {
                payload.issues.push(...prefixIssues(key, result2.issues));
              }
              payload.value[outKey] = result2.value;
            }));
          } else {
            if (result.issues.length) {
              payload.issues.push(...prefixIssues(key, result.issues));
            }
            payload.value[outKey] = result.value;
          }
        }
      }
      let unrecognized;
      for (const key in input) {
        if (!recordKeys.has(key)) {
          if (def.mode === "loose") {
            if (key === "__proto__")
              continue;
            payload.value[key] = input[key];
          } else {
            unrecognized = unrecognized ?? [];
            unrecognized.push(key);
          }
        }
      }
      if (unrecognized && unrecognized.length > 0) {
        payload.issues.push({
          code: "unrecognized_keys",
          input,
          inst,
          keys: unrecognized,
          continue: true
        });
      }
    } else {
      payload.value = memo2 ? memo2.alloc(inst, payload, {}, ctx) : {};
      let unrecognized;
      for (const key of Reflect.ownKeys(input)) {
        if (key === "__proto__")
          continue;
        if (!Object.prototype.propertyIsEnumerable.call(input, key))
          continue;
        let keyResult = def.keyType._zod.run({ value: key, issues: [] }, ctx);
        if (keyResult instanceof Promise) {
          throw new Error("Async schemas not supported in object keys currently");
        }
        const checkNumericKey = typeof key === "string" && number.test(key) && keyResult.issues.length;
        if (checkNumericKey) {
          const retryResult = def.keyType._zod.run({ value: Number(key), issues: [] }, ctx);
          if (retryResult instanceof Promise) {
            throw new Error("Async schemas not supported in object keys currently");
          }
          if (retryResult.issues.length === 0) {
            keyResult = retryResult;
          }
        }
        if (keyResult.issues.length) {
          if (def.mode === "loose") {
            payload.value[key] = input[key];
          } else if (values) {
            unrecognized = unrecognized ?? [];
            unrecognized.push(key);
          } else {
            payload.issues.push({
              code: "invalid_key",
              origin: "record",
              issues: keyResult.issues.map((iss) => finalizeIssue(iss, ctx, config())),
              input: key,
              path: [key],
              inst
            });
          }
          continue;
        }
        const outKey = keyResult.value;
        if (outKey === "__proto__")
          continue;
        const result = def.valueType._zod.run({ value: input[key], issues: [] }, ctx);
        if (result instanceof Promise) {
          proms.push(result.then((result2) => {
            if (result2.issues.length) {
              payload.issues.push(...prefixIssues(key, result2.issues));
            }
            payload.value[outKey] = result2.value;
          }));
        } else {
          if (result.issues.length) {
            payload.issues.push(...prefixIssues(key, result.issues));
          }
          payload.value[outKey] = result.value;
        }
      }
      if (unrecognized && unrecognized.length > 0) {
        payload.issues.push({
          code: "unrecognized_keys",
          input,
          inst,
          keys: unrecognized,
          continue: true
        });
      }
    }
    if (proms.length) {
      return Promise.all(proms).then(() => payload);
    }
    return payload;
  };
});
var $ZodEnum = /* @__PURE__ */ $constructor("$ZodEnum", (inst, def) => {
  $ZodType.init(inst, def);
  const values = getEnumValues(def.entries);
  const valuesSet = new Set(values);
  inst._zod.values = valuesSet;
  defineLazyInternal(inst, "pattern", (zod) => {
    const patternValues = getEnumValues(zod.def.entries).filter((k) => propertyKeyTypes.has(typeof k));
    return new RegExp(patternValues.length ? `^(${patternValues.map((o) => escapeRegex(o.toString())).join("|")})$` : "^[^\\s\\S]$");
  });
  inst._zod.parse = (payload, _ctx) => {
    const input = payload.value;
    if (valuesSet.has(input)) {
      return payload;
    }
    payload.issues.push({
      code: "invalid_value",
      values,
      input,
      inst
    });
    return payload;
  };
});
var $ZodLiteral = /* @__PURE__ */ $constructor("$ZodLiteral", (inst, def) => {
  $ZodType.init(inst, def);
  const values = new Set(def.values);
  inst._zod.values = values;
  defineLazyInternal(inst, "pattern", (zod) => {
    const vals = zod.def.values;
    return new RegExp(vals.length ? `^(${vals.map((o) => typeof o === "string" ? escapeRegex(o) : o ? escapeRegex(o.toString()) : String(o)).join("|")})$` : "^[^\\s\\S]$");
  });
  inst._zod.parse = (payload, _ctx) => {
    const input = payload.value;
    if (values.has(input)) {
      return payload;
    }
    payload.issues.push({
      code: "invalid_value",
      values: def.values,
      input,
      inst
    });
    return payload;
  };
});
var $ZodTransform = /* @__PURE__ */ $constructor("$ZodTransform", (inst, def) => {
  $ZodType.init(inst, def);
  inst._zod.optin = "optional";
  globalConfig.memoizer?.guard(inst);
  inst._zod.parse = (payload, ctx) => {
    if (ctx.direction === "backward") {
      throw new $ZodEncodeError(inst.constructor.name);
    }
    const _out = def.transform(payload.value, payload);
    if (ctx.async) {
      const output = _out instanceof Promise ? _out : Promise.resolve(_out);
      return output.then((output2) => {
        payload.value = output2;
        return payload;
      });
    }
    if (_out instanceof Promise) {
      throw new $ZodAsyncError();
    }
    payload.value = _out;
    return payload;
  };
});
function handleOptionalResult(payload, result) {
  payload.value = result.issues.length ? void 0 : result.value;
  return payload;
}
var $ZodOptional = /* @__PURE__ */ $constructor("$ZodOptional", (inst, def) => {
  $ZodType.init(inst, def);
  defineLazyInternal(inst, "optin", (zod) => zod.def.innerType._zod.optin === "defaulted" ? "defaulted" : "optional");
  inst._zod.optout = "optional";
  defineLazyInternal(inst, "values", (zod) => {
    const values = zod.def.innerType._zod.values;
    return values ? /* @__PURE__ */ new Set([...values, void 0]) : void 0;
  });
  defineLazyInternal(inst, "pattern", (zod) => {
    const pattern = zod.def.innerType._zod.pattern;
    return pattern ? new RegExp(`^(${cleanRegex(pattern.source)})?$`) : void 0;
  });
  inst._zod.parse = (payload, ctx) => {
    if (payload.value === void 0) {
      if (def.innerType._zod.optin !== "defaulted")
        return payload;
      const result = def.innerType._zod.run({ value: payload.value, issues: [] }, ctx);
      if (result instanceof Promise)
        return result.then((result2) => handleOptionalResult(payload, result2));
      return handleOptionalResult(payload, result);
    }
    return def.innerType._zod.run(payload, ctx);
  };
});
var $ZodExactOptional = /* @__PURE__ */ $constructor("$ZodExactOptional", (inst, def) => {
  $ZodOptional.init(inst, def);
  defineLazyInternal(inst, "values", (zod) => zod.def.innerType._zod.values);
  defineLazyInternal(inst, "pattern", (zod) => zod.def.innerType._zod.pattern);
  inst._zod.parse = (payload, ctx) => {
    return def.innerType._zod.run(payload, ctx);
  };
});
var $ZodNullable = /* @__PURE__ */ $constructor("$ZodNullable", (inst, def) => {
  $ZodType.init(inst, def);
  defineLazyInternal(inst, "optin", (zod) => zod.def.innerType._zod.optin);
  defineLazyInternal(inst, "optout", (zod) => zod.def.innerType._zod.optout);
  defineLazyInternal(inst, "pattern", (zod) => {
    const pattern = zod.def.innerType._zod.pattern;
    return pattern ? new RegExp(`^(${cleanRegex(pattern.source)}|null)$`) : void 0;
  });
  defineLazyInternal(inst, "values", (zod) => {
    return zod.def.innerType._zod.values ? /* @__PURE__ */ new Set([...zod.def.innerType._zod.values, null]) : void 0;
  });
  inst._zod.parse = (payload, ctx) => {
    if (payload.value === null)
      return payload;
    return def.innerType._zod.run(payload, ctx);
  };
});
var $ZodDefault = /* @__PURE__ */ $constructor("$ZodDefault", (inst, def) => {
  $ZodType.init(inst, def);
  inst._zod.optin = "defaulted";
  defineLazyInternal(inst, "values", (zod) => zod.def.innerType._zod.values);
  inst._zod.parse = (payload, ctx) => {
    if (ctx.direction === "backward") {
      return def.innerType._zod.run(payload, ctx);
    }
    if (payload.value === void 0) {
      payload.value = def.defaultValue;
      return payload;
    }
    const result = def.innerType._zod.run(payload, ctx);
    if (result instanceof Promise) {
      return result.then((result2) => handleDefaultResult(result2, def));
    }
    return handleDefaultResult(result, def);
  };
});
function handleDefaultResult(payload, def) {
  if (payload.value === void 0) {
    payload.value = def.defaultValue;
  }
  return payload;
}
var $ZodPrefault = /* @__PURE__ */ $constructor("$ZodPrefault", (inst, def) => {
  $ZodType.init(inst, def);
  inst._zod.optin = "defaulted";
  defineLazyInternal(inst, "values", (zod) => zod.def.innerType._zod.values);
  inst._zod.parse = (payload, ctx) => {
    if (ctx.direction === "backward") {
      return def.innerType._zod.run(payload, ctx);
    }
    if (payload.value === void 0) {
      payload.value = def.defaultValue;
    }
    return def.innerType._zod.run(payload, ctx);
  };
});
var $ZodNonOptional = /* @__PURE__ */ $constructor("$ZodNonOptional", (inst, def) => {
  $ZodType.init(inst, def);
  defineLazyInternal(inst, "values", (zod) => {
    const v = zod.def.innerType._zod.values;
    return v ? new Set([...v].filter((x) => x !== void 0)) : void 0;
  });
  inst._zod.parse = (payload, ctx) => {
    const result = def.innerType._zod.run(payload, ctx);
    if (result instanceof Promise) {
      return result.then((result2) => handleNonOptionalResult(result2, inst));
    }
    return handleNonOptionalResult(result, inst);
  };
});
function handleNonOptionalResult(payload, inst) {
  if (!payload.issues.length && payload.value === void 0) {
    payload.issues.push({
      code: "invalid_type",
      expected: "nonoptional",
      input: payload.value,
      inst
    });
  }
  return payload;
}
function handleCatchResult(payload, result, def, ctx) {
  if (!result.issues.length) {
    payload.value = result.value;
    if (result.memo)
      payload.memo = true;
    return payload;
  }
  payload.value = def.catchValue({
    ...result,
    value: payload.value,
    error: {
      issues: result.issues.map((iss) => finalizeIssue(iss, ctx, config()))
    },
    input: payload.value
  });
  return payload;
}
var $ZodCatch = /* @__PURE__ */ $constructor("$ZodCatch", (inst, def) => {
  $ZodType.init(inst, def);
  defineLazyInternal(inst, "optin", (zod) => zod.def.innerType._zod.optin === "defaulted" ? "defaulted" : "optional");
  defineLazyInternal(inst, "optout", (zod) => zod.def.innerType._zod.optout);
  defineLazyInternal(inst, "values", (zod) => zod.def.innerType._zod.values);
  inst._zod.parse = (payload, ctx) => {
    if (ctx.direction === "backward") {
      return def.innerType._zod.run(payload, ctx);
    }
    const result = def.innerType._zod.run({ value: payload.value, issues: [] }, ctx);
    if (result instanceof Promise) {
      return result.then((result2) => handleCatchResult(payload, result2, def, ctx));
    }
    return handleCatchResult(payload, result, def, ctx);
  };
});
var $ZodPipe = /* @__PURE__ */ $constructor("$ZodPipe", (inst, def) => {
  $ZodType.init(inst, def);
  defineLazyInternal(inst, "values", (zod) => zod.def.in._zod.values);
  defineLazyInternal(inst, "optin", (zod) => zod.def.in._zod.optin);
  defineLazyInternal(inst, "optout", (zod) => zod.def.out._zod.optout);
  defineLazyInternal(inst, "propValues", (zod) => zod.def.in._zod.propValues);
  inst._zod.parse = (payload, ctx) => {
    if (ctx.direction === "backward") {
      const right = def.out._zod.run(payload, ctx);
      if (right instanceof Promise) {
        return right.then((right2) => handlePipeResult(right2, def.in, ctx));
      }
      return handlePipeResult(right, def.in, ctx);
    }
    const left = def.in._zod.run(payload, ctx);
    if (left instanceof Promise) {
      return left.then((left2) => handlePipeResult(left2, def.out, ctx));
    }
    return handlePipeResult(left, def.out, ctx);
  };
});
function handlePipeResult(left, next, ctx) {
  if (left.issues.some((iss) => iss.code !== "unrecognized_keys")) {
    left.aborted = true;
    return left;
  }
  return next._zod.run({ value: left.value, issues: left.issues }, ctx);
}
var $ZodReadonly = /* @__PURE__ */ $constructor("$ZodReadonly", (inst, def) => {
  $ZodType.init(inst, def);
  defineLazyInternal(inst, "propValues", (zod) => zod.def.innerType._zod.propValues);
  defineLazyInternal(inst, "values", (zod) => zod.def.innerType._zod.values);
  defineLazyInternal(inst, "optin", (zod) => zod.def.innerType?._zod?.optin);
  defineLazyInternal(inst, "optout", (zod) => zod.def.innerType?._zod?.optout);
  inst._zod.parse = (payload, ctx) => {
    if (ctx.direction === "backward") {
      return def.innerType._zod.run(payload, ctx);
    }
    const result = def.innerType._zod.run(payload, ctx);
    if (result instanceof Promise) {
      return result.then(handleReadonlyResult);
    }
    return handleReadonlyResult(result);
  };
});
function handleReadonlyResult(payload) {
  if (!payload.memo)
    payload.value = Object.freeze(payload.value);
  return payload;
}
var $ZodCustom = /* @__PURE__ */ $constructor("$ZodCustom", (inst, def) => {
  $ZodCheck.init(inst, def);
  $ZodType.init(inst, def);
  inst._zod.parse = (payload, _) => {
    return payload;
  };
  inst._zod.check = (payload) => {
    const input = payload.value;
    const r = def.fn(input);
    if (r instanceof Promise) {
      return r.then((r2) => handleRefineResult(r2, payload, input, inst));
    }
    handleRefineResult(r, payload, input, inst);
    return;
  };
});
function handleRefineResult(result, payload, input, inst) {
  if (!result) {
    const _iss = {
      code: "custom",
      input,
      inst,
      // incorporates params.error into issue reporting
      path: [...inst._zod.def.path ?? []],
      // incorporates params.error into issue reporting
      continue: !inst._zod.def.abort
      // params: inst._zod.def.params,
    };
    if (inst._zod.def.params)
      _iss.params = inst._zod.def.params;
    payload.issues.push(issue(_iss));
  }
}

// node_modules/zod/v4/core/memoizer.js
var $ZodCyclicError = class extends Error {
  constructor() {
    super(`Cannot parse a reference cycle that closes through a transform`);
    this.name = "ZodCyclicError";
  }
};
var STATE = "~memo";
var NO_ISSUES = [];
function isRef(value) {
  return value !== null && typeof value === "object";
}
function cloneIssues(issues) {
  return issues.map((iss) => iss.path ? { ...iss, path: iss.path.slice() } : { ...iss });
}
var recursive = /* @__PURE__ */ new WeakMap();
var NONE = 0;
var ASSUMED = 1;
var PROVEN = 2;
function isRecursive(inst, stack, resolve) {
  const cached2 = recursive.get(inst);
  if (cached2 !== void 0)
    return cached2 ? PROVEN : NONE;
  if (stack.has(inst))
    return PROVEN;
  stack.add(inst);
  let result = NONE;
  const check = (child) => {
    if (result !== PROVEN && child?._zod) {
      const answer = isRecursive(child, stack, resolve);
      if (answer > result)
        result = answer;
    }
  };
  const shape = (sh, spread) => {
    let answer = NONE;
    for (const key of Reflect.ownKeys(sh)) {
      const desc = Object.getOwnPropertyDescriptor(sh, key);
      if (spread && !desc.enumerable)
        continue;
      const child = desc.get ? ASSUMED : desc.value?._zod ? isRecursive(desc.value, stack, resolve) : NONE;
      if (child > answer)
        answer = child;
    }
    return answer;
  };
  const merge2 = (answer) => {
    if (answer > result)
      result = answer;
  };
  const def = inst._zod.def;
  const kind = def.type;
  switch (kind) {
    case "object": {
      const raw = rawShape(def);
      merge2(raw ? shape(raw, true) : ASSUMED);
      check(def.catchall);
      break;
    }
    case "array":
      check(def.element);
      break;
    case "tuple":
      for (const el of def.items)
        check(el);
      check(def.rest);
      break;
    case "record":
    case "map":
      check(def.keyType);
      check(def.valueType);
      break;
    case "set":
      check(def.valueType);
      break;
    case "union":
      for (const el of def.options)
        check(el);
      break;
    case "intersection":
      check(def.left);
      check(def.right);
      break;
    case "optional":
    case "nullable":
    case "default":
    case "prefault":
    case "catch":
    case "readonly":
    case "nonoptional":
    case "promise":
    case "success":
      check(def.innerType);
      break;
    case "pipe":
      check(def.in);
      check(def.out);
      break;
    case "function":
      check(def.input);
      check(def.output);
      break;
    // `$ZodLazy` caches its inner on the def, so a resolved edge is followed exactly
    case "lazy": {
      const inner = def._cachedInner ?? (resolve ? inst._zod.innerType : void 0);
      merge2(inner ? isRecursive(inner, stack, false) : ASSUMED);
      break;
    }
    // a leaf by choice: `parts` are regex fragments, not data positions
    case "template_literal":
    // leaves
    case "string":
    case "number":
    case "int":
    case "boolean":
    case "bigint":
    case "symbol":
    case "undefined":
    case "null":
    case "void":
    case "never":
    case "any":
    case "unknown":
    case "date":
    case "nan":
    case "enum":
    case "literal":
    case "file":
    case "transform":
    case "custom":
      break;
    default: {
      kind;
      for (const key in def) {
        const desc = Object.getOwnPropertyDescriptor(def, key);
        if (!desc || desc.get)
          continue;
        const value = desc.value;
        if (!value || typeof value !== "object")
          continue;
        if (value._zod)
          check(value);
        else if (Array.isArray(value))
          for (const el of value)
            check(el);
      }
    }
  }
  stack.delete(inst);
  return settle(inst, result);
}
function settle(inst, answer) {
  if (answer !== ASSUMED)
    recursive.set(inst, answer === PROVEN);
  return answer;
}
function bucketFor(state, inst) {
  let bucket = state.buckets.get(inst);
  if (!bucket) {
    bucket = /* @__PURE__ */ new WeakMap();
    state.buckets.set(inst, bucket);
  }
  return bucket;
}
var handoff;
var open = [];
var memo = {
  alloc(_inst, payload, empty) {
    const bucket = handoff;
    if (!bucket)
      return empty;
    handoff = void 0;
    const entry = { value: empty, issues: null };
    bucket.set(payload.value, entry);
    open.push(entry);
    return empty;
  },
  guard(inst) {
    var _a3;
    (_a3 = inst._zod).deferred ?? (_a3.deferred = []);
    inst._zod.deferred.push(() => {
      const base = inst._zod.parse;
      const wrapped = (payload, ctx) => {
        if (ctx.direction !== "backward" && isBackEdge(ctx, payload.value))
          throw new $ZodCyclicError();
        return base(payload, ctx);
      };
      inst._zod.parse = wrapped;
      if (inst._zod.run === base)
        inst._zod.run = wrapped;
    });
  },
  attach(inst) {
    var _a3;
    let isRecursiveInst;
    let rechecked = false;
    let lastCtx;
    let lastBucket;
    (_a3 = inst._zod).deferred ?? (_a3.deferred = []);
    inst._zod.deferred.push(() => {
      const base = inst._zod.parse;
      const wrapped = (payload, ctx) => {
        if (isRecursiveInst === void 0) {
          const walked = isRecursive(inst, /* @__PURE__ */ new Set(), false);
          if (walked === NONE) {
            inst._zod.parse = base;
            if (inst._zod.run === wrapped)
              inst._zod.run = base;
            return base(payload, ctx);
          }
          if (walked === PROVEN || rechecked)
            isRecursiveInst = true;
          else
            rechecked = true;
        }
        const input = payload.value;
        if (!isRef(input))
          return base(payload, ctx);
        let state = ctx[STATE];
        if (!state) {
          state = { buckets: /* @__PURE__ */ new WeakMap(), backEdges: void 0 };
          ctx[STATE] = state;
        }
        let bucket;
        if (lastCtx === ctx) {
          bucket = lastBucket;
        } else {
          bucket = bucketFor(state, inst);
          lastCtx = ctx;
          lastBucket = bucket;
        }
        const hit = bucket.get(input);
        if (hit) {
          payload.value = hit.value;
          if (hit.issues) {
            if (hit.issues.length)
              payload.issues.push(...cloneIssues(hit.issues));
          } else {
            payload.memo = true;
            state.backEdges ?? (state.backEdges = /* @__PURE__ */ new WeakSet());
            state.backEdges.add(hit.value);
          }
          return payload;
        }
        handoff = bucket;
        const depth = open.length;
        const result = base(payload, ctx);
        handoff = void 0;
        const entry = open.length > depth ? open.pop() : void 0;
        if (result instanceof Promise) {
          return result.then((r) => {
            if (entry)
              entry.issues = r.issues.length ? cloneIssues(r.issues) : NO_ISSUES;
            return r;
          });
        }
        if (entry)
          entry.issues = result.issues.length ? cloneIssues(result.issues) : NO_ISSUES;
        return result;
      };
      inst._zod.parse = wrapped;
      if (inst._zod.run === base)
        inst._zod.run = wrapped;
    });
  }
};
function memoizer() {
  return memo;
}
function isBackEdge(ctx, value) {
  const backEdges = ctx[STATE]?.backEdges;
  return backEdges !== void 0 && isRef(value) && backEdges.has(value);
}

// node_modules/zod/v4/locales/en.js
var error = () => {
  const Sizable = {
    string: { unit: "characters", verb: "to have" },
    file: { unit: "bytes", verb: "to have" },
    array: { unit: "items", verb: "to have" },
    set: { unit: "items", verb: "to have" },
    map: { unit: "entries", verb: "to have" }
  };
  function getSizing(origin) {
    return Sizable[origin] ?? null;
  }
  const FormatDictionary = {
    regex: "input",
    email: "email address",
    url: "URL",
    emoji: "emoji",
    uuid: "UUID",
    uuidv4: "UUIDv4",
    uuidv6: "UUIDv6",
    nanoid: "nanoid",
    guid: "GUID",
    cuid: "cuid",
    cuid2: "cuid2",
    ulid: "ULID",
    xid: "XID",
    ksuid: "KSUID",
    datetime: "ISO datetime",
    date: "ISO date",
    time: "ISO time",
    duration: "ISO duration",
    ipv4: "IPv4 address",
    ipv6: "IPv6 address",
    mac: "MAC address",
    cidrv4: "IPv4 range",
    cidrv6: "IPv6 range",
    base64: "base64-encoded string",
    base64url: "base64url-encoded string",
    json_string: "JSON string",
    e164: "E.164 number",
    currency_code: "currency code",
    credit_card: "credit card number",
    iban: "IBAN",
    jwt: "JWT",
    template_literal: "input"
  };
  const TypeDictionary = {
    // Compatibility: "nan" -> "NaN" for display
    nan: "NaN"
    // All other type names omitted - they fall back to raw values via ?? operator
  };
  function getTypeName(type, input) {
    if (type === "number" && typeof input === "number" && !Number.isFinite(input)) {
      return String(input);
    }
    return TypeDictionary[type] ?? type;
  }
  return (issue2) => {
    switch (issue2.code) {
      case "invalid_type": {
        const expected = getTypeName(issue2.expected);
        const receivedType = parsedType(issue2.input);
        const received = getTypeName(receivedType, issue2.input);
        return `Invalid input: expected ${expected}, received ${received}`;
      }
      case "invalid_value":
        if (issue2.values.length === 1)
          return `Invalid input: expected ${stringifyPrimitive(issue2.values[0])}`;
        return `Invalid option: expected one of ${joinValues(issue2.values, "|")}`;
      case "too_big": {
        const adj = issue2.exact ? "exactly " : issue2.inclusive ? "<=" : "<";
        const sizing = getSizing(issue2.origin);
        if (sizing)
          return `Too big: expected ${issue2.origin ?? "value"} to have ${adj}${issue2.maximum.toString()} ${sizing.unit ?? "elements"}`;
        return `Too big: expected ${issue2.origin ?? "value"} to be ${adj}${issue2.maximum.toString()}`;
      }
      case "too_small": {
        const adj = issue2.exact ? "exactly " : issue2.inclusive ? ">=" : ">";
        const sizing = getSizing(issue2.origin);
        if (sizing) {
          return `Too small: expected ${issue2.origin} to have ${adj}${issue2.minimum.toString()} ${sizing.unit}`;
        }
        return `Too small: expected ${issue2.origin} to be ${adj}${issue2.minimum.toString()}`;
      }
      case "invalid_format": {
        const _issue = issue2;
        if (_issue.format === "starts_with") {
          return `Invalid string: must start with "${_issue.prefix}"`;
        }
        if (_issue.format === "ends_with")
          return `Invalid string: must end with "${_issue.suffix}"`;
        if (_issue.format === "includes")
          return `Invalid string: must include "${_issue.includes}"`;
        if (_issue.format === "regex")
          return `Invalid string: must match pattern ${_issue.pattern}`;
        return `Invalid ${FormatDictionary[_issue.format] ?? issue2.format}`;
      }
      case "not_multiple_of":
        return `Invalid number: must be a multiple of ${issue2.divisor}`;
      case "unrecognized_keys":
        return `Unrecognized key${issue2.keys.length > 1 ? "s" : ""}: ${joinValues(issue2.keys, ", ")}`;
      case "invalid_key":
        return `Invalid key in ${issue2.origin}`;
      case "invalid_union":
        if (issue2.options && Array.isArray(issue2.options) && issue2.options.length > 0) {
          const opts = issue2.options.map((o) => `'${o}'`).join(" | ");
          return `Invalid discriminator value. Expected ${opts}`;
        }
        if (issue2.inclusive === false) {
          return "Invalid input: more than one option matched";
        }
        return "Invalid input";
      case "invalid_element":
        return `Invalid value in ${issue2.origin}`;
      default:
        return `Invalid input`;
    }
  };
};
function en_default() {
  return {
    localeError: error()
  };
}

// node_modules/zod/v4/core/registries.js
var _a2;
var $ZodRegistry = class {
  constructor() {
    this._map = /* @__PURE__ */ new WeakMap();
    this._idmap = /* @__PURE__ */ new Map();
  }
  add(schema, ..._meta) {
    const meta2 = _meta[0];
    this._map.set(schema, meta2);
    if (meta2 && typeof meta2 === "object" && "id" in meta2) {
      this._idmap.set(meta2.id, schema);
    }
    return this;
  }
  clear() {
    this._map = /* @__PURE__ */ new WeakMap();
    this._idmap = /* @__PURE__ */ new Map();
    return this;
  }
  remove(schema) {
    const meta2 = this._map.get(schema);
    if (meta2 && typeof meta2 === "object" && "id" in meta2) {
      this._idmap.delete(meta2.id);
    }
    this._map.delete(schema);
    return this;
  }
  get(schema) {
    const p = schema._zod.parent;
    if (p) {
      const pm = { ...this.get(p) ?? {} };
      delete pm.id;
      const f = { ...pm, ...this._map.get(schema) };
      return Object.keys(f).length ? f : void 0;
    }
    return this._map.get(schema);
  }
  has(schema) {
    return this._map.has(schema);
  }
};
function registry() {
  return new $ZodRegistry();
}
(_a2 = globalThis).__zod_globalRegistry ?? (_a2.__zod_globalRegistry = registry());
var globalRegistry = globalThis.__zod_globalRegistry;

// node_modules/zod/v4/core/api.js
function snapshotChecks(def) {
  if (def.checks)
    def.checks = [...def.checks];
  return def;
}
// @__NO_SIDE_EFFECTS__
function _string(Class2, params) {
  return new Class2(snapshotChecks({ type: "string", ...normalizeParams(params) }));
}
// @__NO_SIDE_EFFECTS__
function _email(Class2, params) {
  return new Class2({
    type: "string",
    format: "email",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _guid(Class2, params) {
  return new Class2({
    type: "string",
    format: "guid",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _uuid(Class2, params) {
  return new Class2({
    type: "string",
    format: "uuid",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _uuidv4(Class2, params) {
  return new Class2({
    type: "string",
    format: "uuid",
    check: "string_format",
    abort: false,
    version: "v4",
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _uuidv6(Class2, params) {
  return new Class2({
    type: "string",
    format: "uuid",
    check: "string_format",
    abort: false,
    version: "v6",
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _uuidv7(Class2, params) {
  return new Class2({
    type: "string",
    format: "uuid",
    check: "string_format",
    abort: false,
    version: "v7",
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _url(Class2, params) {
  return new Class2({
    type: "string",
    format: "url",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _emoji2(Class2, params) {
  return new Class2({
    type: "string",
    format: "emoji",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _nanoid(Class2, params) {
  return new Class2({
    type: "string",
    format: "nanoid",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _cuid(Class2, params) {
  return new Class2({
    type: "string",
    format: "cuid",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _cuid2(Class2, params) {
  return new Class2({
    type: "string",
    format: "cuid2",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _ulid(Class2, params) {
  return new Class2({
    type: "string",
    format: "ulid",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _xid(Class2, params) {
  return new Class2({
    type: "string",
    format: "xid",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _ksuid(Class2, params) {
  return new Class2({
    type: "string",
    format: "ksuid",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _ipv4(Class2, params) {
  return new Class2({
    type: "string",
    format: "ipv4",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _ipv6(Class2, params) {
  return new Class2({
    type: "string",
    format: "ipv6",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _cidrv4(Class2, params) {
  return new Class2({
    type: "string",
    format: "cidrv4",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _cidrv6(Class2, params) {
  return new Class2({
    type: "string",
    format: "cidrv6",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _base64(Class2, params) {
  return new Class2({
    type: "string",
    format: "base64",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _base64url(Class2, params) {
  return new Class2({
    type: "string",
    format: "base64url",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _e164(Class2, params) {
  return new Class2({
    type: "string",
    format: "e164",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _jwt(Class2, params) {
  return new Class2({
    type: "string",
    format: "jwt",
    check: "string_format",
    abort: false,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _isoDateTime(Class2, params) {
  return new Class2({
    type: "string",
    format: "datetime",
    check: "string_format",
    offset: false,
    local: false,
    precision: null,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _isoDate(Class2, params) {
  return new Class2({
    type: "string",
    format: "date",
    check: "string_format",
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _isoTime(Class2, params) {
  return new Class2({
    type: "string",
    format: "time",
    check: "string_format",
    precision: null,
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _isoDuration(Class2, params) {
  return new Class2({
    type: "string",
    format: "duration",
    check: "string_format",
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _number(Class2, params) {
  return new Class2(snapshotChecks({ type: "number", checks: [], ...normalizeParams(params) }));
}
// @__NO_SIDE_EFFECTS__
function _int(Class2, params) {
  return new Class2({
    type: "number",
    check: "number_format",
    abort: false,
    format: "safeint",
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _boolean(Class2, params) {
  return new Class2({
    type: "boolean",
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _unknown(Class2) {
  return new Class2({
    type: "unknown"
  });
}
// @__NO_SIDE_EFFECTS__
function _never(Class2, params) {
  return new Class2({
    type: "never",
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _lt(value, params) {
  return new $ZodCheckLessThan({
    check: "less_than",
    ...normalizeParams(params),
    value,
    inclusive: false
  });
}
// @__NO_SIDE_EFFECTS__
function _lte(value, params) {
  return new $ZodCheckLessThan({
    check: "less_than",
    ...normalizeParams(params),
    value,
    inclusive: true
  });
}
// @__NO_SIDE_EFFECTS__
function _gt(value, params) {
  return new $ZodCheckGreaterThan({
    check: "greater_than",
    ...normalizeParams(params),
    value,
    inclusive: false
  });
}
// @__NO_SIDE_EFFECTS__
function _gte(value, params) {
  return new $ZodCheckGreaterThan({
    check: "greater_than",
    ...normalizeParams(params),
    value,
    inclusive: true
  });
}
// @__NO_SIDE_EFFECTS__
function _multipleOf(value, params) {
  return new $ZodCheckMultipleOf({
    check: "multiple_of",
    ...normalizeParams(params),
    value
  });
}
// @__NO_SIDE_EFFECTS__
function _maxLength(maximum, params) {
  const ch = new $ZodCheckMaxLength({
    check: "max_length",
    ...normalizeParams(params),
    maximum
  });
  return ch;
}
// @__NO_SIDE_EFFECTS__
function _minLength(minimum, params) {
  return new $ZodCheckMinLength({
    check: "min_length",
    ...normalizeParams(params),
    minimum
  });
}
// @__NO_SIDE_EFFECTS__
function _length(length, params) {
  return new $ZodCheckLengthEquals({
    check: "length_equals",
    ...normalizeParams(params),
    length
  });
}
// @__NO_SIDE_EFFECTS__
function _regex(pattern, params) {
  return new $ZodCheckRegex({
    check: "string_format",
    format: "regex",
    ...normalizeParams(params),
    pattern
  });
}
// @__NO_SIDE_EFFECTS__
function _lowercase(params) {
  return new $ZodCheckLowerCase({
    check: "string_format",
    format: "lowercase",
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _uppercase(params) {
  return new $ZodCheckUpperCase({
    check: "string_format",
    format: "uppercase",
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _includes(includes, params) {
  return new $ZodCheckIncludes({
    check: "string_format",
    format: "includes",
    ...normalizeParams(params),
    includes
  });
}
// @__NO_SIDE_EFFECTS__
function _startsWith(prefix, params) {
  return new $ZodCheckStartsWith({
    check: "string_format",
    format: "starts_with",
    ...normalizeParams(params),
    prefix
  });
}
// @__NO_SIDE_EFFECTS__
function _endsWith(suffix, params) {
  return new $ZodCheckEndsWith({
    check: "string_format",
    format: "ends_with",
    ...normalizeParams(params),
    suffix
  });
}
// @__NO_SIDE_EFFECTS__
function _overwrite(tx) {
  return new $ZodCheckOverwrite({
    check: "overwrite",
    tx
  });
}
// @__NO_SIDE_EFFECTS__
function _normalize(form) {
  return /* @__PURE__ */ _overwrite((input) => input.normalize(form));
}
// @__NO_SIDE_EFFECTS__
function _trim() {
  return /* @__PURE__ */ _overwrite((input) => input.trim());
}
// @__NO_SIDE_EFFECTS__
function _toLowerCase() {
  return /* @__PURE__ */ _overwrite((input) => input.toLowerCase());
}
// @__NO_SIDE_EFFECTS__
function _toUpperCase() {
  return /* @__PURE__ */ _overwrite((input) => input.toUpperCase());
}
// @__NO_SIDE_EFFECTS__
function _slugify() {
  return /* @__PURE__ */ _overwrite((input) => slugify(input));
}
// @__NO_SIDE_EFFECTS__
function _array(Class2, element, params) {
  return new Class2({
    type: "array",
    element,
    // get element() {
    //   return element;
    // },
    ...normalizeParams(params)
  });
}
// @__NO_SIDE_EFFECTS__
function _refine(Class2, fn, _params) {
  const schema = new Class2({
    type: "custom",
    check: "custom",
    fn,
    ...normalizeParams(_params)
  });
  return schema;
}
// @__NO_SIDE_EFFECTS__
function _superRefine(fn, params) {
  const ch = /* @__PURE__ */ _check((payload) => {
    payload.addIssue = (issue2) => {
      if (typeof issue2 === "string") {
        payload.issues.push(issue(issue2, payload.value, ch._zod.def));
      } else {
        const _issue = issue2;
        if (_issue.fatal)
          _issue.continue = false;
        _issue.code ?? (_issue.code = "custom");
        if (!("input" in _issue))
          _issue.input = payload.value;
        _issue.inst ?? (_issue.inst = ch);
        _issue.continue ?? (_issue.continue = !ch._zod.def.abort);
        payload.issues.push(issue(_issue));
      }
    };
    return fn(payload.value, payload);
  }, params);
  return ch;
}
// @__NO_SIDE_EFFECTS__
function _check(fn, params) {
  const ch = new $ZodCheck({
    check: "custom",
    ...normalizeParams(params)
  });
  ch._zod.check = fn;
  return ch;
}

// node_modules/zod/v4/core/to-json-schema.js
function assignProps(target, ...sources) {
  for (const source of sources) {
    for (const key of Reflect.ownKeys(source)) {
      if (Object.prototype.propertyIsEnumerable.call(source, key)) {
        assignProp(target, key, source[key]);
      }
    }
  }
  return target;
}
function initializeContext(params) {
  let target = params?.target ?? "draft-2020-12";
  if (target === "draft-4")
    target = "draft-04";
  if (target === "draft-7")
    target = "draft-07";
  return {
    processors: params.processors ?? {},
    metadataRegistry: params?.metadata ?? globalRegistry,
    target,
    unrepresentable: params?.unrepresentable ?? "throw",
    override: params?.override ?? (() => {
    }),
    io: params?.io ?? "output",
    counter: 0,
    seen: /* @__PURE__ */ new Map(),
    sharedDefsExtractedFor: void 0,
    sharedEmitDoneFor: void 0,
    cycles: params?.cycles ?? "ref",
    reused: params?.reused ?? "inline",
    intersections: [],
    deferred: [],
    external: params?.external ?? void 0
  };
}
function handleUnrepresentable(schema, ctx, json2, params, message) {
  const result = typeof ctx.unrepresentable === "function" ? ctx.unrepresentable({ zodSchema: schema, path: params.path, message }) : ctx.unrepresentable;
  if (result === "any")
    return false;
  if (result === void 0 || result === "throw")
    throw new Error(message);
  Object.assign(json2, result);
  return true;
}
function processSchema(schema, ctx, _params = { path: [], schemaPath: [] }) {
  var _a3;
  const def = schema._zod.def;
  const seen = ctx.seen.get(schema);
  if (seen) {
    seen.count++;
    const isCycle = _params.schemaPath.includes(schema);
    if (isCycle) {
      seen.cycle = _params.path;
    }
    return seen.schema;
  }
  const result = { schema: {}, count: 1, cycle: void 0, path: _params.path };
  ctx.seen.set(schema, result);
  ctx.sharedDefsExtractedFor = void 0;
  ctx.sharedEmitDoneFor = void 0;
  const overrideSchema = schema._zod.toJSONSchema?.();
  if (overrideSchema) {
    result.schema = overrideSchema;
  } else {
    const params = {
      ..._params,
      schemaPath: [..._params.schemaPath, schema],
      path: _params.path
    };
    if (schema._zod.processJSONSchema) {
      schema._zod.processJSONSchema(ctx, result.schema, params);
    } else {
      const _json = result.schema;
      const processor = ctx.processors[def.type];
      if (!processor) {
        throw new Error(`[toJSONSchema]: Non-representable type encountered: ${def.type}`);
      }
      processor(schema, ctx, _json, params);
    }
    const parent = schema._zod.parent;
    if (parent) {
      if (!result.ref)
        result.ref = parent;
      processSchema(parent, ctx, params);
      ctx.seen.get(parent).isParent = true;
    }
  }
  const meta2 = ctx.metadataRegistry.get(schema);
  if (meta2)
    assignProps(result.schema, meta2);
  if (ctx.io === "input" && isTransforming(schema)) {
    delete result.schema.examples;
    delete result.schema.default;
  }
  if (ctx.io === "input" && "_prefault" in result.schema)
    (_a3 = result.schema).default ?? (_a3.default = result.schema._prefault);
  delete result.schema._prefault;
  const _result = ctx.seen.get(schema);
  return _result.schema;
}
function encodeJSONPointerSegment(segment) {
  return segment.replace(/~/g, "~0").replace(/\//g, "~1");
}
function extractDefs(ctx, schema) {
  const root = ctx.seen.get(schema);
  if (!root)
    throw new Error("Unprocessed schema. This is a bug in Zod.");
  if (ctx.external && ctx.sharedDefsExtractedFor === ctx.external)
    return;
  const idToSchema = /* @__PURE__ */ new Map();
  for (const entry of ctx.seen.entries()) {
    const id = ctx.metadataRegistry.get(entry[0])?.id;
    if (id) {
      const existing = idToSchema.get(id);
      if (existing && existing !== entry[0]) {
        throw new Error(`Duplicate schema id "${id}" detected during JSON Schema conversion. Two different schemas cannot share the same id when converted together.`);
      }
      idToSchema.set(id, entry[0]);
    }
  }
  const makeURI = (entry) => {
    const defsSegment = ctx.target === "draft-2020-12" ? "$defs" : "definitions";
    if (ctx.external) {
      const externalId = ctx.external.registry.get(entry[0])?.id;
      const uriGenerator = ctx.external.uri ?? ((id2) => id2);
      if (externalId) {
        return { ref: uriGenerator(externalId) };
      }
      const id = entry[1].defId ?? entry[1].schema.id ?? `schema${ctx.counter++}`;
      entry[1].defId = id;
      return { defId: id, ref: `${uriGenerator("__shared")}#/${defsSegment}/${encodeJSONPointerSegment(id)}` };
    }
    const uriPrefix = `#`;
    const defUriPrefix = `${uriPrefix}/${defsSegment}/`;
    if (entry[1] === root && !entry[1].schema.id) {
      return { ref: uriPrefix };
    }
    const defId = entry[1].schema.id ?? `__schema${ctx.counter++}`;
    return { defId, ref: defUriPrefix + encodeJSONPointerSegment(defId) };
  };
  const extractToDef = (entry) => {
    if (entry[1].schema.$ref) {
      return;
    }
    const seen = entry[1];
    const { ref, defId } = makeURI(entry);
    seen.def = { ...seen.schema };
    if (defId)
      seen.defId = defId;
    const schema2 = seen.schema;
    for (const key in schema2) {
      delete schema2[key];
    }
    schema2.$ref = ref;
  };
  if (ctx.cycles === "throw") {
    for (const entry of ctx.seen.entries()) {
      const seen = entry[1];
      if (seen.cycle) {
        throw new Error(`Cycle detected: #/${seen.cycle?.join("/")}/<root>

Set the \`cycles\` parameter to \`"ref"\` to resolve cyclical schemas with defs.`);
      }
    }
  }
  for (const entry of ctx.seen.entries()) {
    const seen = entry[1];
    if (schema === entry[0]) {
      extractToDef(entry);
      continue;
    }
    if (ctx.external) {
      const ext = ctx.external.registry.get(entry[0])?.id;
      if (schema !== entry[0] && ext) {
        extractToDef(entry);
        continue;
      }
    }
    const id = ctx.metadataRegistry.get(entry[0])?.id;
    if (id) {
      extractToDef(entry);
      continue;
    }
    if (seen.cycle) {
      extractToDef(entry);
      continue;
    }
    if (seen.count > 1) {
      if (ctx.reused === "ref") {
        extractToDef(entry);
      }
    }
  }
  if (ctx.external)
    ctx.sharedDefsExtractedFor = ctx.external;
}
function compactTypeUnion(schema) {
  const options = schema.anyOf;
  if (!Array.isArray(options) || options.length === 0 || schema.type !== void 0)
    return;
  const types = [];
  for (const option of options) {
    if (!option || typeof option !== "object")
      return;
    compactTypeUnion(option);
    const keys = Object.keys(option);
    if (keys.length !== 1 || keys[0] !== "type")
      return;
    const type = option.type;
    for (const member of Array.isArray(type) ? type : [type]) {
      if (typeof member !== "string")
        return;
      if (!types.includes(member))
        types.push(member);
    }
  }
  delete schema.anyOf;
  schema.type = types.length === 1 ? types[0] : types;
}
var FOLDABLE_KEYS = /* @__PURE__ */ new Set(["type", "properties", "required", "additionalProperties"]);
var UNION_KEYS = ["oneOf", "anyOf"];
function undeclaredConstraint(member) {
  const extra = member.additionalProperties;
  if (extra === void 0 || extra === false || typeof extra !== "object" || extra === null)
    return null;
  return Object.keys(extra).length ? extra : null;
}
function foldObjects(members2) {
  const objects = [];
  for (const member of members2) {
    if (typeof member !== "object" || member.type !== "object")
      return null;
    for (const key in member) {
      if (!FOLDABLE_KEYS.has(key))
        return null;
    }
    objects.push(member);
  }
  const properties = {};
  const required2 = /* @__PURE__ */ new Set();
  for (const object of objects) {
    for (const key in object.properties) {
      if (Object.prototype.hasOwnProperty.call(properties, key))
        continue;
      const parts = [];
      for (const other of objects) {
        const part = other.properties?.[key] ?? undeclaredConstraint(other);
        if (part === null || part === void 0)
          continue;
        if (!parts.some((seen) => JSON.stringify(seen) === JSON.stringify(part)))
          parts.push(part);
      }
      const merged = parts.length === 1 ? parts[0] : foldObjects(parts) ?? { allOf: parts };
      assignProp(properties, key, merged);
    }
    for (const key of object.required ?? [])
      required2.add(key);
  }
  const folded = { type: "object", properties };
  if (required2.size)
    folded.required = [...required2];
  if (objects.every((object) => object.additionalProperties === false)) {
    folded.additionalProperties = false;
  } else {
    const constraints = [];
    for (const object of objects) {
      const constraint = undeclaredConstraint(object);
      if (constraint && !constraints.some((seen) => JSON.stringify(seen) === JSON.stringify(constraint)))
        constraints.push(constraint);
    }
    if (constraints.length === 1)
      folded.additionalProperties = constraints[0];
    else if (constraints.length > 1)
      folded.additionalProperties = { allOf: constraints };
  }
  return folded;
}
function foldIntersection(json2) {
  const allOf = json2.allOf;
  if (!Array.isArray(allOf) || allOf.length < 2)
    return;
  for (const key of FOLDABLE_KEYS)
    if (key in json2)
      return;
  const unions = allOf.filter((m) => UNION_KEYS.some((k) => Array.isArray(m[k])));
  let folded = null;
  if (!unions.length) {
    folded = foldObjects(allOf);
  } else {
    const union2 = unions[0];
    const keyword = UNION_KEYS.find((k) => Array.isArray(union2[k]));
    if (Object.keys(union2).length !== 1)
      return;
    const rest = allOf.filter((m) => m !== union2);
    const branches = union2[keyword].map((branch) => foldObjects([...rest, branch]));
    if (branches.some((b) => !b))
      return;
    folded = { [keyword]: branches };
  }
  if (!folded)
    return;
  delete json2.allOf;
  assignProps(json2, folded);
}
function finalize(ctx, schema) {
  const root = ctx.seen.get(schema);
  if (!root)
    throw new Error("Unprocessed schema. This is a bug in Zod.");
  const flattenRef = (zodSchema) => {
    const seen = ctx.seen.get(zodSchema);
    if (seen.ref === null)
      return;
    const schema2 = seen.def ?? seen.schema;
    const _cached = { ...schema2 };
    const ref = seen.ref;
    seen.ref = null;
    if (ref) {
      flattenRef(ref);
      const refSeen = ctx.seen.get(ref);
      const refSchema = refSeen.schema;
      if (refSchema.$ref && (ctx.target === "draft-07" || ctx.target === "draft-04" || ctx.target === "openapi-3.0")) {
        schema2.allOf = schema2.allOf ?? [];
        schema2.allOf.push(refSchema);
      } else {
        assignProps(schema2, refSchema);
      }
      assignProps(schema2, _cached);
      const isParentRef = zodSchema._zod.parent === ref;
      if (isParentRef) {
        for (const key in schema2) {
          if (key === "$ref" || key === "allOf")
            continue;
          if (!(key in _cached)) {
            delete schema2[key];
          }
        }
      }
      if (refSchema.$ref && refSeen.def) {
        for (const key in schema2) {
          if (key === "$ref" || key === "allOf")
            continue;
          if (key in refSeen.def && JSON.stringify(schema2[key]) === JSON.stringify(refSeen.def[key])) {
            delete schema2[key];
          }
        }
      }
    }
    const parent = zodSchema._zod.parent;
    if (parent && parent !== ref) {
      flattenRef(parent);
      const parentSeen = ctx.seen.get(parent);
      if (parentSeen?.schema.$ref) {
        schema2.$ref = parentSeen.schema.$ref;
        if (parentSeen.def) {
          for (const key in schema2) {
            if (key === "$ref" || key === "allOf")
              continue;
            if (key in parentSeen.def && JSON.stringify(schema2[key]) === JSON.stringify(parentSeen.def[key])) {
              delete schema2[key];
            }
          }
        }
      }
    }
    ctx.override({
      zodSchema,
      jsonSchema: schema2,
      path: seen.path ?? []
    });
  };
  if (!ctx.external || ctx.sharedEmitDoneFor !== ctx.external) {
    for (const entry of [...ctx.seen.entries()].reverse()) {
      flattenRef(entry[0]);
    }
    if (ctx.target !== "openapi-3.0") {
      for (const entry of ctx.seen.entries()) {
        compactTypeUnion(entry[1].def ?? entry[1].schema);
      }
    }
    for (const rewrite of ctx.deferred)
      rewrite();
    if (ctx.intersections.length) {
      const carriers = /* @__PURE__ */ new Map();
      for (const seen of ctx.seen.values()) {
        for (const json2 of [seen.schema, seen.def]) {
          const allOf = json2?.allOf;
          if (!Array.isArray(allOf))
            continue;
          const existing = carriers.get(allOf);
          if (existing)
            existing.push(json2);
          else
            carriers.set(allOf, [json2]);
        }
      }
      for (const allOf of ctx.intersections) {
        for (const json2 of carriers.get(allOf) ?? [])
          foldIntersection(json2);
      }
    }
  }
  const result = {};
  if (ctx.target === "draft-2020-12") {
    result.$schema = "https://json-schema.org/draft/2020-12/schema";
  } else if (ctx.target === "draft-07") {
    result.$schema = "http://json-schema.org/draft-07/schema#";
  } else if (ctx.target === "draft-04") {
    result.$schema = "http://json-schema.org/draft-04/schema#";
  } else if (ctx.target === "openapi-3.0") {
  } else {
  }
  if (ctx.external?.uri) {
    const id = ctx.external.registry.get(schema)?.id;
    if (!id)
      throw new Error("Schema is missing an `id` property");
    result.$id = ctx.external.uri(id);
  }
  assignProps(result, root.defId ? root.schema : root.def ?? root.schema);
  const rootMetaId = ctx.metadataRegistry.get(schema)?.id;
  if (rootMetaId !== void 0 && result.id === rootMetaId)
    delete result.id;
  const defs = ctx.external?.defs ?? {};
  if (!ctx.external || ctx.sharedEmitDoneFor !== ctx.external) {
    for (const entry of ctx.seen.entries()) {
      const seen = entry[1];
      if (seen.def && seen.defId) {
        if (seen.def.id === seen.defId)
          delete seen.def.id;
        assignProp(defs, seen.defId, seen.def);
      }
    }
  }
  if (ctx.external)
    ctx.sharedEmitDoneFor = ctx.external;
  if (ctx.external) {
  } else {
    if (Object.keys(defs).length > 0) {
      if (ctx.target === "draft-2020-12") {
        result.$defs = defs;
      } else {
        result.definitions = defs;
      }
    }
  }
  try {
    const finalized = JSON.parse(JSON.stringify(result));
    Object.defineProperty(finalized, "~standard", {
      value: {
        ...schema["~standard"],
        jsonSchema: {
          input: createStandardJSONSchemaMethod(schema, "input", ctx.processors),
          output: createStandardJSONSchemaMethod(schema, "output", ctx.processors)
        }
      },
      enumerable: false,
      writable: false
    });
    return finalized;
  } catch (_err) {
    throw new Error("Error converting schema to JSON.");
  }
}
function isTransforming(_schema, _ctx) {
  const ctx = _ctx ?? { seen: /* @__PURE__ */ new Set() };
  if (ctx.seen.has(_schema))
    return false;
  ctx.seen.add(_schema);
  const def = _schema._zod.def;
  if (def.type === "transform")
    return true;
  if (def.type === "array")
    return isTransforming(def.element, ctx);
  if (def.type === "set")
    return isTransforming(def.valueType, ctx);
  if (def.type === "lazy")
    return isTransforming(def.getter(), ctx);
  if (def.type === "promise" || def.type === "optional" || def.type === "nonoptional" || def.type === "nullable" || def.type === "readonly" || def.type === "default" || def.type === "prefault" || def.type === "catch") {
    return isTransforming(def.innerType, ctx);
  }
  if (def.type === "intersection") {
    return isTransforming(def.left, ctx) || isTransforming(def.right, ctx);
  }
  if (def.type === "record" || def.type === "map") {
    return isTransforming(def.keyType, ctx) || isTransforming(def.valueType, ctx);
  }
  if (def.type === "pipe") {
    if (_schema._zod.traits.has("$ZodCodec"))
      return true;
    return isTransforming(def.in, ctx) || isTransforming(def.out, ctx);
  }
  if (def.type === "object") {
    for (const key in def.shape) {
      if (isTransforming(def.shape[key], ctx))
        return true;
    }
    return false;
  }
  if (def.type === "union") {
    for (const option of def.options) {
      if (isTransforming(option, ctx))
        return true;
    }
    return false;
  }
  if (def.type === "tuple") {
    for (const item of def.items) {
      if (isTransforming(item, ctx))
        return true;
    }
    if (def.rest && isTransforming(def.rest, ctx))
      return true;
    return false;
  }
  return false;
}
var createToJSONSchemaMethod = (schema, processors = {}) => (params) => {
  const ctx = initializeContext({ ...params, processors });
  processSchema(schema, ctx);
  extractDefs(ctx, schema);
  return finalize(ctx, schema);
};
var createStandardJSONSchemaMethod = (schema, io, processors = {}) => (params) => {
  const { libraryOptions, target } = params ?? {};
  const ctx = initializeContext({ ...libraryOptions ?? {}, target, io, processors });
  processSchema(schema, ctx);
  extractDefs(ctx, schema);
  return finalize(ctx, schema);
};

// node_modules/zod/v4/core/json-schema-processors.js
var narrowMin = (agg, key, value) => {
  if (agg[key] === void 0 || value > agg[key])
    agg[key] = value;
};
var narrowMax = (agg, key, value) => {
  if (agg[key] === void 0 || value < agg[key])
    agg[key] = value;
};
var narrowBoth = (agg, value) => {
  narrowMin(agg, "minimum", value);
  narrowMax(agg, "maximum", value);
};
var addDivisor = (agg, value) => {
  agg.multipleOf ?? (agg.multipleOf = []);
  if (!agg.multipleOf.includes(value))
    agg.multipleOf.push(value);
};
var addPattern = (agg, pattern) => {
  agg.patterns ?? (agg.patterns = /* @__PURE__ */ new Set());
  agg.patterns.add(pattern);
};
var intersectMime = (agg, mime) => {
  agg.mime = agg.mime ? agg.mime.filter((m) => mime.includes(m)) : [...mime];
};
var setFormat = (agg, format) => {
  agg.format = format;
  if (format.includes("int"))
    agg.isInt = true;
};
var minContributor = (agg, def) => narrowMin(agg, "minimum", def.minimum);
var maxContributor = (agg, def) => narrowMax(agg, "maximum", def.maximum);
var formatContributor = (ranges) => (agg, def) => {
  setFormat(agg, def.format);
  const [minimum, maximum] = ranges[def.format];
  narrowMin(agg, "minimum", minimum);
  narrowMax(agg, "maximum", maximum);
};
var contributors = {
  greater_than: (agg, def) => narrowMin(agg, def.inclusive ? "minimum" : "exclusiveMinimum", def.value),
  less_than: (agg, def) => narrowMax(agg, def.inclusive ? "maximum" : "exclusiveMaximum", def.value),
  multiple_of: (agg, def) => addDivisor(agg, def.value),
  number_format: formatContributor(NUMBER_FORMAT_RANGES),
  bigint_format: formatContributor(BIGINT_FORMAT_RANGES),
  min_length: minContributor,
  max_length: maxContributor,
  length_equals: (agg, def) => narrowBoth(agg, def.length),
  min_size: minContributor,
  max_size: maxContributor,
  size_equals: (agg, def) => narrowBoth(agg, def.size),
  string_format: (agg, def) => {
    setFormat(agg, def.format);
    if (def.pattern)
      addPattern(agg, def.pattern);
    if (def.format === "base64" || def.format === "base64url")
      agg.contentEncoding = def.format;
    if (def.local || def.precision === -1)
      agg.laxFormat = true;
  },
  mime_type: (agg, def) => intersectMime(agg, def.mime)
};
function aggregateChecks(schema) {
  const agg = {};
  const def = schema._zod.def;
  const list = schema._zod.traits.has("$ZodCheck") ? [schema, ...def.checks ?? []] : def.checks ?? [];
  for (const ch of list)
    contributors[ch._zod.def.check]?.(agg, ch._zod.def);
  const bag = schema._zod.bag;
  if (bag.minimum !== void 0)
    narrowMin(agg, "minimum", bag.minimum);
  if (bag.exclusiveMinimum !== void 0)
    narrowMin(agg, "exclusiveMinimum", bag.exclusiveMinimum);
  if (bag.maximum !== void 0)
    narrowMax(agg, "maximum", bag.maximum);
  if (bag.exclusiveMaximum !== void 0)
    narrowMax(agg, "exclusiveMaximum", bag.exclusiveMaximum);
  if (bag.multipleOf !== void 0)
    addDivisor(agg, bag.multipleOf);
  if (bag.format !== void 0) {
    agg.format ?? (agg.format = bag.format);
    if (bag.format.includes("int"))
      agg.isInt = true;
  }
  if (bag.mime)
    intersectMime(agg, bag.mime);
  for (const pattern of bag.patterns ?? [])
    addPattern(agg, pattern);
  return agg;
}
var formatMap = {
  guid: "uuid",
  url: "uri",
  datetime: "date-time",
  json_string: "json-string",
  regex: ""
  // do not set
};
var exactPatterns = /* @__PURE__ */ new Map([
  [base64Charset, base64],
  [base64urlCharset, base64url]
]);
var exactPattern = (p) => exactPatterns.get(p) ?? p;
var stringProcessor = (schema, ctx, _json, _params) => {
  const json2 = _json;
  json2.type = "string";
  const { minimum, maximum, format, patterns, contentEncoding, laxFormat } = aggregateChecks(schema);
  if (typeof minimum === "number")
    json2.minLength = minimum;
  if (typeof maximum === "number")
    json2.maxLength = maximum;
  if (format) {
    json2.format = formatMap[format] ?? format;
    if (json2.format === "")
      delete json2.format;
    if (format === "time" || laxFormat) {
      delete json2.format;
    }
  }
  if (contentEncoding)
    json2.contentEncoding = contentEncoding;
  if (patterns && patterns.size > 0) {
    const patternList = [...patterns].map(exactPattern);
    if (patternList.length === 1)
      json2.pattern = patternList[0].source;
    else if (patternList.length > 1) {
      json2.allOf = [
        ...patternList.map((regex) => ({
          ...ctx.target === "draft-07" || ctx.target === "draft-04" || ctx.target === "openapi-3.0" ? { type: "string" } : {},
          pattern: regex.source
        }))
      ];
    }
  }
};
var numberProcessor = (schema, ctx, _json, params) => {
  const json2 = _json;
  const { minimum, maximum, multipleOf, exclusiveMaximum, exclusiveMinimum, isInt } = aggregateChecks(schema);
  json2.type = isInt ? "integer" : "number";
  const exMin = typeof exclusiveMinimum === "number" && exclusiveMinimum >= (minimum ?? Number.NEGATIVE_INFINITY);
  const exMax = typeof exclusiveMaximum === "number" && exclusiveMaximum <= (maximum ?? Number.POSITIVE_INFINITY);
  const legacy = ctx.target === "draft-04" || ctx.target === "openapi-3.0";
  if (exMin) {
    if (legacy) {
      json2.minimum = exclusiveMinimum;
      json2.exclusiveMinimum = true;
    } else {
      json2.exclusiveMinimum = exclusiveMinimum;
    }
  } else if (typeof minimum === "number") {
    json2.minimum = minimum;
  }
  if (exMax) {
    if (legacy) {
      json2.maximum = exclusiveMaximum;
      json2.exclusiveMaximum = true;
    } else {
      json2.exclusiveMaximum = exclusiveMaximum;
    }
  } else if (typeof maximum === "number") {
    json2.maximum = maximum;
  }
  if (multipleOf) {
    const divisors = /* @__PURE__ */ new Set();
    for (const divisor of multipleOf) {
      if (Number.isFinite(divisor) && divisor !== 0)
        divisors.add(Math.abs(divisor));
      else
        handleUnrepresentable(schema, ctx, json2, params, `A multipleOf divisor of ${divisor} cannot be represented in JSON Schema`);
    }
    const [first, ...rest] = divisors;
    if (first !== void 0)
      json2.multipleOf = first;
    if (rest.length)
      json2.allOf = [...json2.allOf ?? [], ...rest.map((m) => ({ multipleOf: m }))];
  }
};
var booleanProcessor = (_schema, _ctx, json2, _params) => {
  json2.type = "boolean";
};
var neverProcessor = (_schema, _ctx, json2, _params) => {
  json2.not = {};
};
var unknownProcessor = (_schema, _ctx, _json, _params) => {
};
var enumProcessor = (schema, _ctx, json2, _params) => {
  const def = schema._zod.def;
  const values = getEnumValues(def.entries);
  if (values.length === 0) {
    json2.not = {};
    return;
  }
  if (values.every((v) => typeof v === "number"))
    json2.type = "number";
  if (values.every((v) => typeof v === "string"))
    json2.type = "string";
  json2.enum = values;
};
var literalProcessor = (schema, ctx, json2, params) => {
  const def = schema._zod.def;
  if (def.values.length === 0) {
    json2.not = {};
    return;
  }
  const vals = [];
  for (const val of def.values) {
    if (val === void 0) {
      if (handleUnrepresentable(schema, ctx, json2, params, "Literal `undefined` cannot be represented in JSON Schema"))
        return;
    } else if (typeof val === "bigint") {
      if (handleUnrepresentable(schema, ctx, json2, params, "BigInt literals cannot be represented in JSON Schema"))
        return;
      vals.push(Number(val));
    } else {
      vals.push(val);
    }
  }
  if (vals.length === 0) {
  } else if (vals.length === 1) {
    const val = vals[0];
    json2.type = val === null ? "null" : typeof val;
    if (ctx.target === "draft-04" || ctx.target === "openapi-3.0") {
      json2.enum = [val];
    } else {
      json2.const = val;
    }
  } else {
    if (vals.every((v) => typeof v === "number"))
      json2.type = "number";
    if (vals.every((v) => typeof v === "string"))
      json2.type = "string";
    if (vals.every((v) => typeof v === "boolean"))
      json2.type = "boolean";
    if (vals.every((v) => v === null))
      json2.type = "null";
    json2.enum = vals;
  }
};
var customProcessor = (schema, ctx, json2, params) => {
  handleUnrepresentable(schema, ctx, json2, params, "Custom types cannot be represented in JSON Schema");
};
var transformProcessor = (schema, ctx, json2, params) => {
  handleUnrepresentable(schema, ctx, json2, params, "Transforms cannot be represented in JSON Schema");
};
var arrayProcessor = (schema, ctx, _json, params) => {
  const json2 = _json;
  const def = schema._zod.def;
  const { minimum, maximum } = aggregateChecks(schema);
  if (typeof minimum === "number")
    json2.minItems = minimum;
  if (typeof maximum === "number")
    json2.maxItems = maximum;
  json2.type = "array";
  json2.items = processSchema(def.element, ctx, {
    ...params,
    path: [...params.path, "items"]
  });
};
function inputOptin(schema) {
  const def = schema._zod.def;
  if (def.type === "pipe" && def.in._zod.traits.has("$ZodTransform")) {
    return inputOptin(def.out);
  }
  if (def.type === "catch") {
    return inputOptin(def.innerType);
  }
  return schema._zod.optin;
}
var objectProcessor = (schema, ctx, _json, params) => {
  const json2 = _json;
  const def = schema._zod.def;
  const shape = def.shape;
  const symbolKeys = Object.getOwnPropertySymbols(shape);
  if (symbolKeys.length && handleUnrepresentable(schema, ctx, json2, params, "Symbol keys cannot be represented in JSON Schema")) {
    return;
  }
  json2.type = "object";
  json2.properties = {};
  for (const key in shape) {
    assignProp(json2.properties, key, processSchema(shape[key], ctx, {
      ...params,
      path: [...params.path, "properties", key]
    }));
  }
  const requiredKeys = [];
  for (const key of Object.keys(shape)) {
    const field = def.shape[key];
    if (ctx.io === "input" ? inputOptin(field) === void 0 : field._zod.optout === void 0) {
      requiredKeys.push(key);
    }
  }
  if (requiredKeys.length > 0) {
    json2.required = requiredKeys;
  }
  if (def.catchall?._zod.def.type === "never") {
    json2.additionalProperties = false;
  } else if (!def.catchall) {
    if (ctx.io === "output")
      json2.additionalProperties = false;
  } else if (def.catchall) {
    json2.additionalProperties = processSchema(def.catchall, ctx, {
      ...params,
      path: [...params.path, "additionalProperties"]
    });
  }
};
var unionProcessor = (schema, ctx, json2, params) => {
  const def = schema._zod.def;
  const isExclusive = def.inclusive === false;
  const options = def.options.map((x, i) => processSchema(x, ctx, {
    ...params,
    path: [...params.path, isExclusive ? "oneOf" : "anyOf", i]
  }));
  if (isExclusive) {
    json2.oneOf = options;
  } else {
    json2.anyOf = options;
  }
};
var intersectionProcessor = (schema, ctx, json2, params) => {
  const def = schema._zod.def;
  const a = processSchema(def.left, ctx, {
    ...params,
    path: [...params.path, "allOf", 0]
  });
  const b = processSchema(def.right, ctx, {
    ...params,
    path: [...params.path, "allOf", 1]
  });
  const isSimpleIntersection = (val) => "allOf" in val && Object.keys(val).length === 1;
  const allOf = [
    ...isSimpleIntersection(a) ? a.allOf : [a],
    ...isSimpleIntersection(b) ? b.allOf : [b]
  ];
  json2.allOf = allOf;
  ctx.intersections.push(allOf);
};
function stringifyKeyNames(bySchema, json2, visited) {
  if (json2.$ref) {
    if (visited.has(json2))
      return json2;
    visited.add(json2);
    const def = bySchema.get(json2)?.def;
    if (!def)
      return json2;
    const inlined = stringifyKeyNames(bySchema, def, visited);
    return inlined === def ? json2 : inlined;
  }
  for (const keyword of ["anyOf", "oneOf"]) {
    const branches = json2[keyword];
    if (!Array.isArray(branches))
      continue;
    const mapped = branches.map((branch) => stringifyKeyNames(bySchema, branch, visited));
    if (mapped.some((branch, i) => branch !== branches[i]))
      json2 = { ...json2, [keyword]: mapped };
  }
  const types = Array.isArray(json2.type) ? json2.type : [json2.type];
  const numericType = !types.includes("string") && types.some((t) => t === "number" || t === "integer");
  const values = json2.enum ?? (json2.const !== void 0 ? [json2.const] : void 0);
  if (!numericType && !values?.some((v) => typeof v === "number"))
    return json2;
  const { minimum, maximum, exclusiveMinimum, exclusiveMaximum, multipleOf, format, id, ...rest } = json2;
  if (rest.enum)
    rest.enum = rest.enum.map((v) => typeof v === "number" ? String(v) : v);
  else if (typeof rest.const === "number")
    rest.const = String(rest.const);
  if (!numericType)
    return rest;
  rest.type = "string";
  if (!values)
    rest.pattern = (types.includes("number") ? number : integer).source;
  return rest;
}
var pendingRecords = /* @__PURE__ */ new WeakMap();
function rewriteKeyNames(ctx) {
  const bySchema = /* @__PURE__ */ new Map();
  for (const entry of ctx.seen.values()) {
    if (entry.def && !bySchema.has(entry.schema))
      bySchema.set(entry.schema, entry);
  }
  const rewrites = /* @__PURE__ */ new Map();
  for (const record3 of pendingRecords.get(ctx) ?? []) {
    const seen = ctx.seen.get(record3);
    const names = (seen?.def ?? seen?.schema)?.propertyNames;
    if (!names || names === true || rewrites.has(names))
      continue;
    const rewritten = stringifyKeyNames(bySchema, names, /* @__PURE__ */ new Set());
    if (rewritten !== names)
      rewrites.set(names, rewritten);
  }
  if (!rewrites.size)
    return;
  for (const entry of ctx.seen.values()) {
    for (const carrier of [entry.schema, entry.def]) {
      const rewritten = carrier && rewrites.get(carrier.propertyNames);
      if (rewritten)
        carrier.propertyNames = rewritten;
    }
  }
}
var recordProcessor = (schema, ctx, _json, params) => {
  const json2 = _json;
  const def = schema._zod.def;
  json2.type = "object";
  const keyType = def.keyType;
  const patterns = aggregateChecks(keyType).patterns;
  if (def.mode === "loose" && patterns && patterns.size > 0) {
    const valueSchema = processSchema(def.valueType, ctx, {
      ...params,
      path: [...params.path, "patternProperties", "*"]
    });
    json2.patternProperties = {};
    for (const pattern of patterns) {
      assignProp(json2.patternProperties, exactPattern(pattern).source, valueSchema);
    }
  } else {
    if (ctx.target === "draft-07" || ctx.target === "draft-2020-12") {
      json2.propertyNames = processSchema(def.keyType, ctx, {
        ...params,
        path: [...params.path, "propertyNames"]
      });
      let pending = pendingRecords.get(ctx);
      if (!pending) {
        pending = [];
        pendingRecords.set(ctx, pending);
        ctx.deferred.push(() => rewriteKeyNames(ctx));
      }
      pending.push(schema);
    }
    json2.additionalProperties = processSchema(def.valueType, ctx, {
      ...params,
      path: [...params.path, "additionalProperties"]
    });
  }
  const keyValues = keyType._zod.values;
  const omittableOnInput = ctx.io === "input" && inputOptin(def.valueType) !== void 0;
  if (keyValues && !def.partial && !omittableOnInput) {
    const validKeyValues = [...keyValues].filter((v) => typeof v === "string" || typeof v === "number");
    if (validKeyValues.length > 0) {
      json2.required = validKeyValues.map(String);
    }
  }
};
var nullableProcessor = (schema, ctx, json2, params) => {
  const def = schema._zod.def;
  const inner = processSchema(def.innerType, ctx, params);
  const seen = ctx.seen.get(schema);
  if (ctx.target === "openapi-3.0") {
    seen.ref = def.innerType;
    json2.nullable = true;
  } else {
    json2.anyOf = [inner, { type: "null" }];
  }
};
var nonoptionalProcessor = (schema, ctx, _json, params) => {
  const def = schema._zod.def;
  processSchema(def.innerType, ctx, params);
  const seen = ctx.seen.get(schema);
  seen.ref = def.innerType;
};
var UNREPRESENTABLE_DEFAULT = /* @__PURE__ */ Symbol();
function serializeDefaultValue(value, schema, ctx, json2, params) {
  let unrepresentable = false;
  const serialized = JSON.stringify(value, (_, val) => {
    if (typeof val !== "bigint")
      return val;
    unrepresentable = true;
    return null;
  });
  if (!unrepresentable)
    return JSON.parse(serialized);
  handleUnrepresentable(schema, ctx, json2, params, "BigInt defaults cannot be represented in JSON Schema");
  return UNREPRESENTABLE_DEFAULT;
}
var defaultProcessor = (schema, ctx, json2, params) => {
  const def = schema._zod.def;
  processSchema(def.innerType, ctx, params);
  const seen = ctx.seen.get(schema);
  seen.ref = def.innerType;
  const value = serializeDefaultValue(def.defaultValue, schema, ctx, json2, params);
  if (value !== UNREPRESENTABLE_DEFAULT)
    json2.default = value;
};
var prefaultProcessor = (schema, ctx, json2, params) => {
  const def = schema._zod.def;
  processSchema(def.innerType, ctx, params);
  const seen = ctx.seen.get(schema);
  seen.ref = def.innerType;
  if (ctx.io !== "input")
    return;
  const value = serializeDefaultValue(def.defaultValue, schema, ctx, json2, params);
  if (value !== UNREPRESENTABLE_DEFAULT)
    json2._prefault = value;
};
var catchProcessor = (schema, ctx, json2, params) => {
  const def = schema._zod.def;
  processSchema(def.innerType, ctx, params);
  const seen = ctx.seen.get(schema);
  seen.ref = def.innerType;
  let catchValue;
  try {
    catchValue = def.catchValue(void 0);
  } catch {
    handleUnrepresentable(schema, ctx, json2, params, "Dynamic catch values are not supported in JSON Schema");
    return;
  }
  json2.default = catchValue;
};
var pipeProcessor = (schema, ctx, _json, params) => {
  const def = schema._zod.def;
  const inIsTransform = def.in._zod.traits.has("$ZodTransform");
  const innerType = ctx.io === "input" ? inIsTransform ? def.out : def.in : def.out;
  processSchema(innerType, ctx, params);
  const seen = ctx.seen.get(schema);
  seen.ref = innerType;
};
var readonlyProcessor = (schema, ctx, json2, params) => {
  const def = schema._zod.def;
  processSchema(def.innerType, ctx, params);
  const seen = ctx.seen.get(schema);
  seen.ref = def.innerType;
  json2.readOnly = true;
};
var optionalProcessor = (schema, ctx, _json, params) => {
  const def = schema._zod.def;
  processSchema(def.innerType, ctx, params);
  const seen = ctx.seen.get(schema);
  seen.ref = def.innerType;
};

// node_modules/zod/v4/classic/errors.js
var _installedErrorProtos = /* @__PURE__ */ new WeakSet([Object.prototype, Error.prototype]);
function _lazyMethod(proto, key, make) {
  Object.defineProperty(proto, key, {
    configurable: true,
    enumerable: false,
    get() {
      const value = make(this);
      Object.defineProperty(this, key, { value, configurable: true, writable: true });
      return value;
    },
    set(value) {
      Object.defineProperty(this, key, { value, configurable: true, writable: true });
    }
  });
}
var initializer2 = (inst, issues) => {
  $ZodError.init(inst, issues);
  inst.name = "ZodError";
  const proto = Object.getPrototypeOf(inst);
  if (_installedErrorProtos.has(proto))
    return;
  _installedErrorProtos.add(proto);
  _lazyMethod(proto, "format", (self) => (mapper) => formatError(self, mapper));
  _lazyMethod(proto, "flatten", (self) => (mapper) => flattenError(self, mapper));
  _lazyMethod(proto, "addIssue", (self) => (issue2) => {
    self.issues.push(issue2);
    self.message = JSON.stringify(self.issues, jsonStringifyReplacer, 2);
  });
  _lazyMethod(proto, "addIssues", (self) => (issues2) => {
    self.issues.push(...issues2);
    self.message = JSON.stringify(self.issues, jsonStringifyReplacer, 2);
  });
  Object.defineProperty(proto, "isEmpty", {
    configurable: true,
    enumerable: false,
    get() {
      return this.issues.length === 0;
    }
  });
};
var ZodRealError = /* @__PURE__ */ $constructor("ZodError", initializer2, void 0, {
  Parent: Error
});

// node_modules/zod/v4/classic/parse.js
var parse = /* @__PURE__ */ _parse(ZodRealError);
var parseAsync = /* @__PURE__ */ _parseAsync(ZodRealError);
var safeParse = /* @__PURE__ */ _safeParse(ZodRealError);
var safeParseAsync = /* @__PURE__ */ _safeParseAsync(ZodRealError);
var encode = /* @__PURE__ */ _encode(ZodRealError);
var decode = /* @__PURE__ */ _decode(ZodRealError);
var encodeAsync = /* @__PURE__ */ _encodeAsync(ZodRealError);
var decodeAsync = /* @__PURE__ */ _decodeAsync(ZodRealError);
var safeEncode = /* @__PURE__ */ _safeEncode(ZodRealError);
var safeDecode = /* @__PURE__ */ _safeDecode(ZodRealError);
var safeEncodeAsync = /* @__PURE__ */ _safeEncodeAsync(ZodRealError);
var safeDecodeAsync = /* @__PURE__ */ _safeDecodeAsync(ZodRealError);

// node_modules/zod/v4/classic/schemas.js
function _ensureDefaultLocale() {
  if (!globalConfig.localeError)
    config(en_default());
}
function _ensureDefaultMemoizer() {
  if (!globalConfig.memoizer)
    config({ memoizer: memoizer() });
}
var ZodType = /* @__PURE__ */ $constructor("ZodType", (inst, def) => {
  _ensureDefaultLocale();
  $ZodType.init(inst, def);
  inst.def = def;
  inst.type = def.type;
  return inst;
}, {
  check(...chks) {
    const def = this.def;
    return this.clone(util_exports.mergeDefs(def, {
      checks: [
        ...def.checks ?? [],
        ...chks.map((ch) => typeof ch === "function" ? { _zod: { check: ch, def: { check: "custom" }, onattach: [] } } : ch)
      ]
    }), { parent: true });
  },
  with(...chks) {
    return this.check(...chks);
  },
  clone(def, params) {
    return clone(this, def, params);
  },
  brand() {
    return this;
  },
  register(reg, meta2) {
    reg.add(this, meta2);
    return this;
  },
  refine(check, params) {
    return this.check(refine(check, params));
  },
  superRefine(refinement, params) {
    return this.check(superRefine(refinement, params));
  },
  overwrite(fn) {
    return this.check(_overwrite(fn));
  },
  optional() {
    return optional(this);
  },
  exactOptional() {
    return exactOptional(this);
  },
  nullable() {
    return nullable(this);
  },
  nullish() {
    return optional(nullable(this));
  },
  nonoptional(params) {
    return nonoptional(this, params);
  },
  array() {
    return array(this);
  },
  or(arg) {
    return union([this, arg]);
  },
  and(arg) {
    return intersection(this, arg);
  },
  transform(tx) {
    return pipe(this, transform(tx));
  },
  default(d) {
    return _default(this, d);
  },
  prefault(d) {
    return prefault(this, d);
  },
  catch(params) {
    return _catch(this, params);
  },
  pipe(target) {
    return pipe(this, target);
  },
  readonly() {
    return readonly(this);
  },
  describe(description) {
    const cl = this.clone();
    globalRegistry.add(cl, { description });
    return cl;
  },
  meta(...args) {
    if (args.length === 0)
      return globalRegistry.get(this);
    const cl = this.clone();
    globalRegistry.add(cl, args[0]);
    return cl;
  },
  isOptional() {
    return this.safeParse(void 0).success;
  },
  isNullable() {
    return this.safeParse(null).success;
  },
  apply(fn, ...args) {
    return args.length === 0 ? fn(this) : fn(this, ...args);
  },
  // Overrides core's `~standard` to add `jsonSchema`. Must stay a prototype entry: redefining it per instance demotes instances to dictionary mode.
  get "~standard"() {
    return util_exports.hide(this, "~standard", {
      ...standardProps(this),
      jsonSchema: {
        input: createStandardJSONSchemaMethod(this, "input"),
        output: createStandardJSONSchemaMethod(this, "output")
      }
    });
  },
  set "~standard"(value) {
    util_exports.own(this, "~standard", value);
  },
  parse: function _parse2(data, params) {
    return parse(this, data, params, { callee: _parse2 });
  },
  parseAsync: async function _parseAsync2(data, params) {
    return await parseAsync(this, data, params, { callee: _parseAsync2 });
  },
  safeParse(data, params) {
    return safeParse(this, data, params);
  },
  async safeParseAsync(data, params) {
    return safeParseAsync(this, data, params);
  },
  // `spa` is an alias: same function object as `safeParseAsync`, as before.
  get spa() {
    return this?.safeParseAsync;
  },
  set spa(value) {
    util_exports.own(this, "spa", value);
  },
  validate(data, params) {
    return validate(this, data, params);
  },
  validateAsync(data, params) {
    return validateAsync(this, data, params);
  },
  encode: function _encode2(data, params) {
    return encode(this, data, params, { callee: _encode2 });
  },
  decode: function _decode2(data, params) {
    return decode(this, data, params, { callee: _decode2 });
  },
  encodeAsync: async function _encodeAsync2(data, params) {
    return await encodeAsync(this, data, params, { callee: _encodeAsync2 });
  },
  decodeAsync: async function _decodeAsync2(data, params) {
    return await decodeAsync(this, data, params, { callee: _decodeAsync2 });
  },
  safeEncode(data, params) {
    return safeEncode(this, data, params);
  },
  safeDecode(data, params) {
    return safeDecode(this, data, params);
  },
  async safeEncodeAsync(data, params) {
    return safeEncodeAsync(this, data, params);
  },
  async safeDecodeAsync(data, params) {
    return safeDecodeAsync(this, data, params);
  },
  toJSONSchema(params) {
    return createToJSONSchemaMethod(this, {})(params);
  },
  // Reads through to the registry on every access, so it must not cache.
  get description() {
    return globalRegistry.get(this)?.description;
  },
  // No setter: `schema._def = x` throws, as it did when `_def` was a non-writable own property.
  get _def() {
    return this._zod.def;
  }
});
var _ZodString = /* @__PURE__ */ $constructor(
  "_ZodString",
  (inst, def) => {
    $ZodString.init(inst, def);
    ZodType.init(inst, def);
    inst._zod.processJSONSchema = (ctx, json2, params) => stringProcessor(inst, ctx, json2, params);
  },
  /* @__PURE__ */ util_exports.derived({
    format: (inst) => aggregateChecks(inst).format ?? null,
    minLength: (inst) => aggregateChecks(inst).minimum ?? null,
    maxLength: (inst) => aggregateChecks(inst).maximum ?? null
  }, {
    regex(...args) {
      return this.check(_regex(...args));
    },
    includes(...args) {
      return this.check(_includes(...args));
    },
    startsWith(...args) {
      return this.check(_startsWith(...args));
    },
    endsWith(...args) {
      return this.check(_endsWith(...args));
    },
    min(...args) {
      return this.check(_minLength(...args));
    },
    max(...args) {
      return this.check(_maxLength(...args));
    },
    length(...args) {
      return this.check(_length(...args));
    },
    nonempty(...args) {
      return this.check(_minLength(1, ...args));
    },
    lowercase(params) {
      return this.check(_lowercase(params));
    },
    uppercase(params) {
      return this.check(_uppercase(params));
    },
    trim() {
      return this.check(_trim());
    },
    normalize(...args) {
      return this.check(_normalize(...args));
    },
    toLowerCase() {
      return this.check(_toLowerCase());
    },
    toUpperCase() {
      return this.check(_toUpperCase());
    },
    slugify() {
      return this.check(_slugify());
    }
  })
);
var ZodString = /* @__PURE__ */ $constructor("ZodString", (inst, def) => {
  $ZodString.init(inst, def);
  _ZodString.init(inst, def);
}, {
  email(params) {
    return this.check(_email(ZodEmail, params));
  },
  url(params) {
    return this.check(_url(ZodURL, params));
  },
  jwt(params) {
    return this.check(_jwt(ZodJWT, params));
  },
  emoji(params) {
    return this.check(_emoji2(ZodEmoji, params));
  },
  guid(params) {
    return this.check(_guid(ZodGUID, params));
  },
  uuid(params) {
    return this.check(_uuid(ZodUUID, params));
  },
  uuidv4(params) {
    return this.check(_uuidv4(ZodUUID, params));
  },
  uuidv6(params) {
    return this.check(_uuidv6(ZodUUID, params));
  },
  uuidv7(params) {
    return this.check(_uuidv7(ZodUUID, params));
  },
  nanoid(params) {
    return this.check(_nanoid(ZodNanoID, params));
  },
  cuid(params) {
    return this.check(_cuid(ZodCUID, params));
  },
  cuid2(params) {
    return this.check(_cuid2(ZodCUID2, params));
  },
  ulid(params) {
    return this.check(_ulid(ZodULID, params));
  },
  base64(params) {
    return this.check(_base64(ZodBase64, params));
  },
  base64url(params) {
    return this.check(_base64url(ZodBase64URL, params));
  },
  xid(params) {
    return this.check(_xid(ZodXID, params));
  },
  ksuid(params) {
    return this.check(_ksuid(ZodKSUID, params));
  },
  ipv4(params) {
    return this.check(_ipv4(ZodIPv4, params));
  },
  ipv6(params) {
    return this.check(_ipv6(ZodIPv6, params));
  },
  cidrv4(params) {
    return this.check(_cidrv4(ZodCIDRv4, params));
  },
  cidrv6(params) {
    return this.check(_cidrv6(ZodCIDRv6, params));
  },
  e164(params) {
    return this.check(_e164(ZodE164, params));
  },
  datetime(params) {
    return this.check(_isoDateTime(ZodISODateTime, params));
  },
  date(params) {
    return this.check(_isoDate(ZodISODate, params));
  },
  time(params) {
    return this.check(_isoTime(ZodISOTime, params));
  },
  duration(params) {
    return this.check(_isoDuration(ZodISODuration, params));
  }
});
function string2(params) {
  return _string(ZodString, params);
}
var ZodStringFormat = /* @__PURE__ */ $constructor("ZodStringFormat", (inst, def) => {
  $ZodStringFormat.init(inst, def);
  _ZodString.init(inst, def);
});
var ZodISODateTime = /* @__PURE__ */ $constructor("ZodISODateTime", (inst, def) => {
  $ZodISODateTime.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodISODate = /* @__PURE__ */ $constructor("ZodISODate", (inst, def) => {
  $ZodISODate.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodISOTime = /* @__PURE__ */ $constructor("ZodISOTime", (inst, def) => {
  $ZodISOTime.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodISODuration = /* @__PURE__ */ $constructor("ZodISODuration", (inst, def) => {
  $ZodISODuration.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodEmail = /* @__PURE__ */ $constructor("ZodEmail", (inst, def) => {
  $ZodEmail.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodGUID = /* @__PURE__ */ $constructor("ZodGUID", (inst, def) => {
  $ZodGUID.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodUUID = /* @__PURE__ */ $constructor("ZodUUID", (inst, def) => {
  $ZodUUID.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodURL = /* @__PURE__ */ $constructor("ZodURL", (inst, def) => {
  $ZodURL.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodEmoji = /* @__PURE__ */ $constructor("ZodEmoji", (inst, def) => {
  $ZodEmoji.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodNanoID = /* @__PURE__ */ $constructor("ZodNanoID", (inst, def) => {
  $ZodNanoID.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodCUID = /* @__PURE__ */ $constructor("ZodCUID", (inst, def) => {
  $ZodCUID.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodCUID2 = /* @__PURE__ */ $constructor("ZodCUID2", (inst, def) => {
  $ZodCUID2.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodULID = /* @__PURE__ */ $constructor("ZodULID", (inst, def) => {
  $ZodULID.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodXID = /* @__PURE__ */ $constructor("ZodXID", (inst, def) => {
  $ZodXID.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodKSUID = /* @__PURE__ */ $constructor("ZodKSUID", (inst, def) => {
  $ZodKSUID.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodIPv4 = /* @__PURE__ */ $constructor("ZodIPv4", (inst, def) => {
  $ZodIPv4.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodIPv6 = /* @__PURE__ */ $constructor("ZodIPv6", (inst, def) => {
  $ZodIPv6.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodCIDRv4 = /* @__PURE__ */ $constructor("ZodCIDRv4", (inst, def) => {
  $ZodCIDRv4.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodCIDRv6 = /* @__PURE__ */ $constructor("ZodCIDRv6", (inst, def) => {
  $ZodCIDRv6.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodBase64 = /* @__PURE__ */ $constructor("ZodBase64", (inst, def) => {
  $ZodBase64.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodBase64URL = /* @__PURE__ */ $constructor("ZodBase64URL", (inst, def) => {
  $ZodBase64URL.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodE164 = /* @__PURE__ */ $constructor("ZodE164", (inst, def) => {
  $ZodE164.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodJWT = /* @__PURE__ */ $constructor("ZodJWT", (inst, def) => {
  $ZodJWT.init(inst, def);
  ZodStringFormat.init(inst, def);
});
var ZodNumber = /* @__PURE__ */ $constructor(
  "ZodNumber",
  (inst, def) => {
    $ZodNumber.init(inst, def);
    ZodType.init(inst, def);
    inst._zod.processJSONSchema = (ctx, json2, params) => numberProcessor(inst, ctx, json2, params);
    inst.isFinite = true;
  },
  /* @__PURE__ */ util_exports.derived({
    minValue: (inst) => {
      const { minimum, exclusiveMinimum } = aggregateChecks(inst);
      return Math.max(minimum ?? Number.NEGATIVE_INFINITY, exclusiveMinimum ?? Number.NEGATIVE_INFINITY);
    },
    maxValue: (inst) => {
      const { maximum, exclusiveMaximum } = aggregateChecks(inst);
      return Math.min(maximum ?? Number.POSITIVE_INFINITY, exclusiveMaximum ?? Number.POSITIVE_INFINITY);
    },
    isInt: (inst) => {
      const { isInt, multipleOf } = aggregateChecks(inst);
      return !!isInt || !!multipleOf?.some(Number.isSafeInteger);
    },
    format: (inst) => aggregateChecks(inst).format ?? null
  }, {
    gt(value, params) {
      return this.check(_gt(value, params));
    },
    gte(value, params) {
      return this.check(_gte(value, params));
    },
    min(value, params) {
      return this.check(_gte(value, params));
    },
    lt(value, params) {
      return this.check(_lt(value, params));
    },
    lte(value, params) {
      return this.check(_lte(value, params));
    },
    max(value, params) {
      return this.check(_lte(value, params));
    },
    int(params) {
      return this.check(int(params));
    },
    safe(params) {
      return this.check(int(params));
    },
    positive(params) {
      return this.check(_gt(0, params));
    },
    nonnegative(params) {
      return this.check(_gte(0, params));
    },
    negative(params) {
      return this.check(_lt(0, params));
    },
    nonpositive(params) {
      return this.check(_lte(0, params));
    },
    multipleOf(value, params) {
      return this.check(_multipleOf(value, params));
    },
    step(value, params) {
      return this.check(_multipleOf(value, params));
    },
    finite() {
      return this;
    }
  })
);
function number2(params) {
  return _number(ZodNumber, params);
}
var ZodNumberFormat = /* @__PURE__ */ $constructor("ZodNumberFormat", (inst, def) => {
  $ZodNumberFormat.init(inst, def);
  ZodNumber.init(inst, def);
});
function int(params) {
  return _int(ZodNumberFormat, params);
}
var ZodBoolean = /* @__PURE__ */ $constructor("ZodBoolean", (inst, def) => {
  $ZodBoolean.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => booleanProcessor(inst, ctx, json2, params);
});
function boolean2(params) {
  return _boolean(ZodBoolean, params);
}
var ZodUnknown = /* @__PURE__ */ $constructor("ZodUnknown", (inst, def) => {
  $ZodUnknown.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => unknownProcessor(inst, ctx, json2, params);
});
function unknown() {
  return _unknown(ZodUnknown);
}
var ZodNever = /* @__PURE__ */ $constructor("ZodNever", (inst, def) => {
  $ZodNever.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => neverProcessor(inst, ctx, json2, params);
});
function never(params) {
  return _never(ZodNever, params);
}
var ZodArray = /* @__PURE__ */ $constructor("ZodArray", (inst, def) => {
  _ensureDefaultMemoizer();
  $ZodArray.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => arrayProcessor(inst, ctx, json2, params);
  inst.element = def.element;
}, {
  min(n, params) {
    return this.check(_minLength(n, params));
  },
  nonempty(params) {
    return this.check(_minLength(1, params));
  },
  max(n, params) {
    return this.check(_maxLength(n, params));
  },
  length(n, params) {
    return this.check(_length(n, params));
  },
  unwrap() {
    return this.element;
  }
});
function array(element, params) {
  return _array(ZodArray, element, params);
}
var ZodObject = /* @__PURE__ */ $constructor("ZodObject", (inst, def) => {
  _ensureDefaultMemoizer();
  $ZodObjectJIT.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => objectProcessor(inst, ctx, json2, params);
  util_exports.installLazyProp(inst, "shape", (self) => self._zod.def.shape, false);
}, {
  keyof() {
    return _enum(Object.keys(this._zod.def.shape));
  },
  catchall(catchall) {
    return this.clone(util_exports.mergeDefs(this._zod.def, { catchall }));
  },
  passthrough() {
    return this.clone(util_exports.mergeDefs(this._zod.def, { catchall: unknown() }));
  },
  loose() {
    return this.clone(util_exports.mergeDefs(this._zod.def, { catchall: unknown() }));
  },
  strict() {
    return this.clone(util_exports.mergeDefs(this._zod.def, { catchall: never() }));
  },
  strip() {
    return this.clone(util_exports.mergeDefs(this._zod.def, { catchall: void 0 }));
  },
  extend(incoming) {
    return util_exports.extend(this, incoming);
  },
  safeExtend(incoming) {
    return util_exports.safeExtend(this, incoming);
  },
  merge(other) {
    return util_exports.merge(this, other);
  },
  pick(mask) {
    return util_exports.pick(this, mask);
  },
  omit(mask) {
    return util_exports.omit(this, mask);
  },
  partial(...args) {
    return util_exports.partial(ZodOptional, this, args[0]);
  },
  exactPartial(...args) {
    return util_exports.partial(ZodExactOptional, this, args[0], "exactPartial");
  },
  required(...args) {
    return util_exports.required(ZodNonOptional, this, args[0]);
  }
});
function strictObject(shape, params) {
  return new ZodObject({
    type: "object",
    shape,
    catchall: never(),
    ...util_exports.normalizeParams(params)
  });
}
var ZodUnion = /* @__PURE__ */ $constructor("ZodUnion", (inst, def) => {
  $ZodUnion.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => unionProcessor(inst, ctx, json2, params);
  inst.options = def.options;
});
function union(options, params) {
  return new ZodUnion({
    type: "union",
    options,
    ...util_exports.normalizeParams(params)
  });
}
var ZodIntersection = /* @__PURE__ */ $constructor("ZodIntersection", (inst, def) => {
  $ZodIntersection.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => intersectionProcessor(inst, ctx, json2, params);
});
function intersection(left, right) {
  return new ZodIntersection({
    type: "intersection",
    left,
    right
  });
}
var ZodRecord = /* @__PURE__ */ $constructor("ZodRecord", (inst, def) => {
  _ensureDefaultMemoizer();
  $ZodRecord.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => recordProcessor(inst, ctx, json2, params);
  inst.keyType = def.keyType;
  inst.valueType = def.valueType;
});
function record(keyType, valueType, params) {
  if (!valueType || !valueType._zod) {
    return new ZodRecord({
      type: "record",
      keyType: string2(),
      valueType: keyType,
      ...util_exports.normalizeParams(valueType)
    });
  }
  return new ZodRecord({
    type: "record",
    keyType,
    valueType,
    ...util_exports.normalizeParams(params)
  });
}
var ZodEnum = /* @__PURE__ */ $constructor("ZodEnum", (inst, def) => {
  $ZodEnum.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => enumProcessor(inst, ctx, json2, params);
  inst.enum = def.entries;
  inst.options = [...inst._zod.values];
  const keys = new Set(Object.keys(def.entries));
  inst.extract = (values, params) => {
    const newEntries = {};
    for (const value of values) {
      if (keys.has(value)) {
        newEntries[value] = def.entries[value];
      } else
        throw new Error(`Key ${value} not found in enum`);
    }
    return new ZodEnum({
      ...def,
      checks: [],
      ...util_exports.normalizeParams(params),
      entries: newEntries
    });
  };
  inst.exclude = (values, params) => {
    const newEntries = { ...def.entries };
    for (const value of values) {
      if (keys.has(value)) {
        delete newEntries[value];
      } else
        throw new Error(`Key ${value} not found in enum`);
    }
    return new ZodEnum({
      ...def,
      checks: [],
      ...util_exports.normalizeParams(params),
      entries: newEntries
    });
  };
});
function _enum(values, params) {
  const entries = Array.isArray(values) ? Object.fromEntries(values.map((v) => [v, v])) : values;
  return new ZodEnum({
    type: "enum",
    entries,
    ...util_exports.normalizeParams(params)
  });
}
var ZodLiteral = /* @__PURE__ */ $constructor("ZodLiteral", (inst, def) => {
  $ZodLiteral.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => literalProcessor(inst, ctx, json2, params);
  inst.values = new Set(def.values);
  Object.defineProperty(inst, "value", {
    get() {
      if (def.values.length > 1) {
        throw new Error("This schema contains multiple valid literal values. Use `.values` instead.");
      }
      return def.values[0];
    }
  });
});
function literal(value, params) {
  return new ZodLiteral({
    type: "literal",
    values: Array.isArray(value) ? value : [value],
    ...util_exports.normalizeParams(params)
  });
}
var ZodTransform = /* @__PURE__ */ $constructor("ZodTransform", (inst, def) => {
  _ensureDefaultMemoizer();
  $ZodTransform.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => transformProcessor(inst, ctx, json2, params);
  inst._zod.parse = (payload, _ctx) => {
    if (_ctx.direction === "backward") {
      throw new $ZodEncodeError(inst.constructor.name);
    }
    payload.addIssue = (issue2) => {
      if (typeof issue2 === "string") {
        payload.issues.push(util_exports.issue(issue2, payload.value, def));
      } else {
        const _issue = issue2;
        if (_issue.fatal)
          _issue.continue = false;
        _issue.code ?? (_issue.code = "custom");
        if (!("input" in _issue))
          _issue.input = payload.value;
        _issue.inst ?? (_issue.inst = inst);
        payload.issues.push(util_exports.issue(_issue));
      }
    };
    const output = def.transform(payload.value, payload);
    if (output instanceof Promise) {
      return output.then((output2) => {
        payload.value = output2;
        return payload;
      });
    }
    payload.value = output;
    return payload;
  };
});
function transform(fn) {
  return new ZodTransform({
    type: "transform",
    transform: fn
  });
}
var ZodOptional = /* @__PURE__ */ $constructor("ZodOptional", (inst, def) => {
  $ZodOptional.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => optionalProcessor(inst, ctx, json2, params);
  inst.unwrap = () => inst._zod.def.innerType;
});
function optional(innerType) {
  return new ZodOptional({
    type: "optional",
    innerType
  });
}
var ZodExactOptional = /* @__PURE__ */ $constructor("ZodExactOptional", (inst, def) => {
  $ZodExactOptional.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => optionalProcessor(inst, ctx, json2, params);
  inst.unwrap = () => inst._zod.def.innerType;
});
function exactOptional(innerType) {
  return new ZodExactOptional({
    type: "optional",
    innerType
  });
}
var ZodNullable = /* @__PURE__ */ $constructor("ZodNullable", (inst, def) => {
  $ZodNullable.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => nullableProcessor(inst, ctx, json2, params);
  inst.unwrap = () => inst._zod.def.innerType;
});
function nullable(innerType) {
  return new ZodNullable({
    type: "nullable",
    innerType
  });
}
var ZodDefault = /* @__PURE__ */ $constructor("ZodDefault", (inst, def) => {
  $ZodDefault.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => defaultProcessor(inst, ctx, json2, params);
  inst.unwrap = () => inst._zod.def.innerType;
  inst.removeDefault = inst.unwrap;
});
function _default(innerType, defaultValue) {
  return new ZodDefault({
    type: "default",
    innerType,
    get defaultValue() {
      return typeof defaultValue === "function" ? defaultValue() : util_exports.shallowClone(defaultValue);
    }
  });
}
var ZodPrefault = /* @__PURE__ */ $constructor("ZodPrefault", (inst, def) => {
  $ZodPrefault.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => prefaultProcessor(inst, ctx, json2, params);
  inst.unwrap = () => inst._zod.def.innerType;
});
function prefault(innerType, defaultValue) {
  return new ZodPrefault({
    type: "prefault",
    innerType,
    get defaultValue() {
      return typeof defaultValue === "function" ? defaultValue() : util_exports.shallowClone(defaultValue);
    }
  });
}
var ZodNonOptional = /* @__PURE__ */ $constructor("ZodNonOptional", (inst, def) => {
  $ZodNonOptional.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => nonoptionalProcessor(inst, ctx, json2, params);
  inst.unwrap = () => inst._zod.def.innerType;
});
function nonoptional(innerType, params) {
  return new ZodNonOptional({
    type: "nonoptional",
    innerType,
    ...util_exports.normalizeParams(params)
  });
}
var ZodCatch = /* @__PURE__ */ $constructor("ZodCatch", (inst, def) => {
  $ZodCatch.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => catchProcessor(inst, ctx, json2, params);
  inst.unwrap = () => inst._zod.def.innerType;
  inst.removeCatch = inst.unwrap;
});
function _catch(innerType, catchValue) {
  return new ZodCatch({
    type: "catch",
    innerType,
    catchValue: typeof catchValue === "function" ? catchValue : util_exports.constantCatch(catchValue)
  });
}
var ZodPipe = /* @__PURE__ */ $constructor("ZodPipe", (inst, def) => {
  $ZodPipe.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => pipeProcessor(inst, ctx, json2, params);
  inst.in = def.in;
  inst.out = def.out;
});
function pipe(in_, out) {
  return new ZodPipe({
    type: "pipe",
    in: in_,
    out
    // ...util.normalizeParams(params),
  });
}
var ZodReadonly = /* @__PURE__ */ $constructor("ZodReadonly", (inst, def) => {
  $ZodReadonly.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => readonlyProcessor(inst, ctx, json2, params);
  inst.unwrap = () => inst._zod.def.innerType;
});
function readonly(innerType) {
  return new ZodReadonly({
    type: "readonly",
    innerType
  });
}
var ZodCustom = /* @__PURE__ */ $constructor("ZodCustom", (inst, def) => {
  $ZodCustom.init(inst, def);
  ZodType.init(inst, def);
  inst._zod.processJSONSchema = (ctx, json2, params) => customProcessor(inst, ctx, json2, params);
});
function refine(fn, _params = {}) {
  return _refine(ZodCustom, fn, _params);
}
function superRefine(fn, params) {
  return _superRefine(fn, params);
}

// src/api-schemas.ts
var TASK_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/;
var taskIdSchema = string2().regex(TASK_ID_PATTERN, `task_id must match ${TASK_ID_PATTERN.source}`);
var stringArray = array(string2());
var zcodeTaskInputSchema = strictObject({
  task_id: taskIdSchema,
  workspace: string2().min(1),
  worktree_path: string2().min(1).optional(),
  model: strictObject({
    provider_id: string2().trim().min(1).optional(),
    model_id: string2().trim().min(1),
    reasoning_level: string2().trim().min(1).optional()
  }).optional(),
  timeout_ms: number2().int().min(6e4).max(144e5).optional(),
  objective: string2().min(1),
  requirements: stringArray,
  allowed_paths: stringArray,
  forbidden_paths: stringArray,
  acceptance_criteria: stringArray,
  test_commands: stringArray,
  context: string2().optional()
}).describe("Full TaskPackage; workspace is the calling host project root. Optional worktree_path is an existing execution directory selected and prepared by the calling host; the Bridge never creates or selects worktrees. The five array fields must be present (empty allowed), context is optional.");
var taskIdOnlyInputSchema = strictObject({
  task_id: string2().min(1)
});
var zcodeContinueInputSchema = strictObject({
  task_id: string2().min(1),
  feedback: string2().min(1),
  additional_requirements: array(string2()).optional(),
  operation_id: string2().trim().min(1).max(128).optional()
});
var zcodeEventsInputSchema = strictObject({
  task_id: taskIdSchema,
  after_seq: number2().int().nonnegative().optional(),
  limit: number2().int().min(1).max(200).optional(),
  wait_ms: number2().int().min(0).max(25e3).optional(),
  view: _enum(["raw", "summary"]).optional(),
  include_attempt: boolean2().optional().describe("Include each event's persisted attempt number."),
  scan_cursor: string2().max(2048).optional(),
  max_bytes: number2().int().min(1024).max(33554432).optional(),
  wait_for: literal("attention").optional()
});
var zcodeInteractionReplyInputSchema = strictObject({
  task_id: taskIdSchema,
  request_id: string2().trim().min(1).max(512),
  decision: _enum(["allow", "deny", "accept", "decline"]),
  answers: record(string2(), string2()).optional(),
  reason: string2().max(2e3).optional()
});
var zcodeModelCatalogInputSchema = strictObject({
  workspace: string2().trim().min(1)
});
var zcodeDefaultModelInputSchema = strictObject({
  provider_id: string2().trim().min(1),
  model_id: string2().trim().min(1),
  reasoning_level: string2().trim().min(1).optional()
});

// src/task-list.ts
var MAX_TASK_LIST_LIMIT = 100;
var listTasksInputSchema = strictObject({
  after_task_id: taskIdSchema.optional(),
  limit: number2().int().min(1).max(MAX_TASK_LIST_LIMIT).optional(),
  status: _enum([
    "queued",
    "running",
    "completed",
    "failed",
    "cancelled",
    "waiting_for_master"
  ]).optional()
});
var consoleTaskListInputSchema = strictObject({
  after_task_id: taskIdSchema.optional(),
  limit: number2().int().min(1).max(MAX_TASK_LIST_LIMIT).optional(),
  bucket: _enum(["running", "attention", "completed"]).optional()
});

// src/executor/protocol.ts
var EXECUTOR_CONTROL_PROTOCOL_VERSION = 1;
var EXECUTOR_CONTROL_FRAME_LIMIT_BYTES = 33 * 1024 * 1024;
var nonEmptyString = string2().min(1);
var emptyParams = strictObject({});
var taskAdmissionSchema = strictObject({
  owner_thread_id: string2().nullable(),
  source: _enum(["mcp_meta", "mcp_meta_missing", "mcp_meta_invalid", "non_host_admission"])
}).refine(
  (value) => value.source === "mcp_meta" === (value.owner_thread_id !== null),
  { message: "owner_thread_id must be present only for mcp_meta admission" }
);
var executorControlParamsSchemas = {
  createTask: strictObject({ task: zcodeTaskInputSchema, admission: taskAdmissionSchema.optional() }),
  listTasks: listTasksInputSchema,
  listConsoleTasks: consoleTaskListInputSchema,
  getConsoleTaskDetail: strictObject({ task_id: nonEmptyString }),
  getStatus: strictObject({ task_id: nonEmptyString }),
  getResult: strictObject({ task_id: nonEmptyString, view: _enum(["summary", "full"]).optional() }),
  getResultPage: strictObject({ task_id: nonEmptyString, offset_bytes: number2().int().nonnegative(), max_bytes: number2().int().min(1024).max(4194304) }),
  continueTask: strictObject({ input: zcodeContinueInputSchema }),
  cancelTask: strictObject({ task_id: nonEmptyString }),
  getEvents: strictObject({ input: zcodeEventsInputSchema }),
  getFeedback: strictObject({ task_id: nonEmptyString }),
  getAttention: strictObject({ task_id: nonEmptyString }),
  replyToInteraction: strictObject({ input: zcodeInteractionReplyInputSchema }),
  listModels: zcodeModelCatalogInputSchema,
  getDefaultModel: emptyParams,
  setDefaultModel: zcodeDefaultModelInputSchema,
  clearDefaultModel: emptyParams,
  doctor: emptyParams,
  executorStatus: emptyParams,
  shutdown: emptyParams,
  health: emptyParams
};

// src/executor/frame.ts
var EXECUTOR_FRAME_HEADER_BYTES = 4;
function encodeExecutorFrame(value) {
  const body = Buffer.from(JSON.stringify(value), "utf8");
  if (body.byteLength > EXECUTOR_CONTROL_FRAME_LIMIT_BYTES) {
    throw new Error("EXECUTOR_CONTROL_FRAME_TOO_LARGE");
  }
  const frame = Buffer.alloc(EXECUTOR_FRAME_HEADER_BYTES + body.byteLength);
  frame.writeUInt32BE(body.byteLength, 0);
  body.copy(frame, EXECUTOR_FRAME_HEADER_BYTES);
  return frame;
}
function createExecutorFrameDecoder(limitBytes = EXECUTOR_CONTROL_FRAME_LIMIT_BYTES) {
  let buffer = Buffer.alloc(0);
  return new Transform({
    transform(chunk, _encoding, callback) {
      buffer = buffer.length === 0 ? chunk : Buffer.concat([buffer, chunk]);
      while (buffer.byteLength >= EXECUTOR_FRAME_HEADER_BYTES) {
        const bodyLength = buffer.readUInt32BE(0);
        if (bodyLength > limitBytes) {
          callback(new Error("EXECUTOR_CONTROL_FRAME_TOO_LARGE"));
          return;
        }
        if (buffer.byteLength < EXECUTOR_FRAME_HEADER_BYTES + bodyLength) break;
        const body = buffer.subarray(EXECUTOR_FRAME_HEADER_BYTES, EXECUTOR_FRAME_HEADER_BYTES + bodyLength);
        buffer = buffer.subarray(EXECUTOR_FRAME_HEADER_BYTES + bodyLength);
        let parsed;
        try {
          parsed = JSON.parse(body.toString("utf8"));
          if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("EXECUTOR_CONTROL_FRAME_MALFORMED");
        } catch (error2) {
          callback(error2 instanceof Error ? error2 : new Error("EXECUTOR_CONTROL_FRAME_MALFORMED"));
          return;
        }
        this.push(JSON.stringify(parsed));
      }
      callback();
    }
  });
}

// src/executor/control-client.ts
function executorError(code) {
  return Object.assign(new Error(code), { code });
}
function submissionUnknownCode(method) {
  if (method === "createTask" || method === "continueTask" || method === "replyToInteraction" || method === "setDefaultModel" || method === "clearDefaultModel" || method === "shutdown") {
    return "SUBMISSION_UNKNOWN";
  }
  if (method === "cancelTask") return "TASK_CANCEL_REQUESTED";
  return "EXECUTOR_UNAVAILABLE";
}
var ExecutorControlClient = class {
  #pipeName;
  #connectTimeoutMs;
  #recoverUnavailable;
  #socket = null;
  #connectPromise = null;
  #pending = /* @__PURE__ */ new Map();
  constructor(options) {
    this.#pipeName = options.pipeName;
    this.#connectTimeoutMs = options.connectTimeoutMs ?? 5e3;
    this.#recoverUnavailable = options.recoverUnavailable;
  }
  async connect() {
    if (this.#socket && !this.#socket.destroyed) return;
    if (this.#connectPromise) return this.#connectPromise;
    const attempt = (async () => {
      try {
        await this.#connectOnce();
      } catch (error2) {
        if (!this.#recoverUnavailable || !(error2 instanceof Error && "code" in error2 && error2.code === "EXECUTOR_UNAVAILABLE")) {
          throw error2;
        }
        await this.#recoverUnavailable();
        await this.#connectOnce();
      }
    })();
    this.#connectPromise = attempt;
    try {
      await attempt;
    } finally {
      if (this.#connectPromise === attempt) this.#connectPromise = null;
    }
  }
  async #connectOnce() {
    if (this.#socket && !this.#socket.destroyed) return;
    await new Promise((resolve, reject) => {
      const socket = net.connect(this.#pipeName);
      const timer = setTimeout(() => {
        socket.destroy();
        reject(executorError("EXECUTOR_UNAVAILABLE"));
      }, this.#connectTimeoutMs);
      socket.once("connect", () => {
        clearTimeout(timer);
        this.#socket = socket;
        const decoder = createExecutorFrameDecoder();
        socket.pipe(decoder);
        socket.resume();
        decoder.on("data", (chunk) => {
          try {
            const response = JSON.parse(chunk.toString("utf8"));
            const pending = this.#pending.get(response.request_id);
            if (pending) {
              this.#pending.delete(response.request_id);
              pending.resolve(response);
            }
          } catch {
            this.#failPending("EXECUTOR_CONTROL_RESPONSE_MALFORMED");
            socket.destroy();
          }
        });
        decoder.on("error", (error2) => {
          this.#failPending(void 0, socket);
          socket.destroy(error2);
        });
        socket.on("error", (error2) => {
          this.#failPending("EXECUTOR_UNAVAILABLE");
          reject(error2);
        });
        socket.on("close", () => {
          if (this.#socket === socket) this.#socket = null;
          this.#failPending(void 0, socket);
        });
        resolve();
      });
      socket.once("error", (error2) => {
        clearTimeout(timer);
        reject(Object.assign(executorError("EXECUTOR_UNAVAILABLE"), { cause: error2 }));
      });
    });
  }
  request(method, params, signal, idempotencyKey) {
    if (!this.#socket || this.#socket.destroyed) {
      return Promise.reject(executorError("EXECUTOR_UNAVAILABLE"));
    }
    const request = {
      protocol_version: EXECUTOR_CONTROL_PROTOCOL_VERSION,
      request_id: randomUUID2(),
      method,
      params,
      // The transport records the key for diagnostics, while durable submission
      // idempotency remains owned by task_id/operation_id in SQLite.
      ...idempotencyKey ? { idempotency_key: idempotencyKey } : {}
    };
    const attempt = new Promise((resolve, reject) => {
      this.#pending.set(request.request_id, { method, resolve, reject });
      this.#socket.write(encodeExecutorFrame(request), (error2) => {
        if (error2) {
          this.#pending.delete(request.request_id);
          reject(executorError(submissionUnknownCode(method)));
        }
      });
    });
    if (!signal) return attempt;
    signal.addEventListener("abort", () => {
      const pending = this.#pending.get(request.request_id);
      if (pending) {
        this.#pending.delete(request.request_id);
        pending.reject(executorError("REQUEST_CANCELLED"));
      }
    }, { once: true });
    return attempt;
  }
  #failPending(code, socket) {
    for (const [requestId, pending] of this.#pending) {
      if (socket && this.#socket !== null && this.#socket !== socket) continue;
      this.#pending.delete(requestId);
      pending.reject(executorError(code ?? submissionUnknownCode(pending.method)));
    }
  }
  close() {
    const socket = this.#socket;
    this.#socket = null;
    this.#failPending(void 0);
    socket?.destroy();
  }
};

// src/task-errors.ts
var TaskManagerError = class extends Error {
  code;
  constructor(code, message) {
    super(message);
    this.name = "TaskManagerError";
    this.code = code;
  }
};

// src/executor/remote-task-manager.ts
var TASK_MANAGER_ERROR_CODES = /* @__PURE__ */ new Set([
  "TASK_NOT_FOUND",
  "TASK_NOT_FINISHED",
  "TASK_ALREADY_EXISTS",
  "TASK_ID_CONFLICT",
  "CONTINUE_OPERATION_CONFLICT",
  "BRIDGE_BUSY",
  "REQUEST_QUEUE_TIMEOUT",
  "TASK_INVALID",
  "TASK_STATE",
  "CANCEL_FAILED",
  "EXECUTOR_STORE_CLOSE_UNKNOWN",
  "interaction_reply_outcome_unknown"
]);
var RemoteTaskManager = class {
  #client;
  #taskConsoleLink;
  constructor(client, options = {}) {
    this.#client = client;
    this.#taskConsoleLink = options.taskConsoleLink;
  }
  async #call(method, params, idempotencyKey) {
    await this.#client.connect();
    const response = await this.#client.request(
      method,
      params,
      void 0,
      idempotencyKey
    );
    if (!response.ok) {
      const code = response.error?.code ?? "EXECUTOR_REQUEST_FAILED";
      if (TASK_MANAGER_ERROR_CODES.has(code)) {
        throw new TaskManagerError(
          code,
          response.error?.message ?? code
        );
      }
      const error2 = new Error(response.error?.message ?? "EXECUTOR_REQUEST_FAILED");
      error2.code = code;
      throw error2;
    }
    return response.result ?? {};
  }
  async #withConsoleLink(receipt) {
    if (!this.#taskConsoleLink) return receipt;
    try {
      return { ...receipt, console_link: await this.#taskConsoleLink(receipt.task_id) };
    } catch (error2) {
      const reason = error2 instanceof Error && "code" in error2 && typeof error2.code === "string" ? error2.code : "WEB_CONSOLE_UNAVAILABLE";
      return {
        ...receipt,
        console_link: {
          available: false,
          web_url: null,
          console_id: null,
          console_reused: null,
          reason_code: reason
        }
      };
    }
  }
  async createTask(task, admission) {
    const receipt = await this.#call(
      "createTask",
      { task, ...admission ? { admission } : {} },
      task.task_id
    );
    return this.#withConsoleLink(receipt);
  }
  async listTasks(input = {}) {
    return this.#call("listTasks", input);
  }
  async listConsoleTasks(input = {}) {
    return this.#call("listConsoleTasks", input);
  }
  async getConsoleTaskDetail(taskId) {
    return this.#call("getConsoleTaskDetail", { task_id: taskId });
  }
  async getStatus(taskId) {
    return this.#call("getStatus", { task_id: taskId });
  }
  async getResult(taskId, view) {
    return this.#call("getResult", { task_id: taskId, ...view ? { view } : {} });
  }
  async getResultPage(taskId, offsetBytes, maxBytes) {
    return this.#call("getResultPage", { task_id: taskId, offset_bytes: offsetBytes, max_bytes: maxBytes });
  }
  async continueTask(input) {
    const receipt = await this.#call(
      "continueTask",
      { input },
      input.operation_id ?? `${input.task_id}:continue`
    );
    return this.#withConsoleLink(receipt);
  }
  async cancelTask(taskId) {
    return this.#call("cancelTask", { task_id: taskId });
  }
  async getEvents(input) {
    return this.#call("getEvents", { input });
  }
  async getFeedback(taskId) {
    return this.#call("getFeedback", { task_id: taskId });
  }
  async getAttention(taskId) {
    return this.#call("getAttention", { task_id: taskId });
  }
  async replyToInteraction(input) {
    return this.#call("replyToInteraction", { input });
  }
};

// src/web/cost-lab-integration.ts
import { createHash as createHash10 } from "node:crypto";
import { existsSync as existsSync6 } from "node:fs";
import path20 from "node:path";
import { fileURLToPath as fileURLToPath8 } from "node:url";

// src/adapters/official-host-adapter.ts
import { createHash as createHash5 } from "node:crypto";
import { createReadStream as createReadStream2 } from "node:fs";
import { lstat as lstat2, realpath as realpath2 } from "node:fs/promises";
import path10 from "node:path";
import { fileURLToPath as fileURLToPath3, pathToFileURL } from "node:url";

// src/runtime/official-app-server-runtime.ts
import { createHash as createHash4 } from "node:crypto";
import { execFile } from "node:child_process";
import { closeSync as closeSync2, createReadStream, openSync as openSync2, readSync as readSync2 } from "node:fs";
import { lstat, realpath } from "node:fs/promises";
import { homedir as homedir3 } from "node:os";
import path9 from "node:path";
import { promisify } from "node:util";

// src/runtime/node-runtime.ts
var SUPPORTED_NODE_RANGE = ">=24.16.0 <25";
function isSupportedNodeVersion(version2) {
  const match = /^(\d+)\.(\d+)\.(\d+)$/u.exec(version2);
  if (!match) return false;
  const major = Number(match[1]);
  const minor = Number(match[2]);
  const patch = Number(match[3]);
  return major === 24 && minor >= 16 && patch >= 0;
}

// src/runtime/official-runtime-authorization.ts
import { createHash as createHash3 } from "node:crypto";
function computeOfficialInstallationFingerprint(input) {
  const normalized = {
    schema_version: 1,
    desktop_version: input.desktop_version,
    desktop_app_version: input.desktop_app_version,
    desktop_build_commit_id: input.desktop_build_commit_id,
    desktop_executable: {
      bytes: input.desktop_executable_bytes,
      sha256: input.desktop_executable_sha256.toLowerCase()
    },
    desktop_archive: {
      bytes: input.desktop_archive_bytes,
      sha256: input.desktop_archive_sha256.toLowerCase()
    },
    appserver_bundle: {
      bytes: input.bundle_bytes,
      sha256: input.bundle_sha256.toLowerCase()
    },
    builtin_provider_config: {
      bytes: input.builtin_provider_config_bytes,
      sha256: input.builtin_provider_config_sha256.toLowerCase()
    },
    runtime_host: {
      bytes: input.runtime_host_bytes,
      sha256: input.runtime_host_sha256.toLowerCase()
    },
    signers: {
      desktop: input.desktop_signer_thumbprint.replace(/[^0-9A-F]/giu, "").toUpperCase(),
      runtime_host: input.runtime_host_signer_thumbprint.replace(/[^0-9A-F]/giu, "").toUpperCase()
    },
    node_version: input.node_version
  };
  return createHash3("sha256").update(JSON.stringify(normalized), "utf8").digest("hex");
}

// src/runtime/official-app-server-runtime.ts
var execFileAsync = promisify(execFile);
var OFFICIAL_APPSERVER_COMPATIBILITY_MANIFEST = Object.freeze([
  Object.freeze({
    desktop_version: "3.18.2.10443",
    desktop_app_version: "3.18.2",
    desktop_build_commit_id: "2681f4af",
    bundle_sha256: "08726b5ef69e1e9072828baa4656713cb3aac93bb096938681278c5600312b2c",
    bundle_bytes: 15675386,
    builtin_provider_config_sha256: "ef3d64656cb5281cce292b77ef12e96b5251582cfb00cdf9eb08e3d4565abb69",
    builtin_provider_config_bytes: 261659,
    runtime_host_sha256: "c2c8ff5ff28cbddc4f177c094aa67c322830889612251bd173baaabc89379ab4",
    runtime_host_bytes: 179608,
    node_compatibility: SUPPORTED_NODE_RANGE,
    appserver_protocol: "zcode-app-server-stdio-desktop-v1",
    request_security_capability: "official-installed-bundle-signing",
    coding_plan_discount_verified: true,
    start_plan_static_compatibility: "OFFLINE_COMPATIBLE",
    verification_date: "2026-11-18",
    desktop_asset_pinning: "LEGACY_SAFETY_ONLY"
  }),
  Object.freeze({
    desktop_version: "3.19.0.10774",
    desktop_app_version: "3.19.0",
    desktop_build_commit_id: "a7ed1054",
    desktop_executable_sha256: "c5afb161a2d9389761d417ca668bc94311e3d2aff6ca3d0117b0b15701666f27",
    desktop_executable_bytes: 246332312,
    desktop_archive_sha256: "2421850970f361aaa1b3f1d6c960b101a5d476ad95631359d0413a19de1197cb",
    desktop_archive_bytes: 385171742,
    bundle_sha256: "6b84e928d9258fe020c6ab8c75fa2c123b0cd658fe43c0ce141a13df677fb0ea",
    bundle_bytes: 15843692,
    builtin_provider_config_sha256: "ef3d64656cb5281cce292b77ef12e96b5251582cfb00cdf9eb08e3d4565abb69",
    builtin_provider_config_bytes: 261659,
    runtime_host_sha256: "c87a9f3cf9cf920e4b5993aad69f8840a5d9bc7c0ae90b32acb29c15a1db0aae",
    runtime_host_bytes: 179608,
    node_compatibility: SUPPORTED_NODE_RANGE,
    appserver_protocol: "zcode-app-server-stdio-desktop-v1",
    request_security_capability: "identity-observed-provider-verification-pending",
    coding_plan_discount_verified: false,
    start_plan_static_compatibility: "OFFLINE_RESEARCH_PENDING",
    verification_date: "2026-11-20",
    verification_stage: "EXPERIMENTAL",
    desktop_asset_pinning: "FULL"
  })
]);
var OfficialAppServerRuntimeResolver = class {
  #env;
  #homeDir;
  #host;
  #baseResolver;
  #manifest;
  #platform;
  #architecture;
  #hashFile;
  #probeNodeVersion;
  #probeDesktopVersion;
  #inspectExecutable;
  #readDesktopLaunch;
  constructor(options = {}) {
    this.#env = options.env ?? process.env;
    this.#homeDir = options.homeDir ?? homedir3();
    this.#host = options.host;
    this.#baseResolver = options.baseResolver ?? null;
    this.#manifest = options.manifest ?? OFFICIAL_APPSERVER_COMPATIBILITY_MANIFEST;
    this.#platform = options.platform ?? process.platform;
    this.#architecture = options.architecture ?? process.arch;
    this.#hashFile = options.hashFile ?? sha256File;
    this.#probeNodeVersion = options.probeNodeVersion ?? probeNodeCliVersion;
    this.#probeDesktopVersion = options.probeDesktopVersion ?? probeWindowsFileVersion;
    this.#inspectExecutable = options.inspectExecutable ?? inspectWindowsExecutable;
    this.#readDesktopLaunch = options.readDesktopLaunch ?? ((bundlePath) => buildZCodeAppServerLaunch(bundlePath, {}));
  }
  async inspect() {
    let env;
    try {
      env = loadPersistedRuntimeEnvironment(
        this.#env,
        this.#homeDir,
        this.#host ?? codexHostProfile(this.#homeDir)
      );
    } catch (error2) {
      return unverified(`Bridge runtime settings could not be loaded: ${errorMessage(error2)}`, "node");
    }
    const nodeExecutable = env["ZCODE_BRIDGE_NODE"]?.trim() || "node";
    if (this.#platform !== "win32" || this.#architecture !== "x64") {
      return unverified(
        `installed Official AppServer requires Windows x64, got ${this.#platform}/${this.#architecture}`,
        nodeExecutable
      );
    }
    const discovery = discoverZCodeInstall(env, { requireBuiltin: true });
    if (!discovery.installDir || !discovery.zcodeEntrypoint || !discovery.builtinConfigFile) {
      return unverified(
        "installed ZCode Desktop AppServer with same-root builtin provider config was not found",
        nodeExecutable
      );
    }
    if (!isAbsolutePathForPlatform(discovery.installDir)) {
      return unverified("installed ZCode path is not absolute", nodeExecutable);
    }
    let installDir;
    let bundlePath;
    let builtinPath;
    let runtimeHostPath;
    let desktopExecutablePath;
    let desktopArchivePath;
    try {
      installDir = await canonicalDirectory(discovery.installDir);
      bundlePath = await canonicalFileInside(
        installDir,
        discovery.zcodeEntrypoint,
        "installed AppServer bundle"
      );
      builtinPath = await canonicalFileInside(
        installDir,
        discovery.builtinConfigFile,
        "installed builtin provider config"
      );
      runtimeHostPath = await canonicalFileInside(
        installDir,
        path9.join(installDir, "resources", "tools", "runtime-host", "zcode-runtime-host.exe"),
        "installed runtime-host"
      );
      desktopExecutablePath = await canonicalFileInside(
        installDir,
        path9.join(installDir, "ZCode.exe"),
        "installed Desktop executable"
      );
      desktopArchivePath = await canonicalFileInside(
        installDir,
        path9.join(installDir, "resources", "app.asar"),
        "installed Desktop archive"
      );
    } catch (error2) {
      return unverified(errorMessage(error2), nodeExecutable);
    }
    let bundleBytes;
    let builtinBytes;
    let runtimeHostBytes;
    let desktopExecutableBytes;
    let desktopArchiveBytes;
    try {
      [
        { size: bundleBytes },
        { size: builtinBytes },
        { size: runtimeHostBytes },
        { size: desktopExecutableBytes },
        { size: desktopArchiveBytes }
      ] = await Promise.all([
        lstat(bundlePath),
        lstat(builtinPath),
        lstat(runtimeHostPath),
        lstat(desktopExecutablePath),
        lstat(desktopArchivePath)
      ]);
    } catch (error2) {
      return unverified(`could not verify installed Official runtime assets: ${errorMessage(error2)}`, nodeExecutable);
    }
    const [
      bundleSha256,
      builtinSha256,
      runtimeHostSha256,
      desktopExecutableSha256,
      desktopArchiveSha256
    ] = await Promise.all([
      optionalSha256(this.#hashFile, bundlePath),
      optionalSha256(this.#hashFile, builtinPath),
      optionalSha256(this.#hashFile, runtimeHostPath),
      optionalSha256(this.#hashFile, desktopExecutablePath),
      optionalSha256(this.#hashFile, desktopArchivePath)
    ]);
    let desktopExecutableIdentity;
    let runtimeHostIdentity;
    try {
      desktopExecutableIdentity = await this.#inspectExecutable(desktopExecutablePath);
      runtimeHostIdentity = await this.#inspectExecutable(runtimeHostPath);
    } catch (error2) {
      return unsafe(
        `official executable safety inspection failed: ${errorMessage(error2)}`,
        nodeExecutable,
        {
          install_dir: installDir,
          install_source: discovery.source,
          bundle_path: bundlePath,
          bundle_bytes: bundleBytes,
          bundle_sha256: bundleSha256,
          builtin_provider_config_path: builtinPath,
          builtin_provider_config_bytes: builtinBytes,
          builtin_provider_config_sha256: builtinSha256,
          runtime_host_path: runtimeHostPath,
          runtime_host_bytes: runtimeHostBytes,
          runtime_host_sha256: runtimeHostSha256,
          desktop_executable_path: desktopExecutablePath,
          desktop_executable_bytes: desktopExecutableBytes,
          desktop_executable_sha256: desktopExecutableSha256,
          desktop_archive_path: desktopArchivePath,
          desktop_archive_bytes: desktopArchiveBytes,
          desktop_archive_sha256: desktopArchiveSha256
        }
      );
    }
    const unsafeExecutableReason = executableArchitectureFailure(
      desktopExecutableIdentity,
      "Desktop executable"
    ) ?? executableArchitectureFailure(runtimeHostIdentity, "runtime-host");
    if (unsafeExecutableReason) {
      return unsafe(unsafeExecutableReason, nodeExecutable, {
        install_dir: installDir,
        install_source: discovery.source,
        bundle_path: bundlePath,
        bundle_bytes: bundleBytes,
        bundle_sha256: bundleSha256,
        builtin_provider_config_path: builtinPath,
        builtin_provider_config_bytes: builtinBytes,
        builtin_provider_config_sha256: builtinSha256,
        runtime_host_path: runtimeHostPath,
        runtime_host_bytes: runtimeHostBytes,
        runtime_host_sha256: runtimeHostSha256,
        runtime_host_signer_subject: runtimeHostIdentity.signer_subject,
        runtime_host_signer_thumbprint: runtimeHostIdentity.signer_thumbprint,
        desktop_executable_path: desktopExecutablePath,
        desktop_executable_bytes: desktopExecutableBytes,
        desktop_executable_sha256: desktopExecutableSha256,
        desktop_executable_signer_subject: desktopExecutableIdentity.signer_subject,
        desktop_executable_signer_thumbprint: desktopExecutableIdentity.signer_thumbprint,
        desktop_archive_path: desktopArchivePath,
        desktop_archive_bytes: desktopArchiveBytes,
        desktop_archive_sha256: desktopArchiveSha256
      });
    }
    let launchEnv;
    try {
      launchEnv = this.#readDesktopLaunch(bundlePath).env;
    } catch {
      launchEnv = {};
    }
    let desktopVersion = null;
    try {
      desktopVersion = normalizeDesktopVersion(await this.#probeDesktopVersion(desktopExecutablePath));
    } catch {
    }
    let nodeVersion = null;
    try {
      nodeVersion = normalizeNodeVersion(await this.#probeNodeVersion(nodeExecutable));
    } catch {
    }
    const nodeCompatible = nodeVersion !== null && isSupportedNodeVersion(nodeVersion);
    const observedDesktopVersion = desktopVersion ?? "unavailable";
    const observedAppVersion = launchEnv.ZCODE_APP_VERSION ?? "unavailable";
    const observedBuildCommitId = launchEnv.ZCODE_BUILD_COMMIT_ID ?? "unavailable";
    const registryPinned = await this.#builtinRegistryPinned(builtinPath);
    let registry2 = null;
    if (!registryPinned) {
      const dataBaseDir = await this.#personalDataBaseDir();
      const runtimePath = dataBaseDir && launchEnv.ZCODE_APP_VERSION ? officialRuntimeRegistryPath({
        dataBaseDir,
        appVersion: launchEnv.ZCODE_APP_VERSION,
        env
      }) : null;
      registry2 = await selectOfficialBuiltinRegistry({ bundledPath: builtinPath, runtimePath });
    }
    const installationFingerprint = computeOfficialInstallationFingerprint({
      desktop_version: observedDesktopVersion,
      desktop_app_version: observedAppVersion,
      desktop_build_commit_id: observedBuildCommitId,
      desktop_executable_bytes: desktopExecutableBytes,
      desktop_executable_sha256: desktopExecutableSha256 ?? "unavailable",
      desktop_archive_bytes: desktopArchiveBytes,
      desktop_archive_sha256: desktopArchiveSha256 ?? "unavailable",
      bundle_bytes: bundleBytes,
      bundle_sha256: bundleSha256 ?? "unavailable",
      builtin_provider_config_bytes: builtinBytes,
      builtin_provider_config_sha256: builtinSha256 ?? "unavailable",
      runtime_host_bytes: runtimeHostBytes,
      runtime_host_sha256: runtimeHostSha256 ?? "unavailable",
      desktop_signer_thumbprint: desktopExecutableIdentity.signer_thumbprint ?? "",
      runtime_host_signer_thumbprint: runtimeHostIdentity.signer_thumbprint ?? "",
      node_version: nodeVersion ?? "unavailable"
    });
    const manifestCandidate = this.#manifest.find(
      (entry) => entry.desktop_version === desktopVersion && entry.bundle_bytes === bundleBytes && bundleSha256 !== null && entry.bundle_sha256.toLowerCase() === bundleSha256.toLowerCase()
    ) ?? null;
    const mismatches = [];
    if (!manifestCandidate) {
      mismatches.push("desktop version/bundle bytes/SHA-256 are not in the compatibility manifest");
    } else {
      if (manifestCandidate.desktop_app_version !== observedAppVersion || manifestCandidate.desktop_build_commit_id !== observedBuildCommitId) {
        mismatches.push("Desktop launch identity does not match the compatibility manifest");
      }
      if (manifestCandidate.builtin_provider_config_bytes !== builtinBytes || builtinSha256 === null || manifestCandidate.builtin_provider_config_sha256.toLowerCase() !== builtinSha256.toLowerCase()) {
        mismatches.push("builtin provider config identity does not match the compatibility manifest");
      }
      if (manifestCandidate.runtime_host_bytes !== runtimeHostBytes || runtimeHostSha256 === null || manifestCandidate.runtime_host_sha256.toLowerCase() !== runtimeHostSha256.toLowerCase()) {
        mismatches.push("runtime-host identity does not match the compatibility manifest");
      }
      if (manifestCandidate.desktop_executable_bytes !== void 0 && (manifestCandidate.desktop_executable_bytes !== desktopExecutableBytes || desktopExecutableSha256 === null || manifestCandidate.desktop_executable_sha256?.toLowerCase() !== desktopExecutableSha256.toLowerCase())) {
        mismatches.push("Desktop executable identity does not match the compatibility manifest");
      }
      if (manifestCandidate.desktop_archive_bytes !== void 0 && (manifestCandidate.desktop_archive_bytes !== desktopArchiveBytes || desktopArchiveSha256 === null || manifestCandidate.desktop_archive_sha256?.toLowerCase() !== desktopArchiveSha256.toLowerCase())) {
        mismatches.push("Desktop archive identity does not match the compatibility manifest");
      }
    }
    const manifest = manifestCandidate && mismatches.length === 0 ? manifestCandidate : null;
    const manifestStage = manifest?.verification_stage ?? "VERIFIED";
    const common = {
      install_dir: installDir,
      install_source: discovery.source,
      installation_safety: "OFFICIAL_INSTALLATION_SAFE",
      installation_fingerprint: installationFingerprint,
      desktop_version: observedDesktopVersion,
      desktop_app_version: observedAppVersion,
      desktop_build_commit_id: observedBuildCommitId,
      bundle_path: bundlePath,
      bundle_bytes: bundleBytes,
      bundle_sha256: bundleSha256,
      builtin_provider_config_path: builtinPath,
      builtin_provider_config_bytes: builtinBytes,
      builtin_provider_config_sha256: builtinSha256,
      active_builtin_provider_config_path: registry2?.path ?? builtinPath,
      active_builtin_provider_config_source: registry2?.source ?? "bundled",
      active_builtin_provider_config_revision: registry2?.revision ?? null,
      runtime_host_path: runtimeHostPath,
      runtime_host_bytes: runtimeHostBytes,
      runtime_host_sha256: runtimeHostSha256,
      runtime_host_signer_subject: runtimeHostIdentity.signer_subject,
      runtime_host_signer_thumbprint: runtimeHostIdentity.signer_thumbprint,
      desktop_executable_path: desktopExecutablePath,
      desktop_executable_bytes: desktopExecutableBytes,
      desktop_executable_sha256: desktopExecutableSha256,
      desktop_executable_signer_subject: desktopExecutableIdentity.signer_subject,
      desktop_executable_signer_thumbprint: desktopExecutableIdentity.signer_thumbprint,
      desktop_archive_path: desktopArchivePath,
      desktop_archive_bytes: desktopArchiveBytes,
      desktop_archive_sha256: desktopArchiveSha256,
      node_version: nodeVersion,
      node_compatible: nodeCompatible,
      manifest
    };
    if (manifest && manifestStage === "VERIFIED") {
      return {
        status: "OFFICIAL_RUNTIME_VERIFIED",
        ...common,
        discount_capability: manifest.coding_plan_discount_verified ? "OFFICIAL_DISCOUNT_VERIFIED" : "OFFICIAL_DISCOUNT_NOT_VERIFIED",
        start_plan_static_compatibility: manifest.start_plan_static_compatibility,
        reason: null,
        node_executable: nodeExecutable
      };
    }
    const diagnosticReason = mismatches.join("; ") || "runtime identity is not present in the reviewed compatibility manifest";
    if (manifest && manifestStage === "EXPERIMENTAL") {
      return {
        status: "OFFICIAL_RUNTIME_EXPERIMENTAL",
        ...common,
        discount_capability: "OFFICIAL_DISCOUNT_NOT_VERIFIED",
        start_plan_static_compatibility: manifest.start_plan_static_compatibility,
        reason: `SAFE_INSTALLATION_EXPERIMENTAL_MANIFEST: ${diagnosticReason}`,
        node_executable: nodeExecutable
      };
    }
    return {
      status: "OFFICIAL_RUNTIME_UNVERIFIED",
      ...common,
      discount_capability: "OFFICIAL_DISCOUNT_NOT_VERIFIED",
      start_plan_static_compatibility: "OFFLINE_RESEARCH_PENDING",
      reason: `SAFE_INSTALLATION_MANIFEST_UNVERIFIED: ${diagnosticReason}`,
      node_executable: nodeExecutable
    };
  }
  async resolve() {
    const descriptor = await this.inspect();
    if (descriptor.installation_safety !== "OFFICIAL_INSTALLATION_SAFE" || !descriptor.bundle_path || !descriptor.builtin_provider_config_path || !descriptor.active_builtin_provider_config_path || !descriptor.runtime_host_path) {
      throw new BridgeError(
        "provider_config_invalid",
        `OFFICIAL_INSTALLATION_UNSAFE: ${descriptor.reason ?? "installed Official AppServer is unavailable"}; OFFICIAL_DISCOUNT_NOT_VERIFIED`
      );
    }
    const registryPinned = await this.#builtinRegistryPinned(descriptor.builtin_provider_config_path);
    const base = this.#baseResolver ?? new NodeRuntimeResolver({
      env: this.#env,
      ...this.#homeDir ? { homeDir: this.#homeDir } : {},
      ...this.#host ? { host: this.#host } : {}
    });
    const configured = await base.resolve();
    return {
      ...configured,
      nodeExecutable: descriptor.node_executable,
      zcodeEntrypoint: descriptor.bundle_path,
      providerBuiltinConfigFile: registryPinned ? configured.providerBuiltinConfigFile : descriptor.active_builtin_provider_config_path
    };
  }
  /** True only for an explicit builtin file that is not this installation's bundled file. */
  async #builtinRegistryPinned(bundledPath) {
    return isOfficialBuiltinRegistryPin(
      this.#persistedEnv()["ZCODE_BUILTIN_PROVIDER_CONFIG_FILE"],
      bundledPath
    );
  }
  #persistedEnv() {
    return loadPersistedRuntimeEnvironment(
      this.#env,
      this.#homeDir,
      this.#host ?? codexHostProfile(this.#homeDir)
    );
  }
  /** Data base directory of the personal provider config the base resolver selects; null when unavailable. */
  async #personalDataBaseDir() {
    try {
      const base = this.#baseResolver ?? new NodeRuntimeResolver({
        env: this.#env,
        ...this.#homeDir ? { homeDir: this.#homeDir } : {},
        ...this.#host ? { host: this.#host } : {}
      });
      return zcodeDataBaseDir((await base.resolve()).providerPersonalConfigFile);
    } catch {
      return null;
    }
  }
};
function unverified(reason, nodeExecutable, details = {}) {
  return {
    status: "OFFICIAL_RUNTIME_UNVERIFIED",
    installation_safety: details.installation_safety ?? "OFFICIAL_INSTALLATION_INCOMPLETE",
    installation_fingerprint: details.installation_fingerprint ?? null,
    discount_capability: "OFFICIAL_DISCOUNT_NOT_VERIFIED",
    start_plan_static_compatibility: null,
    reason,
    install_dir: details.install_dir ?? null,
    install_source: details.install_source ?? null,
    desktop_version: details.desktop_version ?? null,
    desktop_app_version: details.desktop_app_version ?? null,
    desktop_build_commit_id: details.desktop_build_commit_id ?? null,
    bundle_path: details.bundle_path ?? null,
    bundle_bytes: details.bundle_bytes ?? null,
    bundle_sha256: details.bundle_sha256 ?? null,
    builtin_provider_config_path: details.builtin_provider_config_path ?? null,
    builtin_provider_config_bytes: details.builtin_provider_config_bytes ?? null,
    builtin_provider_config_sha256: details.builtin_provider_config_sha256 ?? null,
    active_builtin_provider_config_path: details.active_builtin_provider_config_path ?? null,
    active_builtin_provider_config_source: details.active_builtin_provider_config_source ?? null,
    active_builtin_provider_config_revision: details.active_builtin_provider_config_revision ?? null,
    runtime_host_path: details.runtime_host_path ?? null,
    runtime_host_bytes: details.runtime_host_bytes ?? null,
    runtime_host_sha256: details.runtime_host_sha256 ?? null,
    runtime_host_signer_subject: details.runtime_host_signer_subject ?? null,
    runtime_host_signer_thumbprint: details.runtime_host_signer_thumbprint ?? null,
    desktop_executable_path: details.desktop_executable_path ?? null,
    desktop_executable_bytes: details.desktop_executable_bytes ?? null,
    desktop_executable_sha256: details.desktop_executable_sha256 ?? null,
    desktop_executable_signer_subject: details.desktop_executable_signer_subject ?? null,
    desktop_executable_signer_thumbprint: details.desktop_executable_signer_thumbprint ?? null,
    desktop_archive_path: details.desktop_archive_path ?? null,
    desktop_archive_bytes: details.desktop_archive_bytes ?? null,
    desktop_archive_sha256: details.desktop_archive_sha256 ?? null,
    node_executable: nodeExecutable,
    node_version: details.node_version ?? null,
    node_compatible: details.node_compatible === true,
    manifest: details.manifest ?? null
  };
}
function unsafe(reason, nodeExecutable, details = {}) {
  return unverified(reason, nodeExecutable, {
    ...details,
    installation_safety: "OFFICIAL_INSTALLATION_UNSAFE"
  });
}
function executableArchitectureFailure(identity, label) {
  if (identity.architecture !== "x64") {
    return `OFFICIAL_INSTALLATION_UNSAFE: ${label} is not an x64 PE executable`;
  }
  return null;
}
async function inspectWindowsExecutable(filePath) {
  const architecture = readPortableExecutableArchitecture(filePath);
  const systemRoot = process.env["SystemRoot"]?.trim();
  let signatureStatus = "";
  let signerSubject = null;
  let signerThumbprint = null;
  if (systemRoot) {
    try {
      const powershell = path9.join(
        systemRoot,
        "System32",
        "WindowsPowerShell",
        "v1.0",
        "powershell.exe"
      );
      const script = [
        "$ProgressPreference = 'SilentlyContinue'",
        "$ErrorActionPreference = 'Stop'",
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)",
        "$target = $env:ZCODE_BRIDGE_AUTHENTICODE_FILE",
        "if ([string]::IsNullOrWhiteSpace($target)) { exit 2 }",
        "$signature = Get-AuthenticodeSignature -LiteralPath $target",
        "$certificate = $signature.SignerCertificate",
        "[pscustomobject]@{",
        "status = [string]$signature.Status;",
        "subject = if ($null -eq $certificate) { $null } else { [string]$certificate.Subject };",
        "thumbprint = if ($null -eq $certificate) { $null } else { [string]$certificate.Thumbprint }",
        "} | ConvertTo-Json -Compress"
      ].join("\n");
      const encoded = Buffer.from(script, "utf16le").toString("base64");
      const { stdout } = await execFileAsync(powershell, [
        "-NoProfile",
        "-NonInteractive",
        "-EncodedCommand",
        encoded
      ], {
        encoding: "utf8",
        timeout: 3e4,
        windowsHide: true,
        env: {
          SystemRoot: systemRoot,
          ZCODE_BRIDGE_AUTHENTICODE_FILE: filePath
        }
      });
      const parsed = JSON.parse(stdout.trim());
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        const value = parsed;
        signatureStatus = typeof value["status"] === "string" ? value["status"] : "";
        signerSubject = typeof value["subject"] === "string" ? value["subject"] : null;
        signerThumbprint = typeof value["thumbprint"] === "string" ? value["thumbprint"] : null;
      }
    } catch {
    }
  }
  return {
    architecture,
    signature_status: signatureStatus,
    signer_subject: signerSubject,
    signer_thumbprint: signerThumbprint
  };
}
function readPortableExecutableArchitecture(filePath) {
  const fd = openSync2(filePath, "r");
  try {
    const dosHeader = Buffer.alloc(64);
    if (readSync2(fd, dosHeader, 0, dosHeader.length, 0) !== dosHeader.length || dosHeader.toString("ascii", 0, 2) !== "MZ") {
      return "unknown";
    }
    const peOffset = dosHeader.readUInt32LE(60);
    if (!Number.isSafeInteger(peOffset) || peOffset < 64 || peOffset > 64 * 1024 * 1024) {
      return "unknown";
    }
    const coffHeader = Buffer.alloc(6);
    if (readSync2(fd, coffHeader, 0, coffHeader.length, peOffset) !== coffHeader.length || coffHeader.toString("ascii", 0, 4) !== "PE\0\0") {
      return "unknown";
    }
    return coffHeader.readUInt16LE(4) === 34404 ? "x64" : "unknown";
  } finally {
    closeSync2(fd);
  }
}
async function canonicalDirectory(candidate) {
  const stat5 = await lstat(candidate);
  if (!stat5.isDirectory() || stat5.isSymbolicLink()) throw new Error("installed ZCode root is not a real directory");
  return realpath(candidate);
}
async function canonicalFileInside(root, candidate, label) {
  const stat5 = await lstat(candidate);
  if (!stat5.isFile() || stat5.isSymbolicLink()) throw new Error(`${label} is not a regular file`);
  const resolved = await realpath(candidate);
  const relative = path9.relative(root, resolved);
  if (!relative || relative === ".." || relative.startsWith(`..${path9.sep}`) || path9.isAbsolute(relative)) {
    throw new Error(`${label} resolves outside the installed ZCode root`);
  }
  return resolved;
}
async function sha256File(filePath) {
  const hash = createHash4("sha256");
  await new Promise((resolve, reject) => {
    const stream = createReadStream(filePath);
    stream.on("data", (chunk) => hash.update(chunk));
    stream.once("error", reject);
    stream.once("end", resolve);
  });
  return hash.digest("hex");
}
async function optionalSha256(hashFile, filePath) {
  try {
    return await hashFile(filePath);
  } catch {
    return null;
  }
}
async function probeNodeCliVersion(executable) {
  const { stdout } = await execFileAsync(executable, ["--version"], {
    encoding: "utf8",
    timeout: 5e3,
    windowsHide: true
  });
  return stdout.trim();
}
function normalizeNodeVersion(value) {
  const normalized = value.trim().replace(/^v/u, "");
  if (!/^\d+\.\d+\.\d+$/u.test(normalized)) throw new Error(`invalid Node version output: ${value.slice(0, 80)}`);
  return normalized;
}
function normalizeDesktopVersion(value) {
  const normalized = value.trim();
  if (!/^\d+\.\d+\.\d+(?:\.\d+)?(?:-[0-9A-Za-z.-]+)?$/u.test(normalized)) {
    throw new Error(`invalid Desktop file version output: ${value.slice(0, 80)}`);
  }
  return normalized;
}
async function probeWindowsFileVersion(executable) {
  const script = [
    "$path = $env:ZCODE_BRIDGE_VERSION_FILE",
    "if ([string]::IsNullOrWhiteSpace($path)) { exit 2 }",
    "$version = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($path).FileVersion",
    "[Console]::Out.Write($version)"
  ].join("; ");
  const encoded = Buffer.from(script, "utf16le").toString("base64");
  const systemRoot = process.env["SystemRoot"]?.trim();
  if (!systemRoot) throw new Error("SystemRoot is unavailable for the Windows version probe");
  const powershell = path9.join(
    systemRoot,
    "System32",
    "WindowsPowerShell",
    "v1.0",
    "powershell.exe"
  );
  const { stdout } = await execFileAsync(powershell, [
    "-NoProfile",
    "-NonInteractive",
    "-EncodedCommand",
    encoded
  ], {
    encoding: "utf8",
    timeout: 5e3,
    windowsHide: true,
    env: {
      SystemRoot: systemRoot,
      ZCODE_BRIDGE_VERSION_FILE: executable
    }
  });
  return stdout.trim();
}
function errorMessage(error2) {
  const message = error2 instanceof Error ? error2.message : String(error2);
  return message.slice(0, 500);
}

// src/adapters/official-host-adapter.ts
var OFFICIAL_HOST_TRANSPORT_MAX_FRAME_BYTES = 16 * 1024 * 1024;
var OFFICIAL_HOST_ASSET_RELATIVE_ROOT = "./vendor/official-host/win32-x64-node24.16.0-zcode3.18.2-fec97590";
var OFFICIAL_HOST_ASSETS = {
  hostModule: {
    relativePath: "official-host-runtime.mjs",
    bytes: 1829872,
    sha256: "7E2B8B772F1DD83135903B64D569D634C7E7FC6F303460E08C98E27D311B6A91"
  },
  runtimeHost: {
    relativePath: "zcode-runtime-host.exe",
    bytes: 179608,
    sha256: "C2C8FF5FF28CBDDC4F177C094AA67C322830889612251BD173BAAABC89379AB4"
  },
  keyringLoader: {
    relativePath: "node_modules/@napi-rs/keyring/index.js",
    bytes: 29176,
    sha256: "8A89DB37F981D05B484EB063ADAE3399660AE7734AD38797463E5691382F5036"
  },
  keyringPackage: {
    relativePath: "node_modules/@napi-rs/keyring/package.json",
    bytes: 3325,
    sha256: "4BA8C90AC72BE27FCB3337ED7BC0159C68747E0824294DF5F2AAAEB03130CD4F"
  },
  keyringNativePackage: {
    relativePath: "node_modules/@napi-rs/keyring-win32-x64-msvc/package.json",
    bytes: 641,
    sha256: "1552C08589EEAEBC3680642883A8CAFEA8C72F80ED62908DE814177498562121"
  },
  keyringNative: {
    relativePath: "node_modules/@napi-rs/keyring-win32-x64-msvc/keyring.win32-x64-msvc.node",
    bytes: 1912832,
    sha256: "52B16658275B7848F8081A6542FEE3448F1B1C5D3A36487107AE0E7CEC95AC6F"
  }
};
async function loadOfficialStartPlanAuthenticationResolverFactory(workerModuleUrl = import.meta.url) {
  const assets = await verifyOfficialHostAssets(workerModuleUrl);
  const module = await loadOfficialHostModule(assets.hostModulePath);
  if (typeof module.createOfficialStartPlanAuthenticationResolver !== "function") {
    throw new BridgeError(
      "provider_config_invalid",
      "The Official Host module is missing the Start Plan authentication resolver."
    );
  }
  return module.createOfficialStartPlanAuthenticationResolver;
}
async function loadOfficialHostProductVersion(workerModuleUrl = import.meta.url) {
  const assets = await verifyOfficialHostAssets(workerModuleUrl);
  const module = await loadOfficialHostModule(assets.hostModulePath);
  return normalizeOfficialHostProductVersion(module.ZCODE_PRODUCT_VERSION);
}
async function verifyOfficialHostAssets(workerModuleUrl = import.meta.url) {
  const workerUrl = workerModuleUrl instanceof URL ? workerModuleUrl : new URL(workerModuleUrl);
  const root = fileURLToPath3(new URL(`${OFFICIAL_HOST_ASSET_RELATIVE_ROOT}/`, workerUrl));
  let rootReal;
  try {
    const rootStat = await lstat2(root);
    if (!rootStat.isDirectory() || rootStat.isSymbolicLink()) throw new Error("not a real directory");
    rootReal = await realpath2(root);
  } catch (error2) {
    throw new BridgeError("runtime_not_found", "The shipped Official Host asset directory is absent.", { cause: error2 });
  }
  const verified = /* @__PURE__ */ new Map();
  for (const [name, definition] of Object.entries(OFFICIAL_HOST_ASSETS)) {
    const candidate = path10.resolve(rootReal, definition.relativePath);
    try {
      const candidateStat = await lstat2(candidate);
      if (!candidateStat.isFile() || candidateStat.isSymbolicLink()) throw new Error("not a regular file");
      const candidateReal = await realpath2(candidate);
      if (!isPathInside(rootReal, candidateReal)) throw new Error("resolved outside the shipped asset root");
      if (candidateStat.size !== definition.bytes) throw new Error("byte length mismatch");
      const sha2562 = await sha256File2(candidateReal);
      if (sha2562.toUpperCase() !== definition.sha256) throw new Error("SHA-256 mismatch");
      verified.set(name, candidateReal);
    } catch (error2) {
      throw new BridgeError("provider_config_invalid", "A shipped Official Host asset failed presence or integrity validation.", {
        cause: error2
      });
    }
  }
  const manifestDigest = createHash5("sha256").update(JSON.stringify(
    Object.entries(OFFICIAL_HOST_ASSETS).sort(([left], [right]) => left.localeCompare(right)).map(([name, definition]) => ({
      name,
      relativePath: definition.relativePath,
      bytes: definition.bytes,
      sha256: definition.sha256
    }))
  ), "utf8").digest("hex");
  return {
    root: rootReal,
    hostModulePath: verified.get("hostModule"),
    runtimeHostPath: verified.get("runtimeHost"),
    manifestDigest
  };
}
async function loadOfficialHostModule(modulePath) {
  return resolveOfficialHostModule(await import(pathToFileURL(modulePath).href));
}
async function resolveOfficialHostModule(source) {
  const value = typeof source === "function" ? await source() : source;
  if (!value || typeof value.ZCodeAgentProcessManager !== "function" || typeof value.ZCodeProtocolClient !== "function") {
    throw new BridgeError("provider_config_invalid", "The Official Host module is missing required exports.");
  }
  return value;
}
function normalizeOfficialHostProductVersion(value) {
  const version2 = typeof value === "string" ? value.trim() : "";
  if (!/^[0-9A-Za-z][0-9A-Za-z._+-]{0,63}$/u.test(version2)) {
    throw new BridgeError(
      "provider_config_invalid",
      "The Official Host module is missing a valid product version."
    );
  }
  return version2;
}
var officialHostEnvironmentTail = Promise.resolve();
function isPathInside(root, candidate) {
  const relative = path10.relative(root, candidate);
  return relative !== "" && !relative.startsWith(`..${path10.sep}`) && relative !== ".." && !path10.isAbsolute(relative);
}
async function sha256File2(filePath) {
  const hash = createHash5("sha256");
  await new Promise((resolve, reject) => {
    const stream = createReadStream2(filePath);
    stream.on("data", (chunk) => hash.update(chunk));
    stream.once("error", reject);
    stream.once("end", resolve);
  });
  return hash.digest("hex");
}

// src/runtime/start-plan-production-auth.ts
import { version as readOsVersion } from "node:os";
function isRecord4(value) {
  return !!value && typeof value === "object" && !Array.isArray(value);
}
function asOfficialBillingEnvelope(value) {
  if (!isRecord4(value)) return null;
  const data = isRecord4(value.data) ? value.data : void 0;
  return {
    success: value.success,
    code: value.code,
    msg: value.msg,
    ...data ? { data: {
      plans: data.plans,
      balances: data.balances,
      server_time: data.server_time
    } } : {}
  };
}
function isSuccessfulBusinessEnvelope(envelope) {
  return envelope.success !== false && (envelope.code === void 0 || envelope.code === 0 || envelope.code === 200);
}
function stringKeyedArray(value) {
  return Array.isArray(value) ? value.filter(isRecord4) : [];
}
function isActiveStartPlan(plan) {
  const status = typeof plan.status === "string" ? plan.status.trim().toLowerCase() : "";
  const planId = typeof plan.plan_id === "string" ? plan.plan_id.trim().toLowerCase() : "";
  const name = typeof plan.name === "string" ? plan.name.trim().toLowerCase() : "";
  const startPlanIdentity = planId.includes("start-plan") || planId.includes("start plan") || name.includes("start-plan") || name.includes("start plan");
  return status === "active" && startPlanIdentity;
}
function activeStartPlans(envelope) {
  return stringKeyedArray(envelope.data?.plans).filter(isActiveStartPlan);
}
function hasActiveStartPlan(envelope) {
  return activeStartPlans(envelope).length > 0;
}
function startPlanBalanceModelIds(balances) {
  const seen = /* @__PURE__ */ new Set();
  const models = [];
  for (const balance of balances) {
    const capabilities = Array.isArray(balance.capabilities) ? balance.capabilities : [];
    const capabilityModels = capabilities.flatMap((capability2) => {
      const raw = typeof capability2 === "string" ? capability2.trim().toLowerCase() : "";
      return raw.startsWith("model:") ? [raw.slice(6).trim()] : [];
    }).filter(Boolean);
    const candidates = capabilityModels.length > 0 ? capabilityModels : typeof balance.show_name === "string" ? [balance.show_name.trim().toLowerCase()] : [];
    for (const model of candidates) {
      if (!model || seen.has(model)) continue;
      seen.add(model);
      models.push(model);
    }
  }
  return models;
}
function readIdentifier(value) {
  return typeof value === "string" ? value.trim() : "";
}
function balanceBelongsToPlan(balance, plan) {
  const balanceUserPlanId = readIdentifier(balance.user_plan_id);
  const planUserPlanId = readIdentifier(plan.user_plan_id);
  if (balanceUserPlanId && planUserPlanId) return balanceUserPlanId === planUserPlanId;
  const balancePlanId = readIdentifier(balance.plan_id);
  const planId = readIdentifier(plan.plan_id);
  return Boolean(balancePlanId && planId && balancePlanId === planId);
}
function requestedModelBalances(balances, requestedModel) {
  return balances.filter((balance) => {
    const capabilities = Array.isArray(balance.capabilities) ? balance.capabilities : [];
    const capabilityModels = capabilities.flatMap((capability2) => {
      const raw = typeof capability2 === "string" ? capability2.trim().toLowerCase() : "";
      return raw.startsWith("model:") ? [raw.slice(6).trim()] : [];
    }).filter(Boolean);
    const candidates = capabilityModels.length > 0 ? capabilityModels : typeof balance.show_name === "string" ? [balance.show_name.trim().toLowerCase()] : [];
    return candidates.includes(requestedModel);
  });
}
function numericUnit(value) {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() && Number.isFinite(Number(value))) return Number(value);
  return null;
}
function finiteEpochSeconds(value) {
  const number3 = typeof value === "number" ? value : typeof value === "string" && value.trim() ? Number(value) : NaN;
  return Number.isFinite(number3) && number3 >= 0 ? number3 : void 0;
}
function normalizeBillingAvailabilityEnvelope(envelope, responseTimeSeconds2) {
  const data = envelope.data;
  if (!data) return envelope;
  const nowSeconds = responseTimeSeconds2 ?? (typeof data.server_time === "number" && Number.isFinite(data.server_time) && data.server_time >= 0 ? data.server_time : void 0) ?? Date.now() / 1e3;
  const plans = stringKeyedArray(data.plans).map((plan) => {
    const status = typeof plan.status === "string" ? plan.status.trim().toLowerCase() : "";
    const end = finiteEpochSeconds(plan.ends_at);
    return status === "active" && end !== void 0 && end > 0 && end <= nowSeconds ? { ...plan, status: "expired" } : plan;
  });
  const balances = stringKeyedArray(data.balances).filter((balance) => {
    const userPlanId = typeof balance.user_plan_id === "string" ? balance.user_plan_id : "";
    const planId = typeof balance.plan_id === "string" ? balance.plan_id : "";
    const owners = plans.filter((plan) => {
      const ownerUserPlanId = typeof plan.user_plan_id === "string" ? plan.user_plan_id : "";
      const ownerPlanId = typeof plan.plan_id === "string" ? plan.plan_id : "";
      return userPlanId && ownerUserPlanId ? userPlanId === ownerUserPlanId : planId === ownerPlanId;
    });
    return owners.length === 0 || owners.some((plan) => typeof plan.status === "string" && plan.status.trim().toLowerCase() !== "expired");
  });
  return {
    ...envelope,
    data: {
      ...data,
      plans,
      balances
    }
  };
}
function hasPendingActivation(envelope) {
  const data = envelope.data;
  if (!data) return false;
  const nowSeconds = typeof data.server_time === "number" && Number.isFinite(data.server_time) && data.server_time >= 0 ? data.server_time : Date.now() / 1e3;
  const effectiveTimes = activeStartPlans(envelope).flatMap((plan) => {
    const entitlements = stringKeyedArray(plan.entitlements);
    return entitlements.length > 0 ? entitlements.map((entry) => entry.effective_at) : [plan.starts_at];
  }).map((value) => value === null || value === void 0 || value === "" ? void 0 : Number(value));
  return effectiveTimes.length > 0 && effectiveTimes.every((value) => value !== void 0 && Number.isFinite(value) && value > nowSeconds);
}
function extractProviderCode(value) {
  if (!value) return void 0;
  const error2 = isRecord4(value.error) ? value.error : void 0;
  const candidates = [
    value.providerCode,
    error2?.providerCode,
    error2 && isRecord4(error2) ? error2.code : void 0,
    value.code
  ];
  const raw = candidates.find((candidate) => typeof candidate === "number" || typeof candidate === "string");
  const code = typeof raw === "number" || typeof raw === "string" ? String(raw).trim() : "";
  return /^[0-9A-Za-z_.-]{1,32}$/u.test(code) ? code : void 0;
}
function classifyEntitlementFailure(input) {
  const code = input.providerCode?.trim();
  const providerCode = code ? code : void 0;
  if (code === "3007") return { status: "captcha_required", reason: "provider requested captcha verification", providerCode, failureClass: "captcha_required" };
  if (code === "3012") return { status: "unusual_activity", reason: "provider blocked this identity due to unusual activity", providerCode, failureClass: "unusual_activity" };
  if (code === "3001") return { status: "billing_parameter_error", reason: "billing request parameters were rejected", providerCode, failureClass: "billing_parameter_error" };
  if (input.statusCode === 401) return { status: "unauthorized", reason: "credential was rejected as unauthenticated", failureClass: "unauthorized" };
  if (input.statusCode === 403) return { status: "forbidden", reason: "credential is authenticated but forbidden from this plan or model", failureClass: "forbidden" };
  const rawEnvelope = input.statusCode === 200 ? asOfficialBillingEnvelope(input.body) : void 0;
  const envelope = rawEnvelope ? normalizeBillingAvailabilityEnvelope(rawEnvelope, input.responseTimeSeconds) : void 0;
  const activePlans = envelope ? activeStartPlans(envelope) : [];
  if (envelope && isSuccessfulBusinessEnvelope(envelope) && activePlans.length > 0) {
    const balances = stringKeyedArray(envelope.data?.balances);
    const attributedBalances = balances.filter((balance) => activePlans.some((plan) => balanceBelongsToPlan(balance, plan)));
    const models = startPlanBalanceModelIds(attributedBalances);
    const requested = input.model?.trim().toLowerCase();
    if (!requested) {
      return { status: "unavailable", reason: "billing response had no requested model identity to authorize", failureClass: "response_malformed" };
    }
    if (hasPendingActivation(envelope)) {
      return {
        status: "unavailable",
        reason: "active Start Plan has not taken effect",
        failureClass: "activation_pending"
      };
    }
    if (models.length === 0) {
      return {
        status: "unavailable",
        reason: "billing response did not prove available model quota for this Start Plan",
        failureClass: "model_quota_unproven"
      };
    }
    if (!models.includes(requested)) {
      return { status: "model_unavailable", reason: "active Start Plan does not list the requested model", failureClass: "requested_model_absent" };
    }
    const relevant = requestedModelBalances(attributedBalances, requested);
    const units = relevant.map((balance) => numericUnit(balance.remaining_units));
    if (relevant.length === 0 || units.some((unit) => unit === null || unit < 0)) {
      return {
        status: "unavailable",
        reason: "billing response did not prove positive remaining quota for the requested model",
        failureClass: "model_quota_unproven"
      };
    }
    if (units.every((unit) => unit === 0)) {
      return {
        status: "quota_exhausted",
        reason: "Start Plan quota is exhausted for the requested model",
        failureClass: "quota_exhausted"
      };
    }
    return { status: "entitled", reason: "active Start Plan has positive quota for the requested model", failureClass: "unknown" };
  } else if (envelope && isSuccessfulBusinessEnvelope(envelope) && !hasActiveStartPlan(envelope)) {
    return { status: "no_entitlement", reason: "no active Start Plan was present in the billing response", failureClass: "active_plan_absent" };
  }
  if (input.statusCode === 429) return { status: "rate_limited", reason: "rate limited; quota state unknown from status alone", failureClass: "rate_limited" };
  if (input.statusCode >= 500) return { status: "unavailable", reason: "entitlement service error", failureClass: "service_error" };
  if (input.statusCode >= 400) return { status: "unavailable", reason: "entitlement query rejected without a recognized provider code", failureClass: "http_rejected" };
  if (envelope) return { status: "unavailable", reason: "billing response reported an unsuccessful business outcome", failureClass: "business_rejected" };
  return { status: "unavailable", reason: "entitlement response could not be interpreted", failureClass: "response_malformed" };
}
function sanitizeHeaderValue(value) {
  const trimmed = value?.trim();
  return trimmed && /^[\x20-\x7e]+$/u.test(trimmed) ? trimmed : void 0;
}
function clientLanguage() {
  try {
    return sanitizeHeaderValue(process.env.ZCODE_CLIENT_LANGUAGE) ?? sanitizeHeaderValue(Intl.DateTimeFormat().resolvedOptions().locale) ?? "unknown";
  } catch {
    return sanitizeHeaderValue(process.env.ZCODE_CLIENT_LANGUAGE) ?? "unknown";
  }
}
function clientTimezone() {
  try {
    return sanitizeHeaderValue(Intl.DateTimeFormat().resolvedOptions().timeZone) ?? "unknown";
  } catch {
    return "unknown";
  }
}
function osCategory() {
  if (process.platform === "darwin") return "macos";
  if (process.platform === "win32") return "windows";
  return "linux";
}
function officialBillingHeaders(input) {
  return {
    Authorization: `Bearer ${input.jwt}`,
    "X-Device-Mid": input.deviceMid,
    "User-Agent": `ZCode/${input.appVersion}`,
    "HTTP-Referer": input.origin,
    "X-Title": "Z Code@electron",
    "X-ZCode-App-Version": input.appVersion,
    "X-Release-Channel": process.env.ZCODE_ENV?.trim().toLowerCase() === "test" ? "test" : "production",
    "X-Platform": `${process.platform}-${process.arch}`,
    "X-Client-Language": clientLanguage(),
    "X-Client-Timezone": clientTimezone(),
    "X-Os-Category": osCategory(),
    "X-Os-Version": sanitizeHeaderValue(readOsVersion()) ?? "unknown"
  };
}
function failureVerdict(status) {
  return status === "no_entitlement" || status === "model_unavailable" || status === "quota_exhausted" ? "not_entitled" : "unavailable";
}
function withFailureFacts(verdict2, input) {
  const providerCode = verdict2.providerCode ?? null;
  return {
    status: verdict2.status,
    reason: verdict2.reason,
    ...providerCode ? { providerCode } : {},
    observedAt: input.observedAt,
    failureFacts: Object.freeze({
      request_attempted: input.requestAttempted,
      http_status: input.httpStatus,
      provider_code: providerCode,
      failure_class: verdict2.failureClass,
      entitlement_verdict: failureVerdict(verdict2.status)
    })
  };
}
var OFFICIAL_START_PLAN_ORIGIN = "https://zcode.z.ai";
var BILLING_REQUEST_TIMEOUT_MS = 15e3;
var StartPlanBillingEntitlement = class {
  #origin;
  #getAppVersion;
  #fetchImpl;
  #now;
  constructor(options) {
    this.#origin = (options.origin ?? OFFICIAL_START_PLAN_ORIGIN).replace(/\/+$/, "");
    this.#getAppVersion = options.getAppVersion;
    this.#fetchImpl = options.fetchImpl ?? fetch;
    this.#now = options.now ?? Date.now;
  }
  async check(input) {
    const observedAt = this.#now();
    const appVersion = await this.#getAppVersion();
    if (!appVersion || !/^[0-9A-Za-z][0-9A-Za-z._+-]{0,63}$/u.test(appVersion)) {
      return withFailureFacts({
        status: "unavailable",
        reason: "official cli version unavailable; refusing to guess",
        failureClass: "not_attempted"
      }, { observedAt, requestAttempted: false, httpStatus: null });
    }
    const deviceMid = sanitizeHeaderValue(input.deviceMid);
    if (!deviceMid) {
      return withFailureFacts({
        status: "unavailable",
        reason: "official device identity unavailable; refusing to guess",
        failureClass: "not_attempted"
      }, { observedAt, requestAttempted: false, httpStatus: null });
    }
    const url = `${this.#origin}/api/v1/zcode-plan/billing/balance?app_version=${encodeURIComponent(appVersion)}`;
    let response;
    try {
      response = await this.#fetchImpl(url, {
        method: "GET",
        headers: officialBillingHeaders({
          origin: this.#origin,
          appVersion,
          deviceMid,
          jwt: input.jwt
        }),
        signal: AbortSignal.any([input.signal, AbortSignal.timeout(BILLING_REQUEST_TIMEOUT_MS)])
      });
    } catch (error2) {
      if (input.signal.aborted) throw error2;
      return withFailureFacts({
        status: "unavailable",
        reason: "entitlement transport failed",
        failureClass: "transport"
      }, { observedAt: this.#now(), requestAttempted: true, httpStatus: null });
    }
    if (response.status === 200) {
      let body2;
      let providerCode2;
      try {
        const parsed = await response.json();
        if (isRecord4(parsed)) {
          body2 = parsed;
          providerCode2 = extractProviderCode(parsed);
        }
      } catch {
      }
      const classified = this.#interpretBillingBody({
        statusCode: response.status,
        providerCode: providerCode2,
        body: body2,
        model: input.model,
        responseTimeSeconds: responseTimeSeconds(response)
      });
      if (classified.status === "entitled") {
        let requestId = "";
        try {
          requestId = (response.headers.get("x-request-id") ?? "").trim();
        } catch {
        }
        return { status: "entitled", observedAt: this.#now(), requestId };
      }
      return withFailureFacts(classified, {
        observedAt: this.#now(),
        requestAttempted: true,
        httpStatus: response.status
      });
    }
    let body;
    let providerCode;
    try {
      const parsed = await response.json();
      if (isRecord4(parsed)) {
        body = parsed;
        providerCode = extractProviderCode(parsed);
      }
    } catch {
    }
    return withFailureFacts(this.#interpretBillingBody({
      statusCode: response.status,
      providerCode,
      body,
      model: input.model,
      responseTimeSeconds: responseTimeSeconds(response)
    }), { observedAt, requestAttempted: true, httpStatus: response.status });
  }
  #interpretBillingBody(input) {
    return classifyEntitlementFailure(input);
  }
};
function responseTimeSeconds(response) {
  try {
    const parsed = Date.parse(response.headers.get("date") ?? "");
    return Number.isFinite(parsed) ? parsed / 1e3 : void 0;
  } catch {
    return void 0;
  }
}

// tools/cost-lab/web-services.mjs
import { access as access2, stat as stat2 } from "node:fs/promises";
import path14 from "node:path";

// tools/cost-lab/path-discovery.mjs
import { existsSync as existsSync4, readFileSync as readFileSync4 } from "node:fs";
import path11 from "node:path";
var USER_HOME_SOURCES = Object.freeze(["HOME", "USERPROFILE", "FALLBACK"]);
var SETTING_FILE_STATUSES = Object.freeze([
  "ok",
  "absent",
  "unreadable",
  "invalid_json",
  "invalid_shape",
  "permission_denied"
]);
function isWindowsAbsolutePath2(value) {
  return /^[A-Za-z]:[\\/]/u.test(value) || /^\/\/[^\\/]+[\\/][^\\/]+(?:[\\/].*)?$/u.test(value) || /^\\\\[^\\/]+[\\/][^\\/]+(?:[\\/].*)?$/u.test(value);
}
function isAbsolutePathForPlatform2(value, platform = process.platform) {
  return platform === "win32" ? isWindowsAbsolutePath2(value) : path11.posix.isAbsolute(value);
}
function isPermissionDenied(error2) {
  return error2?.code === "EACCES" || error2?.code === "EPERM";
}
function resolveUserHome2({
  env = process.env,
  platform = process.platform,
  fallbackHomeDir = null
} = {}) {
  const pathImpl = platform === "win32" ? path11.win32 : path11.posix;
  const homeRaw = env.HOME?.trim() || null;
  const userProfileRaw = env.USERPROFILE?.trim() || null;
  if (platform !== "win32") {
    if (homeRaw) return { userHome: pathImpl.resolve(homeRaw), source: "HOME", homeRaw, homeConflict: null };
    const fallback = userProfileRaw ?? fallbackHomeDir;
    if (!fallback) throw new Error("user_home_unavailable");
    return {
      userHome: pathImpl.resolve(fallback),
      source: userProfileRaw ? "USERPROFILE" : "FALLBACK",
      homeRaw: null,
      homeConflict: null
    };
  }
  if (homeRaw) {
    const rooted = isWindowsAbsolutePath2(homeRaw);
    const matchesProfile = userProfileRaw !== null && pathImpl.normalize(homeRaw).toLowerCase() === pathImpl.normalize(userProfileRaw).toLowerCase();
    if (rooted && matchesProfile) {
      return { userHome: pathImpl.resolve(homeRaw), source: "HOME", homeRaw, homeConflict: null };
    }
    const conflict = !rooted ? "home_not_absolute" : userProfileRaw === null ? "home_without_userprofile" : "home_does_not_match_userprofile";
    if (userProfileRaw) {
      return {
        userHome: pathImpl.resolve(userProfileRaw),
        source: "USERPROFILE",
        homeRaw,
        homeConflict: conflict
      };
    }
    if (!fallbackHomeDir) throw new Error("windows_user_home_unavailable");
    return {
      userHome: pathImpl.resolve(fallbackHomeDir),
      source: "FALLBACK",
      homeRaw,
      homeConflict: conflict
    };
  }
  if (userProfileRaw) {
    return {
      userHome: pathImpl.resolve(userProfileRaw),
      source: "USERPROFILE",
      homeRaw: null,
      homeConflict: null
    };
  }
  if (!fallbackHomeDir) throw new Error("windows_user_home_unavailable");
  return {
    userHome: pathImpl.resolve(fallbackHomeDir),
    source: "FALLBACK",
    homeRaw: null,
    homeConflict: null
  };
}
function discoverZCodeData2({
  env = process.env,
  platform = process.platform,
  fallbackHomeDir = null,
  fileExists = existsSync4,
  readFile: readFile7 = (filePath) => readFileSync4(filePath, "utf8")
} = {}) {
  const pathImpl = platform === "win32" ? path11.win32 : path11.posix;
  const home = resolveUserHome2({ env, platform, fallbackHomeDir });
  const settingFile = pathImpl.join(home.userHome, ".zcode", "v2", "setting.json");
  let settingStatus = "ok";
  let settingError = null;
  let configuredDataBaseDir = null;
  if (!fileExists(settingFile)) {
    settingStatus = "absent";
  } else {
    let text;
    try {
      text = readFile7(settingFile);
    } catch (error2) {
      settingStatus = isPermissionDenied(error2) ? "permission_denied" : "unreadable";
      settingError = error2 instanceof Error ? error2.message : String(error2);
    }
    if (settingStatus === "ok") {
      let parsed;
      try {
        parsed = JSON.parse(text);
      } catch (error2) {
        settingStatus = "invalid_json";
        settingError = error2 instanceof Error ? error2.message : String(error2);
      }
      if (settingStatus === "ok") {
        if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
          settingStatus = "invalid_shape";
          settingError = "setting_json_not_object";
        } else {
          const raw = parsed.dataBaseDir;
          if (raw === void 0 || raw === null) {
          } else if (typeof raw !== "string") {
            settingStatus = "invalid_shape";
            settingError = "data_base_dir_not_string";
          } else {
            const trimmed = raw.trim();
            if (trimmed && isAbsolutePathForPlatform2(trimmed, platform)) {
              configuredDataBaseDir = pathImpl.resolve(trimmed);
            } else if (trimmed) {
              settingError = "relative_data_base_dir_ignored";
            }
          }
        }
      }
    }
  }
  const dataBaseDir = configuredDataBaseDir ?? home.userHome;
  return {
    userHome: home.userHome,
    userHomeSource: home.source,
    settingFile,
    settingStatus,
    settingError,
    configuredDataBaseDir,
    dataBaseDir,
    dataBaseDirSource: configuredDataBaseDir ? "setting.json" : "default",
    zcodeDataDir: pathImpl.join(dataBaseDir, ".zcode"),
    zcodeV2Dir: pathImpl.join(dataBaseDir, ".zcode", "v2")
  };
}
function resolveBillingDataBaseDir(explicitDataBaseDir, discoveryOptions = {}) {
  if (explicitDataBaseDir !== null && explicitDataBaseDir !== void 0) {
    if (typeof explicitDataBaseDir !== "string" || !explicitDataBaseDir.trim()) {
      throw new Error("billing_data_base_dir_empty");
    }
    return {
      dataBaseDir: path11.resolve(explicitDataBaseDir.trim()),
      dataBaseDirSource: "explicit",
      discovery: null
    };
  }
  const discovery = discoverZCodeData2(discoveryOptions);
  return {
    dataBaseDir: discovery.dataBaseDir,
    dataBaseDirSource: discovery.dataBaseDirSource,
    discovery
  };
}

// tools/cost-lab/official-runtime-manifest.mjs
import { createHash as createHash6 } from "node:crypto";
import { access } from "node:fs/promises";
import path12 from "node:path";
var resolverModule = new URL("../../dist/src/runtime/official-app-server-runtime.js", import.meta.url);
async function inspectOfficialRuntimeAssets({ env, platform, arch } = {}) {
  if (!await access(resolverModule).then(() => true, () => false)) {
    return {
      install_root: null,
      install_root_fingerprint: null,
      runtime_status: "OFFICIAL_RUNTIME_UNVERIFIED",
      installation_safety: "OFFICIAL_INSTALLATION_INCOMPLETE",
      installation_fingerprint: null,
      discount_status: "OFFICIAL_DISCOUNT_NOT_VERIFIED",
      reason: "bridge_build_missing",
      manifest: null,
      assets: {}
    };
  }
  const { OfficialAppServerRuntimeResolver: OfficialAppServerRuntimeResolver2 } = await import(resolverModule.href);
  const runtime = await new OfficialAppServerRuntimeResolver2({ env, platform, architecture: arch }).inspect();
  const root = runtime.install_dir;
  const assets = {};
  for (const name of ["bundle", "runtime_host", "builtin_provider_config"]) {
    const file = runtime[`${name}_path`];
    if (root && file) {
      assets[name] = {
        relative_path: path12.relative(root, file).split(path12.sep).join("/"),
        bytes: runtime[`${name}_bytes`],
        sha256: runtime[`${name}_sha256`]
      };
    }
  }
  return {
    install_root: root,
    install_source: runtime.install_source,
    install_root_fingerprint: root ? createHash6("sha256").update(root).digest("hex") : null,
    runtime_status: runtime.status,
    installation_safety: runtime.installation_safety ?? "OFFICIAL_INSTALLATION_INCOMPLETE",
    installation_fingerprint: runtime.installation_fingerprint ?? null,
    experimental_authorization: runtime.experimental_authorization ?? null,
    discount_status: runtime.discount_capability,
    desktop_version: runtime.desktop_version,
    desktop_app_version: runtime.desktop_app_version ?? null,
    desktop_build_commit_id: runtime.desktop_build_commit_id ?? null,
    node_executable: runtime.node_executable,
    reason: runtime.reason,
    manifest: runtime.manifest && { ...runtime.manifest, version: runtime.manifest.desktop_version },
    desktop_executable: runtime.desktop_executable_path ? {
      bytes: runtime.desktop_executable_bytes,
      sha256: runtime.desktop_executable_sha256,
      signer_subject: runtime.desktop_executable_signer_subject,
      signer_thumbprint: runtime.desktop_executable_signer_thumbprint
    } : null,
    desktop_archive: runtime.desktop_archive_path ? {
      bytes: runtime.desktop_archive_bytes,
      sha256: runtime.desktop_archive_sha256
    } : null,
    runtime_host_signer: {
      subject: runtime.runtime_host_signer_subject ?? null,
      thumbprint: runtime.runtime_host_signer_thumbprint ?? null
    },
    assets
  };
}

// tools/cost-lab/vendor-loader.mjs
import { createHash as createHash7 } from "node:crypto";
import { existsSync as existsSync5 } from "node:fs";
import { readFile as readFile2, stat } from "node:fs/promises";
import { registerHooks } from "node:module";
import path13 from "node:path";
import { fileURLToPath as fileURLToPath4, pathToFileURL as pathToFileURL2 } from "node:url";
var SCRIPT_ROOT = path13.dirname(fileURLToPath4(import.meta.url));
var BUNDLED_VENDOR_ROOT = path13.basename(SCRIPT_ROOT) === "dist" && existsSync5(path13.join(SCRIPT_ROOT, "vendor", "official-billing-runtime.mjs"));
var PROJECT_ROOT = BUNDLED_VENDOR_ROOT ? path13.resolve(SCRIPT_ROOT, "..") : path13.resolve(SCRIPT_ROOT, "..", "..");
var OFFICIAL_RUNTIME_PATH = path13.join(
  SCRIPT_ROOT,
  "vendor",
  "official-billing-runtime.mjs"
);
var OFFICIAL_RUNTIME_SHA256 = "dcb3fc7cb7a62e7a6dbe7ce8a9e1427075309458453641f6a4c7e8e1971a63e6";
var OFFICIAL_KEYRING_NATIVE_SHA256 = "52b16658275b7848f8081a6542fee3448f1b1c5d3a36487107ae0e7cec95ac6f";
var OFFICIAL_HOST_MODULES = BUNDLED_VENDOR_ROOT ? path13.join(
  PROJECT_ROOT,
  "worker",
  "vendor",
  "official-host",
  "win32-x64-node24.16.0-zcode3.18.2-fec97590",
  "node_modules",
  "@napi-rs"
) : path13.join(
  PROJECT_ROOT,
  "plugins",
  "codex-zcode-bridge",
  "worker",
  "vendor",
  "official-host",
  "win32-x64-node24.16.0-zcode3.18.2-fec97590",
  "node_modules",
  "@napi-rs"
);
var OFFICIAL_KEYRING_JS_PATH = path13.join(OFFICIAL_HOST_MODULES, "keyring", "index.js");
var OFFICIAL_KEYRING_NATIVE_PATH = path13.join(
  OFFICIAL_HOST_MODULES,
  "keyring-win32-x64-msvc",
  "keyring.win32-x64-msvc.node"
);
var keyringHook;
function sha256(data) {
  return createHash7("sha256").update(data).digest("hex");
}
async function verifyFile(filePath, expectedSha256, code) {
  const metadata = await stat(filePath).catch(() => null);
  if (!metadata?.isFile()) throw new Error(`${code}_missing`);
  const digest = sha256(await readFile2(filePath));
  if (digest !== expectedSha256) throw new Error(`${code}_hash_mismatch`);
  return digest;
}
async function verifyOfficialVendor() {
  const runtimeSha256 = await verifyFile(
    OFFICIAL_RUNTIME_PATH,
    OFFICIAL_RUNTIME_SHA256,
    "official_billing_runtime"
  );
  const keyringNativeSha256 = await verifyFile(
    OFFICIAL_KEYRING_NATIVE_PATH,
    OFFICIAL_KEYRING_NATIVE_SHA256,
    "official_keyring_native"
  );
  await verifyFile(
    OFFICIAL_KEYRING_JS_PATH,
    "8a89db37f981d05b484eb063adae3399660ae7734ad38797463e5691382f5036",
    "official_keyring_js"
  );
  return {
    runtime_sha256: runtimeSha256,
    keyring_native_sha256: keyringNativeSha256,
    keyring_native_source: "official_host_vendor"
  };
}
async function prepareOfficialBillingVendor({
  env = process.env,
  platform = process.platform,
  arch = process.arch
} = {}) {
  if (platform !== "win32" || arch !== "x64") {
    throw new Error(`official_billing_vendor_unsupported_platform:${platform}:${arch}`);
  }
  const integrity = await verifyOfficialVendor();
  env.NAPI_RS_NATIVE_LIBRARY_PATH = OFFICIAL_KEYRING_NATIVE_PATH;
  const bundleUrl = pathToFileURL2(OFFICIAL_RUNTIME_PATH).href;
  keyringHook ??= registerHooks({
    resolve(specifier, context, nextResolve) {
      if (specifier === "@napi-rs/keyring" && context.parentURL === bundleUrl) {
        return {
          url: pathToFileURL2(OFFICIAL_KEYRING_JS_PATH).href,
          format: "commonjs",
          shortCircuit: true
        };
      }
      return nextResolve(specifier, context);
    }
  });
  return integrity;
}

// tools/cost-lab/web-services.mjs
async function inspectCostLabEnvironment(options = {}) {
  const env = options.env ?? process.env;
  const platform = options.platform ?? process.platform;
  const arch = options.arch ?? process.arch;
  const nodeVersion = options.nodeVersion ?? process.versions.node;
  const generatedAt = (options.now?.() ?? /* @__PURE__ */ new Date()).toISOString();
  const data = resolveBillingDataBaseDir(null, {
    env,
    platform,
    fallbackHomeDir: options.fallbackHomeDir,
    fileExists: options.fileExists,
    readFile: options.readFile
  });
  const runtime = await (options.inspectRuntime ?? inspectOfficialRuntimeAssets)({ env, platform, arch });
  const billing = await inspectBillingAvailability(options);
  const credentials = await inspectCredentialAvailability(data, options);
  const nodeOk = /^24\.16\.\d+$/u.test(nodeVersion);
  const deep = options.deep === true;
  const protocolSmoke = deep && typeof options.protocolSmoke === "function" ? await runBoundedProtocolSmoke(options.protocolSmoke, options.protocolSmokeTimeoutMs ?? 3e4) : {
    status: "NOT_RUN",
    reason: deep ? "protocol_smoke_runner_not_configured" : "deep_check_not_requested",
    model_requests: 0
  };
  return {
    schema_version: 1,
    kind: "cost_lab_environment",
    generated_at: generatedAt,
    host: {
      platform,
      arch,
      node_version: nodeVersion,
      node_compatible: nodeOk,
      supported: platform === "win32" && arch === "x64" && nodeOk
    },
    zcode: {
      installed: runtime.install_root !== null,
      install_source: runtime.install_source ?? null,
      install_root_fingerprint: runtime.install_root_fingerprint,
      installation_fingerprint: runtime.installation_fingerprint ?? null,
      installation_safety: runtime.installation_safety ?? null,
      runtime_status: runtime.runtime_status,
      discount_status: runtime.discount_status,
      version: runtime.desktop_version ?? null,
      appserver_protocol: runtime.manifest?.appserver_protocol ?? null,
      request_security_capability: runtime.manifest?.request_security_capability ?? null,
      manifest: runtime.manifest,
      assets: runtime.assets
    },
    billing_reader: billing,
    credential_readability: credentials,
    resource_isolation: {
      status: "PASS",
      server_binding: "127.0.0.1_ONLY",
      evidence_root: ".run/cost-lab-web",
      model_requests_on_page_load: 0
    },
    provider: {
      id: "account:bigmodel-individual-coding-plan",
      model: "GLM-5.3-Flash",
      plan: "PERSONAL_CODING_PLAN"
    },
    appserver_protocol_smoke: protocolSmoke,
    start_plan: {
      status: "START_PLAN_OFFLINE_RESEARCH",
      live_test: "UNAVAILABLE",
      offline_compatibility: "AVAILABLE",
      discount: "NOT_VERIFIED"
    },
    warnings: buildWarnings({ nodeOk, platform, arch, runtime, billing, credentials })
  };
}
async function inspectBillingAvailability(options = {}) {
  try {
    const integrity = await (options.verifyBillingVendor ?? verifyOfficialVendor)();
    return {
      status: "PASS",
      accessor: "usageStatsService.getCodingPlanUsageSnapshot",
      runtime_sha256: integrity.runtime_sha256,
      native_keyring_sha256: integrity.keyring_native_sha256
    };
  } catch (error2) {
    return {
      status: "BLOCKED",
      accessor: "usageStatsService.getCodingPlanUsageSnapshot",
      error: safeErrorCode(error2)
    };
  }
}
async function inspectCredentialAvailability(data, options) {
  const credentialFile = path14.join(data.dataBaseDir, ".zcode", "v2", "credentials.json");
  try {
    const metadata = await (options.statFile ?? stat2)(credentialFile);
    return {
      status: "AVAILABLE",
      source: data.dataBaseDirSource,
      readable: await (options.accessFile ?? access2)(credentialFile).then(() => true, () => false),
      file_present: metadata.isFile(),
      content_read: false,
      absolute_path_returned: false
    };
  } catch (error2) {
    return {
      status: errorCode(error2) === "ENOENT" ? "NOT_FOUND" : "UNAVAILABLE",
      source: data.dataBaseDirSource,
      readable: false,
      file_present: false,
      content_read: false,
      absolute_path_returned: false
    };
  }
}
async function runBoundedProtocolSmoke(run2, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new Error("protocol_smoke_timeout")), timeoutMs);
  try {
    const result = await run2({ signal: controller.signal, timeoutMs, modelRequests: 0 });
    if (result?.status === "PASS") controller.signal.throwIfAborted();
    return {
      status: result?.status === "PASS" ? "PASS" : "FAIL",
      ...result?.reason ? { reason: safeErrorCode(result.reason) } : {},
      duration_ms: result?.duration_ms ?? null,
      model_requests: 0,
      evidence: redactValue(result?.evidence ?? null)
    };
  } catch (error2) {
    return {
      status: "FAIL",
      reason: safeErrorCode(error2),
      model_requests: 0
    };
  } finally {
    clearTimeout(timer);
  }
}
function buildWarnings({ nodeOk, platform, arch, runtime, billing, credentials }) {
  const warnings = [];
  if (platform !== "win32" || arch !== "x64") warnings.push("PLATFORM_UNSUPPORTED");
  if (!nodeOk) warnings.push("NODE_RUNTIME_INCOMPATIBLE");
  if (runtime.runtime_status === "OFFICIAL_RUNTIME_EXPERIMENTAL") {
    warnings.push("OFFICIAL_RUNTIME_EXPERIMENTAL");
  } else if (runtime.runtime_status !== "OFFICIAL_RUNTIME_VERIFIED") {
    warnings.push("OFFICIAL_RUNTIME_UNVERIFIED");
  }
  if (billing.status !== "PASS") warnings.push("BILLING_READER_UNAVAILABLE");
  if (credentials.status !== "AVAILABLE") warnings.push("CREDENTIAL_SOURCE_UNAVAILABLE");
  return warnings;
}
function redactValue(value, key = "") {
  if (isSecretKey(key)) return "<redacted>";
  if (Array.isArray(value)) return value.map((item) => redactValue(item));
  if (typeof value === "string") return redactAbsolutePaths(value);
  if (!value || typeof value !== "object") return value;
  const output = {};
  for (const [childKey, child] of Object.entries(value)) {
    output[childKey] = redactValue(child, childKey);
  }
  return output;
}
function redactAbsolutePaths(value) {
  return value.replace(/\b[A-Za-z]:[\\/][^\r\n\t"'<>|]*/gu, "<redacted-path>").replace(/\\\\[^\\/\s]+[\\/][^\r\n\t"'<>|]*/gu, "<redacted-path>").replace(/\/(?:Users|home|tmp|var|opt|private)\/[^\s"'<>|]*/gu, "<redacted-path>");
}
function isSecretKey(key) {
  const normalized = key.replaceAll("-", "_").toLowerCase();
  if (/^(api_key_id|organization_id|project_id|request_id|session_id)$/u.test(normalized)) return false;
  if (/(status|readability|present|read|returned|source|capability)$/u.test(normalized)) return false;
  if (/^(authorization|cookie|password|secret|credential|credentials|jwt|bearer)$/u.test(normalized)) return true;
  return /(access_token|refresh_token|project_token|api_key|client_secret|private_key|authorization_header|cookie_header)$/u.test(normalized);
}
function safeErrorCode(error2) {
  const message = error2 instanceof Error ? error2.message : String(error2);
  return message.replace(/\b(authorization|api[_-]?key|access[_-]?token|project[_-]?token)\b\s*[:=]\s*(?:Bearer\s+)?[^\s,;]+/giu, "$1=<redacted>").replace(/\bBearer\s+[^\s,;]+/giu, "Bearer <redacted>").slice(0, 300);
}
function errorCode(error2) {
  const code = error2 && typeof error2 === "object" && "code" in error2 ? error2.code : null;
  return typeof code === "string" ? code : "unavailable";
}

// tools/cost-lab/official-app-server-protocol-smoke.mjs
import { randomUUID as randomUUID3 } from "node:crypto";
import { access as access3, mkdir, rm, stat as stat3 } from "node:fs/promises";
import path15 from "node:path";
import { fileURLToPath as fileURLToPath5, pathToFileURL as pathToFileURL3 } from "node:url";
var SCRIPT_ROOT2 = path15.dirname(fileURLToPath5(import.meta.url));
var PROJECT_ROOT2 = path15.resolve(SCRIPT_ROOT2, "..", "..");
var OFFICIAL_PROTOCOL_SMOKE_METHOD = "runtime/capabilities";
var DEFAULT_TIMEOUT_MS = 3e4;
var RUNTIME_HOST_TRANSPORT_MAX_FRAME_BYTES = 16 * 1024 * 1024;
var FIXED_HOST_MODULE_RELATIVE_PATH = path15.join(
  "plugins",
  "codex-zcode-bridge",
  "worker",
  "vendor",
  "official-host",
  "win32-x64-node24.16.0-zcode3.18.2-fec97590",
  "official-host-runtime.mjs"
);
var runtimeHostEnvironmentTail = Promise.resolve();
async function runOfficialAppServerProtocolSmoke(options = {}) {
  const startedAt = Date.now();
  const projectRoot = path15.resolve(options.projectRoot ?? PROJECT_ROOT2);
  const platform = options.platform ?? process.platform;
  const arch = options.arch ?? process.arch;
  if (platform !== "win32" || arch !== "x64") {
    return failed("unsupported_platform", startedAt);
  }
  const env = options.env ?? process.env;
  const inspectRuntime = options.inspectRuntime ?? inspectOfficialRuntimeAssets;
  const resolveDataRoot = options.resolveDataRoot ?? resolveBillingDataBaseDir;
  const createId = options.createId ?? randomUUID3;
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1e3 || timeoutMs > 12e4) {
    return failed("timeout_invalid", startedAt);
  }
  const runtime = await inspectRuntime({ env, platform, arch });
  if (runtime.installation_safety !== "OFFICIAL_INSTALLATION_SAFE" || !runtime.install_root) {
    return failed("installed_official_runtime_unsafe_or_incomplete", startedAt);
  }
  if (!runtime.desktop_app_version || !runtime.assets?.bundle?.relative_path || !runtime.assets?.runtime_host?.relative_path || !runtime.assets?.builtin_provider_config?.relative_path) {
    return failed("runtime_launch_assets_incomplete", startedAt);
  }
  const account = resolveDataRoot(null, {
    env,
    platform,
    fallbackHomeDir: options.fallbackHomeDir
  });
  const zcodeHome = path15.join(account.dataBaseDir, ".zcode");
  const personalProviderConfig = path15.join(zcodeHome, "v2", "provider_config.json");
  try {
    await access3(personalProviderConfig);
    await stat3(personalProviderConfig);
  } catch {
    return failed("personal_provider_config_unavailable", startedAt);
  }
  const runRootParent = path15.resolve(options.runRootParent ?? path15.join(projectRoot, ".run"));
  const runRoot = path15.join(runRootParent, "cost-lab-web", `protocol-smoke-${createId()}`);
  assertInside(runRootParent, runRoot);
  const layout = {
    root: runRoot,
    home: path15.join(runRoot, "home"),
    appData: path15.join(runRoot, "app-data"),
    localAppData: path15.join(runRoot, "local-app-data"),
    temp: path15.join(runRoot, "temp"),
    workspace: path15.join(runRoot, "workspace")
  };
  let manager = null;
  let workspace = null;
  let capabilities = null;
  let disposeError = null;
  try {
    options.signal?.throwIfAborted();
    for (const directory of Object.values(layout).slice(1)) {
      await mkdir(directory, { recursive: true });
    }
    const hostModulePath = path15.resolve(
      options.hostModulePath ?? path15.join(projectRoot, FIXED_HOST_MODULE_RELATIVE_PATH)
    );
    if (!options.loadHostModule) await stat3(hostModulePath);
    const module = await (options.loadHostModule ? options.loadHostModule(hostModulePath) : import(pathToFileURL3(hostModulePath).href));
    if (typeof module.ZCodeAgentProcessManager !== "function") {
      return failed("official_host_manager_missing", startedAt);
    }
    const bundlePath = path15.join(runtime.install_root, runtime.assets.bundle.relative_path);
    const runtimeHostPath = path15.join(runtime.install_root, runtime.assets.runtime_host.relative_path);
    const builtinProviderConfig = path15.join(
      runtime.install_root,
      runtime.assets.builtin_provider_config.relative_path
    );
    const childEnv = buildSmokeEnvironment(layout, env, {
      version: runtime.desktop_app_version,
      buildCommitId: runtime.desktop_build_commit_id,
      builtinProviderConfig,
      personalProviderConfig,
      runtimeHostPath,
      zcodeHome,
      dataBaseDir: account.dataBaseDir
    });
    const managerOptions = {
      useSharedTaskRuntime: () => false,
      maxFrameBytes: RUNTIME_HOST_TRANSPORT_MAX_FRAME_BYTES,
      requestTimeoutMs: timeoutMs,
      processLifecycleReporter: {
        onSpawn: () => void 0,
        onExit: () => void 0,
        onError: () => void 0,
        onException: () => void 0
      },
      commandResolver: async ({ workspacePath }) => ({
        command: runtime.node_executable ?? process.execPath,
        args: [bundlePath, "app-server", "--stdio", "--surface", "desktop"],
        cwd: workspacePath,
        env: childEnv
      })
    };
    manager = options.createManager ? options.createManager(module, managerOptions) : new module.ZCodeAgentProcessManager(managerOptions);
    workspace = {
      workspacePath: layout.workspace,
      workspaceIdentity: layout.workspace
    };
    const client = await withRuntimeHostEnvironment(
      runtimeHostPath,
      () => {
        options.signal?.throwIfAborted();
        return manager.getClient(workspace);
      }
    );
    options.signal?.throwIfAborted();
    const runtimeIdentity = await manager.getRuntimeIdentity(workspace);
    options.signal?.throwIfAborted();
    capabilities = await client.request(
      OFFICIAL_PROTOCOL_SMOKE_METHOD,
      {},
      void 0,
      { signal: options.signal, timeoutMs, invalidateConnectionOnTimeout: false }
    );
    options.signal?.throwIfAborted();
    if (!runtimeIdentity || !Number.isSafeInteger(runtimeIdentity.processId) || runtimeIdentity.processId < 1) {
      return failed("official_process_identity_missing", startedAt, {
        protocol_initialized: true,
        model_requests: 0
      });
    }
    return {
      status: "PASS",
      duration_ms: Date.now() - startedAt,
      evidence: {
        protocol_initialized: true,
        protocol_method: OFFICIAL_PROTOCOL_SMOKE_METHOD,
        capabilities_received: capabilities !== null && typeof capabilities === "object",
        process_started: true,
        session_created: false,
        model_requests: 0,
        runtime_status: runtime.runtime_status,
        installation_fingerprint: runtime.installation_fingerprint,
        installation_safety: runtime.installation_safety,
        desktop_version: runtime.desktop_version,
        bundle_sha256: runtime.assets.bundle.sha256
      }
    };
  } catch (error2) {
    return failed(safeErrorCode2(error2), startedAt, {
      protocol_initialized: capabilities !== null,
      model_requests: 0
    });
  } finally {
    if (manager && workspace) {
      try {
        await manager.disposeWorkspace(workspace);
      } catch (error2) {
        disposeError = error2;
      }
    }
    if (manager) {
      try {
        await manager.disposeAllAndWait();
      } catch (error2) {
        disposeError ??= error2;
      }
    }
    let managedProcessesAfter = null;
    try {
      managedProcessesAfter = manager?.listManagedProcesses?.().length ?? null;
    } catch {
      managedProcessesAfter = null;
    }
    if (!disposeError && (managedProcessesAfter ?? 0) === 0) {
      await rm(runRoot, { recursive: true, force: true }).catch((error2) => {
        disposeError = error2;
      });
    }
    if (disposeError || (managedProcessesAfter ?? 0) > 0) {
      return failed(
        disposeError ? "official_protocol_smoke_cleanup_failed" : "official_protocol_smoke_process_leak",
        startedAt,
        { protocol_initialized: capabilities !== null, model_requests: 0, managed_processes_after: managedProcessesAfter }
      );
    }
  }
}
function buildSmokeEnvironment(layout, source, official) {
  const homeDrive = path15.parse(layout.home).root.replace(/[\\/]+$/u, "");
  const homePath = layout.home.slice(path15.parse(layout.home).root.length - 1);
  const retained = {};
  for (const key of [
    "PATH",
    "SystemRoot",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
    "OS",
    "PROCESSOR_ARCHITECTURE",
    "NUMBER_OF_PROCESSORS",
    "PROGRAMDATA",
    "ProgramFiles",
    "ProgramFiles(x86)"
  ]) {
    if (source[key] !== void 0) retained[key] = source[key];
  }
  return {
    ...retained,
    HOME: layout.home,
    USERPROFILE: layout.home,
    HOMEDRIVE: homeDrive,
    HOMEPATH: homePath,
    APPDATA: layout.appData,
    LOCALAPPDATA: layout.localAppData,
    TEMP: layout.temp,
    TMP: layout.temp,
    TMPDIR: layout.temp,
    ZCODE_APP_VERSION: official.version,
    ZCODE_BUILD_COMMIT_ID: official.buildCommitId,
    ZCODE_BUILTIN_PROVIDER_CONFIG_FILE: official.builtinProviderConfig,
    ZCODE_PERSONAL_PROVIDER_CONFIG_FILE: official.personalProviderConfig,
    ZCODE_RUNTIME_HOST_PATH: official.runtimeHostPath,
    ZCODE_HOME: official.zcodeHome,
    ZCODE_DATA_BASE_DIR: official.dataBaseDir
  };
}
async function withRuntimeHostEnvironment(runtimeHostPath, action) {
  const previous = runtimeHostEnvironmentTail;
  let release;
  runtimeHostEnvironmentTail = new Promise((resolve) => {
    release = resolve;
  });
  await previous;
  const priorValue = process.env.ZCODE_RUNTIME_HOST_PATH;
  process.env.ZCODE_RUNTIME_HOST_PATH = runtimeHostPath;
  try {
    return await action();
  } finally {
    if (priorValue === void 0) delete process.env.ZCODE_RUNTIME_HOST_PATH;
    else process.env.ZCODE_RUNTIME_HOST_PATH = priorValue;
    release();
  }
}
function failed(reason, startedAt, evidence = {}) {
  return {
    status: "FAIL",
    duration_ms: Date.now() - startedAt,
    reason,
    evidence: {
      protocol_initialized: false,
      session_created: false,
      model_requests: 0,
      ...evidence
    }
  };
}
function safeErrorCode2(error2) {
  const code = error2 && typeof error2 === "object" && "code" in error2 ? error2.code : error2 instanceof Error ? error2.message : String(error2);
  return String(code).replace(/\b(authorization|api[_-]?key|access[_-]?token|project[_-]?token)\b\s*[:=]\s*(?:Bearer\s+)?[^\s,;]+/giu, "$1=<redacted>").replace(/\bBearer\s+[^\s,;]+/giu, "Bearer <redacted>").replace(/\b[A-Za-z]:[\\/][^\r\n\t"'<>|]*/gu, "<redacted-path>").replace(/\\\\[^\\/\s]+[\\/][^\r\n\t"'<>|]*/gu, "<redacted-path>").slice(0, 200);
}
function assertInside(root, candidate) {
  const relative = path15.relative(path15.resolve(root), path15.resolve(candidate));
  if (relative === "" || relative === ".." || relative.startsWith(`..${path15.sep}`) || path15.isAbsolute(relative)) {
    throw new Error("protocol_smoke_path_outside_run_root");
  }
}

// tools/cost-lab/startplan-reader.mjs
import { lstat as lstat3 } from "node:fs/promises";
import path16 from "node:path";
import { pathToFileURL as pathToFileURL4 } from "node:url";

// tools/cost-lab/startplan-billing.mjs
import { createHash as createHash8 } from "node:crypto";
var START_PLAN_PROVIDER_ID = "account:bigmodel-start-plan";
var START_PLAN_BILLING_ORIGIN = "https://zcode.z.ai";
var START_PLAN_BILLING_PATH = "/api/v1/zcode-plan/billing/balance";
var STARTPLAN_HISTORY_SCHEMA_VERSION = 1;
var FRESHNESS_WINDOW_MS = 5 * 60 * 1e3;
var SENSITIVE_KEY = /(authorization|cookie|credential|device.?mid|jwt|password|refresh.?token|secret|api.?key|access.?token)/iu;
var OPAQUE_KEY = /(account.?id|bucket.?id|customer.?id|entitlement.?id|request.?id|log.?id|user.?id|user.?plan.?id)/iu;
function record2(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : null;
}
function boundedText(value, maximum = 256) {
  return typeof value === "string" ? value.slice(0, maximum) : null;
}
function finiteInteger(value) {
  if (typeof value === "string" && value.trim() !== "") value = Number(value);
  return typeof value === "number" && Number.isFinite(value) ? Math.trunc(value) : null;
}
function timestampToIso(value) {
  if (value === null || value === void 0 || value === "") return null;
  let milliseconds;
  if (typeof value === "number") {
    milliseconds = value < 1e10 ? value * 1e3 : value;
  } else if (typeof value === "string" && /^\d+(?:\.\d+)?$/u.test(value.trim())) {
    const numeric = Number(value);
    milliseconds = numeric < 1e10 ? numeric * 1e3 : numeric;
  } else {
    milliseconds = Date.parse(String(value));
  }
  if (!Number.isFinite(milliseconds)) return null;
  const date2 = new Date(milliseconds);
  return Number.isNaN(date2.getTime()) ? null : date2.toISOString();
}
function stableStringify(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(",")}]`;
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(",")}}`;
}
function shortHash(value) {
  return createHash8("sha256").update(String(value)).digest("hex").slice(0, 16);
}
function hashStartPlanOpaque(prefix, value) {
  if (value === null || value === void 0 || value === "") return null;
  const normalized = String(value);
  if (/^sha256:[a-f0-9]{16}$/u.test(normalized)) return normalized;
  return `sha256:${shortHash(`${prefix}:${normalized}`)}`;
}
function looksSecret(value) {
  return /^(?:bearer\s+|basic\s+)?[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}$/iu.test(value) || /\b(?:bearer|basic)\s+[A-Za-z0-9._~+/=-]{16,}\b/iu.test(value) || /\bsk-[A-Za-z0-9_-]{16,}\b/u.test(value);
}
function opaquePrefix(key) {
  const normalized = key.replace(/([a-z])([A-Z])/gu, "$1_$2").toLowerCase();
  if (normalized.includes("user_plan")) return "startplan-user-plan";
  if (normalized.includes("bucket")) return "startplan-bucket";
  if (normalized.includes("entitlement")) return "startplan-entitlement";
  if (normalized.includes("request") || normalized.includes("logid") || normalized.includes("log_id")) {
    return "official-request";
  }
  if (normalized.includes("account") || normalized.includes("customer") || normalized.includes("user")) {
    return "official-account";
  }
  return "official-opaque";
}
function sanitizeValue(value, depth = 0) {
  if (depth > 20 || value === void 0) return "[UNKNOWN]";
  if (value === null || typeof value === "number" || typeof value === "boolean") return value;
  if (typeof value === "string") return looksSecret(value) ? "[REDACTED]" : value.slice(0, 2048);
  if (Array.isArray(value)) return value.slice(0, 2e3).map((item) => sanitizeValue(item, depth + 1));
  const input = record2(value);
  if (!input) return "[UNKNOWN]";
  const output = {};
  for (const [key, item] of Object.entries(input).slice(0, 1e3)) {
    if (SENSITIVE_KEY.test(key)) {
      output[key] = "[REDACTED]";
    } else if (OPAQUE_KEY.test(key) && (typeof item === "string" || typeof item === "number")) {
      output[key] = hashStartPlanOpaque(opaquePrefix(key), item);
    } else {
      output[key] = sanitizeValue(item, depth + 1);
    }
  }
  return output;
}
function sanitizeOfficialStartPlanPayload(raw) {
  return sanitizeValue(raw);
}
function extractBillingData(raw) {
  const root = record2(raw);
  if (!root) return null;
  if (record2(root.data) && (Array.isArray(root.data.plans) || Array.isArray(root.data.balances))) {
    return root.data;
  }
  const payload = record2(root.payload);
  if (record2(payload?.data) && (Array.isArray(payload.data.plans) || Array.isArray(payload.data.balances))) {
    return payload.data;
  }
  if (Array.isArray(root.plans) || Array.isArray(root.balances)) return root;
  return null;
}
function safeCapabilities(value) {
  return Array.isArray(value) ? value.filter((item) => typeof item === "string").map((item) => boundedText(item, 128)).filter(Boolean).sort() : [];
}
function modelIdsFromCapabilities(capabilities, showName) {
  const models = capabilities.map((capability2) => capability2.toLowerCase().startsWith("model:") ? capability2.slice("model:".length).trim() : "").filter(Boolean);
  return [...new Set(models.length > 0 ? models : showName ? [showName.toLowerCase()] : [])].sort();
}
function uniqueNullable(values) {
  if (values.length === 0 || values.some((value) => value === null || value === void 0)) return null;
  return new Set(values.map(stableStringify)).size === 1 ? values[0] : null;
}
function summedInteger(buckets, key) {
  const values = buckets.map((bucket) => bucket[key]);
  if (values.length === 0 || values.some((value) => !Number.isSafeInteger(value) || value < 0)) return null;
  const total = values.reduce((sum, value) => sum + value, 0);
  return Number.isSafeInteger(total) ? total : null;
}
function buildSummary(snapshot) {
  const { buckets, plans } = snapshot;
  const units = [...new Set(buckets.map((bucket) => bucket.unit_type).filter(Boolean))];
  const planIds = [...new Set(buckets.map((bucket) => bucket.plan_id).filter(Boolean))];
  const planNames = [...new Set(plans.map((plan) => plan.name).filter(Boolean))];
  const planStatuses = [...new Set(plans.map((plan) => plan.status).filter(Boolean))];
  const periods = uniqueNullable(buckets.map((bucket) => bucket.period_start && bucket.period_end ? { start: bucket.period_start, end: bucket.period_end } : null));
  const expiry = uniqueNullable(buckets.map((bucket) => bucket.expires_at));
  const aggregateUnits = units.length === 1 ? units[0] : null;
  const summary = {
    plan_id: planIds.length === 1 ? planIds[0] : null,
    plan_type: planNames.length === 1 ? planNames[0] : null,
    plan_status: planStatuses.length === 1 ? planStatuses[0] : null,
    unit_type: aggregateUnits,
    total_balance: aggregateUnits ? summedInteger(buckets, "total_units") : null,
    used_balance: aggregateUnits ? summedInteger(buckets, "used_units") : null,
    remaining_balance: aggregateUnits ? summedInteger(buckets, "remaining_units") : null,
    billing_period: aggregateUnits ? periods : null,
    expiry: aggregateUnits ? expiry : null
  };
  const missing = Object.entries(summary).filter(([, value]) => value === null).map(([key]) => key);
  if (buckets.length > 1) missing.push("single_bucket");
  if (units.length > 1) missing.push("unambiguous_unit_type");
  return { ...summary, missing_fields: [...new Set(missing)] };
}
function normalizedIntegrity(raw, first, second) {
  const rawData = extractBillingData(raw);
  const rawBuckets = Array.isArray(rawData?.balances) ? rawData.balances : [];
  const rawPlans = Array.isArray(rawData?.plans) ? rawData.plans : [];
  const mismatches = [];
  if (rawBuckets.length !== first.buckets.length || first.buckets.length !== second.buckets.length) {
    mismatches.push("bucket_count");
  }
  if (rawPlans.length !== first.plans.length || first.plans.length !== second.plans.length) {
    mismatches.push("plan_count");
  }
  for (let index = 0; index < Math.min(rawBuckets.length, first.buckets.length, second.buckets.length); index += 1) {
    for (const key of [
      "bucket_key",
      "user_plan_key",
      "entitlement_key",
      "total_units",
      "used_units",
      "remaining_units",
      "available_units"
    ]) {
      if (first.buckets[index][key] !== second.buckets[index][key]) {
        mismatches.push(`bucket_${index}_${key}`);
      }
    }
  }
  return {
    status: mismatches.length === 0 ? "PASS" : "FAIL",
    checks: {
      response_shape_recognized: Boolean(rawData),
      raw_bucket_count: rawBuckets.length,
      normalized_bucket_count: first.buckets.length,
      reparsed_bucket_count: second.buckets.length,
      raw_plan_count: rawPlans.length,
      normalized_plan_count: first.plans.length,
      reparsed_plan_count: second.plans.length,
      numeric_fields_match_reparse: mismatches.length === 0
    },
    mismatches
  };
}
function normalizeEntitlement(value) {
  const input = record2(value);
  if (!input) return null;
  return {
    status: boundedText(input.status, 64),
    reason: boundedText(input.reason, 200),
    provider_code: boundedText(input.providerCode, 64),
    observed_at: timestampToIso(input.observedAt),
    request_id_hash: typeof input.requestId === "string" && input.requestId ? hashStartPlanOpaque("official-request", input.requestId) : null,
    failure_facts: record2(input.failureFacts) ?? null
  };
}
function parseStartPlanSnapshot(raw, options = {}) {
  const data = extractBillingData(raw);
  if (!data) throw new Error("start_plan_balance_data_required");
  const serverTime = timestampToIso(data.server_time ?? data.serverTime);
  const capturedAt = timestampToIso(options.capturedAt ?? raw?.captured_at ?? raw?.capturedAt) ?? serverTime;
  const plans = (Array.isArray(data.plans) ? data.plans : []).map((value) => {
    const plan = record2(value);
    if (!plan) return null;
    return {
      plan_id: boundedText(plan.plan_id ?? plan.planId, 128),
      user_plan_key: hashStartPlanOpaque(
        "startplan-user-plan",
        plan.user_plan_id ?? plan.userPlanId
      ),
      name: boundedText(plan.name, 128),
      status: boundedText(plan.status, 64),
      starts_at: timestampToIso(plan.starts_at ?? plan.startsAt),
      ends_at: timestampToIso(plan.ends_at ?? plan.endsAt),
      entitlements: (Array.isArray(plan.entitlements) ? plan.entitlements : []).map((entryValue) => {
        const entry = record2(entryValue);
        if (!entry) return null;
        return {
          entitlement_key: hashStartPlanOpaque(
            "startplan-entitlement",
            entry.entitlement_id ?? entry.entitlementId
          ),
          show_name: boundedText(entry.show_name ?? entry.showName, 128),
          meter: boundedText(entry.meter, 64),
          unit_type: boundedText(entry.unit_type ?? entry.unitType, 64),
          period: boundedText(entry.period, 64),
          grant_units: finiteInteger(entry.grant_units ?? entry.grantUnits),
          effective_at: timestampToIso(entry.effective_at ?? entry.effectiveAt)
        };
      }).filter(Boolean)
    };
  }).filter(Boolean);
  const buckets = (Array.isArray(data.balances) ? data.balances : []).map((value) => {
    const bucket = record2(value);
    if (!bucket) return null;
    const capabilities = safeCapabilities(bucket.capabilities);
    const showName = boundedText(bucket.show_name ?? bucket.showName, 128);
    return {
      bucket_key: hashStartPlanOpaque("startplan-bucket", bucket.bucket_id ?? bucket.bucketId),
      user_plan_key: hashStartPlanOpaque(
        "startplan-user-plan",
        bucket.user_plan_id ?? bucket.userPlanId
      ),
      plan_id: boundedText(bucket.plan_id ?? bucket.planId, 128),
      entitlement_key: hashStartPlanOpaque(
        "startplan-entitlement",
        bucket.entitlement_id ?? bucket.entitlementId
      ),
      show_name: showName,
      model_ids: modelIdsFromCapabilities(capabilities, showName),
      meter: boundedText(bucket.meter, 64),
      unit_type: boundedText(bucket.unit_type ?? bucket.unitType, 64),
      capabilities,
      total_units: finiteInteger(bucket.total_units ?? bucket.totalUnits),
      used_units: finiteInteger(bucket.used_units ?? bucket.usedUnits),
      reserved_units: finiteInteger(bucket.reserved_units ?? bucket.reservedUnits),
      remaining_units: finiteInteger(bucket.remaining_units ?? bucket.remainingUnits),
      available_units: finiteInteger(bucket.available_units ?? bucket.availableUnits),
      period_start: timestampToIso(bucket.period_start ?? bucket.periodStart),
      period_end: timestampToIso(bucket.period_end ?? bucket.periodEnd),
      expires_at: timestampToIso(bucket.expires_at ?? bucket.expiresAt),
      plan_priority: finiteInteger(bucket.plan_priority ?? bucket.planPriority),
      entitlement_priority: finiteInteger(
        bucket.entitlement_priority ?? bucket.entitlementPriority
      )
    };
  }).filter(Boolean);
  return {
    schema_version: 1,
    kind: "start_plan_billing_snapshot",
    source: boundedText(options.source, 128) ?? "official_billing_balance",
    captured_at: capturedAt,
    server_time: serverTime,
    provider_scope: START_PLAN_PROVIDER_ID,
    plans,
    buckets,
    available_models: [...new Set(buckets.flatMap((bucket) => bucket.model_ids))].sort(),
    precision: {
      unit: "token_units",
      request_level_deductions: false,
      note: "Start Plan balance is token units and is not a Coding Plan credit ledger."
    }
  };
}
function normalizeStartPlanSnapshot(raw, options = {}) {
  const first = parseStartPlanSnapshot(raw, options);
  const sanitized = sanitizeOfficialStartPlanPayload(raw);
  const second = parseStartPlanSnapshot(sanitized, {
    capturedAt: first.captured_at,
    source: "sanitized_reparse"
  });
  const summary = buildSummary(first);
  const integrity = normalizedIntegrity(raw, first, second);
  return {
    ...first,
    account: {
      key: options.accountIdentity ? hashStartPlanOpaque("official-account", options.accountIdentity) : null,
      provider_scope: START_PLAN_PROVIDER_ID,
      scope: "personal"
    },
    ...summary,
    official_entitlement: normalizeEntitlement(options.officialEntitlement),
    integrity: {
      ...integrity,
      raw_sanitized_reparse_match: integrity.status === "PASS",
      http_status: finiteInteger(options.requestMetadata?.http_status),
      response_bytes: finiteInteger(options.requestMetadata?.response_bytes)
    },
    request: options.requestMetadata ?? null,
    process: {
      model_requests_triggered: 0
    }
  };
}
function annotateStartPlanFreshness(snapshot, now = Date.now()) {
  if (!record2(snapshot)) {
    return {
      status: "UNKNOWN",
      reason: "snapshot_unavailable",
      evaluated_at_ms: now
    };
  }
  const capturedMs = Date.parse(snapshot.captured_at ?? "");
  const serverMs = Date.parse(snapshot.server_time ?? "");
  const referenceMs = Number.isFinite(serverMs) ? serverMs : capturedMs;
  const expiryMs = Math.min(
    ...[snapshot.expiry, snapshot.billing_period?.end, snapshot.period_end].map((value) => Date.parse(value ?? "")).filter(Number.isFinite)
  );
  const ageMs = Number.isFinite(referenceMs) ? now - referenceMs : null;
  let status = "UNKNOWN";
  let reason = "capture_time_unavailable";
  if (Number.isFinite(expiryMs) && expiryMs <= now) {
    status = "EXPIRED";
    reason = "official_period_ended";
  } else if (ageMs !== null && ageMs < -FRESHNESS_WINDOW_MS) {
    status = "UNKNOWN";
    reason = "server_time_in_future";
  } else if (ageMs !== null) {
    status = Math.abs(ageMs) <= FRESHNESS_WINDOW_MS ? "FRESH" : "STALE";
    reason = status === "FRESH" ? "recent_official_capture" : "capture_older_than_window";
  }
  return {
    status,
    reason,
    evaluated_at: new Date(now).toISOString(),
    captured_at: snapshot.captured_at ?? null,
    server_time: snapshot.server_time ?? null,
    age_ms: ageMs,
    expiry: Number.isFinite(expiryMs) ? new Date(expiryMs).toISOString() : null,
    maximum_fresh_age_ms: FRESHNESS_WINDOW_MS
  };
}
function bucketIdentity(bucket) {
  return [
    bucket.bucket_key,
    bucket.entitlement_key,
    bucket.plan_id,
    bucket.unit_type
  ].map((value) => value ?? "null").join("|");
}
function delta(current, previous) {
  return Number.isSafeInteger(current) && Number.isSafeInteger(previous) ? current - previous : null;
}
function compareStartPlanSnapshots(previous, current) {
  if (!previous || !current) {
    return {
      status: previous === current ? "NO_BASELINE" : "PARTIAL",
      reason: "two_snapshots_required",
      buckets: [],
      aggregate: null
    };
  }
  if (previous.account?.key !== current.account?.key) {
    return {
      status: "NOT_COMPARABLE",
      reason: "account_changed",
      buckets: [],
      aggregate: null
    };
  }
  const previousBuckets = Array.isArray(previous.buckets) ? previous.buckets : [];
  const currentBuckets = Array.isArray(current.buckets) ? current.buckets : [];
  const comparisons = currentBuckets.map((bucket) => {
    const sameLogicalBucket = previousBuckets.filter((candidate) => candidate.bucket_key === bucket.bucket_key && candidate.entitlement_key === bucket.entitlement_key && candidate.plan_id === bucket.plan_id);
    const exact = sameLogicalBucket.find((candidate) => candidate.unit_type === bucket.unit_type && candidate.period_start === bucket.period_start && candidate.period_end === bucket.period_end);
    if (exact) {
      return {
        bucket_key: bucket.bucket_key,
        entitlement_key: bucket.entitlement_key,
        unit_type: bucket.unit_type,
        period_start: bucket.period_start,
        period_end: bucket.period_end,
        status: "COMPARABLE",
        used_delta: delta(bucket.used_units, exact.used_units),
        remaining_delta: delta(bucket.remaining_units, exact.remaining_units),
        total_delta: delta(bucket.total_units, exact.total_units)
      };
    }
    if (sameLogicalBucket.some((candidate) => candidate.unit_type !== bucket.unit_type)) {
      return {
        bucket_key: bucket.bucket_key,
        entitlement_key: bucket.entitlement_key,
        unit_type: bucket.unit_type,
        status: "UNIT_CHANGED",
        used_delta: null,
        remaining_delta: null,
        total_delta: null
      };
    }
    if (sameLogicalBucket.length > 0) {
      return {
        bucket_key: bucket.bucket_key,
        entitlement_key: bucket.entitlement_key,
        unit_type: bucket.unit_type,
        period_start: bucket.period_start,
        period_end: bucket.period_end,
        status: bucket.period_start && bucket.period_start === current.period_start ? "NEW_BUCKET" : "ROLLED_OVER",
        used_delta: null,
        remaining_delta: null,
        total_delta: null
      };
    }
    return {
      bucket_key: bucket.bucket_key,
      entitlement_key: bucket.entitlement_key,
      unit_type: bucket.unit_type,
      period_start: bucket.period_start,
      period_end: bucket.period_end,
      status: "NEW_BUCKET",
      used_delta: null,
      remaining_delta: null,
      total_delta: null
    };
  });
  const currentIdentities = new Set(currentBuckets.map(bucketIdentity));
  const removed = previousBuckets.filter((bucket) => !currentIdentities.has(bucketIdentity(bucket))).map((bucket) => ({
    bucket_key: bucket.bucket_key,
    entitlement_key: bucket.entitlement_key,
    unit_type: bucket.unit_type,
    status: "REMOVED_BUCKET",
    used_delta: null,
    remaining_delta: null,
    total_delta: null
  }));
  const units = [...new Set(currentBuckets.map((bucket) => bucket.unit_type).filter(Boolean))];
  const allComparable = comparisons.length > 0 && removed.length === 0 && comparisons.every((item) => item.status === "COMPARABLE") && units.length === 1;
  const aggregate = allComparable ? {
    unit_type: units[0],
    used_delta: comparisons.every((item) => item.used_delta !== null) ? comparisons.reduce((sum, item) => sum + item.used_delta, 0) : null,
    remaining_delta: comparisons.every((item) => item.remaining_delta !== null) ? comparisons.reduce((sum, item) => sum + item.remaining_delta, 0) : null,
    total_delta: comparisons.every((item) => item.total_delta !== null) ? comparisons.reduce((sum, item) => sum + item.total_delta, 0) : null
  } : null;
  const status = allComparable ? "COMPARABLE" : comparisons.some((item) => ["ROLLED_OVER", "NEW_PERIOD"].includes(item.status)) ? "NEW_PERIOD" : "PARTIAL";
  return {
    status,
    reason: allComparable ? "matching_account_bucket_entitlement_unit_and_period" : "non_comparable_bucket_scope",
    previous_captured_at: previous.captured_at ?? null,
    current_captured_at: current.captured_at ?? null,
    buckets: [...comparisons, ...removed],
    aggregate
  };
}

// tools/cost-lab/startplan-reader.mjs
var MAX_RESPONSE_BYTES = 4 * 1024 * 1024;
function readerError(code, message, options = {}) {
  const error2 = new Error(message);
  error2.code = code;
  if (options.cause) error2.cause = options.cause;
  return error2;
}
function isRecord5(value) {
  return value && typeof value === "object" && !Array.isArray(value);
}
async function fileMetadata(filePath) {
  try {
    const info = await lstat3(filePath);
    return {
      exists: true,
      type: info.isFile() ? "file" : info.isDirectory() ? "directory" : "other",
      symbolic_link: info.isSymbolicLink(),
      size: info.size,
      mtime_ms: info.mtimeMs,
      birthtime_ms: info.birthtimeMs,
      mode: info.mode
    };
  } catch (error2) {
    if (error2?.code === "ENOENT") return { exists: false };
    throw error2;
  }
}
function sameMetadata(left, right) {
  return JSON.stringify(left) === JSON.stringify(right);
}
function assertOfficialRequest(input, expectedAppVersion) {
  const isRequestObject = isRecord5(input) && Object.hasOwn(input, "url");
  const rawUrl = isRequestObject ? input.url : input;
  const rawMethod = isRequestObject ? input.init?.method : null;
  let url;
  try {
    url = new URL(String(rawUrl));
  } catch (error2) {
    throw readerError("startplan_billing_url_invalid", "Official billing URL is invalid.", {
      cause: error2
    });
  }
  if (url.origin !== START_PLAN_BILLING_ORIGIN) {
    throw readerError("startplan_billing_origin_invalid", "Official billing origin is invalid.");
  }
  if (url.pathname !== START_PLAN_BILLING_PATH) {
    throw readerError("startplan_billing_path_invalid", "Official billing path is invalid.");
  }
  if (String(rawMethod ?? "GET").toUpperCase() !== "GET") {
    throw readerError("startplan_billing_method_invalid", "Official billing method is invalid.");
  }
  const queryKeys = [...new Set(url.searchParams.keys())].sort();
  if (queryKeys.length !== 1 || queryKeys[0] !== "app_version") {
    throw readerError("startplan_billing_query_invalid", "Official billing query is invalid.");
  }
  if (url.searchParams.get("app_version") !== expectedAppVersion) {
    throw readerError("startplan_billing_version_mismatch", "Official billing version is invalid.");
  }
  return {
    method: "GET",
    origin: url.origin,
    path: url.pathname,
    query_keys: queryKeys,
    app_version: expectedAppVersion
  };
}
async function defaultOfficialDependencies(projectRoot) {
  const authFile = path16.join(projectRoot, "dist", "src", "runtime", "start-plan-production-auth.js");
  const adapterFile = path16.join(projectRoot, "dist", "src", "adapters", "official-host-adapter.js");
  let authModule;
  let adapterModule;
  try {
    authModule = await import(pathToFileURL4(authFile).href);
    adapterModule = await import(pathToFileURL4(adapterFile).href);
  } catch (error2) {
    if (error2?.code === "ERR_MODULE_NOT_FOUND" || error2?.code === "ENOENT") {
      throw readerError(
        "startplan_official_reader_build_missing",
        "Build the official Bridge sources before refreshing Start Plan billing.",
        { cause: error2 }
      );
    }
    throw error2;
  }
  if (typeof authModule.StartPlanBillingEntitlement !== "function") {
    throw readerError(
      "startplan_entitlement_missing",
      "The compiled official Start Plan entitlement reader is missing."
    );
  }
  if (typeof adapterModule.loadOfficialHostProductVersion !== "function" || typeof adapterModule.loadOfficialStartPlanAuthenticationResolverFactory !== "function") {
    throw readerError(
      "startplan_authentication_reader_missing",
      "The compiled official Start Plan authentication reader is missing."
    );
  }
  return {
    StartPlanBillingEntitlement: authModule.StartPlanBillingEntitlement,
    loadOfficialHostProductVersion: adapterModule.loadOfficialHostProductVersion,
    loadOfficialStartPlanAuthenticationResolverFactory: adapterModule.loadOfficialStartPlanAuthenticationResolverFactory
  };
}
async function readOfficialStartPlanBilling(options = {}) {
  if (!options.dataBaseDir) {
    throw readerError("startplan_data_base_dir_required", "The official ZCode data directory is required.");
  }
  if (!options.officialHostWorker) {
    throw readerError("startplan_official_host_worker_required", "The official Host Worker is required.");
  }
  const projectRoot = path16.resolve(options.projectRoot ?? process.cwd());
  const dataBaseDir = path16.resolve(options.dataBaseDir);
  const officialHostWorker = path16.resolve(options.officialHostWorker);
  const workerUrl = pathToFileURL4(officialHostWorker);
  const now = typeof options.now === "function" ? options.now : () => Date.now();
  const timeoutMs = options.timeoutMs ?? 2e4;
  const dependencies = options.officialDependencies ?? await defaultOfficialDependencies(projectRoot);
  const transportFetch = options.transportFetch ?? globalThis.fetch;
  const credentialFile = path16.join(dataBaseDir, ".zcode", "v2", "credentials.json");
  const keyringLockFile = `${credentialFile}.keyring.lock`;
  const operationController = new AbortController();
  const abortFromParent = () => operationController.abort(options.signal?.reason);
  if (options.signal?.aborted) abortFromParent();
  else options.signal?.addEventListener("abort", abortFromParent, { once: true });
  const timeout = setTimeout(() => {
    operationController.abort(readerError("startplan_billing_timeout", "Official billing refresh timed out."));
  }, timeoutMs);
  const credentialBefore = await fileMetadata(credentialFile);
  const lockBefore = await fileMetadata(keyringLockFile);
  if (lockBefore.exists) {
    clearTimeout(timeout);
    options.signal?.removeEventListener("abort", abortFromParent);
    throw readerError(
      "startplan_keyring_lock_present_before_capture",
      "The official keyring lock was already present before the read."
    );
  }
  let requestCount = 0;
  let captured = null;
  try {
    const productVersion = await dependencies.loadOfficialHostProductVersion(workerUrl);
    const resolverFactory = await dependencies.loadOfficialStartPlanAuthenticationResolverFactory(workerUrl);
    const resolver = resolverFactory({ dataBaseDir });
    const auth = await resolver.resolveStartPlanAuthentication({
      family: "bigmodel",
      signal: operationController.signal
    });
    operationController.signal.throwIfAborted();
    if (!auth?.requestCredential || !auth?.deviceMid || !auth?.accountIdentity) {
      throw readerError(
        "startplan_authentication_unavailable",
        "Official Start Plan authentication is unavailable."
      );
    }
    const fetchImpl = async (input, init) => {
      requestCount += 1;
      if (requestCount !== 1) {
        throw readerError(
          "startplan_multiple_billing_requests_forbidden",
          "More than one official billing request was attempted."
        );
      }
      const requestMetadata2 = assertOfficialRequest(input, productVersion);
      const headerNames = Object.keys(Object.fromEntries(new Headers(init?.headers))).sort();
      const started = performance.now();
      let response;
      try {
        response = await transportFetch(input, {
          ...init,
          signal: AbortSignal.any([
            init?.signal ?? operationController.signal,
            operationController.signal
          ])
        });
      } catch (error2) {
        if (operationController.signal.aborted) throw operationController.signal.reason;
        throw readerError("startplan_billing_transport_failed", "Official billing transport failed.", {
          cause: error2
        });
      }
      const responseText = await response.clone().text();
      if (Buffer.byteLength(responseText, "utf8") > MAX_RESPONSE_BYTES) {
        throw readerError("startplan_billing_response_too_large", "Official billing response is too large.");
      }
      let raw = null;
      try {
        raw = JSON.parse(responseText);
      } catch {
      }
      captured = {
        ...requestMetadata2,
        header_names: headerNames,
        http_status: response.status,
        response_bytes: Buffer.byteLength(responseText, "utf8"),
        content_type: response.headers.get("content-type"),
        request_id_hash: response.headers.get("x-request-id") ? sanitizeOfficialStartPlanPayload({ request_id: response.headers.get("x-request-id") }).request_id : null,
        duration_ms: Math.round(performance.now() - started),
        raw
      };
      return response;
    };
    const entitlement = new dependencies.StartPlanBillingEntitlement({
      getAppVersion: async () => productVersion,
      fetchImpl,
      now
    });
    const officialEntitlement = await entitlement.check({
      account: START_PLAN_PROVIDER_ID,
      provider: START_PLAN_PROVIDER_ID,
      model: "GLM-5.3-Flash",
      deviceMid: auth.deviceMid,
      jwt: auth.requestCredential,
      signal: operationController.signal
    });
    operationController.signal.throwIfAborted();
    if (requestCount !== 1 || !captured) {
      throw readerError(
        "startplan_billing_request_not_observed",
        "The official billing response was not observed."
      );
    }
    if (captured.http_status !== 200 || !isRecord5(captured.raw)) {
      const code = captured.http_status === 401 ? "startplan_billing_unauthorized" : captured.http_status === 403 ? "startplan_billing_forbidden" : captured.http_status === 429 ? "startplan_billing_rate_limited" : "startplan_billing_response_invalid";
      throw readerError(code, `Official billing returned HTTP ${captured.http_status ?? "transport"}.`);
    }
    const capturedAt = new Date(now()).toISOString();
    const requestMetadata = {
      method: captured.method,
      origin: captured.origin,
      path: captured.path,
      query_keys: captured.query_keys,
      app_version: captured.app_version,
      header_names: captured.header_names,
      http_status: captured.http_status,
      response_bytes: captured.response_bytes,
      content_type: captured.content_type,
      request_id_hash: captured.request_id_hash,
      duration_ms: captured.duration_ms,
      attempts: requestCount
    };
    const snapshot = normalizeStartPlanSnapshot(captured.raw, {
      capturedAt,
      source: "official_billing_balance",
      accountIdentity: auth.accountIdentity,
      officialEntitlement,
      requestMetadata
    });
    const credentialAfter = await fileMetadata(credentialFile);
    const lockAfter = await fileMetadata(keyringLockFile);
    const state = {
      credentials_unchanged: sameMetadata(credentialBefore, credentialAfter),
      keyring_lock_released: !lockAfter.exists,
      credential_metadata: {
        before: credentialBefore,
        after: credentialAfter
      },
      keyring_lock: {
        before: lockBefore,
        after: lockAfter
      }
    };
    return {
      captured_at: capturedAt,
      sanitized_raw: {
        schema_version: 1,
        source: "official_billing_balance",
        request: requestMetadata,
        payload: sanitizeOfficialStartPlanPayload(captured.raw)
      },
      snapshot,
      metadata: {
        schema_version: 1,
        official_runtime: {
          product_version: productVersion,
          worker_module: path16.relative(projectRoot, officialHostWorker).replaceAll("\\", "/")
        },
        authentication: {
          resolver: "createOfficialStartPlanAuthenticationResolver",
          credential_read: "read_only",
          account_hash: snapshot.account.key
        },
        request: requestMetadata,
        state,
        process: {
          model_requests_triggered: 0,
          official_billing_get_attempts: requestCount
        }
      }
    };
  } finally {
    clearTimeout(timeout);
    options.signal?.removeEventListener("abort", abortFromParent);
  }
}

// tools/cost-lab/web-server.mjs
import { randomBytes, randomUUID as randomUUID6 } from "node:crypto";
import { createReadStream as createReadStream3 } from "node:fs";
import { mkdir as mkdir3, readFile as readFile5 } from "node:fs/promises";
import http from "node:http";
import path19 from "node:path";
import { fileURLToPath as fileURLToPath7, pathToFileURL as pathToFileURL6 } from "node:url";

// tools/cost-lab/coding-plan-billing.mjs
import { access as access4, mkdir as mkdir2, readFile as readFile3, rename, rm as rm2, writeFile } from "node:fs/promises";
import { randomUUID as randomUUID4 } from "node:crypto";
import path17 from "node:path";
import { fileURLToPath as fileURLToPath6, pathToFileURL as pathToFileURL5 } from "node:url";
var SNAPSHOT_SCHEMA_VERSION = 1;
var RECONCILIATION_SCHEMA_VERSION = 3;
var DEFAULT_PROVIDER_ID = "account:bigmodel-individual-coding-plan";
var DEFAULT_TIME_ZONE = "Asia/Shanghai";
var DEFAULT_TIMEOUT_MS2 = 45e3;
var SCRIPT_ROOT3 = path17.dirname(fileURLToPath6(import.meta.url));
var PROJECT_ROOT3 = path17.resolve(SCRIPT_ROOT3, "..", "..");
var RUN_ROOT = path17.join(PROJECT_ROOT3, ".run");
var DEFAULT_OUTPUT_ROOT = path17.join(PROJECT_ROOT3, ".run", "cost-lab-billing");
var DEFAULT_RUNTIME_PATH = OFFICIAL_RUNTIME_PATH;
var MODEL_ARRAY_FIELDS = Object.freeze([
  "cachedInputTokensUsage",
  "uncachedInputTokensUsage",
  "outputTokensUsage",
  "cachedInputCreditsUsage",
  "uncachedInputCreditsUsage",
  "outputCreditsUsage"
]);
var PROVIDERS = Object.freeze({
  "account:bigmodel-individual-coding-plan": Object.freeze({
    family: "bigmodel",
    plan_scope: "personal"
  }),
  "account:zai-individual-coding-plan": Object.freeze({
    family: "zai",
    plan_scope: "personal"
  })
});
function requiredValue(argv, index, name) {
  const value = argv[index + 1];
  if (!value || value.startsWith("--")) throw new Error(`${name}_requires_value`);
  return value;
}
function parseArgs(argv) {
  const [command, ...rest] = argv;
  if (command !== "snapshot" && command !== "reconcile") {
    throw new Error("command_must_be_snapshot_or_reconcile");
  }
  const options = {
    command,
    json: false,
    provider: DEFAULT_PROVIDER_ID,
    model: null,
    range: "today",
    start: null,
    end: null,
    timeZone: DEFAULT_TIME_ZONE,
    dataRoot: null,
    out: null,
    timeoutMs: DEFAULT_TIMEOUT_MS2,
    before: null,
    after: null,
    usage: null,
    hour: null
  };
  for (let index = 0; index < rest.length; index += 1) {
    const arg = rest[index];
    if (arg === "--json") {
      options.json = true;
    } else if (arg === "--provider") {
      options.provider = requiredValue(rest, index, arg);
      index += 1;
    } else if (arg === "--model") {
      options.model = requiredValue(rest, index, arg);
      index += 1;
    } else if (arg === "--range") {
      options.range = requiredValue(rest, index, arg);
      index += 1;
    } else if (arg === "--start") {
      options.start = requiredValue(rest, index, arg);
      index += 1;
    } else if (arg === "--end") {
      options.end = requiredValue(rest, index, arg);
      index += 1;
    } else if (arg === "--timezone") {
      options.timeZone = requiredValue(rest, index, arg);
      index += 1;
    } else if (arg === "--data-root") {
      options.dataRoot = requiredValue(rest, index, arg);
      index += 1;
    } else if (arg === "--out") {
      options.out = path17.resolve(requiredValue(rest, index, arg));
      index += 1;
    } else if (arg === "--timeout-ms") {
      const value = Number(requiredValue(rest, index, arg));
      if (!Number.isSafeInteger(value) || value < 1e3 || value > 3e5) {
        throw new Error("timeout_ms_must_be_between_1000_and_300000");
      }
      options.timeoutMs = value;
      index += 1;
    } else if (arg === "--before") {
      options.before = path17.resolve(requiredValue(rest, index, arg));
      index += 1;
    } else if (arg === "--after") {
      options.after = path17.resolve(requiredValue(rest, index, arg));
      index += 1;
    } else if (arg === "--usage") {
      options.usage = path17.resolve(requiredValue(rest, index, arg));
      index += 1;
    } else if (arg === "--hour") {
      const value = Number(requiredValue(rest, index, arg));
      if (!Number.isInteger(value) || value < 0 || value > 23) {
        throw new Error("hour_must_be_between_0_and_23");
      }
      options.hour = value;
      index += 1;
    } else {
      throw new Error(`unknown_option:${arg}`);
    }
  }
  if (command === "snapshot") {
    if (!["today", "7d", "30d", "custom"].includes(options.range)) {
      throw new Error("range_must_be_today_7d_30d_or_custom");
    }
    if (options.range === "custom" && (!options.start || !options.end)) {
      throw new Error("custom_range_requires_start_and_end");
    }
    if (options.timeZone !== DEFAULT_TIME_ZONE) {
      throw new Error("only_asia_shanghai_is_supported_for_billing_windows");
    }
    assertSupportedProvider(options.provider);
  } else {
    if (!options.before || !options.after || !options.usage) {
      throw new Error("reconcile_requires_before_after_and_usage");
    }
  }
  return Object.freeze(options);
}
function assertSupportedProvider(providerId) {
  const provider = PROVIDERS[providerId];
  if (!provider) throw new Error(`unsupported_individual_coding_plan_provider:${providerId}`);
  return provider;
}
function finiteNumber(value, fallback = 0) {
  const number3 = typeof value === "string" && value.trim() ? Number(value) : value;
  return Number.isFinite(number3) ? number3 : fallback;
}
function ledgerNumber(value, tokens = false) {
  const number3 = finiteNumber(value, null);
  return number3 !== null && number3 >= 0 && (!tokens || Number.isSafeInteger(number3)) ? number3 : null;
}
function knownSum(...values) {
  return values.includes(null) ? null : values.reduce((sum, value) => sum + value, 0);
}
function normalizeHourAxis(xTime, granularity, expectedDate = null) {
  if (!Array.isArray(xTime)) return [];
  return xTime.map((entry) => {
    const raw = String(entry);
    if (granularity !== "hour") return raw;
    const match = /^(?:(\d{4}-\d{2}-\d{2})[ T])?(\d{2}):(\d{2})(?::(\d{2}))?$/u.exec(raw);
    if (!match || expectedDate && match[1] && match[1] !== expectedDate) return raw;
    return `${match[2]}:${match[3]}:${match[4] ?? "00"}`;
  });
}
function normalizeBucket(row, index) {
  const value = (field) => {
    const sequence = row?.[field];
    return Array.isArray(sequence) ? ledgerNumber(sequence[index], field.includes("Tokens")) : null;
  };
  const cachedInputTokens = value("cachedInputTokensUsage");
  const uncachedInputTokens = value("uncachedInputTokensUsage");
  const outputTokens = value("outputTokensUsage");
  const cachedInputCredits = value("cachedInputCreditsUsage");
  const uncachedInputCredits = value("uncachedInputCreditsUsage");
  const outputCredits = value("outputCreditsUsage");
  return {
    cached_input_tokens: cachedInputTokens,
    uncached_input_tokens: uncachedInputTokens,
    output_tokens: outputTokens,
    total_tokens: knownSum(cachedInputTokens, uncachedInputTokens, outputTokens),
    cached_input_credits: cachedInputCredits,
    uncached_input_credits: uncachedInputCredits,
    output_credits: outputCredits,
    total_credits: knownSum(cachedInputCredits, uncachedInputCredits, outputCredits)
  };
}
function missingModelFields(row, model) {
  const missing = [];
  for (const field of MODEL_ARRAY_FIELDS) {
    if (!Array.isArray(row?.[field]) || row[field].length !== model.hours.length || row[field].some((value) => ledgerNumber(value, field.includes("Tokens")) === null)) {
      missing.push(field);
    }
  }
  if (model.total_tokens === null) missing.push("totalTokens");
  if (model.total_credits === null) missing.push("totalCredits");
  return missing;
}
function buildSnapshotEnvelope({
  result,
  providerId,
  modelFilter = null,
  query,
  capturedAt,
  dataBaseDirSource = null
}) {
  if (!result?.snapshot || !result?.identity) throw new Error("official_billing_result_invalid");
  const provider = assertSupportedProvider(providerId);
  const snapshot = result.snapshot;
  const billingSource = sourceModelUsage(snapshot.modelUsage);
  const xTime = normalizeHourAxis(billingSource?.xTime, snapshot.modelUsage?.granularity);
  const allRows = Array.isArray(billingSource?.modelDataList) ? billingSource.modelDataList : [];
  const selectedRows = modelFilter ? allRows.filter((row) => billingModelName(row) === modelFilter) : allRows;
  if (modelFilter && selectedRows.length === 0) throw new Error(`model_not_found:${modelFilter}`);
  const models = selectedRows.map((row) => {
    const hours = xTime.map((axis, index) => ({
      bucket: axis,
      ...normalizeBucket(row, index)
    }));
    const total = (raw, field) => raw === void 0 && hours.length > 0 ? ledgerNumber(knownSum(...hours.map((hour) => hour[field])), field === "total_tokens") : ledgerNumber(raw, field === "total_tokens");
    return {
      model: billingModelName(row),
      total_tokens: total(row.totalTokens, "total_tokens"),
      total_credits: total(row.totalCredits, "total_credits"),
      hours
    };
  });
  const missingFields = selectedRows.flatMap(
    (row, index) => missingModelFields(row, models[index]).map((field) => `${billingModelName(row)}.${field}`)
  );
  if (!Array.isArray(billingSource?.xTime) || xTime.length === 0 || new Set(xTime).size !== xTime.length || snapshot.modelUsage?.granularity === "hour" && xTime.some((label) => !/^(?:[01]\d|2[0-3]):00:00$/u.test(label))) {
    missingFields.push("modelUsage.xTime");
  }
  if (snapshot.quota == null) missingFields.push("quota");
  const integrityStatus = models.length === 0 || missingFields.length > 0 ? "PARTIAL" : "COMPLETE";
  const retainedSnapshot = sanitizeOfficialSnapshot(snapshot);
  return {
    schema_version: SNAPSHOT_SCHEMA_VERSION,
    kind: "coding_plan_billing_snapshot",
    source: "official:usageStatsService.getCodingPlanUsageSnapshot",
    captured_at: capturedAt,
    provider: {
      id: String(snapshot.sourceProvider?.id ?? providerId),
      name: String(snapshot.sourceProvider?.name ?? "Coding Plan")
    },
    identity: {
      api_key_id: result.identity.apiKeyId ?? null,
      official_account_scope: result.identity.accountScope ?? null,
      plan_scope: provider.plan_scope,
      organization_id: result.identity.organizationId ?? null,
      project_id: result.identity.projectId ?? null
    },
    query: {
      range: query.range,
      custom_start_date: query.customStartDate ?? null,
      custom_end_date: query.customEndDate ?? null,
      time_zone: query.timeZone,
      model_filter: modelFilter
    },
    range: {
      start_date: snapshot.rangeStartDate ?? null,
      end_date: snapshot.rangeEndDate ?? null,
      granularity: snapshot.modelUsage?.granularity ?? null,
      generated_at: finiteNumber(snapshot.generatedAt, null)
    },
    quota: snapshot.quota ?? null,
    models,
    integrity: {
      status: integrityStatus,
      missing_fields: missingFields,
      settlement_status: "UNKNOWN",
      source_snapshot_retained: retainedSnapshot.redactedPaths.length === 0,
      redacted_secret_fields: retainedSnapshot.redactedPaths
    },
    data_discovery: {
      data_base_dir_source: dataBaseDirSource
    },
    official_snapshot: retainedSnapshot.value
  };
}
function sourceModelUsage(modelUsage) {
  return modelUsage && Object.hasOwn(modelUsage, "costLabBillingSource") ? modelUsage.costLabBillingSource : modelUsage;
}
function billingModelName(row) {
  return row?.modelName?.trim() || row?.modelCode?.trim() || null;
}
var SECRET_FIELD_PATTERN = /^(?:authorization|cookie|password|secret|credentials?|access[_-]?token|refresh[_-]?token|project[_-]?token|jwt|bearer|private[_-]?key|api[_-]?key)$/iu;
function sanitizeOfficialSnapshot(value) {
  const redactedPaths = [];
  const visit = (entry, location) => {
    if (Array.isArray(entry)) {
      return entry.map((item, index) => visit(item, `${location}[${index}]`));
    }
    if (!entry || typeof entry !== "object") return entry;
    const result = {};
    for (const [key, child] of Object.entries(entry)) {
      const childLocation = location ? `${location}.${key}` : key;
      if (SECRET_FIELD_PATTERN.test(key)) {
        result[key] = "<redacted>";
        redactedPaths.push(childLocation);
      } else {
        result[key] = visit(child, childLocation);
      }
    }
    return result;
  };
  return { value: visit(value, ""), redactedPaths };
}
function shanghaiHourForTimestamp(timestamp) {
  const date2 = timestamp instanceof Date ? timestamp : new Date(timestamp);
  if (Number.isNaN(date2.getTime())) throw new Error("usage_timestamp_invalid");
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: DEFAULT_TIME_ZONE,
    hour: "2-digit",
    hourCycle: "h23"
  }).formatToParts(date2);
  return Number(parts.find((part) => part.type === "hour")?.value);
}
function isOffPeakShanghai(date2) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: DEFAULT_TIME_ZONE,
    weekday: "short",
    hour: "2-digit",
    hourCycle: "h23"
  }).formatToParts(date2);
  const weekday = parts.find((part) => part.type === "weekday")?.value ?? "";
  const hour = Number(parts.find((part) => part.type === "hour")?.value);
  const weekdayPeak = ["Mon", "Tue", "Wed", "Thu", "Fri"].includes(weekday) && hour >= 14 && hour < 18;
  return !weekdayPeak;
}
function usageRecord(raw) {
  return raw?.request_usage ?? raw?.usage ?? raw?.tokens ?? raw;
}
function extractRequestUsage(raw) {
  const usage = usageRecord(raw);
  if (!usage || typeof usage !== "object") throw new Error("usage_record_missing");
  const pick2 = (...names) => {
    for (const name of names) {
      if (usage[name] !== void 0 && usage[name] !== null) return usage[name];
    }
    return void 0;
  };
  const cachedInputTokens = finiteNumber(
    pick2("cached_input_tokens", "cachedInputTokens", "cached_input", "cachedInput"),
    null
  );
  const explicitUncached = pick2(
    "uncached_input_tokens",
    "uncachedInputTokens",
    "uncached_input",
    "uncachedInput"
  );
  const inputTokens = pick2("input_tokens", "inputTokens");
  const outputTokensRaw = pick2("output_tokens", "outputTokens", "output");
  const explicitTotal = pick2("total_tokens", "totalTokens", "total");
  if (![
    pick2("cached_input_tokens", "cachedInputTokens", "cached_input", "cachedInput"),
    explicitUncached,
    inputTokens,
    outputTokensRaw,
    explicitTotal
  ].some((value) => value !== void 0)) {
    throw new Error("usage_token_fields_missing");
  }
  const inclusiveInput = ledgerNumber(inputTokens, true);
  const uncachedInputTokens = explicitUncached !== void 0 ? ledgerNumber(explicitUncached, true) : inclusiveInput !== null && cachedInputTokens !== null ? inclusiveInput - cachedInputTokens : null;
  const outputTokens = ledgerNumber(outputTokensRaw, true);
  const totalTokens = explicitTotal !== void 0 ? ledgerNumber(explicitTotal, true) : knownSum(cachedInputTokens, uncachedInputTokens, outputTokens);
  for (const [name, value] of Object.entries({
    cached_input_tokens: cachedInputTokens,
    uncached_input_tokens: uncachedInputTokens,
    output_tokens: outputTokens,
    total_tokens: totalTokens
  })) {
    if (!Number.isSafeInteger(value) || value < 0) throw new Error(`usage_${name}_invalid`);
  }
  if (knownSum(cachedInputTokens, uncachedInputTokens, outputTokens) !== totalTokens) {
    throw new Error("usage_total_tokens_inconsistent");
  }
  return {
    model: pick2("model", "modelName", "model_id", "modelId")?.toString() ?? raw?.model ?? raw?.model_id ?? null,
    timestamp: pick2("observed_at", "captured_at", "timestamp", "ended_at", "started_at", "time") ?? raw?.captured_at ?? raw?.timestamp ?? null,
    cached_input_tokens: cachedInputTokens,
    uncached_input_tokens: uncachedInputTokens,
    output_tokens: outputTokens,
    total_tokens: totalTokens
  };
}
function bucketAt(snapshot, model, hour) {
  const label = `${String(hour).padStart(2, "0")}:00:00`;
  const official = snapshot.official_snapshot?.modelUsage?.costLabBillingSource;
  if (!Array.isArray(official?.modelDataList) || !Array.isArray(official?.xTime)) return null;
  const rows = official.modelDataList.filter((row) => billingModelName(row) === model);
  const axis = normalizeHourAxis(official.xTime, "hour", snapshot.range.end_date);
  const index = axis.indexOf(label);
  if (rows.length !== 1 || index < 0 || axis.lastIndexOf(label) !== index) return null;
  return normalizeBucket(rows[0], index);
}
function subtractBucket(after, before) {
  const result = {};
  for (const field of [
    "cached_input_tokens",
    "uncached_input_tokens",
    "output_tokens",
    "total_tokens",
    "cached_input_credits",
    "uncached_input_credits",
    "output_credits",
    "total_credits"
  ]) {
    const isToken = field.endsWith("_tokens");
    const first = ledgerNumber(before?.[field], isToken);
    const last = ledgerNumber(after?.[field], isToken);
    result[field] = first === null || last === null ? null : last - first;
  }
  return result;
}
function changedHours(before, after, model) {
  return Array.from({ length: 24 }, (_, hour) => {
    const diff = subtractBucket(bucketAt(after, model, hour), bucketAt(before, model, hour));
    return Object.values(diff).some((value) => value !== null && Math.abs(value) > 1e-12) ? hour : null;
  }).filter((hour) => hour !== null);
}
function calculateCreditBreakdown({
  uncachedInputTokens,
  cachedInputTokens,
  outputTokens,
  offPeak,
  actualCredits,
  discountRatio = null
}) {
  for (const [name, value] of Object.entries({
    uncachedInputTokens,
    cachedInputTokens,
    outputTokens
  })) {
    if (!Number.isFinite(value) || value < 0) throw new Error(`credit_${name}_invalid`);
  }
  if (actualCredits !== null && (!Number.isFinite(actualCredits) || actualCredits < 0)) {
    throw new Error("credit_actualCredits_invalid");
  }
  const discountProvided = Number.isFinite(discountRatio) && discountRatio > 0 && discountRatio < 1;
  const baseCredits = (uncachedInputTokens * 2.3 + cachedInputTokens * 0.56 + outputTokens * 8) / 1e4;
  const timeMultiplier = offPeak ? 0.5 : 1;
  const expectedNormal = baseCredits * timeMultiplier;
  const expectedDiscount = discountProvided ? expectedNormal * discountRatio : null;
  return {
    base_credits: baseCredits,
    time_multiplier: timeMultiplier,
    expected_normal: expectedNormal,
    ...discountProvided ? { expected_with_discount: expectedDiscount, discount_ratio: discountRatio } : {},
    actual_credits: actualCredits,
    effective_extra_ratio: expectedNormal > 0 && actualCredits !== null ? actualCredits / expectedNormal : null
  };
}
function classifyCredit(actual, normal, withDiscount, discountRatio, tolerance) {
  if (actual === null) return "INCONCLUSIVE";
  if (actual === 0) return "ZERO_CHARGE";
  const normalMatch = Math.abs(actual - normal) <= tolerance;
  const discountMatch = withDiscount !== null && Math.abs(actual - withDiscount) <= tolerance;
  if (normalMatch && discountMatch) return "INCONCLUSIVE";
  if (normalMatch) return "NORMAL";
  if (discountMatch) return `EXTRA_DISCOUNT_${discountRatio}`;
  return "OTHER";
}
function reconcileBillingSnapshots(before, after, rawUsage, options = {}) {
  if (before?.kind !== "coding_plan_billing_snapshot" || after?.kind !== "coding_plan_billing_snapshot") {
    throw new Error("billing_snapshot_schema_invalid");
  }
  if (!before.provider?.id || before.provider.id !== after.provider?.id) throw new Error("billing_provider_changed");
  if (!before.query?.time_zone || before.query.time_zone !== after.query?.time_zone) {
    throw new Error("billing_timezone_changed");
  }
  for (const key of ["api_key_id", "organization_id", "project_id", "official_account_scope", "plan_scope"]) {
    if ((before.identity?.[key] ?? null) !== (after.identity?.[key] ?? null)) {
      throw new Error("billing_identity_changed");
    }
  }
  if (typeof before.identity?.api_key_id !== "string" || !before.identity.api_key_id.trim()) {
    throw new Error("billing_identity_missing");
  }
  const beforeStartDate = before.range?.start_date;
  const beforeEndDate = before.range?.end_date;
  const afterStartDate = after.range?.start_date;
  const afterEndDate = after.range?.end_date;
  if (!beforeStartDate || !beforeEndDate || !afterStartDate || !afterEndDate) {
    throw new Error("billing_range_date_missing");
  }
  if (beforeStartDate !== afterStartDate || beforeEndDate !== afterEndDate) {
    throw new Error("billing_range_changed");
  }
  if (beforeStartDate !== beforeEndDate || before.range.granularity !== "hour" || after.range.granularity !== "hour") throw new Error("billing_single_day_hourly_range_required");
  const usage = extractRequestUsage(rawUsage);
  const model = options.model ?? usage.model;
  if (!model) throw new Error("model_required_for_reconciliation");
  if (usage.model && usage.model !== model) throw new Error("billing_usage_model_changed");
  let hour = options.hour;
  if (hour === void 0 || hour === null) {
    const changed = changedHours(before, after, model);
    if (changed.length !== 1) throw new Error("hour_required_for_reconciliation");
    hour = changed[0];
  }
  if (!Number.isInteger(hour) || hour < 0 || hour > 23) throw new Error("billing_hour_invalid");
  const beforeCaptured = Date.parse(before.captured_at);
  const afterCaptured = Date.parse(after.captured_at);
  if (!Number.isFinite(beforeCaptured) || !Number.isFinite(afterCaptured) || afterCaptured < beforeCaptured) {
    throw new Error("billing_capture_order_invalid");
  }
  if (usage.timestamp !== null) {
    const observed = new Date(usage.timestamp);
    const observedAt = observed.getTime();
    if (!Number.isFinite(observedAt)) {
      throw new Error("billing_usage_outside_capture_window");
    }
    const localDate = new Intl.DateTimeFormat("en-CA", {
      timeZone: DEFAULT_TIME_ZONE,
      year: "numeric",
      month: "2-digit",
      day: "2-digit"
    }).format(observed);
    if (localDate !== afterEndDate || shanghaiHourForTimestamp(observed) !== hour) {
      throw new Error("billing_usage_window_changed");
    }
    if (observedAt < beforeCaptured || observedAt > afterCaptured) {
      throw new Error("billing_usage_outside_capture_window");
    }
  }
  const diff = subtractBucket(bucketAt(after, model, hour), bucketAt(before, model, hour));
  const complete = Object.values(diff).every((value) => value !== null && value >= -1e-12);
  const creditsObserved = complete && diff.total_credits > 1e-12;
  const settledZero = complete && diff.total_credits === 0 && after.integrity?.settlement_status === "SETTLED";
  const tokenDeltaObserved = complete && diff.total_tokens > 0;
  const tokenMatch = complete && (tokenDeltaObserved || settledZero) && diff.cached_input_tokens === usage.cached_input_tokens && diff.uncached_input_tokens === usage.uncached_input_tokens && diff.output_tokens === usage.output_tokens && diff.total_tokens === usage.total_tokens;
  const bucketDateKey = after.range.end_date ?? after.range.start_date;
  if (!bucketDateKey) throw new Error("billing_range_date_missing");
  const bucketInstant = /* @__PURE__ */ new Date(
    `${bucketDateKey}T${String(hour).padStart(2, "0")}:00:00+08:00`
  );
  if (Number.isNaN(bucketInstant.getTime())) throw new Error("billing_hour_date_invalid");
  const calculation = calculateCreditBreakdown({
    uncachedInputTokens: usage.uncached_input_tokens,
    cachedInputTokens: usage.cached_input_tokens,
    outputTokens: usage.output_tokens,
    offPeak: isOffPeakShanghai(bucketInstant),
    actualCredits: tokenMatch && (creditsObserved || settledZero) ? diff.total_credits : null,
    discountRatio: options.discountRatio ?? null
  });
  const tolerance = options.creditTolerance ?? 5e-4;
  const creditClass = classifyCredit(
    calculation.actual_credits,
    calculation.expected_normal,
    calculation.expected_with_discount ?? null,
    calculation.discount_ratio ?? null,
    tolerance
  );
  const reconciliationStatus = tokenMatch && (creditClass === "NORMAL" || creditClass === "ZERO_CHARGE" || creditClass.startsWith("EXTRA_DISCOUNT_")) ? "PASS" : "INCONCLUSIVE";
  let settlementStatus = "NO_OBSERVED_CREDIT_DELTA";
  if (!complete) settlementStatus = "INVALID_BILLING_DATA";
  else if (settledZero) settlementStatus = "ZERO_CHARGE_OBSERVED";
  else if (creditsObserved) settlementStatus = "DELTA_OBSERVED";
  else if (tokenDeltaObserved) settlementStatus = "CREDITS_PENDING";
  if ((creditsObserved || settledZero) && !tokenMatch) settlementStatus = "UNATTRIBUTED_DELTA";
  return {
    schema_version: RECONCILIATION_SCHEMA_VERSION,
    kind: "coding_plan_billing_reconciliation",
    provider: after.provider,
    model,
    time_zone: after.query.time_zone,
    hour: `${String(hour).padStart(2, "0")}:00:00`,
    captured_at: (/* @__PURE__ */ new Date()).toISOString(),
    before_captured_at: before.captured_at,
    after_captured_at: after.captured_at,
    official_delta: Object.fromEntries(Object.entries(diff).map(([key, value]) => [
      key,
      key.endsWith("_credits") && !creditsObserved && !settledZero ? null : value
    ])),
    request_usage: usage,
    token_match: tokenMatch,
    calculation,
    credit_class: creditClass,
    credit_tolerance: tolerance,
    billing_reconciliation: reconciliationStatus,
    settlement_status: settlementStatus,
    limitations: [
      "official_api_is_hour_aggregated",
      "unique_attribution_requires_token_match_and_no_parallel_activity",
      "entitlement_is_not_inferred_from_a_single_credit_ratio"
    ]
  };
}
async function atomicWriteJson(filePath, value) {
  const directory = path17.dirname(filePath);
  await mkdir2(directory, { recursive: true });
  const temporary = path17.join(
    directory,
    `.${path17.basename(filePath)}.${process.pid}.${randomUUID4()}.tmp`
  );
  try {
    await writeFile(temporary, `${JSON.stringify(value, null, 2)}
`, {
      encoding: "utf8",
      flag: "wx"
    });
    await rename(temporary, filePath);
  } catch (error2) {
    await rm2(temporary, { force: true }).catch(() => void 0);
    throw error2;
  }
}
function assertProjectRunOutput(filePath) {
  const relative = path17.relative(RUN_ROOT, path17.resolve(filePath));
  if (relative === "" || relative.startsWith(`..${path17.sep}`) || relative === ".." || path17.isAbsolute(relative)) {
    throw new Error("output_must_be_inside_project_run_root");
  }
}
function timestampSlug(date2) {
  return date2.toISOString().replaceAll(":", "").replaceAll(".", "").replace("T", "-").replace("Z", "Z");
}
function defaultOutputPath(prefix, now) {
  return path17.join(DEFAULT_OUTPUT_ROOT, `${prefix}-${timestampSlug(now)}.json`);
}
function sanitizeErrorMessage(error2) {
  const raw = error2 instanceof Error ? error2.message : String(error2);
  return raw.replace(
    /\b(authorization|api[_-]?key|access[_-]?token|project[_-]?token)\b\s*[:=]\s*(?:Bearer\s+)?[^\s,;]+/giu,
    "$1=<redacted>"
  ).replace(/\bBearer\s+[^\s,;]+/giu, "Bearer <redacted>").slice(0, 500);
}
function safeError(error2) {
  return {
    ok: false,
    error: {
      code: "cost_lab_billing_error",
      message: sanitizeErrorMessage(error2)
    }
  };
}
async function withTimeout(promise, timeoutMs, timeoutCode, onTimeout) {
  let timer;
  try {
    return await Promise.race([
      promise,
      new Promise((_, reject) => {
        timer = setTimeout(() => {
          reject(new Error(timeoutCode));
          queueMicrotask(() => onTimeout?.());
        }, timeoutMs);
      })
    ]);
  } finally {
    clearTimeout(timer);
  }
}
async function loadOfficialRuntime(runtimePath = DEFAULT_RUNTIME_PATH) {
  const module = await import(pathToFileURL5(runtimePath).href);
  if (typeof module.createCostLabBillingRuntime !== "function") {
    throw new Error("official_billing_runtime_export_missing");
  }
  return module;
}
async function captureSnapshot(options, dependencies = {}) {
  const provider = assertSupportedProvider(options.provider);
  const now = dependencies.now?.() ?? /* @__PURE__ */ new Date();
  const resolvedData = resolveBillingDataBaseDir(options.dataRoot, {
    env: dependencies.env ?? process.env,
    platform: dependencies.platform ?? process.platform,
    fallbackHomeDir: dependencies.fallbackHomeDir,
    fileExists: dependencies.fileExists,
    readFile: dependencies.readFile
  });
  const dataDirectoryExists = dependencies.dataDirectoryExists ? await dependencies.dataDirectoryExists(resolvedData.dataBaseDir) : await access4(resolvedData.dataBaseDir).then(
    () => true,
    () => false
  );
  if (!dataDirectoryExists) throw new Error("billing_data_base_dir_not_found");
  if (!dependencies.runtimeModule) {
    await prepareOfficialBillingVendor({
      platform: dependencies.platform ?? process.platform,
      arch: dependencies.arch ?? process.arch
    });
  }
  const runtimeModule = dependencies.runtimeModule ?? await loadOfficialRuntime(dependencies.runtimePath);
  const controller = new AbortController();
  const runtime = runtimeModule.createCostLabBillingRuntime({
    dataBaseDir: resolvedData.dataBaseDir,
    signal: controller.signal
  });
  const request = {
    range: options.range,
    preferredProviderId: options.provider,
    accountAccess: {
      type: "zhipu-account",
      family: provider.family,
      planKind: "individual-coding-plan"
    },
    timeZone: options.timeZone,
    ...options.range === "custom" ? {
      customStartDate: options.start,
      customEndDate: options.end
    } : {}
  };
  const result = await withTimeout(
    runtime.getCodingPlanUsageSnapshot(request),
    options.timeoutMs,
    "official_billing_read_timeout",
    () => controller.abort(new Error("official_billing_read_timeout"))
  ).finally(() => controller.abort(new Error("official_billing_read_complete")));
  return buildSnapshotEnvelope({
    result,
    providerId: options.provider,
    modelFilter: options.model,
    query: request,
    capturedAt: now.toISOString(),
    dataBaseDirSource: resolvedData.dataBaseDirSource
  });
}
async function readJson(filePath) {
  try {
    return JSON.parse(await readFile3(filePath, "utf8"));
  } catch (error2) {
    if (error2 instanceof SyntaxError) throw new Error(`json_invalid:${path17.basename(filePath)}`);
    throw error2;
  }
}
async function run(argv, dependencies = {}) {
  const options = parseArgs(argv);
  const stdout = dependencies.stdout ?? ((text) => process.stdout.write(text));
  const now = dependencies.now?.() ?? /* @__PURE__ */ new Date();
  let result;
  let prefix;
  if (options.command === "snapshot") {
    result = await captureSnapshot(options, { ...dependencies, now: () => now });
    prefix = "snapshot";
  } else {
    const [before, after, usage] = await Promise.all([
      readJson(options.before),
      readJson(options.after),
      readJson(options.usage)
    ]);
    result = reconcileBillingSnapshots(before, after, usage, {
      model: options.model,
      hour: options.hour
    });
    prefix = "reconciliation";
  }
  const outputPath = options.out ?? defaultOutputPath(prefix, now);
  assertProjectRunOutput(outputPath);
  await atomicWriteJson(outputPath, result);
  const commandResult = {
    ok: true,
    output_path: path17.relative(PROJECT_ROOT3, outputPath).replaceAll(path17.sep, "/"),
    data: result
  };
  if (options.json) {
    stdout(`${JSON.stringify(commandResult, null, 2)}
`);
  } else {
    stdout(`${prefix} written: ${commandResult.output_path}
`);
  }
  return commandResult;
}
async function main() {
  try {
    await run(process.argv.slice(2));
  } catch (error2) {
    process.stderr.write(`${JSON.stringify(safeError(error2), null, 2)}
`);
    process.exitCode = 1;
  }
}
if (process.argv[1] && import.meta.url === pathToFileURL5(path17.resolve(process.argv[1])).href) {
  await main();
}

// tools/cost-lab/startplan-web.mjs
import { createHash as createHash9, randomUUID as randomUUID5 } from "node:crypto";
import { readFile as readFile4 } from "node:fs/promises";
import path18 from "node:path";
var DEFAULT_COOLDOWN_MS = 5e3;
var DEFAULT_HISTORY_LIMIT = 25;
var MAX_HISTORY_ITEMS = 100;
function serviceError(statusCode, code, message, details = {}) {
  const error2 = new Error(message);
  error2.statusCode = statusCode;
  error2.code = code;
  Object.assign(error2, details);
  return error2;
}
function asDate(now) {
  const value = now();
  const date2 = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date2.getTime())) throw new Error("startplan_clock_invalid");
  return date2;
}
function validStoredItem(value) {
  return value && typeof value === "object" && typeof value.id === "string" && /^[0-9a-f-]{36}$/u.test(value.id) && value.snapshot && typeof value.snapshot === "object" && typeof value.captured_at === "string";
}
function snapshotDigest(snapshot) {
  const canonical = {
    account: snapshot.account?.key ?? null,
    server_time: snapshot.server_time ?? null,
    plans: snapshot.plans ?? [],
    buckets: snapshot.buckets ?? []
  };
  return createHash9("sha256").update(JSON.stringify(canonical)).digest("hex");
}
function normalizeQueryDate(value, field) {
  if (value === null || value === void 0 || value === "") return null;
  const milliseconds = Date.parse(value);
  if (!Number.isFinite(milliseconds)) {
    throw serviceError(400, "STARTPLAN_HISTORY_RANGE_INVALID", `${field} must be an ISO timestamp.`);
  }
  return milliseconds;
}
function summarize(item, nowMs) {
  const snapshot = item.snapshot;
  return {
    id: item.id,
    captured_at: item.captured_at,
    server_time: snapshot.server_time ?? null,
    plan_id: snapshot.plan_id ?? null,
    plan_type: snapshot.plan_type ?? null,
    plan_status: snapshot.plan_status ?? null,
    entitlement_status: snapshot.official_entitlement?.status ?? null,
    unit_type: snapshot.unit_type ?? null,
    total_balance: snapshot.total_balance ?? null,
    used_balance: snapshot.used_balance ?? null,
    remaining_balance: snapshot.remaining_balance ?? null,
    billing_period: snapshot.billing_period ?? null,
    expiry: snapshot.expiry ?? null,
    missing_fields: Array.isArray(snapshot.missing_fields) ? snapshot.missing_fields : [],
    buckets: Array.isArray(snapshot.buckets) ? snapshot.buckets : [],
    freshness: annotateStartPlanFreshness(snapshot, nowMs),
    integrity: snapshot.integrity?.status ?? "UNKNOWN",
    bucket_count: Array.isArray(snapshot.buckets) ? snapshot.buckets.length : null
  };
}
function publicItem(item, nowMs) {
  return {
    ...summarize(item, nowMs),
    snapshot: {
      ...item.snapshot,
      freshness: annotateStartPlanFreshness(item.snapshot, nowMs)
    },
    integrity: item.integrity ?? item.snapshot.integrity ?? null,
    sanitized_raw: item.sanitized_raw ?? null,
    capture_metadata: item.capture_metadata ?? null
  };
}
function createStartPlanBillingService(options = {}) {
  if (!options.historyPath) throw new Error("startplan_history_path_required");
  if (typeof options.readBilling !== "function") throw new Error("startplan_reader_required");
  const historyPath = path18.resolve(options.historyPath);
  const now = options.now ?? (() => /* @__PURE__ */ new Date());
  const createId = options.createId ?? randomUUID5;
  const cooldownMs = options.cooldownMs ?? DEFAULT_COOLDOWN_MS;
  const maximumItems = options.maximumItems ?? MAX_HISTORY_ITEMS;
  const state = {
    loaded: false,
    items: [],
    inFlight: null,
    lastAttemptMs: null,
    activeAbortController: null,
    closed: false
  };
  async function ensureLoaded() {
    if (state.loaded) return;
    try {
      const parsed = JSON.parse(await readFile4(historyPath, "utf8"));
      if (parsed?.schema_version !== STARTPLAN_HISTORY_SCHEMA_VERSION || !Array.isArray(parsed.items)) {
        throw new Error("startplan_history_schema_invalid");
      }
      state.items = parsed.items.filter(validStoredItem).slice(-maximumItems);
    } catch (error2) {
      if (error2?.code !== "ENOENT") throw error2;
      state.items = [];
    }
    state.loaded = true;
  }
  async function persist() {
    const updated = asDate(now).toISOString();
    await atomicWriteJson(historyPath, {
      schema_version: STARTPLAN_HISTORY_SCHEMA_VERSION,
      updated_at: updated,
      items: state.items.slice(-maximumItems)
    });
  }
  function latestInternal() {
    return state.items.at(-1) ?? null;
  }
  async function latest2() {
    await ensureLoaded();
    const currentMs = asDate(now).getTime();
    const latestItem = latestInternal();
    const previousItem = state.items.at(-2) ?? null;
    return {
      available: Boolean(latestItem),
      state: latestItem ? "AVAILABLE" : "NO_SNAPSHOT",
      official_request_performed: false,
      snapshot: latestItem ? publicItem(latestItem, currentMs) : null,
      comparison: latestItem && previousItem ? compareStartPlanSnapshots(previousItem.snapshot, latestItem.snapshot) : null
    };
  }
  async function history(query = {}) {
    await ensureLoaded();
    const fromMs = normalizeQueryDate(query.from, "from");
    const toMs = normalizeQueryDate(query.to, "to");
    if (fromMs !== null && toMs !== null && fromMs > toMs) {
      throw serviceError(400, "STARTPLAN_HISTORY_RANGE_INVALID", "from must not be after to.");
    }
    const requestedLimit = query.limit === void 0 || query.limit === null || query.limit === "" ? DEFAULT_HISTORY_LIMIT : Number(query.limit);
    if (!Number.isInteger(requestedLimit) || requestedLimit < 1 || requestedLimit > DEFAULT_HISTORY_LIMIT) {
      throw serviceError(
        400,
        "STARTPLAN_HISTORY_LIMIT_INVALID",
        `limit must be an integer from 1 to ${DEFAULT_HISTORY_LIMIT}.`
      );
    }
    const currentMs = asDate(now).getTime();
    const filtered = state.items.filter((item) => {
      const capturedMs = Date.parse(item.captured_at);
      return Number.isFinite(capturedMs) && (fromMs === null || capturedMs >= fromMs) && (toMs === null || capturedMs <= toMs);
    });
    const selected = filtered.slice(-requestedLimit);
    return {
      items: selected.map((item) => publicItem(item, currentMs)),
      total: filtered.length,
      limit: requestedLimit,
      official_request_performed: false
    };
  }
  async function findById(id) {
    await ensureLoaded();
    return state.items.find((item) => item.id === id) ?? null;
  }
  async function exportSnapshot(id) {
    const item = await findById(id);
    if (!item) {
      throw serviceError(404, "STARTPLAN_SNAPSHOT_NOT_FOUND", "Start Plan snapshot not found.");
    }
    return {
      schema_version: 1,
      exported_at: asDate(now).toISOString(),
      redaction: "credential_fields_absolute_paths_and_raw_opaque_ids_omitted",
      model_requests: 0,
      snapshot: publicItem(item, asDate(now).getTime())
    };
  }
  async function doRefresh(signal) {
    const startedAt = asDate(now);
    const read = await options.readBilling({ signal });
    if (!read?.snapshot || !read?.sanitized_raw) {
      throw serviceError(
        502,
        "STARTPLAN_READER_RESPONSE_INVALID",
        "The official Start Plan reader returned an invalid response."
      );
    }
    const id = createId();
    const digest = snapshotDigest(read.snapshot);
    const duplicate = state.items.find((item2) => item2.dedupe_digest === digest);
    if (duplicate) {
      return {
        snapshot: publicItem(duplicate, startedAt.getTime()),
        deduplicated: true,
        official_request_performed: true,
        official_billing_get_attempts: 1
      };
    }
    const capturedAt = read.snapshot.captured_at ?? startedAt.toISOString();
    const item = {
      id,
      captured_at: capturedAt,
      stored_at: startedAt.toISOString(),
      dedupe_digest: digest,
      snapshot: read.snapshot,
      sanitized_raw: read.sanitized_raw,
      capture_metadata: read.metadata ?? null,
      integrity: read.snapshot.integrity ?? null
    };
    state.items.push(item);
    if (state.items.length > maximumItems) state.items.splice(0, state.items.length - maximumItems);
    try {
      await persist();
    } catch (error2) {
      state.items = state.items.filter((candidate) => candidate !== item);
      throw error2;
    }
    return {
      snapshot: publicItem(item, startedAt.getTime()),
      deduplicated: false,
      official_request_performed: true,
      official_billing_get_attempts: 1
    };
  }
  async function refresh() {
    await ensureLoaded();
    if (state.closed) {
      throw serviceError(503, "STARTPLAN_SERVICE_CLOSING", "The Cost Lab service is closing.");
    }
    if (state.inFlight) {
      const completed = await state.inFlight;
      return { ...completed, deduplicated: true };
    }
    const currentMs = asDate(now).getTime();
    if (state.lastAttemptMs !== null && currentMs - state.lastAttemptMs < cooldownMs) {
      const retryAfterMs = cooldownMs - (currentMs - state.lastAttemptMs);
      throw serviceError(
        429,
        "STARTPLAN_REFRESH_COOLDOWN",
        "Start Plan billing was refreshed recently.",
        { retryAfterMs }
      );
    }
    state.lastAttemptMs = currentMs;
    const abortController = new AbortController();
    state.activeAbortController = abortController;
    const operation = doRefresh(abortController.signal).finally(() => {
      if (state.inFlight === operation) state.inFlight = null;
      if (state.activeAbortController === abortController) state.activeAbortController = null;
    });
    state.inFlight = operation;
    return operation;
  }
  async function close({ abort = true } = {}) {
    state.closed = true;
    if (abort) state.activeAbortController?.abort(new Error("cost_lab_startplan_shutdown"));
    if (!state.inFlight) return;
    await state.inFlight.catch(() => void 0);
  }
  return {
    latest: latest2,
    history,
    refresh,
    exportSnapshot,
    close,
    historyPath
  };
}

// tools/cost-lab/web-server.mjs
var SCRIPT_ROOT4 = path19.dirname(fileURLToPath7(import.meta.url));
var PROJECT_ROOT4 = path19.resolve(SCRIPT_ROOT4, "..", "..");
var DEFAULT_HISTORY_PATH = path19.join(PROJECT_ROOT4, ".run", "cost-lab-web", "history.json");
var DEFAULT_STARTPLAN_HISTORY_PATH = path19.join(PROJECT_ROOT4, ".run", "cost-lab-web", "startplan-history.json");
var LOOPBACK_HOST = "127.0.0.1";
var CONFIRMATION_PHRASE = "START REAL CODING PLAN VERIFICATION";
var MAX_JSON_BYTES = 64 * 1024;
var MAX_HISTORY_ITEMS2 = 50;
var STATIC_FILES = Object.freeze({
  "/": Object.freeze({ file: "index.html", type: "text/html; charset=utf-8" }),
  "/index.html": Object.freeze({ file: "index.html", type: "text/html; charset=utf-8" }),
  "/app.js": Object.freeze({ file: "app.js", type: "text/javascript; charset=utf-8" }),
  "/startplan-view.mjs": Object.freeze({
    file: "startplan-view.mjs",
    type: "text/javascript; charset=utf-8"
  }),
  "/styles.css": Object.freeze({ file: "styles.css", type: "text/css; charset=utf-8" }),
  "/favicon.svg": Object.freeze({ file: "favicon.svg", type: "image/svg+xml" })
});
function createCostLabWebServer(options = {}) {
  const projectRoot = path19.resolve(options.projectRoot ?? PROJECT_ROOT4);
  const uiRoot = path19.join(SCRIPT_ROOT4, "web");
  const apiMountPath = options.apiMountPath ? normalizeApiMountPath(options.apiMountPath) : null;
  const evidenceRoot = path19.resolve(options.evidenceRoot ?? path19.join(projectRoot, ".run"));
  const historyPath = path19.resolve(options.historyPath ?? path19.join(projectRoot, ".run", "cost-lab-web", "history.json"));
  const startPlanHistoryPath = path19.resolve(
    options.startPlanHistoryPath ?? path19.join(projectRoot, ".run", "cost-lab-web", "startplan-history.json")
  );
  assertInside2(evidenceRoot, historyPath);
  assertInside2(evidenceRoot, startPlanHistoryPath);
  const dependencies = {
    captureSnapshot: options.captureSnapshot ?? captureSnapshot,
    inspectEnvironment: options.inspectEnvironment ?? inspectCostLabEnvironment,
    verificationRunner: options.verificationRunner ?? loadOptionalVerificationRunner(),
    protocolSmoke: options.protocolSmoke ?? runOfficialAppServerProtocolSmoke,
    now: options.now ?? (() => /* @__PURE__ */ new Date()),
    createId: options.createId ?? randomUUID6,
    afterRetryDelaysMs: options.afterRetryDelaysMs ?? [
      0,
      5e3,
      15e3,
      3e4,
      45e3,
      6e4
    ]
  };
  const officialHostWorker = path19.resolve(
    options.officialHostWorker ?? path19.join(
      projectRoot,
      "plugins",
      "codex-zcode-bridge",
      "worker",
      "worker-main.mjs"
    )
  );
  const startPlanReadBilling = options.readStartPlanBilling ?? (async ({ signal }) => {
    const data = resolveBillingDataBaseDir(options.startPlanDataBaseDir ?? null, {
      env: options.env ?? process.env,
      platform: options.platform ?? process.platform
    });
    return readOfficialStartPlanBilling({
      projectRoot,
      dataBaseDir: data.dataBaseDir,
      officialHostWorker,
      signal,
      now: () => dependencies.now().getTime()
    });
  });
  const startPlanBilling = options.startPlanBillingService ?? createStartPlanBillingService({
    historyPath: startPlanHistoryPath,
    readBilling: startPlanReadBilling,
    now: dependencies.now,
    createId: dependencies.createId,
    cooldownMs: options.startPlanCooldownMs
  });
  const state = {
    csrfToken: options.csrfToken ?? randomBytes(32).toString("base64url"),
    server: null,
    origin: null,
    port: null,
    closed: false,
    activeVerificationId: null,
    activeAbortController: null,
    activeVerificationPromise: null,
    historyLoaded: false,
    history: []
  };
  const server = http.createServer((request, response) => {
    void handleRequest(request, response).catch((error2) => {
      if (response.headersSent) {
        response.destroy();
        return;
      }
      const status = Number.isInteger(error2?.statusCode) ? error2.statusCode : 500;
      sendJson(response, status, {
        ok: false,
        error: {
          code: typeof error2?.code === "string" ? error2.code : "COST_LAB_INTERNAL_ERROR",
          message: redactValue(sanitizeErrorMessage(error2))
        }
      });
    });
  });
  server.on("clientError", (_error, socket) => {
    socket.end("HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n");
  });
  state.server = server;
  async function start() {
    if (state.server.listening) return publicAddress();
    await mkdir3(path19.dirname(historyPath), { recursive: true });
    await ensureHistoryLoaded();
    await new Promise((resolve, reject) => {
      const onError = (error2) => {
        state.server.off("listening", onListening);
        reject(error2);
      };
      const onListening = () => {
        state.server.off("error", onError);
        resolve();
      };
      state.server.once("error", onError);
      state.server.once("listening", onListening);
      state.server.listen(options.port ?? 0, LOOPBACK_HOST);
    });
    const address = state.server.address();
    if (!address || typeof address === "string") throw new Error("cost_lab_server_address_unavailable");
    state.port = address.port;
    state.origin = `http://${LOOPBACK_HOST}:${state.port}`;
    return publicAddress();
  }
  async function mountEndpoints({ origin, port }) {
    if (!apiMountPath) throw new Error("cost_lab_api_mount_path_required");
    if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error("cost_lab_mount_port_invalid");
    const parsed = new URL(origin);
    if (parsed.protocol !== "http:" || parsed.hostname !== LOOPBACK_HOST || parsed.port !== String(port)) {
      throw new Error("cost_lab_mount_origin_invalid");
    }
    state.origin = parsed.origin;
    state.port = port;
    await ensureHistoryLoaded();
  }
  async function close({ abortActive = true, timeoutMs = 15e4 } = {}) {
    state.closed = true;
    const listenerClosed = new Promise((resolve) => {
      if (!state.server.listening) {
        resolve();
        return;
      }
      const timer = setTimeout(() => state.server.closeAllConnections(), Math.min(timeoutMs, 1e4));
      state.server.close(() => {
        clearTimeout(timer);
        resolve();
      });
    });
    if (abortActive && state.activeAbortController) {
      state.activeAbortController.abort(new Error("cost_lab_server_shutdown"));
    }
    await Promise.all([
      listenerClosed,
      withTimeout2(
        state.activeVerificationPromise?.catch(() => void 0) ?? Promise.resolve(),
        timeoutMs,
        "cost_lab_verification_shutdown_timeout"
      ),
      withTimeout2(
        startPlanBilling.close({ abort: abortActive }),
        Math.min(timeoutMs, 25e3),
        "cost_lab_startplan_shutdown_timeout"
      )
    ]);
  }
  function publicAddress() {
    return {
      host: LOOPBACK_HOST,
      port: state.port,
      origin: state.origin,
      url: state.origin ? `${state.origin}/` : null
    };
  }
  async function handleRequest(request, response) {
    applySecurityHeaders(response);
    if (!isLoopbackAddress(request.socket.remoteAddress)) {
      sendJson(response, 403, {
        ok: false,
        error: { code: "COST_LAB_LOCAL_ONLY", message: "Cost Lab accepts loopback connections only." }
      });
      return;
    }
    if (!validHostHeader(request, state.port)) {
      sendJson(response, 403, {
        ok: false,
        error: { code: "COST_LAB_HOST_REJECTED", message: "The request Host header is not the local Cost Lab origin." }
      });
      return;
    }
    const url = new URL(request.url ?? "/", state.origin ?? `http://${LOOPBACK_HOST}`);
    if (apiMountPath) {
      const mountedPrefix = `${apiMountPath}/`;
      if (!url.pathname.startsWith(mountedPrefix)) {
        sendJson(response, 404, {
          ok: false,
          error: { code: "COST_LAB_NOT_FOUND", message: "Unknown mounted Cost Lab route." }
        });
        return;
      }
      url.pathname = `/api/${url.pathname.slice(mountedPrefix.length)}`;
    }
    if (request.method === "GET" || request.method === "HEAD") {
      const staticFile = STATIC_FILES[url.pathname];
      if (staticFile) {
        await serveStatic(uiRoot, staticFile, request.method, response);
        return;
      }
    }
    if (!url.pathname.startsWith("/api/")) {
      sendJson(response, 404, {
        ok: false,
        error: { code: "COST_LAB_NOT_FOUND", message: "Unknown Cost Lab route." }
      });
      return;
    }
    if (request.method === "OPTIONS") {
      sendJson(response, 405, {
        ok: false,
        error: { code: "COST_LAB_PREFLIGHT_REJECTED", message: "Cross-origin requests are not supported." }
      }, { Allow: "GET, HEAD, POST" });
      return;
    }
    if (request.method === "POST" && !validStateChangingRequest(request, state.origin, state.csrfToken)) {
      sendJson(response, 403, {
        ok: false,
        error: { code: "COST_LAB_CSRF_REJECTED", message: "Origin or CSRF validation failed." }
      });
      return;
    }
    const body = request.method === "POST" ? await readJsonBody(request) : null;
    await routeApi(request.method, url, body, response);
  }
  async function routeApi(method, url, body, response) {
    if (method === "GET" && url.pathname === "/api/session") {
      await ensureHistoryLoaded();
      sendJson(response, 200, {
        ok: true,
        data: {
          schema_version: 1,
          csrf_token: state.csrfToken,
          confirmation_phrase: CONFIRMATION_PHRASE,
          provider: DEFAULT_PROVIDER_ID,
          model: "GLM-5.3-Flash",
          time_zone: DEFAULT_TIME_ZONE,
          model_requests_on_page_load: 0,
          active_verification_id: state.activeVerificationId
        }
      });
      return;
    }
    if (method === "GET" && url.pathname === "/api/health") {
      sendJson(response, 200, { ok: true, data: { status: "READY", local_only: true } });
      return;
    }
    if (method === "GET" && url.pathname === "/api/environment") {
      const environment = await dependencies.inspectEnvironment({ deep: false });
      sendJson(response, 200, { ok: true, data: redactValue(environment) });
      return;
    }
    if (method === "POST" && url.pathname === "/api/environment/check") {
      const deep = body?.deep === true;
      const environment = await dependencies.inspectEnvironment({
        deep,
        protocolSmoke: dependencies.protocolSmoke
      });
      sendJson(response, 200, { ok: true, data: redactValue(environment) });
      return;
    }
    if (method === "POST" && url.pathname === "/api/billing/snapshot") {
      const snapshot = await dependencies.captureSnapshot(snapshotOptions(body));
      sendJson(response, 200, {
        ok: true,
        data: redactValue(snapshot)
      });
      return;
    }
    if (method === "GET" && url.pathname === "/api/billing/startplan/latest") {
      const result = await startPlanBilling.latest();
      sendJson(response, 200, { ok: true, data: redactValue(result) });
      return;
    }
    if (method === "GET" && url.pathname === "/api/billing/startplan/history") {
      const result = await startPlanBilling.history({
        from: url.searchParams.get("from"),
        to: url.searchParams.get("to"),
        limit: url.searchParams.get("limit")
      });
      sendJson(response, 200, { ok: true, data: redactValue(result) });
      return;
    }
    if (method === "POST" && url.pathname === "/api/billing/startplan/refresh") {
      if (body !== null && body !== void 0 && Object.keys(body).length !== 0) {
        throw httpError(
          400,
          "STARTPLAN_REFRESH_INPUT_REJECTED",
          "Start Plan refresh uses the discovered official account context only."
        );
      }
      try {
        const result = await startPlanBilling.refresh();
        sendJson(response, 200, { ok: true, data: redactValue(result) });
      } catch (error2) {
        throw mapStartPlanError(error2);
      }
      return;
    }
    const startPlanExport = /^\/api\/billing\/startplan\/history\/([0-9a-f-]{36})\/export$/u.exec(url.pathname);
    if (method === "GET" && startPlanExport) {
      const exported = await startPlanBilling.exportSnapshot(startPlanExport[1]);
      const bodyText = `${JSON.stringify(redactValue(exported), null, 2)}
`;
      response.writeHead(200, {
        "Content-Type": "application/json; charset=utf-8",
        "Content-Disposition": `attachment; filename="cost-lab-startplan-${startPlanExport[1]}.json"`,
        "Cache-Control": "no-store"
      });
      response.end(bodyText);
      return;
    }
    if (method === "POST" && url.pathname === "/api/verifications") {
      const started = await startVerification(body);
      sendJson(response, 202, { ok: true, data: redactValue(started) });
      return;
    }
    const verification = /^\/api\/verifications\/([0-9a-f-]{36})$/u.exec(url.pathname);
    if (method === "GET" && verification) {
      const record3 = findRecord(verification[1]);
      if (!record3) {
        sendJson(response, 404, { ok: false, error: { code: "VERIFICATION_NOT_FOUND", message: "Verification not found." } });
        return;
      }
      sendJson(response, 200, { ok: true, data: redactValue(record3) });
      return;
    }
    if (method === "GET" && url.pathname === "/api/history") {
      await ensureHistoryLoaded();
      sendJson(response, 200, {
        ok: true,
        data: {
          items: state.history.map(historySummary).reverse(),
          limit: MAX_HISTORY_ITEMS2
        }
      });
      return;
    }
    const exportMatch = /^\/api\/history\/([0-9a-f-]{36})\/export$/u.exec(url.pathname);
    if (method === "GET" && exportMatch) {
      const record3 = findRecord(exportMatch[1]);
      if (!record3) {
        sendJson(response, 404, { ok: false, error: { code: "VERIFICATION_NOT_FOUND", message: "Verification not found." } });
        return;
      }
      const bodyText = `${JSON.stringify({
        schema_version: 1,
        exported_at: dependencies.now().toISOString(),
        redaction: "credential_fields_and_absolute_user_paths_omitted",
        verification: redactValue(record3)
      }, null, 2)}
`;
      response.writeHead(200, {
        "Content-Type": "application/json; charset=utf-8",
        "Content-Disposition": `attachment; filename="cost-lab-${record3.id}.json"`,
        "Cache-Control": "no-store"
      });
      response.end(bodyText);
      return;
    }
    if (method === "GET" && url.pathname === "/api/start-plan") {
      sendJson(response, 200, {
        ok: true,
        data: {
          status: "START_PLAN_READ_ONLY_BILLING",
          live_test: "AVAILABLE_ON_EXPLICIT_REFRESH",
          billing_api: "/api/billing/startplan/refresh",
          discount: "NOT_VERIFIED",
          execution_button: false,
          reason: "Start Plan exposes read-only official balance access. It does not expose model execution."
        }
      });
      return;
    }
    sendJson(response, 404, {
      ok: false,
      error: { code: "COST_LAB_API_NOT_FOUND", message: "Unknown Cost Lab API route." }
    });
  }
  async function startVerification(body) {
    if (typeof dependencies.verificationRunner !== "function") {
      throw httpError(503, "REAL_VERIFICATION_NOT_CONFIGURED", "The production verification runner is not configured.");
    }
    if (!body || body.confirmation !== CONFIRMATION_PHRASE) {
      throw httpError(400, "REAL_VERIFICATION_CONFIRMATION_REQUIRED", "Explicit verification confirmation is required.");
    }
    if (body.provider !== DEFAULT_PROVIDER_ID || body.model !== "GLM-5.3-Flash" || body.reasoning !== "low") {
      throw httpError(400, "REAL_VERIFICATION_INPUT_REJECTED", "Only the verified Coding Plan provider/model/reasoning tuple is allowed.");
    }
    const taskMode = body.task_mode ?? "marker";
    if (taskMode !== "marker" && taskMode !== "code_edit") {
      throw httpError(400, "REAL_VERIFICATION_TASK_MODE_REJECTED", "task_mode must be marker or code_edit.");
    }
    if (state.closed || state.activeVerificationId) {
      throw httpError(409, "REAL_VERIFICATION_ALREADY_RUNNING", "A real verification is already running or the service is closing.");
    }
    const id = dependencies.createId();
    state.activeVerificationId = id;
    const startedAt = dependencies.now().toISOString();
    const record3 = {
      schema_version: 1,
      id,
      status: "QUEUED",
      started_at: startedAt,
      updated_at: startedAt,
      finished_at: null,
      provider: DEFAULT_PROVIDER_ID,
      model: "GLM-5.3-Flash",
      reasoning: "low",
      task_mode: taskMode,
      billing_window: {
        time_zone: DEFAULT_TIME_ZONE,
        before: null,
        after: null
      },
      model_requests: 0,
      request_usage: null,
      runtime_evidence: null,
      reconciliation: null,
      error: null,
      warnings: [
        "Auxiliary official requests may consume credits.",
        "A clean billing observation window is required."
      ]
    };
    const abortController = new AbortController();
    state.activeAbortController = abortController;
    const enqueue = (async () => {
      await ensureHistoryLoaded();
      assertNotAborted(abortController.signal);
      state.history.push(record3);
      try {
        await persistHistory();
      } catch (error2) {
        state.history = state.history.filter((item) => item !== record3);
        throw error2;
      }
    })();
    const verificationPromise = enqueue.then(() => executeVerification(record3, abortController.signal)).finally(() => {
      if (state.activeVerificationId === id) state.activeVerificationId = null;
      if (state.activeAbortController === abortController) state.activeAbortController = null;
      if (state.activeVerificationPromise === verificationPromise) state.activeVerificationPromise = null;
    });
    state.activeVerificationPromise = verificationPromise;
    void verificationPromise.catch(() => void 0);
    await enqueue;
    return {
      id,
      status: "QUEUED",
      poll_url: `/api/verifications/${id}`,
      confirmation: "REAL_MODEL_REQUEST_AUTHORIZED"
    };
  }
  async function executeVerification(record3, signal) {
    try {
      updateRecord(record3, { status: "RUNNING" });
      await persistHistory();
      const before = await dependencies.captureSnapshot({
        provider: DEFAULT_PROVIDER_ID,
        model: "GLM-5.3-Flash",
        range: "today",
        start: null,
        end: null,
        timeZone: DEFAULT_TIME_ZONE,
        dataRoot: null,
        timeoutMs: 6e4
      });
      assertNotAborted(signal);
      record3.billing_window.before = redactValue(before);
      updateRecord(record3, { status: "MODEL_REQUESTED", model_requests: null });
      await persistHistory();
      const verification = await dependencies.verificationRunner({
        signal,
        provider: DEFAULT_PROVIDER_ID,
        model: "GLM-5.3-Flash",
        reasoning: "low",
        taskMode: record3.task_mode,
        beforeSnapshot: record3.billing_window.before
      });
      assertNotAborted(signal);
      record3.model_requests = Number.isSafeInteger(verification?.model_requests) ? verification.model_requests : null;
      record3.request_usage = redactValue(verification?.usage ?? null);
      record3.runtime_evidence = redactValue(verification?.runtime_evidence ?? null);
      updateRecord(record3, { status: "AWAITING_SETTLEMENT" });
      await persistHistory();
      const { after, reconciliation } = await captureAfterWithRetry(signal, {
        before,
        usage: verification?.usage ?? null,
        hour: Number.isInteger(verification?.hour) ? verification.hour : null
      });
      record3.billing_window.after = redactValue(after);
      record3.reconciliation = redactValue(reconciliation);
      await persistHistoryWithRecordPatch(record3, {
        status: "SUCCEEDED",
        finished_at: dependencies.now().toISOString()
      });
    } catch (error2) {
      const interrupted = signal.aborted;
      const evidence = error2 && typeof error2 === "object" && error2.evidence && typeof error2.evidence === "object" && !Array.isArray(error2.evidence) ? error2.evidence : null;
      if (evidence) {
        record3.model_requests = Number.isSafeInteger(evidence.model_requests) ? evidence.model_requests : null;
        record3.request_usage = redactValue(evidence.usage ?? null);
        record3.runtime_evidence = redactValue(evidence);
        if (evidence.usage && !interrupted) {
          try {
            const { after, reconciliation } = await captureAfterWithRetry(signal, {
              before: record3.billing_window.before,
              usage: evidence.usage,
              hour: Number.isInteger(evidence.hour) ? evidence.hour : null
            });
            record3.billing_window.after = redactValue(after);
            record3.reconciliation = redactValue(reconciliation);
          } catch (billingError) {
            record3.warnings.push(`Post-failure billing capture failed: ${safeErrorCode3(billingError)}`);
          }
        }
      }
      updateRecord(record3, {
        status: interrupted ? "INTERRUPTED" : "FAILED",
        finished_at: dependencies.now().toISOString(),
        error: {
          code: interrupted ? "VERIFICATION_INTERRUPTED" : "VERIFICATION_FAILED",
          message: safeErrorCode3(error2)
        }
      });
    } finally {
      await persistHistory().catch(() => void 0);
    }
  }
  async function captureAfterWithRetry(signal, { before, usage, hour }) {
    let lastError;
    let observation = null;
    for (const delay of dependencies.afterRetryDelaysMs) {
      if (delay > 0) await delayWithSignal(delay, signal);
      assertNotAborted(signal);
      try {
        const snapshot = await dependencies.captureSnapshot({
          provider: DEFAULT_PROVIDER_ID,
          model: "GLM-5.3-Flash",
          range: "today",
          start: null,
          end: null,
          timeZone: DEFAULT_TIME_ZONE,
          dataRoot: null,
          timeoutMs: 6e4
        });
        assertNotAborted(signal);
        if (!usage) {
          return { after: snapshot, reconciliation: inconclusiveBilling("USAGE_MISSING") };
        }
        let reconciliation;
        try {
          reconciliation = reconcileBillingSnapshots(before, snapshot, usage, {
            model: "GLM-5.3-Flash",
            hour
          });
        } catch (error2) {
          return {
            after: snapshot,
            reconciliation: inconclusiveBilling("BILLING_NOT_COMPARABLE", safeErrorCode3(error2))
          };
        }
        observation = { after: snapshot, reconciliation };
        if (reconciliation.calculation.actual_credits !== null) return observation;
      } catch (error2) {
        assertNotAborted(signal);
        lastError = error2;
      }
    }
    return observation ?? {
      after: null,
      reconciliation: inconclusiveBilling("BILLING_UNAVAILABLE", safeErrorCode3(lastError))
    };
  }
  function snapshotOptions(body) {
    if (body !== null && body !== void 0) {
      const keys = Object.keys(body).sort();
      if (keys.length !== 0) throw httpError(400, "BILLING_INPUT_REJECTED", "Billing snapshots use the discovered account context only.");
    }
    return {
      provider: DEFAULT_PROVIDER_ID,
      model: "GLM-5.3-Flash",
      range: "today",
      start: null,
      end: null,
      timeZone: DEFAULT_TIME_ZONE,
      dataRoot: null,
      timeoutMs: 6e4
    };
  }
  function findRecord(id) {
    return state.history.find((record3) => record3.id === id) ?? null;
  }
  function updateRecord(record3, patch) {
    Object.assign(record3, patch, { updated_at: dependencies.now().toISOString() });
  }
  async function ensureHistoryLoaded() {
    if (state.historyLoaded) return;
    try {
      const parsed = JSON.parse(await readFile5(historyPath, "utf8"));
      if (!parsed || parsed.schema_version !== 1 || !Array.isArray(parsed.items)) {
        throw new Error("cost_lab_history_schema_invalid");
      }
      state.history = parsed.items.filter(validHistoryRecord).slice(-MAX_HISTORY_ITEMS2).map(normalizeHistoricReconciliation);
    } catch (error2) {
      if (error2?.code !== "ENOENT") throw error2;
      state.history = [];
    }
    state.historyLoaded = true;
  }
  async function persistHistory() {
    if (state.historyLoaded) {
      trimHistory();
      await atomicWriteJson(historyPath, {
        schema_version: 1,
        updated_at: dependencies.now().toISOString(),
        items: state.history
      });
    }
  }
  async function persistHistoryWithRecordPatch(record3, patch) {
    if (!state.historyLoaded) throw new Error("cost_lab_history_not_loaded");
    trimHistory();
    const updatedAt = dependencies.now().toISOString();
    const items = state.history.map((item) => item === record3 ? { ...item, ...patch, updated_at: updatedAt } : item);
    await atomicWriteJson(historyPath, {
      schema_version: 1,
      updated_at: updatedAt,
      items
    });
    Object.assign(record3, patch, { updated_at: updatedAt });
  }
  function trimHistory() {
    if (state.history.length > MAX_HISTORY_ITEMS2) {
      state.history.splice(0, state.history.length - MAX_HISTORY_ITEMS2);
    }
  }
  return {
    start,
    close,
    address: publicAddress,
    server,
    mountEndpoints,
    handleRequest,
    async inspectEnvironment() {
      return redactValue(await dependencies.inspectEnvironment({ deep: false }));
    },
    async runProtocolProbe() {
      return redactValue(await dependencies.inspectEnvironment({
        deep: true,
        protocolSmoke: dependencies.protocolSmoke
      }));
    }
  };
}
function normalizeApiMountPath(value) {
  if (typeof value !== "string" || !/^\/api\/[a-z0-9][a-z0-9-]*$/u.test(value)) {
    throw new Error("cost_lab_api_mount_path_invalid");
  }
  return value;
}
async function serveStatic(root, definition, method, response) {
  const filePath = path19.join(root, definition.file);
  assertInside2(root, filePath);
  response.writeHead(200, {
    "Content-Type": definition.type,
    "Cache-Control": "no-store"
  });
  if (method === "HEAD") {
    response.end();
    return;
  }
  await new Promise((resolve, reject) => {
    const stream = createReadStream3(filePath);
    stream.once("error", reject);
    stream.once("end", resolve);
    stream.pipe(response);
  });
}
function applySecurityHeaders(response) {
  response.setHeader("Content-Security-Policy", [
    "default-src 'self'",
    "base-uri 'none'",
    "connect-src 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "img-src 'self' data:",
    "object-src 'none'",
    "script-src 'self'",
    "style-src 'self'"
  ].join("; "));
  response.setHeader("Cross-Origin-Opener-Policy", "same-origin");
  response.setHeader("Cross-Origin-Resource-Policy", "same-origin");
  response.setHeader("Referrer-Policy", "no-referrer");
  response.setHeader("X-Content-Type-Options", "nosniff");
  response.setHeader("X-Frame-Options", "DENY");
}
function sendJson(response, status, payload, extraHeaders = {}) {
  const text = `${JSON.stringify(payload)}
`;
  response.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    ...extraHeaders
  });
  response.end(text);
}
async function readJsonBody(request) {
  if (!/^application\/json(?:;|$)/iu.test(request.headers["content-type"] ?? "")) {
    throw httpError(415, "COST_LAB_JSON_REQUIRED", "Content-Type must be application/json.");
  }
  const chunks = [];
  let size = 0;
  for await (const chunk of request) {
    size += chunk.length;
    if (size > MAX_JSON_BYTES) throw httpError(413, "COST_LAB_BODY_TOO_LARGE", "JSON body exceeds 64 KiB.");
    chunks.push(chunk);
  }
  if (size === 0) return null;
  let parsed;
  try {
    parsed = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  } catch {
    throw httpError(400, "COST_LAB_JSON_INVALID", "JSON body is invalid.");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw httpError(400, "COST_LAB_JSON_OBJECT_REQUIRED", "JSON body must be an object.");
  }
  return parsed;
}
function validStateChangingRequest(request, origin, csrfToken) {
  if (request.headers.origin !== origin) return false;
  if (request.headers["x-cost-lab-csrf"] !== csrfToken) return false;
  return request.headers["sec-fetch-site"] === void 0 || request.headers["sec-fetch-site"] === "same-origin";
}
function validHostHeader(request, port) {
  if (!port) return true;
  const host = request.headers.host;
  return host === `${LOOPBACK_HOST}:${port}` || host === `localhost:${port}`;
}
function isLoopbackAddress(address) {
  if (typeof address !== "string") return false;
  return address === "127.0.0.1" || address === "::1" || address === "::ffff:127.0.0.1";
}
function historySummary(record3) {
  const settlementStatus = record3.reconciliation?.settlement_status ?? null;
  return redactValue({
    id: record3.id,
    status: record3.status,
    started_at: record3.started_at,
    finished_at: record3.finished_at,
    provider: record3.provider,
    model: record3.model,
    model_requests: record3.model_requests,
    billing_reconciliation: record3.reconciliation?.billing_reconciliation ?? null,
    credit_class: record3.reconciliation?.credit_class ?? null,
    settlement_status: settlementStatus,
    actual_credits: record3.reconciliation?.calculation?.actual_credits ?? null,
    effective_extra_ratio: record3.reconciliation?.billing_reconciliation === "PASS" ? record3.reconciliation.calculation?.effective_extra_ratio ?? null : null
  });
}
function inconclusiveBilling(settlementStatus, limitation = null) {
  return {
    billing_reconciliation: "INCONCLUSIVE",
    credit_class: "INCONCLUSIVE",
    settlement_status: settlementStatus,
    ...limitation ? { limitation } : {}
  };
}
function normalizeHistoricReconciliation(record3) {
  const reconciliation = record3.reconciliation;
  const { before, after } = record3.billing_window ?? {};
  if (!reconciliation?.calculation) return record3;
  if (reconciliation.schema_version === RECONCILIATION_SCHEMA_VERSION && before?.official_snapshot?.modelUsage?.costLabBillingSource && after?.official_snapshot?.modelUsage?.costLabBillingSource) return record3;
  let updated;
  try {
    updated = reconcileBillingSnapshots(before, after, record3.request_usage ?? reconciliation.request_usage, {
      model: record3.model,
      hour: Number.parseInt(reconciliation.hour, 10)
    });
  } catch (error2) {
    updated = inconclusiveBilling("BILLING_NOT_COMPARABLE", safeErrorCode3(error2));
  }
  return {
    ...record3,
    reconciliation: {
      ...updated,
      ...updated.captured_at ? { captured_at: reconciliation.captured_at } : {}
    }
  };
}
function validHistoryRecord(value) {
  return value && typeof value === "object" && typeof value.id === "string" && /^[0-9a-f-]{36}$/u.test(value.id) && typeof value.status === "string";
}
function assertInside2(root, candidate) {
  const relative = path19.relative(path19.resolve(root), path19.resolve(candidate));
  if (relative === "" || relative.startsWith(`..${path19.sep}`) || relative === ".." || path19.isAbsolute(relative)) {
    throw new Error("cost_lab_path_outside_allowed_root");
  }
}
function httpError(status, code, message) {
  const error2 = new Error(message);
  error2.statusCode = status;
  error2.code = code;
  return error2;
}
function safeErrorCode3(error2) {
  if (error2 && typeof error2 === "object" && "code" in error2 && typeof error2.code === "string") {
    return error2.code.slice(0, 120);
  }
  return sanitizeErrorMessage(error2);
}
function mapStartPlanError(error2) {
  if (Number.isInteger(error2?.statusCode)) return error2;
  const code = typeof error2?.code === "string" ? error2.code : "STARTPLAN_REFRESH_FAILED";
  const message = {
    startplan_billing_timeout: "Official Start Plan billing timed out.",
    startplan_billing_unauthorized: "Official Start Plan authentication was rejected.",
    startplan_billing_forbidden: "Official Start Plan billing access was forbidden.",
    startplan_billing_rate_limited: "Official Start Plan billing rate-limited the request.",
    startplan_authentication_unavailable: "Official Start Plan authentication is unavailable.",
    startplan_official_reader_build_missing: "Build the official Bridge sources before refreshing Start Plan billing.",
    startplan_keyring_lock_present_before_capture: "The official keyring lock was already present; the refresh was not attempted."
  }[code] ?? "Official Start Plan billing refresh failed.";
  const mapped = httpError(
    code === "startplan_official_reader_build_missing" ? 503 : code === "startplan_billing_timeout" ? 504 : code === "startplan_billing_rate_limited" ? 502 : 502,
    code.toUpperCase(),
    message
  );
  mapped.cause = error2;
  return mapped;
}
function assertNotAborted(signal) {
  if (signal.aborted) throw signal.reason ?? new Error("verification_aborted");
}
function delayWithSignal(milliseconds, signal) {
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(signal.reason ?? new Error("verification_aborted"));
      return;
    }
    const timer = setTimeout(resolve, milliseconds);
    signal.addEventListener("abort", () => {
      clearTimeout(timer);
      reject(signal.reason ?? new Error("verification_aborted"));
    }, { once: true });
  });
}
function withTimeout2(promise, milliseconds, code) {
  let timer;
  return Promise.race([
    promise,
    new Promise((_, reject) => {
      timer = setTimeout(() => reject(new Error(code)), milliseconds);
    })
  ]).finally(() => clearTimeout(timer));
}
function loadOptionalVerificationRunner() {
  const fixedModule = path19.join(SCRIPT_ROOT4, "production-verification-runner.mjs");
  return async (input) => {
    let module;
    try {
      module = await import(pathToFileURL6(fixedModule).href);
    } catch (error2) {
      if (error2?.code === "ERR_MODULE_NOT_FOUND") {
        throw httpError(503, "REAL_VERIFICATION_NOT_CONFIGURED", "The production verification runner is not configured.");
      }
      throw error2;
    }
    if (typeof module.runProductionCodingPlanVerification !== "function") {
      throw httpError(503, "REAL_VERIFICATION_NOT_CONFIGURED", "The production verification runner export is missing.");
    }
    return module.runProductionCodingPlanVerification(input);
  };
}
async function main2() {
  const port = Number(process.env.COST_LAB_PORT ?? 0);
  if (!Number.isInteger(port) || port < 0 || port > 65535) {
    throw new Error("COST_LAB_PORT must be an integer between 0 and 65535");
  }
  const app = createCostLabWebServer({ port });
  const address = await app.start();
  process.stdout.write(`Cost Lab Web: ${address.url}
`);
  process.stdout.write("Press Ctrl+C to stop. Bound to 127.0.0.1 only.\n");
  const shutdown = async () => {
    try {
      await app.close();
    } catch (error2) {
      process.stderr.write(`Cost Lab shutdown: ${safeErrorCode3(error2)}; inspect persisted verification history.
`);
      process.exitCode = 1;
    }
  };
  process.once("SIGINT", shutdown);
  process.once("SIGTERM", shutdown);
}
if (process.argv[1] && import.meta.url === pathToFileURL6(path19.resolve(process.argv[1])).href) {
  await main2();
}

// src/web/cost-lab-integration.ts
function createUnifiedCostLabApplication(options) {
  const layout = consoleLayout(options.moduleUrl);
  const inspectRuntime = (input = {}) => inspectInstalledRuntime(input);
  const protocolSmoke = (input = {}) => runOfficialAppServerProtocolSmoke({
    ...input,
    projectRoot: layout.costLabProjectRoot,
    hostModulePath: layout.officialHostModule,
    runRootParent: path20.join(options.dataRoot, ".run"),
    inspectRuntime
  });
  const readStartPlanBilling = async ({ signal } = {}) => {
    const data = resolveBillingDataBaseDir(null, {
      env: process.env,
      platform: process.platform
    });
    return readOfficialStartPlanBilling({
      projectRoot: layout.costLabProjectRoot,
      dataBaseDir: data.dataBaseDir,
      officialHostWorker: layout.officialHostWorker,
      signal,
      officialDependencies: {
        StartPlanBillingEntitlement,
        loadOfficialHostProductVersion,
        loadOfficialStartPlanAuthenticationResolverFactory
      }
    });
  };
  return createCostLabWebServer({
    projectRoot: layout.costLabProjectRoot,
    evidenceRoot: path20.join(options.dataRoot, ".run"),
    historyPath: path20.join(options.dataRoot, ".run", "cost-lab-web", "history.json"),
    startPlanHistoryPath: path20.join(options.dataRoot, ".run", "cost-lab-web", "startplan-history.json"),
    apiMountPath: "/api/cost-lab",
    officialHostWorker: layout.officialHostWorker,
    inspectEnvironment: (input = {}) => inspectCostLabEnvironment({ ...input, inspectRuntime }),
    protocolSmoke,
    readStartPlanBilling
  });
}
function resolveConsoleProjectRoot(moduleUrl) {
  return consoleLayout(moduleUrl).costLabProjectRoot;
}
function consoleLayout(moduleUrl) {
  const moduleDirectory = path20.dirname(fileURLToPath8(moduleUrl));
  const bundleRoot = path20.basename(moduleDirectory) === "dist" && existsSync6(path20.join(path20.dirname(moduleDirectory), "worker", "worker-main.mjs")) ? path20.dirname(moduleDirectory) : null;
  if (bundleRoot) {
    return {
      costLabProjectRoot: bundleRoot,
      officialHostWorker: path20.join(bundleRoot, "worker", "worker-main.mjs"),
      officialHostModule: path20.join(
        bundleRoot,
        "worker",
        "vendor",
        "official-host",
        "win32-x64-node24.16.0-zcode3.18.2-fec97590",
        "official-host-runtime.mjs"
      )
    };
  }
  const repositoryRoot = findRepositoryRoot(moduleDirectory);
  const pluginRoot = path20.join(repositoryRoot, "plugins", "codex-zcode-bridge");
  return {
    costLabProjectRoot: repositoryRoot,
    officialHostWorker: path20.join(pluginRoot, "worker", "worker-main.mjs"),
    officialHostModule: path20.join(
      pluginRoot,
      "worker",
      "vendor",
      "official-host",
      "win32-x64-node24.16.0-zcode3.18.2-fec97590",
      "official-host-runtime.mjs"
    )
  };
}
function findRepositoryRoot(start) {
  let current = path20.resolve(start);
  for (; ; ) {
    if (existsSync6(path20.join(current, "plugins", "codex-zcode-bridge", "worker", "worker-main.mjs"))) {
      return current;
    }
    const parent = path20.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  throw new Error("cost_lab_repository_root_unavailable");
}
async function inspectInstalledRuntime(input = {}) {
  const runtime = await new OfficialAppServerRuntimeResolver({
    env: input.env,
    platform: input.platform,
    architecture: input.arch
  }).inspect();
  const root = runtime.install_dir;
  const assets = {};
  for (const name of ["bundle", "runtime_host", "builtin_provider_config"]) {
    const file = runtime[`${name}_path`];
    if (root && typeof file === "string") {
      assets[name] = {
        relative_path: path20.relative(root, file).split(path20.sep).join("/"),
        bytes: runtime[`${name}_bytes`],
        sha256: runtime[`${name}_sha256`]
      };
    }
  }
  return {
    install_root: root,
    install_source: runtime.install_source,
    install_root_fingerprint: root ? createHash10("sha256").update(root).digest("hex") : null,
    runtime_status: runtime.status,
    installation_safety: runtime.installation_safety ?? "OFFICIAL_INSTALLATION_INCOMPLETE",
    installation_fingerprint: runtime.installation_fingerprint ?? null,
    discount_status: runtime.discount_capability,
    desktop_version: runtime.desktop_version,
    desktop_app_version: runtime.desktop_app_version ?? null,
    desktop_build_commit_id: runtime.desktop_build_commit_id ?? null,
    node_executable: runtime.node_executable,
    reason: runtime.reason,
    manifest: runtime.manifest && { ...runtime.manifest, version: runtime.manifest.desktop_version },
    desktop_executable: runtime.desktop_executable_path ? {
      bytes: runtime.desktop_executable_bytes,
      sha256: runtime.desktop_executable_sha256,
      signer_subject: runtime.desktop_executable_signer_subject,
      signer_thumbprint: runtime.desktop_executable_signer_thumbprint
    } : null,
    desktop_archive: runtime.desktop_archive_path ? {
      bytes: runtime.desktop_archive_bytes,
      sha256: runtime.desktop_archive_sha256
    } : null,
    runtime_host_signer: {
      subject: runtime.runtime_host_signer_subject ?? null,
      thumbprint: runtime.runtime_host_signer_thumbprint ?? null
    },
    assets
  };
}

// src/web/runtime-compatibility.ts
import { createHash as createHash11, randomUUID as randomUUID7 } from "node:crypto";
import { existsSync as existsSync7, lstatSync as lstatSync2, mkdirSync as mkdirSync2, readFileSync as readFileSync5, renameSync, writeFileSync } from "node:fs";
import path21 from "node:path";
var STORE_SCHEMA_VERSION = 1;
var EVIDENCE_SCHEMA_VERSION = 1;
var MAX_EVIDENCE_RECORDS = 200;
var RuntimeCompatibilityError = class extends Error {
  constructor(code, message, status = 409) {
    super(message);
    this.code = code;
    this.name = "RuntimeCompatibilityError";
    this.status = status;
  }
  code;
  status;
};
var RuntimeCompatibilityService = class {
  #historyPath;
  #inspectEnvironment;
  #runProtocolProbe;
  #now;
  #createId;
  constructor(options) {
    this.#historyPath = path21.resolve(
      options.historyPath ?? path21.join(options.projectRoot, ".run", "bridge-console", "runtime-compatibility.json")
    );
    this.#inspectEnvironment = options.inspectEnvironment;
    this.#runProtocolProbe = options.runProtocolProbe;
    this.#now = options.now ?? (() => /* @__PURE__ */ new Date());
    this.#createId = options.createId ?? randomUUID7;
  }
  async inspect() {
    const environment = await this.#readEnvironment(this.#inspectEnvironment);
    const installation = installationIdentity(environment);
    const fingerprint = stringValue(recordValue(environment.zcode), "installation_fingerprint");
    if (!fingerprint) {
      throw new RuntimeCompatibilityError(
        "RUNTIME_FINGERPRINT_UNAVAILABLE",
        "The exact installed Runtime fingerprint is unavailable.",
        503
      );
    }
    const store = this.#readStore();
    const previous = previousDistinctFingerprint(store.records, fingerprint);
    const staticResult = installation.installation_safety === "OFFICIAL_INSTALLATION_SAFE" ? "PASS" : installation.installation_safety === "OFFICIAL_INSTALLATION_UNSAFE" ? "FAIL" : "INCOMPLETE";
    const staticEvidence = this.#recordStatic({
      fingerprint,
      installation,
      result: staticResult,
      environment
    });
    const updated = this.#appendDeduplicated(store, staticEvidence);
    return buildSnapshot({
      capturedAt: this.#now().toISOString(),
      fingerprint,
      installation,
      records: updated.records,
      environment,
      previous
    });
  }
  async runAuthorizedProtocolProbe() {
    const before = await this.#readEnvironment(this.#inspectEnvironment);
    const installation = installationIdentity(before);
    const fingerprint = stringValue(recordValue(before.zcode), "installation_fingerprint");
    if (!fingerprint) {
      throw new RuntimeCompatibilityError(
        "RUNTIME_FINGERPRINT_UNAVAILABLE",
        "The exact installed Runtime fingerprint is unavailable.",
        503
      );
    }
    if (installation.installation_safety !== "OFFICIAL_INSTALLATION_SAFE") {
      throw new RuntimeCompatibilityError(
        "RUNTIME_UNSAFE",
        "Protocol probing is unavailable until the installation passes the safety gate.",
        403
      );
    }
    const probed = await this.#readEnvironment(this.#runProtocolProbe, "RUNTIME_PROBE_UNAVAILABLE");
    const protocol = recordValue(probed.appserver_protocol_smoke);
    const status = stringValue(protocol, "status");
    if (status !== "PASS" && status !== "FAIL") {
      throw new RuntimeCompatibilityError(
        "RUNTIME_PROBE_UNAVAILABLE",
        "The zero-model protocol probe did not return a terminal verdict.",
        502
      );
    }
    const evidence = this.#recordProtocol({
      fingerprint,
      installation,
      result: status,
      protocol
    });
    const storeBefore = this.#readStore();
    const previous = previousDistinctFingerprint(storeBefore.records, fingerprint);
    const store = this.#appendDeduplicated(storeBefore, evidence);
    return buildSnapshot({
      capturedAt: this.#now().toISOString(),
      fingerprint,
      installation,
      records: store.records,
      environment: probed,
      previous
    });
  }
  async candidateReport() {
    const snapshot = await this.inspect();
    if (!snapshot.fingerprint || !snapshot.installation) {
      throw new RuntimeCompatibilityError("RUNTIME_FINGERPRINT_UNAVAILABLE", "No Runtime identity is available.");
    }
    return {
      schema_version: 1,
      kind: "runtime_compatibility_candidate",
      generated_at: this.#now().toISOString(),
      fingerprint: snapshot.fingerprint,
      installation: snapshot.installation,
      detected_changes: snapshot.changed_assets,
      capabilities: snapshot.capabilities,
      evidence: snapshot.evidence,
      manifest_candidate: {
        desktop_version: snapshot.installation.desktop_version,
        desktop_app_version: snapshot.installation.desktop_app_version,
        desktop_build_commit_id: snapshot.installation.desktop_build_commit_id,
        bundle_sha256: snapshot.installation.assets.bundle?.sha256 ?? null,
        builtin_provider_config_sha256: snapshot.installation.assets.builtin_provider_config?.sha256 ?? null,
        runtime_host_sha256: snapshot.installation.assets.runtime_host?.sha256 ?? null,
        verification_stage: "CANDIDATE"
      },
      approval: {
        production_manifest_modified: false,
        experimental_promoted: false,
        provider_authorization_granted: false,
        owner_review_required: true
      },
      limitations: [
        "This report is generated from the current fingerprint only.",
        "Static or protocol evidence does not verify provider execution or billing.",
        "No production compatibility manifest was modified."
      ]
    };
  }
  #recordStatic(input) {
    return sealEvidence({
      schema_version: EVIDENCE_SCHEMA_VERSION,
      evidence_id: this.#createId(),
      fingerprint: input.fingerprint,
      captured_at: this.#now().toISOString(),
      installation: input.installation,
      probe_type: "static",
      probe_scope: "installation/safety",
      result: input.result,
      classification: String(input.installation.installation_safety),
      provider: null,
      model: null,
      evidence_source: "OfficialAppServerRuntimeResolver",
      limitations: [
        "Static inspection does not create a model session.",
        "Static PASS does not prove Provider execution, billing, or discount compatibility."
      ]
    });
  }
  #recordProtocol(input) {
    return sealEvidence({
      schema_version: EVIDENCE_SCHEMA_VERSION,
      evidence_id: this.#createId(),
      fingerprint: input.fingerprint,
      captured_at: this.#now().toISOString(),
      installation: input.installation,
      probe_type: "protocol",
      probe_scope: "runtime/capabilities",
      result: input.result,
      classification: input.result === "PASS" ? "PROTOCOL_PASS" : "PROTOCOL_FAIL",
      provider: null,
      model: null,
      evidence_source: "Official AppServer protocol smoke",
      limitations: [
        "The probe creates no session and sends no model request.",
        "Protocol PASS does not elevate Coding Plan, Start Plan, or other Provider capabilities.",
        input.result === "PASS" ? "The probe verified bounded process disposal after the capability response." : "Cleanup and Provider capabilities remain unverified after a failed probe."
      ]
    });
  }
  #appendDeduplicated(store, record3) {
    const latest2 = store.records.at(-1);
    const duplicate = store.records.find((item) => item.fingerprint === record3.fingerprint && (item.evidence_digest === record3.evidence_digest || evidenceSemanticDigest(item) === record3.evidence_digest));
    if (latest2?.fingerprint === record3.fingerprint && duplicate) return store;
    const retained = duplicate ? store.records.filter((item) => item.evidence_id !== duplicate.evidence_id) : store.records;
    const next = {
      schema_version: STORE_SCHEMA_VERSION,
      updated_at: this.#now().toISOString(),
      records: [...retained, record3].slice(-MAX_EVIDENCE_RECORDS)
    };
    this.#writeStore(next);
    return next;
  }
  #readStore() {
    if (!existsSync7(this.#historyPath)) {
      return { schema_version: STORE_SCHEMA_VERSION, updated_at: this.#now().toISOString(), records: [] };
    }
    try {
      const metadata = lstatSync2(this.#historyPath);
      if (!metadata.isFile() || metadata.isSymbolicLink() || metadata.size > 4 * 1024 * 1024) {
        throw new Error("unsafe_store");
      }
      const parsed = JSON.parse(readFileSync5(this.#historyPath, "utf8"));
      if (parsed.schema_version !== STORE_SCHEMA_VERSION || !Array.isArray(parsed.records)) {
        throw new Error("schema_invalid");
      }
      const records = parsed.records.filter(validEvidenceRecord).slice(-MAX_EVIDENCE_RECORDS);
      if (records.length !== parsed.records.length) throw new Error("record_invalid");
      return {
        schema_version: STORE_SCHEMA_VERSION,
        updated_at: typeof parsed.updated_at === "string" ? parsed.updated_at : this.#now().toISOString(),
        records
      };
    } catch (error2) {
      throw new RuntimeCompatibilityError(
        "RUNTIME_EVIDENCE_STORE_INVALID",
        `Runtime evidence store is invalid: ${error2 instanceof Error ? error2.message : String(error2)}`,
        500
      );
    }
  }
  #writeStore(store) {
    const parent = path21.dirname(this.#historyPath);
    if (!existsSync7(parent)) mkdirSync2(parent, { recursive: true });
    const temporary = `${this.#historyPath}.new-${this.#createId()}`;
    writeFileSync(temporary, `${JSON.stringify(store, null, 2)}
`, { encoding: "utf8", flag: "wx" });
    renameSync(temporary, this.#historyPath);
  }
  async #readEnvironment(inspect, code = "RUNTIME_INSPECTION_FAILED") {
    try {
      const environment = await inspect();
      if (!recordValue(environment.zcode)) throw new Error("zcode_identity_missing");
      return environment;
    } catch (error2) {
      if (error2 instanceof RuntimeCompatibilityError) throw error2;
      throw new RuntimeCompatibilityError(
        code,
        `Runtime ${code === "RUNTIME_PROBE_UNAVAILABLE" ? "probe" : "inspection"} failed: ` + (error2 instanceof Error ? error2.message : String(error2)),
        code === "RUNTIME_PROBE_UNAVAILABLE" ? 502 : 503
      );
    }
  }
};
function buildSnapshot(input) {
  const currentEvidence = input.records.filter((record3) => record3.fingerprint === input.fingerprint);
  const previousFingerprint = input.previous?.fingerprint ?? null;
  const changedAssets = currentAssetChanges(input.installation, input.previous?.installation ?? null);
  const capabilities = capabilityMatrix(input.installation, currentEvidence);
  const zcode = recordValue(input.environment.zcode);
  const warnings = Array.isArray(input.environment.warnings) ? input.environment.warnings.filter((item) => typeof item === "string") : [];
  if (previousFingerprint !== null && previousFingerprint !== input.fingerprint) {
    warnings.unshift("RUNTIME_CHANGED");
  }
  return {
    schema_version: 1,
    captured_at: input.capturedAt,
    fingerprint: input.fingerprint,
    installation: input.installation,
    runtime_changed: previousFingerprint !== null && previousFingerprint !== input.fingerprint,
    previous_fingerprint: previousFingerprint,
    changed_assets: changedAssets,
    warnings,
    capabilities,
    evidence: currentEvidence.slice().reverse(),
    evidence_count: currentEvidence.length,
    manifest_modified: false,
    model_requests: 0,
    ...stringValue(zcode, "reason") ? { reason: stringValue(zcode, "reason") } : {}
  };
}
function installationIdentity(environment) {
  const zcode = recordValue(environment.zcode);
  const host = recordValue(environment.host);
  const manifest = recordValue(zcode.manifest);
  const assets = recordValue(zcode.assets);
  const desktopExecutable = recordValue(zcode.desktop_executable);
  const desktopArchive = recordValue(zcode.desktop_archive);
  const normalizedAssets = {};
  for (const name of ["bundle", "runtime_host", "builtin_provider_config"]) {
    const value = recordValue(assets[name]);
    normalizedAssets[name] = {
      bytes: safeInteger(value.bytes),
      sha256: shaString(value.sha256)
    };
  }
  normalizedAssets.desktop_executable = {
    bytes: safeInteger(desktopExecutable.bytes),
    sha256: shaString(desktopExecutable.sha256)
  };
  normalizedAssets.desktop_archive = {
    bytes: safeInteger(desktopArchive.bytes),
    sha256: shaString(desktopArchive.sha256)
  };
  const runtimeStatus = stringValue(zcode, "runtime_status") ?? "OFFICIAL_RUNTIME_UNVERIFIED";
  return {
    desktop_version: stringValue(zcode, "version") ?? stringValue(zcode, "desktop_version"),
    desktop_app_version: stringValue(zcode, "desktop_app_version"),
    desktop_build_commit_id: stringValue(zcode, "desktop_build_commit_id"),
    node_version: stringValue(host, "node_version"),
    installation_safety: stringValue(zcode, "installation_safety") ?? "OFFICIAL_INSTALLATION_INCOMPLETE",
    runtime_status: runtimeStatus,
    manifest_status: runtimeStatus === "OFFICIAL_RUNTIME_VERIFIED" ? "VERIFIED" : runtimeStatus === "OFFICIAL_RUNTIME_EXPERIMENTAL" ? "EXPERIMENTAL" : "UNVERIFIED",
    assets: normalizedAssets
  };
}
function capabilityMatrix(installation, evidence) {
  const staticEvidence = latest(evidence, (item) => item.probe_type === "static");
  const protocolEvidence = latest(evidence, (item) => item.probe_type === "protocol");
  const codingPlanEvidence = latest(evidence, (item) => item.probe_type === "real_provider" && item.provider === "account:bigmodel-individual-coding-plan");
  const startPlanEvidence = latest(evidence, (item) => item.probe_type === "real_provider" && item.provider === "account:bigmodel-start-plan");
  const otherProviderEvidence = latest(evidence, (item) => item.probe_type === "real_provider" && item.provider !== null && !["account:bigmodel-individual-coding-plan", "account:bigmodel-start-plan"].includes(item.provider));
  const billingEvidence = latest(evidence, (item) => item.probe_type === "billing" && item.provider === "account:bigmodel-individual-coding-plan");
  return {
    installation_safety: capability(
      installation.installation_safety === "OFFICIAL_INSTALLATION_SAFE" ? "SAFE" : installation.installation_safety === "OFFICIAL_INSTALLATION_UNSAFE" ? "UNSAFE" : "INCOMPLETE",
      staticEvidence,
      "Official installation safety inspection"
    ),
    manifest_compatibility: capability(
      installation.manifest_status,
      staticEvidence,
      "Exact Runtime compatibility manifest"
    ),
    protocol: evidenceCapability(protocolEvidence, "No authorized zero-model protocol evidence exists."),
    coding_plan_execution: evidenceCapability(
      codingPlanEvidence,
      "No Coding Plan provider execution evidence exists."
    ),
    coding_plan_billing: billingCapability(billingEvidence),
    start_plan_execution: evidenceCapability(
      startPlanEvidence,
      "No Start Plan execution evidence exists."
    ),
    other_providers: evidenceCapability(
      otherProviderEvidence,
      "No other Provider execution evidence exists."
    ),
    cleanup: protocolEvidence?.result === "PASS" ? capability("VERIFIED", protocolEvidence, "Authorized protocol probe disposed its bounded runtime processes") : evidenceCapability(null, "No runtime cleanup evidence exists.")
  };
}
function evidenceCapability(record3, limitation) {
  if (!record3) return capability("NOT_RUN", null, "No matching evidence", limitation);
  return capability(
    record3.result === "PASS" ? "PASS" : record3.result === "INCOMPLETE" ? "INCONCLUSIVE" : "FAIL",
    record3,
    record3.evidence_source,
    record3.limitations[0] ?? null
  );
}
function billingCapability(record3) {
  if (!record3) {
    return capability(
      "NOT_RUN",
      null,
      "No matching evidence",
      "No attributable Coding Plan billing evidence exists."
    );
  }
  const verified = record3.result === "PASS" && /^(?:VERIFIED|BILLING_VERIFIED)$/iu.test(record3.classification);
  return capability(
    verified ? "VERIFIED" : record3.result === "FAIL" ? "FAIL" : "INCONCLUSIVE",
    record3,
    record3.evidence_source,
    record3.limitations[0] ?? null
  );
}
function capability(status, evidence, source, limitation = null) {
  return {
    status,
    evidence_id: evidence?.evidence_id ?? null,
    source,
    limitation
  };
}
function latest(records, predicate) {
  return [...records].reverse().find(predicate) ?? null;
}
function previousDistinctFingerprint(records, fingerprint) {
  const last = records.at(-1);
  if (!last || last.fingerprint === fingerprint) return null;
  return [...records].reverse().find((record3) => record3.fingerprint === last.fingerprint) ?? last;
}
function currentAssetChanges(current, previous) {
  if (!previous) return [];
  const changes = [];
  for (const key of /* @__PURE__ */ new Set([...Object.keys(current.assets), ...Object.keys(previous.assets)])) {
    if (current.assets[key]?.sha256 !== previous.assets[key]?.sha256 || current.assets[key]?.bytes !== previous.assets[key]?.bytes) {
      changes.push(key);
    }
  }
  if (current.desktop_version !== previous.desktop_version) changes.push("desktop_version");
  if (current.desktop_app_version !== previous.desktop_app_version) changes.push("desktop_app_version");
  if (current.desktop_build_commit_id !== previous.desktop_build_commit_id) changes.push("desktop_build_commit_id");
  if (current.node_version !== previous.node_version) changes.push("node_version");
  return changes.sort();
}
function sealEvidence(value) {
  const digest = evidenceSemanticDigest(value);
  return { ...value, evidence_digest: digest };
}
function evidenceSemanticDigest(value) {
  return createHash11("sha256").update(canonicalJson({
    schema_version: value.schema_version,
    fingerprint: value.fingerprint,
    installation: value.installation,
    probe_type: value.probe_type,
    probe_scope: value.probe_scope,
    result: value.result,
    classification: value.classification,
    provider: value.provider,
    model: value.model,
    evidence_source: value.evidence_source,
    limitations: value.limitations
  }), "utf8").digest("hex");
}
function validEvidenceRecord(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const record3 = value;
  if (record3.schema_version !== EVIDENCE_SCHEMA_VERSION || typeof record3.evidence_id !== "string" || record3.evidence_id.length < 1 || typeof record3.fingerprint !== "string" || !/^[0-9a-f]{64}$/u.test(record3.fingerprint) || typeof record3.captured_at !== "string" || !["static", "protocol", "real_provider", "billing"].includes(record3.probe_type ?? "") || typeof record3.probe_scope !== "string" || !["PASS", "FAIL", "INCOMPLETE"].includes(record3.result ?? "") || typeof record3.classification !== "string" || typeof record3.evidence_source !== "string" || typeof record3.evidence_digest !== "string" || !/^[0-9a-f]{64}$/u.test(record3.evidence_digest) || !Array.isArray(record3.limitations)) {
    return false;
  }
  const { evidence_digest: digest, ...body } = record3;
  const legacyDigest = createHash11("sha256").update(canonicalJson(body), "utf8").digest("hex");
  return evidenceSemanticDigest(body) === digest || legacyDigest === digest;
}
function canonicalJson(value) {
  return JSON.stringify(sortObject(value)) ?? "null";
}
function sortObject(value) {
  if (Array.isArray(value)) return value.map(sortObject);
  if (value === null || typeof value !== "object" || value instanceof Date) return value;
  if (Object.getPrototypeOf(value) !== Object.prototype && Object.getPrototypeOf(value) !== null) return value;
  return Object.fromEntries(Object.entries(value).sort(([left], [right]) => left < right ? -1 : left > right ? 1 : 0).map(([key, item]) => [key, sortObject(item)]));
}
function recordValue(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}
function stringValue(record3, key) {
  const value = record3[key];
  return typeof value === "string" && value.length > 0 ? value : null;
}
function safeInteger(value) {
  return Number.isSafeInteger(value) && Number(value) >= 0 ? Number(value) : null;
}
function shaString(value) {
  return typeof value === "string" && /^[0-9a-f]{64}$/iu.test(value) ? value.toLowerCase() : null;
}

// src/web/server.ts
import { randomBytes as randomBytes2, randomUUID as randomUUID10 } from "node:crypto";
import http2 from "node:http";

// src/runtime/auto-wake-setting.ts
import { randomUUID as randomUUID9 } from "node:crypto";
import { mkdir as mkdir4, readFile as readFile6, rm as rm3, stat as stat4, writeFile as writeFile2 } from "node:fs/promises";
import path23 from "node:path";

// src/store/atomic-rename.ts
import { rename as rename2 } from "node:fs/promises";
function retryable(error2, deadline) {
  return process.platform === "win32" && Date.now() < deadline && ["EPERM", "EBUSY", "EACCES"].includes(error2.code ?? "");
}
async function atomicRename(source, target) {
  const deadline = Date.now() + 2e3;
  while (true) {
    try {
      await rename2(source, target);
      return;
    } catch (error2) {
      if (!retryable(error2, deadline)) throw error2;
      await new Promise((resolve) => setTimeout(resolve, 10));
    }
  }
}

// src/store/process-lock.ts
import { existsSync as existsSync8, mkdirSync as mkdirSync3, readFileSync as readFileSync6, renameSync as renameSync2, rmdirSync, statSync as statSync2, unlinkSync, writeFileSync as writeFileSync2 } from "node:fs";
import { spawnSync } from "node:child_process";
import { randomUUID as randomUUID8 } from "node:crypto";
import path22 from "node:path";
function parseLockOwner(raw) {
  try {
    const owner = JSON.parse(raw);
    return Number.isSafeInteger(owner?.pid) && owner.pid > 0 && typeof owner.identity?.fingerprint === "string" && owner.identity.fingerprint.length > 0 && owner.identity.identity_version === 1 && owner.identity.platform === process.platform ? owner : null;
  } catch {
    return null;
  }
}
function processStartEvidence(pid) {
  if (pid === process.pid && cachedStartFingerprint !== void 0) {
    return { state: "live", fingerprint: cachedStartFingerprint };
  }
  let evidence = { state: "unknown" };
  try {
    if (process.platform === "linux") {
      try {
        const stat5 = readFileSync6(`/proc/${pid}/stat`, "utf8");
        const fingerprint = stat5.slice(stat5.lastIndexOf(")") + 2).split(" ")[19]?.trim();
        evidence = fingerprint ? { state: "live", fingerprint } : { state: "unknown" };
      } catch (error2) {
        if (error2.code === "ENOENT") evidence = { state: "absent" };
      }
    } else if (process.platform === "darwin") {
      const timeout = pid === process.pid ? 15e3 : 5e3;
      const query = spawnSync("ps", ["-o", "pid=,lstart=", "-p", String(pid)], {
        encoding: "utf8",
        timeout,
        windowsHide: true,
        shell: false
      });
      const row = query.status === 0 ? query.stdout.split(/\r?\n/u).find((line) => line.trim()) : void 0;
      evidence = query.status !== 0 ? { state: "unknown" } : row ? { state: "live", fingerprint: row.trim().split(/\s+/u).slice(1).join(" ") } : { state: "absent" };
    } else if (process.platform === "win32") {
      const systemRoot = Object.entries(process.env).find(([key]) => key.toLowerCase() === "systemroot")?.[1];
      const executable = systemRoot ? `${systemRoot}\\System32\\WindowsPowerShell\\v1.0\\powershell.exe` : "powershell.exe";
      const timeout = pid === process.pid ? 15e3 : 5e3;
      const query = spawnSync(executable, [
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        `$p=$null; try { $p=[System.Diagnostics.Process]::GetProcessById(${pid}); [Console]::Out.Write($p.StartTime.Ticks) } catch [System.ArgumentException] { [Console]::Out.Write('bridge_pid_absent_v1') }`
      ], {
        encoding: "utf8",
        timeout,
        windowsHide: true,
        shell: false
      });
      const output = query.status === 0 ? query.stdout.trim() : "";
      evidence = output === "bridge_pid_absent_v1" ? { state: "absent" } : /^[0-9]+$/u.test(output) ? { state: "live", fingerprint: output } : { state: "unknown" };
    }
  } catch {
    evidence = { state: "unknown" };
  }
  if (pid === process.pid && evidence.state === "live") cachedStartFingerprint = evidence.fingerprint;
  return evidence;
}
var selfIdentity = null;
var cachedStartFingerprint;
var SELF_IDENTITY_PROBE_ATTEMPTS = 2;
var SELF_IDENTITY_RETRY_MS = 50;
function createSelfIdentityResolver(probe = processStartEvidence) {
  let identity = null;
  return function resolveSelfIdentity2() {
    if (identity) return identity;
    for (let attempt = 0; attempt < SELF_IDENTITY_PROBE_ATTEMPTS; attempt += 1) {
      const evidence = probe(process.pid);
      if (evidence.state === "live") {
        identity = {
          pid: process.pid,
          fingerprint: evidence.fingerprint,
          fingerprint_precision: "exact",
          identity_version: 1,
          platform: process.platform,
          captured_at: (/* @__PURE__ */ new Date()).toISOString()
        };
        return identity;
      }
      if (attempt + 1 < SELF_IDENTITY_PROBE_ATTEMPTS) pauseBriefly(SELF_IDENTITY_RETRY_MS);
    }
    return null;
  };
}
var TRANSIENT_LOCK_FS_CODES = /* @__PURE__ */ new Set(["EEXIST", "EPERM", "EACCES", "EBUSY", "ENOTEMPTY"]);
var DESTINATION_PRESENT_CONTENTION_CODES = /* @__PURE__ */ new Set(["EEXIST", "ENOTEMPTY"]);
var PUBLICATION_RETRY_PAUSE_MS = 50;
var PUBLICATION_RETRY_MS = 5e3;
var WITHDRAW_RETRY_MS = 5e3;
var SHARED_GUARD_RETRY_MS = 2e3;
var PRIVATE_CLEANUP_RETRY_MS = 1e3;
var RETRY_PAUSE_MS = 10;
function isTransientLockFsError(error2) {
  return TRANSIENT_LOCK_FS_CODES.has(error2?.code ?? "");
}
function pauseBriefly(delayMs = RETRY_PAUSE_MS) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, delayMs);
}
var resolveSelfIdentity = createSelfIdentityResolver();
function currentSelfIdentity() {
  if (!selfIdentity) selfIdentity = resolveSelfIdentity();
  return selfIdentity;
}
async function withProcessLock(directory, operation, timeoutMs = 3e4) {
  const deadline = Date.now() + timeoutMs;
  let release;
  while (!(release = tryAcquireProcessLock(directory))) {
    if (Date.now() >= deadline) {
      const owner = describeLockOwner(directory);
      throw new Error(`timed out waiting for process lock: ${directory}${owner ? ` (live owner: ${owner})` : ""}`);
    }
    await new Promise((resolve) => setTimeout(resolve, 25));
  }
  try {
    return await operation();
  } finally {
    release();
  }
}
function describeLockOwner(directory) {
  try {
    const owner = JSON.parse(readFileSync6(path22.join(directory, "owner.json"), "utf8"));
    if (!Number.isSafeInteger(owner.pid)) return null;
    return `pid ${String(owner.pid)}${owner.started_at ? `, started ${owner.started_at}` : ""}`;
  } catch {
    return null;
  }
}
function tryAcquireProcessLock(directory) {
  return tryAcquireProcessLockWithRetry(directory, Date.now() + PUBLICATION_RETRY_MS);
}
function tryAcquireProcessLockWithRetry(directory, deadline) {
  const token = randomUUID8();
  if (existsSync8(directory)) return acquireExistingLock(directory);
  const staging = `${directory}.${process.pid}.${token}.pending`;
  const ownerRecord = {
    pid: process.pid,
    token,
    started_at: (/* @__PURE__ */ new Date()).toISOString(),
    identity: currentSelfIdentity() ? { fingerprint: currentSelfIdentity().fingerprint, identity_version: currentSelfIdentity().identity_version, platform: currentSelfIdentity().platform } : null
  };
  try {
    mkdirSync3(staging, { mode: 448 });
    writeFileSync2(path22.join(staging, "owner.json"), JSON.stringify(ownerRecord), { mode: 384, flag: "wx" });
    try {
      renameSync2(staging, directory);
    } catch (error2) {
      removeStagedLock(staging);
      const code = error2.code;
      if (!isTransientLockFsError(error2)) throw error2;
      if (DESTINATION_PRESENT_CONTENTION_CODES.has(code ?? "") || existsSync8(directory)) {
        return acquireExistingLock(directory);
      }
      if (Date.now() < deadline) {
        pauseBriefly(PUBLICATION_RETRY_PAUSE_MS);
        return tryAcquireProcessLockWithRetry(directory, deadline);
      }
      throw error2;
    }
  } catch (error2) {
    removeStagedLock(staging);
    throw error2;
  }
  return () => {
    const owner = JSON.parse(readFileSync6(path22.join(directory, "owner.json"), "utf8"));
    if (owner.token !== token) throw new Error("process lock ownership changed");
    const retired = `${directory}.${token}.retired`;
    renameWithTransientRetry(directory, retired);
    removeStagedLock(retired);
  };
}
function renameWithTransientRetry(source, target) {
  const deadline = Date.now() + WITHDRAW_RETRY_MS;
  while (true) {
    try {
      renameSync2(source, target);
      return;
    } catch (error2) {
      if (!isTransientLockFsError(error2) || Date.now() >= deadline) throw error2;
      pauseBriefly();
    }
  }
}
function acquireExistingLock(directory) {
  let owner;
  try {
    owner = parseLockOwner(readFileSync6(path22.join(directory, "owner.json"), "utf8"));
  } catch {
    try {
      if (Date.now() - statSync2(directory).mtimeMs > 3e4) throw new Error(`unreadable lock owner: ${directory}`);
    } catch (failure3) {
      if (failure3.code !== "ENOENT") throw failure3;
    }
    return null;
  }
  if (!owner) return null;
  try {
    process.kill(owner.pid, 0);
  } catch (failure3) {
    if (failure3.code === "ESRCH") {
      if (reclaimDeadOwner(directory)) return tryAcquireProcessLock(directory);
    }
  }
  return null;
}
function removeStagedLock(directory) {
  removePrivateFile(path22.join(directory, "owner.json"));
  removePrivateDirectory(directory);
}
function removePrivateFile(file) {
  const deadline = Date.now() + PRIVATE_CLEANUP_RETRY_MS;
  while (true) {
    try {
      unlinkSync(file);
      return;
    } catch (error2) {
      const code = error2?.code;
      if (code === "ENOENT" || !isTransientLockFsError(error2) || Date.now() >= deadline) return;
      pauseBriefly();
    }
  }
}
function removePrivateDirectory(directory) {
  const deadline = Date.now() + PRIVATE_CLEANUP_RETRY_MS;
  while (true) {
    try {
      rmdirSync(directory);
      return;
    } catch (error2) {
      const code = error2?.code;
      if (code === "ENOENT" || !isTransientLockFsError(error2) || Date.now() >= deadline) return;
      pauseBriefly();
    }
  }
}
function reclaimDeadOwner(directory) {
  const guard = `${directory}.reclaim`;
  try {
    mkdirSync3(guard);
  } catch (error2) {
    if (error2.code === "EEXIST") return false;
    throw error2;
  }
  let outcome;
  try {
    const owner = parseLockOwner(readFileSync6(path22.join(directory, "owner.json"), "utf8"));
    if (!owner) {
      outcome = { kind: "busy" };
    } else {
      const identityEvidence = processStartEvidence(owner.pid);
      if (identityEvidence.state !== "absent") {
        outcome = { kind: "busy" };
      } else {
        const retired = `${directory}.${randomUUID8()}.retired`;
        renameWithTransientRetry(directory, retired);
        removeStagedLock(retired);
        outcome = { kind: "reclaimed" };
      }
    }
  } catch (error2) {
    outcome = error2.code === "ENOENT" ? { kind: "busy" } : { kind: "error", error: error2 };
  }
  let guardCleanupError = null;
  try {
    removeSharedGuard(guard);
  } catch (error2) {
    guardCleanupError = error2;
  }
  if (outcome.kind === "error") throw outcome.error;
  if (guardCleanupError !== null) throw guardCleanupError;
  return outcome.kind === "reclaimed";
}
function removeSharedGuard(guard) {
  const deadline = Date.now() + SHARED_GUARD_RETRY_MS;
  while (true) {
    try {
      rmdirSync(guard);
      return;
    } catch (error2) {
      const code = error2?.code;
      if (code === "ENOENT") return;
      if (!isTransientLockFsError(error2) || Date.now() >= deadline) {
        throw new Error(
          `could not remove the lock reclaim guard at ${guard} (${code ?? "unknown error"}); a leftover guard blocks all future dead-owner reclaims of this lock and needs manual diagnosis`,
          { cause: error2 }
        );
      }
      pauseBriefly();
    }
  }
}

// src/runtime/auto-wake-setting.ts
var AUTO_WAKE_RUNTIME_KEY = "ZCODE_BRIDGE_AUTO_WAKE";
var SETTINGS_LIMIT_BYTES = 64 * 1024;
function autoWakeEnabledFromEnvironment(env) {
  const raw = env[AUTO_WAKE_RUNTIME_KEY]?.trim().toLowerCase();
  return raw !== "false" && raw !== "0" && raw !== "off" && raw !== "no";
}
async function readAutoWakeSetting(settingsDirectory) {
  const config2 = await readRuntimeConfig(settingsDirectory);
  const value = config2[AUTO_WAKE_RUNTIME_KEY];
  if (value === void 0 || value === null || value === "") return true;
  if (typeof value !== "string") {
    throw new BridgeError("provider_config_invalid", `${AUTO_WAKE_RUNTIME_KEY} must be "true" or "false"`);
  }
  return autoWakeEnabledFromEnvironment({ [AUTO_WAKE_RUNTIME_KEY]: value });
}
async function writeAutoWakeSetting(settingsDirectory, enabled) {
  if (typeof enabled !== "boolean") {
    throw new BridgeError("provider_config_invalid", "auto_wake must be a boolean");
  }
  await mkdir4(settingsDirectory, { recursive: true });
  await withProcessLock(path23.join(settingsDirectory, ".settings.lock"), async () => {
    const config2 = await readRuntimeConfig(settingsDirectory);
    config2[AUTO_WAKE_RUNTIME_KEY] = enabled ? "true" : "false";
    const serialized = `${JSON.stringify(config2, null, 2)}
`;
    if (Buffer.byteLength(serialized, "utf8") > SETTINGS_LIMIT_BYTES) {
      throw new BridgeError("provider_config_invalid", "Updated Bridge runtime config would exceed 64 KiB");
    }
    const configPath = path23.join(settingsDirectory, "runtime-config.json");
    const tempPath = `${configPath}.${process.pid}.${randomUUID9()}.tmp`;
    try {
      await writeFile2(tempPath, serialized, { encoding: "utf8", flag: "wx", mode: 384 });
      await atomicRename(tempPath, configPath);
    } catch (error2) {
      await rm3(tempPath, { force: true }).catch(() => void 0);
      throw new BridgeError(
        "provider_config_invalid",
        `Could not save Bridge runtime config: ${error2 instanceof Error ? error2.message : String(error2)}`,
        { cause: error2 }
      );
    }
  });
}
async function readRuntimeConfig(settingsDirectory) {
  const configPath = path23.join(settingsDirectory, "runtime-config.json");
  try {
    const info = await stat4(configPath);
    if (!info.isFile() || info.size > SETTINGS_LIMIT_BYTES) {
      throw new BridgeError("provider_config_invalid", "Bridge runtime config is not a small regular JSON file");
    }
    const parsed = JSON.parse(await readFile6(configPath, "utf8"));
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new BridgeError("provider_config_invalid", "Bridge runtime config must contain a JSON object");
    }
    return parsed;
  } catch (error2) {
    if (error2.code === "ENOENT") return {};
    if (error2 instanceof BridgeError) throw error2;
    throw new BridgeError("provider_config_invalid", "Could not read Bridge runtime config", { cause: error2 });
  }
}

// src/web/console-ui.ts
import { existsSync as existsSync9, readFileSync as readFileSync7 } from "node:fs";
import path24 from "node:path";
import { fileURLToPath as fileURLToPath9 } from "node:url";

// src/web/task-console-ui.ts
function renderTaskConsoleHtml(brandIconDataUri) {
  return String.raw`<!doctype html>
<html lang="en" data-theme="system">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>Bridge Task Console</title>
<style>
:root{
  --bg:#f5f7f4;
  --surface:#ffffff;
  --surface-2:#eef1ed;
  --line:#dfe4df;
  --text:#18211c;
  --text-2:#3d4842;
  --muted:#6c7770;
  --accent:#0f6b5b;
  --primary:#245fc0;
  --ok:#1f704b;
  --warn:#955708;
  --bad:#a72f2a;
  --attention:#fbf4e8;
  --attention-line:#e2c18b;
  --focus:#245fc0;
  --code:#111815;
  --code-ink:#eef3ec;
  --radius:9px;
  --sans:"Aptos","Segoe UI Variable","Segoe UI",sans-serif;
  --display:"Aptos Display","Segoe UI Variable Display","Segoe UI",sans-serif;
  --mono:"Cascadia Code","Consolas",monospace
}
:root[data-theme="dark"]{
  --bg:#0f1512;
  --surface:#161e1a;
  --surface-2:#1d2722;
  --line:#2c3932;
  --text:#e9eee9;
  --text-2:#c3ccc6;
  --muted:#96a39b;
  --accent:#68c8b5;
  --primary:#7aaeff;
  --ok:#7bcaa0;
  --warn:#e0a45d;
  --bad:#ff9188;
  --attention:#211b12;
  --attention-line:#5a4528;
  --focus:#7aaeff;
  --code:#090f0c;
  --code-ink:#eef3ec
}
@media(prefers-color-scheme:dark){:root[data-theme="system"]{
  --bg:#0f1512;--surface:#161e1a;--surface-2:#1d2722;--line:#2c3932;--text:#e9eee9;--text-2:#c3ccc6;
  --muted:#96a39b;--accent:#68c8b5;--primary:#7aaeff;--ok:#7bcaa0;--warn:#e0a45d;--bad:#ff9188;
  --attention:#211b12;--attention-line:#5a4528;--focus:#7aaeff;--code:#090f0c;--code-ink:#eef3ec
}}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;min-height:100vh;background:var(--bg);color:var(--text);font:13.5px/1.45 var(--sans)}
button,input,select,textarea{font:inherit;color:inherit}
button{cursor:pointer}
button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,a:focus-visible,summary:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.visually-hidden{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}
.mono,code,pre{font-family:var(--mono)}
.shell{max-width:1460px;margin:0 auto;padding:0 clamp(14px,2.6vw,32px) 40px}
.masthead{display:flex;align-items:center;justify-content:space-between;gap:14px;min-height:58px;border-bottom:1px solid var(--line);padding:9px 0}
.brand{display:flex;align-items:center;gap:9px;min-width:0;color:inherit;text-decoration:none}
.brand-mark{display:grid;place-items:center;flex:0 0 30px;width:30px;height:30px;padding:2px;border:1px solid var(--line);border-radius:7px;background:#fff;overflow:hidden}
.brand-icon{display:block;width:100%;height:100%;object-fit:contain}
.brand strong{display:block;font:650 15px/1.2 var(--display);letter-spacing:-.01em;white-space:nowrap}
.experimental-pill{display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:999px;background:var(--surface-2);padding:2px 7px;color:var(--muted);font:600 9px/1.3 var(--sans);letter-spacing:.01em;white-space:nowrap}
.top-tools{display:flex;align-items:center;justify-content:flex-end;gap:7px;flex-wrap:wrap}
.button{border:1px solid var(--line);border-radius:7px;background:var(--surface);color:var(--text);padding:7px 10px;font:600 11.5px/1.2 var(--sans);white-space:nowrap}
.button:hover{border-color:var(--focus);background:color-mix(in srgb,var(--focus) 5%,var(--surface))}
.button.primary{border-color:var(--primary);background:var(--primary);color:#fff}
.button.primary:hover{filter:brightness(.95)}
.button.danger{border-color:var(--bad);background:transparent;color:var(--bad)}
.button.danger:hover{background:color-mix(in srgb,var(--bad) 7%,var(--surface))}
.button:disabled{opacity:.45;cursor:not-allowed}
.icon-button{width:31px;height:31px;padding:0;display:grid;place-items:center;font-size:15px;line-height:1}
.prefs{display:flex;align-items:center;gap:6px}
.prefs select{height:31px;border:1px solid var(--line);border-radius:7px;background:var(--surface);padding:4px 6px;font-size:11px}
#language{min-width:92px}
#theme{min-width:82px}
.page-head{padding:24px 0 14px}
.page-head h1{margin:0;font:640 clamp(28px,4vw,36px)/1 var(--display);letter-spacing:-.035em}
.lede{margin:7px 0 0;color:var(--muted);font:12.5px/1.5 var(--sans)}
.summary-line{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin:13px 0 0;color:var(--muted);font:11.5px/1.4 var(--sans)}
.summary-item{display:inline-flex;align-items:baseline;gap:5px;border:0;border-bottom:2px solid transparent;background:transparent;padding:2px 0;color:var(--muted);font:inherit}
.summary-item strong{color:var(--text);font:650 14px/1 var(--display);letter-spacing:-.02em}
.summary-item:hover{color:var(--text)}
.summary-item.active{border-bottom-color:var(--accent);color:var(--text)}
.summary-item[data-filter="attention"] strong{color:var(--warn)}
.summary-item[data-filter="running"] strong{color:var(--primary)}
.summary-item[data-filter="completed"] strong{color:var(--ok)}
.summary-sep{color:var(--line)}
.executor-notice{margin:0 0 12px;border-left:2px solid var(--warn);background:var(--attention);padding:7px 10px;color:var(--text-2);font:11.5px/1.5 var(--sans)}
.executor-notice[hidden]{display:none}
.error{display:none;margin:0 0 12px;border-left:2px solid var(--bad);background:color-mix(in srgb,var(--bad) 6%,var(--surface));padding:8px 10px;color:var(--bad);font-size:11.5px}
.error.visible{display:block}
.workspace{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,3fr);gap:18px;align-items:start}
.panel{min-width:0;border:1px solid var(--line);border-radius:var(--radius);background:var(--surface);overflow:hidden}
.list-toolbar{display:grid;grid-template-columns:minmax(0,1fr) 118px 31px;gap:7px;align-items:center;border-bottom:1px solid var(--line);padding:9px 11px}
.search-box{position:relative;display:block;min-width:0}
.search-icon{position:absolute;left:8px;top:50%;width:13px;height:13px;transform:translateY(-50%);fill:var(--muted);pointer-events:none}
.search-box input{width:100%;height:31px;border:1px solid var(--line);border-radius:7px;background:var(--surface);padding:5px 8px 5px 26px;font:11px var(--sans)}
.search-box input::placeholder{color:var(--muted)}
.bucket-filter{width:100%;height:31px;border:1px solid var(--line);border-radius:7px;background:var(--surface);padding:4px 6px;font:11px var(--sans)}
.task-list{max-height:calc(100vh - 278px);min-height:240px;overflow:auto}
.task-row{position:relative;display:block;width:100%;border:0;border-bottom:1px solid var(--line);background:transparent;color:var(--text);padding:11px 12px;text-align:left}
.task-row:last-child{border-bottom:0}
.task-row:before{content:"";position:absolute;left:0;top:10px;bottom:10px;width:2px;background:transparent}
.task-row:hover{background:color-mix(in srgb,var(--surface-2) 65%,var(--surface))}
.task-row.selected{background:color-mix(in srgb,var(--accent) 5%,var(--surface))}
.task-row.selected:before{background:var(--accent)}
.task-row.attention{background:color-mix(in srgb,var(--warn) 4%,var(--surface))}
.task-row.attention:before{background:var(--warn)}
.task-main{display:grid;gap:3px;min-width:0}
.task-line{display:flex;align-items:center;gap:7px;min-width:0}
.task-line-title{justify-content:space-between}
.task-name{display:block;flex:1;min-width:0;overflow:hidden;color:var(--text);font:650 13px/1.35 var(--display);text-overflow:ellipsis;white-space:nowrap}
.task-line-meta{display:flex;align-items:center;flex-wrap:wrap;gap:1px 5px;color:var(--muted);font:10px/1.45 var(--sans)}
.task-meta-item{display:inline-flex;min-width:0;white-space:nowrap}
.task-meta-item+.task-meta-item:before{content:"·";margin-right:3px;color:var(--line)}
.task-line-problem{display:flex;align-items:flex-start;gap:5px;color:var(--warn);font:600 10px/1.45 var(--sans)}
.task-line-problem:before{content:"!";display:grid;place-items:center;width:12px;height:12px;flex:0 0 12px;margin-top:1px;border:1px solid currentColor;border-radius:50%;font:700 8px var(--mono)}
.status-chip{display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:999px;background:var(--surface-2);color:var(--text-2);padding:2px 6px;font:650 8.5px/1.3 var(--sans);letter-spacing:.01em;white-space:nowrap;max-width:100%;overflow:hidden;text-overflow:ellipsis}
.status-chip.completed,.status-chip.released,.status-chip.ok{background:color-mix(in srgb,var(--ok) 10%,var(--surface));border-color:color-mix(in srgb,var(--ok) 30%,var(--line));color:var(--ok)}
.status-chip.review-pending{background:color-mix(in srgb,var(--accent) 7%,var(--surface));border-color:color-mix(in srgb,var(--accent) 28%,var(--line));color:var(--accent)}
.status-chip.review-blocked,.status-chip.running,.status-chip.waiting_for_master{background:color-mix(in srgb,var(--warn) 9%,var(--surface));border-color:color-mix(in srgb,var(--warn) 30%,var(--line));color:var(--warn)}
.status-chip.failed,.status-chip.cancelled{background:color-mix(in srgb,var(--bad) 8%,var(--surface));border-color:color-mix(in srgb,var(--bad) 28%,var(--line));color:var(--bad)}
.status-chip.queued{background:color-mix(in srgb,var(--primary) 7%,var(--surface));border-color:color-mix(in srgb,var(--primary) 26%,var(--line));color:var(--primary)}
.empty{padding:34px 18px;color:var(--muted);font:12.5px var(--sans);text-align:center}
.detail-panel{min-height:480px}
.detail-body{padding:17px 19px 22px;min-width:0}
.detail-empty{padding:64px 18px;color:var(--muted);font:13px var(--sans);text-align:center}
.task-header{padding:0 0 13px}
.detail-title{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.detail-title-main{min-width:0}
.detail-title h2{margin:0;font:640 20px/1.25 var(--display);letter-spacing:-.02em;overflow-wrap:anywhere}
.detail-title p{margin:4px 0 0;color:var(--text-2);font:12px/1.5 var(--sans);overflow-wrap:anywhere}
.hero-chips{display:flex;align-items:center;justify-content:flex-end;gap:4px;flex:0 0 auto;flex-wrap:wrap}
.detail-context{display:flex;align-items:center;flex-wrap:wrap;gap:2px 6px;margin-top:6px;color:var(--muted);font:10px/1.45 var(--mono);min-width:0}
.detail-context-sep{color:var(--line)}
.detail-workspace{margin-top:5px;min-width:0;color:var(--muted);font:9.5px/1.45 var(--mono)}
.detail-workspace>summary{display:inline-flex;align-items:baseline;gap:6px;cursor:pointer;list-style:none}
.detail-workspace>summary::-webkit-details-marker{display:none}
.detail-workspace>summary:after{content:"+";margin-left:2px;color:var(--muted);font:600 10px var(--mono)}
.detail-workspace[open]>summary:after{content:"−"}
.detail-workspace-label{flex:0 0 auto;color:var(--muted);font:9px var(--sans)}
.detail-workspace code{min-width:0;overflow-wrap:anywhere}
.detail-workspace-full{margin:5px 0 0 0;padding:5px 7px;border-left:1px solid var(--line);color:var(--text-2);font:9px/1.45 var(--mono);overflow-wrap:anywhere}
.region{border-top:1px solid var(--line);margin-top:15px;padding-top:14px;min-width:0}
.region:first-of-type{border-top:0;margin-top:0;padding-top:0}
.region-title{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin:0 0 8px}
.region-title h3{margin:0;color:var(--muted);font:650 10px/1.3 var(--sans);letter-spacing:.09em;text-transform:uppercase}
.region-title small{color:var(--muted);font:9.5px/1.35 var(--sans);text-align:right}
.problem{display:grid;gap:5px;border-left:2px solid var(--line);padding:1px 0 1px 9px}
.problem.bad{border-color:var(--bad)}
.problem.warn{border-color:var(--warn)}
.problem.info{border-color:var(--line)}
.problem.ok{border-color:var(--line)}
.problem-line{margin:0;color:var(--text-2);font:11.5px/1.55 var(--sans);overflow-wrap:anywhere}
.problem-line strong{margin-right:0;color:var(--text);font-weight:650}
.problem-sep{color:var(--muted)}
.problem.bad .problem-line strong{color:var(--bad)}
.problem.warn .problem-line strong{color:var(--warn)}
.problem.ok .problem-line strong{color:var(--muted)}
.actions{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:9px}
.action-note{margin:6px 0 0;color:var(--muted);font:10.5px/1.45 var(--sans)}
.action-note.blocked{color:var(--warn)}
.form-card{border:1px solid var(--line);border-radius:7px;background:color-mix(in srgb,var(--surface-2) 35%,var(--surface));padding:9px;margin:9px 0 0}
.form-card label{display:grid;gap:4px;margin-bottom:7px;color:var(--muted);font:9.5px var(--sans)}
.form-card textarea,.form-card input,.form-card select{width:100%;min-height:31px;border:1px solid var(--line);border-radius:6px;background:var(--surface);padding:6px 7px;font-size:11px}
.form-card textarea{min-height:66px;resize:vertical}
.form-grid{display:grid;grid-template-columns:1fr 112px;gap:7px}
.form-grid .wide{grid-column:1/-1}
.attempts{display:flex;gap:6px;overflow:auto;padding:1px 0 4px}
.attempt{min-width:118px;border:1px solid var(--line);border-radius:7px;background:var(--surface);padding:7px 8px;text-align:left;color:var(--text)}
.attempt:hover{border-color:var(--focus)}
.attempt.active{border-color:var(--accent);background:color-mix(in srgb,var(--accent) 5%,var(--surface))}
.attempt strong{display:block;font:650 10.5px var(--sans)}
.attempt span{display:block;margin-top:2px;overflow:hidden;color:var(--muted);font:8.5px var(--mono);text-overflow:ellipsis;white-space:nowrap}
.attempt .status-chip{margin-top:4px}
.result-block{margin-top:8px}
.result-summary{margin:7px 0 0;font:12px/1.6 var(--sans);white-space:pre-wrap;overflow-wrap:anywhere}
.result-metrics{display:flex;align-items:center;gap:5px;flex-wrap:wrap;margin-top:6px;color:var(--muted);font:10px/1.45 var(--sans)}
.result-metrics span+span:before{content:"·";margin-right:5px;color:var(--line)}
.result-details{margin-top:7px}
.result-details>summary{cursor:pointer;color:var(--muted);font:10px var(--sans);list-style:none}
.result-details>summary::-webkit-details-marker{display:none}
.result-details>summary:before{content:"+";display:inline-block;width:11px;color:var(--muted);font:600 12px var(--mono)}
.result-details[open]>summary:before{content:"−"}
.result-detail-body{display:grid;gap:6px;margin-top:6px}
.detail-label{margin:0;color:var(--muted);font:9px/1.3 var(--sans);letter-spacing:.04em;text-transform:uppercase}
.detail-list{display:grid;gap:2px;margin:0;padding:0;list-style:none}
.detail-list li{padding:3px 0;border-bottom:1px solid color-mix(in srgb,var(--line) 65%,transparent);font:10.5px/1.45 var(--mono);overflow-wrap:anywhere}
.detail-list li:last-child{border-bottom:0}
.detail-list .test-row{font-family:var(--sans)}
.test-failed{color:var(--bad)}
.test-not-run{color:var(--warn)}
.execution-region>summary,.technical-region>summary{display:flex;align-items:baseline;justify-content:space-between;gap:10px;cursor:pointer;list-style:none;min-width:0}
.execution-region>summary::-webkit-details-marker,.technical-region>summary::-webkit-details-marker{display:none}
.execution-region>summary:after,.technical-region>summary:after{content:"+";flex:0 0 auto;color:var(--muted);font:600 13px var(--mono)}
.execution-region[open]>summary:after,.technical-region[open]>summary:after{content:"−"}
.execution-title{flex:0 0 auto;color:var(--muted);font:650 10px/1.3 var(--sans);letter-spacing:.09em;text-transform:uppercase}
.execution-line{display:flex;align-items:baseline;justify-content:flex-end;gap:5px;flex-wrap:wrap;min-width:0;color:var(--text-2);font:10.5px/1.45 var(--sans);text-align:right}
.execution-sep{color:var(--line)}
.execution-body{margin-top:10px}
.exec-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px 14px}
.exec-cell{min-width:0}
.exec-cell label,.usage-fact label{display:block;margin-bottom:2px;color:var(--muted);font:9px var(--sans)}
.exec-cell strong,.usage-fact strong{display:block;font:600 11.5px/1.4 var(--sans);overflow-wrap:anywhere}
.usage-fact strong{font:650 13px/1.25 var(--display)}
.provider-cost{margin-top:10px;padding-top:8px;border-top:1px solid color-mix(in srgb,var(--line) 65%,transparent)}
.provider-cost strong{display:block;font:600 11px var(--sans)}
.provider-cost small{display:block;margin-top:2px;color:var(--muted);font:9.5px/1.45 var(--sans)}
.usage-scope{display:grid;gap:1px;margin-top:8px;color:var(--text-2);font:10.5px/1.45 var(--sans)}
.usage-scope b{font-weight:650}
.usage-scope small{color:var(--muted);font:9.5px/1.4 var(--sans)}
.usage-observed{color:var(--text)}
.tech-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px 14px;margin-top:10px}
.tech-item{min-width:0}
.tech-item h4{margin:0 0 3px;color:var(--muted);font:9px var(--sans);letter-spacing:.04em;text-transform:uppercase}
.tech-item strong{display:block;font:600 11px/1.4 var(--sans);overflow-wrap:anywhere}
.tech-item small{display:block;margin-top:2px;color:var(--muted);font:9px/1.45 var(--mono);overflow-wrap:anywhere}
.tech-note{margin:5px 0 0;border-left:2px solid var(--warn);padding-left:7px;color:var(--warn);font:10px/1.45 var(--sans)}
.events{margin-top:12px;padding-top:9px;border-top:1px solid color-mix(in srgb,var(--line) 65%,transparent)}
.events>summary{cursor:pointer;color:var(--muted);font:600 10px var(--sans);list-style:none}
.events>summary::-webkit-details-marker{display:none}
.events>summary:after{content:"+";margin-left:5px;font:600 12px var(--mono)}
.events[open]>summary:after{content:"−"}
.event-list{max-height:380px;overflow:auto;margin-top:7px;border-top:1px solid color-mix(in srgb,var(--line) 65%,transparent)}
.event-row{border-bottom:1px solid color-mix(in srgb,var(--line) 65%,transparent);padding:6px 1px;font-size:10px;overflow-wrap:anywhere}
.event-top{display:flex;align-items:baseline;gap:6px;flex-wrap:wrap}
.event-seq{color:var(--muted);font:9px var(--mono)}
.event-type{color:var(--primary);font:700 9px var(--mono)}
.event-summary{margin-top:2px;line-height:1.45}
.event-details summary{color:var(--muted);font:9px var(--mono);margin-top:3px}
.event-details pre{max-height:160px;overflow:auto;margin:4px 0 0;padding:7px;background:var(--code);color:var(--code-ink);font:9px/1.45 var(--mono);white-space:pre-wrap;overflow-wrap:anywhere}
.toast{position:fixed;right:16px;bottom:16px;z-index:40;max-width:440px;border-radius:7px;background:var(--text);color:var(--bg);padding:8px 11px;font:10.5px var(--mono);opacity:0;transform:translateY(8px);transition:.2s;pointer-events:none}
.toast.show{opacity:1;transform:none}
.toast.error{background:var(--bad);color:#fff}
dialog{border:1px solid var(--line);border-radius:10px;background:var(--surface);color:var(--text);padding:0;width:min(900px,calc(100vw - 28px));max-height:calc(100vh - 40px)}
dialog::backdrop{background:rgba(0,0,0,.38)}
.dialog-head{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:10px 12px;border-bottom:1px solid var(--line);background:var(--surface-2)}
.dialog-head h2{margin:0;font:650 12px var(--sans)}
.dialog-body{padding:12px;overflow:auto;max-height:calc(100vh - 120px)}
.diag-notice{margin:0 0 10px;color:var(--muted);font:10.5px/1.5 var(--sans)}
.diag-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}
.diag-card{border:1px solid var(--line);border-radius:8px;background:var(--surface);padding:10px;min-width:0}
.diag-card h3{margin:0 0 5px;font:650 11px var(--sans)}
.diag-card p{margin:0 0 7px;color:var(--muted);font-size:10px;line-height:1.45}
.diag-actions{display:flex;gap:5px;flex-wrap:wrap}
.tag{display:inline-block;border:1px solid color-mix(in srgb,var(--warn) 32%,var(--line));border-radius:999px;background:color-mix(in srgb,var(--warn) 7%,var(--surface));color:var(--warn);padding:1px 5px;font:650 8px var(--sans);vertical-align:middle}
.diag-output{border-radius:7px;background:var(--code);color:var(--code-ink);padding:8px;white-space:pre-wrap;overflow-wrap:anywhere;font:9.5px/1.5 var(--mono);max-height:240px;overflow:auto;margin-top:9px}
.checkbox{display:flex;gap:6px;align-items:flex-start;font-size:10px;line-height:1.4;margin:6px 0}
@media(max-width:980px){
  .workspace{grid-template-columns:1fr}
  .task-list{max-height:44vh}
  .exec-grid,.tech-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .diag-grid{grid-template-columns:1fr}
}
@media(max-width:700px){
  .shell{padding:0 12px 28px}
  .masthead{display:grid;gap:7px;padding:9px 0}
  .top-tools{justify-content:flex-start}
  .page-head{padding:18px 0 12px}
  .page-head h1{font-size:30px}
  .lede{font-size:12px}
  .summary-line{gap:5px}
  .list-toolbar{grid-template-columns:minmax(0,1fr) 108px 31px;padding:8px 9px}
  .task-row{padding:10px 10px 10px 11px}
  .task-line-meta{font-size:9.5px}
  .detail-body{padding:13px 13px 20px}
  .detail-title{display:grid;gap:7px}
  .hero-chips{justify-content:flex-start}
  .exec-grid,.tech-grid{grid-template-columns:1fr}
  .execution-region>summary,.technical-region>summary{display:grid;gap:3px}
  .execution-line{justify-content:flex-start;text-align:left}
  .form-grid{grid-template-columns:1fr}
  .form-grid .wide{grid-column:auto}
  .attempts{flex-wrap:wrap;overflow:visible}
  .attempt{min-width:calc(50% - 3px);flex:1 1 calc(50% - 3px)}
}
@media(max-width:430px){
  .prefs{gap:5px}
  #language{min-width:86px}
  #theme{min-width:76px}
  .task-line-meta{font-size:9px}
  .result-metrics{display:grid;gap:1px}
  .result-metrics span+span:before{display:none}
}
</style>
</head>
<body>
<div class="shell">
  <header class="masthead">
    <a class="brand" href="/" aria-label="Bridge Task Console">
      <span class="brand-mark"><img class="brand-icon" src="${brandIconDataUri}" alt="" width="30" height="30"></span>
      <strong data-i18n="brand">Bridge Task Console</strong>
      <span class="experimental-pill" id="experimental-notice">
        <span class="experimental-label" data-i18n="experimental">Experimental</span>
        <span class="visually-hidden" data-i18n="experimentalNotice">Experimental: task status and recovery operations are still being refined.</span>
      </span>
    </a>
    <div class="top-tools">
      <button class="button" id="diagnostics-open" type="button" data-i18n="diagnostics">Diagnostics</button>
      <div class="prefs">
        <label><span class="visually-hidden" data-i18n="language">Language</span><select id="language" aria-label="Language"><option value="zh-CN">简体中文</option><option value="en">English</option></select></label>
        <label><span class="visually-hidden" data-i18n="theme">Theme</span><select id="theme" aria-label="Theme"><option value="system" data-i18n="themeSystem">System</option><option value="light" data-i18n="themeLight">Light</option><option value="dark" data-i18n="themeDark">Dark</option></select></label>
      </div>
    </div>
  </header>

  <div class="page-head">
    <h1 data-i18n="titleTasks">Tasks</h1>
    <p class="lede" data-i18n="lede">Review task status, results, and recovery actions.</p>
    <div class="summary-line" role="group" aria-label="Task filters">
      <button class="summary-item" type="button" data-filter="running" aria-pressed="false"><span data-i18n="running">Running</span><strong id="count-running">0</strong></button>
      <span class="summary-sep" aria-hidden="true">·</span>
      <button class="summary-item" type="button" data-filter="attention" aria-pressed="false"><span data-i18n="attention">Needs attention</span><strong id="count-attention">0</strong></button>
      <span class="summary-sep" aria-hidden="true">·</span>
      <button class="summary-item" type="button" data-filter="completed" aria-pressed="false"><span data-i18n="completed">Completed</span><strong id="count-completed">0</strong></button>
    </div>
  </div>

  <div id="executor-notice" class="executor-notice" hidden></div>
  <div id="global-error" class="error" role="alert"></div>

  <div class="workspace">
    <section class="panel list-panel">
      <div class="list-toolbar">
        <label class="search-box">
          <svg class="search-icon" viewBox="0 0 20 20" aria-hidden="true"><path d="M8.6 2.5a6.1 6.1 0 1 0 3.8 10.9l3.2 3.2 1.1-1.1-3.2-3.2A6.1 6.1 0 0 0 8.6 2.5Zm0 1.6a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9Z"/></svg>
          <input id="task-search" type="search" autocomplete="off" spellcheck="false" placeholder="Search tasks (name or workspace)">
        </label>
        <select id="bucket-filter" class="bucket-filter" aria-label="Task filter">
          <option value="" data-i18n="allTasks">All tasks</option>
          <option value="running" data-i18n="running">Running</option>
          <option value="attention" data-i18n="attention">Needs attention</option>
          <option value="completed" data-i18n="completed">Completed</option>
        </select>
        <button class="button icon-button" id="refresh-tasks" type="button" title="Refresh" aria-label="Refresh">↻</button>
      </div>
      <div id="task-list" class="task-list" aria-live="polite"><div class="empty" data-i18n="loadingTasks">Loading tasks...</div></div>
    </section>

    <section class="panel detail-panel">
      <div id="task-detail" class="detail-body"><div class="detail-empty" data-i18n="chooseTask">Select a task to review its status, result, and next action.</div></div>
    </section>
  </div>
</div>

<dialog id="diagnostics" aria-labelledby="diagnostics-title">
  <div class="dialog-head"><h2 id="diagnostics-title" data-i18n="diagnosticsTitle">Diagnostics and explicit operations</h2><button class="button" id="diagnostics-close" type="button" data-i18n="close">Close</button></div>
  <div class="dialog-body">
    <p class="diag-notice" data-i18n="diagNotice">Experimental entry points. Opening this dialog performs no model, Runtime-probe or Billing request; every external read or write below is an explicit click.</p>
    <div class="diag-grid">
      <section class="diag-card">
        <h3><span data-i18n="runtime">Runtime</span> <span class="tag" data-i18n="experimental">Experimental</span></h3>
        <p data-i18n="runtimeHelp">Static installation inspection, authorized zero-model protocol probe, and candidate report export.</p>
        <div class="diag-actions">
          <button class="button" id="diag-runtime-inspect" type="button" data-i18n="inspectRuntime">Inspect</button>
          <button class="button" id="diag-runtime-check" type="button" data-i18n="staticCheck">Static check</button>
          <button class="button" id="diag-runtime-probe" type="button" data-i18n="protocolProbe">Protocol probe</button>
          <button class="button" id="diag-runtime-report" type="button" data-i18n="exportReport">Export report</button>
        </div>
      </section>
      <section class="diag-card">
        <h3><span data-i18n="costLab">Cost evidence</span> <span class="tag" data-i18n="experimental">Experimental</span></h3>
        <p data-i18n="costHelp">Installation environment and historical evidence. A verification entry only loads its explicit confirmation state; it is not started here.</p>
        <div class="diag-actions">
          <button class="button" id="diag-cost-environment" type="button" data-i18n="loadEnvironment">Environment</button>
          <button class="button" id="diag-cost-history" type="button" data-i18n="loadHistory">History</button>
          <button class="button" id="diag-cost-verification" type="button" data-i18n="loadVerification">Verification entry</button>
        </div>
      </section>
      <section class="diag-card">
        <h3><span data-i18n="settings">Settings</span></h3>
        <p data-i18n="autoWakeHelp">Auto Wake defaults on. Turning it off records web_notify/auto_wake_disabled instead of calling the official Queue.</p>
        <label class="checkbox"><input id="auto-wake" type="checkbox"><span data-i18n="autoWake">Auto Wake</span></label>
        <button class="button" id="diag-save-settings" type="button" data-i18n="saveSettings">Save setting</button>
      </section>
    </div>
    <pre id="diag-output" class="diag-output" aria-live="polite"></pre>
  </div>
</dialog>

<div id="toast" class="toast" role="status"></div>
<script>
(function(){
"use strict";
var TEXT={
  en:{
    brand:"Bridge Task Console",language:"Language",theme:"Theme",themeSystem:"System",themeLight:"Light",themeDark:"Dark",
    diagnostics:"Diagnostics",titleTasks:"Tasks",experimental:"Experimental",
    experimentalNotice:"Experimental: task status and recovery operations are still being refined.",
    lede:"Review task status, results, and recovery actions.",
    running:"Running",attention:"Needs attention",completed:"Execution completed",waitingMasterShort:"Waiting for Master",
    searchTasks:"Search tasks (name or workspace)",filterTasks:"Task filter",allTasks:"All tasks",refresh:"Refresh",
    loadingTasks:"Loading tasks...",noTasks:"No Task matches this filter.",chooseTask:"Select a task to review its status, result, and next action.",
    refreshFailed:"Could not refresh the Task list.",detailFailed:"Could not load this Task.",invalidTask:"Invalid Task ID.",sessionOffline:"Executor session is unavailable.",
    completedReviewPending:"Execution completed · Awaiting review",completedReviewBlocked:"Execution completed · Review blocked",
    problemActions:"Problem and actions",workHistory:"Work history",execution:"Execution",technicalDetails:"Technical details",
    technicalHint:"Wake · Cleanup · Release · Events",
    completedNotAccepted:"Worker execution completed. Master acceptance is not recorded.",
    review:"Review",current:"Current",usageSummaryNotObserved:"Execution usage not observed",executionUsage:"Execution usage",
    waitingMaster:"Waiting for Master review. This page does not create an acceptance.",
    workerActive:"A Worker or dispatch is active. Continue and related rework stay disabled.",
    resultFailed:"Result failed",resultFailedHint:"The Worker Result failed. This is not a Master acceptance decision; inspect the error and choose a safe recovery action.",
    resultIssues:"Result issues",resultIssuesHint:"The Worker reported issues. This is not a Master acceptance decision; review the Result before choosing the next action.",
    cleanup:"Cleanup",cleanupPending:"Cleanup is pending.",cleanupUnverified:"Cleanup is unverified. Release is not proven.",cleanupVerified:"Cleanup verified.",cleanupNotRequired:"Cleanup is not required.",cleanupNotStarted:"Cleanup has not started.",cleanupPendingShort:"Pending.",cleanupUnverifiedShort:"Unverified. Release is not proven.",
    wake:"Wake",wakeSubmissionUnknown:"Queue state needs verification. The page will not resend automatically.",wakeWebNotify:"Web notification only; the official Queue was not opened.",
    hold:"Hold",holdActive:"Active Hold: {reason}",noAttentionItems:"No blocking issue is active.",
    pendingInteraction:"Pending interaction",pendingInteractionHint:"A reply is required before this Task can continue.",replyUnknownWarning:"A previous reply may have reached the Worker. Reconcile before sending anything else; this page will not resend automatically.",
    needsMaster:"Needs Master decision",resultSubmissionError:"Result submission error",
    resultMissing:"No Result was observed for this Attempt.",resultDetails:"Result details",
    issues:"Issues",filesChanged:"Files changed",tests:"Tests",started:"Started",finished:"Finished",
    masterAccepted:"Master accepted. Final goal resolved.",masterAcceptedShort:"Master accepted",
    continue:"Continue",continueHint:"Create the next Attempt from this released Result.",continueFeedback:"Feedback for the next Attempt",continueRequirements:"Additional requirements, one per line",continueSubmit:"Start continuation",
    rework:"Create related rework",reworkHint:"Creates a new Task with the same goal and acceptance boundaries. The original Task, Attempts and results stay intact.",reworkFeedback:"Review feedback for the new Task",reworkSubmit:"Create rework Task",
    reply:"Reply",replyForm:"Reply to permission request",request:"Request",decision:"Decision",reason:"Reason",sendReply:"Send reply",
    decisionAllow:"Allow",decisionDeny:"Deny",decisionAccept:"Accept",decisionDecline:"Decline",
    cancel:"Request cancel",cancelConfirm:"Request cancellation of the active Attempt? This never forces Release.",
    cleanupRecovery:"Recover Cleanup",cleanupRecoveryConfirm:"Retry the Cleanup check for this Task? This re-checks the Worker and Cleanup facts, never clears a Hold, and does not bypass the Task state machine.",
    authorizedCleanup:"Authorize cleanup",authorizedCleanupConfirm:
      "Abandon this selected Task and release its Bridge occupancy? Existing evidence stays, execution success is not claimed, and a possibly live Worker may keep writing its Workspace. Type-safe confirmation only accepts these risks.",
    actionUnavailable:"No safe action is available for this Task right now.",actionBlocked:"Blocked by: {reasons}.",
    historicalReadOnly:"This is a historical Attempt. Actions apply only to the current Attempt.",
    task:"Task",attempt:"Attempt",workspace:"Workspace",updated:"Updated",model:"Model",plan:"Plan",discount:"Discount",effort:"Effort",status:"Status",result:"Result",
    notObserved:"Not observed",notAvailable:"Not available",dash:"--",unknown:"Unknown",
    modelObserved:"Observed",modelRequested:"Requested",modelNotObserved:"Not observed",
    planCoding:"Coding Plan",planStart:"Start Plan",planOther:"Other",planNotObserved:"Not observed",
    applied:"Applied",notApplied:"Not applied",notApplicable:"Not applicable",
    inputTokens:"Input tokens",outputTokens:"Output tokens",cacheRead:"Cache read",cacheWrite:"Cache write",reasoning:"Reasoning",totalTokens:"Total tokens",
    providerActualCost:"Provider actual cost",
    masterUsage:"Master usage",workerUsage:"Worker usage",workerUsageHint:"Tokens recorded for this Attempt.",
    usageSource:"Usage source",finality:"Finality",observedAt:"Observed at",
    notObservedFields:"Not observed: {fields}.",
    tokens:"{n} tokens",oneFileChanged:"{n} file changed",filesChangedCount:"{n} files changed",
    noTests:"No tests reported",testsSummary:"{passed} passed",testsFailedSummary:"{failed} failed",testsNotRunSummary:"{notRun} not run",
    events:"Events",loadingEvents:"Loading all Events...",eventsComplete:"All Events loaded",eventsFiltered:"Attempt {n}",eventsCount:"{n} Events",eventsEmpty:"No Events were recorded for this Attempt.",
    showDetails:"Details",hideDetails:"Hide details",
    executorUnavailable:"Executor unavailable.",executorRecoveryHint:"Opening or acting on a Task will attempt local Lease recovery; no second Worker is started while the previous Worker is alive.",
    diagnosticsTitle:"Diagnostics and explicit operations",close:"Close",
    diagNotice:"Experimental entry points. Opening this dialog performs no model, Runtime-probe or Billing request; every external read or write below is an explicit click.",
    runtime:"Runtime",runtimeHelp:"Static installation inspection, authorized zero-model protocol probe, and candidate report export.",
    inspectRuntime:"Inspect",staticCheck:"Static check",protocolProbe:"Protocol probe",exportReport:"Export report",
    costLab:"Cost evidence",costHelp:"Installation environment and historical evidence. A verification entry only loads its explicit confirmation state; it is not started here.",
    loadEnvironment:"Environment",loadHistory:"History",loadVerification:"Verification entry",settings:"Settings",
    autoWakeHelp:"Auto Wake defaults on. Turning it off records web_notify/auto_wake_disabled instead of calling the official Queue.",autoWake:"Auto Wake",saveSettings:"Save setting",
    settingsLoaded:"Settings loaded.",settingsSaved:"Auto Wake setting saved.",runtimeInspectFailed:"Runtime inspection failed.",costEnvironmentLoaded:"Cost evidence environment loaded.",costHistoryLoaded:"Cost evidence history loaded.",verificationLoaded:"Verification entry loaded. Starting it requires the existing explicit confirmation flow.",reportReady:"Candidate report downloaded.",reportUnavailable:"Candidate report is unavailable.",noHistory:"No historical evidence returned.",diagNoOutput:"Choose an explicit diagnostics operation.",
    taskActionDone:"Request accepted.",loadingDetail:"Loading task details...",
    wakeNotObserved:"No Wake observed",wakeWebNotifyShort:"Web notification",wakeSubmissionUnknownShort:"Needs verification",wakeIntent:"Delivery intent recorded",wakeQueued:"Queued for delivery",wakeTurnStarted:"New Turn started",
    release:"Release",releaseHeld:"Release is held.",releaseNotReleased:"Not released.",released:"Released",releaseVerified:"Cleanup verified at Release",releaseUnverified:"Released without verified Cleanup",
    cleanupIdentityUnverified:"Cleanup could not be verified because the Worker identity could not be confirmed. Nothing was released."
  },
  "zh-CN":{
    brand:"Bridge Task Console",language:"语言",theme:"主题",themeSystem:"跟随系统",themeLight:"浅色",themeDark:"深色",
    diagnostics:"诊断",titleTasks:"任务",experimental:"实验性",
    experimentalNotice:"实验性功能：任务状态与恢复操作仍在持续完善。",
    lede:"查看任务状态、结果与可用的恢复操作。",
    running:"进行中",attention:"需处理",completed:"执行完成",waitingMasterShort:"等待 Master",
    searchTasks:"搜索任务（名称或 Workspace）",filterTasks:"任务筛选",allTasks:"全部任务",refresh:"刷新",
    loadingTasks:"正在读取任务...",noTasks:"没有符合筛选条件的任务。",chooseTask:"选择一个任务，查看状态、结果与下一步。",
    refreshFailed:"刷新任务列表失败。",detailFailed:"读取该任务失败。",invalidTask:"Task ID 无效。",sessionOffline:"Executor 会话不可用。",
    completedReviewPending:"执行完成 · 待验收",completedReviewBlocked:"执行完成 · 验收受阻",
    problemActions:"问题与操作",workHistory:"执行历史",execution:"执行消耗",technicalDetails:"技术详情",
    technicalHint:"Wake · Cleanup · Release · Events",
    completedNotAccepted:"Worker 执行完成，未记录 Master 验收结论。",
    review:"验收",current:"当前",usageSummaryNotObserved:"未观测到执行消耗",executionUsage:"执行消耗",
    waitingMaster:"等待 Master 复核。本页面不会伪造验收。",
    workerActive:"Worker 或派发仍在进行，继续与关联返工保持禁用。",
    resultFailed:"Result 失败",resultFailedHint:"Worker Result 失败。这不是 Master 验收结论；请检查错误并选择安全的恢复操作。",
    resultIssues:"Result 问题",resultIssuesHint:"Worker 报告了问题。这不是 Master 验收结论；请先复核 Result 再选择下一步。",
    cleanup:"Cleanup",cleanupPending:"Cleanup 仍在等待。",cleanupUnverified:"Cleanup 未验证，Release 未被证明。",cleanupVerified:"Cleanup 已验证。",cleanupNotRequired:"无需 Cleanup。",cleanupNotStarted:"Cleanup 尚未开始。",cleanupPendingShort:"等待中。",cleanupUnverifiedShort:"未验证，Release 未被证明。",
    wake:"Wake",wakeSubmissionUnknown:"Queue 状态需要核实；页面不会自动重发。",wakeWebNotify:"仅 Web 通知，未打开官方 Queue。",
    hold:"Hold",holdActive:"活动 Hold：{reason}",noAttentionItems:"当前没有阻塞问题。",
    pendingInteraction:"待处理交互",pendingInteractionHint:"需要先回复，任务才能继续。",replyUnknownWarning:"上一次回复可能已到达 Worker。请先对账，不要自动重发；本页面不会自动重发。",
    needsMaster:"需要 Master 决策",resultSubmissionError:"Result 提交错误",
    resultMissing:"该 Attempt 未观测到 Result。",resultDetails:"Result 详情",
    issues:"问题",filesChanged:"变更文件",tests:"测试",started:"开始",finished:"结束",
    masterAccepted:"Master 已验收，最终目标已解决。",masterAcceptedShort:"Master 已验收",
    continue:"继续",continueHint:"基于这个已 Release 的 Result 创建下一个 Attempt。",continueFeedback:"给下一个 Attempt 的反馈",continueRequirements:"补充要求，每行一条",continueSubmit:"开始继续",
    rework:"创建关联返工",reworkHint:"会创建一个新 Task，继承原目标与验收边界；原 Task、Attempt 与结果完整保留。",reworkFeedback:"给新 Task 的审查反馈",reworkSubmit:"创建返工 Task",
    reply:"回复",replyForm:"回复权限请求",request:"请求",decision:"决定",reason:"原因",sendReply:"发送回复",
    decisionAllow:"允许",decisionDeny:"拒绝",decisionAccept:"接受",decisionDecline:"不接受",
    cancel:"请求取消",cancelConfirm:"请求取消当前 Attempt？这不会强制 Release。",
    cleanupRecovery:"恢复 Cleanup",cleanupRecoveryConfirm:"重新核对 Worker 与 Cleanup 事实？此操作不会清除 Hold，也不会绕过任务状态机。",
    authorizedCleanup:"授权清理",authorizedCleanupConfirm:
      "放弃所选任务并解除 Bridge 占用？历史证据保留，不会宣称执行成功；Worker 仍可能存活并并发写入 Workspace。确认即表示接受这些风险。",
    actionUnavailable:"当前任务暂时没有安全可执行的动作。",actionBlocked:"阻塞原因：{reasons}。",
    historicalReadOnly:"这是历史 Attempt，动作只作用于当前 Attempt。",
    task:"任务",attempt:"Attempt",workspace:"Workspace",updated:"更新时间",model:"模型",plan:"套餐",discount:"优惠",effort:"Effort",status:"状态",result:"Result",
    notObserved:"未观测",notAvailable:"不可用",dash:"--",unknown:"未知",
    modelObserved:"已观测",modelRequested:"请求值",modelNotObserved:"未观测",
    planCoding:"Coding Plan",planStart:"Start Plan",planOther:"其他",planNotObserved:"未观测",
    applied:"已应用",notApplied:"未应用",notApplicable:"不适用",
    inputTokens:"输入 tokens",outputTokens:"输出 tokens",cacheRead:"缓存读取",cacheWrite:"缓存写入",reasoning:"推理 tokens",totalTokens:"总 tokens",
    providerActualCost:"Provider 实际成本",
    masterUsage:"Master 消耗",workerUsage:"Worker 消耗",workerUsageHint:"该 Attempt 记录的 Token 消耗。",
    usageSource:"Usage 来源",finality:"最终性",observedAt:"观测时间",
    notObservedFields:"未观测：{fields}。",
    tokens:"{n} tokens",oneFileChanged:"变更 {n} 个文件",filesChangedCount:"变更 {n} 个文件",
    noTests:"未报告测试",testsSummary:"{passed} 通过",testsFailedSummary:"{failed} 失败",testsNotRunSummary:"{notRun} 未运行",
    events:"Events",loadingEvents:"正在加载完整 Events...",eventsComplete:"全部 Events 已加载",eventsFiltered:"Attempt {n}",eventsCount:"{n} 条 Events",eventsEmpty:"该 Attempt 没有记录 Events。",
    showDetails:"详情",hideDetails:"收起详情",
    executorUnavailable:"Executor 不可用。",executorRecoveryHint:"打开任务或执行操作会尝试本地 Lease 恢复；原 Worker 仍存活时不会启动第二个 Worker。",
    diagnosticsTitle:"诊断与显式操作",close:"关闭",
    diagNotice:"实验性入口。打开本对话框不会发出模型、Runtime 探针或 Billing 请求；以下外部读取或写入都必须由你显式点击。",
    runtime:"Runtime",runtimeHelp:"静态安装检查、授权的零模型协议检查与 Candidate Report 导出。",
    inspectRuntime:"检查",staticCheck:"静态检查",protocolProbe:"协议探针",exportReport:"导出报告",
    costLab:"成本证据",costHelp:"安装环境与历史证据；验证入口只加载显式确认状态，不会在这里启动。",
    loadEnvironment:"环境",loadHistory:"历史",loadVerification:"验证入口",settings:"设置",
    autoWakeHelp:"Auto Wake 默认开启。关闭后 Worker 完成只记录 web_notify/auto_wake_disabled，不调用官方 Queue。",autoWake:"Auto Wake",saveSettings:"保存设置",
    settingsLoaded:"设置已读取。",settingsSaved:"Auto Wake 设置已保存。",runtimeInspectFailed:"Runtime 检查失败。",costEnvironmentLoaded:"成本证据环境已读取。",costHistoryLoaded:"成本证据历史已读取。",verificationLoaded:"验证入口已读取；启动仍需既有显式确认流程。",reportReady:"Candidate Report 已下载。",reportUnavailable:"Candidate Report 不可用。",noHistory:"没有历史证据。",diagNoOutput:"请选择一个显式诊断操作。",
    taskActionDone:"请求已受理。",loadingDetail:"正在读取任务详情...",
    wakeNotObserved:"未观测到 Wake",wakeWebNotifyShort:"仅 Web 通知",wakeSubmissionUnknownShort:"需要核实",wakeIntent:"已记录投递意图",wakeQueued:"已进入投递队列",wakeTurnStarted:"已开始新 Turn",
    release:"Release",releaseHeld:"Release 被 Hold 阻止。",releaseNotReleased:"尚未 Release。",released:"已 Release",releaseVerified:"Release 时 Cleanup 已验证",releaseUnverified:"已 Release，但 Cleanup 未验证",
    cleanupIdentityUnverified:"无法确认 Worker 身份，Cleanup 未能验证；没有执行 Release。"
  }
};
var STATUS={
  en:{queued:"Queued",running:"Running",completed:"Execution completed",failed:"Failed",cancelled:"Cancelled",waiting_for_master:"Waiting for Master"},
  "zh-CN":{queued:"排队中",running:"执行中",completed:"执行完成",failed:"失败",cancelled:"已取消",waiting_for_master:"等待 Master"}
};
var REASON={
  en:{pending_interaction:"Pending interaction",interaction_reply_outcome_unknown:"Reply outcome unknown",cleanup_pending:"Cleanup pending",cleanup_unverified:"Cleanup unverified",waiting_for_master:"Waiting for Master",needs_master_decision:"Needs Master decision",task_failed:"Task failed",worker_active:"Task is still running",wake_submission_unknown:"Queue state needs verification",wake_web_notify:"Web notification",result_submission_failed:"Result submission failed",release_not_completed:"Release is not complete",release_cleanup_unverified:"Release Cleanup is unverified",administrative_release_unverified:"Administrative Release is unverified"},
  "zh-CN":{pending_interaction:"待处理交互",interaction_reply_outcome_unknown:"回复结果未知",cleanup_pending:"Cleanup 等待中",cleanup_unverified:"Cleanup 未验证",waiting_for_master:"等待 Master",needs_master_decision:"需要 Master 决策",task_failed:"任务失败",worker_active:"任务仍在运行",wake_submission_unknown:"Queue 状态需要核实",wake_web_notify:"Web 通知",result_submission_failed:"Result 提交失败",release_not_completed:"Release 尚未完成",release_cleanup_unverified:"Release 时 Cleanup 未验证",administrative_release_unverified:"管理式 Release 未验证"}
};
var state={lang:"zh-CN",theme:"system",tasks:[],detail:null,detailError:"",listError:"",selected:null,selectedAttempt:null,filter:null,query:"",csrf:"",session:null,sessionLoaded:false,events:{taskId:null,rows:[],complete:false,loading:false,error:"",loaded:false},eventsOpen:false,technicalOpen:false,executionOpen:false,actionForm:null,busy:false,refreshTimer:null,settingsLoaded:false,settings:null,diagOutput:""};
function $(selector){return document.querySelector(selector);}
function el(tag,cls,text){var node=document.createElement(tag);if(cls)node.className=cls;if(text!==undefined&&text!==null)node.textContent=String(text);return node;}
function t(key,vars){var table=TEXT[state.lang]||TEXT.en;var value=table[key]||TEXT.en[key]||key;if(vars){Object.keys(vars).forEach(function(name){value=value.split("{"+name+"}").join(String(vars[name]));});}return value;}
function statusLabel(value){var table=STATUS[state.lang]||STATUS.en;return table[value]||value||t("unknown");}
function reasonLabel(value){var table=REASON[state.lang]||REASON.en;if(value&&value.indexOf("hold:")===0)return t("hold")+": "+(table[value.slice(5)]||value.slice(5));return table[value]||value;}
function chip(text,cls){return el("span","status-chip "+(cls||""),text);}
function number(value){return typeof value==="number"&&Number.isFinite(value)?value.toLocaleString(state.lang):t("dash");}
function formatDate(value){if(!value)return t("dash");var date=new Date(value);if(Number.isNaN(date.getTime()))return t("dash");return date.toLocaleString(state.lang);}
function formatShortDate(value){if(!value)return t("dash");var date=new Date(value);if(Number.isNaN(date.getTime()))return t("dash");try{return date.toLocaleString(state.lang,{month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"});}catch(_ignore){return formatDate(value);}}
function workspaceShort(value){var text=String(value||"").trim();if(!text)return "";var parts=text.split(/[\\/]+/).filter(Boolean);return parts.length?parts[parts.length-1]:text;}
function setError(message){var box=$("#global-error");if(!box)return;box.textContent=message||"";box.classList.toggle("visible",Boolean(message));}
function toast(message,error){var node=$("#toast");if(!node)return;node.textContent=message;node.classList.toggle("error",Boolean(error));node.classList.add("show");clearTimeout(toast._timer);toast._timer=setTimeout(function(){node.classList.remove("show");},3200);}
function errorMessage(error){if(!error)return t("unknown");return error.message||String(error);}
function errorCode(error){return error&&error.code?error.code:"";}
function friendlyError(error){var code=errorCode(error);var message=errorMessage(error);if(code==="CANCEL_FAILED"&&message.indexOf("worker_identity_unverifiable")>=0)return t("cleanupIdentityUnverified");return message;}
async function api(path,options){var opts=options||{};var headers=Object.assign({},opts.headers||{});if(opts.body!==undefined)headers["Content-Type"]="application/json";if(opts.csrf){if(!state.csrf){await loadSession();}headers["X-ZCode-Bridge-CSRF"]=state.csrf;}var response=await fetch(path,{method:opts.method||"GET",headers:headers,body:opts.body});var text=await response.text();var json=null;try{json=text?JSON.parse(text):null;}catch(_ignore){json=null;}if(!response.ok||!json||json.ok===false){var error=new Error((json&&json.error&&json.error.message)||text||("HTTP "+response.status));error.code=json&&json.error&&json.error.code||("HTTP_"+response.status);throw error;}return json.result!==undefined?json.result:(json.data!==undefined?json.data:json);}
function taskIdFromLocation(){try{return new URL(location.href).searchParams.get("task_id");}catch(_ignore){return null;}}
function setTaskInLocation(id){try{var url=new URL(location.href);if(id)url.searchParams.set("task_id",id);else url.searchParams.delete("task_id");history.replaceState(null,"",url.pathname+url.search+url.hash);}catch(_ignore){}}
function applyTheme(){document.documentElement.setAttribute("data-theme",state.theme);try{localStorage.setItem("bridge.ui.theme",state.theme);}catch(_ignore){}}
function applyLanguage(){document.documentElement.setAttribute("lang",state.lang);try{localStorage.setItem("bridge.ui.language",state.lang);}catch(_ignore){}var lang=$("#language");if(lang)lang.value=state.lang;document.querySelectorAll("[data-i18n]").forEach(function(node){node.textContent=t(node.getAttribute("data-i18n"));});var searchBox=$("#task-search");if(searchBox)searchBox.placeholder=t("searchTasks");var bucket=$("#bucket-filter");if(bucket)bucket.setAttribute("aria-label",t("filterTasks"));var notice=$("#experimental-notice");if(notice)notice.title=t("experimentalNotice");document.title=t("brand");renderExecutor();renderList();renderDetail();}
function taskBucket(task){if(task.needs_attention)return "attention";if(task.status==="queued"||task.status==="running")return "running";return "completed";}
function counts(){var result={running:0,attention:0,completed:0};state.tasks.forEach(function(task){result[taskBucket(task)]+=1;});return result;}
function modelText(model){if(!model||model.state==="not_observed")return t("modelNotObserved");return model.model_id||t("dash");}
function modelSourceText(model){if(!model)return t("modelNotObserved");if(model.state==="observed")return t("modelObserved");if(model.state==="requested")return t("modelRequested");return t("modelNotObserved");}
function planText(plan){if(!plan||plan.kind==="not_observed")return t("planNotObserved");if(plan.kind==="coding_plan")return t("planCoding");if(plan.kind==="start_plan")return t("planStart");return t("planOther");}
function discountText(discount){if(!discount)return t("notObserved");if(discount.state==="applied")return t("applied");if(discount.state==="not_applied")return t("notApplied");if(discount.state==="not_applicable")return t("notApplicable");return t("notObserved");}
function cleanupText(cleanup){if(!cleanup||cleanup.state==="not_started")return t("cleanupNotStarted");if(cleanup.state==="not_required")return t("cleanupNotRequired");if(cleanup.state==="pending")return t("cleanupPending");if(cleanup.state==="verified")return t("cleanupVerified");if(cleanup.state==="unverified")return t("cleanupUnverified");return t("unknown");}
function releaseText(release){if(!release||release.state==="not_released")return t("releaseNotReleased");if(release.state==="held")return t("releaseHeld");if(release.state==="released")return t("released");return t("unknown");}
function effortText(model){var effort=model&&model.effort;if(!effort||effort.state==="not_observed"||!effort.value)return t("notObserved");return effort.value;}
function effortSourceText(model){var effort=model&&model.effort;if(!effort||effort.state==="not_observed")return t("notObserved");return effort.state==="observed"?t("modelObserved"):t("modelRequested");}
function metricText(value){return value===null||value===undefined?t("notObserved"):number(value);}
function usageTotalText(usage){if(!usage||usage.state!=="observed"||usage.total_tokens===null||usage.total_tokens===undefined)return t("notObserved");return t("tokens",{n:number(usage.total_tokens)});}
function modelPlanText(attempt){
  var modelObserved=attempt&&attempt.model&&attempt.model.state!=="not_observed";
  var planObserved=attempt&&attempt.plan&&attempt.plan.kind!=="not_observed";
  if(!modelObserved&&!planObserved)return t("modelPlanNotObserved");
  return modelText(attempt&&attempt.model)+" / "+planText(attempt&&attempt.plan);
}
function executionSummaryValues(attempt){
  var values=[];
  if(attempt.model&&attempt.model.state!=="not_observed")values.push(modelText(attempt.model));
  if(attempt.plan&&attempt.plan.kind!=="not_observed")values.push(planText(attempt.plan));
  if(attempt.discount&&attempt.discount.state!=="not_observed")values.push(discountText(attempt.discount));
  var usage=attempt.usage;
  if(usage&&usage.state==="observed"&&usage.total_tokens!==null&&usage.total_tokens!==undefined)values.push(t("tokens",{n:number(usage.total_tokens)}));
  if(!values.length)values.push(t("usageSummaryNotObserved"));
  return values;
}
function taskTitle(task){return task&&task.name||task&&task.objective||(task&&task.task_id)||t("task");}
function taskMatchesQuery(task,query){if(!query)return true;var hay=[taskTitle(task),task.task_id,task.workspace,task.objective].join(" ").toLowerCase();return hay.indexOf(query)>=0;}
function taskStatusMeta(task){
  var label=statusLabel(task.status),cls=task.status;
  if(task.master_accepted===true){label=t("masterAcceptedShort");cls="ok";}
  else if(task.status==="completed"){
    var caps=task.action_capabilities||{};
    if(caps.can_continue||caps.can_rework){label=t("completedReviewPending");cls="completed review-pending";}
    else{label=t("completedReviewBlocked");cls="completed review-blocked";}
  }
  if(task.status==="waiting_for_master"){label=t("waitingMasterShort");cls="waiting_for_master";}
  return {label:label,cls:cls};
}
function attentionSummary(task){
  var reasons=Array.isArray(task.attention_reasons)?task.attention_reasons:[];
  var labels=[];
  reasons.forEach(function(reason){var label=reasonLabel(reason);if(labels.indexOf(label)<0)labels.push(label);});
  var shown=labels.slice(0,2);
  if(labels.length>2)shown.push("+"+String(labels.length-2));
  return shown.join(" · ");
}
function metaItem(text,mono){return el("span","task-meta-item"+(mono?" mono":""),text);}
function fileSummary(count){return count===1?t("oneFileChanged",{n:count}):t("filesChangedCount",{n:count});}
function testsSummary(tests){
  var values=Array.isArray(tests)?tests:[];
  if(!values.length)return t("noTests");
  var passed=values.filter(function(test){return test.status==="passed";}).length;
  var failed=values.filter(function(test){return test.status==="failed";}).length;
  var notRun=values.filter(function(test){return test.status==="not_run";}).length;
  var parts=[];
  if(passed)parts.push(t("testsSummary",{passed:passed}));
  if(failed)parts.push(t("testsFailedSummary",{failed:failed}));
  if(notRun)parts.push(t("testsNotRunSummary",{notRun:notRun}));
  return parts.join(" · ");
}
function renderExecutor(){
  var notice=$("#executor-notice");if(!notice)return;
  if(!state.sessionLoaded){notice.hidden=true;notice.textContent="";return;}
  var status=state.session&&state.session.state?String(state.session.state):"unknown";
  notice.setAttribute("data-state",status);
  if(status==="active"||status==="idle"){notice.hidden=true;notice.textContent="";return;}
  notice.hidden=false;notice.textContent=t("executorUnavailable")+" "+t("executorRecoveryHint");
}
function renderList(){renderTaskInbox();}
function renderTaskInbox(){
  var list=$("#task-list");if(!list)return;
  var current=counts();
  $("#count-running").textContent=current.running;
  $("#count-attention").textContent=current.attention;
  $("#count-completed").textContent=current.completed;
  document.querySelectorAll(".summary-item").forEach(function(button){
    var active=button.getAttribute("data-filter")===state.filter;
    button.classList.toggle("active",active);
    button.setAttribute("aria-pressed",active?"true":"false");
  });
  var bucket=$("#bucket-filter");if(bucket)bucket.value=state.filter||"";
  list.replaceChildren();
  if(state.listError){list.appendChild(el("div","empty",state.listError));return;}
  var query=String(state.query||"").trim().toLowerCase();
  var visible=state.tasks.filter(function(task){return (!state.filter||taskBucket(task)===state.filter)&&taskMatchesQuery(task,query);})
    .sort(function(a,b){
      if(Boolean(a.needs_attention)!==Boolean(b.needs_attention))return a.needs_attention?-1:1;
      return String(b.updated_at||"").localeCompare(String(a.updated_at||""))||String(a.task_id).localeCompare(String(b.task_id));
    });
  if(!visible.length){list.appendChild(el("div","empty",t("noTasks")));return;}
  visible.forEach(function(task){
    var meta=taskStatusMeta(task);
    var button=el("button","task-row "+(task.task_id===state.selected?"selected ":"")+(task.needs_attention?"attention":""));
    button.type="button";
    button.setAttribute("data-task-id",task.task_id);
    button.setAttribute("aria-label",taskTitle(task)+", "+meta.label+(task.needs_attention?", "+attentionSummary(task):""));
    var main=el("span","task-main");
    var line1=el("span","task-line task-line-title");
    line1.appendChild(el("span","task-name",taskTitle(task)));
    line1.appendChild(chip(meta.label,meta.cls));
    main.appendChild(line1);
    var line2=el("span","task-line task-line-meta");
    var workspaceName=workspaceShort(task.workspace);
    if(workspaceName)line2.appendChild(metaItem(workspaceName));
    if(task.model&&task.model.state!=="not_observed")line2.appendChild(metaItem(modelText(task.model)));
    if(task.plan&&task.plan.kind!=="not_observed")line2.appendChild(metaItem(planText(task.plan)));
    line2.appendChild(metaItem(t("attempt")+" #"+String(task.attempt)));
    if(task.updated_at)line2.appendChild(metaItem(formatShortDate(task.updated_at)));
    main.appendChild(line2);
    if(task.needs_attention){
      var problem=attentionSummary(task);
      if(problem)main.appendChild(el("span","task-line task-line-problem",problem));
    }
    button.appendChild(main);
    button.addEventListener("click",function(){void selectTask(task.task_id,true);});
    list.appendChild(button);
  });
}
function sectionTitle(title,subtitle){
  var head=el("div","region-title");
  head.appendChild(el("h3","",title));
  if(subtitle)head.appendChild(el("small","",subtitle));
  return head;
}
function renderDetail(){renderDetailV2();}
function renderDetailV2(){
  var target=$("#task-detail");if(!target)return;
  target.replaceChildren();
  target.removeAttribute("data-task-id");
  if(!state.selected){target.appendChild(el("div","detail-empty",t("chooseTask")));return;}
  if(state.detailError){target.appendChild(el("p","action-note blocked",state.detailError));return;}
  if(!state.detail){target.appendChild(el("div","detail-empty",t("loadingDetail")));return;}
  var detail=state.detail;
  target.setAttribute("data-task-id",detail.task_id);
  var attempt=currentAttempt();
  if(!attempt){target.appendChild(el("div","detail-empty",t("chooseTask")));return;}
  var meta=taskStatusMeta(detail);
  var header=el("header","task-header");
  header.setAttribute("data-region","header");
  var title=el("div","detail-title");
  var left=el("div","detail-title-main");
  left.appendChild(el("h2","",taskTitle(detail)));
  if(detail.objective&&detail.objective!==taskTitle(detail))left.appendChild(el("p","",detail.objective));
  var context=el("div","detail-context");
  context.appendChild(el("span","",t("attempt")+" #"+String(attempt.attempt)));
  if(detail.updated_at){
    context.appendChild(el("span","detail-context-sep","·"));
    context.appendChild(el("span","",t("updated")+" "+formatDate(detail.updated_at)));
  }
  left.appendChild(context);
  var chips=el("div","hero-chips");
  chips.appendChild(chip(meta.label,meta.cls));
  title.appendChild(left);title.appendChild(chips);header.appendChild(title);
  if(detail.workspace){
    var pathDetails=el("details","detail-workspace");
    var pathSummary=el("summary","");
    pathSummary.appendChild(el("span","detail-workspace-label",t("workspace")));
    pathSummary.appendChild(el("code","",workspaceShort(detail.workspace)));
    pathDetails.appendChild(pathSummary);
    var pathFull=el("div","detail-workspace-full");
    pathFull.appendChild(document.createTextNode(detail.workspace));
    pathDetails.appendChild(pathFull);
    header.appendChild(pathDetails);
  }
  target.appendChild(header);
  target.appendChild(renderProblemActions(detail,attempt,attempt.attempt===detail.attempt));
  target.appendChild(renderWorkHistory(detail,attempt));
  target.appendChild(renderExecution(detail,attempt));
  target.appendChild(renderTechnicalDetails(attempt));
}
function problemItems(detail,attempt,current){
  var items=[];
  var result=attempt.result;
  var resultFailed=Boolean(result&&(result.status==="failed"||result.error_code));
  if(resultFailed){
    items.push({kind:"bad",label:t("resultFailed"),text:(result.error_code?result.error_code+". ":"")+t("resultFailedHint")});
  }
  if(result&&result.issues&&result.issues.length){
    var issues=result.issues.slice(0,2).join(" · ");
    if(result.issues.length>2)issues+=" +"+(result.issues.length-2);
    items.push({kind:resultFailed?"bad":"warn",label:t("resultIssues"),text:issues});
  }
  if(result&&result.needs_master_decision)items.push({kind:"warn",label:t("needsMaster"),text:t("waitingMaster")});
  if(attempt.pending_requests&&attempt.pending_requests.length)items.push({kind:"warn",label:t("pendingInteraction"),text:t("pendingInteractionHint")});
  if(attempt.reply_outcome_unknown_requests&&attempt.reply_outcome_unknown_requests.length)items.push({kind:"bad",label:t("replyUnknownWarning"),text:""});
  if(attempt.cleanup&&attempt.cleanup.state==="pending")items.push({kind:"warn",label:t("cleanup"),text:t("cleanupPendingShort")});
  if(attempt.cleanup&&attempt.cleanup.state==="unverified")items.push({kind:"warn",label:t("cleanup"),text:t("cleanupUnverifiedShort")});
  if(attempt.hold&&attempt.hold.active)items.push({kind:"bad",label:t("hold"),text:(attempt.hold.reason_code?reasonLabel(attempt.hold.reason_code):t("unknown"))+(attempt.hold.at?" · "+formatDate(attempt.hold.at):"")});
  if(attempt.wake&&attempt.wake.state==="submission_unknown")items.push({kind:"warn",label:t("wake"),text:t("wakeSubmissionUnknown")});
  if(attempt.wake&&attempt.wake.state==="web_notify")items.push({kind:"info",label:t("wake"),text:t("wakeWebNotify")});
  if(detail.result_submission_error)items.push({kind:"bad",label:t("resultSubmissionError"),text:detail.result_submission_error});
  if(current&&detail.status==="waiting_for_master"&&!resultFailed)items.push({kind:"warn",label:t("review"),text:t("waitingMaster")});
  if(current&&detail.status==="completed"&&!resultFailed&&detail.master_accepted!==true)items.push({kind:"info",label:t("review"),text:t("completedNotAccepted")});
  if(current&&detail.status==="failed"&&!resultFailed)items.push({kind:"bad",label:statusLabel("failed"),text:t("resultFailedHint")});
  if(current&&(detail.status==="queued"||detail.status==="running"))items.push({kind:"info",label:statusLabel(detail.status),text:t("workerActive")});
  if(!items.length)items.push({kind:"ok",label:t("noAttentionItems"),text:""});
  return items;
}
function severity(items){var rank={bad:4,warn:3,info:2,ok:1};var top="ok";items.forEach(function(item){if(rank[item.kind]>rank[top])top=item.kind;});return top;}
function actionBlockerReasons(caps){
  var blockers=Array.isArray(caps.blockers)?caps.blockers:[];
  var labels=[];
  blockers.forEach(function(reason){
    if((reason==="release_not_completed"||reason==="release_cleanup_unverified")&&
      (blockers.indexOf("cleanup_unverified")>=0||blockers.indexOf("cleanup_pending")>=0))return;
    if((reason==="cleanup_unverified"||reason==="cleanup_pending")&&blockers.indexOf("worker_active")>=0)return;
    var label=reasonLabel(reason);
    if(labels.indexOf(label)<0)labels.push(label);
  });
  return labels;
}
function renderProblemActions(detail,attempt,current){
  var section=el("section","region");
  section.setAttribute("data-section","problem-actions");
  section.appendChild(sectionTitle(t("problemActions")));
  var items=problemItems(detail,attempt,current);
  var box=el("div","problem "+severity(items));
  items.forEach(function(item){
    var line=el("p","problem-line");
    line.appendChild(el("strong","",item.label));
    if(item.text){
      line.appendChild(el("span","problem-sep",": "));
      line.appendChild(document.createTextNode(item.text));
    }
    box.appendChild(line);
  });
  section.appendChild(box);
  var caps=detail.action_capabilities||{};
  if(!current){section.appendChild(el("p","action-note",t("historicalReadOnly")));return section;}
  var actions=el("div","actions");
  if(caps.can_continue){var continueButton=el("button","button primary",t("continue"));continueButton.type="button";continueButton.addEventListener("click",function(){state.actionForm=state.actionForm==="continue"?null:"continue";renderDetail();});actions.appendChild(continueButton);}
  if(caps.can_rework){var reworkButton=el("button","button",t("rework"));reworkButton.type="button";reworkButton.addEventListener("click",function(){state.actionForm=state.actionForm==="rework"?null:"rework";renderDetail();});actions.appendChild(reworkButton);}
  if(caps.can_recover_cleanup){var recoverButton=el("button","button",t("cleanupRecovery"));recoverButton.type="button";recoverButton.addEventListener("click",function(){void recoverCleanup();});actions.appendChild(recoverButton);}
  var cleanupRisk=current&&(attempt.cleanup.state!=="verified"||attempt.hold.active
    ||attempt.reply_outcome_unknown_requests.length>0
    ||attempt.wake?.state==="submission_unknown"||attempt.operation_phase==="launch_intent");
  if(current&&(caps.can_cancel||caps.can_recover_cleanup||cleanupRisk)){
    var forceButton=el("button","button danger",t("authorizedCleanup"));
    forceButton.type="button";forceButton.addEventListener("click",function(){void forceCleanup();});actions.appendChild(forceButton);
  }
  if(caps.can_reply){var replyButton=el("button","button",t("reply"));replyButton.type="button";replyButton.addEventListener("click",function(){state.actionForm=state.actionForm==="reply"?null:"reply";renderDetail();});actions.appendChild(replyButton);}
  if(caps.can_cancel){var cancelButton=el("button","button danger",t("cancel"));cancelButton.type="button";cancelButton.addEventListener("click",function(){void cancelTask();});actions.appendChild(cancelButton);}
  if(actions.children.length)section.appendChild(actions);
  var blockers=actionBlockerReasons(caps);
  if(!caps.can_continue&&!caps.can_rework&&blockers.length&&detail.status!=="queued"&&detail.status!=="running")section.appendChild(el("p","action-note blocked",t("actionBlocked",{reasons:blockers.join("; ")})));
  else if(!actions.children.length)section.appendChild(el("p","action-note",t("actionUnavailable")));
  if(state.actionForm==="continue"&&caps.can_continue)section.appendChild(renderContinueForm());
  if(state.actionForm==="rework"&&caps.can_rework)section.appendChild(renderReworkForm());
  if(state.actionForm==="reply"&&caps.can_reply)section.appendChild(renderReplyForm(attempt));
  return section;
}
function renderWorkHistory(detail,attempt){
  var section=el("section","region");
  section.setAttribute("data-section","work-history");
  section.appendChild(sectionTitle(t("workHistory")));
  var tabs=el("div","attempts");
  detail.attempts.forEach(function(item){
    var button=el("button","attempt"+(item.attempt===state.selectedAttempt?" active":""));
    button.type="button";
    button.setAttribute("aria-pressed",item.attempt===state.selectedAttempt?"true":"false");
    button.appendChild(el("strong","","Attempt #"+String(item.attempt)+(item.current?" · "+t("current"):"")));
    button.appendChild(el("span","",formatShortDate(item.updated_at)));
    button.appendChild(chip(statusLabel(item.status),item.status));
    button.addEventListener("click",function(){state.selectedAttempt=item.attempt;state.actionForm=null;renderDetail();if(state.eventsOpen)void ensureEvents(false);});
    tabs.appendChild(button);
  });
  section.appendChild(tabs);
  var result=attempt.result;
  var block=el("div","result-block");
  if(result){
    if(result.summary)block.appendChild(el("p","result-summary",result.summary));
    var metrics=el("div","result-metrics");
    var files=Array.isArray(result.files_changed)?result.files_changed.length:0;
    var tests=Array.isArray(result.tests)?result.tests.length:0;
    if(files)metrics.appendChild(el("span","",fileSummary(files)));
    if(tests)metrics.appendChild(el("span","",testsSummary(result.tests)));
    if(metrics.children.length)block.appendChild(metrics);
    var hasDetails=(result.issues&&result.issues.length)||(result.files_changed&&result.files_changed.length)||(result.tests&&result.tests.length)||result.error_code||result.started_at||result.finished_at;
    if(hasDetails){
      var details=el("details","result-details");
      details.appendChild(el("summary","",t("resultDetails")));
      var body=el("div","result-detail-body");
      if(result.error_code){body.appendChild(el("p","detail-label",t("status")+"  "+result.error_code));}
      if(result.issues&&result.issues.length){
        body.appendChild(el("p","detail-label",t("issues")));
        var issueList=el("ul","detail-list");
        result.issues.forEach(function(issue){issueList.appendChild(el("li","",issue));});
        body.appendChild(issueList);
      }
      if(result.files_changed&&result.files_changed.length){
        body.appendChild(el("p","detail-label",t("filesChanged")));
        var fileList=el("ul","detail-list");
        result.files_changed.forEach(function(file){fileList.appendChild(el("li","",file));});
        body.appendChild(fileList);
      }
      if(result.tests&&result.tests.length){
        body.appendChild(el("p","detail-label",t("tests")));
        var testList=el("ul","detail-list");
        result.tests.forEach(function(test){
          var row=el("li","test-row"+(test.status==="failed"?" test-failed":test.status==="not_run"?" test-not-run":""));
          row.textContent=test.status+"  "+test.command+(test.details?"\n"+test.details:"");
          testList.appendChild(row);
        });
        body.appendChild(testList);
      }
      if(result.started_at||result.finished_at){
        var times=el("div","result-metrics");
        if(result.started_at)times.appendChild(el("span","",t("started")+" "+formatDate(result.started_at)));
        if(result.finished_at)times.appendChild(el("span","",t("finished")+" "+formatDate(result.finished_at)));
        body.appendChild(times);
      }
      details.appendChild(body);block.appendChild(details);
    }
  }else{
    block.appendChild(el("p","action-note",t("resultMissing")));
  }
  section.appendChild(block);
  return section;
}
function renderExecution(detail,attempt){
  var details=el("details","region execution-region");
  details.setAttribute("data-section","execution");
  details.open=state.executionOpen;
  var summary=el("summary","");
  summary.appendChild(el("span","execution-title",t("execution")));
  var line=el("span","execution-line");
  var values=executionSummaryValues(attempt);
  values.forEach(function(value,index){
    if(index)line.appendChild(el("span","execution-sep","·"));
    line.appendChild(el("span","",value));
  });
  summary.appendChild(line);
  details.appendChild(summary);
  details.addEventListener("toggle",function(){state.executionOpen=details.open;});
  var body=el("div","execution-body");
  var grid=el("div","exec-grid");
  var modelObserved=attempt.model&&attempt.model.state!=="not_observed";
  var planObserved=attempt.plan&&attempt.plan.kind!=="not_observed";
  var discountObserved=attempt.discount&&attempt.discount.state!=="not_observed";
  var effortObserved=attempt.model&&attempt.model.effort&&attempt.model.effort.state!=="not_observed"&&attempt.model.effort.value;
  var missing=[];
  if(modelObserved)grid.appendChild(execCell(t("model"),modelText(attempt.model)));
  else missing.push(t("model"));
  if(planObserved)grid.appendChild(execCell(t("plan"),planText(attempt.plan)));
  else missing.push(t("plan"));
  if(discountObserved)grid.appendChild(execCell(t("discount"),discountText(attempt.discount)));
  else missing.push(t("discount"));
  if(effortObserved)grid.appendChild(execCell(t("effort"),effortText(attempt.model)));
  else missing.push(t("effort"));
  var usage=attempt.usage||{state:"not_observed"};
  var tokenFields=[
    [t("inputTokens"),usage.input_tokens],
    [t("outputTokens"),usage.output_tokens],
    [t("cacheRead"),usage.cached_input_tokens],
    [t("cacheWrite"),usage.cached_write_input_tokens],
    [t("reasoning"),usage.reasoning_tokens],
    [t("totalTokens"),usage.total_tokens],
  ];
  if(usage.state==="observed"){
    tokenFields.forEach(function(field){if(field[1]!==null&&field[1]!==undefined)grid.appendChild(execCell(field[0],number(field[1])));else missing.push(field[0]);});
  }else{
    missing.push(t("executionUsage"));
  }
  if(grid.children.length)body.appendChild(grid);
  var provider=attempt.usage&&attempt.usage.provider_cost;
  if(provider&&provider.state==="observed"&&provider.amount!==null&&provider.amount!==undefined){
    var providerLine=el("div","provider-cost");
    providerLine.appendChild(el("strong","",t("providerActualCost")+": "+String(provider.amount)+(provider.currency?" "+provider.currency:"")));
    body.appendChild(providerLine);
  }else{
    missing.push(t("providerActualCost"));
  }
  if(usage.state==="observed"){
    var sourceParts=[];
    if(usage.source)sourceParts.push(t("usageSource")+": "+usage.source);
    if(usage.finality)sourceParts.push(t("finality")+": "+usage.finality);
    if(usage.observed_at)sourceParts.push(t("observedAt")+": "+formatDate(usage.observed_at));
    if(sourceParts.length)body.appendChild(el("p","action-note",sourceParts.join(" · ")));
    if(usage.conflicts&&usage.conflicts.length)body.appendChild(el("p","action-note blocked",usage.conflicts.join(", ")));
  }
  var worker=el("div","usage-scope");
  if(usage.state==="observed"&&usage.total_tokens!==null&&usage.total_tokens!==undefined){
    worker.appendChild(el("b","",t("workerUsage")+": "+usageTotalText(usage)));
    worker.appendChild(el("small","",t("workerUsageHint")));
    body.appendChild(worker);
  }else{
    missing.push(t("workerUsage"));
  }
  var master=detail.master_usage;
  if(master&&master.state==="observed"&&master.total_tokens!==null&&master.total_tokens!==undefined){
    var masterLine=el("div","usage-scope");
    masterLine.appendChild(el("b","",t("masterUsage")+": "+t("tokens",{n:number(master.total_tokens)})));
    body.appendChild(masterLine);
  }else{
    missing.push(t("masterUsage"));
  }
  var uniqueMissing=[];
  missing.forEach(function(label){if(uniqueMissing.indexOf(label)<0)uniqueMissing.push(label);});
  if(uniqueMissing.length)body.appendChild(el("p","action-note",t("notObservedFields",{fields:uniqueMissing.join(", ")})));
  details.appendChild(body);
  return details;
}
function execCell(label,value){
  var cell=el("div","exec-cell usage-fact");
  cell.appendChild(el("label","",label));
  cell.appendChild(el("strong","",value===null||value===undefined||value===""?t("dash"):String(value)));
  return cell;
}
function wakeLabel(value){
  if(!value)return t("wakeNotObserved");
  if(value==="web_notify")return t("wakeWebNotifyShort");
  if(value==="intent")return t("wakeIntent");
  if(value==="queued")return t("wakeQueued");
  if(value==="turn_started")return t("wakeTurnStarted");
  if(value==="submission_unknown")return t("wakeSubmissionUnknownShort");
  return value;
}
function techItem(title,status,detail,note){
  var box=el("div","tech-item");
  box.appendChild(el("h4","",title));
  box.appendChild(el("strong","",status));
  if(detail)box.appendChild(el("small","",detail));
  if(note)box.appendChild(el("p","tech-note",note));
  return box;
}
function technicalReason(value){if(!value)return "";if(value==="released"||value==="verified"||value==="not_required"||value==="not_started")return "";return value;}
function renderTechnicalDetails(attempt){
  var details=el("details","region technical-region");
  details.setAttribute("data-section","technical-details");
  details.open=state.technicalOpen;
  var summary=el("summary","");
  summary.appendChild(el("span","execution-title",t("technicalDetails")));
  summary.appendChild(el("small","",t("technicalHint")));
  details.appendChild(summary);
  details.addEventListener("toggle",function(){state.technicalOpen=details.open;});
  var body=el("div","execution-body");
  var grid=el("div","tech-grid");
  if(attempt.wake){
    grid.appendChild(techItem(t("wake"),wakeLabel(attempt.wake.state),attempt.wake.reason_code+" · "+formatDate(attempt.wake.at),attempt.wake.state==="submission_unknown"?t("wakeSubmissionUnknown"):attempt.wake.state==="web_notify"?t("wakeWebNotify"):""));
  }else{
    grid.appendChild(techItem(t("wake"),t("wakeNotObserved"),"",""));
  }
  grid.appendChild(techItem(t("cleanup"),cleanupText(attempt.cleanup),technicalReason(attempt.cleanup&&attempt.cleanup.reason_code),""));
  grid.appendChild(techItem(t("release"),releaseText(attempt.release),technicalReason(attempt.release&&attempt.release.reason_code),attempt.release&&attempt.release.cleanup_verified!==null?(attempt.release.cleanup_verified?t("releaseVerified"):t("releaseUnverified")):""));
  body.appendChild(grid);
  body.appendChild(renderEventsV2(attempt));
  details.appendChild(body);
  return details;
}
function renderEventsV2(attempt){
  var details=el("details","events");
  details.open=state.eventsOpen;
  var summary=el("summary","");
  summary.textContent=t("events")+" · "+t("eventsFiltered",{n:attempt.attempt});
  details.appendChild(summary);
  var body=el("div","");
  body.id="events-body";
  body.appendChild(el("p","action-note",state.events.loading?t("loadingEvents"):t("eventsEmpty")));
  details.appendChild(body);
  details.addEventListener("toggle",function(){state.eventsOpen=details.open;if(details.open)void ensureEvents(false);else{var current=document.getElementById("events-body");if(current)renderEventsInto(current,attempt);}});
  if(state.eventsOpen)void ensureEvents(false);
  return details;
}
function renderContinueForm(){
  var form=el("form","form-card");
  form.appendChild(el("p","action-note",t("continueHint")));
  var feedback=el("label","",t("continueFeedback"));
  var text=el("textarea");text.name="feedback";text.required=true;feedback.appendChild(text);form.appendChild(feedback);
  var requirements=el("label","",t("continueRequirements"));
  var req=el("textarea");req.name="additional_requirements";requirements.appendChild(req);form.appendChild(requirements);
  var row=el("div","actions");
  var submit=el("button","button primary",t("continueSubmit"));submit.type="submit";row.appendChild(submit);form.appendChild(row);
  form.addEventListener("submit",function(event){event.preventDefault();void continueTask(text.value,req.value);});
  return form;
}
function renderReworkForm(){
  var form=el("form","form-card");
  form.appendChild(el("p","action-note",t("reworkHint")));
  var feedback=el("label","",t("reworkFeedback"));
  var text=el("textarea");text.name="feedback";text.required=true;feedback.appendChild(text);form.appendChild(feedback);
  var row=el("div","actions");
  var submit=el("button","button",t("reworkSubmit"));submit.type="submit";row.appendChild(submit);form.appendChild(row);
  form.addEventListener("submit",function(event){event.preventDefault();void reworkTask(text.value);});
  return form;
}
function renderReplyForm(attempt){
  var form=el("form","form-card");
  form.appendChild(el("p","action-note",t("replyForm")));
  var grid=el("div","form-grid");
  var request=el("label","",t("request"));
  var select=el("select");select.name="request_id";
  attempt.pending_requests.forEach(function(value){var option=el("option","",value);option.value=value;select.appendChild(option);});
  request.appendChild(select);grid.appendChild(request);
  var decision=el("label","",t("decision"));
  var decisionSelect=el("select");decisionSelect.name="decision";
  [["allow",t("decisionAllow")],["deny",t("decisionDeny")],["accept",t("decisionAccept")],["decline",t("decisionDecline")]].forEach(function(pair){var option=el("option","",pair[1]);option.value=pair[0];decisionSelect.appendChild(option);});
  decision.appendChild(decisionSelect);grid.appendChild(decision);
  var reason=el("label","wide",t("reason"));
  var reasonInput=el("input");reasonInput.name="reason";reason.appendChild(reasonInput);grid.appendChild(reason);
  form.appendChild(grid);
  var row=el("div","actions");
  var submit=el("button","button primary",t("sendReply"));submit.type="submit";row.appendChild(submit);form.appendChild(row);
  form.addEventListener("submit",function(event){event.preventDefault();void replyInteraction(select.value,decisionSelect.value,reasonInput.value);});
  return form;
}
function renderEventsInto(target,attempt){
  if(!target)return;
  target.replaceChildren();
  if(!state.eventsOpen)return;
  if(state.events.loading){target.appendChild(el("p","action-note",t("loadingEvents")));return;}
  if(state.events.error){target.appendChild(el("p","action-note blocked",state.events.error));return;}
  var rows=state.events.rows.filter(function(event){return event.attempt===attempt.attempt;}).sort(function(a,b){return Number(a.seq)-Number(b.seq);});
  target.appendChild(el("p","action-note",t("eventsCount",{n:rows.length})+(state.events.complete?" · "+t("eventsComplete"):"")));
  if(!rows.length){target.appendChild(el("p","action-note",t("eventsEmpty")));return;}
  var list=el("div","event-list");
  rows.forEach(function(event){
    var row=el("div","event-row");
    var top=el("div","event-top");
    top.appendChild(el("span","event-seq","#"+String(event.seq)));
    top.appendChild(el("span","event-type",event.type||"event"));
    top.appendChild(el("span","event-seq",formatDate(event.at)+(event.attempt?" · Attempt #"+String(event.attempt):"")));
    row.appendChild(top);
    row.appendChild(el("div","event-summary",event.summary||""));
    if(event.details&&Object.keys(event.details).length){
      var details=el("details","event-details");
      details.appendChild(el("summary","",t("showDetails")));
      var pre=el("pre","");pre.textContent=JSON.stringify(event.details,null,2);details.appendChild(pre);row.appendChild(details);
    }
    list.appendChild(row);
  });
  target.appendChild(list);
}
async function ensureEvents(force){
  var attempt=currentAttempt();if(!state.detail||!attempt)return;
  if(state.events.taskId!==state.detail.task_id){state.events={taskId:state.detail.task_id,rows:[],complete:false,loading:false,error:"",loaded:false};}
  if(state.events.loaded&&!force){var mount=document.getElementById("events-body");if(mount)renderEventsInto(mount,attempt);return;}
  if(state.events.loading)return;
  state.events.loading=true;state.events.error="";
  var currentMount=document.getElementById("events-body");if(currentMount)renderEventsInto(currentMount,attempt);
  var rows=[];var after=0;var complete=false;
  try{
    for(var pageIndex=0;pageIndex<500;pageIndex+=1){
      var path="/api/tasks/"+encodeURIComponent(state.detail.task_id)+"/events?limit=200&include_attempt=true&view=summary&max_bytes=33554432";
      if(after>0)path+="&after_seq="+String(after);
      var page=await api(path);
      if(Array.isArray(page.events))rows=rows.concat(page.events);
      if(!page.has_more){complete=true;break;}
      if(!Number.isSafeInteger(page.next_seq)||page.next_seq<=after)break;
      after=page.next_seq;
    }
    state.events.rows=rows;state.events.complete=complete;state.events.loaded=true;
  }catch(error){state.events.error=errorMessage(error);}
  finally{state.events.loading=false;}
  var mountNow=document.getElementById("events-body");
  if(mountNow&&state.eventsOpen&&state.detail&&state.selected)renderEventsInto(mountNow,currentAttempt()||attempt);
}
async function loadSession(){try{var session=await api("/api/session");state.csrf=session.csrf_token||"";state.session=session.executor||null;state.sessionLoaded=true;renderExecutor();return session;}catch(error){state.session=null;state.sessionLoaded=true;renderExecutor();throw error;}}
async function loadTasks(){
  try{
    var all=[];var after=null;
    for(var pageIndex=0;pageIndex<100;pageIndex+=1){
      var path="/api/tasks?limit=100";if(after)path+="&after_task_id="+encodeURIComponent(after);
      var page=await api(path);var rows=Array.isArray(page.tasks)?page.tasks:[];
      rows.forEach(function(task){if(task&&task.task_id)all.push(task);});
      if(!page.has_more||!page.next_task_id||page.next_task_id===after)break;
      after=page.next_task_id;
    }
    var seen={};state.tasks=all.filter(function(task){if(seen[task.task_id])return false;seen[task.task_id]=true;return true;});state.listError="";
  }catch(error){state.listError=t("refreshFailed")+" "+errorMessage(error);}
  renderList();
}
async function selectTask(id,updateUrl){
  if(!id||!/^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/u.test(id)){setError(t("invalidTask"));return;}
  setError("");
  if(state.selected!==id){state.eventsOpen=false;state.technicalOpen=false;state.executionOpen=false;state.events={taskId:null,rows:[],complete:false,loading:false,error:"",loaded:false};state.selectedAttempt=null;state.actionForm=null;}
  state.selected=id;if(updateUrl)setTaskInLocation(id);renderList();await loadDetail();
  if(updateUrl&&window.matchMedia&&window.matchMedia("(max-width:980px)").matches){var panel=document.querySelector(".detail-panel");if(panel&&panel.scrollIntoView)panel.scrollIntoView({behavior:"smooth",block:"start"});}
}
async function loadDetail(){
  var id=state.selected;if(!id)return;
  try{
    var detail=await api("/api/tasks/"+encodeURIComponent(id)+"/console");
    if(state.selected!==id)return;
    state.detail=detail;state.detailError="";
    if(state.selectedAttempt===null||!detail.attempts.some(function(attempt){return attempt.attempt===state.selectedAttempt;}))state.selectedAttempt=detail.attempt;
    renderDetail();
  }catch(error){if(state.selected!==id)return;state.detail=null;state.detailError=t("detailFailed")+" "+errorMessage(error);renderDetail();}
}
function currentAttempt(){if(!state.detail)return null;return state.detail.attempts.find(function(attempt){return attempt.attempt===state.selectedAttempt;})||null;}
function canMutate(){return !state.busy&&state.selected&&state.detail;}
async function continueTask(feedback,requirements){
  if(!canMutate())return;state.busy=true;
  try{
    var list=String(requirements||"").split(/\r?\n/u).map(function(value){return value.trim();}).filter(Boolean);
    await api("/api/tasks/"+encodeURIComponent(state.selected)+"/continue",{method:"POST",csrf:true,body:JSON.stringify({feedback:String(feedback||"").trim(),additional_requirements:list})});
    state.actionForm=null;state.selectedAttempt=null;toast(t("taskActionDone"));await loadTasks();await loadDetail();
  }catch(error){toast(errorMessage(error),true);setError(errorMessage(error));}
  finally{state.busy=false;}
}
async function reworkTask(feedback){
  if(!canMutate())return;state.busy=true;
  try{
    await api("/api/tasks/"+encodeURIComponent(state.selected)+"/rework",{method:"POST",csrf:true,body:JSON.stringify({feedback:String(feedback||"").trim()})});
    state.actionForm=null;state.selectedAttempt=null;toast(t("taskActionDone"));await loadTasks();await loadDetail();
  }catch(error){toast(errorMessage(error),true);setError(errorMessage(error));}
  finally{state.busy=false;}
}
async function replyInteraction(requestId,decision,reason){
  if(!canMutate())return;state.busy=true;
  try{
    await api("/api/tasks/"+encodeURIComponent(state.selected)+"/reply",{method:"POST",csrf:true,body:JSON.stringify({request_id:requestId,decision:decision,...(reason?{reason:String(reason)}:{})})});
    state.selectedAttempt=null;toast(t("taskActionDone"));await loadTasks();await loadDetail();if(state.eventsOpen)await ensureEvents(true);
  }catch(error){toast(errorMessage(error),true);setError(errorMessage(error));}
  finally{state.busy=false;}
}
async function cancelTask(){
  if(!canMutate())return;if(!window.confirm(t("cancelConfirm")))return;state.busy=true;
  try{
    await api("/api/tasks/"+encodeURIComponent(state.selected)+"/cancel",{method:"POST",csrf:true,body:"{}"});
    state.selectedAttempt=null;toast(t("taskActionDone"));await loadTasks();await loadDetail();if(state.eventsOpen)await ensureEvents(true);
  }catch(error){toast(errorMessage(error),true);setError(errorMessage(error));}
  finally{state.busy=false;}
}
async function forceCleanup(){
  if(!canMutate())return;if(!window.confirm(t("authorizedCleanupConfirm")))return;state.busy=true;
  try {
    await api("/api/tasks/"+encodeURIComponent(state.selected)+"/force-cleanup",{method:"POST",csrf:true,body:JSON.stringify({
      release_mode:"user_authorized_unverified_release",accept_worker_risk:true})});
    state.selectedAttempt=null;state.actionForm=null;toast(t("taskActionDone"));await loadTasks();await loadDetail();if(state.eventsOpen)await ensureEvents(true);
  } finally {state.busy=false;}
}
async function recoverCleanup(){
  if(!canMutate())return;if(!window.confirm(t("cleanupRecoveryConfirm")))return;state.busy=true;
  try{
    await api("/api/tasks/"+encodeURIComponent(state.selected)+"/recover-cleanup",{method:"POST",csrf:true,body:JSON.stringify({release_mode:"zcode_cancel_administrative_release"})});
    state.selectedAttempt=null;toast(t("taskActionDone"));await loadTasks();await loadDetail();if(state.eventsOpen)await ensureEvents(true);
  }catch(error){var message=friendlyError(error);toast(message,true);setError(message);}
  finally{state.busy=false;}
}
async function refreshAll(forceEvents){
  state.busy=true;
  try{await Promise.all([loadTasks(),state.selected?loadDetail():Promise.resolve()]);if(forceEvents&&state.eventsOpen)await ensureEvents(true);}
  finally{state.busy=false;}
}
function diagOutput(value){state.diagOutput=typeof value==="string"?value:JSON.stringify(value,null,2);var node=$("#diag-output");if(node)node.textContent=state.diagOutput;}
function diagError(error){diagOutput((error&&error.code?error.code+": ":"")+errorMessage(error));toast(errorMessage(error),true);}
async function openDiagnostics(){
  var dialog=$("#diagnostics");if(!dialog)return;
  if(!state.settingsLoaded){
    try{
      var settings=await api("/api/settings");state.settings=settings;state.settingsLoaded=true;
      var checkbox=$("#auto-wake");if(checkbox)checkbox.checked=Boolean(settings.auto_wake&&settings.auto_wake.enabled);
      diagOutput(t("settingsLoaded"));
    }catch(error){diagError(error);}
  }
  if(typeof dialog.showModal==="function")dialog.showModal();else dialog.setAttribute("open","");
}
async function saveAutoWake(){
  try{
    var checkbox=$("#auto-wake");
    var result=await api("/api/settings/auto-wake",{method:"POST",csrf:true,body:JSON.stringify({enabled:Boolean(checkbox.checked)})});
    state.settings=result;state.settingsLoaded=true;diagOutput(t("settingsSaved")+"\n"+JSON.stringify(result,null,2));toast(t("settingsSaved"));
  }catch(error){diagError(error);}
}
async function inspectRuntime(mode){
  try{
    var result;
    if(mode==="check")result=await api("/api/runtime/check",{method:"POST",csrf:true,body:"{}"});
    else if(mode==="probe")result=await api("/api/runtime/protocol-probe",{method:"POST",csrf:true,body:"{}"});
    else result=await api("/api/runtime");
    diagOutput(result);toast(mode==="probe"?t("protocolProbe"):t("inspectRuntime"));
  }catch(error){diagError(error);}
}
async function exportRuntimeReport(){
  try{
    var report=await api("/api/runtime/candidate");diagOutput(report);
    var blob=new Blob([JSON.stringify(report,null,2)+"\n"],{type:"application/json"});
    var url=URL.createObjectURL(blob);var anchor=document.createElement("a");
    anchor.href=url;anchor.download="runtime-compatibility-candidate.json";
    document.body.appendChild(anchor);anchor.click();anchor.remove();
    setTimeout(function(){URL.revokeObjectURL(url);},1000);toast(t("reportReady"));
  }catch(error){diagError(error);}
}
async function costDiagnostic(mode){
  try{
    var path=mode==="history"?"/api/cost-lab/history":mode==="verification"?"/api/cost-lab/session":"/api/cost-lab/environment";
    var result=await api(path);diagOutput(result);
    toast(mode==="history"?t("costHistoryLoaded"):mode==="verification"?t("verificationLoaded"):t("costEnvironmentLoaded"));
  }catch(error){diagError(error);}
}
function bindUi(){
  var language=$("#language");var theme=$("#theme");
  language.value=state.lang;theme.value=state.theme;
  language.addEventListener("change",function(){state.lang=language.value;applyLanguage();});
  theme.addEventListener("change",function(){state.theme=theme.value;applyTheme();});
  $("#refresh-tasks").addEventListener("click",function(){void refreshAll(false);});
  var search=$("#task-search");if(search)search.addEventListener("input",function(){state.query=search.value||"";renderList();});
  var bucket=$("#bucket-filter");if(bucket)bucket.addEventListener("change",function(){state.filter=bucket.value||null;renderList();});
  document.querySelectorAll(".summary-item").forEach(function(button){
    button.addEventListener("click",function(){
      var value=button.getAttribute("data-filter");
      state.filter=state.filter===value?null:value;
      renderList();
      if(state.selected)void loadDetail();
    });
  });
  $("#diagnostics-open").addEventListener("click",function(){void openDiagnostics();});
  $("#diagnostics-close").addEventListener("click",function(){var dialog=$("#diagnostics");if(dialog)if(typeof dialog.close==="function")dialog.close();else dialog.removeAttribute("open");});
  $("#diag-save-settings").addEventListener("click",function(){void saveAutoWake();});
  $("#diag-runtime-inspect").addEventListener("click",function(){void inspectRuntime("inspect");});
  $("#diag-runtime-check").addEventListener("click",function(){void inspectRuntime("check");});
  $("#diag-runtime-probe").addEventListener("click",function(){void inspectRuntime("probe");});
  $("#diag-runtime-report").addEventListener("click",function(){void exportRuntimeReport();});
  $("#diag-cost-environment").addEventListener("click",function(){void costDiagnostic("environment");});
  $("#diag-cost-history").addEventListener("click",function(){void costDiagnostic("history");});
  $("#diag-cost-verification").addEventListener("click",function(){void costDiagnostic("verification");});
  var diag=$("#diagnostics");
  if(diag)diag.addEventListener("click",function(event){if(event.target===diag){if(typeof diag.close==="function")diag.close();else diag.removeAttribute("open");}});
  window.addEventListener("popstate",function(){var id=taskIdFromLocation();if(id)void selectTask(id,false);});
  document.addEventListener("visibilitychange",function(){if(document.visibilityState==="visible")void refreshAll(false);});
}
async function bootstrap(){
  try{var savedTheme=localStorage.getItem("bridge.ui.theme");if(savedTheme==="light"||savedTheme==="dark"||savedTheme==="system")state.theme=savedTheme;}catch(_ignore){}
  try{var savedLang=localStorage.getItem("bridge.ui.language");if(savedLang==="en"||savedLang==="zh-CN")state.lang=savedLang;else if(navigator.language&&navigator.language.indexOf("zh")===0)state.lang="zh-CN";}catch(_ignore){}
  applyTheme();bindUi();applyLanguage();
  try{await loadSession();}catch(error){setError(t("sessionOffline")+" "+errorMessage(error));}
  await loadTasks();
  var deep=taskIdFromLocation();
  if(deep){await selectTask(deep,false);}
  else if(state.tasks.length){var preferred=state.tasks.find(function(task){return task.needs_attention;})||state.tasks[0];await selectTask(preferred.task_id,false);}
  state.refreshTimer=setInterval(function(){if(document.visibilityState==="visible")void refreshAll(false);},10000);
}
document.addEventListener("DOMContentLoaded",function(){void bootstrap();});
})();
</script>
</body>
</html>`;
}

// src/web/console-ui.ts
function resolveBrandIconPath(moduleUrl) {
  const moduleDirectory = path24.dirname(fileURLToPath9(moduleUrl));
  const candidates = [];
  if (path24.basename(moduleDirectory) === "dist" && existsSync9(path24.join(path24.dirname(moduleDirectory), "worker", "worker-main.mjs"))) {
    candidates.push(path24.join(path24.dirname(moduleDirectory), "assets", "icon.png"));
  }
  let current = moduleDirectory;
  for (; ; ) {
    const pluginRoot = path24.join(current, "plugins", "codex-zcode-bridge");
    if (existsSync9(path24.join(pluginRoot, "worker", "worker-main.mjs"))) {
      candidates.push(path24.join(pluginRoot, "assets", "icon.png"));
      break;
    }
    const parent = path24.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  for (const candidate of candidates) {
    if (existsSync9(candidate)) return candidate;
  }
  throw new Error("brand_icon_unavailable");
}
var brandIconPath = resolveBrandIconPath(import.meta.url);
var BRAND_ICON_DATA_URI = `data:image/png;base64,${readFileSync7(brandIconPath).toString("base64")}`;
var OPERATIONS_CONSOLE_HTML = renderTaskConsoleHtml(BRAND_ICON_DATA_URI);

// src/web/server.ts
var LOOPBACK_HOST2 = "127.0.0.1";
var MAX_BODY_BYTES = 64 * 1024;
var MAX_FULL_RESULT_BYTES = 2 * 1024 * 1024;
var TASK_ID = /^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/u;
function failure2(status, code, message) {
  return Object.assign(new Error(message), { status, code });
}
function json(response, status, value) {
  const body = `${JSON.stringify(value)}
`;
  response.statusCode = status;
  response.setHeader("Content-Type", "application/json; charset=utf-8");
  response.setHeader("Content-Length", String(Buffer.byteLength(body)));
  response.end(body);
}
function securityHeaders(response) {
  response.setHeader("Cache-Control", "no-store");
  response.setHeader("Pragma", "no-cache");
  response.setHeader("X-Content-Type-Options", "nosniff");
  response.setHeader("X-Frame-Options", "DENY");
  response.setHeader("Referrer-Policy", "no-referrer");
  response.setHeader("Cross-Origin-Opener-Policy", "same-origin");
  response.setHeader("Cross-Origin-Resource-Policy", "same-origin");
  response.setHeader(
    "Content-Security-Policy",
    "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
  );
}
function isLoopback(remoteAddress) {
  return remoteAddress === "127.0.0.1" || remoteAddress === "::1" || remoteAddress === "::ffff:127.0.0.1";
}
function allowedHosts(port) {
  return /* @__PURE__ */ new Set([
    `127.0.0.1:${port}`,
    `localhost:${port}`,
    `[::1]:${port}`
  ]);
}
function allowedOrigins(port) {
  return /* @__PURE__ */ new Set([
    `http://127.0.0.1:${port}`,
    `http://localhost:${port}`,
    `http://[::1]:${port}`
  ]);
}
function validMutation(request, port, csrfToken) {
  const origin = request.headers.origin;
  if (typeof origin !== "string" || !allowedOrigins(port).has(origin)) return false;
  if (request.headers["x-zcode-bridge-csrf"] !== csrfToken) return false;
  const fetchSite = request.headers["sec-fetch-site"];
  return fetchSite === void 0 || fetchSite === "same-origin" || fetchSite === "none";
}
async function readJson2(request) {
  const declared = request.headers["content-length"];
  if (declared !== void 0) {
    const length = Number(declared);
    if (!Number.isSafeInteger(length) || length < 0 || length > MAX_BODY_BYTES) {
      throw failure2(413, "WEB_BODY_TOO_LARGE", "request body exceeds the 64 KiB limit");
    }
  }
  const chunks = [];
  let total = 0;
  for await (const chunk of request) {
    const bytes = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
    total += bytes.length;
    if (total > MAX_BODY_BYTES) throw failure2(413, "WEB_BODY_TOO_LARGE", "request body exceeds the 64 KiB limit");
    chunks.push(bytes);
  }
  if (total === 0) return {};
  let parsed;
  try {
    parsed = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  } catch {
    throw failure2(400, "WEB_INVALID_JSON", "request body must be valid JSON");
  }
  if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw failure2(400, "WEB_INVALID_JSON", "request body must be a JSON object");
  }
  return parsed;
}
function taskIdFromPath(value) {
  if (!TASK_ID.test(value)) throw failure2(400, "WEB_INVALID_TASK_ID", "task_id is invalid");
  return value;
}
function decodeTaskId(value) {
  try {
    return taskIdFromPath(decodeURIComponent(value));
  } catch (error2) {
    if (error2 && typeof error2 === "object" && "status" in error2) throw error2;
    throw failure2(400, "WEB_INVALID_TASK_ID", "task_id is not valid URL encoding");
  }
}
function queryNumber(query, name, min, max) {
  const raw = query.get(name);
  if (raw === null) return void 0;
  if (!/^\d+$/u.test(raw)) throw failure2(400, "WEB_INVALID_QUERY", `${name} must be an integer`);
  const value = Number(raw);
  if (!Number.isSafeInteger(value) || value < min || value > max) {
    throw failure2(400, "WEB_INVALID_QUERY", `${name} is outside its allowed range`);
  }
  return value;
}
function queryBoolean(query, name) {
  const raw = query.get(name);
  if (raw === null) return void 0;
  if (raw === "true") return true;
  if (raw === "false") return false;
  throw failure2(400, "WEB_INVALID_QUERY", `${name} must be true or false`);
}
function taskErrorStatus(error2) {
  if (error2 && typeof error2 === "object" && "status" in error2 && typeof error2.status === "number") {
    return error2.status;
  }
  const code = error2 && typeof error2 === "object" && "code" in error2 && typeof error2.code === "string" ? error2.code : "";
  if (code === "TASK_NOT_FOUND" || code === "NOT_FOUND") return 404;
  if (code === "TASK_NOT_FINISHED" || code === "TASK_STATE" || code === "TASK_CANCEL_REQUESTED") return 409;
  if (code === "TASK_ID_CONFLICT" || code === "TASK_ALREADY_EXISTS") return 409;
  if (code === "TASK_INVALID" || code === "WEB_INVALID_INPUT") return 400;
  if (code === "TASK_PROJECTION_UNAVAILABLE") return 501;
  if (code === "provider_config_invalid" || code === "PROVIDER_CONFIG_INVALID") return 400;
  if (code === "EXECUTOR_UNAVAILABLE" || code === "SUBMISSION_UNKNOWN") return 503;
  if (code === "REQUEST_CANCELLED") return 408;
  return 500;
}
function taskErrorCode(error2) {
  if (error2 && typeof error2 === "object" && "code" in error2 && typeof error2.code === "string") return error2.code;
  return "WEB_INTERNAL_ERROR";
}
function errorMessage2(error2) {
  return error2 instanceof Error ? error2.message : String(error2);
}
async function findTaskSummary(manager, taskId) {
  let afterTaskId = null;
  for (let pageNumber = 0; pageNumber < 100; pageNumber += 1) {
    const page = await manager.listTasks({
      limit: 100,
      ...afterTaskId === null ? {} : { after_task_id: afterTaskId }
    });
    const task = page.tasks.find((candidate) => candidate.task_id === taskId);
    if (task) return task;
    if (!page.has_more || page.next_task_id === null) return null;
    afterTaskId = page.next_task_id;
  }
  return null;
}
function createTaskConsoleServer(options) {
  const state = {
    server: null,
    address: null,
    csrfToken: options.csrfToken ?? randomBytes2(32).toString("base64url"),
    sockets: /* @__PURE__ */ new Set(),
    closed: false
  };
  const requestHandler = async (request, response) => {
    securityHeaders(response);
    if (!isLoopback(request.socket.remoteAddress)) {
      throw failure2(403, "WEB_LOCAL_ONLY", "Task Console accepts loopback connections only");
    }
    const address = state.address;
    if (!address) throw failure2(503, "WEB_NOT_READY", "Task Console is not ready");
    const host = request.headers.host;
    if (typeof host !== "string" || !allowedHosts(address.port).has(host)) {
      throw failure2(403, "WEB_HOST_REJECTED", "Host must be the local Task Console origin");
    }
    const url = new URL(request.url ?? "/", address.origin);
    if (url.pathname.startsWith("/api/cost-lab/")) {
      if (!options.costLab) throw failure2(503, "COST_LAB_UNAVAILABLE", "Cost Lab is not configured");
      await options.costLab.handleRequest(request, response);
      return;
    }
    if (request.method === "GET" || request.method === "HEAD") {
      await handleRead(request, response, url);
      return;
    }
    if (request.method === "POST") {
      if (!validMutation(request, address.port, state.csrfToken)) {
        throw failure2(403, "WEB_CSRF_REJECTED", "same-origin Origin and CSRF validation failed");
      }
      await handleMutation(request, response, url);
      return;
    }
    throw failure2(405, "WEB_METHOD_NOT_ALLOWED", "method is not supported");
  };
  const handleRead = async (request, response, url) => {
    if (url.pathname === "/" || url.pathname === "/index.html") {
      const body = OPERATIONS_CONSOLE_HTML;
      response.statusCode = 200;
      response.setHeader("Content-Type", "text/html; charset=utf-8");
      response.setHeader("Content-Length", String(Buffer.byteLength(body)));
      response.end(request.method === "HEAD" ? void 0 : body);
      return;
    }
    if (url.pathname === "/api/session") {
      let executor = { state: "unknown" };
      if (options.executorStatus) {
        try {
          executor = await options.executorStatus();
        } catch (error2) {
          executor = { state: "unavailable", reason: errorMessage2(error2) };
        }
      }
      json(response, 200, {
        ok: true,
        result: {
          csrf_token: state.csrfToken,
          executor,
          console: {
            console_id: options.consoleId ?? null,
            authority_root_digest: options.authorityRootDigest ?? null,
            url: state.address?.url ?? null
          }
        }
      });
      return;
    }
    if (url.pathname === "/api/runtime") {
      if (!options.runtimeCompatibility) {
        throw failure2(503, "RUNTIME_COMPATIBILITY_UNAVAILABLE", "Runtime compatibility is not configured");
      }
      json(response, 200, { ok: true, result: await options.runtimeCompatibility.inspect() });
      return;
    }
    if (url.pathname === "/api/runtime/candidate") {
      if (!options.runtimeCompatibility) {
        throw failure2(503, "RUNTIME_COMPATIBILITY_UNAVAILABLE", "Runtime compatibility is not configured");
      }
      json(response, 200, { ok: true, result: await options.runtimeCompatibility.candidateReport() });
      return;
    }
    if (url.pathname === "/api/settings") {
      if (!options.settingsDirectory) {
        throw failure2(503, "SETTINGS_UNAVAILABLE", "Bridge settings are not configured");
      }
      json(response, 200, {
        ok: true,
        result: { auto_wake: { enabled: await readAutoWakeSetting(options.settingsDirectory) } }
      });
      return;
    }
    if (url.pathname === "/api/tasks") {
      if (options.manager.listConsoleTasks) {
        const input2 = parseConsoleListQuery(url.searchParams);
        json(response, 200, { ok: true, result: await options.manager.listConsoleTasks(input2) });
        return;
      }
      if (!options.manager.listTasks) throw failure2(501, "WEB_LIST_UNAVAILABLE", "task listing is unavailable");
      const input = parseListQuery(url.searchParams);
      json(response, 200, { ok: true, result: await options.manager.listTasks(input) });
      return;
    }
    const match = /^\/api\/tasks\/([^/]+)(?:\/(status|summary|events|result|attention|console))?$/u.exec(url.pathname);
    if (!match) throw failure2(404, "WEB_NOT_FOUND", "route not found");
    const taskId = decodeTaskId(match[1]);
    const action = match[2] ?? "status";
    if (action === "status") {
      json(response, 200, { ok: true, result: await options.manager.getStatus(taskId) });
      return;
    }
    if (action === "summary") {
      if (!options.manager.listTasks) throw failure2(501, "WEB_LIST_UNAVAILABLE", "task listing is unavailable");
      const summary = await findTaskSummary(options.manager, taskId);
      if (!summary) throw failure2(404, "TASK_NOT_FOUND", `unknown task: ${taskId}`);
      json(response, 200, { ok: true, result: summary });
      return;
    }
    if (action === "events") {
      const input = parseEventsQuery(url.searchParams, taskId);
      json(response, 200, { ok: true, result: await options.manager.getEvents(input) });
      return;
    }
    if (action === "attention") {
      if (!options.manager.getAttention) {
        throw failure2(501, "WEB_ATTENTION_UNAVAILABLE", "attention projection is unavailable");
      }
      json(response, 200, { ok: true, result: await options.manager.getAttention(taskId) });
      return;
    }
    if (action === "console") {
      if (!options.manager.getConsoleTaskDetail) {
        throw failure2(501, "TASK_PROJECTION_UNAVAILABLE", "console task projection is unavailable");
      }
      json(response, 200, { ok: true, result: consoleDetailForHttp(await options.manager.getConsoleTaskDetail(taskId)) });
      return;
    }
    const view = url.searchParams.get("view") ?? "summary";
    if (view !== "summary" && view !== "full") {
      throw failure2(400, "WEB_INVALID_QUERY", "view must be summary or full");
    }
    const value = await options.manager.getResult(taskId, view);
    const serialized = JSON.stringify(value);
    if (view === "full" && Buffer.byteLength(serialized) > MAX_FULL_RESULT_BYTES) {
      throw failure2(413, "WEB_RESULT_TOO_LARGE", "full Result exceeds the 2 MiB Web response budget; read via the paged zcode_result MCP contract");
    }
    json(response, 200, { ok: true, result: value });
  };
  const handleMutation = async (request, response, url) => {
    if (url.pathname === "/api/runtime/check") {
      if (!options.runtimeCompatibility) {
        throw failure2(503, "RUNTIME_COMPATIBILITY_UNAVAILABLE", "Runtime compatibility is not configured");
      }
      await readJson2(request);
      json(response, 200, { ok: true, result: await options.runtimeCompatibility.inspect() });
      return;
    }
    if (url.pathname === "/api/runtime/protocol-probe") {
      if (!options.runtimeCompatibility) {
        throw failure2(503, "RUNTIME_COMPATIBILITY_UNAVAILABLE", "Runtime compatibility is not configured");
      }
      await readJson2(request);
      json(response, 200, { ok: true, result: await options.runtimeCompatibility.runAuthorizedProtocolProbe() });
      return;
    }
    if (request.headers["content-type"]?.split(";")[0]?.trim().toLowerCase() !== "application/json") {
      throw failure2(415, "WEB_CONTENT_TYPE_REQUIRED", "mutations require application/json");
    }
    if (url.pathname === "/api/settings/auto-wake") {
      if (!options.settingsDirectory) {
        throw failure2(503, "SETTINGS_UNAVAILABLE", "Bridge settings are not configured");
      }
      const body2 = await readJson2(request);
      if (typeof body2.enabled !== "boolean") {
        throw failure2(400, "WEB_INVALID_SETTING", "enabled must be a boolean");
      }
      await writeAutoWakeSetting(options.settingsDirectory, body2.enabled);
      json(response, 200, {
        ok: true,
        result: { auto_wake: { enabled: body2.enabled } }
      });
      return;
    }
    const match = /^\/api\/tasks\/([^/]+)\/(cancel|force-cleanup|reply|continue|rework|recover-cleanup)$/u.exec(url.pathname);
    if (!match) throw failure2(404, "WEB_NOT_FOUND", "route not found");
    const taskId = decodeTaskId(match[1]);
    const action = match[2];
    const body = await readJson2(request);
    if (action === "recover-cleanup") {
      if (!options.manager.getConsoleTaskDetail) {
        throw failure2(501, "CLEANUP_RECOVERY_UNAVAILABLE", "Cleanup recovery is unavailable");
      }
      if (body.release_mode !== "zcode_cancel_administrative_release") {
        throw failure2(400, "WEB_INVALID_INPUT", "release_mode must be zcode_cancel_administrative_release");
      }
      const source = await options.manager.getConsoleTaskDetail(taskId);
      if (!source.action_capabilities.can_recover_cleanup) {
        throw failure2(409, "TASK_STATE", "this Task is not eligible for zcode_cancel Release recovery");
      }
      json(response, 200, {
        ok: true,
        result: {
          ...await options.manager.cancelTask(taskId),
          release_mode: "zcode_cancel_administrative_release"
        }
      });
      return;
    }
    if (action === "cancel") {
      json(response, 200, { ok: true, result: await options.manager.cancelTask(taskId) });
      return;
    }
    if (action === "force-cleanup") {
      if (body.release_mode !== "user_authorized_unverified_release" || body.accept_worker_risk !== true) {
        throw failure2(400, "WEB_INVALID_INPUT", "authorized cleanup requires explicit worker-risk acceptance");
      }
      json(response, 200, {
        ok: true,
        result: {
          ...await options.manager.cancelTask(taskId, { acceptWorkerRisk: true }),
          release_mode: "user_authorized_unverified_release"
        }
      });
      return;
    }
    if (action === "continue") {
      if (!options.manager.continueTask || !options.manager.getConsoleTaskDetail) {
        throw failure2(501, "CONTINUE_UNAVAILABLE", "task continuation is unavailable");
      }
      const source = await options.manager.getConsoleTaskDetail(taskId);
      if (!source.action_capabilities.can_continue) {
        throw failure2(409, "TASK_STATE", "this Task is not eligible for a verified continuation");
      }
      const feedback = boundedText2(body.feedback, "feedback", 16e3);
      const additionalRequirements = stringList(body.additional_requirements, "additional_requirements", 100, 4096);
      const operationId = body.operation_id === void 0 ? randomUUID10() : boundedToken(body.operation_id, "operation_id", 128);
      const receipt = await options.manager.continueTask({
        task_id: taskId,
        feedback,
        additional_requirements: additionalRequirements,
        operation_id: operationId
      });
      json(response, 200, { ok: true, result: receipt });
      return;
    }
    if (action === "rework") {
      if (!options.manager.createTask || !options.manager.getConsoleTaskDetail) {
        throw failure2(501, "REWORK_UNAVAILABLE", "related rework is unavailable");
      }
      const source = await options.manager.getConsoleTaskDetail(taskId);
      if (!source.action_capabilities.can_rework) {
        throw failure2(409, "TASK_STATE", "an active Task cannot be duplicated for related rework");
      }
      const feedback = boundedText2(body.feedback, "feedback", 16e3);
      const sourceTask = source.task;
      const context = [
        sourceTask.context?.trim(),
        "RELATED REWORK",
        `Source task: ${taskId}`,
        `Source Attempt: ${source.attempt}`,
        "Relationship: context-only; SQLite Authority has no persistent Task parent/child edge.",
        `Reviewer request: ${feedback}`
      ].filter((value) => Boolean(value)).join("\n\n");
      const next = {
        ...sourceTask,
        task_id: `task-${randomUUID10()}`,
        context
      };
      const receipt = await options.manager.createTask(next);
      json(response, 200, {
        ok: true,
        result: {
          ...receipt,
          relationship: "context_only",
          source_task_id: taskId,
          source_attempt: source.attempt
        }
      });
      return;
    }
    let input;
    try {
      input = zcodeInteractionReplyInputSchema.parse({ ...body, task_id: taskId });
    } catch (error2) {
      throw failure2(400, "WEB_INVALID_INTERACTION_REPLY", errorMessage2(error2));
    }
    json(response, 200, { ok: true, result: await options.manager.replyToInteraction(input) });
  };
  const server = http2.createServer((request, response) => {
    void requestHandler(request, response).catch((error2) => {
      if (response.headersSent) {
        response.destroy();
        return;
      }
      json(response, taskErrorStatus(error2), {
        ok: false,
        error: { code: taskErrorCode(error2), message: errorMessage2(error2) }
      });
    });
  });
  server.requestTimeout = 3e4;
  server.headersTimeout = 1e4;
  server.keepAliveTimeout = 5e3;
  server.on("connection", (socket) => {
    state.sockets.add(socket);
    socket.once("close", () => state.sockets.delete(socket));
  });
  server.on("clientError", (_error, socket) => {
    socket.end("HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n");
  });
  state.server = server;
  return {
    get address() {
      return state.address;
    },
    async start() {
      if (state.address !== null) return state.address;
      if (state.closed) throw failure2(410, "WEB_CLOSED", "Task Console server is closed");
      await new Promise((resolve, reject) => {
        const onError = (error2) => {
          server.off("listening", onListening);
          reject(error2);
        };
        const onListening = () => {
          server.off("error", onError);
          resolve();
        };
        server.once("error", onError);
        server.once("listening", onListening);
        server.listen(options.port ?? 0, LOOPBACK_HOST2);
      });
      const bound = server.address();
      if (!bound || typeof bound === "string") throw failure2(500, "WEB_ADDRESS_UNAVAILABLE", "server address unavailable");
      state.address = {
        host: LOOPBACK_HOST2,
        port: bound.port,
        origin: `http://${LOOPBACK_HOST2}:${bound.port}`,
        url: `http://${LOOPBACK_HOST2}:${bound.port}/`
      };
      try {
        await options.costLab?.mountEndpoints({
          origin: state.address.origin,
          port: state.address.port
        });
      } catch (error2) {
        state.address = null;
        await new Promise((resolve) => server.close(() => resolve()));
        throw error2;
      }
      return state.address;
    },
    async close() {
      if (state.closed) return;
      state.closed = true;
      await new Promise((resolve) => {
        if (!server.listening) {
          resolve();
          return;
        }
        server.close(() => resolve());
        for (const socket of state.sockets) socket.end();
      });
      state.address = null;
      await options.costLab?.close({ abortActive: true });
    }
  };
}
function parseListQuery(query) {
  const raw = {
    ...query.get("after_task_id") === null ? {} : { after_task_id: query.get("after_task_id") },
    ...queryNumber(query, "limit", 1, 100) === void 0 ? {} : { limit: queryNumber(query, "limit", 1, 100) },
    ...query.get("status") === null ? {} : { status: query.get("status") }
  };
  try {
    return listTasksInputSchema.parse(raw);
  } catch (error2) {
    throw failure2(400, "WEB_INVALID_QUERY", errorMessage2(error2));
  }
}
function parseConsoleListQuery(query) {
  const raw = {
    ...query.get("after_task_id") === null ? {} : { after_task_id: query.get("after_task_id") },
    ...queryNumber(query, "limit", 1, 100) === void 0 ? {} : { limit: queryNumber(query, "limit", 1, 100) },
    ...query.get("bucket") === null ? {} : { bucket: query.get("bucket") }
  };
  try {
    return consoleTaskListInputSchema.parse(raw);
  } catch (error2) {
    throw failure2(400, "WEB_INVALID_QUERY", errorMessage2(error2));
  }
}
function boundedText2(value, field, maxBytes) {
  if (typeof value !== "string" || !value.trim() || value.includes("\0") || Buffer.byteLength(value, "utf8") > maxBytes) {
    throw failure2(400, "WEB_INVALID_INPUT", `${field} must be non-empty text within ${maxBytes} bytes`);
  }
  return value.trim();
}
function boundedToken(value, field, maxLength) {
  if (typeof value !== "string" || !/^[A-Za-z0-9][A-Za-z0-9_-]*$/u.test(value) || value.length > maxLength) {
    throw failure2(400, "WEB_INVALID_INPUT", `${field} must be a bounded stable token`);
  }
  return value;
}
function stringList(value, field, maxItems, maxItemBytes) {
  if (value === void 0) return [];
  if (!Array.isArray(value) || value.length > maxItems) {
    throw failure2(400, "WEB_INVALID_INPUT", `${field} must be an array with at most ${maxItems} items`);
  }
  return value.map((entry) => {
    if (typeof entry !== "string" || !entry.trim() || entry.includes("\0") || Buffer.byteLength(entry, "utf8") > maxItemBytes) {
      throw failure2(400, "WEB_INVALID_INPUT", `${field} contains invalid text`);
    }
    return entry.trim();
  });
}
function consoleDetailForHttp(detail) {
  const task = Object.fromEntries(
    Object.entries(detail.task).filter(([key]) => key !== "context")
  );
  return { ...detail, task };
}
function parseEventsQuery(query, taskId) {
  const raw = {
    task_id: taskId,
    ...queryNumber(query, "after_seq", 0, Number.MAX_SAFE_INTEGER) === void 0 ? {} : { after_seq: queryNumber(query, "after_seq", 0, Number.MAX_SAFE_INTEGER) },
    ...queryNumber(query, "limit", 1, 200) === void 0 ? {} : { limit: queryNumber(query, "limit", 1, 200) },
    ...queryNumber(query, "wait_ms", 0, 25e3) === void 0 ? {} : { wait_ms: queryNumber(query, "wait_ms", 0, 25e3) },
    ...query.get("view") === null ? {} : { view: query.get("view") },
    ...queryBoolean(query, "include_attempt") === void 0 ? {} : { include_attempt: queryBoolean(query, "include_attempt") },
    ...query.get("scan_cursor") === null ? {} : { scan_cursor: query.get("scan_cursor") },
    ...queryNumber(query, "max_bytes", 1024, 33554432) === void 0 ? {} : { max_bytes: queryNumber(query, "max_bytes", 1024, 33554432) }
  };
  try {
    return zcodeEventsInputSchema.parse(raw);
  } catch (error2) {
    throw failure2(400, "WEB_INVALID_QUERY", errorMessage2(error2));
  }
}

// src/web/discovery.ts
import { createHash as createHash12 } from "node:crypto";
import {
  closeSync as closeSync3,
  existsSync as existsSync10,
  lstatSync as lstatSync3,
  openSync as openSync3,
  readFileSync as readFileSync8,
  unlinkSync as unlinkSync2,
  writeSync
} from "node:fs";
import path25 from "node:path";
var TASK_CONSOLE_DISCOVERY_FILE = "task-console.json";
var TASK_CONSOLE_PROTOCOL_VERSION = 1;
var DISCOVERY_LIMIT_BYTES = 16 * 1024;
var TASK_CONSOLE_ID = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/u;
var SHA256 = /^[0-9a-f]{64}$/u;
var TaskConsoleDiscoveryError = class extends Error {
  constructor(code, message = code) {
    super(message);
    this.code = code;
    this.name = "TaskConsoleDiscoveryError";
  }
  code;
};
function canonicalJson2(value) {
  return JSON.stringify(sortObject2(value)) ?? "null";
}
function sortObject2(value) {
  if (Array.isArray(value)) return value.map(sortObject2);
  if (value === null || typeof value !== "object" || value instanceof Date) return value;
  if (Object.getPrototypeOf(value) !== Object.prototype && Object.getPrototypeOf(value) !== null) return value;
  return Object.fromEntries(Object.entries(value).sort(([left], [right]) => left < right ? -1 : left > right ? 1 : 0).map(([key, item]) => [key, sortObject2(item)]));
}
function recordDigest(record3) {
  return createHash12("sha256").update(canonicalJson2(record3), "utf8").digest("hex");
}
function discoveryRoot(dataRoot) {
  let root;
  try {
    root = path25.resolve(dataRoot);
    const stat5 = lstatSync3(root);
    if (!stat5.isDirectory() || stat5.isSymbolicLink()) throw new Error("not_plain_directory");
  } catch {
    throw new TaskConsoleDiscoveryError("WEB_CONSOLE_ROOT_UNSAFE");
  }
  return root;
}
function validatedEndpoint(originValue, urlValue, port) {
  let origin;
  let url;
  try {
    origin = new URL(originValue);
    url = new URL(urlValue);
  } catch {
    throw new TaskConsoleDiscoveryError("WEB_CONSOLE_DISCOVERY_INVALID");
  }
  if (origin.origin !== originValue || origin.protocol !== "http:" || origin.hostname !== "127.0.0.1" || origin.port !== String(port) || url.origin !== originValue || url.pathname !== "/" || url.search !== "" || url.hash !== "" || !Number.isSafeInteger(port) || port < 1 || port > 65535) {
    throw new TaskConsoleDiscoveryError("WEB_CONSOLE_DISCOVERY_INVALID");
  }
}
function taskConsoleDiscoveryPath(dataRoot) {
  return path25.join(discoveryRoot(dataRoot), TASK_CONSOLE_DISCOVERY_FILE);
}
function parseRecord(value) {
  let parsed;
  try {
    parsed = JSON.parse(value);
  } catch {
    throw new TaskConsoleDiscoveryError("WEB_CONSOLE_DISCOVERY_INVALID");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new TaskConsoleDiscoveryError("WEB_CONSOLE_DISCOVERY_INVALID");
  }
  const record3 = parsed;
  if (record3.protocol_version !== TASK_CONSOLE_PROTOCOL_VERSION || typeof record3.console_id !== "string" || !TASK_CONSOLE_ID.test(record3.console_id) || typeof record3.authority_root_digest !== "string" || !SHA256.test(record3.authority_root_digest) || !Number.isSafeInteger(record3.pid) || record3.pid < 1 || record3.start_fingerprint !== null && typeof record3.start_fingerprint !== "string" || !["exact", "coarse", "unknown"].includes(record3.fingerprint_precision ?? "") || record3.identity_version !== PROCESS_IDENTITY_VERSION || typeof record3.platform !== "string" || typeof record3.captured_at !== "string" || typeof record3.origin !== "string" || typeof record3.url !== "string" || !Number.isSafeInteger(record3.port) || record3.port < 1 || record3.port > 65535 || typeof record3.started_at !== "string" || typeof record3.record_digest !== "string" || !SHA256.test(record3.record_digest)) {
    throw new TaskConsoleDiscoveryError("WEB_CONSOLE_DISCOVERY_INVALID");
  }
  let origin;
  let url;
  try {
    origin = new URL(record3.origin);
    url = new URL(record3.url);
  } catch {
    throw new TaskConsoleDiscoveryError("WEB_CONSOLE_DISCOVERY_INVALID");
  }
  if (origin.origin !== record3.origin || origin.protocol !== "http:" || origin.hostname !== "127.0.0.1" || origin.port !== String(record3.port) || url.origin !== record3.origin || url.pathname !== "/" || url.search !== "" || url.hash !== "") {
    throw new TaskConsoleDiscoveryError("WEB_CONSOLE_DISCOVERY_INVALID");
  }
  const { record_digest: recordedDigest, ...body } = record3;
  if (recordDigest(body) !== recordedDigest) {
    throw new TaskConsoleDiscoveryError("WEB_CONSOLE_DISCOVERY_INVALID");
  }
  return { ...body, record_digest: recordedDigest };
}
function readTaskConsoleDiscovery(dataRoot) {
  const file = taskConsoleDiscoveryPath(dataRoot);
  if (!existsSync10(file)) return null;
  try {
    const stat5 = lstatSync3(file);
    if (!stat5.isFile() || stat5.isSymbolicLink() || stat5.size > DISCOVERY_LIMIT_BYTES) {
      throw new TaskConsoleDiscoveryError("WEB_CONSOLE_DISCOVERY_INVALID");
    }
    const record3 = parseRecord(readFileSync8(file, "utf8"));
    if (record3.authority_root_digest !== authorityRootDigest(dataRoot)) {
      throw new TaskConsoleDiscoveryError("WEB_CONSOLE_DISCOVERY_INVALID");
    }
    return record3;
  } catch (error2) {
    if (error2 instanceof TaskConsoleDiscoveryError) throw error2;
    throw new TaskConsoleDiscoveryError("WEB_CONSOLE_DISCOVERY_INVALID");
  }
}
async function publishTaskConsoleDiscovery(input) {
  const root = discoveryRoot(input.dataRoot);
  if (!TASK_CONSOLE_ID.test(input.consoleId)) throw new TaskConsoleDiscoveryError("WEB_CONSOLE_DISCOVERY_INVALID");
  validatedEndpoint(input.origin, input.url, input.port);
  const identity = await (input.processProbe ?? createPlatformProbe()).selfIdentity();
  const body = {
    protocol_version: TASK_CONSOLE_PROTOCOL_VERSION,
    console_id: input.consoleId,
    authority_root_digest: authorityRootDigest(root),
    pid: identity.pid,
    start_fingerprint: identity.fingerprint,
    fingerprint_precision: identity.fingerprint_precision,
    identity_version: identity.identity_version,
    platform: identity.platform,
    captured_at: identity.captured_at,
    origin: input.origin,
    url: input.url,
    port: input.port,
    started_at: input.startedAt ?? (/* @__PURE__ */ new Date()).toISOString()
  };
  const record3 = { ...body, record_digest: recordDigest(body) };
  const file = path25.join(root, TASK_CONSOLE_DISCOVERY_FILE);
  let fd;
  let created = false;
  try {
    fd = openSync3(file, "wx", 384);
    created = true;
    writeSync(fd, canonicalJson2(record3), void 0, "utf8");
    closeSync3(fd);
    fd = void 0;
    if (readTaskConsoleDiscovery(root)?.record_digest !== record3.record_digest) {
      throw new TaskConsoleDiscoveryError("WEB_CONSOLE_DISCOVERY_INVALID");
    }
  } catch (error2) {
    if (fd !== void 0) {
      try {
        closeSync3(fd);
      } catch {
      }
      fd = void 0;
    }
    if (error2.code === "EEXIST") {
      throw new TaskConsoleDiscoveryError("WEB_CONSOLE_DISCOVERY_EXISTS");
    }
    if (created) {
      try {
        unlinkSync2(file);
      } catch {
      }
    }
    throw error2;
  } finally {
    if (fd !== void 0) {
      try {
        closeSync3(fd);
      } catch {
      }
    }
  }
  return record3;
}
function identityFromRecord(record3) {
  return {
    pid: record3.pid,
    fingerprint: record3.start_fingerprint,
    fingerprint_precision: record3.fingerprint_precision,
    identity_version: PROCESS_IDENTITY_VERSION,
    platform: record3.platform,
    captured_at: record3.captured_at
  };
}
async function inspectTaskConsoleDiscovery(dataRoot, processProbe = createPlatformProbe()) {
  let record3;
  try {
    record3 = readTaskConsoleDiscovery(dataRoot);
  } catch (error2) {
    if (error2 instanceof TaskConsoleDiscoveryError && error2.code === "WEB_CONSOLE_DISCOVERY_INVALID") {
      throw error2;
    }
    throw error2;
  }
  if (record3 === null) return { state: "absent" };
  const [verdict2] = await processProbe.probe([{
    pid: record3.pid,
    identity: identityFromRecord(record3)
  }]);
  if (!verdict2 || verdict2.state === "unknown") return { state: "owner_unknown", record: record3 };
  if (verdict2.state === "exited") return { state: "stale_owner", record: record3 };
  return { state: "active_owner", record: record3 };
}
function removeTaskConsoleDiscovery(dataRoot, expected) {
  const current = readTaskConsoleDiscovery(dataRoot);
  if (current === null) return;
  if (current.console_id !== expected.console_id || current.record_digest !== expected.record_digest) {
    throw new TaskConsoleDiscoveryError("WEB_CONSOLE_DISCOVERY_CHANGED");
  }
  try {
    unlinkSync2(taskConsoleDiscoveryPath(dataRoot));
  } catch (error2) {
    if (error2.code !== "ENOENT") throw error2;
  }
}
async function fetchTaskConsoleSession(record3, timeoutMs = 2e3) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(new URL("/api/session", record3.url), {
      method: "GET",
      headers: { Accept: "application/json" },
      signal: controller.signal
    });
    const body = await response.json().catch(() => null);
    if (!response.ok || body?.ok !== true || !body.result || body.result.console?.console_id !== record3.console_id || body.result.console?.authority_root_digest !== record3.authority_root_digest || body.result.console?.url !== record3.url) {
      throw new TaskConsoleDiscoveryError("WEB_CONSOLE_SESSION_INVALID");
    }
    return body.result;
  } catch (error2) {
    if (error2 instanceof TaskConsoleDiscoveryError) throw error2;
    throw new TaskConsoleDiscoveryError("WEB_CONSOLE_OWNER_UNRESPONSIVE");
  } finally {
    clearTimeout(timer);
  }
}

// src/web/main.ts
var WEB_CONSOLE_USAGE = [
  "usage: node dist/src/web/main.js --data-root ABS [--settings-directory ABS] [--port 0..65535]"
].join("\n");
function fail(message) {
  console.error(`TASK_CONSOLE_FAILED ${message}`);
  process2.exitCode = 1;
  throw new Error(message);
}
function parseArguments(argv, host) {
  let dataRoot = null;
  let settingsDirectory = host.settingsDirectory;
  let port = 0;
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const value = argv[index + 1];
    if (argument === "--data-root") {
      if (!value || !path26.isAbsolute(value)) fail("data_root_absolute_required");
      dataRoot = path26.normalize(value);
      index += 1;
    } else if (argument === "--settings-directory") {
      if (!value || !path26.isAbsolute(value)) fail("settings_directory_absolute_required");
      settingsDirectory = path26.normalize(value);
      index += 1;
    } else if (argument === "--port") {
      if (!value || !/^\d+$/u.test(value)) fail("port_invalid");
      const parsed = Number(value);
      if (!Number.isSafeInteger(parsed) || parsed < 0 || parsed > 65535) fail("port_invalid");
      port = parsed;
      index += 1;
    } else {
      fail(`unknown_argument:${argument}`);
    }
  }
  const effectiveHost = { ...host, settingsDirectory };
  const selection = loadInstallAuthoritySelection(effectiveHost);
  const resolvedRoot = dataRoot ?? resolveSqliteStateDirectory(selection, process2.env).dataRoot;
  return { dataRoot: resolvedRoot, settingsDirectory, port };
}
async function runTaskConsoleMain(argv = process2.argv.slice(2)) {
  if (argv.includes("--help") || argv.includes("-h")) {
    console.log(WEB_CONSOLE_USAGE);
    return;
  }
  const host = codexHostProfile();
  const options = parseArguments(argv, host);
  const client = new ExecutorControlClient({ pipeName: executorPipeName(options.dataRoot) });
  let consoleServer;
  let ownDiscovery;
  try {
    await client.connect();
    const executorResponse = await client.request("executorStatus", {});
    if (!executorResponse.ok || typeof executorResponse.result?.lease_id !== "string") {
      throw Object.assign(new Error("Task Console requires an active Executor lease"), {
        code: "EXECUTOR_UNAVAILABLE"
      });
    }
    const consoleId = randomUUID11();
    const manager = new RemoteTaskManager(client);
    const costLab = createUnifiedCostLabApplication({
      moduleUrl: import.meta.url,
      dataRoot: options.dataRoot
    });
    const projectRoot = resolveConsoleProjectRoot(import.meta.url);
    const runtimeCompatibility = new RuntimeCompatibilityService({
      projectRoot,
      historyPath: path26.join(
        options.dataRoot,
        ".run",
        "bridge-console",
        "runtime-compatibility.json"
      ),
      inspectEnvironment: () => costLab.inspectEnvironment(),
      runProtocolProbe: () => costLab.runProtocolProbe()
    });
    consoleServer = createTaskConsoleServer({
      manager,
      costLab,
      runtimeCompatibility,
      executorStatus: async () => {
        const response = await client.request("executorStatus", {});
        if (!response.ok) throw Object.assign(new Error(response.error?.message ?? "EXECUTOR_STATUS_FAILED"), {
          code: response.error?.code ?? "EXECUTOR_STATUS_FAILED"
        });
        return response.result ?? {};
      },
      port: options.port,
      consoleId,
      authorityRootDigest: authorityRootDigest(options.dataRoot),
      settingsDirectory: options.settingsDirectory
    });
    const address = await consoleServer.start();
    const processProbe = createPlatformProbe();
    try {
      ownDiscovery = await publishTaskConsoleDiscovery({
        dataRoot: options.dataRoot,
        consoleId,
        origin: address.origin,
        url: address.url,
        port: address.port,
        processProbe
      });
    } catch (error2) {
      if (!(error2 instanceof TaskConsoleDiscoveryError) || error2.code !== "WEB_CONSOLE_DISCOVERY_EXISTS") {
        throw error2;
      }
      const existing = await inspectTaskConsoleDiscovery(options.dataRoot, processProbe);
      if (existing.state === "stale_owner" && existing.record) {
        removeTaskConsoleDiscovery(options.dataRoot, existing.record);
        ownDiscovery = await publishTaskConsoleDiscovery({
          dataRoot: options.dataRoot,
          consoleId,
          origin: address.origin,
          url: address.url,
          port: address.port,
          processProbe
        });
      } else if (existing.state === "active_owner" && existing.record) {
        const session = await fetchTaskConsoleSession(existing.record);
        if (session.executor.lease_id !== executorResponse.result.lease_id) {
          throw new TaskConsoleDiscoveryError(
            "WEB_CONSOLE_DISCOVERY_CHANGED",
            "Task Console discovery is bound to a different Executor lease"
          );
        }
        console.log(`TASK_CONSOLE_READY ${JSON.stringify({
          ...existing.record,
          executor: session.executor,
          reused: true
        })}`);
        return;
      } else {
        throw new TaskConsoleDiscoveryError(
          existing.state === "owner_unknown" ? "WEB_CONSOLE_OWNER_UNRESPONSIVE" : "WEB_CONSOLE_DISCOVERY_INVALID",
          "Task Console discovery already has an owner that cannot be safely reused"
        );
      }
    }
    console.log(`TASK_CONSOLE_READY ${JSON.stringify({
      ...address,
      console_id: ownDiscovery.console_id,
      pid: ownDiscovery.pid,
      reused: false
    })}`);
    await new Promise((resolve) => {
      const stop = () => {
        process2.off("SIGINT", stop);
        process2.off("SIGTERM", stop);
        resolve();
      };
      process2.on("SIGINT", stop);
      process2.on("SIGTERM", stop);
    });
  } finally {
    try {
      await consoleServer?.close();
      if (ownDiscovery) {
        try {
          removeTaskConsoleDiscovery(options.dataRoot, ownDiscovery);
        } catch (error2) {
          if (!(error2 instanceof TaskConsoleDiscoveryError) || error2.code !== "WEB_CONSOLE_DISCOVERY_CHANGED") {
            console.error(`TASK_CONSOLE_DISCOVERY_RELEASE_UNKNOWN ${error2 instanceof Error ? error2.message : String(error2)}`);
          }
        }
      }
    } finally {
      client.close();
    }
  }
}
if (process2.argv[1] && path26.resolve(process2.argv[1]) === path26.resolve(fileURLToPath10(import.meta.url))) {
  void runTaskConsoleMain().catch((error2) => {
    fail(error2 instanceof Error ? error2.message : String(error2));
  });
}
export {
  runTaskConsoleMain
};
