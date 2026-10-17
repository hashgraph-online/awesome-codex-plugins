import { createHash } from "node:crypto";
import { lstat, readdir, readFile, writeFile } from "node:fs/promises";
import { isAbsolute, relative, resolve, sep } from "node:path";

export const GOAL_PROGRESS_PLUGIN_TREE_MANIFEST = ".goal-progress-files.json";

interface PluginTreeFile {
  readonly path: string;
  readonly sha256: string;
  readonly mode: number;
}

interface PluginTreeManifest {
  readonly schemaVersion: 1;
  readonly files: readonly PluginTreeFile[];
}

function fileSha256(contents: Buffer): string {
  return createHash("sha256").update(contents).digest("hex");
}

function normalizedRelativePath(root: string, path: string): string {
  return relative(root, path).split(sep).join("/");
}

async function assertDirectory(path: string): Promise<void> {
  const metadata = await lstat(path);
  if (metadata.isSymbolicLink()) {
    throw new Error("GOAL_PROGRESS_PLUGIN_SYMLINK_FORBIDDEN");
  }
  if (!metadata.isDirectory()) {
    throw new Error("GOAL_PROGRESS_PLUGIN_TREE_INVALID");
  }
}

export async function assertPluginTreeHasNoSymlinks(root: string): Promise<void> {
  const resolvedRoot = resolve(root);
  await assertDirectory(resolvedRoot);
  const visit = async (directory: string): Promise<void> => {
    const entries = await readdir(directory);
    for (const name of entries.sort()) {
      const path = resolve(directory, name);
      const metadata = await lstat(path);
      if (metadata.isSymbolicLink()) {
        throw new Error("GOAL_PROGRESS_PLUGIN_SYMLINK_FORBIDDEN");
      }
      if (metadata.isDirectory()) {
        await visit(path);
        continue;
      }
      if (!metadata.isFile()) {
        throw new Error("GOAL_PROGRESS_PLUGIN_TREE_INVALID");
      }
    }
  };
  await visit(resolvedRoot);
}

async function collectPluginTreeFiles(root: string): Promise<readonly PluginTreeFile[]> {
  const resolvedRoot = resolve(root);
  await assertDirectory(resolvedRoot);
  const files: PluginTreeFile[] = [];
  const visit = async (directory: string): Promise<void> => {
    const entries = await readdir(directory);
    for (const name of entries.sort()) {
      const path = resolve(directory, name);
      const metadata = await lstat(path);
      if (metadata.isSymbolicLink()) {
        throw new Error("GOAL_PROGRESS_PLUGIN_SYMLINK_FORBIDDEN");
      }
      if (metadata.isDirectory()) {
        await visit(path);
        continue;
      }
      if (!metadata.isFile()) {
        throw new Error("GOAL_PROGRESS_PLUGIN_TREE_INVALID");
      }
      const relativePath = normalizedRelativePath(resolvedRoot, path);
      if (relativePath === GOAL_PROGRESS_PLUGIN_TREE_MANIFEST) {
        continue;
      }
      files.push({
        path: relativePath,
        sha256: fileSha256(await readFile(path)),
        mode: metadata.mode & 0o777,
      });
    }
  };
  await visit(resolvedRoot);
  return files.sort((left, right) => left.path.localeCompare(right.path));
}

function parsePluginTreeManifest(value: unknown): PluginTreeManifest {
  if (
    value === null ||
    typeof value !== "object" ||
    Array.isArray(value) ||
    (value as { schemaVersion?: unknown }).schemaVersion !== 1 ||
    !Array.isArray((value as { files?: unknown }).files)
  ) {
    throw new Error("GOAL_PROGRESS_PLUGIN_TREE_MANIFEST_INVALID");
  }
  const seen = new Set<string>();
  const files = (value as { files: unknown[] }).files.map((entry) => {
    if (
      entry === null ||
      typeof entry !== "object" ||
      Array.isArray(entry) ||
      typeof (entry as { path?: unknown }).path !== "string" ||
      typeof (entry as { sha256?: unknown }).sha256 !== "string" ||
      typeof (entry as { mode?: unknown }).mode !== "number"
    ) {
      throw new Error("GOAL_PROGRESS_PLUGIN_TREE_MANIFEST_INVALID");
    }
    const file = entry as PluginTreeFile;
    if (
      !file.path ||
      isAbsolute(file.path) ||
      file.path.split("/").includes("..") ||
      file.path === GOAL_PROGRESS_PLUGIN_TREE_MANIFEST ||
      !/^[0-9a-f]{64}$/u.test(file.sha256) ||
      !Number.isInteger(file.mode) ||
      file.mode < 0 ||
      file.mode > 0o777 ||
      seen.has(file.path)
    ) {
      throw new Error("GOAL_PROGRESS_PLUGIN_TREE_MANIFEST_INVALID");
    }
    seen.add(file.path);
    return file;
  });
  return {
    schemaVersion: 1,
    files: files.sort((left, right) => left.path.localeCompare(right.path)),
  };
}

export async function writePluginTreeManifest(root: string): Promise<string> {
  const manifest: PluginTreeManifest = {
    schemaVersion: 1,
    files: await collectPluginTreeFiles(root),
  };
  const contents = `${JSON.stringify(manifest, null, 2)}\n`;
  await writeFile(resolve(root, GOAL_PROGRESS_PLUGIN_TREE_MANIFEST), contents, "utf8");
  return fileSha256(Buffer.from(contents, "utf8"));
}

export async function verifyPluginTreeManifest(
  root: string,
  expectedManifestSha256: string,
): Promise<void> {
  if (!/^[0-9a-f]{64}$/u.test(expectedManifestSha256)) {
    throw new Error("GOAL_PROGRESS_PLUGIN_TREE_MANIFEST_SHA256_INVALID");
  }
  await assertPluginTreeHasNoSymlinks(root);
  const manifestPath = resolve(root, GOAL_PROGRESS_PLUGIN_TREE_MANIFEST);
  const manifestMetadata = await lstat(manifestPath);
  if (!manifestMetadata.isFile() || manifestMetadata.isSymbolicLink()) {
    throw new Error("GOAL_PROGRESS_PLUGIN_TREE_MANIFEST_INVALID");
  }
  const manifestContents = await readFile(manifestPath);
  if (fileSha256(manifestContents) !== expectedManifestSha256) {
    throw new Error("GOAL_PROGRESS_PLUGIN_TREE_MANIFEST_SHA256_MISMATCH");
  }
  const expected = parsePluginTreeManifest(JSON.parse(manifestContents.toString("utf8")));
  const actual = await collectPluginTreeFiles(root);
  if (JSON.stringify(expected.files) !== JSON.stringify(actual)) {
    throw new Error("GOAL_PROGRESS_PLUGIN_TREE_MISMATCH");
  }
}
