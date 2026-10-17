import { createHash } from "node:crypto";
import {
  chmod,
  copyFile,
  lstat,
  readFile,
  readlink,
  rename,
  stat,
  symlink,
  unlink,
} from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { ensurePrivateDirectory } from "../../../packages/store/src/index.js";
import { CODEX_BUNDLE_ID, CODEX_TEAM_ID } from "./app-discovery.js";
import {
  ensureMacosInstallationDirectories,
  type MacosInstallationLayout,
} from "./install-layout.js";
import { isNotFound } from "./macos-errors.js";
import type { MacosReleaseFile } from "./release.js";

export const INSTALL_MANIFEST_SCHEMA_VERSION = 1;

export interface CodexInstallIdentity {
  readonly realAppPath: string;
  readonly bundleId: string;
  readonly teamId: string;
}

export interface ParsedReleaseManifest {
  readonly schemaVersion: 1;
  readonly releaseVersion: string;
  readonly platform: "darwin";
  readonly arch: "arm64";
  readonly pluginTreeManifestSha256: string;
  readonly runtime: {
    readonly kind: "node-sea";
    readonly nodeVersion: string;
  };
  readonly files: {
    readonly helper: MacosReleaseFile;
    readonly startupListener: MacosReleaseFile;
    readonly renderer: MacosReleaseFile;
    readonly rendererManifest: MacosReleaseFile;
    readonly pluginArchive: MacosReleaseFile;
    readonly license: MacosReleaseFile;
    readonly nodeLicense: MacosReleaseFile;
    readonly thirdPartyNotices: MacosReleaseFile;
    readonly readme: MacosReleaseFile;
    readonly installGuide: MacosReleaseFile;
    readonly installCommand: MacosReleaseFile;
    readonly repairCommand: MacosReleaseFile;
    readonly disableCommand: MacosReleaseFile;
    readonly uninstallCommand: MacosReleaseFile;
  };
}

export interface InstalledManifest {
  readonly schemaVersion: 1;
  readonly releaseVersion: string;
  readonly installedAt: string;
  readonly helperSha256: string;
  readonly pluginVersion: string;
  readonly hookSha256: string;
  readonly programReleaseRoot: string;
  readonly currentReleasePath: string;
  readonly launchAgentLabel: string;
  readonly launchAgentPath: string;
  readonly codex: CodexInstallIdentity;
}

function assertReleaseFile(file: unknown): asserts file is MacosReleaseFile {
  if (
    file === null ||
    typeof file !== "object" ||
    !("path" in file) ||
    typeof file.path !== "string" ||
    file.path.startsWith("/") ||
    file.path.split("/").includes("..") ||
    !("bytes" in file) ||
    !Number.isSafeInteger(file.bytes) ||
    Number(file.bytes) < 0 ||
    !("sha256" in file) ||
    typeof file.sha256 !== "string" ||
    !/^[0-9a-f]{64}$/u.test(file.sha256)
  ) {
    throw new Error("GOAL_PROGRESS_RELEASE_FILE_INVALID");
  }
}

function parseReleaseManifest(input: unknown): ParsedReleaseManifest {
  if (
    input === null ||
    typeof input !== "object" ||
    !("schemaVersion" in input) ||
    input.schemaVersion !== 1 ||
    !("releaseVersion" in input) ||
    typeof input.releaseVersion !== "string" ||
    !("platform" in input) ||
    input.platform !== "darwin" ||
    !("arch" in input) ||
    input.arch !== "arm64" ||
    !("pluginTreeManifestSha256" in input) ||
    typeof input.pluginTreeManifestSha256 !== "string" ||
    !/^[0-9a-f]{64}$/u.test(input.pluginTreeManifestSha256) ||
    !("runtime" in input) ||
    input.runtime === null ||
    typeof input.runtime !== "object" ||
    !("kind" in input.runtime) ||
    input.runtime.kind !== "node-sea" ||
    !("nodeVersion" in input.runtime) ||
    typeof input.runtime.nodeVersion !== "string" ||
    !("files" in input) ||
    input.files === null ||
    typeof input.files !== "object" ||
    !("helper" in input.files) ||
    !("startupListener" in input.files) ||
    !("renderer" in input.files) ||
    !("rendererManifest" in input.files) ||
    !("pluginArchive" in input.files) ||
    !("license" in input.files) ||
    !("nodeLicense" in input.files) ||
    !("thirdPartyNotices" in input.files) ||
    !("readme" in input.files) ||
    !("installGuide" in input.files) ||
    !("installCommand" in input.files) ||
    !("repairCommand" in input.files) ||
    !("disableCommand" in input.files) ||
    !("uninstallCommand" in input.files)
  ) {
    throw new Error("GOAL_PROGRESS_RELEASE_MANIFEST_INVALID");
  }
  assertReleaseFile(input.files.helper);
  assertReleaseFile(input.files.startupListener);
  assertReleaseFile(input.files.renderer);
  assertReleaseFile(input.files.rendererManifest);
  assertReleaseFile(input.files.pluginArchive);
  assertReleaseFile(input.files.license);
  assertReleaseFile(input.files.nodeLicense);
  assertReleaseFile(input.files.thirdPartyNotices);
  assertReleaseFile(input.files.readme);
  assertReleaseFile(input.files.installGuide);
  assertReleaseFile(input.files.installCommand);
  assertReleaseFile(input.files.repairCommand);
  assertReleaseFile(input.files.disableCommand);
  assertReleaseFile(input.files.uninstallCommand);
  return input as ParsedReleaseManifest;
}

export async function fileSha256(path: string): Promise<string> {
  return createHash("sha256")
    .update(await readFile(path))
    .digest("hex");
}

async function verifyReleaseFile(root: string, file: MacosReleaseFile): Promise<void> {
  const path = resolve(root, file.path);
  if (!path.startsWith(`${resolve(root)}/`)) {
    throw new Error("GOAL_PROGRESS_RELEASE_FILE_ESCAPE");
  }
  const metadata = await stat(path);
  if (
    !metadata.isFile() ||
    metadata.size !== file.bytes ||
    (await fileSha256(path)) !== file.sha256
  ) {
    throw new Error(`GOAL_PROGRESS_RELEASE_CHECKSUM_MISMATCH: ${file.path}`);
  }
}

async function verifySha256Sums(
  root: string,
  expectedFiles: readonly MacosReleaseFile[],
): Promise<void> {
  const lines = (await readFile(resolve(root, "SHA256SUMS"), "utf8"))
    .trim()
    .split("\n")
    .filter(Boolean);
  const expected = new Map(expectedFiles.map((file) => [file.path, file.sha256]));
  for (const line of lines) {
    const match = /^([0-9a-f]{64}) {2}(.+)$/u.exec(line);
    if (!match?.[1] || !match[2] || expected.get(match[2]) !== match[1]) {
      throw new Error("GOAL_PROGRESS_RELEASE_SHA256_MANIFEST_INVALID");
    }
    expected.delete(match[2]);
  }
  if (expected.size !== 0) {
    throw new Error("GOAL_PROGRESS_RELEASE_SHA256_MANIFEST_INCOMPLETE");
  }
}

export async function readVerifiedRelease(root: string): Promise<ParsedReleaseManifest> {
  const manifestPath = resolve(root, "manifest.json");
  const manifest = parseReleaseManifest(JSON.parse(await readFile(manifestPath, "utf8")));
  const manifestFile: MacosReleaseFile = {
    path: "manifest.json",
    bytes: (await stat(manifestPath)).size,
    sha256: await fileSha256(manifestPath),
  };
  const files = Object.values(manifest.files);
  await Promise.all(files.map((file) => verifyReleaseFile(root, file)));
  await verifySha256Sums(root, [...files, manifestFile]);
  return manifest;
}

export async function replaceCurrentReleaseLink(
  currentPath: string,
  releasePath: string,
): Promise<void> {
  const temporaryPath = `${currentPath}.${process.pid}.new`;
  await unlink(temporaryPath).catch((error) => {
    if (!isNotFound(error)) {
      throw error;
    }
  });
  try {
    await symlink(releasePath, temporaryPath, "dir");
    try {
      const metadata = await lstat(currentPath);
      if (!metadata.isSymbolicLink()) {
        throw new Error("GOAL_PROGRESS_CURRENT_RELEASE_NOT_SYMLINK");
      }
      await unlink(currentPath);
    } catch (error) {
      if (!isNotFound(error)) {
        throw error;
      }
    }
    await rename(temporaryPath, currentPath);
  } finally {
    await unlink(temporaryPath).catch(() => undefined);
  }
}

export async function readInstalledManifest(path: string): Promise<InstalledManifest | null> {
  try {
    const parsed = JSON.parse(await readFile(path, "utf8")) as InstalledManifest;
    return parsed.schemaVersion === INSTALL_MANIFEST_SCHEMA_VERSION ? parsed : null;
  } catch (error) {
    if (isNotFound(error)) {
      return null;
    }
    throw error;
  }
}

export async function currentLinkMatches(layout: MacosInstallationLayout): Promise<boolean> {
  try {
    return (await readlink(layout.currentReleasePath)) === layout.programReleaseRoot;
  } catch {
    return false;
  }
}

export async function installedReleaseMatches(
  layout: MacosInstallationLayout,
  release: ParsedReleaseManifest,
): Promise<boolean> {
  try {
    const installedRelease = await readVerifiedRelease(layout.programReleaseRoot);
    const installedFiles = Object.values(installedRelease.files).sort((left, right) =>
      left.path.localeCompare(right.path),
    );
    const candidateFiles = Object.values(release.files).sort((left, right) =>
      left.path.localeCompare(right.path),
    );
    return (
      installedRelease.releaseVersion === release.releaseVersion &&
      installedFiles.length === candidateFiles.length &&
      installedFiles.every((installedFile, index) => {
        const candidateFile = candidateFiles[index];
        return (
          candidateFile !== undefined &&
          installedFile.path === candidateFile.path &&
          installedFile.bytes === candidateFile.bytes &&
          installedFile.sha256 === candidateFile.sha256
        );
      })
    );
  } catch {
    return false;
  }
}

export async function copyRelease(
  sourceRoot: string,
  layout: MacosInstallationLayout,
  manifest: ParsedReleaseManifest,
): Promise<void> {
  await ensureMacosInstallationDirectories(layout);
  const files = [
    ...Object.values(manifest.files),
    { path: "manifest.json" },
    { path: "SHA256SUMS" },
  ];
  for (const file of files) {
    const source = resolve(sourceRoot, file.path);
    const destination = resolve(layout.programReleaseRoot, file.path);
    await ensurePrivateDirectory(dirname(destination));
    await copyFile(source, destination);
    await chmod(
      destination,
      file.path === manifest.files.helper.path ||
        file.path === manifest.files.startupListener.path ||
        file.path === manifest.files.installCommand.path ||
        file.path === manifest.files.repairCommand.path ||
        file.path === manifest.files.disableCommand.path ||
        file.path === manifest.files.uninstallCommand.path
        ? 0o700
        : 0o600,
    );
  }
}

export function validateCodexIdentity(identity: CodexInstallIdentity): void {
  if (
    identity.bundleId !== CODEX_BUNDLE_ID ||
    identity.teamId !== CODEX_TEAM_ID ||
    !identity.realAppPath.endsWith(".app")
  ) {
    throw new Error("GOAL_PROGRESS_CODEX_IDENTITY_INVALID");
  }
}
