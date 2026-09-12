import { randomBytes } from "node:crypto";
import { chmod, link, mkdir, open, readdir, rename, stat, unlink } from "node:fs/promises";
import { basename, dirname, resolve } from "node:path";

export interface AtomicWriteFaults {
  beforeRename?(): Promise<void> | void;
}

function escapeRegularExpression(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export async function ensurePrivateDirectory(path: string): Promise<void> {
  const firstCreated = await mkdir(path, { recursive: true, mode: 0o700 });
  await chmod(path, 0o700);
  if (firstCreated) {
    const firstCreatedPath = resolve(firstCreated);
    let current = resolve(path);
    while (true) {
      await syncDirectory(dirname(current));
      if (current === firstCreatedPath) {
        break;
      }
      const parent = dirname(current);
      if (parent === current) {
        break;
      }
      current = parent;
    }
  }
}

async function syncDirectory(path: string): Promise<void> {
  let directory: Awaited<ReturnType<typeof open>> | undefined;
  try {
    directory = await open(path, "r");
    await directory.sync();
  } catch (error) {
    const code =
      error instanceof Error && "code" in error ? (error as NodeJS.ErrnoException).code : undefined;
    if (code !== "EINVAL" && code !== "EPERM" && code !== "EISDIR") {
      throw error;
    }
  } finally {
    await directory?.close();
  }
}

export async function atomicWriteFile(
  path: string,
  contents: string,
  faults: AtomicWriteFaults = {},
): Promise<void> {
  const directory = dirname(path);
  await ensurePrivateDirectory(directory);
  const temporaryPath = resolve(
    directory,
    `.${basename(path)}.${process.pid}.${randomBytes(8).toString("hex")}`,
  );
  const temporaryFile = await open(temporaryPath, "wx", 0o600);
  try {
    try {
      await temporaryFile.writeFile(contents, "utf8");
      await temporaryFile.sync();
    } finally {
      await temporaryFile.close();
    }
    await faults.beforeRename?.();
    await rename(temporaryPath, path);
    await chmod(path, 0o600);
    await syncDirectory(directory);
  } catch (error) {
    await unlink(temporaryPath).catch(() => undefined);
    throw error;
  }
}

export async function atomicCreateFile(path: string, contents: string): Promise<boolean> {
  const directory = dirname(path);
  await ensurePrivateDirectory(directory);
  const temporaryPath = resolve(
    directory,
    `.${basename(path)}.${process.pid}.${randomBytes(8).toString("hex")}`,
  );
  const temporaryFile = await open(temporaryPath, "wx", 0o600);
  let linked = false;
  try {
    try {
      await temporaryFile.writeFile(contents, "utf8");
      await temporaryFile.sync();
    } finally {
      await temporaryFile.close();
    }
    try {
      await link(temporaryPath, path);
    } catch (error) {
      if (
        error instanceof Error &&
        "code" in error &&
        (error as NodeJS.ErrnoException).code === "EEXIST"
      ) {
        return false;
      }
      throw error;
    }
    linked = true;
    await chmod(path, 0o600);
    await syncDirectory(directory);
    return true;
  } catch (error) {
    if (linked) {
      await unlink(path).catch(() => undefined);
    }
    throw error;
  } finally {
    await unlink(temporaryPath).catch(() => undefined);
  }
}

export async function cleanupAtomicTemporaryFiles(
  directory: string,
  baseName: string,
  minimumAgeMs = 0,
): Promise<number> {
  const pattern = new RegExp(`^\\.${escapeRegularExpression(baseName)}\\.\\d+\\.[0-9a-f]{16}$`);
  let removed = 0;
  let entries: string[];
  try {
    entries = await readdir(directory);
  } catch (error) {
    if (
      error instanceof Error &&
      "code" in error &&
      (error as NodeJS.ErrnoException).code === "ENOENT"
    ) {
      return 0;
    }
    throw error;
  }
  for (const entry of entries) {
    if (pattern.test(entry)) {
      if (minimumAgeMs > 0) {
        try {
          const metadata = await stat(resolve(directory, entry));
          if (Date.now() - metadata.mtimeMs < minimumAgeMs) {
            continue;
          }
        } catch (error) {
          if (
            error instanceof Error &&
            "code" in error &&
            (error as NodeJS.ErrnoException).code === "ENOENT"
          ) {
            continue;
          }
          throw error;
        }
      }
      await unlink(resolve(directory, entry));
      removed += 1;
    }
  }
  if (removed > 0) {
    await syncDirectory(directory);
  }
  return removed;
}

export async function appendDurableLine(path: string, line: string): Promise<void> {
  const directory = dirname(path);
  await ensurePrivateDirectory(directory);
  let created = false;
  let file: Awaited<ReturnType<typeof open>>;
  try {
    file = await open(path, "ax", 0o600);
    created = true;
  } catch (error) {
    if (
      !(
        error instanceof Error &&
        "code" in error &&
        (error as NodeJS.ErrnoException).code === "EEXIST"
      )
    ) {
      throw error;
    }
    file = await open(path, "a", 0o600);
  }
  try {
    await chmod(path, 0o600);
    if (created) {
      await file.sync();
      await syncDirectory(directory);
    }
    await file.writeFile(`${line}\n`, "utf8");
    await file.sync();
  } catch (error) {
    await file.close().catch(() => undefined);
    throw error;
  }
  await file.close().catch(() => undefined);
}
