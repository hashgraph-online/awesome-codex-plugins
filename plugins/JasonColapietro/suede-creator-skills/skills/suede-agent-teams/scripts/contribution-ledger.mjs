#!/usr/bin/env node

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { createHash, randomUUID } from "node:crypto";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const SCHEMA_VERSION = 1;
const MAX_LEDGER_BYTES = 5_000_000;
const MAX_ARTIFACT_BYTES = 1_000_000;
const MAX_HISTORY_EVENTS = 100;
const ARTIFACT_KINDS = ["branch", "commit", "pr"];
const PUBLICATION_ACTIONS = ["push", "draft_pr", "ready_pr", "merge"];
const TOOL_ORIGIN_PATTERN = "\\b(?:ai|aider|anthropic|chatgpt|claude|codex|copilot|cursor|devin|gemini|greptile|openai|windsurf)\\b";
const ACTIVE_STATUSES = new Set([
  "claimed",
  "changed_locally",
  "verified_locally",
  "reviewed",
]);
const TERMINAL_STATUSES = new Set(["merged", "closed", "superseded"]);
const TRANSITIONS = new Map([
  ["queued", new Set(["blocked", "closed", "superseded"])],
  ["claimed", new Set(["changed_locally", "queued", "blocked", "superseded"])],
  ["changed_locally", new Set(["verified_locally", "blocked", "superseded"])],
  ["verified_locally", new Set(["reviewed", "changed_locally", "blocked", "superseded"])],
  ["reviewed", new Set(["packet_ready", "changed_locally", "blocked", "superseded"])],
  ["packet_ready", new Set(["published", "queued", "blocked", "closed", "superseded"])],
  ["published", new Set(["published", "merged", "closed", "queued", "blocked"])],
  ["blocked", new Set(["queued", "closed", "superseded"])],
]);

const ARTIFACT_RULES = [
  {
    id: "coauthor-tool-trailer",
    pattern: /^\s*co-authored-by:\s*(?:(?:aider|anthropic|chatgpt|codex|copilot|cursor|gemini|greptile|openai|windsurf)(?:\s+(?:ai|agent|assistant|bot|cli|code|model|[0-9][\w.-]*))?|(?:claude|devin|ai)\s+(?:ai|agent|assistant|bot|cli|code|haiku(?:\s+[0-9][\w.-]*)?|model|opus(?:\s+[0-9][\w.-]*)?|sonnet(?:\s+[0-9][\w.-]*)?))\s*<[^>\n]+>\s*$|^\s*co-authored-by:\s*(?:claude|devin|ai)\s*<[^@\n]+@(?:[^>\n]*\.)?(?:anthropic\.com|cognition\.ai|openai\.com)>\s*$/gim,
  },
  {
    id: "generated-by-footer",
    pattern: new RegExp(
      `^\\s*(?:(?:this\\s+(?:change|commit|contribution|implementation|patch|pr|pull request)\\s+(?:is|was)\\s+)?(?:created|generated|produced|written)\\s+(?:by|with)\\s+(?:an?\\s+)?${TOOL_ORIGIN_PATTERN})\\s*[.!]?\\s*$`,
      "gim",
    ),
  },
  {
    id: "tool-badge",
    pattern: new RegExp(`(?:badge|shields?\\.io)[^\\n]*${TOOL_ORIGIN_PATTERN}`, "gi"),
  },
  {
    id: "automation-branding",
    pattern: new RegExp(`^\\s*${TOOL_ORIGIN_PATTERN}\\s+(?:agent|assistant|bot|generated|model)\\s*[.!]?\\s*$`, "gim"),
  },
  {
    id: "tool-origin-footer",
    pattern: new RegExp(
      `^\\s*(?:(?:this\\s+(?:change|commit|contribution|implementation|patch|pr|pull request)\\s+(?:is|was)\\s+)?(?:assisted|authored|built|developed|implemented)\\s+(?:by|using|via|with)\\s+(?:an?\\s+)?${TOOL_ORIGIN_PATTERN}|${TOOL_ORIGIN_PATTERN}[- ]assisted\\s+(?:change|commit|contribution|implementation|patch|pr|pull request))\\s*[.!]?\\s*$`,
      "gim",
    ),
  },
  {
    id: "robot-marker",
    pattern: /🤖/gu,
  },
];

class UsageError extends Error {
  constructor(message, exitCode = 1) {
    super(message);
    this.name = "UsageError";
    this.exitCode = exitCode;
  }
}

function nowIso() {
  return new Date().toISOString();
}

function parseArgs(argv) {
  const [command, ...tokens] = argv;
  if (!command || command === "--help" || command === "-h") return { command: "help", options: {} };

  const options = {};
  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (!token.startsWith("--")) throw new UsageError(`Unexpected argument: ${token}`);
    const key = token.slice(2);
    if (!key) throw new UsageError("Option names cannot be empty");
    const next = tokens[index + 1];
    if (next === undefined || next.startsWith("--")) {
      options[key] = true;
    } else {
      options[key] = next;
      index += 1;
    }
  }
  return { command, options };
}

function required(options, key) {
  const value = options[key];
  if (typeof value !== "string" || !value.trim()) throw new UsageError(`Missing --${key}`);
  return value.trim();
}

function enumValue(options, key, allowed, fallback) {
  const value = options[key] === undefined ? fallback : options[key];
  if (!allowed.includes(value)) {
    throw new UsageError(`--${key} must be one of: ${allowed.join(", ")}`);
  }
  return value;
}

function boundedInteger(options, key, fallback, minimum, maximum) {
  const raw = options[key] === undefined ? fallback : options[key];
  const value = Number(raw);
  if (!Number.isInteger(value) || value < minimum || value > maximum) {
    throw new UsageError(`--${key} must be an integer from ${minimum} to ${maximum}`);
  }
  return value;
}

function canonicalRepo(value) {
  let repo = String(value).trim();
  const httpsMatch = repo.match(/^https?:\/\/github\.com\/([^/]+)\/([^/#]+?)(?:\.git)?\/?$/i);
  const sshMatch = repo.match(/^git@github\.com:([^/]+)\/(.+?)(?:\.git)?$/i);
  if (httpsMatch) repo = `${httpsMatch[1]}/${httpsMatch[2]}`;
  else if (sshMatch) repo = `${sshMatch[1]}/${sshMatch[2]}`;
  repo = repo.replace(/\.git$/i, "").replace(/^\/+|\/+$/g, "");
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repo)) {
    throw new UsageError("--repo must be owner/repo or a GitHub clone URL");
  }
  return repo.toLowerCase();
}

function positiveReferenceNumber(value) {
  const normalized = String(value).replace(/^0+(?=\d)/, "");
  if (!/^\d+$/.test(normalized) || /^0+$/.test(normalized)) {
    throw new UsageError("Issue and pull-request numbers must be positive integers");
  }
  return normalized;
}

function canonicalRef(repo, value) {
  const ref = String(value).trim();
  const numeric = ref.match(/^#?(\d+)$/);
  if (numeric) return `issue:${positiveReferenceNumber(numeric[1])}`;

  const typed = ref.match(/^(issue|pull(?:\s+request)?|pr)(?:\s*#|\s*:|\s+)\s*(\d+)$/i);
  if (typed) {
    const type = typed[1].toLowerCase() === "issue" ? "issue" : "pull";
    return `${type}:${positiveReferenceNumber(typed[2])}`;
  }

  if (/^https?:\/\//i.test(ref)) {
    let parsed;
    try {
      parsed = new URL(ref);
    } catch {
      throw new UsageError("--ref URL must be a valid GitHub issue or pull-request URL");
    }
    const match = parsed.pathname.match(/^\/([^/]+)\/([^/]+)\/(issues|pull)\/(\d+)\/?$/i);
    if (parsed.protocol !== "https:" || parsed.hostname.toLowerCase() !== "github.com" || !match) {
      throw new UsageError("--ref URL must be an https://github.com issue or pull-request URL");
    }
    const referencedRepo = canonicalRepo(`${match[1]}/${match[2]}`);
    if (referencedRepo !== repo) {
      throw new UsageError(`--ref URL targets ${referencedRepo}, not ${repo}`);
    }
    return `${match[3].toLowerCase() === "issues" ? "issue" : "pull"}:${positiveReferenceNumber(match[4])}`;
  }

  const normalized = ref.normalize("NFKC").replace(/\s+/g, " ").toLowerCase();
  if (!normalized) throw new UsageError("--ref cannot be empty");
  return `key:${normalized}`;
}

function taskId(repo, ref) {
  return createHash("sha256").update(`${repo}\0${ref}`).digest("hex").slice(0, 12);
}

function contentHash(text) {
  return createHash("sha256").update(text, "utf8").digest("hex");
}

function scoreTask({ scope, impact, confidence, effort, risk }) {
  return impact * 4 + confidence * 3 - effort * 2 - risk * 3 + (scope === "owned" ? 8 : 0);
}

function validateLedger(ledger) {
  if (!ledger || typeof ledger !== "object" || Array.isArray(ledger)) {
    throw new UsageError("Ledger must be a JSON object");
  }
  if (ledger.schemaVersion !== SCHEMA_VERSION) {
    throw new UsageError(`Unsupported ledger schema: ${ledger.schemaVersion ?? "missing"}`);
  }
  if (!ledger.settings || !["disabled", "owned", "reviewed"].includes(ledger.settings.publishMode)) {
    throw new UsageError("Ledger publishMode must be disabled, owned, or reviewed");
  }
  if (ledger.settings.publishMode !== "disabled" && (
    !ledger.settings.publishAuthority?.note || !ledger.settings.publishAuthority?.actor
  )) {
    throw new UsageError("Active publish mode requires recorded kill-switch authority");
  }
  if (!Number.isInteger(ledger.settings.defaultLeaseMinutes)) {
    throw new UsageError("Ledger defaultLeaseMinutes must be an integer");
  }
  if (!Number.isInteger(ledger.settings.publishGeneration) || ledger.settings.publishGeneration < 0) {
    throw new UsageError("Ledger publishGeneration must be a non-negative integer");
  }
  if (!Array.isArray(ledger.items)) throw new UsageError("Ledger items must be an array");
  return ledger;
}

function readLedger(ledgerPath) {
  let parsed;
  try {
    if (fs.statSync(ledgerPath).size > MAX_LEDGER_BYTES) {
      throw new UsageError(`Ledger exceeds ${MAX_LEDGER_BYTES} bytes`);
    }
    parsed = JSON.parse(fs.readFileSync(ledgerPath, "utf8"));
  } catch (error) {
    if (error?.code === "ENOENT") throw new UsageError(`Ledger does not exist: ${ledgerPath}`);
    throw new UsageError(`Cannot read ledger: ${error.message}`);
  }
  return validateLedger(parsed);
}

function atomicWriteJson(targetPath, value) {
  const directory = path.dirname(targetPath);
  fs.mkdirSync(directory, { recursive: true });
  const temporary = path.join(directory, `.${path.basename(targetPath)}.${process.pid}.${randomUUID()}.tmp`);
  const serialized = `${JSON.stringify(value, null, 2)}\n`;
  if (Buffer.byteLength(serialized, "utf8") > MAX_LEDGER_BYTES) {
    throw new UsageError(`Refusing to write ledger larger than ${MAX_LEDGER_BYTES} bytes`);
  }
  try {
    fs.writeFileSync(temporary, serialized, { encoding: "utf8", mode: 0o600 });
    if (fs.existsSync(targetPath) && fs.statSync(targetPath).nlink > 1) {
      throw new UsageError("Refusing to replace a hard-linked ledger");
    }
    fs.renameSync(temporary, targetPath);
  } finally {
    if (fs.existsSync(temporary)) fs.unlinkSync(temporary);
  }
}

function processStartSignature(pid) {
  try {
    return execFileSync("ps", ["-p", String(pid), "-o", "lstart="], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim() || null;
  } catch {
    return null;
  }
}

function pidIsRunning(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    if (error?.code === "EPERM") return true;
    if (error?.code === "ESRCH") return false;
    throw new UsageError(`Cannot verify lock owner PID ${pid}: ${error.message}`);
  }
}

function removeLockIfOwned(lockPath, token, inode) {
  try {
    const initialStat = fs.statSync(lockPath);
    const initialRaw = fs.readFileSync(lockPath, "utf8");
    const current = JSON.parse(initialRaw);
    if (initialStat.ino !== inode || current.token !== token) return;
    const finalStat = fs.statSync(lockPath);
    const finalRaw = fs.readFileSync(lockPath, "utf8");
    if (finalStat.ino === inode && finalRaw === initialRaw) fs.unlinkSync(lockPath);
  } catch (error) {
    if (error?.code !== "ENOENT") {
      // Preserve an unreadable or replacement lock; recovery must verify it explicitly.
    }
  }
}

function canonicalLedgerPath(value) {
  const absolute = path.resolve(value);
  const directory = path.dirname(absolute);
  fs.mkdirSync(directory, { recursive: true, mode: 0o700 });
  const candidate = path.join(fs.realpathSync(directory), path.basename(absolute));
  let entry;
  try {
    entry = fs.lstatSync(candidate);
  } catch (error) {
    if (error?.code === "ENOENT") return candidate;
    throw new UsageError(`Cannot inspect ledger path: ${error.message}`);
  }
  if (entry.isSymbolicLink()) {
    try {
      return canonicalLedgerPath(fs.realpathSync(candidate));
    } catch (error) {
      throw new UsageError(`Cannot resolve ledger symlink: ${error.message}`);
    }
  }
  if (!entry.isFile()) throw new UsageError("Ledger path must be a regular file");
  if (entry.nlink > 1) {
    throw new UsageError("Hard-linked ledgers are unsupported because aliases can bypass atomic locking");
  }
  return candidate;
}

function withLedgerLock(ledgerPath, callback) {
  const resolved = canonicalLedgerPath(ledgerPath);
  const lockPath = `${resolved}.lock`;
  const lockToken = randomUUID();
  const temporaryLockPath = `${lockPath}.${process.pid}.${lockToken}.tmp`;
  let lockDescriptor;
  let lockInode;
  let lockLinked = false;
  try {
    lockDescriptor = fs.openSync(temporaryLockPath, "wx", 0o600);
    fs.writeFileSync(lockDescriptor, `${JSON.stringify({
      pid: process.pid,
      host: os.hostname(),
      token: lockToken,
      processStartedAt: processStartSignature(process.pid),
      createdAt: nowIso(),
    })}\n`);
    fs.fsyncSync(lockDescriptor);
    lockInode = fs.fstatSync(lockDescriptor).ino;
    fs.linkSync(temporaryLockPath, lockPath);
    lockLinked = true;
    fs.unlinkSync(temporaryLockPath);
  } catch (error) {
    if (lockDescriptor !== undefined) {
      fs.closeSync(lockDescriptor);
      lockDescriptor = undefined;
    }
    if (lockLinked) removeLockIfOwned(lockPath, lockToken, lockInode);
    if (fs.existsSync(temporaryLockPath)) fs.unlinkSync(temporaryLockPath);
    if (error?.code === "EEXIST") {
      throw new UsageError(`Ledger is locked: ${lockPath}`);
    }
    throw error;
  }

  try {
    return callback(resolved);
  } finally {
    if (lockDescriptor !== undefined) fs.closeSync(lockDescriptor);
    if (fs.existsSync(temporaryLockPath)) fs.unlinkSync(temporaryLockPath);
    removeLockIfOwned(lockPath, lockToken, lockInode);
  }
}

function recoverLedgerLock(options) {
  const ledgerPath = canonicalLedgerPath(required(options, "ledger"));
  const lockPath = `${ledgerPath}.lock`;
  let initialStat;
  let raw;
  try {
    initialStat = fs.statSync(lockPath);
    raw = fs.readFileSync(lockPath, "utf8");
  } catch (error) {
    if (error?.code === "ENOENT") {
      return { ok: true, command: "recover-lock", recovered: false, reason: "no_lock" };
    }
    throw new UsageError(`Cannot inspect ledger lock: ${error.message}`);
  }

  let record;
  try {
    record = JSON.parse(raw);
  } catch {
    throw new UsageError("Lock record is invalid; refusing unverified recovery");
  }
  if (record.host !== os.hostname()) {
    throw new UsageError("Lock belongs to another host; refusing unverified recovery");
  }
  const expectedToken = required(options, "expected-token");
  if (!record.token || record.token !== expectedToken) {
    throw new UsageError("Lock token does not match --expected-token; refusing recovery");
  }
  if (!Number.isInteger(record.pid) || record.pid <= 0 || !record.processStartedAt || !record.createdAt) {
    throw new UsageError("Lock lacks token/PID/start identity; refusing unverified recovery");
  }
  const createdAt = Date.parse(record.createdAt);
  const staleAfterSeconds = boundedInteger(options, "stale-after-seconds", 60, 1, 86_400);
  if (Number.isNaN(createdAt) || createdAt > Date.now()) {
    throw new UsageError("Lock timestamp is invalid or in the future; refusing recovery");
  }
  if (Date.now() - createdAt < staleAfterSeconds * 1_000) {
    throw new UsageError(`Lock is younger than ${staleAfterSeconds} seconds; refusing recovery`);
  }

  const liveStart = processStartSignature(record.pid);
  const pidRunning = pidIsRunning(record.pid);
  if (pidRunning && (!liveStart || liveStart === record.processStartedAt)) {
    throw new UsageError(`Lock owner PID ${record.pid} is still running; refusing recovery`);
  }

  const finalStat = fs.statSync(lockPath);
  const finalRaw = fs.readFileSync(lockPath, "utf8");
  if (finalStat.ino !== initialStat.ino || finalRaw !== raw) {
    throw new UsageError("Lock changed during recovery; refusing removal");
  }
  const quarantinePath = `${lockPath}.recovered-${record.token}`;
  fs.renameSync(lockPath, quarantinePath);
  fs.unlinkSync(quarantinePath);
  return {
    ok: true,
    command: "recover-lock",
    recovered: true,
    previous: { pid: record.pid, host: record.host, processStartedAt: record.processStartedAt },
  };
}

function event(task, type, detail = {}) {
  const at = nowIso();
  task.updatedAt = at;
  task.history.push({ at, type, ...detail });
  if (task.history.length > MAX_HISTORY_EVENTS) {
    const removed = task.history.length - MAX_HISTORY_EVENTS;
    task.history.splice(0, removed);
    task.historyTrimmedCount = (task.historyTrimmedCount ?? 0) + removed;
  }
}

function leaseIsExpired(task, now = Date.now()) {
  if (!task.lease?.expiresAt) return false;
  const expiry = Date.parse(task.lease.expiresAt);
  return Number.isNaN(expiry) || expiry <= now;
}

function requeueExpired(ledger) {
  let changed = false;
  for (const task of ledger.items) {
    if (!ACTIVE_STATUSES.has(task.status) || !task.lease || !leaseIsExpired(task)) continue;
    const previousWorker = task.lease.worker;
    task.status = "queued";
    task.lease = null;
    event(task, "lease_expired", { previousWorker });
    changed = true;
  }
  return changed;
}

function findTask(ledger, id) {
  const task = ledger.items.find((entry) => entry.id === id);
  if (!task) throw new UsageError(`Unknown task: ${id}`);
  return task;
}

function requireLeaseOwner(task, worker) {
  if (!task.lease) throw new UsageError(`Task ${task.id} has no active lease`);
  if (leaseIsExpired(task)) throw new UsageError(`Task ${task.id} lease has expired`);
  if (task.lease.worker !== worker) {
    throw new UsageError(`Task ${task.id} is leased to ${task.lease.worker}`);
  }
}

function saveLedger(ledgerPath, ledger) {
  ledger.updatedAt = nowIso();
  atomicWriteJson(ledgerPath, ledger);
}

function initLedger(options) {
  return withLedgerLock(required(options, "ledger"), (ledgerPath) => {
    if (fs.existsSync(ledgerPath)) throw new UsageError(`Refusing to overwrite existing ledger: ${ledgerPath}`);
    const publishMode = enumValue(options, "publish-mode", ["disabled"], "disabled");
    const defaultLeaseMinutes = boundedInteger(options, "lease-minutes", 45, 1, 1440);
    const createdAt = nowIso();
    const ledger = {
      schemaVersion: SCHEMA_VERSION,
      createdAt,
      updatedAt: createdAt,
      settings: { publishMode, publishGeneration: 0, publishAuthority: null, defaultLeaseMinutes },
      items: [],
    };
    atomicWriteJson(ledgerPath, ledger);
    return { ok: true, command: "init", ledger: ledgerPath, settings: ledger.settings };
  });
}

function configureLedger(options) {
  return withLedgerLock(required(options, "ledger"), (ledgerPath) => {
    const ledger = readLedger(ledgerPath);
    const publishMode = enumValue(
      options,
      "publish-mode",
      ["disabled", "owned", "reviewed"],
      ledger.settings.publishMode,
    );
    if (publishMode !== "disabled" && ledger.settings.publishMode !== publishMode) {
      ledger.settings.publishGeneration += 1;
      ledger.settings.publishAuthority = {
        note: required(options, "authority-note"),
        actor: required(options, "actor"),
        generation: ledger.settings.publishGeneration,
        recordedAt: nowIso(),
      };
    } else if (publishMode === "disabled" && ledger.settings.publishMode !== "disabled") {
      for (const task of ledger.items) {
        for (const [capability, grant] of Object.entries(task.grants ?? {})) {
          if (grant.usedAt) continue;
          delete task.grants[capability];
          event(task, "authority_revoked", {
            capability,
            reason: "publication_kill_switch_disabled",
          });
        }
      }
      ledger.settings.publishAuthority = null;
    }
    ledger.settings.publishMode = publishMode;
    ledger.settings.defaultLeaseMinutes = boundedInteger(
      options,
      "lease-minutes",
      ledger.settings.defaultLeaseMinutes,
      1,
      1440,
    );
    saveLedger(ledgerPath, ledger);
    return { ok: true, command: "configure", settings: ledger.settings };
  });
}

function addTask(options) {
  return withLedgerLock(required(options, "ledger"), (ledgerPath) => {
    const ledger = readLedger(ledgerPath);
    const repo = canonicalRepo(required(options, "repo"));
    const ref = canonicalRef(repo, required(options, "ref"));
    const title = required(options, "title");
    const scope = enumValue(options, "scope", ["owned", "external"], "external");
    const ownershipEvidence = typeof options["ownership-evidence"] === "string"
      ? options["ownership-evidence"].trim()
      : null;
    if (scope === "owned" && !ownershipEvidence) {
      throw new UsageError("Owned tasks require --ownership-evidence; never infer ownership from a clone or login");
    }
    const disclosure = enumValue(options, "disclosure", ["unknown", "not-required", "required"], "unknown");
    const disclosureSource = typeof options["disclosure-source"] === "string"
      ? options["disclosure-source"].trim()
      : null;
    const disclosureStatement = typeof options["disclosure-statement"] === "string"
      ? options["disclosure-statement"]
      : null;
    if (disclosure !== "unknown" && !disclosureSource) {
      throw new UsageError(`${disclosure} disclosure requires --disclosure-source`);
    }
    if (disclosure === "required" && !disclosureStatement?.trim()) {
      throw new UsageError("Required disclosure requires --disclosure-statement with the exact upstream text");
    }
    if (disclosure === "required") requireBoundedDisclosureStatement(disclosureStatement);
    const factors = {
      impact: boundedInteger(options, "impact", 3, 1, 5),
      confidence: boundedInteger(options, "confidence", 3, 1, 5),
      effort: boundedInteger(options, "effort", 3, 1, 5),
      risk: boundedInteger(options, "risk", 3, 1, 5),
    };
    const id = taskId(repo, ref);
    if (ledger.items.some((entry) => entry.repo === repo && entry.ref === ref)) {
      throw new UsageError(`Duplicate repo/ref task: ${repo} ${ref}`);
    }
    const conflictingScope = ledger.items.find(
      (entry) => entry.repo === repo && entry.scope !== scope,
    );
    if (conflictingScope) {
      // Scope is a property of the repository, not of one task. Allowing both
      // scopes for the same repo let an "owned" twin obtain a merge grant for
      // a repository the ledger had already classified as external — the
      // external-merge prohibition held per task while being defeated in
      // substance.
      throw new UsageError(
        `Repository ${repo} is already tracked as ${conflictingScope.scope} by task ${conflictingScope.id}; one repository cannot hold both scopes`,
      );
    }
    const createdAt = nowIso();
    const task = {
      id,
      repo,
      ref,
      title,
      scope,
      ownershipEvidence,
      disclosure,
      disclosureSource,
      disclosureStatement,
      score: scoreTask({ scope, ...factors }),
      factors,
      status: "queued",
      lease: null,
      artifacts: {},
      packet: null,
      grants: {},
      publications: [],
      createdAt,
      updatedAt: createdAt,
      history: [{ at: createdAt, type: "added" }],
    };
    ledger.items.push(task);
    saveLedger(ledgerPath, ledger);
    return { ok: true, command: "add", task };
  });
}

function listTasks(options) {
  return withLedgerLock(required(options, "ledger"), (ledgerPath) => {
    const ledger = readLedger(ledgerPath);
    const changed = requeueExpired(ledger);
    if (changed) saveLedger(ledgerPath, ledger);
    const status = typeof options.status === "string" ? options.status : null;
    const scope = typeof options.scope === "string" ? options.scope : null;
    const items = ledger.items.filter((task) => (!status || task.status === status) && (!scope || task.scope === scope));
    return { ok: true, command: "list", count: items.length, items };
  });
}

function nextTask(options) {
  return withLedgerLock(required(options, "ledger"), (ledgerPath) => {
    const ledger = readLedger(ledgerPath);
    const changed = requeueExpired(ledger);
    if (changed) saveLedger(ledgerPath, ledger);
    const scope = options.scope === undefined
      ? null
      : enumValue(options, "scope", ["owned", "external"], null);
    const candidates = ledger.items
      .filter((task) => task.status === "queued" && (!scope || task.scope === scope))
      .sort((left, right) => right.score - left.score || left.createdAt.localeCompare(right.createdAt) || left.id.localeCompare(right.id));
    return { ok: true, command: "next", task: candidates[0] ?? null };
  });
}

function claimTask(options) {
  return withLedgerLock(required(options, "ledger"), (ledgerPath) => {
    const ledger = readLedger(ledgerPath);
    requeueExpired(ledger);
    const task = findTask(ledger, required(options, "id"));
    if (task.status !== "queued") {
      const owner = task.lease?.worker ? ` by ${task.lease.worker}` : "";
      throw new UsageError(`Task ${task.id} is ${task.status}${owner}`);
    }
    const worker = required(options, "worker");
    const leaseMinutes = boundedInteger(
      options,
      "lease-minutes",
      ledger.settings.defaultLeaseMinutes,
      1,
      1440,
    );
    const claimedAt = nowIso();
    task.status = "claimed";
    task.lease = {
      worker,
      claimedAt,
      expiresAt: new Date(Date.parse(claimedAt) + leaseMinutes * 60_000).toISOString(),
    };
    event(task, "claimed", { worker, leaseMinutes });
    saveLedger(ledgerPath, ledger);
    return { ok: true, command: "claim", task };
  });
}

function heartbeatTask(options) {
  return withLedgerLock(required(options, "ledger"), (ledgerPath) => {
    const ledger = readLedger(ledgerPath);
    const task = findTask(ledger, required(options, "id"));
    const worker = required(options, "worker");
    requireLeaseOwner(task, worker);
    const leaseMinutes = boundedInteger(
      options,
      "lease-minutes",
      ledger.settings.defaultLeaseMinutes,
      1,
      1440,
    );
    task.lease.expiresAt = new Date(Date.now() + leaseMinutes * 60_000).toISOString();
    event(task, "heartbeat", { worker, leaseMinutes });
    saveLedger(ledgerPath, ledger);
    return { ok: true, command: "heartbeat", task };
  });
}

function releaseTask(options) {
  return withLedgerLock(required(options, "ledger"), (ledgerPath) => {
    const ledger = readLedger(ledgerPath);
    const task = findTask(ledger, required(options, "id"));
    const worker = required(options, "worker");
    requireLeaseOwner(task, worker);
    task.status = "queued";
    task.lease = null;
    event(task, "released", { worker });
    saveLedger(ledgerPath, ledger);
    return { ok: true, command: "release", task };
  });
}

function parsePushAuthorityTarget(task, value) {
  const qualified = value.match(/^([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+)@(refs\/heads\/[A-Za-z0-9._/-]+)$/);
  const ref = qualified?.[2] ?? value;
  if (!/^refs\/heads\/[A-Za-z0-9._/-]+$/.test(ref)) {
    throw new UsageError(
      "Push grant --target must be refs/heads/<branch> or owner/repo@refs/heads/<branch>",
    );
  }
  const repo = (qualified?.[1] ?? task.repo).toLowerCase();
  if (task.scope === "owned" && repo !== task.repo) {
    throw new UsageError("Owned push grants must target the task repository");
  }
  return { repo, branch: ref.slice("refs/heads/".length) };
}

function grantTask(options) {
  return withLedgerLock(required(options, "ledger"), (ledgerPath) => {
    const ledger = readLedger(ledgerPath);
    const task = findTask(ledger, required(options, "id"));
    const capability = enumValue(options, "capability", PUBLICATION_ACTIONS, null);
    if (task.scope === "external" && ledger.settings.publishMode !== "reviewed") {
      throw new UsageError("External tasks require reviewed publication mode before recording a task grant");
    }
    if (task.scope === "external" && capability === "merge") {
      throw new UsageError("External tasks cannot receive merge grants");
    }
    if (task.scope === "owned" && !["owned", "reviewed"].includes(ledger.settings.publishMode)) {
      throw new UsageError("Publication kill switch is disabled; enable a publish mode before recording a task grant");
    }
    const expectedStatus = capability === "push" ? "packet_ready" : "published";
    if (task.status !== expectedStatus) {
      throw new UsageError(`${capability} authority can only be recorded while task is ${expectedStatus}`);
    }
    if (!task.packet?.sha256) {
      throw new UsageError(`Task ${task.id} has no current reviewed packet to bind authority to`);
    }
    if (task.grants?.[capability]) {
      throw new UsageError(`Task ${task.id} already has a one-shot ${capability} grant record`);
    }
    const grant = {
      capability,
      actor: required(options, "actor"),
      note: required(options, "authority-note"),
      target: required(options, "target"),
      packetSha256: task.packet.sha256,
      publishGeneration: ledger.settings.publishGeneration,
      recordedAt: nowIso(),
      usedAt: null,
      evidenceUrl: null,
    };
    if (capability === "push") {
      parsePushAuthorityTarget(task, grant.target);
    }
    if (["ready_pr", "merge"].includes(capability)) {
      const evidence = validateGitHubEvidenceUrl(task, grant.target, capability);
      grant.target = evidence.url;
    }
    task.grants ??= {};
    task.grants[capability] = grant;
    event(task, "authority_granted", {
      capability,
      actor: grant.actor,
      target: grant.target,
    });
    saveLedger(ledgerPath, ledger);
    return { ok: true, command: "grant", taskId: task.id, grant };
  });
}

function validateGitHubEvidenceUrl(task, value, action) {
  let parsed;
  try {
    parsed = new URL(value);
  } catch {
    throw new UsageError("--remote-url must be a valid https://github.com/ URL");
  }
  const parts = parsed.pathname.split("/").filter(Boolean);
  if (
    parsed.protocol !== "https:"
    || parsed.hostname.toLowerCase() !== "github.com"
    || parsed.username
    || parsed.password
    || parsed.port
    || parsed.search
    || parsed.hash
    || parts.length < 2
  ) {
    throw new UsageError("--remote-url must be a valid https://github.com/ URL");
  }
  const evidenceRepo = `${parts[0]}/${parts[1]}`.toLowerCase();
  if (action !== "push" && evidenceRepo !== task.repo) {
    throw new UsageError(`--remote-url must point to task repository ${task.repo}`);
  }
  if (action === "push") {
    if (parts[2] !== "tree" || parts.length < 4) {
      throw new UsageError("Push evidence must be the authorized repository's /tree/<branch> URL");
    }
    return {
      url: parsed.toString(),
      repo: evidenceRepo,
      branch: decodeURIComponent(parts.slice(3).join("/")),
    };
  }
  if (!parts[3] || parts[2] !== "pull" || parts.length !== 4 || !/^\d+$/.test(parts[3])) {
    throw new UsageError(`${action} evidence must be the task repository's canonical /pull/<number> URL`);
  }
  if (positiveReferenceNumber(parts[3]) !== parts[3]) {
    throw new UsageError(`${action} evidence must use a canonical positive pull-request number`);
  }
  return { url: parsed.toString(), pullNumber: parts[3] };
}

function requirePublicationPrerequisite(task, action) {
  const completed = new Set((task.publications ?? []).map((entry) => entry.action));
  if (completed.has(action)) throw new UsageError(`Task ${task.id} already recorded ${action}`);
  if (action === "draft_pr" && !completed.has("push")) {
    throw new UsageError("draft_pr requires a recorded push action");
  }
  if (action === "ready_pr" && !completed.has("draft_pr")) {
    throw new UsageError("ready_pr requires a separately authorized draft_pr action");
  }
  if (action === "merge" && !completed.has("ready_pr")) {
    throw new UsageError("merge requires a separately authorized ready_pr action");
  }
}

function applyPublicationAction(ledger, task, options, targetStatus) {
  const action = enumValue(options, "action", PUBLICATION_ACTIONS, null);
  if (task.scope === "external" && action === "merge") {
    throw new UsageError("External tasks cannot be merged by the contribution ledger");
  }
  if (task.scope === "external" && ledger.settings.publishMode !== "reviewed") {
    throw new UsageError("External publication requires reviewed mode and a separate grant for every action");
  }
  if (task.scope === "owned" && !["owned", "reviewed"].includes(ledger.settings.publishMode)) {
    throw new UsageError("Publishing is disabled; configure a publish mode only after explicit authority");
  }
  if (!task.packet) throw new UsageError("Task has no artifact-bound contribution packet");

  if (targetStatus === "merged" && action !== "merge") {
    throw new UsageError("Only --action merge can enter merged state");
  }
  if (targetStatus === "published" && action === "merge") {
    throw new UsageError("--action merge must transition to merged");
  }
  if (task.status === "packet_ready" && action !== "push") {
    throw new UsageError("The first publication action must be a separately authorized push");
  }
  if (task.status === "published" && action === "push") {
    throw new UsageError("Push was already recorded for this task");
  }
  requirePublicationPrerequisite(task, action);

  const grant = task.grants?.[action];
  if (!grant || grant.usedAt) throw new UsageError(`Task ${task.id} requires an unused ${action} grant`);
  if (grant.packetSha256 !== task.packet.sha256) {
    throw new UsageError(`${action} grant does not match the current reviewed packet`);
  }
  if (grant.publishGeneration !== ledger.settings.publishGeneration) {
    throw new UsageError(`${action} grant belongs to an expired publication run`);
  }
  const authorityTarget = required(options, "authority-target");
  if (authorityTarget !== grant.target) {
    throw new UsageError(`--authority-target does not match the recorded ${action} grant`);
  }
  const evidence = validateGitHubEvidenceUrl(task, required(options, "remote-url"), action);
  const remoteUrl = evidence.url;
  if (action === "push") {
    const pushTarget = parsePushAuthorityTarget(task, authorityTarget);
    if (pushTarget.repo !== evidence.repo || pushTarget.branch !== evidence.branch) {
      throw new UsageError("Push evidence does not match the authorized repository and branch target");
    }
  }
  if (["ready_pr", "merge"].includes(action) && authorityTarget !== remoteUrl) {
    throw new UsageError(`${action} authority target must equal the canonical PR URL`);
  }
  const priorPr = [...(task.publications ?? [])].reverse().find((entry) => ["draft_pr", "ready_pr"].includes(entry.action));
  if (["ready_pr", "merge"].includes(action) && priorPr && priorPr.remoteUrl !== remoteUrl) {
    throw new UsageError(`${action} evidence must refer to the previously recorded PR`);
  }
  const performedBy = required(options, "performed-by");
  const recordedAt = nowIso();
  grant.usedAt = recordedAt;
  grant.evidenceUrl = remoteUrl;
  task.publications ??= [];
  task.publications.push({ action, target: authorityTarget, remoteUrl, performedBy, recordedAt });
  task.remote = { url: remoteUrl, recordedAt };
  event(task, "publication_recorded", { action, target: authorityTarget, remoteUrl, performedBy });
}

function requireArtifactPacket(task) {
  const missing = ARTIFACT_KINDS.filter((kind) => !task.artifacts?.[kind]);
  if (missing.length > 0) {
    throw new UsageError(`Task ${task.id} is missing task-bound artifact checks: ${missing.join(", ")}`);
  }
  const invalid = ARTIFACT_KINDS.filter((kind) => {
    const artifact = task.artifacts[kind];
    const statementHash = task.disclosureStatement ? contentHash(task.disclosureStatement) : null;
    if (
      artifact.disclosure !== task.disclosure
      || artifact.disclosureSource !== task.disclosureSource
      || artifact.disclosureStatementSha256 !== statementHash
    ) return true;
    if (artifact.outcome === "pass") return false;
    return artifact.outcome !== "owner_review_required"
      || artifact.ownerReview?.decision !== "approve"
      || artifact.ownerReview.sha256 !== artifact.sha256;
  });
  if (invalid.length > 0) {
    throw new UsageError(`Task ${task.id} has unresolved artifact checks: ${invalid.join(", ")}`);
  }
  const artifactManifest = Object.fromEntries(ARTIFACT_KINDS.map((kind) => [kind, {
    sha256: task.artifacts[kind].sha256,
    outcome: task.artifacts[kind].outcome,
    ownerReviewDecision: task.artifacts[kind].ownerReview?.decision ?? null,
  }]));
  const packetPayload = {
    repo: task.repo,
    ref: task.ref,
    disclosure: task.disclosure,
    disclosureSource: task.disclosureSource,
    disclosureStatementSha256: task.disclosureStatement ? contentHash(task.disclosureStatement) : null,
    artifacts: artifactManifest,
  };
  task.packet = {
    recordedAt: nowIso(),
    sha256: contentHash(JSON.stringify(packetPayload)),
    artifacts: artifactManifest,
    disclosure: task.disclosure,
    disposition: Object.values(task.artifacts).some((artifact) => artifact.outcome === "owner_review_required")
      ? "owner_review_approved"
      : "ready",
  };
}

function clearPackagingEvidence(task) {
  // Publications record real, already-performed pushes and pull requests
  // upstream. Requeuing a task must reset its working state, but it must not
  // be able to erase evidence of what was actually published: `published ->
  // queued` requires no authority at all, and `history` is FIFO-capped, so a
  // handful of heartbeats used to remove the last trace. The log is
  // append-only and exempt from that cap.
  if (task.publications?.length) {
    task.publicationLog ??= [];
    for (const entry of task.publications) {
      task.publicationLog.push({ ...entry, clearedAt: nowIso() });
    }
  }
  task.artifacts = {};
  task.packet = null;
  task.grants = {};
  task.publications = [];
  task.remote = null;
}

function transitionTask(options) {
  return withLedgerLock(required(options, "ledger"), (ledgerPath) => {
    const ledger = readLedger(ledgerPath);
    const task = findTask(ledger, required(options, "id"));
    const target = required(options, "to");
    const allowed = TRANSITIONS.get(task.status);
    if (!allowed?.has(target)) {
      throw new UsageError(`Invalid transition for ${task.id}: ${task.status} -> ${target}`);
    }
    if (task.lease) requireLeaseOwner(task, required(options, "worker"));
    if (ACTIVE_STATUSES.has(target) && !task.lease) {
      throw new UsageError(`Task ${task.id} must be claimed before entering ${target}`);
    }
    if (target === "packet_ready") requireArtifactPacket(task);
    if (target === "published" || target === "merged") {
      applyPublicationAction(ledger, task, options, target);
    }
    const previous = task.status;
    task.status = target;
    if (target === "changed_locally" || (target === "queued" && previous !== "claimed")) {
      clearPackagingEvidence(task);
    }
    if (["queued", "blocked", "packet_ready", "published"].includes(target) || TERMINAL_STATUSES.has(target)) {
      task.lease = null;
    }
    event(task, "transitioned", { from: previous, to: target });
    saveLedger(ledgerPath, ledger);
    return { ok: true, command: "transition", task };
  });
}

function lineForOffset(text, offset) {
  return text.slice(0, offset).split("\n").length;
}

function lintArtifact(text) {
  const findings = [];
  for (const rule of ARTIFACT_RULES) {
    rule.pattern.lastIndex = 0;
    let match;
    while ((match = rule.pattern.exec(text)) !== null) {
      findings.push({ rule: rule.id, line: lineForOffset(text, match.index) });
      if (match[0].length === 0) rule.pattern.lastIndex += 1;
    }
  }
  return findings;
}

const MAX_DISCLOSURE_STATEMENT_CHARS = 400;
const MAX_DISCLOSURE_STATEMENT_LINES = 4;

// The required disclosure statement is masked out of the PR artifact before
// linting, so every byte it covers is exempt from the outward-copy rules. An
// unbounded statement is therefore a lint kill switch, two ways: declare the
// entire PR body as the "statement" and no rule can fire, or hide the exact
// banned trailers inside a short statement so masking deletes them. An
// upstream-mandated disclosure is an attribution line, not a document — bound
// it, and refuse one that smuggles the very markers masking would exempt.
function requireBoundedDisclosureStatement(statement) {
  const text = String(statement ?? "");
  if (text.length > MAX_DISCLOSURE_STATEMENT_CHARS) {
    throw new UsageError(
      `--disclosure-statement must be at most ${MAX_DISCLOSURE_STATEMENT_CHARS} characters; got ${text.length}`,
    );
  }
  const lines = text.replace(/\n+$/, "").split("\n").length;
  if (lines > MAX_DISCLOSURE_STATEMENT_LINES) {
    throw new UsageError(
      `--disclosure-statement must be at most ${MAX_DISCLOSURE_STATEMENT_LINES} lines; got ${lines}`,
    );
  }
  const smuggled = [...new Set(lintArtifact(text).map((finding) => finding.rule))];
  if (smuggled.length > 0) {
    throw new UsageError(
      `--disclosure-statement contains outward-copy violations that masking would exempt: ${smuggled.join(", ")}`,
    );
  }
}

function validateArtifactShape(kind, text) {
  const findings = [];
  if (kind === "branch") {
    const branch = text.trim();
    if (!branch || branch.includes("\n") || branch.includes("\r")) {
      findings.push({ rule: "invalid-branch-ref", line: 1 });
    } else {
      try {
        execFileSync("git", ["check-ref-format", "--branch", branch], {
          stdio: ["ignore", "ignore", "ignore"],
        });
      } catch {
        findings.push({ rule: "invalid-branch-ref", line: 1 });
      }
    }
  }

  if (kind === "commit") {
    const subject = text.split(/\r?\n/, 1)[0];
    const conventional = /^(?:build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(?:\([a-z0-9][a-z0-9._/-]*\))?!?: \S.{2,71}$/;
    if (!conventional.test(subject)) {
      findings.push({ rule: "invalid-conventional-commit-subject", line: 1 });
    }
  }

  if (kind === "pr") {
    const headings = [...text.matchAll(/^#{1,6}\s+(Summary|Why|Testing|Scope|Risks)\s*$/gim)];
    for (const name of ["Summary", "Why", "Testing", "Scope", "Risks"]) {
      const match = headings.find((entry) => entry[1].toLowerCase() === name.toLowerCase());
      if (!match) {
        findings.push({ rule: `missing-pr-section-${name.toLowerCase()}`, line: 1 });
        continue;
      }
      const start = match.index + match[0].length;
      const nextHeading = text.slice(start).search(/^#{1,6}\s+/m);
      const end = nextHeading === -1 ? text.length : start + nextHeading;
      if (text.slice(start, end).trim().length < 3) {
        findings.push({ rule: `empty-pr-section-${name.toLowerCase()}`, line: lineForOffset(text, match.index) });
      }
    }
  }
  return findings;
}

async function readInput(options) {
  if (typeof options.input === "string") {
    const inputPath = path.resolve(options.input);
    if (fs.statSync(inputPath).size > MAX_ARTIFACT_BYTES) {
      throw new UsageError(`Artifact exceeds ${MAX_ARTIFACT_BYTES} bytes`);
    }
    return fs.readFileSync(inputPath, "utf8");
  }
  if (process.stdin.isTTY) throw new UsageError("Pass --input <path> or pipe artifact text on stdin");
  const chunks = [];
  let size = 0;
  for await (const chunk of process.stdin) {
    size += chunk.length;
    if (size > MAX_ARTIFACT_BYTES) throw new UsageError(`Artifact exceeds ${MAX_ARTIFACT_BYTES} bytes`);
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
}

async function checkArtifact(options) {
  const kind = enumValue(options, "kind", ARTIFACT_KINDS, null);
  const text = await readInput(options);
  return withLedgerLock(required(options, "ledger"), (ledgerPath) => {
    const ledger = readLedger(ledgerPath);
    const task = findTask(ledger, required(options, "id"));
    const worker = required(options, "worker");
    requireLeaseOwner(task, worker);
    if (task.status !== "reviewed") {
      throw new UsageError(`Artifact checks can only be recorded while task is reviewed, not ${task.status}`);
    }
    if (task.disclosure === "unknown") {
      throw new UsageError("Disclosure rules are unknown; inspect upstream instructions before packaging", 2);
    }

    let lintText = text;
    let outcome = "pass";
    if (task.disclosure === "required" && kind === "pr") {
      outcome = "owner_review_required";
      const statement = task.disclosureStatement;
      requireBoundedDisclosureStatement(statement);
      const occurrences = statement ? text.split(statement).length - 1 : 0;
      if (occurrences !== 1) {
        throw new UsageError("PR artifact must contain the exact required disclosure statement once", 3);
      }
      const masked = statement.replace(/[^\n]/g, " ");
      lintText = text.replace(statement, masked);
    }

    const findings = [...validateArtifactShape(kind, text), ...lintArtifact(lintText)];
    if (kind === "branch" && /^(?:ai|agent|aider|automation|bot|chatgpt|claude|codex|copilot|cursor|devin|gemini|greptile|windsurf)[/-]/i.test(text.trim())) {
      findings.push({ rule: "automation-branch-prefix", line: 1 });
    }
    if (findings.length > 0) {
      const error = new UsageError("Outward artifact failed packaging checks", 4);
      error.details = findings;
      throw error;
    }

    const checkedAt = nowIso();
    const artifact = {
      kind,
      sha256: contentHash(text),
      bytes: Buffer.byteLength(text, "utf8"),
      disclosure: task.disclosure,
      disclosureSource: task.disclosureSource,
      disclosureStatementSha256: task.disclosureStatement ? contentHash(task.disclosureStatement) : null,
      outcome,
      checkedAt,
      worker,
      findings: [],
      ownerReview: null,
    };
    task.artifacts ??= {};
    task.artifacts[kind] = artifact;
    task.packet = null;
    event(task, "artifact_checked", { kind, sha256: artifact.sha256, outcome, worker });
    saveLedger(ledgerPath, ledger);
    return {
      ok: outcome === "pass",
      command: "artifact-check",
      taskId: task.id,
      artifact,
      ...(outcome === "owner_review_required" ? { exitCode: 3 } : {}),
    };
  });
}

function reviewArtifact(options) {
  return withLedgerLock(required(options, "ledger"), (ledgerPath) => {
    const ledger = readLedger(ledgerPath);
    const task = findTask(ledger, required(options, "id"));
    if (task.status !== "reviewed") {
      throw new UsageError(`Artifact owner review can only be recorded while task is reviewed, not ${task.status}`);
    }
    const kind = enumValue(options, "kind", ARTIFACT_KINDS, null);
    const artifact = task.artifacts?.[kind];
    if (!artifact) throw new UsageError(`Task ${task.id} has no ${kind} artifact check`);
    if (artifact.outcome !== "owner_review_required") {
      throw new UsageError(`${kind} artifact does not require an owner review disposition`);
    }
    const sha256 = required(options, "sha256");
    if (sha256 !== artifact.sha256) {
      throw new UsageError("--sha256 does not match the current artifact content");
    }
    // A recorded rejection is the only human veto in this pipeline, and it must
    // survive the party under review. Without this guard the same content could
    // be re-reviewed with --decision approve — same sha256, opposite verdict,
    // no lease, worker, or actor separation required — and the packet would
    // proceed to publication. Remediation is to change the artifact, which
    // re-runs artifact-check and clears ownerReview.
    const priorReview = artifact.ownerReview;
    if (priorReview?.decision === "reject" && priorReview.sha256 === sha256) {
      throw new UsageError(
        `${kind} artifact was already rejected by ${priorReview.actor} at ${priorReview.recordedAt}; change the artifact and re-run artifact-check to request a new review`,
      );
    }
    const decision = enumValue(options, "decision", ["approve", "reject"], null);
    const ownerReview = {
      decision,
      sha256,
      actor: required(options, "actor"),
      note: required(options, "review-note"),
      recordedAt: nowIso(),
    };
    artifact.ownerReview = ownerReview;
    task.packet = null;
    event(task, "artifact_owner_reviewed", { kind, sha256, decision, actor: ownerReview.actor });
    saveLedger(ledgerPath, ledger);
    return { ok: true, command: "review-artifact", taskId: task.id, kind, ownerReview };
  });
}

function help() {
  return {
    ok: true,
    usage: [
      "contribution-ledger.mjs init --ledger <path> [--publish-mode disabled]",
      "contribution-ledger.mjs configure --ledger <path> [--publish-mode disabled|owned|reviewed] [--actor <name> --authority-note <text>]",
      "contribution-ledger.mjs add --ledger <path> --repo <owner/repo> --ref <issue> --title <text> [--scope external|owned --ownership-evidence <text>] [--disclosure unknown|not-required|required --disclosure-source <source> --disclosure-statement <exact text>]",
      "contribution-ledger.mjs next --ledger <path> [--scope owned|external]",
      "contribution-ledger.mjs claim --ledger <path> --id <id> --worker <name>",
      "contribution-ledger.mjs heartbeat --ledger <path> --id <id> --worker <name>",
      "contribution-ledger.mjs release --ledger <path> --id <id> --worker <name>",
      "contribution-ledger.mjs grant --ledger <path> --id <id> --capability <push|draft_pr|ready_pr|merge> --actor <name> --authority-note <text> --target <exact target>",
      "contribution-ledger.mjs transition --ledger <path> --id <id> --worker <name> --to <status>",
      "contribution-ledger.mjs transition --ledger <path> --id <id> --to <published|merged> --action <push|draft_pr|ready_pr|merge> --authority-target <exact target> --remote-url <GitHub URL> --performed-by <name>",
      "contribution-ledger.mjs list --ledger <path> [--status <status>] [--scope owned|external]",
      "contribution-ledger.mjs artifact-check --ledger <path> --id <id> --worker <name> --kind <branch|commit|pr> [--input <path>]",
      "contribution-ledger.mjs review-artifact --ledger <path> --id <id> --kind <branch|commit|pr> --sha256 <hash> --decision <approve|reject> --actor <name> --review-note <text>",
      "contribution-ledger.mjs recover-lock --ledger <path> --expected-token <token> [--stale-after-seconds <seconds>]",
    ],
  };
}

export async function run(argv) {
  const { command, options } = parseArgs(argv);
  switch (command) {
    case "help": return help();
    case "init": return initLedger(options);
    case "configure": return configureLedger(options);
    case "add": return addTask(options);
    case "list": return listTasks(options);
    case "next": return nextTask(options);
    case "claim": return claimTask(options);
    case "heartbeat": return heartbeatTask(options);
    case "release": return releaseTask(options);
    case "grant": return grantTask(options);
    case "transition": return transitionTask(options);
    case "artifact-check": return checkArtifact(options);
    case "review-artifact": return reviewArtifact(options);
    case "recover-lock": return recoverLedgerLock(options);
    default: throw new UsageError(`Unknown command: ${command}`);
  }
}

async function main() {
  try {
    const result = await run(process.argv.slice(2));
    const { exitCode, ...payload } = result;
    process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
    if (Number.isInteger(exitCode)) process.exitCode = exitCode;
  } catch (error) {
    const payload = {
      ok: false,
      error: error instanceof Error ? error.message : String(error),
      ...(error?.details ? { findings: error.details } : {}),
    };
    process.stderr.write(`${JSON.stringify(payload, null, 2)}\n`);
    process.exitCode = Number.isInteger(error?.exitCode) ? error.exitCode : 1;
  }
}

// `import.meta.url` is already realpath-resolved, so the invoked path must be
// too. path.resolve() does not follow symlinks: invoking through any symlinked
// path (on macOS, anything under /tmp) made these disagree, main() never ran,
// and the process exited 0 having done nothing — an authority gate that reads
// as success to any caller checking $?.
function realInvokedPath(argvPath) {
  if (!argvPath) return null;
  const resolved = path.resolve(argvPath);
  try {
    return fs.realpathSync(resolved);
  } catch {
    return resolved;
  }
}

const invokedPath = realInvokedPath(process.argv[1]);
if (invokedPath === fileURLToPath(import.meta.url)) await main();
