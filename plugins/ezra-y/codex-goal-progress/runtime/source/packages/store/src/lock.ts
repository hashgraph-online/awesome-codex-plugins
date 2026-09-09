import { execFile } from "node:child_process";
import { randomUUID } from "node:crypto";
import { readdir, readFile, realpath, unlink } from "node:fs/promises";
import { basename, resolve } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { promisify } from "node:util";
import { z } from "zod";
import {
  atomicCreateFile,
  atomicWriteFile,
  cleanupAtomicTemporaryFiles,
  ensurePrivateDirectory,
} from "./atomic.js";
import { GoalProgressStoreError } from "./errors.js";
import type { GoalProgressPaths } from "./paths.js";

const execFileAsync = promisify(execFile);
const LOCK_FILE_PATTERN =
  /^([0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})\.json$/i;
const LOCK_TEMP_FILE_PATTERN =
  /^\.([0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\.json)\.\d+\.[0-9a-f]{16}$/i;
const PROCESS_START_TOLERANCE_MS = 5_000;
const LOCK_COLLISION_RETRY_MS = 20;
const LOCK_COLLISION_SETTLE_ATTEMPTS = 50;
const LOCK_TEMP_RETENTION_MS = 60_000;

const HelperIdentitySchema = z
  .object({
    schemaVersion: z.literal(1),
    pid: z.number().int().positive(),
    processStartedAtMs: z.number().int().nonnegative(),
    acquiredAt: z.string().datetime({ offset: true }),
    instanceId: z.string().uuid(),
    executablePath: z.string().trim().min(1),
  })
  .strict();

export type HelperIdentity = z.infer<typeof HelperIdentitySchema>;

export interface HelperLockOptions {
  readonly pid?: number;
  readonly processStartedAtMs?: number;
  readonly instanceId?: string;
  readonly executablePath?: string;
  readonly now?: Date;
  readonly isProcessIdentityCurrent?: (identity: HelperIdentity) => boolean | Promise<boolean>;
}

interface LockContender {
  readonly identity: HelperIdentity;
  readonly path: string;
}

function hasCode(error: unknown, code: string): boolean {
  return (
    error instanceof Error && "code" in error && (error as NodeJS.ErrnoException).code === code
  );
}

async function pidExists(pid: number): Promise<boolean> {
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    if (hasCode(error, "ESRCH")) {
      return false;
    }
    if (hasCode(error, "EPERM")) {
      return true;
    }
    throw error;
  }
}

async function canonicalPath(path: string): Promise<string> {
  try {
    return await realpath(path);
  } catch {
    return resolve(path);
  }
}

export async function helperExecutablePathsMatch(
  observedPath: string,
  expectedPath: string,
): Promise<boolean> {
  if (!observedPath.includes("/")) {
    return observedPath === basename(expectedPath);
  }
  return (await canonicalPath(observedPath)) === (await canonicalPath(expectedPath));
}

async function inspectDarwinProcess(pid: number): Promise<{
  readonly processStartedAtMs: number;
  readonly executablePath: string;
} | null> {
  const { stdout } = await execFileAsync(
    "/bin/ps",
    ["-p", String(pid), "-o", "lstart=", "-o", "comm="],
    {
      encoding: "utf8",
      env: { ...process.env, LC_ALL: "C" },
    },
  );
  const match = String(stdout)
    .trim()
    .match(/^([A-Z][a-z]{2}\s+[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\d{4})\s+(.+)$/);
  if (!match) {
    return null;
  }
  const startedAt = match[1];
  const executablePath = match[2];
  if (!startedAt || !executablePath) {
    return null;
  }
  const processStartedAtMs = Date.parse(startedAt);
  if (!Number.isFinite(processStartedAtMs)) {
    return null;
  }
  return {
    processStartedAtMs,
    executablePath: executablePath.trim(),
  };
}

async function defaultIsProcessIdentityCurrent(identity: HelperIdentity): Promise<boolean> {
  if (!(await pidExists(identity.pid))) {
    return false;
  }
  if (process.platform !== "darwin") {
    return true;
  }
  let observed: Awaited<ReturnType<typeof inspectDarwinProcess>>;
  try {
    observed = await inspectDarwinProcess(identity.pid);
  } catch {
    return true;
  }
  if (!observed) {
    return true;
  }
  if (
    Math.abs(observed.processStartedAtMs - identity.processStartedAtMs) > PROCESS_START_TOLERANCE_MS
  ) {
    return false;
  }
  return helperExecutablePathsMatch(observed.executablePath, identity.executablePath);
}

async function readIdentity(path: string): Promise<HelperIdentity> {
  try {
    return HelperIdentitySchema.parse(JSON.parse(await readFile(path, "utf8")));
  } catch (error) {
    throw new GoalProgressStoreError(
      "HELPER_LOCK_INVALID",
      "Existing Helper lock identity is invalid",
      { cause: error },
    );
  }
}

async function readContenders(paths: GoalProgressPaths): Promise<LockContender[]> {
  const entries = await readdir(paths.helperLocksRoot, { withFileTypes: true });
  const contenders: LockContender[] = [];
  for (const entry of entries) {
    if (entry.name.startsWith(".")) {
      continue;
    }
    const match = LOCK_FILE_PATTERN.exec(entry.name);
    if (!entry.isFile() || !match) {
      throw new GoalProgressStoreError(
        "HELPER_LOCK_INVALID",
        "Helper lock directory contains an invalid entry",
      );
    }
    const path = resolve(paths.helperLocksRoot, entry.name);
    let identity: HelperIdentity;
    try {
      identity = await readIdentity(path);
    } catch (error) {
      if (error instanceof GoalProgressStoreError && hasCode(error.cause, "ENOENT")) {
        continue;
      }
      throw error;
    }
    if (identity.instanceId.toLowerCase() !== match[1]?.toLowerCase()) {
      throw new GoalProgressStoreError(
        "HELPER_LOCK_INVALID",
        "Helper lock filename does not match its identity",
      );
    }
    contenders.push({ identity, path });
  }
  return contenders;
}

async function cleanupStaleLockTemps(paths: GoalProgressPaths): Promise<void> {
  const baseNames = new Set<string>();
  for (const entry of await readdir(paths.helperLocksRoot)) {
    const match = LOCK_TEMP_FILE_PATTERN.exec(entry);
    if (match?.[1]) {
      baseNames.add(match[1]);
    }
  }
  for (const baseName of baseNames) {
    await cleanupAtomicTemporaryFiles(paths.helperLocksRoot, baseName, LOCK_TEMP_RETENTION_MS);
  }
}

async function unlinkContender(path: string): Promise<void> {
  try {
    await unlink(path);
  } catch (error) {
    if (!hasCode(error, "ENOENT")) {
      throw new GoalProgressStoreError("STORE_IO_FAILED", "Could not remove Helper lock", {
        cause: error,
      });
    }
  }
}

async function collectCurrentContenders(
  paths: GoalProgressPaths,
  isProcessIdentityCurrent: (identity: HelperIdentity) => boolean | Promise<boolean>,
): Promise<LockContender[]> {
  const current: LockContender[] = [];
  for (const contender of await readContenders(paths)) {
    if (await isProcessIdentityCurrent(contender.identity)) {
      current.push(contender);
    } else {
      await unlinkContender(contender.path);
    }
  }
  return current;
}

async function removeIdentityFileIfOwned(path: string, instanceId: string): Promise<void> {
  let identity: HelperIdentity;
  try {
    identity = await readIdentity(path);
  } catch (error) {
    if (error instanceof GoalProgressStoreError && hasCode(error.cause, "ENOENT")) {
      return;
    }
    throw error;
  }
  if (identity.instanceId === instanceId) {
    await unlinkContender(path);
  }
}

export class HelperInstanceLock {
  readonly identity: HelperIdentity;
  readonly identityPath: string;
  readonly #paths: GoalProgressPaths;
  #releasePromise: Promise<void> | undefined;

  constructor(paths: GoalProgressPaths, identity: HelperIdentity, identityPath: string) {
    this.#paths = paths;
    this.identity = identity;
    this.identityPath = identityPath;
  }

  release(): Promise<void> {
    this.#releasePromise ??= this.#release();
    return this.#releasePromise;
  }

  async #release(): Promise<void> {
    await removeIdentityFileIfOwned(this.#paths.helperPidPath, this.identity.instanceId);
    await removeIdentityFileIfOwned(this.identityPath, this.identity.instanceId);
  }
}

export async function acquireHelperInstanceLock(
  paths: GoalProgressPaths,
  options: HelperLockOptions = {},
): Promise<HelperInstanceLock> {
  await ensurePrivateDirectory(paths.runtimeRoot);
  await ensurePrivateDirectory(paths.helperLocksRoot);
  await cleanupStaleLockTemps(paths);
  const identity = HelperIdentitySchema.parse({
    schemaVersion: 1,
    pid: options.pid ?? process.pid,
    processStartedAtMs:
      options.processStartedAtMs ?? Math.max(0, Math.floor(Date.now() - process.uptime() * 1_000)),
    acquiredAt: (options.now ?? new Date()).toISOString(),
    instanceId: options.instanceId ?? randomUUID(),
    executablePath: options.executablePath ?? process.execPath,
  });
  const isProcessIdentityCurrent =
    options.isProcessIdentityCurrent ?? defaultIsProcessIdentityCurrent;

  const identityPath = resolve(paths.helperLocksRoot, `${identity.instanceId}.json`);
  const existing = await collectCurrentContenders(paths, isProcessIdentityCurrent);
  const firstExisting = existing[0];
  if (firstExisting) {
    throw new GoalProgressStoreError(
      "HELPER_ALREADY_RUNNING",
      `Helper is already running with PID ${firstExisting.identity.pid}`,
    );
  }

  let published: boolean;
  try {
    published = await atomicCreateFile(identityPath, `${JSON.stringify(identity)}\n`);
  } catch (error) {
    throw new GoalProgressStoreError("STORE_IO_FAILED", "Could not publish Helper lock", {
      cause: error,
    });
  }
  if (!published) {
    throw new GoalProgressStoreError(
      "HELPER_ALREADY_RUNNING",
      "Helper instance identity is already in use",
    );
  }

  try {
    for (let attempt = 0; attempt < LOCK_COLLISION_SETTLE_ATTEMPTS; attempt += 1) {
      const current = await collectCurrentContenders(paths, isProcessIdentityCurrent);
      if (!current.some((contender) => contender.identity.instanceId === identity.instanceId)) {
        throw new GoalProgressStoreError(
          "HELPER_LOCK_INVALID",
          "Published Helper identity is not current",
        );
      }
      const others = current.filter(
        (contender) => contender.identity.instanceId !== identity.instanceId,
      );
      if (others.length === 0) {
        await cleanupAtomicTemporaryFiles(paths.runtimeRoot, "helper.pid.json");
        await atomicWriteFile(paths.helperPidPath, `${JSON.stringify(identity, null, 2)}\n`);
        return new HelperInstanceLock(paths, identity, identityPath);
      }
      const preferredInstanceId = current
        .map((contender) => contender.identity.instanceId)
        .sort()[0];
      if (preferredInstanceId !== identity.instanceId) {
        await unlinkContender(identityPath);
        throw new GoalProgressStoreError(
          "HELPER_ALREADY_RUNNING",
          "Another Helper won the concurrent lock election",
        );
      }
      await delay(LOCK_COLLISION_RETRY_MS);
    }
    throw new GoalProgressStoreError(
      "HELPER_ALREADY_RUNNING",
      "Helper lock election did not settle",
    );
  } catch (error) {
    await unlinkContender(identityPath);
    await removeIdentityFileIfOwned(paths.helperPidPath, identity.instanceId);
    throw error;
  }
}

export async function readHelperIdentity(paths: GoalProgressPaths): Promise<HelperIdentity | null> {
  try {
    return await readIdentity(paths.helperPidPath);
  } catch (error) {
    const code =
      error instanceof Error && "cause" in error
        ? (error.cause as NodeJS.ErrnoException | undefined)?.code
        : undefined;
    if (code === "ENOENT") {
      return null;
    }
    throw error;
  }
}

export async function readCurrentHelperIdentity(
  paths: GoalProgressPaths,
): Promise<HelperIdentity | null> {
  const identity = await readHelperIdentity(paths);
  if (!identity) {
    return null;
  }
  const identityPath = resolve(paths.helperLocksRoot, `${identity.instanceId}.json`);
  let contender: HelperIdentity;
  try {
    contender = await readIdentity(identityPath);
  } catch (error) {
    if (error instanceof GoalProgressStoreError && hasCode(error.cause, "ENOENT")) {
      return null;
    }
    throw error;
  }
  if (
    contender.instanceId !== identity.instanceId ||
    contender.pid !== identity.pid ||
    contender.processStartedAtMs !== identity.processStartedAtMs ||
    contender.executablePath !== identity.executablePath
  ) {
    return null;
  }
  return (await defaultIsProcessIdentityCurrent(identity)) ? identity : null;
}

export async function inspectCurrentHelperOwners(
  paths: GoalProgressPaths,
): Promise<readonly HelperIdentity[]> {
  let contenders: LockContender[];
  try {
    contenders = await readContenders(paths);
  } catch (error) {
    if (hasCode(error, "ENOENT")) {
      return [];
    }
    throw error;
  }
  const current: HelperIdentity[] = [];
  for (const contender of contenders) {
    if (await defaultIsProcessIdentityCurrent(contender.identity)) {
      current.push(contender.identity);
    }
  }
  return current;
}
