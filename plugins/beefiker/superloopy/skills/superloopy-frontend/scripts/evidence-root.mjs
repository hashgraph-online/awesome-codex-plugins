#!/usr/bin/env node
// Create and verify cross-shell skill evidence roots (frontend or slides lane)
// without relying on a platform-specific date command, path separator, or
// mkdir syntax.

import { lstatSync, mkdirSync, realpathSync } from "node:fs";
import { isAbsolute, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const PORTABLE_SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/u;
const WINDOWS_RESERVED = /^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])$/iu;
const RUN_LANE = /^(?:frontend|slides)$/u;
const RUN_ROOT = /^\.superloopy\/evidence\/(frontend|slides)\/\d{8}T\d{6}Z-([a-z0-9]+(?:-[a-z0-9]+)*)$/u;

export function validateSlug(value) {
  if (typeof value !== "string" || value.length > 48 || !PORTABLE_SLUG.test(value) || WINDOWS_RESERVED.test(value)) {
    throw new Error("slug must be 1-48 lowercase ASCII letters/digits joined by single hyphens and must not be a Windows reserved name");
  }
  return value;
}

export function validateLane(value) {
  if (typeof value !== "string" || !RUN_LANE.test(value)) {
    throw new Error("lane must be frontend or slides");
  }
  return value;
}

export function createEvidenceRoot(slug, lane = "frontend", cwd = process.cwd(), now = new Date()) {
  const safeSlug = validateSlug(slug);
  const safeLane = validateLane(lane);
  const stamp = now.toISOString().replaceAll("-", "").replaceAll(":", "").replace(/\.\d{3}Z$/u, "Z");
  const root = `.superloopy/evidence/${safeLane}/${stamp}-${safeSlug}`;
  const base = realpathSync(cwd);
  ensureDirectoryTree(base, root.split("/"));
  return root;
}

export function verifyEvidenceFiles(root, files, cwd = process.cwd()) {
  const normalizedRoot = root.replaceAll("\\", "/");
  const match = normalizedRoot.match(RUN_ROOT);
  if (!match) throw new Error("evidence root must match .superloopy/evidence/<frontend|slides>/YYYYMMDDTHHMMSSZ-<portable-slug>");
  validateSlug(match[2]);
  if (!Array.isArray(files) || files.length === 0) throw new Error("at least one evidence file is required");

  const base = realpathSync(cwd);
  const absoluteRoot = requireDirectoryTree(base, normalizedRoot.split("/"));
  for (const file of files) {
    if (typeof file !== "string" || file.length === 0 || isAbsolute(file)) throw new Error("evidence filenames must be non-empty relative paths");
    const candidate = resolve(absoluteRoot, file);
    const inside = relative(absoluteRoot, candidate);
    if (inside === "" || inside === ".." || inside.startsWith("../") || inside.startsWith("..\\") || isAbsolute(inside)) {
      throw new Error(`evidence file escapes its run root: ${file}`);
    }
    requireNoSymlinkPath(absoluteRoot, inside);
    const metadata = lstatSync(candidate);
    if (!metadata.isFile() || metadata.size === 0) throw new Error(`evidence file must be a non-empty regular file: ${file}`);
  }
  return normalizedRoot;
}

function ensureDirectoryTree(base, segments) {
  let current = base;
  for (const [index, segment] of segments.entries()) {
    current = resolve(current, segment);
    try {
      const metadata = lstatSync(current);
      if (metadata.isSymbolicLink()) throw new Error(`evidence directory must not be a symlink: ${segment}`);
      if (!metadata.isDirectory()) throw new Error(`evidence path component must be a directory: ${segment}`);
      if (index === segments.length - 1) throw new Error(`evidence run root already exists: ${current}`);
    } catch (error) {
      if (error?.code !== "ENOENT") throw error;
      mkdirSync(current);
    }
  }
  return current;
}

function requireDirectoryTree(base, segments) {
  let current = base;
  for (const segment of segments) {
    current = resolve(current, segment);
    const metadata = lstatSync(current);
    if (metadata.isSymbolicLink()) throw new Error(`evidence directory must not be a symlink: ${segment}`);
    if (!metadata.isDirectory()) throw new Error(`evidence path component must be a directory: ${segment}`);
  }
  return current;
}

function requireNoSymlinkPath(base, relativePath) {
  let current = base;
  for (const segment of relativePath.split(/[\\/]/u)) {
    current = resolve(current, segment);
    if (lstatSync(current).isSymbolicLink()) throw new Error(`evidence file path must not contain symlinks: ${relativePath}`);
  }
}

function main(argv) {
  const [command, value, ...files] = argv;
  if (command === "create" && value && files.length <= 1) {
    process.stdout.write(`${createEvidenceRoot(value, files[0] ?? "frontend")}\n`);
    return;
  }
  if (command === "verify" && value) {
    process.stdout.write(`${verifyEvidenceFiles(value, files)}\n`);
    return;
  }
  throw new Error("usage: evidence-root.mjs create <slug> [frontend|slides] | verify <evidence-root> <file...>");
}

function isCliEntry(argvPath) {
  if (!argvPath) return false;
  try {
    return realpathSync(argvPath) === realpathSync(fileURLToPath(import.meta.url));
  } catch {
    return false;
  }
}

if (isCliEntry(process.argv[1])) {
  try {
    main(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(`evidence-root: ${error.message}\n`);
    process.exitCode = 2;
  }
}
