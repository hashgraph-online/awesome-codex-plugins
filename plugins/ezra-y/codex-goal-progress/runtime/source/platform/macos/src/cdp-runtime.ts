import { type ChildProcess, spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { chmod, mkdir, readFile, rename, stat, unlink, writeFile } from "node:fs/promises";
import { createServer, Socket } from "node:net";
import { dirname, isAbsolute, resolve } from "node:path";
import {
  CODEX_BUNDLE_ID,
  CODEX_TEAM_ID,
  type CodexMacosAppIdentity,
  type CommandRunner,
  discoveryError,
  requireSuccessfulCommand,
  runSystemCommand,
} from "./app-discovery.js";

const LOOPBACK_ADDRESS = "127.0.0.1";
const PROCESS_LOOKUP_LIMIT = 32;
const PROCESS_LAUNCH_TIMEOUT_MS = 15_000;
const PROCESS_STOP_TIMEOUT_MS = 5_000;

export interface CodexCdpProcessSnapshot {
  readonly pid: number;
  readonly parentPid: number;
  readonly startedAt: string;
  readonly command: string;
}

export interface CodexCdpListener {
  readonly pid: number;
  readonly commandName: string;
  readonly address: string;
}

export interface CodexCdpListenerOwnership {
  readonly mainProcess: CodexCdpProcessSnapshot;
  readonly listeners: readonly CodexCdpListener[];
  readonly listenerPids: readonly number[];
}

export interface CodexCdpRuntimeState {
  readonly schemaVersion: 1;
  readonly launchId: string;
  readonly address: typeof LOOPBACK_ADDRESS;
  readonly port: number;
  readonly mainPid: number;
  readonly launchedAt: string;
  readonly processStartedAt: string;
  readonly executablePath: string;
  readonly appPath: string;
  readonly bundleId: typeof CODEX_BUNDLE_ID;
  readonly teamId: typeof CODEX_TEAM_ID;
  readonly command: string;
  readonly listenerPids: readonly number[];
}

export interface LaunchCodexCdpOptions {
  readonly port: number;
  readonly userDataDir?: string;
  readonly headless?: boolean;
  readonly extraArgs?: readonly string[];
  readonly runner?: CommandRunner;
  readonly processSnapshotTimeoutMs?: number;
  readonly postSpawnCleanupTimeoutMs?: number;
  readonly portOpenProbe?: (port: number) => Promise<boolean>;
  readonly spawnProcess?: (executablePath: string, args: readonly string[]) => ChildProcess;
}

export class CodexCdpPostSpawnCleanupError extends Error {
  readonly port: number;
  readonly userDataDir: string | undefined;

  constructor(port: number, userDataDir: string | undefined, detail: string) {
    super(
      `GOAL_PROGRESS_CDP_POST_SPAWN_CLEANUP_FAILED: port=${port}; userDataDir=${
        userDataDir ?? "default"
      }; cause=${detail}`,
    );
    this.name = "CodexCdpPostSpawnCleanupError";
    this.port = port;
    this.userDataDir = userDataDir;
  }
}

export interface LaunchedCodexCdpProcess {
  readonly child: ChildProcess;
  readonly pid: number;
  readonly launchedAt: string;
  readonly args: readonly string[];
  readonly processStartedAt: string;
  readonly command: string;
}

export interface RestoreCodexCdpResult {
  readonly mainPid: number;
  readonly forced: boolean;
  readonly portClosed: boolean;
}

export interface CodexCdpLaunchServicesInvocation {
  readonly command: "/usr/bin/open";
  readonly args: readonly string[];
}

export type ProcessSignalSender = (pid: number, signal: NodeJS.Signals) => void;

export interface StopCodexCdpOptions {
  readonly runner?: CommandRunner;
  readonly signalProcess?: ProcessSignalSender;
  readonly timeoutMs?: number;
  readonly intervalMs?: number;
}

function validatePort(port: number): void {
  if (!Number.isInteger(port) || port < 1_024 || port > 65_535) {
    throw discoveryError("GOAL_PROGRESS_CDP_INVALID_PORT", String(port));
  }
}

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolveDelay) => setTimeout(resolveDelay, milliseconds));
}

export async function allocateRandomLoopbackPort(): Promise<number> {
  const server = createServer();
  return new Promise<number>((resolvePort, rejectPort) => {
    server.once("error", rejectPort);
    server.listen(0, LOOPBACK_ADDRESS, () => {
      const address = server.address();
      if (address === null || typeof address === "string") {
        server.close();
        rejectPort(discoveryError("GOAL_PROGRESS_CDP_PORT_ALLOCATION_FAILED"));
        return;
      }
      const port = address.port;
      server.close((error) => {
        if (error) {
          rejectPort(error);
          return;
        }
        resolvePort(port);
      });
    });
  });
}

function validateLaunchArgs(extraArgs: readonly string[]): void {
  const protectedPrefixes = [
    "--remote-debugging-address",
    "--remote-debugging-port",
    "--user-data-dir",
  ];
  const protectedArgument = extraArgs.find((argument) =>
    protectedPrefixes.some((prefix) => argument === prefix || argument.startsWith(`${prefix}=`)),
  );
  if (protectedArgument) {
    throw discoveryError("GOAL_PROGRESS_CDP_PROTECTED_LAUNCH_ARG", protectedArgument);
  }
}

export function createCodexCdpLaunchServicesInvocation(
  app: CodexMacosAppIdentity,
  args: readonly string[],
): CodexCdpLaunchServicesInvocation {
  return {
    command: "/usr/bin/open",
    args: ["-n", app.realAppPath, "--args", ...args],
  };
}

async function findCodexCdpMainProcess(
  app: CodexMacosAppIdentity,
  port: number,
  runner: CommandRunner,
): Promise<CodexCdpProcessSnapshot | null> {
  const result = await runner("/bin/ps", ["-axo", "pid=,command="]);
  if (result.exitCode !== 0) {
    throw discoveryError("GOAL_PROGRESS_CDP_PROCESS_LIST_FAILED", result.stderr);
  }
  const portArgument = `--remote-debugging-port=${port}`;
  const candidatePids = result.stdout.split(/\r?\n/u).flatMap((line) => {
    const match = /^\s*(\d+)\s+(.+)$/u.exec(line);
    const pid = Number(match?.[1]);
    const command = match?.[2]?.trim();
    return Number.isSafeInteger(pid) &&
      pid > 1 &&
      command &&
      commandBelongsToExecutable(command, app.realExecutablePath) &&
      command.split(/\s+/u).includes(portArgument)
      ? [pid]
      : [];
  });
  if (candidatePids.length > 1) {
    throw discoveryError(
      "GOAL_PROGRESS_CDP_MAIN_PROCESS_AMBIGUOUS",
      `count=${candidatePids.length}`,
    );
  }
  const pid = candidatePids[0];
  return pid === undefined ? null : inspectProcess(pid, runner);
}

async function waitForCodexCdpMainProcess(
  app: CodexMacosAppIdentity,
  port: number,
  runner: CommandRunner,
  timeoutMs: number,
): Promise<CodexCdpProcessSnapshot> {
  const timeoutAt = Date.now() + timeoutMs;
  let lastError: unknown;
  do {
    try {
      const process = await findCodexCdpMainProcess(app, port, runner);
      if (process) {
        return process;
      }
    } catch (error) {
      lastError = error;
    }
    await delay(50);
  } while (Date.now() < timeoutAt);
  throw discoveryError(
    "GOAL_PROGRESS_CDP_PROCESS_SNAPSHOT_TIMEOUT",
    lastError instanceof Error ? lastError.message : String(lastError ?? "not found"),
  );
}

export async function launchCodexWithCdp(
  app: CodexMacosAppIdentity,
  options: LaunchCodexCdpOptions,
): Promise<LaunchedCodexCdpProcess> {
  validatePort(options.port);
  const extraArgs = options.extraArgs ?? [];
  validateLaunchArgs(extraArgs);
  if (options.userDataDir !== undefined && !isAbsolute(options.userDataDir)) {
    throw discoveryError("GOAL_PROGRESS_CDP_USER_DATA_PATH_NOT_ABSOLUTE");
  }
  const args = [
    `--remote-debugging-address=${LOOPBACK_ADDRESS}`,
    `--remote-debugging-port=${options.port}`,
    ...(options.userDataDir === undefined
      ? []
      : [`--user-data-dir=${resolve(options.userDataDir)}`]),
    ...(options.headless ? ["--headless=new"] : []),
    "--no-first-run",
    ...extraArgs,
  ];
  const launchedAt = new Date().toISOString();
  const invocation = createCodexCdpLaunchServicesInvocation(app, args);
  const child =
    options.spawnProcess?.(invocation.command, invocation.args) ??
    spawn(invocation.command, invocation.args, {
      stdio: "ignore",
      detached: false,
      shell: false,
    });
  await new Promise<void>((resolveLaunch, rejectLaunch) => {
    child.once("spawn", resolveLaunch);
    child.once("error", rejectLaunch);
  });
  let processSnapshot: CodexCdpProcessSnapshot;
  try {
    processSnapshot = await waitForCodexCdpMainProcess(
      app,
      options.port,
      options.runner ?? runSystemCommand,
      options.processSnapshotTimeoutMs ?? PROCESS_LAUNCH_TIMEOUT_MS,
    );
  } catch (error) {
    const stopped = await stopUnidentifiedSpawnedChild(
      child,
      options.port,
      options.postSpawnCleanupTimeoutMs ?? 2_000,
      options.portOpenProbe ?? isLoopbackPortOpen,
    );
    if (!stopped) {
      throw new CodexCdpPostSpawnCleanupError(
        options.port,
        options.userDataDir,
        error instanceof Error ? error.message : String(error),
      );
    }
    throw error;
  }
  return {
    child,
    pid: processSnapshot.pid,
    launchedAt,
    args,
    processStartedAt: processSnapshot.startedAt,
    command: processSnapshot.command,
  };
}

export interface LaunchCodexNormallyOptions {
  readonly spawnProcess?: typeof spawn;
}

export async function launchCodexNormally(
  app: CodexMacosAppIdentity,
  options: LaunchCodexNormallyOptions = {},
): Promise<void> {
  const child = (options.spawnProcess ?? spawn)(app.realExecutablePath, [], {
    detached: true,
    shell: false,
    stdio: "ignore",
  });
  child.unref();
  await new Promise<void>((resolveLaunch, rejectLaunch) => {
    child.once("spawn", resolveLaunch);
    child.once("error", rejectLaunch);
  });
}

async function readProcessField(
  runner: CommandRunner,
  pid: number,
  field: "ppid" | "lstart" | "command",
): Promise<string> {
  const result = await runner("/bin/ps", ["-p", String(pid), "-o", `${field}=`]);
  return requireSuccessfulCommand(result, "GOAL_PROGRESS_CDP_PROCESS_LOOKUP_FAILED").trim();
}

export async function inspectProcess(
  pid: number,
  runner: CommandRunner = runSystemCommand,
): Promise<CodexCdpProcessSnapshot> {
  if (!Number.isSafeInteger(pid) || pid <= 1) {
    throw discoveryError("GOAL_PROGRESS_CDP_INVALID_PID", String(pid));
  }
  const [parentPidText, startedAt, command] = await Promise.all([
    readProcessField(runner, pid, "ppid"),
    readProcessField(runner, pid, "lstart"),
    readProcessField(runner, pid, "command"),
  ]);
  const parentPid = Number(parentPidText);
  if (!Number.isSafeInteger(parentPid) || parentPid < 0 || !startedAt || !command) {
    throw discoveryError("GOAL_PROGRESS_CDP_INVALID_PROCESS_SNAPSHOT");
  }
  return {
    pid,
    parentPid,
    startedAt,
    command,
  };
}

export async function listCodexMainProcesses(
  app: CodexMacosAppIdentity,
  runner: CommandRunner = runSystemCommand,
): Promise<readonly CodexCdpProcessSnapshot[]> {
  const result = await runner("/bin/ps", ["-axo", "pid=,command="]);
  if (result.exitCode !== 0) {
    throw discoveryError("GOAL_PROGRESS_CDP_PROCESS_LIST_FAILED", result.stderr);
  }
  const candidatePids = result.stdout.split(/\r?\n/u).flatMap((line) => {
    const match = /^\s*(\d+)\s+(.+)$/u.exec(line);
    const pid = Number(match?.[1]);
    const command = match?.[2]?.trim();
    return Number.isSafeInteger(pid) &&
      pid > 1 &&
      command &&
      commandBelongsToExecutable(command, app.realExecutablePath)
      ? [pid]
      : [];
  });
  const processes: CodexCdpProcessSnapshot[] = [];
  for (const pid of candidatePids) {
    try {
      const snapshot = await inspectProcess(pid, runner);
      if (commandBelongsToExecutable(snapshot.command, app.realExecutablePath)) {
        processes.push(snapshot);
      }
    } catch {
      // The process exited after the process list was captured.
    }
  }
  return processes;
}

function childHasExited(child: ChildProcess): boolean {
  return child.exitCode !== null || child.signalCode !== null;
}

async function waitForChildExit(child: ChildProcess, timeoutMs: number): Promise<boolean> {
  if (childHasExited(child)) {
    return true;
  }
  return new Promise<boolean>((resolveExit) => {
    const onExit = () => {
      clearTimeout(timeout);
      resolveExit(true);
    };
    const timeout = setTimeout(() => {
      child.off("exit", onExit);
      resolveExit(childHasExited(child));
    }, timeoutMs);
    child.once("exit", onExit);
  });
}

async function stopUnidentifiedSpawnedChild(
  child: ChildProcess,
  port: number,
  timeoutMs: number,
  portOpenProbe: (port: number) => Promise<boolean>,
): Promise<boolean> {
  if (!childHasExited(child)) {
    child.kill("SIGTERM");
    if (!(await waitForChildExit(child, timeoutMs)) && !childHasExited(child)) {
      child.kill("SIGKILL");
    }
  }
  if (!(await waitForChildExit(child, timeoutMs))) {
    return false;
  }
  return waitForPortClosed(port, timeoutMs, portOpenProbe);
}

function parseLsofListeners(output: string): readonly CodexCdpListener[] {
  const listeners: CodexCdpListener[] = [];
  let pid: number | undefined;
  let commandName = "";
  for (const line of output.split(/\r?\n/u)) {
    const field = line[0];
    const value = line.slice(1);
    if (field === "p") {
      pid = Number(value);
      commandName = "";
    } else if (field === "c") {
      commandName = value;
    } else if (field === "n" && pid !== undefined && Number.isSafeInteger(pid) && pid > 1) {
      listeners.push({
        pid,
        commandName,
        address: value,
      });
    }
  }
  return listeners;
}

async function isProcessDescendant(
  pid: number,
  ancestorPid: number,
  runner: CommandRunner,
): Promise<boolean> {
  let currentPid = pid;
  const visited = new Set<number>();
  for (let depth = 0; depth < PROCESS_LOOKUP_LIMIT; depth += 1) {
    if (currentPid === ancestorPid) {
      return true;
    }
    if (currentPid <= 1 || visited.has(currentPid)) {
      return false;
    }
    visited.add(currentPid);
    try {
      const snapshot = await inspectProcess(currentPid, runner);
      currentPid = snapshot.parentPid;
    } catch {
      return false;
    }
  }
  return false;
}

export async function verifyCodexCdpListenerOwnership(
  app: CodexMacosAppIdentity,
  mainPid: number,
  port: number,
  runner: CommandRunner = runSystemCommand,
): Promise<CodexCdpListenerOwnership> {
  validatePort(port);
  const mainProcess = await inspectProcess(mainPid, runner);
  if (!commandBelongsToExecutable(mainProcess.command, app.realExecutablePath)) {
    throw discoveryError("GOAL_PROGRESS_CDP_MAIN_EXECUTABLE_MISMATCH");
  }
  const lsofResult = await runner("/usr/sbin/lsof", [
    "-nP",
    `-iTCP:${port}`,
    "-sTCP:LISTEN",
    "-Fpctn",
  ]);
  const listeners = parseLsofListeners(
    requireSuccessfulCommand(lsofResult, "GOAL_PROGRESS_CDP_LISTENER_NOT_FOUND"),
  );
  if (listeners.length === 0) {
    throw discoveryError("GOAL_PROGRESS_CDP_LISTENER_NOT_FOUND");
  }
  const expectedAddress = `${LOOPBACK_ADDRESS}:${port}`;
  if (listeners.some((listener) => listener.address !== expectedAddress)) {
    throw discoveryError(
      "GOAL_PROGRESS_CDP_NON_LOOPBACK_LISTENER",
      listeners.map((listener) => listener.address).join(","),
    );
  }
  const listenerPids = [...new Set(listeners.map((listener) => listener.pid))];
  for (const listenerPid of listenerPids) {
    if (!(await isProcessDescendant(listenerPid, mainPid, runner))) {
      throw discoveryError("GOAL_PROGRESS_CDP_LISTENER_PROCESS_MISMATCH", String(listenerPid));
    }
  }
  return {
    mainProcess,
    listeners,
    listenerPids,
  };
}

export function commandBelongsToExecutable(command: string, executablePath: string): boolean {
  return command === executablePath || command.startsWith(`${executablePath} `);
}

export async function waitForCodexCdpListenerOwnership(
  app: CodexMacosAppIdentity,
  mainPid: number,
  port: number,
  options: {
    readonly runner?: CommandRunner;
    readonly timeoutMs?: number;
    readonly intervalMs?: number;
  } = {},
): Promise<CodexCdpListenerOwnership> {
  const runner = options.runner ?? runSystemCommand;
  const timeoutAt = Date.now() + (options.timeoutMs ?? 30_000);
  let lastError: unknown;
  do {
    try {
      return await verifyCodexCdpListenerOwnership(app, mainPid, port, runner);
    } catch (error) {
      lastError = error;
      await delay(options.intervalMs ?? 250);
    }
  } while (Date.now() < timeoutAt);
  throw discoveryError(
    "GOAL_PROGRESS_CDP_LISTENER_TIMEOUT",
    lastError instanceof Error ? lastError.message : String(lastError),
  );
}

function validateRuntimeState(state: CodexCdpRuntimeState): void {
  validatePort(state.port);
  if (
    state.schemaVersion !== 1 ||
    state.address !== LOOPBACK_ADDRESS ||
    state.bundleId !== CODEX_BUNDLE_ID ||
    state.teamId !== CODEX_TEAM_ID ||
    !state.launchId ||
    !state.launchedAt ||
    !state.processStartedAt ||
    !isAbsolute(state.executablePath) ||
    !isAbsolute(state.appPath) ||
    !Number.isSafeInteger(state.mainPid) ||
    state.mainPid <= 1 ||
    state.listenerPids.length === 0
  ) {
    throw discoveryError("GOAL_PROGRESS_CDP_INVALID_RUNTIME_STATE");
  }
}

export async function readCodexCdpRuntimeState(statePath: string): Promise<CodexCdpRuntimeState> {
  if (!isAbsolute(statePath)) {
    throw discoveryError("GOAL_PROGRESS_CDP_STATE_PATH_NOT_ABSOLUTE");
  }
  const metadata = await stat(statePath);
  if (!metadata.isFile() || (metadata.mode & 0o777) !== 0o600) {
    throw discoveryError("GOAL_PROGRESS_CDP_RUNTIME_STATE_PERMISSION_INVALID");
  }
  let state: CodexCdpRuntimeState;
  try {
    state = JSON.parse(await readFile(statePath, "utf8")) as CodexCdpRuntimeState;
  } catch {
    throw discoveryError("GOAL_PROGRESS_CDP_INVALID_RUNTIME_STATE");
  }
  validateRuntimeState(state);
  return state;
}

export async function writeCodexCdpRuntimeState(
  statePath: string,
  state: CodexCdpRuntimeState,
): Promise<void> {
  if (!isAbsolute(statePath)) {
    throw discoveryError("GOAL_PROGRESS_CDP_STATE_PATH_NOT_ABSOLUTE");
  }
  validateRuntimeState(state);
  await mkdir(dirname(statePath), { recursive: true });
  const temporaryPath = `${statePath}.${process.pid}.${randomUUID()}.tmp`;
  try {
    await writeFile(temporaryPath, `${JSON.stringify(state, null, 2)}\n`, {
      encoding: "utf8",
      flag: "wx",
      mode: 0o600,
    });
    await rename(temporaryPath, statePath);
    await chmod(statePath, 0o600);
  } finally {
    await unlink(temporaryPath).catch(() => undefined);
  }
}

export function createCodexCdpRuntimeState(
  app: CodexMacosAppIdentity,
  launched: LaunchedCodexCdpProcess,
  ownership: CodexCdpListenerOwnership,
  port: number,
): CodexCdpRuntimeState {
  if (
    ownership.mainProcess.pid !== launched.pid ||
    ownership.mainProcess.startedAt !== launched.processStartedAt ||
    ownership.mainProcess.command !== launched.command
  ) {
    throw discoveryError("GOAL_PROGRESS_CDP_LAUNCH_IDENTITY_CHANGED");
  }
  return {
    schemaVersion: 1,
    launchId: randomUUID(),
    address: LOOPBACK_ADDRESS,
    port,
    mainPid: launched.pid,
    launchedAt: launched.launchedAt,
    processStartedAt: launched.processStartedAt,
    executablePath: app.realExecutablePath,
    appPath: app.realAppPath,
    bundleId: CODEX_BUNDLE_ID,
    teamId: CODEX_TEAM_ID,
    command: launched.command,
    listenerPids: ownership.listenerPids,
  };
}

interface ProtectedProcessIdentity {
  readonly mainPid: number;
  readonly processStartedAt: string;
  readonly command: string;
  readonly executablePath: string;
  readonly port: number;
}

async function processIdentityMatches(
  identity: ProtectedProcessIdentity,
  runner: CommandRunner,
): Promise<boolean> {
  try {
    const snapshot = await inspectProcess(identity.mainPid, runner);
    return (
      snapshot.startedAt === identity.processStartedAt &&
      snapshot.command === identity.command &&
      (snapshot.command === identity.executablePath ||
        snapshot.command.startsWith(`${identity.executablePath} `))
    );
  } catch {
    return false;
  }
}

async function waitForOriginalProcessExit(
  identity: ProtectedProcessIdentity,
  runner: CommandRunner,
  timeoutMs: number,
  intervalMs: number,
): Promise<boolean> {
  const timeoutAt = Date.now() + timeoutMs;
  while (Date.now() < timeoutAt) {
    if (!(await processIdentityMatches(identity, runner))) {
      return true;
    }
    await delay(intervalMs);
  }
  return !(await processIdentityMatches(identity, runner));
}

async function isLoopbackPortOpen(port: number): Promise<boolean> {
  return new Promise<boolean>((resolveOpen) => {
    const socket = new Socket();
    const finish = (isOpen: boolean) => {
      socket.destroy();
      resolveOpen(isOpen);
    };
    socket.setTimeout(250);
    socket.once("connect", () => finish(true));
    socket.once("timeout", () => finish(false));
    socket.once("error", () => finish(false));
    socket.connect(port, LOOPBACK_ADDRESS);
  });
}

async function waitForPortClosed(
  port: number,
  timeoutMs: number,
  portOpenProbe: (port: number) => Promise<boolean> = isLoopbackPortOpen,
): Promise<boolean> {
  const timeoutAt = Date.now() + timeoutMs;
  while (Date.now() < timeoutAt) {
    if (!(await portOpenProbe(port))) {
      return true;
    }
    await delay(100);
  }
  return !(await portOpenProbe(port));
}

async function stopProtectedCodexProcess(
  identity: ProtectedProcessIdentity,
  options: StopCodexCdpOptions,
): Promise<RestoreCodexCdpResult> {
  const runner = options.runner ?? runSystemCommand;
  const signalProcess = options.signalProcess ?? process.kill.bind(process);
  const timeoutMs = options.timeoutMs ?? PROCESS_STOP_TIMEOUT_MS;
  const intervalMs = options.intervalMs ?? 100;
  if (await processIdentityMatches(identity, runner)) {
    signalProcess(identity.mainPid, "SIGTERM");
  }
  let forced = false;
  if (!(await waitForOriginalProcessExit(identity, runner, timeoutMs, intervalMs))) {
    if (await processIdentityMatches(identity, runner)) {
      forced = true;
      signalProcess(identity.mainPid, "SIGKILL");
    }
    if (!(await waitForOriginalProcessExit(identity, runner, timeoutMs, intervalMs))) {
      throw discoveryError("GOAL_PROGRESS_CDP_RUNTIME_STOP_FAILED");
    }
  }
  const portClosed = await waitForPortClosed(identity.port, timeoutMs);
  if (!portClosed) {
    throw discoveryError("GOAL_PROGRESS_CDP_PORT_STILL_OPEN");
  }
  return {
    mainPid: identity.mainPid,
    forced,
    portClosed,
  };
}

export async function stopLaunchedCodexCdpProcess(
  app: CodexMacosAppIdentity,
  launched: LaunchedCodexCdpProcess,
  port: number,
  options: StopCodexCdpOptions = {},
): Promise<RestoreCodexCdpResult> {
  validatePort(port);
  return stopProtectedCodexProcess(
    {
      mainPid: launched.pid,
      processStartedAt: launched.processStartedAt,
      command: launched.command,
      executablePath: app.realExecutablePath,
      port,
    },
    options,
  );
}

export async function stopCodexCdpRuntime(
  state: CodexCdpRuntimeState,
  options: StopCodexCdpOptions = {},
): Promise<RestoreCodexCdpResult> {
  validateRuntimeState(state);
  return stopProtectedCodexProcess(
    {
      mainPid: state.mainPid,
      processStartedAt: state.processStartedAt,
      command: state.command,
      executablePath: state.executablePath,
      port: state.port,
    },
    options,
  );
}
