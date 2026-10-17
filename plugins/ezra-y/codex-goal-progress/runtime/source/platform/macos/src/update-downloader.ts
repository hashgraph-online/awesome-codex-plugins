import { execFile } from "node:child_process";
import { createHash, randomBytes } from "node:crypto";
import { lstat, mkdir, open, readdir, readFile, rename, rm, stat } from "node:fs/promises";
import type { ClientRequest, IncomingMessage, RequestOptions } from "node:http";
import { request as httpsRequest } from "node:https";
import { resolve } from "node:path";
import { Readable } from "node:stream";
import { isGoalProgressUpdateVersion } from "../../../packages/contracts/src/update-state-runtime.js";
import type { GoalProgressPaths } from "../../../packages/store/src/index.js";
import { ensurePrivateDirectory } from "../../../packages/store/src/index.js";
import {
  GOAL_PROGRESS_MACOS_UPDATE_ASSET,
  type GoalProgressUpdateManifest,
  goalProgressVersionedUpdateUrls,
} from "./update-manifest.js";
import { fileSha256, readVerifiedRelease } from "./verified-release.js";

export const GOAL_PROGRESS_UPDATE_SHA256SUMS_MAX_BYTES = 64 * 1024;
export const GOAL_PROGRESS_UPDATE_ZIP_MAX_BYTES = 256 * 1024 * 1024;
export const GOAL_PROGRESS_UPDATE_METADATA_TIMEOUT_MS = 15_000;
export const GOAL_PROGRESS_UPDATE_ZIP_TIMEOUT_MS = 10 * 60 * 1_000;
export const GOAL_PROGRESS_UPDATE_ARCHIVE_ROOT = "codex-goal-progress-macos-arm64";

export interface GoalProgressUpdateDownloadProgress {
  readonly downloadedBytes: number;
  readonly totalBytes: number | null;
  readonly downloadPercent: number | null;
}

export interface PrepareGoalProgressUpdateOptions {
  readonly manifest: GoalProgressUpdateManifest;
  readonly paths: GoalProgressPaths;
  readonly fetchImpl?: typeof fetch;
  readonly onProgress?: (progress: GoalProgressUpdateDownloadProgress) => Promise<void> | void;
  readonly onVerificationStarted?: () => Promise<void> | void;
  readonly signal?: AbortSignal;
  readonly now?: () => number;
  readonly metadataTimeoutMs?: number;
  readonly zipTimeoutMs?: number;
}

export interface PreparedGoalProgressUpdate {
  readonly version: string;
  readonly verifiedReleaseRoot: string;
  readonly zipSha256: string;
  readonly releaseManifestSha256: string;
  readonly downloadedBytes: number;
  readonly totalBytes: number | null;
}

interface ProgressReporter {
  report(progress: GoalProgressUpdateDownloadProgress): void;
  flush(): Promise<void>;
}

function createProgressReporter(
  callback: PrepareGoalProgressUpdateOptions["onProgress"],
): ProgressReporter {
  let pending: GoalProgressUpdateDownloadProgress | undefined;
  let running = false;
  let current: Promise<void> = Promise.resolve();
  let failure: unknown;

  const start = (): void => {
    if (running || pending === undefined || failure !== undefined || !callback) {
      return;
    }
    running = true;
    current = (async () => {
      while (pending !== undefined && failure === undefined) {
        const next = pending;
        pending = undefined;
        await callback(next);
      }
    })()
      .catch((error: unknown) => {
        failure = error;
        pending = undefined;
      })
      .finally(() => {
        running = false;
        start();
      });
  };

  return {
    report(progress) {
      if (!callback || failure !== undefined) {
        return;
      }
      pending = progress;
      start();
    },
    async flush() {
      while (running || pending !== undefined) {
        start();
        await current;
      }
      if (failure !== undefined) {
        throw failure;
      }
    },
  };
}

function run(command: string, args: readonly string[], code: string): Promise<string> {
  return new Promise((resolveRun, rejectRun) => {
    execFile(
      command,
      [...args],
      { encoding: "utf8", maxBuffer: 8 * 1024 * 1024 },
      (error, stdout) => {
        if (error) {
          rejectRun(new Error(code));
          return;
        }
        resolveRun(stdout);
      },
    );
  });
}

function safeDownloadResponseUrl(value: string): boolean {
  if (!value) {
    return true;
  }
  try {
    const url = new URL(value);
    return (
      url.protocol === "https:" &&
      url.username === "" &&
      url.password === "" &&
      (url.hostname === "github.com" || url.hostname.endsWith(".githubusercontent.com"))
    );
  } catch {
    return false;
  }
}

export type GoalProgressUpdateNodeRequest = (
  url: URL,
  options: RequestOptions,
  callback: (response: IncomingMessage) => void,
) => ClientRequest;

function responseHeaders(response: IncomingMessage): Headers {
  const headers = new Headers();
  for (const [name, value] of Object.entries(response.headers)) {
    if (Array.isArray(value)) {
      for (const item of value) {
        headers.append(name, item);
      }
    } else if (value !== undefined) {
      headers.set(name, value);
    }
  }
  return headers;
}

export function createGoalProgressUpdateFetch(
  request: GoalProgressUpdateNodeRequest = httpsRequest,
): typeof fetch {
  const requestResponse = (
    url: URL,
    signal: AbortSignal | null | undefined,
    redirects: number,
  ): Promise<Response> =>
    new Promise((resolveResponse, rejectResponse) => {
      if (!safeDownloadResponseUrl(url.href)) {
        rejectResponse(new Error("GOAL_PROGRESS_UPDATE_REDIRECT_UNSAFE"));
        return;
      }
      if (redirects > 5) {
        rejectResponse(new Error("GOAL_PROGRESS_UPDATE_DOWNLOAD_HTTP_FAILED"));
        return;
      }
      const requestHandle = request(
        url,
        {
          method: "GET",
          signal: signal ?? undefined,
        },
        (incoming) => {
          try {
            const status = incoming.statusCode ?? 0;
            const location = incoming.headers.location;
            if (
              location &&
              (status === 301 ||
                status === 302 ||
                status === 303 ||
                status === 307 ||
                status === 308)
            ) {
              incoming.resume();
              let redirected: URL;
              try {
                redirected = new URL(location, url);
              } catch {
                rejectResponse(new Error("GOAL_PROGRESS_UPDATE_REDIRECT_UNSAFE"));
                return;
              }
              void requestResponse(redirected, signal, redirects + 1).then(
                resolveResponse,
                rejectResponse,
              );
              return;
            }
            const body =
              status === 204 || status === 205 || status === 304
                ? null
                : (Readable.toWeb(incoming) as ReadableStream<Uint8Array>);
            const response = new Response(body, {
              status,
              headers: responseHeaders(incoming),
            });
            Object.defineProperty(response, "url", {
              configurable: true,
              value: url.href,
            });
            resolveResponse(response);
          } catch (error) {
            incoming.destroy();
            rejectResponse(error);
          }
        },
      );
      requestHandle.once("error", rejectResponse);
      requestHandle.end();
    });

  return async (input, init) => {
    const url =
      input instanceof URL ? input : new URL(typeof input === "string" ? input : input.url);
    return requestResponse(url, init?.signal, 0);
  };
}

async function withDownloadResponse<T>(
  url: string,
  fetchImpl: typeof fetch,
  timeoutMs: number,
  work: (response: Response) => Promise<T>,
  externalSignal?: AbortSignal,
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  timeout.unref?.();
  const abortFromExternal = () => controller.abort();
  externalSignal?.addEventListener("abort", abortFromExternal, { once: true });
  try {
    if (externalSignal?.aborted) {
      throw new Error("GOAL_PROGRESS_UPDATE_CANCELLED");
    }
    const response = await fetchImpl(url, {
      signal: controller.signal,
      redirect: "follow",
    });
    if (!safeDownloadResponseUrl(response.url)) {
      throw new Error("GOAL_PROGRESS_UPDATE_REDIRECT_UNSAFE");
    }
    if (!response.ok) {
      throw new Error("GOAL_PROGRESS_UPDATE_DOWNLOAD_HTTP_FAILED");
    }
    return await work(response);
  } catch (error) {
    if (externalSignal?.aborted) {
      throw new Error("GOAL_PROGRESS_UPDATE_CANCELLED");
    }
    if (controller.signal.aborted || (error instanceof Error && error.name === "AbortError")) {
      throw new Error("GOAL_PROGRESS_UPDATE_DOWNLOAD_TIMEOUT");
    }
    if (error instanceof Error && error.message.startsWith("GOAL_PROGRESS_UPDATE_")) {
      throw error;
    }
    throw new Error("GOAL_PROGRESS_UPDATE_DOWNLOAD_HTTP_FAILED");
  } finally {
    clearTimeout(timeout);
    externalSignal?.removeEventListener("abort", abortFromExternal);
  }
}

function responseTotalBytes(response: Response, maximumBytes: number): number | null {
  const value = response.headers.get("content-length");
  if (value === null) {
    return null;
  }
  const bytes = Number(value);
  if (!Number.isSafeInteger(bytes) || bytes < 0 || bytes > maximumBytes) {
    throw new Error("GOAL_PROGRESS_UPDATE_DOWNLOAD_TOO_LARGE");
  }
  return bytes;
}

async function readBoundedResponse(response: Response, maximumBytes: number): Promise<Uint8Array> {
  responseTotalBytes(response, maximumBytes);
  if (!response.body) {
    return new Uint8Array();
  }
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let bytes = 0;
  while (true) {
    const chunk = await reader.read();
    if (chunk.done) {
      break;
    }
    bytes += chunk.value.byteLength;
    if (bytes > maximumBytes) {
      await reader.cancel().catch(() => undefined);
      throw new Error("GOAL_PROGRESS_UPDATE_DOWNLOAD_TOO_LARGE");
    }
    chunks.push(chunk.value);
  }
  const result = new Uint8Array(bytes);
  let offset = 0;
  for (const chunk of chunks) {
    result.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return result;
}

function parseOuterSha256Sums(contents: string): string {
  const lines = contents.trim().split("\n").filter(Boolean);
  const match = lines.length === 1 ? /^([0-9a-f]{64}) {2}(.+)$/u.exec(lines[0] ?? "") : null;
  if (!match || match[2] !== GOAL_PROGRESS_MACOS_UPDATE_ASSET) {
    throw new Error("GOAL_PROGRESS_UPDATE_SHA256SUMS_INVALID");
  }
  return match[1] ?? "";
}

async function downloadZip(
  response: Response,
  path: string,
  options: PrepareGoalProgressUpdateOptions,
): Promise<{ bytes: number; totalBytes: number | null; sha256: string }> {
  const totalBytes = responseTotalBytes(response, GOAL_PROGRESS_UPDATE_ZIP_MAX_BYTES);
  if (!response.body) {
    throw new Error("GOAL_PROGRESS_UPDATE_DOWNLOAD_HTTP_FAILED");
  }
  const file = await open(path, "wx", 0o600);
  const reader = response.body.getReader();
  const hash = createHash("sha256");
  const progressReporter = createProgressReporter(options.onProgress);
  const now = options.now ?? Date.now;
  let downloadedBytes = 0;
  let lastProgressAt = now();
  let lastPercent: number | null = null;
  try {
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) {
        break;
      }
      downloadedBytes += chunk.value.byteLength;
      if (downloadedBytes > GOAL_PROGRESS_UPDATE_ZIP_MAX_BYTES) {
        await reader.cancel().catch(() => undefined);
        throw new Error("GOAL_PROGRESS_UPDATE_DOWNLOAD_TOO_LARGE");
      }
      hash.update(chunk.value);
      await file.write(chunk.value);
      const percent =
        totalBytes === null || totalBytes === 0
          ? null
          : Math.min(100, (downloadedBytes / totalBytes) * 100);
      const currentTime = now();
      if (
        (percent !== null && (lastPercent === null || percent - lastPercent >= 1)) ||
        currentTime - lastProgressAt >= 500
      ) {
        progressReporter.report({
          downloadedBytes,
          totalBytes,
          downloadPercent: percent,
        });
        lastProgressAt = currentTime;
        lastPercent = percent;
      }
    }
    if (totalBytes !== null && downloadedBytes !== totalBytes) {
      throw new Error("GOAL_PROGRESS_UPDATE_DOWNLOAD_HTTP_FAILED");
    }
    await file.sync();
  } finally {
    try {
      await file.close();
    } finally {
      await progressReporter.flush();
    }
  }
  progressReporter.report({
    downloadedBytes,
    totalBytes,
    downloadPercent:
      totalBytes === null || totalBytes === 0
        ? null
        : Math.min(100, (downloadedBytes / totalBytes) * 100),
  });
  await progressReporter.flush();
  return {
    bytes: downloadedBytes,
    totalBytes,
    sha256: hash.digest("hex"),
  };
}

function updateDownloadProcessIsAlive(pid: number): boolean {
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    return (error as NodeJS.ErrnoException).code !== "ESRCH";
  }
}

export async function cleanupOrphanedGoalProgressUpdateDownloads(
  paths: GoalProgressPaths,
  isProcessAlive: (pid: number) => boolean = updateDownloadProcessIsAlive,
): Promise<readonly string[]> {
  const updatesRoot = resolve(paths.installRoot, "updates");
  const entries = await readdir(updatesRoot, { withFileTypes: true }).catch(
    (error: NodeJS.ErrnoException) => {
      if (error.code === "ENOENT") {
        return [];
      }
      throw error;
    },
  );
  const removed: string[] = [];
  for (const entry of entries) {
    const match = /^\.(.+)\.([1-9]\d{0,9})\.([0-9a-f]{16})$/u.exec(entry.name);
    if (!match || !isGoalProgressUpdateVersion(match[1] ?? "")) {
      continue;
    }
    const pid = Number(match[2]);
    if (!Number.isSafeInteger(pid) || pid <= 0 || isProcessAlive(pid)) {
      continue;
    }
    const candidate = resolve(updatesRoot, entry.name);
    const metadata = await lstat(candidate).catch(() => undefined);
    if (!metadata) {
      continue;
    }
    await rm(candidate, { recursive: metadata.isDirectory(), force: true });
    removed.push(entry.name);
  }
  return removed.sort();
}

export function parseGoalProgressZipInfoSizes(permissionLines: readonly string[]): number {
  let uncompressedBytes = 0;
  for (const permissionLine of permissionLines) {
    const sizeText = permissionLine.trim().split(/\s+/u)[3];
    if (sizeText === undefined || !/^\d+$/u.test(sizeText)) {
      throw new Error("GOAL_PROGRESS_UPDATE_ZIP_INVALID");
    }
    const size = Number(sizeText);
    if (!Number.isSafeInteger(size) || size < 0) {
      throw new Error("GOAL_PROGRESS_UPDATE_ZIP_INVALID");
    }
    uncompressedBytes += size;
    if (
      !Number.isSafeInteger(uncompressedBytes) ||
      uncompressedBytes > GOAL_PROGRESS_UPDATE_ZIP_MAX_BYTES
    ) {
      throw new Error("GOAL_PROGRESS_UPDATE_ZIP_INVALID");
    }
  }
  return uncompressedBytes;
}

function assertSafeArchiveEntries(
  entries: readonly string[],
  permissions: readonly string[],
): void {
  if (entries.length === 0 || entries.length !== permissions.length) {
    throw new Error("GOAL_PROGRESS_UPDATE_ZIP_INVALID");
  }
  parseGoalProgressZipInfoSizes(permissions);
  for (let index = 0; index < entries.length; index += 1) {
    const entry = entries[index] ?? "";
    const permissionLine = permissions[index] ?? "";
    const segments = entry.split("/");
    if (
      !entry ||
      entry.includes("\0") ||
      entry.includes("\\") ||
      entry.startsWith("/") ||
      segments.includes("..") ||
      segments[0] !== GOAL_PROGRESS_UPDATE_ARCHIVE_ROOT ||
      segments.some(
        (segment) => segment === "__MACOSX" || segment === ".DS_Store" || segment.startsWith("._"),
      ) ||
      permissionLine.startsWith("l")
    ) {
      throw new Error("GOAL_PROGRESS_UPDATE_ZIP_INVALID");
    }
  }
}

export async function assertGoalProgressExtractedTree(path: string): Promise<void> {
  const metadata = await lstat(path);
  if (!metadata.isDirectory() && !metadata.isFile()) {
    throw new Error("GOAL_PROGRESS_UPDATE_ZIP_INVALID");
  }
  if (!metadata.isDirectory()) {
    return;
  }
  for (const entry of await readdir(path)) {
    await assertGoalProgressExtractedTree(resolve(path, entry));
  }
}

export async function assertGoalProgressRealDirectory(path: string): Promise<void> {
  const metadata = await lstat(path);
  if (!metadata.isDirectory() || metadata.isSymbolicLink()) {
    throw new Error("GOAL_PROGRESS_UPDATE_ZIP_INVALID");
  }
}

async function inspectArchive(zipPath: string): Promise<void> {
  const entries = (
    await run("/usr/bin/unzip", ["-Z1", zipPath], "GOAL_PROGRESS_UPDATE_ZIP_INVALID")
  )
    .split("\n")
    .filter(Boolean);
  const permissions = (
    await run("/usr/bin/zipinfo", ["-l", zipPath], "GOAL_PROGRESS_UPDATE_ZIP_INVALID")
  )
    .split("\n")
    .filter((line) => /^[-dl][rwxStTs-]{9}\s/u.test(line));
  assertSafeArchiveEntries(entries, permissions);
}

async function extractAndVerify(
  zipPath: string,
  extractionRoot: string,
  manifest: GoalProgressUpdateManifest,
): Promise<string> {
  await inspectArchive(zipPath);
  await mkdir(extractionRoot, { mode: 0o700 });
  await run(
    "/usr/bin/unzip",
    ["-qq", zipPath, "-d", extractionRoot],
    "GOAL_PROGRESS_UPDATE_ZIP_INVALID",
  );
  await assertGoalProgressExtractedTree(extractionRoot);
  const children = await readdir(extractionRoot);
  if (children.length !== 1 || children[0] !== GOAL_PROGRESS_UPDATE_ARCHIVE_ROOT) {
    throw new Error("GOAL_PROGRESS_UPDATE_ZIP_INVALID");
  }
  const releaseRoot = resolve(extractionRoot, GOAL_PROGRESS_UPDATE_ARCHIVE_ROOT);
  const release = await readVerifiedRelease(releaseRoot);
  if (release.releaseVersion !== manifest.version) {
    throw new Error("GOAL_PROGRESS_UPDATE_RELEASE_VERSION_MISMATCH");
  }
  return releaseRoot;
}

async function verifyPreparedDirectory(
  directory: string,
  manifest: GoalProgressUpdateManifest,
): Promise<PreparedGoalProgressUpdate> {
  const releaseDirectory = resolve(directory, "release");
  const releaseRoot = resolve(releaseDirectory, GOAL_PROGRESS_UPDATE_ARCHIVE_ROOT);
  await assertGoalProgressRealDirectory(directory);
  await assertGoalProgressRealDirectory(releaseDirectory);
  await assertGoalProgressRealDirectory(releaseRoot);
  await assertGoalProgressExtractedTree(releaseDirectory);
  const zipPath = resolve(directory, GOAL_PROGRESS_MACOS_UPDATE_ASSET);
  const expectedZipSha = parseOuterSha256Sums(
    await readFile(resolve(directory, "SHA256SUMS"), "utf8"),
  );
  const actualZipSha = await fileSha256(zipPath);
  if (actualZipSha !== expectedZipSha) {
    throw new Error("GOAL_PROGRESS_UPDATE_ZIP_SHA256_MISMATCH");
  }
  await inspectArchive(zipPath);
  const release = await readVerifiedRelease(releaseRoot);
  if (release.releaseVersion !== manifest.version) {
    throw new Error("GOAL_PROGRESS_UPDATE_RELEASE_VERSION_MISMATCH");
  }
  const zipMetadata = await stat(zipPath);
  return {
    version: manifest.version,
    verifiedReleaseRoot: releaseRoot,
    zipSha256: actualZipSha,
    releaseManifestSha256: await fileSha256(resolve(releaseRoot, "manifest.json")),
    downloadedBytes: zipMetadata.size,
    totalBytes: zipMetadata.size,
  };
}

export async function prepareGoalProgressUpdate(
  options: PrepareGoalProgressUpdateOptions,
): Promise<PreparedGoalProgressUpdate> {
  const fetchImpl = options.fetchImpl ?? createGoalProgressUpdateFetch();
  const updatesRoot = resolve(options.paths.installRoot, "updates");
  const finalDirectory = resolve(updatesRoot, options.manifest.version);
  await ensurePrivateDirectory(updatesRoot);
  await cleanupOrphanedGoalProgressUpdateDownloads(options.paths);
  try {
    return await verifyPreparedDirectory(finalDirectory, options.manifest);
  } catch {
    await rm(finalDirectory, { recursive: true, force: true });
  }
  const temporaryDirectory = resolve(
    updatesRoot,
    `.${options.manifest.version}.${process.pid}.${randomBytes(8).toString("hex")}`,
  );
  await mkdir(temporaryDirectory, { mode: 0o700 });
  try {
    const urls = goalProgressVersionedUpdateUrls(options.manifest.version);
    const sums = await withDownloadResponse(
      urls.sha256Sums,
      fetchImpl,
      options.metadataTimeoutMs ?? GOAL_PROGRESS_UPDATE_METADATA_TIMEOUT_MS,
      (response) => readBoundedResponse(response, GOAL_PROGRESS_UPDATE_SHA256SUMS_MAX_BYTES),
      options.signal,
    );
    const expectedZipSha = parseOuterSha256Sums(Buffer.from(sums).toString("utf8"));
    await open(resolve(temporaryDirectory, "SHA256SUMS"), "wx", 0o600).then(async (file) => {
      try {
        await file.writeFile(sums);
        await file.sync();
      } finally {
        await file.close();
      }
    });
    const zipPath = resolve(temporaryDirectory, GOAL_PROGRESS_MACOS_UPDATE_ASSET);
    const downloaded = await withDownloadResponse(
      urls.zip,
      fetchImpl,
      options.zipTimeoutMs ?? GOAL_PROGRESS_UPDATE_ZIP_TIMEOUT_MS,
      (response) => downloadZip(response, zipPath, options),
      options.signal,
    );
    if (downloaded.sha256 !== expectedZipSha) {
      throw new Error("GOAL_PROGRESS_UPDATE_ZIP_SHA256_MISMATCH");
    }
    await options.onVerificationStarted?.();
    const extractedReleaseRoot = await extractAndVerify(
      zipPath,
      resolve(temporaryDirectory, "release"),
      options.manifest,
    );
    const releaseManifestSha256 = await fileSha256(resolve(extractedReleaseRoot, "manifest.json"));
    await rename(temporaryDirectory, finalDirectory);
    return {
      version: options.manifest.version,
      verifiedReleaseRoot: resolve(finalDirectory, "release", GOAL_PROGRESS_UPDATE_ARCHIVE_ROOT),
      zipSha256: downloaded.sha256,
      releaseManifestSha256,
      downloadedBytes: downloaded.bytes,
      totalBytes: downloaded.totalBytes,
    };
  } catch (error) {
    await rm(temporaryDirectory, { recursive: true, force: true });
    throw error;
  }
}
