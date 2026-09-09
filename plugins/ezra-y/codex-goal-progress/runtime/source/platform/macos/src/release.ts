import { isAbsolute, relative, resolve } from "node:path";

export const GOAL_PROGRESS_MACOS_RELEASE_NODE_VERSION = "v24.19.0" as const;
export const GOAL_PROGRESS_INSTALL_COMMAND_PATH = "Install Goal Progress.command" as const;
export const GOAL_PROGRESS_REPAIR_COMMAND_PATH = "Repair Goal Progress.command" as const;
export const GOAL_PROGRESS_DISABLE_COMMAND_PATH = "Disable Goal Progress.command" as const;
export const GOAL_PROGRESS_UNINSTALL_COMMAND_PATH = "Uninstall Goal Progress.command" as const;

export interface MacosReleaseFile {
  readonly path: string;
  readonly bytes: number;
  readonly sha256: string;
}

export function createNodeSeaConfig() {
  return {
    main: "helper.cjs",
    output: "sea.blob",
    disableExperimentalSEAWarning: true,
    useSnapshot: false,
    useCodeCache: false,
    execArgvExtension: "none" as const,
  };
}

export function assertReleaseBinaryHygiene(
  contents: Buffer,
  forbiddenAbsolutePaths: readonly string[],
): void {
  const forbidden = [
    ".build/helper.cjs",
    ...forbiddenAbsolutePaths.filter((path) => isAbsolute(path)),
  ];
  if (forbidden.some((value) => value && contents.includes(Buffer.from(value, "utf8")))) {
    throw new Error("GOAL_PROGRESS_RELEASE_BINARY_PATH_LEAK");
  }
}

export interface CreateMacosReleaseManifestInput {
  readonly releaseVersion: string;
  readonly rendererReleaseVersion: string;
  readonly nodeVersion: string;
  readonly pluginTreeManifestSha256: string;
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
}

function assertReleaseFile(file: MacosReleaseFile): void {
  if (
    !file.path ||
    !Number.isSafeInteger(file.bytes) ||
    file.bytes < 0 ||
    !/^[0-9a-f]{64}$/u.test(file.sha256)
  ) {
    throw new Error("GOAL_PROGRESS_RELEASE_FILE_INVALID");
  }
}

export function createMacosReleaseManifest(input: CreateMacosReleaseManifestInput) {
  if (!input.releaseVersion || input.releaseVersion !== input.rendererReleaseVersion) {
    throw new Error("GOAL_PROGRESS_RELEASE_VERSION_MISMATCH");
  }
  if (!/^[0-9a-f]{64}$/u.test(input.pluginTreeManifestSha256)) {
    throw new Error("GOAL_PROGRESS_PLUGIN_TREE_MANIFEST_SHA256_INVALID");
  }
  for (const file of [
    input.helper,
    input.startupListener,
    input.renderer,
    input.rendererManifest,
    input.pluginArchive,
    input.license,
    input.nodeLicense,
    input.thirdPartyNotices,
    input.readme,
    input.installGuide,
    input.installCommand,
    input.repairCommand,
    input.disableCommand,
    input.uninstallCommand,
  ]) {
    assertReleaseFile(file);
  }
  return {
    schemaVersion: 1 as const,
    releaseVersion: input.releaseVersion,
    platform: "darwin" as const,
    arch: "arm64" as const,
    runtime: {
      kind: "node-sea" as const,
      nodeVersion: input.nodeVersion,
    },
    pluginTreeManifestSha256: input.pluginTreeManifestSha256,
    files: {
      helper: input.helper,
      startupListener: input.startupListener,
      renderer: input.renderer,
      rendererManifest: input.rendererManifest,
      pluginArchive: input.pluginArchive,
      license: input.license,
      nodeLicense: input.nodeLicense,
      thirdPartyNotices: input.thirdPartyNotices,
      readme: input.readme,
      installGuide: input.installGuide,
      installCommand: input.installCommand,
      repairCommand: input.repairCommand,
      disableCommand: input.disableCommand,
      uninstallCommand: input.uninstallCommand,
    },
  };
}

export function renderInstallGoalProgressCommand(): string {
  return renderGoalProgressCommand("install");
}

export function renderRepairGoalProgressCommand(): string {
  return renderGoalProgressCommand("repair");
}

export function renderDisableGoalProgressCommand(): string {
  return renderGoalProgressCommand("emergency-disable");
}

export function renderUninstallGoalProgressCommand(): string {
  return renderGoalProgressCommand("uninstall");
}

function renderGoalProgressCommand(command: string): string {
  return [
    "#!/bin/sh",
    "set -u",
    'script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)',
    `"$script_dir/bin/goal-progress" ${command} --human`,
    "status=$?",
    "if [ -t 0 ]; then",
    '  printf "\\nPress Return to close..."',
    "  read -r _",
    "fi",
    "exit $status",
    "",
  ].join("\n");
}

export function renderSha256Sums(files: readonly MacosReleaseFile[]): string {
  for (const file of files) {
    assertReleaseFile(file);
  }
  return [...files]
    .sort((left, right) => left.path.localeCompare(right.path))
    .map((file) => `${file.sha256}  ${file.path}\n`)
    .join("");
}

export function assertSafeMacosReleaseOutput(workspaceRoot: string, outputRoot: string): void {
  if (!isAbsolute(workspaceRoot) || !isAbsolute(outputRoot)) {
    throw new Error("GOAL_PROGRESS_RELEASE_OUTPUT_INVALID");
  }
  const workspace = resolve(workspaceRoot);
  const output = resolve(outputRoot);
  const workspaceFromOutput = relative(output, workspace);
  if (
    output === "/" ||
    workspaceFromOutput === "" ||
    (!workspaceFromOutput.startsWith("..") && !isAbsolute(workspaceFromOutput))
  ) {
    throw new Error("GOAL_PROGRESS_RELEASE_OUTPUT_UNSAFE");
  }
}
