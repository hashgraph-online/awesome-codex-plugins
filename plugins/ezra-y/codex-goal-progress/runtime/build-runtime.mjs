import { createHash } from "node:crypto";
import { chmod, copyFile, mkdir, readFile, rm, stat, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";

const runtimeRoot = resolve(dirname(fileURLToPath(import.meta.url)));
const args = process.argv.slice(2);
const sourceFlag = args.indexOf("--source");
const outputFlag = args.indexOf("--output");
const sourceRoot = resolve(
  sourceFlag >= 0 && args[sourceFlag + 1] ? args[sourceFlag + 1] : "source",
);
const outputRoot = resolve(
  outputFlag >= 0 && args[outputFlag + 1] ? args[outputFlag + 1] : "output",
);

if (!isAbsolute(sourceRoot) || !isAbsolute(outputRoot)) {
  throw new Error("GOAL_PROGRESS_SOURCE_BUILD_PATH_INVALID");
}

const packageJson = JSON.parse(await readFile(resolve(runtimeRoot, "package.json"), "utf8"));
const releaseVersion = String(packageJson.version ?? "").trim();
if (!/^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/u.test(releaseVersion)) {
  throw new Error("GOAL_PROGRESS_SOURCE_BUILD_VERSION_INVALID");
}
const pageHostVersionDocument = JSON.parse(
  await readFile(resolve(sourceRoot, "packages/contracts/src/page-host-version.json"), "utf8"),
);
const pageHostVersion = pageHostVersionDocument.pageHostVersion;
if (!Number.isSafeInteger(pageHostVersion) || pageHostVersion < 1) {
  throw new Error("GOAL_PROGRESS_SOURCE_BUILD_PAGE_HOST_VERSION_INVALID");
}

await rm(outputRoot, { recursive: true, force: true });
await Promise.all([
  mkdir(resolve(outputRoot, "bin"), { recursive: true }),
  mkdir(resolve(outputRoot, "renderer"), { recursive: true }),
]);

const helperBundlePath = resolve(outputRoot, "bin/goal-progress.cjs");
const cliEntryPath = resolve(sourceRoot, "platform/macos/src/cli.ts");
await build({
  absWorkingDir: sourceRoot,
  bundle: true,
  format: "cjs",
  legalComments: "none",
  logOverride: {
    "empty-import-meta": "silent",
  },
  outfile: helperBundlePath,
  platform: "node",
  stdin: {
    contents: [
      `const { runGoalProgressCli } = require(${JSON.stringify(cliEntryPath)});`,
      "runGoalProgressCli().catch((error) => {",
      '  process.stderr.write((error instanceof Error ? error.message : String(error)) + "\\n");',
      "  process.exitCode = 1;",
      "});",
    ].join("\n"),
    loader: "js",
    resolveDir: sourceRoot,
    sourcefile: "goal-progress-source-runtime-entry.js",
  },
  target: "node22",
});

const rendererPath = resolve(outputRoot, "renderer/goal-progress.js");
await build({
  absWorkingDir: sourceRoot,
  bundle: true,
  entryPoints: ["packages/codex-adapter/src/browser-entry.ts"],
  format: "iife",
  legalComments: "none",
  minify: true,
  outfile: rendererPath,
  platform: "browser",
  target: "chrome120",
});
const renderer = await readFile(rendererPath);
const rendererManifest = {
  schemaVersion: 1,
  releaseVersion,
  pageHostVersion,
  file: "goal-progress.js",
  bytes: renderer.byteLength,
  sha256: createHash("sha256").update(renderer).digest("hex"),
};
await writeFile(
  resolve(outputRoot, "renderer/goal-progress.manifest.json"),
  `${JSON.stringify(rendererManifest, null, 2)}\n`,
);

await Promise.all([
  copyFile(resolve(runtimeRoot, "node-runtime.sh"), resolve(outputRoot, "bin/node-runtime.sh")),
  copyFile(resolve(runtimeRoot, "helper-launcher.sh"), resolve(outputRoot, "bin/goal-progress")),
  copyFile(
    resolve(runtimeRoot, "startup-listener-launcher.sh"),
    resolve(outputRoot, "bin/goal-progress-startup-listener"),
  ),
  copyFile(
    resolve(runtimeRoot, "startup-listener-bridge.mjs"),
    resolve(outputRoot, "bin/startup-listener-bridge.mjs"),
  ),
  copyFile(
    resolve(runtimeRoot, "startup-listener.mjs"),
    resolve(outputRoot, "bin/startup-listener.mjs"),
  ),
  copyFile(
    resolve(runtimeRoot, "startup-listener.jxa"),
    resolve(outputRoot, "bin/startup-listener.jxa"),
  ),
]);
for (const executable of [
  resolve(outputRoot, "bin/node-runtime.sh"),
  resolve(outputRoot, "bin/goal-progress"),
  resolve(outputRoot, "bin/goal-progress-startup-listener"),
]) {
  await chmod(executable, 0o700);
}

async function fileRecord(relativePath) {
  const path = resolve(outputRoot, relativePath);
  const [contents, metadata] = await Promise.all([readFile(path), stat(path)]);
  return {
    path: relativePath,
    bytes: metadata.size,
    sha256: createHash("sha256").update(contents).digest("hex"),
  };
}

const files = {};
for (const relativePath of [
  "bin/goal-progress",
  "bin/goal-progress.cjs",
  "bin/goal-progress-startup-listener",
  "bin/node-runtime.sh",
  "bin/startup-listener-bridge.mjs",
  "bin/startup-listener.mjs",
  "bin/startup-listener.jxa",
  "renderer/goal-progress.js",
  "renderer/goal-progress.manifest.json",
]) {
  files[relativePath] = await fileRecord(relativePath);
}
const manifest = {
  schemaVersion: 1,
  releaseVersion,
  nodeVersion: process.version,
  builtAt: new Date().toISOString(),
  files,
};
await writeFile(resolve(outputRoot, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
