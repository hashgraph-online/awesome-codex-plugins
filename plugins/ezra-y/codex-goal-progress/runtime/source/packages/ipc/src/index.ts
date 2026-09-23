import { createHash, randomBytes } from "node:crypto";
import { readFileSync, realpathSync, statSync } from "node:fs";
import { chmod, link, lstat, mkdir, open, readdir, readFile, unlink } from "node:fs/promises";
import { basename, dirname, isAbsolute, resolve } from "node:path";
import type { RuntimeProof } from "../../contracts/src/index.js";

export * from "./client.js";
export * from "./protocol.js";
export * from "./server.js";

const RUNTIME_PROOF_KEY_BYTES = 32;
const RUNTIME_PROOF_KEY_FILE = "runtime-context.key";
const RUNTIME_PROOF_CONSUMED_DIRECTORY = "runtime-proof-consumed";
const RUNTIME_PROOF_MARKER_RETENTION_MS = 60_000;
const RUNTIME_PROOF_KEY_TEMP_RETENTION_MS = 60_000;
const RUNTIME_PROOF_KEY_TEMP_PATTERN = /^\.runtime-context\.key\.\d+\.[0-9a-f]{16}$/;
const EXPECTED_PLUGIN_NAME = "codex-goal-progress";
export const PLUGIN_DATA_PLACEHOLDER = "$" + "{PLUGIN_DATA}";

function isAlreadyExists(error: unknown): boolean {
  return (
    error instanceof Error && "code" in error && (error as NodeJS.ErrnoException).code === "EEXIST"
  );
}

function isNotFound(error: unknown): boolean {
  return (
    error instanceof Error && "code" in error && (error as NodeJS.ErrnoException).code === "ENOENT"
  );
}

async function readRuntimeProofKey(keyPath: string): Promise<Uint8Array> {
  await chmod(keyPath, 0o600);
  const key = await readFile(keyPath);
  if (key.length !== RUNTIME_PROOF_KEY_BYTES) {
    throw new Error("GOAL_PROGRESS_RUNTIME_PROOF_KEY_INVALID");
  }
  return Uint8Array.from(key);
}

async function cleanupRuntimeProofKeyTemps(dataRoot: string, nowMs = Date.now()): Promise<void> {
  for (const entry of await readdir(dataRoot)) {
    if (!RUNTIME_PROOF_KEY_TEMP_PATTERN.test(entry)) {
      continue;
    }
    const path = resolve(dataRoot, entry);
    try {
      const metadata = await lstat(path);
      if (nowMs - metadata.mtimeMs >= RUNTIME_PROOF_KEY_TEMP_RETENTION_MS) {
        await unlink(path);
      }
    } catch (error) {
      if (!isNotFound(error)) {
        throw error;
      }
    }
  }
}

export function resolveMcpPluginDataRoot(
  configuredRoot = process.env.GOAL_PROGRESS_PLUGIN_DATA,
  pluginRoot = process.cwd(),
  codexHome = process.env.CODEX_HOME,
): string {
  if (configuredRoot && configuredRoot !== PLUGIN_DATA_PLACEHOLDER) {
    if (!isAbsolute(configuredRoot)) {
      throw new Error("GOAL_PROGRESS_PLUGIN_DATA_MUST_BE_ABSOLUTE");
    }
    return resolve(configuredRoot);
  }

  let versionRoot: string;
  try {
    versionRoot = realpathSync.native(resolve(pluginRoot));
  } catch {
    throw new Error("GOAL_PROGRESS_PLUGIN_DATA_UNRESOLVED");
  }

  const pluginDirectory = dirname(versionRoot);
  const marketplaceDirectory = dirname(pluginDirectory);
  const cacheRoot = dirname(marketplaceDirectory);
  const pluginsRoot = dirname(cacheRoot);
  const canonicalCodexHome = dirname(pluginsRoot);
  const marketplaceName = basename(marketplaceDirectory);
  const pluginName = basename(pluginDirectory);
  const version = basename(versionRoot);
  // Codex selects this cwd. Layout checks prevent accidental misrouting; they are not
  // authentication against another same-user process that recreates a full Codex home.
  if (
    basename(cacheRoot) !== "cache" ||
    basename(pluginsRoot) !== "plugins" ||
    !marketplaceName ||
    pluginName !== EXPECTED_PLUGIN_NAME ||
    !version
  ) {
    throw new Error("GOAL_PROGRESS_PLUGIN_DATA_UNRESOLVED");
  }

  try {
    if (codexHome) {
      const expectedCacheRoot = realpathSync.native(resolve(codexHome, "plugins/cache"));
      if (expectedCacheRoot !== cacheRoot) {
        throw new Error("cache mismatch");
      }
    }
    if (!statSync(resolve(canonicalCodexHome, "config.toml")).isFile()) {
      throw new Error("config missing");
    }
    const manifest = JSON.parse(
      readFileSync(resolve(versionRoot, ".codex-plugin/plugin.json"), "utf8"),
    ) as Record<string, unknown>;
    if (manifest.name !== EXPECTED_PLUGIN_NAME || manifest.version !== version) {
      throw new Error("manifest mismatch");
    }
  } catch {
    throw new Error("GOAL_PROGRESS_PLUGIN_DATA_UNRESOLVED");
  }

  return resolve(canonicalCodexHome, "plugins/data", `${EXPECTED_PLUGIN_NAME}-${marketplaceName}`);
}

export async function loadOrCreateRuntimeProofKey(pluginDataRoot: string): Promise<Uint8Array> {
  const dataRoot = resolve(pluginDataRoot);
  await mkdir(dataRoot, { recursive: true, mode: 0o700 });
  await chmod(dataRoot, 0o700);
  await cleanupRuntimeProofKeyTemps(dataRoot);
  const keyPath = resolve(dataRoot, RUNTIME_PROOF_KEY_FILE);
  try {
    return await readRuntimeProofKey(keyPath);
  } catch (error) {
    if (!isNotFound(error)) {
      throw error;
    }
  }

  const temporaryPath = resolve(
    dataRoot,
    `.${RUNTIME_PROOF_KEY_FILE}.${process.pid}.${randomBytes(8).toString("hex")}`,
  );

  const temporaryFile = await open(temporaryPath, "wx", 0o600);
  try {
    await temporaryFile.writeFile(randomBytes(RUNTIME_PROOF_KEY_BYTES));
    await temporaryFile.sync();
  } finally {
    await temporaryFile.close();
  }

  try {
    await link(temporaryPath, keyPath);
  } catch (error) {
    if (!isAlreadyExists(error)) {
      throw error;
    }
  } finally {
    await unlink(temporaryPath).catch(() => undefined);
  }

  return readRuntimeProofKey(keyPath);
}

function runtimeProofMarkerName(proof: RuntimeProof): string {
  return createHash("sha256")
    .update(proof.toolUseId)
    .update("\0")
    .update(proof.nonce)
    .update("\0")
    .update(proof.signature)
    .digest("hex");
}

async function pruneConsumedRuntimeProofs(directory: string, nowMs: number): Promise<void> {
  const entries = await readdir(directory);
  await Promise.all(
    entries.map(async (entry) => {
      if (!/^[0-9a-f]{64}$/.test(entry)) {
        return;
      }
      const markerPath = resolve(directory, entry);
      try {
        const metadata = await lstat(markerPath);
        if (nowMs - metadata.mtimeMs > RUNTIME_PROOF_MARKER_RETENTION_MS) {
          await unlink(markerPath);
        }
      } catch (error) {
        if (!isNotFound(error)) {
          throw error;
        }
      }
    }),
  );
}

export async function consumeRuntimeProofOnce(
  pluginDataRoot: string,
  proof: RuntimeProof,
  nowMs = Date.now(),
): Promise<boolean> {
  const dataRoot = resolve(pluginDataRoot);
  const consumedDirectory = resolve(dataRoot, RUNTIME_PROOF_CONSUMED_DIRECTORY);
  await mkdir(consumedDirectory, { recursive: true, mode: 0o700 });
  await chmod(consumedDirectory, 0o700);
  await pruneConsumedRuntimeProofs(consumedDirectory, nowMs);

  const markerPath = resolve(consumedDirectory, runtimeProofMarkerName(proof));
  let marker: Awaited<ReturnType<typeof open>>;
  try {
    marker = await open(markerPath, "wx", 0o600);
  } catch (error) {
    if (isAlreadyExists(error)) {
      return false;
    }
    throw error;
  }

  try {
    await marker.writeFile(`${proof.issuedAtMs}\n`);
    await marker.sync();
  } finally {
    await marker.close();
  }
  return true;
}
