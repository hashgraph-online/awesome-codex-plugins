import { spawnSync } from "node:child_process";
import { stat, unlink } from "node:fs/promises";
import { isAbsolute, resolve } from "node:path";
import { isSea } from "node:sea";
import {
  atomicWriteFile,
  ensurePrivateDirectory,
  resolveGoalProgressPaths,
} from "../../../packages/store/src/index.js";
import {
  inspectCodexMacosApp,
  requireSingleCodexMacosApp,
  runSystemCommand,
} from "./app-discovery.js";
import {
  allocateRandomLoopbackPort,
  commandBelongsToExecutable,
  createCodexCdpRuntimeState,
  inspectProcess,
  launchCodexWithCdp,
  readCodexCdpRuntimeState,
  stopCodexCdpRuntime,
  stopLaunchedCodexCdpProcess,
  verifyCodexCdpListenerOwnership,
  waitForCodexCdpListenerOwnership,
  writeCodexCdpRuntimeState,
} from "./cdp-runtime.js";
import { GOAL_PROGRESS_LAUNCH_AGENT_LABEL } from "./install-layout.js";
import { restartLoadedLaunchAgent } from "./launch-agent-controller.js";
import { isNotFound, stableErrorCode } from "./macos-errors.js";

export interface CdpController {
  ensure(restartCodex: boolean): Promise<boolean>;
  verify(): Promise<boolean>;
  rollback?(): Promise<void>;
}

export interface RestoreCdpResult {
  readonly changed: boolean;
  readonly scheduled: boolean;
  readonly restartedCodex: boolean;
}

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolveDelay) => setTimeout(resolveDelay, milliseconds));
}

export const GOAL_PROGRESS_CDP_HANDOFF_COMMAND = "__cdp-handoff";
export const GOAL_PROGRESS_CDP_SCHEDULE_COMMAND = "__cdp-schedule";
export const GOAL_PROGRESS_RESTORE_HANDOFF_COMMAND = "__restore-handoff";
const GOAL_PROGRESS_LEGACY_CDP_HANDOFF_LABEL = "com.codexgoalprogress.cdp-handoff";
const GOAL_PROGRESS_LEGACY_RESTORE_HANDOFF_LABEL = "com.codexgoalprogress.restore-handoff";
export const GOAL_PROGRESS_CDP_HANDOFF_LABEL = "com.codexgoalprogress.cdp-handoff-v2";
export const GOAL_PROGRESS_RESTORE_HANDOFF_LABEL = "com.codexgoalprogress.restore-handoff-v2";

function cdpPaths(homeDirectory: string, configuredRoot = process.env.GOAL_PROGRESS_ROOT) {
  const root = configuredRoot?.trim();
  return resolveGoalProgressPaths(
    root
      ? { root: resolve(root) }
      : {
          platform: "darwin",
          homeDirectory,
        },
  );
}

export function decideCodexCdpRestart(input: {
  readonly cdpReady: boolean;
  readonly restartRequested: boolean;
  readonly handoffProcess: boolean;
}): "skip" | "schedule" | "run" {
  if (!input.restartRequested || (input.cdpReady && !input.handoffProcess)) {
    return "skip";
  }
  return input.handoffProcess ? "run" : "schedule";
}

export function createCodexNormalRelaunchInvocation(appPath: string) {
  return {
    command: "/usr/bin/open",
    args: ["-n", appPath],
  };
}

async function reopenCodexNormally(appPath: string): Promise<void> {
  const invocation = createCodexNormalRelaunchInvocation(appPath);
  const result = spawnSync(invocation.command, invocation.args, {
    encoding: "utf8",
    maxBuffer: 1024 * 1024,
  });
  if (result.status !== 0) {
    throw new Error("GOAL_PROGRESS_CODEX_FALLBACK_RESTART_FAILED");
  }
}

export async function runCdpRestartWithFallback<Value>(
  run: () => Promise<Value>,
  reopen?: () => Promise<void>,
): Promise<Value> {
  try {
    return await run();
  } catch (error) {
    if (reopen) {
      try {
        await reopen();
      } catch (reopenError) {
        throw new Error(
          `GOAL_PROGRESS_CODEX_FALLBACK_RESTART_FAILED: original=${stableErrorCode(
            error,
          )}; fallback=${stableErrorCode(reopenError)}`,
        );
      }
    }
    throw error;
  }
}

export async function recordCdpHandoffFailure(
  homeDirectory: string,
  error: unknown,
  observedAt = new Date(),
  configuredRoot = process.env.GOAL_PROGRESS_ROOT,
): Promise<void> {
  const candidate = stableErrorCode(error);
  const code = /^([A-Z][A-Z0-9_]{2,127})/u.exec(candidate)?.[1] ?? "CDP_HANDOFF_FAILED";
  const paths = cdpPaths(homeDirectory, configuredRoot);
  await ensurePrivateDirectory(paths.logsRoot);
  await atomicWriteFile(
    resolve(paths.logsRoot, "cdp-handoff-error.json"),
    `${JSON.stringify(
      {
        schemaVersion: 1,
        observedAt: observedAt.toISOString(),
        code,
      },
      null,
      2,
    )}\n`,
  );
}

interface CreateCodexCdpHandoffInvocationInput {
  readonly execPath: string;
  readonly argvEntry: string;
  readonly execArgv: readonly string[];
  readonly environment: NodeJS.ProcessEnv;
  readonly sea?: boolean;
}

function currentHandoffInvocationInput(): CreateCodexCdpHandoffInvocationInput {
  const sourceLauncher = process.env.GOAL_PROGRESS_SOURCE_LAUNCHER?.trim();
  if (sourceLauncher && isAbsolute(sourceLauncher)) {
    return {
      execPath: sourceLauncher,
      argvEntry: sourceLauncher,
      execArgv: [],
      environment: process.env,
      sea: true,
    };
  }
  return {
    execPath: process.execPath,
    argvEntry: process.argv[1] ?? process.execPath,
    execArgv: process.execArgv,
    environment: process.env,
    sea: isSea(),
  };
}

function handoffProgramArgs(
  input: CreateCodexCdpHandoffInvocationInput,
  command: string,
): readonly string[] {
  return (input.sea ?? input.argvEntry === input.execPath)
    ? [input.execPath, command]
    : [input.execPath, ...input.execArgv, input.argvEntry, command];
}

function createLaunchctlHandoffInvocation(
  input: CreateCodexCdpHandoffInvocationInput,
  label: string,
  command: string,
  environment: Readonly<Record<string, string>>,
) {
  const homeDirectory = input.environment.HOME;
  if (!homeDirectory) {
    throw new Error("GOAL_PROGRESS_HOME_DIRECTORY_MISSING");
  }
  return {
    label,
    command: "/bin/launchctl",
    removeArgs: ["remove", label],
    args: [
      "submit",
      "-l",
      label,
      "--",
      "/usr/bin/env",
      `HOME=${homeDirectory}`,
      ...Object.entries(environment).map(([key, value]) => `${key}=${value}`),
      ...handoffProgramArgs(input, command),
    ],
    options: {
      shell: false as const,
      stdio: "ignore" as const,
      env: input.environment,
    },
  };
}

export function createCodexCdpHandoffInvocation(input: CreateCodexCdpHandoffInvocationInput) {
  return createLaunchctlHandoffInvocation(
    input,
    GOAL_PROGRESS_CDP_HANDOFF_LABEL,
    GOAL_PROGRESS_CDP_HANDOFF_COMMAND,
    {
      GOAL_PROGRESS_INTERNAL_CDP_HANDOFF: "1",
      ...(input.environment.GOAL_PROGRESS_ROOT
        ? { GOAL_PROGRESS_ROOT: input.environment.GOAL_PROGRESS_ROOT }
        : {}),
    },
  );
}

interface CreateCodexRestoreHandoffInvocationInput extends CreateCodexCdpHandoffInvocationInput {
  readonly restartCodex: boolean;
}

export function createCodexRestoreHandoffInvocation(
  input: CreateCodexRestoreHandoffInvocationInput,
) {
  return createLaunchctlHandoffInvocation(
    input,
    GOAL_PROGRESS_RESTORE_HANDOFF_LABEL,
    GOAL_PROGRESS_RESTORE_HANDOFF_COMMAND,
    {
      GOAL_PROGRESS_INTERNAL_RESTORE_HANDOFF: "1",
      GOAL_PROGRESS_RESTORE_RESTART_CODEX: input.restartCodex ? "1" : "0",
      ...(input.environment.GOAL_PROGRESS_ROOT
        ? { GOAL_PROGRESS_ROOT: input.environment.GOAL_PROGRESS_ROOT }
        : {}),
    },
  );
}

function submitCodexHandoff(invocation: ReturnType<typeof createCodexCdpHandoffInvocation>): void {
  spawnSync(invocation.command, invocation.removeArgs, invocation.options);
  const submitted = spawnSync(invocation.command, invocation.args, invocation.options);
  if (submitted.status !== 0) {
    throw new Error("GOAL_PROGRESS_CODEX_HANDOFF_SUBMIT_FAILED");
  }
}

function removeSubmittedHandoffJobs(currentLabel: string): void {
  for (const label of [
    GOAL_PROGRESS_LEGACY_CDP_HANDOFF_LABEL,
    GOAL_PROGRESS_LEGACY_RESTORE_HANDOFF_LABEL,
    currentLabel,
  ]) {
    spawnSync("/bin/launchctl", ["remove", label], {
      encoding: "utf8",
      maxBuffer: 1024 * 1024,
    });
  }
}

export async function scheduleCodexCdpHandoff(): Promise<void> {
  const invocation = createCodexCdpHandoffInvocation(currentHandoffInvocationInput());
  submitCodexHandoff(invocation);
}

async function scheduleCodexRestoreHandoff(restartCodex: boolean): Promise<void> {
  const invocation = createCodexRestoreHandoffInvocation({
    ...currentHandoffInvocationInput(),
    restartCodex,
  });
  submitCodexHandoff(invocation);
}

export async function runCodexCdpHandoff(homeDirectory: string): Promise<void> {
  if (process.env.GOAL_PROGRESS_INTERNAL_CDP_HANDOFF !== "1") {
    throw new Error("GOAL_PROGRESS_CDP_HANDOFF_UNAUTHORIZED");
  }
  await delay(750);
  const controller = createCdpController(homeDirectory);
  try {
    await controller.ensure(true);
    if (!(await controller.verify())) {
      throw new Error("GOAL_PROGRESS_CDP_HANDOFF_VERIFY_FAILED");
    }
  } catch (error) {
    await recordCdpHandoffFailure(homeDirectory, error).catch(() => undefined);
    throw error;
  } finally {
    removeSubmittedHandoffJobs(GOAL_PROGRESS_CDP_HANDOFF_LABEL);
  }
}

export function createCdpController(
  homeDirectory: string,
  configuredRoot = process.env.GOAL_PROGRESS_ROOT,
): CdpController {
  const paths = cdpPaths(homeDirectory, configuredRoot);

  const verify = async (): Promise<boolean> => {
    let state: Awaited<ReturnType<typeof readCodexCdpRuntimeState>>;
    try {
      state = await readCodexCdpRuntimeState(paths.cdpRuntimePath);
    } catch (error) {
      if (isNotFound(error)) {
        return false;
      }
      throw error;
    }
    const app = await inspectCodexMacosApp(state.appPath);
    if (
      app.realExecutablePath !== state.executablePath ||
      app.bundleId !== state.bundleId ||
      app.teamId !== state.teamId
    ) {
      throw new Error("GOAL_PROGRESS_CDP_RUNTIME_APP_MISMATCH");
    }
    try {
      await verifyCodexCdpListenerOwnership(app, state.mainPid, state.port);
      const { discoverCodexCdp } = await import("../../../packages/codex-adapter/src/cdp.js");
      await discoverCodexCdp(state.port);
      return true;
    } catch {
      return false;
    }
  };

  return {
    verify,
    async rollback() {
      await restoreCdpInstallation(homeDirectory, true, false);
    },
    async ensure(restartCodex) {
      const decision = decideCodexCdpRestart({
        cdpReady: await verify(),
        restartRequested: restartCodex,
        handoffProcess: process.env.GOAL_PROGRESS_INTERNAL_CDP_HANDOFF === "1",
      });
      if (decision === "skip") {
        return false;
      }
      if (decision === "schedule") {
        await scheduleCodexCdpHandoff();
        return true;
      }
      const app = await requireSingleCodexMacosApp();
      const processList = await runSystemCommand("/bin/ps", ["-axo", "pid=,command="]);
      if (processList.exitCode !== 0) {
        throw new Error("GOAL_PROGRESS_CODEX_PROCESS_LIST_FAILED");
      }
      const running: Array<Awaited<ReturnType<typeof inspectProcess>>> = [];
      for (const line of processList.stdout.split(/\r?\n/u)) {
        const match = /^\s*(\d+)\s+(.+)$/u.exec(line);
        const pid = Number(match?.[1]);
        if (
          Number.isSafeInteger(pid) &&
          pid > 1 &&
          match?.[2] &&
          commandBelongsToExecutable(match[2].trim(), app.realExecutablePath)
        ) {
          running.push(await inspectProcess(pid));
        }
      }
      if (running.length > 1) {
        throw new Error(`GOAL_PROGRESS_CODEX_MAIN_PROCESS_AMBIGUOUS: count=${running.length}`);
      }
      const original = running[0];
      if (original) {
        process.kill(original.pid, "SIGTERM");
        const timeoutAt = Date.now() + 15_000;
        while (Date.now() < timeoutAt) {
          try {
            const current = await inspectProcess(original.pid);
            if (current.startedAt !== original.startedAt) {
              break;
            }
          } catch {
            break;
          }
          await delay(100);
        }
        try {
          const current = await inspectProcess(original.pid);
          if (current.startedAt === original.startedAt) {
            throw new Error("GOAL_PROGRESS_CODEX_CURRENT_PROCESS_STOP_TIMEOUT");
          }
        } catch (error) {
          if (
            error instanceof Error &&
            error.message === "GOAL_PROGRESS_CODEX_CURRENT_PROCESS_STOP_TIMEOUT"
          ) {
            throw error;
          }
        }
      }
      return runCdpRestartWithFallback(
        async () => {
          const appMetadataBefore = await stat(app.realAppPath);
          const port = await allocateRandomLoopbackPort();
          let launched: Awaited<ReturnType<typeof launchCodexWithCdp>> | undefined;
          try {
            launched = await launchCodexWithCdp(app, { port });
            const ownership = await waitForCodexCdpListenerOwnership(app, launched.pid, port);
            const state = createCodexCdpRuntimeState(app, launched, ownership, port);
            await writeCodexCdpRuntimeState(paths.cdpRuntimePath, state);
            const appMetadataAfter = await stat(app.realAppPath);
            if (
              appMetadataAfter.mtimeMs !== appMetadataBefore.mtimeMs ||
              appMetadataAfter.size !== appMetadataBefore.size
            ) {
              throw new Error("GOAL_PROGRESS_CODEX_APP_MODIFIED");
            }
            launched.child.unref();
            restartLoadedLaunchAgent(GOAL_PROGRESS_LAUNCH_AGENT_LABEL);
            return true;
          } catch (error) {
            if (launched) {
              await stopLaunchedCodexCdpProcess(app, launched, port).catch(() => undefined);
            }
            throw error;
          }
        },
        original ? () => reopenCodexNormally(app.realAppPath) : undefined,
      );
    },
  };
}

async function restoreCdpInstallation(
  homeDirectory: string,
  restartCodex: boolean,
  allowSchedule: boolean,
): Promise<RestoreCdpResult> {
  const paths = cdpPaths(homeDirectory);
  let state: Awaited<ReturnType<typeof readCodexCdpRuntimeState>>;
  try {
    state = await readCodexCdpRuntimeState(paths.cdpRuntimePath);
  } catch (error) {
    if (isNotFound(error)) {
      return { changed: false, scheduled: false, restartedCodex: false };
    }
    throw error;
  }
  if (allowSchedule && process.env.GOAL_PROGRESS_INTERNAL_RESTORE_HANDOFF !== "1") {
    await scheduleCodexRestoreHandoff(restartCodex);
    return { changed: true, scheduled: true, restartedCodex: false };
  }
  const app = await inspectCodexMacosApp(state.appPath);
  if (
    app.realExecutablePath !== state.executablePath ||
    app.bundleId !== state.bundleId ||
    app.teamId !== state.teamId
  ) {
    throw new Error("GOAL_PROGRESS_CDP_RUNTIME_APP_MISMATCH");
  }
  await stopCodexCdpRuntime(state);
  await unlink(paths.cdpRuntimePath);
  if (restartCodex) {
    const opened = spawnSync("/usr/bin/open", [app.realAppPath], {
      encoding: "utf8",
      maxBuffer: 1024 * 1024,
    });
    if (opened.status !== 0) {
      throw new Error("GOAL_PROGRESS_CODEX_RESTART_FAILED");
    }
  }
  return {
    changed: true,
    scheduled: false,
    restartedCodex: restartCodex,
  };
}

export function createDefaultRestoreCdp(homeDirectory: string) {
  return (restartCodex: boolean): Promise<RestoreCdpResult> =>
    restoreCdpInstallation(homeDirectory, restartCodex, true);
}

export async function runCodexRestoreHandoff(homeDirectory: string): Promise<void> {
  if (process.env.GOAL_PROGRESS_INTERNAL_RESTORE_HANDOFF !== "1") {
    throw new Error("GOAL_PROGRESS_RESTORE_HANDOFF_UNAUTHORIZED");
  }
  await delay(750);
  try {
    const result = await createDefaultRestoreCdp(homeDirectory)(
      process.env.GOAL_PROGRESS_RESTORE_RESTART_CODEX === "1",
    );
    if (!result.changed || result.scheduled) {
      throw new Error("GOAL_PROGRESS_RESTORE_HANDOFF_FAILED");
    }
  } finally {
    removeSubmittedHandoffJobs(GOAL_PROGRESS_RESTORE_HANDOFF_LABEL);
  }
}
