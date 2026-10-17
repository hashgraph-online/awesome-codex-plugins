#!/usr/bin/env node

import { lstatSync, readFileSync, readdirSync, realpathSync, statSync } from "node:fs";
import { chmod, rm } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { evidencePublicationLockTarget, resolveConfinedEvidenceArtifact, resolveEvidenceOutputPath, syncEvidenceDirectory, writeEvidenceOutputFileExclusive } from "../../../src/artifacts.js";
import { evidenceRelativeDir, scopeFromSessionId, withFileLock } from "../../../src/store.js";

const PORTABLE_REPORT_ID = /^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$/u;
const WINDOWS_RESERVED = /^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])$/iu;
const REPORT_BINDING_PREFIX = "<!-- superloopy-backend-report-id: ";
const MAX_REPORT_BYTES = 8 * 1024 * 1024;

export function validateReportId(value) {
  if (
    typeof value !== "string"
    || value.length > 128
    || !PORTABLE_REPORT_ID.test(value)
    || WINDOWS_RESERVED.test(value)
  ) {
    throw new Error("report id must be 1-128 ASCII letters/digits joined by single hyphens and must not be a Windows reserved name");
  }
  return value.toLowerCase();
}

export function scopeForEvidenceRoot(value) {
  const normalized = typeof value === "string" ? value.replaceAll("\\", "/").replace(/\/$/u, "") : "";
  if (normalized === evidenceRelativeDir()) return { root: normalized, scope: undefined };

  const match = normalized.match(/^\.superloopy\/sessions\/([^/]+)\/evidence$/u);
  const scope = scopeFromSessionId(match?.[1]);
  if (!scope || evidenceRelativeDir(scope) !== normalized) {
    throw new Error("evidence root must be the active .superloopy/evidence or .superloopy/sessions/<session-id>/evidence root");
  }
  return { root: normalized, scope };
}

function requireWorkspaceRoot(projectRoot) {
  const workspaceRoot = realpathSync(resolve(projectRoot));
  if (!statSync(workspaceRoot).isDirectory()) throw new Error("project root must be an existing directory");
  return workspaceRoot;
}

// A scoped root must name a session the loop has already created; a mistyped or hallucinated
// session id must fail here rather than publish into a tree no gate ever reads.
function requireActiveScopedSession(workspaceRoot, scope) {
  if (!scope) return;
  const sessionDirectory = join(workspaceRoot, ".superloopy", "sessions", scope.sessionId);
  let isDirectory = false;
  try {
    isDirectory = lstatSync(sessionDirectory).isDirectory();
  } catch {
    isDirectory = false;
  }
  if (!isDirectory) {
    throw new Error("scoped evidence root names no existing session: use the active loop's evidence root or the global .superloopy/evidence root");
  }
}

function reportPath(resolvedRoot, safeReportId) {
  return `${resolvedRoot.root}/superloopy-backend/${safeReportId}/backend-skill-report.md`;
}

export async function writeBackendEvidenceReport({ projectRoot, evidenceRoot, reportId, content }) {
  const workspaceRoot = requireWorkspaceRoot(projectRoot);
  const resolvedRoot = scopeForEvidenceRoot(evidenceRoot);
  const safeReportId = validateReportId(reportId);
  if (typeof content !== "string" || content.trim().length === 0) {
    throw new Error("backend evidence report must contain non-whitespace content");
  }
  if (Buffer.byteLength(content, "utf8") > MAX_REPORT_BYTES) {
    throw new Error("backend evidence report exceeds 8 MiB: publish a smaller report and reference large artifacts by path");
  }
  requireActiveScopedSession(workspaceRoot, resolvedRoot.scope);
  const artifact = resolveEvidenceOutputPath(workspaceRoot, reportPath(resolvedRoot, safeReportId), resolvedRoot.scope);
  try {
    await writeEvidenceOutputFileExclusive(artifact, `${REPORT_BINDING_PREFIX}${safeReportId} -->\n${content}`, "utf8");
  } catch (error) {
    // Deterministic steering at the exact decision point the skill prose describes: a re-attempt
    // must mint a new attempt id; recover is only for this same invocation's lost receipt.
    if (/already exists/u.test(error?.message ?? "")) {
      throw new Error(`${error.message}; a re-attempt must publish under a new attempt id (append -attempt-<n>) — use recover only when this same invocation's write may have succeeded`);
    }
    throw error;
  }
  return artifact.relativePath;
}

export async function recoverBackendEvidenceReport({ projectRoot, evidenceRoot, reportId }) {
  const workspaceRoot = requireWorkspaceRoot(projectRoot);
  const resolvedRoot = scopeForEvidenceRoot(evidenceRoot);
  const safeReportId = validateReportId(reportId);
  requireActiveScopedSession(workspaceRoot, resolvedRoot.scope);
  const path = reportPath(resolvedRoot, safeReportId);
  // Validate confinement before acquiring the lock so a symlinked .superloopy never receives
  // even the lock file; the same resolution is repeated under the lock before it is trusted.
  resolveConfinedEvidenceArtifact(workspaceRoot, path, resolvedRoot.scope);
  return withFileLock(
    evidencePublicationLockTarget(workspaceRoot),
    () => recoverCommittedReport(workspaceRoot, path, resolvedRoot.scope, safeReportId),
    { timeoutMs: 60000 },
  );
}

async function recoverCommittedReport(workspaceRoot, path, scope, reportId) {
  const artifact = resolveConfinedEvidenceArtifact(workspaceRoot, path, scope);
  assertReportBinding(artifact, reportId);
  const publishedDirectory = dirname(artifact.absolutePath);
  const publicationRoot = dirname(publishedDirectory);
  await repairCrashedPublication(artifact, publicationRoot, reportId);
  const artifactStat = committedArtifactStat(artifact);
  const directoryStat = existingDirectoryStat(publishedDirectory);
  const publicationRootStat = existingDirectoryStat(publicationRoot);
  await syncEvidenceDirectory(publishedDirectory);
  await syncEvidenceDirectory(publicationRoot);
  const verified = resolveConfinedEvidenceArtifact(workspaceRoot, path, scope);
  assertReportBinding(verified, reportId);
  const verifiedArtifactStat = committedArtifactStat(verified);
  const verifiedDirectoryStat = existingDirectoryStat(dirname(verified.absolutePath));
  const verifiedPublicationRootStat = existingDirectoryStat(dirname(dirname(verified.absolutePath)));
  if (!sameFile(artifactStat, verifiedArtifactStat) || !sameFile(directoryStat, verifiedDirectoryStat) || !sameFile(publicationRootStat, verifiedPublicationRootStat)) {
    throw new Error("existing backend evidence report changed while confirming its committed state");
  }
  return verified.relativePath;
}

// A crash between the rename commit point and finalization can leave a stray hard-link scrub
// anchor (the Windows path) or a still-writable report file. Under the publication lock, remove
// only anchors proven to be the same inode as the bound, confined report, then restore its
// read-only mode before judging the committed state.
async function repairCrashedPublication(artifact, publicationRoot, reportId) {
  // Only Windows finalizes after the rename commit point (anchor removal, mode restore), so only
  // Windows can leave a repairable crash state. On POSIX the report is read-only and single-linked
  // BEFORE the commit: a writable or extra-linked POSIX report is post-publication interference
  // and must fail closed in committedArtifactStat — repairing it would certify tampered content.
  if (process.platform === "win32") {
    const reportStat = statSync(artifact.absolutePath, { bigint: true });
    if (reportStat.nlink > 1n) {
      for (const name of readdirSync(publicationRoot)) {
        if (!name.startsWith(".") || !name.endsWith(".tmp.scrub")) continue;
        const candidate = join(publicationRoot, name);
        let candidateStat;
        try {
          candidateStat = lstatSync(candidate, { bigint: true });
        } catch {
          continue;
        }
        if (candidateStat.isFile() && sameFile(reportStat, candidateStat)) {
          await rm(candidate, { force: true });
        }
      }
    }
    if ((statSync(artifact.absolutePath, { bigint: true }).mode & 0o222n) !== 0n) {
      await chmod(artifact.absolutePath, 0o444);
    }
  }
  // A hard pre-commit crash leaves this report's staging directory behind; nothing else removes
  // it (new attempts mint fresh names). Under the lock, sweep only this report id's staging dirs
  // whose recorded owner PID is provably dead.
  for (const name of readdirSync(publicationRoot)) {
    const staged = name.match(new RegExp(`^\\.${reportId}\\.(\\d+)\\..*\\.tmp$`, "u"));
    if (!staged || processAlive(Number(staged[1]))) continue;
    const candidate = join(publicationRoot, name);
    let candidateStat;
    try {
      candidateStat = lstatSync(candidate);
    } catch {
      continue;
    }
    if (candidateStat.isDirectory() && !candidateStat.isSymbolicLink()) {
      await rm(candidate, { recursive: true, force: true });
    }
  }
}

function processAlive(pid) {
  if (!Number.isInteger(pid) || pid <= 0) return true; // never sweep on a malformed owner pid
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    return error?.code !== "ESRCH";
  }
}

function assertReportBinding(artifact, reportId) {
  if (!readFileSync(artifact.absolutePath, "utf8").startsWith(`${REPORT_BINDING_PREFIX}${reportId} -->\n`)) {
    throw new Error("existing backend evidence report does not match its qualified report id binding");
  }
}

function committedArtifactStat(artifact) {
  const stat = statSync(artifact.absolutePath, { bigint: true });
  if (stat.nlink !== 1n) {
    throw new Error("existing backend evidence report has extra hard links; remove manual links to the report file, then rerun recover");
  }
  if ((stat.mode & 0o222n) !== 0n) {
    throw new Error("existing backend evidence report is writable; a committed report is read-only, so its content can no longer be verified as the published invocation");
  }
  return stat;
}

function existingDirectoryStat(path) {
  const stat = statSync(path, { bigint: true });
  if (!stat.isDirectory()) {
    throw new Error("existing backend evidence publication directory is not a directory");
  }
  return stat;
}

function sameFile(left, right) {
  return left.dev === right.dev && left.ino === right.ino;
}

async function readStandardInput() {
  if (process.stdin.isTTY) {
    throw new Error("no report on standard input: pipe the completed report into the write command");
  }
  process.stdin.setEncoding("utf8");
  let content = "";
  let bytes = 0;
  for await (const chunk of process.stdin) {
    content += chunk;
    bytes += Buffer.byteLength(chunk, "utf8");
    if (bytes > MAX_REPORT_BYTES) {
      throw new Error("backend evidence report exceeds 8 MiB: publish a smaller report and reference large artifacts by path");
    }
  }
  return content;
}

async function main(argv) {
  const [command, projectRoot, evidenceRoot, reportId, ...extra] = argv;
  if (!projectRoot || !evidenceRoot || !reportId || extra.length > 0 || !["recover", "write"].includes(command)) {
    throw new Error("usage: write-evidence-report.mjs <write|recover> <project-root> <active-evidence-root> <qualified-report-id> [< report.md]");
  }
  const path = command === "write"
    ? await writeBackendEvidenceReport({ projectRoot, evidenceRoot, reportId, content: await readStandardInput() })
    : await recoverBackendEvidenceReport({ projectRoot, evidenceRoot, reportId });
  process.stdout.write(`${path}\n`);
}

// import.meta.main (Node >= 22.18) is authoritative; older runtimes compare the invoked path, and
// an unresolvable argv path still runs the CLI so a detection misfire fails loudly on stderr
// instead of exiting 0 with an empty receipt.
function isCliEntry(argvPath) {
  if (import.meta.main !== undefined) return import.meta.main;
  if (!argvPath) return false;
  const self = fileURLToPath(import.meta.url);
  try {
    return realpathSync(argvPath) === realpathSync(self);
  } catch {
    return resolve(argvPath) === self;
  }
}

if (isCliEntry(process.argv[1])) {
  try {
    await main(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(`write-evidence-report: ${error.message}\n`);
    process.exitCode = 2;
  }
}
