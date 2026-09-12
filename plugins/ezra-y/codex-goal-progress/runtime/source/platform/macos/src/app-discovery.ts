import { execFile } from "node:child_process";
import { constants } from "node:fs";
import { access, realpath, stat } from "node:fs/promises";
import { homedir } from "node:os";
import { basename, isAbsolute, join, relative, resolve } from "node:path";

export const CODEX_BUNDLE_ID = "com.openai.codex";
export const CODEX_TEAM_ID = "2DC432GLL2";

const MAX_COMMAND_OUTPUT_BYTES = 1024 * 1024;
const SYSTEM_COMMANDS = {
  codesign: "/usr/bin/codesign",
  file: "/usr/bin/file",
  lipo: "/usr/bin/lipo",
  mdfind: "/usr/bin/mdfind",
  plutil: "/usr/bin/plutil",
} as const;

export type MacosExecutableArchitecture = "arm64" | "x86_64";

export interface CommandResult {
  readonly exitCode: number;
  readonly stdout: string;
  readonly stderr: string;
}

export type CommandRunner = (command: string, args: readonly string[]) => Promise<CommandResult>;

export interface CodexMacosAppIdentity {
  readonly appPath: string;
  readonly realAppPath: string;
  readonly bundleId: typeof CODEX_BUNDLE_ID;
  readonly shortVersion: string;
  readonly bundleVersion: string;
  readonly executableName: string;
  readonly executablePath: string;
  readonly realExecutablePath: string;
  readonly teamId: typeof CODEX_TEAM_ID;
  readonly signingAuthority: string;
  readonly architectures: readonly MacosExecutableArchitecture[];
  readonly hostArchitecture: MacosExecutableArchitecture;
  readonly fileDescription: string;
  readonly signatureValid: true;
}

export interface RejectedCodexAppCandidate {
  readonly appPath: string;
  readonly error: string;
}

export interface CodexAppDiscoveryResult {
  readonly candidates: readonly string[];
  readonly validApps: readonly CodexMacosAppIdentity[];
  readonly rejectedCandidates: readonly RejectedCodexAppCandidate[];
}

export interface InspectCodexAppOptions {
  readonly runner?: CommandRunner;
  readonly hostArchitecture?: MacosExecutableArchitecture;
}

export interface DiscoverCodexAppsOptions extends InspectCodexAppOptions {
  readonly candidatePaths?: readonly string[];
  readonly includeDefaultCandidates?: boolean;
  readonly useSpotlight?: boolean;
}

export function discoveryError(code: string, detail?: string): Error {
  return new Error(detail ? `${code}: ${detail}` : code);
}

export const runSystemCommand: CommandRunner = (command, args) =>
  new Promise((resolveCommand) => {
    execFile(
      command,
      [...args],
      {
        encoding: "utf8",
        maxBuffer: MAX_COMMAND_OUTPUT_BYTES,
      },
      (error, stdout, stderr) => {
        resolveCommand({
          exitCode: error === null ? 0 : typeof error.code === "number" ? error.code : 1,
          stdout,
          stderr,
        });
      },
    );
  });

export function requireSuccessfulCommand(result: CommandResult, errorCode: string): string {
  if (result.exitCode !== 0) {
    const detail = `${result.stderr}\n${result.stdout}`.trim().slice(0, 1_000);
    throw discoveryError(errorCode, detail || `exit ${result.exitCode}`);
  }
  return result.stdout.trim();
}

async function readPlistValue(
  runner: CommandRunner,
  infoPlistPath: string,
  key: string,
): Promise<string> {
  const result = await runner(SYSTEM_COMMANDS.plutil, ["-extract", key, "raw", infoPlistPath]);
  const value = requireSuccessfulCommand(result, `GOAL_PROGRESS_CODEX_APP_PLIST_${key}`);
  if (!value) {
    throw discoveryError(`GOAL_PROGRESS_CODEX_APP_PLIST_${key}_EMPTY`);
  }
  return value;
}

function parseCodesignValue(output: string, key: string): string | undefined {
  const prefix = `${key}=`;
  return output
    .split(/\r?\n/u)
    .find((line) => line.startsWith(prefix))
    ?.slice(prefix.length);
}

function parseHostArchitecture(architecture: NodeJS.Architecture): MacosExecutableArchitecture {
  if (architecture === "arm64") {
    return "arm64";
  }
  if (architecture === "x64") {
    return "x86_64";
  }
  throw discoveryError("GOAL_PROGRESS_CODEX_APP_UNSUPPORTED_HOST_ARCH", architecture);
}

function parseArchitectures(output: string): readonly MacosExecutableArchitecture[] {
  const architectures = output.trim().split(/\s+/u).filter(Boolean);
  if (
    architectures.length === 0 ||
    architectures.some((architecture) => architecture !== "arm64" && architecture !== "x86_64")
  ) {
    throw discoveryError("GOAL_PROGRESS_CODEX_APP_INVALID_ARCH", output.trim());
  }
  return [...new Set(architectures)] as MacosExecutableArchitecture[];
}

function assertSafeExecutableName(executableName: string): void {
  if (
    executableName === "." ||
    executableName === ".." ||
    basename(executableName) !== executableName
  ) {
    throw discoveryError("GOAL_PROGRESS_CODEX_APP_UNSAFE_EXECUTABLE_NAME");
  }
}

export async function inspectCodexMacosApp(
  appPath: string,
  options: InspectCodexAppOptions = {},
): Promise<CodexMacosAppIdentity> {
  if (!isAbsolute(appPath)) {
    throw discoveryError("GOAL_PROGRESS_CODEX_APP_PATH_NOT_ABSOLUTE");
  }
  const runner = options.runner ?? runSystemCommand;
  const realAppPath = await realpath(appPath);
  if (!realAppPath.endsWith(".app")) {
    throw discoveryError("GOAL_PROGRESS_CODEX_APP_NOT_APP_BUNDLE");
  }
  const appStat = await stat(realAppPath);
  if (!appStat.isDirectory()) {
    throw discoveryError("GOAL_PROGRESS_CODEX_APP_NOT_DIRECTORY");
  }

  const infoPlistPath = join(realAppPath, "Contents", "Info.plist");
  const bundleId = await readPlistValue(runner, infoPlistPath, "CFBundleIdentifier");
  if (bundleId !== CODEX_BUNDLE_ID) {
    throw discoveryError("GOAL_PROGRESS_CODEX_APP_BUNDLE_ID_MISMATCH", bundleId);
  }

  const executableName = await readPlistValue(runner, infoPlistPath, "CFBundleExecutable");
  assertSafeExecutableName(executableName);
  const [shortVersion, bundleVersion] = await Promise.all([
    readPlistValue(runner, infoPlistPath, "CFBundleShortVersionString"),
    readPlistValue(runner, infoPlistPath, "CFBundleVersion"),
  ]);

  const executablePath = join(realAppPath, "Contents", "MacOS", executableName);
  const realExecutablePath = await realpath(executablePath);
  const executableRoot = join(realAppPath, "Contents", "MacOS");
  const executableRelativePath = relative(executableRoot, realExecutablePath);
  if (executableRelativePath.startsWith("..") || isAbsolute(executableRelativePath)) {
    throw discoveryError("GOAL_PROGRESS_CODEX_APP_EXECUTABLE_ESCAPE");
  }
  const executableStat = await stat(realExecutablePath);
  if (!executableStat.isFile()) {
    throw discoveryError("GOAL_PROGRESS_CODEX_APP_EXECUTABLE_NOT_FILE");
  }
  await access(realExecutablePath, constants.X_OK);

  const signatureDetails = await runner(SYSTEM_COMMANDS.codesign, [
    "-dv",
    "--verbose=4",
    realAppPath,
  ]);
  const codesignOutput = `${signatureDetails.stdout}\n${signatureDetails.stderr}`;
  if (signatureDetails.exitCode !== 0) {
    throw discoveryError("GOAL_PROGRESS_CODEX_APP_SIGNATURE_DETAILS_FAILED");
  }
  const signedIdentifier = parseCodesignValue(codesignOutput, "Identifier");
  const teamId = parseCodesignValue(codesignOutput, "TeamIdentifier");
  const signingAuthority = parseCodesignValue(codesignOutput, "Authority");
  if (signedIdentifier !== CODEX_BUNDLE_ID) {
    throw discoveryError("GOAL_PROGRESS_CODEX_APP_SIGNED_IDENTIFIER_MISMATCH", signedIdentifier);
  }
  if (teamId !== CODEX_TEAM_ID) {
    throw discoveryError("GOAL_PROGRESS_CODEX_APP_TEAM_ID_MISMATCH", teamId);
  }
  if (!signingAuthority) {
    throw discoveryError("GOAL_PROGRESS_CODEX_APP_AUTHORITY_MISSING");
  }

  const signatureVerification = await runner(SYSTEM_COMMANDS.codesign, [
    "--verify",
    "--deep",
    "--strict",
    realAppPath,
  ]);
  requireSuccessfulCommand(signatureVerification, "GOAL_PROGRESS_CODEX_APP_SIGNATURE_INVALID");

  const lipoResult = await runner(SYSTEM_COMMANDS.lipo, ["-archs", realExecutablePath]);
  const architectures = parseArchitectures(
    requireSuccessfulCommand(lipoResult, "GOAL_PROGRESS_CODEX_APP_ARCH_READ_FAILED"),
  );
  const hostArchitecture = options.hostArchitecture ?? parseHostArchitecture(process.arch);
  if (!architectures.includes(hostArchitecture)) {
    throw discoveryError(
      "GOAL_PROGRESS_CODEX_APP_HOST_ARCH_MISMATCH",
      `${hostArchitecture} not in ${architectures.join(",")}`,
    );
  }

  const fileResult = await runner(SYSTEM_COMMANDS.file, ["-b", realExecutablePath]);
  const fileDescription = requireSuccessfulCommand(
    fileResult,
    "GOAL_PROGRESS_CODEX_APP_FILE_READ_FAILED",
  );
  if (!fileDescription.includes("Mach-O")) {
    throw discoveryError("GOAL_PROGRESS_CODEX_APP_EXECUTABLE_NOT_MACHO");
  }

  return {
    appPath: resolve(appPath),
    realAppPath,
    bundleId: CODEX_BUNDLE_ID,
    shortVersion,
    bundleVersion,
    executableName,
    executablePath,
    realExecutablePath,
    teamId: CODEX_TEAM_ID,
    signingAuthority,
    architectures,
    hostArchitecture,
    fileDescription,
    signatureValid: true,
  };
}

function defaultCandidatePaths(): readonly string[] {
  return [
    "/Applications/Codex.app",
    "/Applications/ChatGPT.app",
    join(homedir(), "Applications", "Codex.app"),
    join(homedir(), "Applications", "ChatGPT.app"),
  ];
}

export async function discoverCodexMacosApps(
  options: DiscoverCodexAppsOptions = {},
): Promise<CodexAppDiscoveryResult> {
  const runner = options.runner ?? runSystemCommand;
  const candidatePaths = new Set<string>(options.candidatePaths ?? []);
  if (options.includeDefaultCandidates ?? true) {
    for (const candidatePath of defaultCandidatePaths()) {
      candidatePaths.add(candidatePath);
    }
  }
  if (options.useSpotlight ?? true) {
    const spotlight = await runner(SYSTEM_COMMANDS.mdfind, [
      `kMDItemCFBundleIdentifier == "${CODEX_BUNDLE_ID}"`,
    ]);
    if (spotlight.exitCode === 0) {
      for (const candidatePath of spotlight.stdout.split(/\r?\n/u)) {
        if (candidatePath.trim()) {
          candidatePaths.add(candidatePath.trim());
        }
      }
    }
  }

  const candidates = [...candidatePaths];
  const validApps: CodexMacosAppIdentity[] = [];
  const rejectedCandidates: RejectedCodexAppCandidate[] = [];
  const seenRealAppPaths = new Set<string>();

  for (const candidatePath of candidates) {
    try {
      const identity = await inspectCodexMacosApp(candidatePath, {
        runner,
        ...(options.hostArchitecture === undefined
          ? {}
          : { hostArchitecture: options.hostArchitecture }),
      });
      if (!seenRealAppPaths.has(identity.realAppPath)) {
        validApps.push(identity);
        seenRealAppPaths.add(identity.realAppPath);
      }
    } catch (error) {
      rejectedCandidates.push({
        appPath: candidatePath,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  return {
    candidates,
    validApps,
    rejectedCandidates,
  };
}

export async function requireSingleCodexMacosApp(
  options: DiscoverCodexAppsOptions = {},
): Promise<CodexMacosAppIdentity> {
  const discovery = await discoverCodexMacosApps(options);
  if (discovery.validApps.length === 0) {
    throw discoveryError(
      "GOAL_PROGRESS_CODEX_APP_NOT_FOUND",
      discovery.rejectedCandidates.map((candidate) => candidate.error).join("; "),
    );
  }
  if (discovery.validApps.length > 1) {
    throw discoveryError(
      "GOAL_PROGRESS_CODEX_APP_AMBIGUOUS",
      discovery.validApps.map((app) => app.realAppPath).join(", "),
    );
  }
  const app = discovery.validApps[0];
  if (!app) {
    throw discoveryError("GOAL_PROGRESS_CODEX_APP_NOT_FOUND");
  }
  return app;
}
