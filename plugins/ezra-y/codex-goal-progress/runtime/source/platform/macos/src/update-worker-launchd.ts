import { spawnSync } from "node:child_process";
import { rm } from "node:fs/promises";
import { isAbsolute, resolve } from "node:path";
import { isSea } from "node:sea";
import { atomicWriteFile } from "../../../packages/store/src/index.js";
import { launchDomain, launchdPlist } from "./launch-agent-controller.js";

export interface UpdateWorkerLaunchctlInvocation {
  readonly label: string;
  readonly command: "/bin/launchctl";
  readonly args: readonly string[];
  readonly removeArgs: readonly string[];
  readonly plistPath: string;
  readonly plist: string;
  readonly options: {
    readonly shell: false;
    readonly stdio: "ignore";
    readonly env: Readonly<Record<string, string>>;
  };
}

export type UpdateWorkerLaunchctlRunner = (
  command: string,
  args: readonly string[],
  options: UpdateWorkerLaunchctlInvocation["options"],
) => { readonly status: number | null };

export const GOAL_PROGRESS_UPDATE_WORKER_NOTIFY_DELAYS_MS = [0, 250, 750] as const;

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolveDelay) => setTimeout(resolveDelay, milliseconds));
}

export async function notifyUpdateWorkerResult(
  send: () => Promise<void>,
  delaysMs: readonly number[] = GOAL_PROGRESS_UPDATE_WORKER_NOTIFY_DELAYS_MS,
): Promise<boolean> {
  for (const delayMs of delaysMs) {
    if (delayMs > 0) {
      await delay(delayMs);
    }
    try {
      await send();
      return true;
    } catch {
      // A later bounded attempt may reach the replacement Helper.
    }
  }
  return false;
}

export interface CreateUpdateWorkerInvocationInput {
  readonly execPath: string;
  readonly argvEntry: string;
  readonly execArgv: readonly string[];
  readonly environment: Readonly<Record<string, string | undefined>>;
  readonly operationId: string;
  readonly sea?: boolean;
}

export interface CreateOneShotUpdateWorkerInvocationInput {
  readonly label: string;
  readonly plistPath: string;
  readonly programArguments: readonly string[];
  readonly environment: Readonly<Record<string, string>>;
}

function programArguments(
  input: CreateUpdateWorkerInvocationInput,
  internalCommand: string,
): readonly string[] {
  return (input.sea ?? input.argvEntry === input.execPath)
    ? [input.execPath, internalCommand]
    : [input.execPath, ...input.execArgv, input.argvEntry, internalCommand];
}

export function createUpdateWorkerInvocation(
  input: CreateUpdateWorkerInvocationInput,
  kind: "install" | "restart",
): UpdateWorkerLaunchctlInvocation {
  const homeDirectory = input.environment.HOME;
  const root = input.environment.GOAL_PROGRESS_ROOT;
  if (!homeDirectory || !root) {
    throw new Error("GOAL_PROGRESS_UPDATE_WORKER_ENVIRONMENT_INVALID");
  }
  const internalCommand =
    kind === "install" ? "__update-install-handoff" : "__update-restart-handoff";
  const internalFlag =
    kind === "install"
      ? "GOAL_PROGRESS_INTERNAL_UPDATE_INSTALL"
      : "GOAL_PROGRESS_INTERNAL_UPDATE_RESTART";
  const environment = {
    HOME: homeDirectory,
    GOAL_PROGRESS_ROOT: root,
    [internalFlag]: "1",
    GOAL_PROGRESS_UPDATE_OPERATION_ID: input.operationId,
  };
  const label = `com.codexgoalprogress.update-${kind}.${input.operationId}`;
  const plistPath = resolve(root, "runtime", "update-workers", `${label}.plist`);
  const invocation = createOneShotUpdateWorkerInvocation({
    label,
    plistPath,
    programArguments: programArguments(input, internalCommand),
    environment,
  });
  return invocation;
}

export function createOneShotUpdateWorkerInvocation(
  input: CreateOneShotUpdateWorkerInvocationInput,
): UpdateWorkerLaunchctlInvocation {
  const domain = launchDomain();
  return {
    label: input.label,
    command: "/bin/launchctl",
    args: ["bootstrap", domain, input.plistPath],
    removeArgs: ["bootout", `${domain}/${input.label}`],
    plistPath: input.plistPath,
    plist: launchdPlist({
      label: input.label,
      programArguments: input.programArguments,
      environment: input.environment,
      runAtLoad: true,
      keepAlive: false,
    }),
    options: {
      shell: false,
      stdio: "ignore",
      env: input.environment,
    },
  };
}

export async function submitUpdateWorker(
  invocation: UpdateWorkerLaunchctlInvocation,
  runner: UpdateWorkerLaunchctlRunner = (command, args, options) =>
    spawnSync(command, [...args], options),
): Promise<void> {
  await atomicWriteFile(invocation.plistPath, invocation.plist);
  const result = runner(invocation.command, invocation.args, invocation.options);
  if (result.status !== 0) {
    await rm(invocation.plistPath, { force: true });
    throw new Error(
      invocation.label.includes("update-install")
        ? "GOAL_PROGRESS_UPDATE_INSTALL_SUBMIT_FAILED"
        : "GOAL_PROGRESS_UPDATE_RESTART_SUBMIT_FAILED",
    );
  }
}

export async function removeUpdateWorker(
  invocation: UpdateWorkerLaunchctlInvocation,
  runner: UpdateWorkerLaunchctlRunner = (command, args, options) =>
    spawnSync(command, [...args], options),
): Promise<void> {
  await rm(invocation.plistPath, { force: true });
  runner(invocation.command, invocation.removeArgs, invocation.options);
}

export function currentUpdateWorkerInvocationInput(
  operationId: string,
): CreateUpdateWorkerInvocationInput {
  const sourceLauncher = process.env.GOAL_PROGRESS_SOURCE_LAUNCHER?.trim();
  if (sourceLauncher && isAbsolute(sourceLauncher)) {
    return {
      execPath: sourceLauncher,
      argvEntry: sourceLauncher,
      execArgv: [],
      environment: process.env,
      operationId,
      sea: true,
    };
  }
  return {
    execPath: process.execPath,
    argvEntry: process.argv[1] ?? process.execPath,
    execArgv: process.execArgv,
    environment: process.env,
    operationId,
    sea: isSea(),
  };
}
