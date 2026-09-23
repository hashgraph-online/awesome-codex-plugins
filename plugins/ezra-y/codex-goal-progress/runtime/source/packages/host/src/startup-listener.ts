import { type ChildProcessWithoutNullStreams, spawn } from "node:child_process";
import type { Dirent } from "node:fs";
import { readdir, readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { createInterface } from "node:readline";
import { z } from "zod";
import {
  allocateRandomLoopbackPort,
  type CodexCdpRuntimeState,
  type CodexMacosAppIdentity,
  createCodexCdpRuntimeState,
  inspectCodexMacosApp,
  inspectProcess,
  launchCodexNormally,
  launchCodexWithCdp,
  listCodexMainProcesses,
  readCodexCdpRuntimeState,
  stopLaunchedCodexCdpProcess,
  verifyCodexCdpListenerOwnership,
  waitForCodexCdpListenerOwnership,
  writeCodexCdpRuntimeState,
} from "../../../platform/macos/src/index.js";
import { GoalContractSchema, GoalContractV1Schema } from "../../contracts/src/index.js";
import type { GoalProgressPaths } from "../../store/src/index.js";

const STARTUP_EVENT_MAX_CLOCK_SKEW_MS = 5_000;
const STARTUP_PROCESS_EXIT_TIMEOUT_MS = 5_000;
const STARTUP_EVENT_DEDUP_LIMIT = 128;
const STARTUP_LISTENER_RESTART_DELAYS_MS = [1_000, 5_000, 30_000] as const;
const STARTUP_LISTENER_READY_TIMEOUT_MS = 1_000;
const StartupOverlaySchema = z
  .object({
    schemaVersion: z.literal(1),
    detached: z.boolean(),
  })
  .strict();
const StartupActivationSchema = z
  .object({
    schemaVersion: z.literal(1),
    detachReason: z.string().nullable(),
  })
  .strict();

export const MacosCodexStartupEventSchema = z
  .object({
    schemaVersion: z.literal(1),
    event: z.literal("codex.willLaunch"),
    pid: z.number().int().positive(),
    bundleId: z.string().trim().min(1).max(256),
    appPath: z.string().trim().min(1).max(4096),
    executablePath: z.string().trim().min(1).max(4096),
    launchedAt: z.string().datetime({ offset: true }),
    deadlineAtMs: z.number().int().positive(),
  })
  .strict();

export type MacosCodexStartupEvent = z.infer<typeof MacosCodexStartupEventSchema>;

export const MacosCodexStartupResponseSchema = z
  .object({
    schemaVersion: z.literal(1),
    pid: z.number().int().positive(),
    action: z.enum(["continue", "complete"]),
    code: z.string().trim().min(1).max(128),
    mainPid: z.number().int().positive().optional(),
    port: z.number().int().min(1_024).max(65_535).optional(),
    launchId: z.string().uuid().optional(),
  })
  .strict();

export type MacosCodexStartupResponse = z.infer<typeof MacosCodexStartupResponseSchema>;

export const MacosStartupListenerReadySchema = z
  .object({
    schemaVersion: z.literal(1),
    event: z.literal("listener.ready"),
    pid: z.number().int().positive(),
  })
  .strict();

export interface GoalProgressStartupListenerHealth {
  readonly running: boolean;
  readonly ready: boolean;
  readonly pid: number | null;
  readonly pendingPid: number | null;
}

export interface GoalProgressStartupListener {
  start(handler: (event: MacosCodexStartupEvent) => Promise<MacosCodexStartupResponse>): void;
  health(): GoalProgressStartupListenerHealth;
  isPending(pid: number): boolean;
  waitUntilReady(timeoutMs?: number): Promise<boolean>;
  stop(): Promise<void>;
}

export interface MacosStartupHandoffControllerOptions {
  readonly paths: GoalProgressPaths;
  readonly inspectApp?: (appPath: string) => Promise<CodexMacosAppIdentity>;
  readonly inspectTargetProcess?: typeof inspectProcess;
  readonly listMainProcesses?: typeof listCodexMainProcesses;
  readonly readRuntimeState?: typeof readCodexCdpRuntimeState;
  readonly verifyExistingOwnership?: typeof verifyCodexCdpListenerOwnership;
  readonly allocatePort?: typeof allocateRandomLoopbackPort;
  readonly launchWithCdp?: typeof launchCodexWithCdp;
  readonly waitForOwnership?: typeof waitForCodexCdpListenerOwnership;
  readonly createRuntimeState?: typeof createCodexCdpRuntimeState;
  readonly writeRuntimeState?: typeof writeCodexCdpRuntimeState;
  readonly stopCdpProcess?: typeof stopLaunchedCodexCdpProcess;
  readonly launchNormal?: typeof launchCodexNormally;
  readonly signalProcess?: (pid: number, signal: NodeJS.Signals) => void;
  readonly now?: () => number;
  readonly sleep?: (milliseconds: number) => Promise<void>;
}

export interface MacosStartupHandoffContext {
  readonly isPending: () => boolean;
  readonly isStopped?: () => boolean;
}

function eventResponse(
  event: MacosCodexStartupEvent,
  action: MacosCodexStartupResponse["action"],
  code: string,
  runtime?: Pick<CodexCdpRuntimeState, "launchId" | "mainPid" | "port">,
): MacosCodexStartupResponse {
  return {
    schemaVersion: 1,
    pid: event.pid,
    action,
    code,
    ...(runtime === undefined
      ? {}
      : {
          mainPid: runtime.mainPid,
          port: runtime.port,
          launchId: runtime.launchId,
        }),
  };
}

function commandHasCdp(command: string): boolean {
  return command
    .split(/\s+/u)
    .some(
      (argument) =>
        argument.startsWith("--remote-debugging-port=") ||
        argument.startsWith("--remote-debugging-address="),
    );
}

async function processStillExists(
  pid: number,
  inspectTargetProcess: typeof inspectProcess,
): Promise<boolean> {
  try {
    await inspectTargetProcess(pid);
    return true;
  } catch {
    return false;
  }
}

async function waitForProcessExit(
  pid: number,
  inspectTargetProcess: typeof inspectProcess,
  sleep: (milliseconds: number) => Promise<void>,
): Promise<boolean> {
  const timeoutAt = Date.now() + STARTUP_PROCESS_EXIT_TIMEOUT_MS;
  do {
    if (!(await processStillExists(pid, inspectTargetProcess))) {
      return true;
    }
    await sleep(10);
  } while (Date.now() < timeoutAt);
  return !(await processStillExists(pid, inspectTargetProcess));
}

export async function hasRecoverableGoalProgress(paths: GoalProgressPaths): Promise<boolean> {
  let entries: Dirent[];
  try {
    entries = await readdir(paths.stateRoot, { withFileTypes: true });
  } catch (error) {
    if (
      error instanceof Error &&
      "code" in error &&
      (error as NodeJS.ErrnoException).code === "ENOENT"
    ) {
      return false;
    }
    throw error;
  }

  for (const entry of entries) {
    if (!entry.isDirectory() || !/^[0-9a-f]{64}$/u.test(entry.name)) {
      continue;
    }
    try {
      const value = JSON.parse(
        await readFile(resolve(paths.stateRoot, entry.name, "snapshot.json"), "utf8"),
      ) as { contract?: unknown };
      const contract = z
        .union([GoalContractV1Schema, GoalContractSchema])
        .safeParse(value.contract);
      if (
        contract.success &&
        (contract.data.phase === "active" || contract.data.phase === "paused")
      ) {
        const sessionRoot = resolve(paths.stateRoot, entry.name);
        const [overlay, activation] = await Promise.all([
          readFile(resolve(sessionRoot, "overlay.json"), "utf8")
            .then((text) => StartupOverlaySchema.safeParse(JSON.parse(text)).data)
            .catch(() => undefined),
          readFile(resolve(sessionRoot, "activation.json"), "utf8")
            .then((text) => StartupActivationSchema.safeParse(JSON.parse(text)).data)
            .catch(() => undefined),
        ]);
        if (overlay?.detached !== true && activation?.detachReason == null) {
          return true;
        }
      }
    } catch {
      // A missing or invalid snapshot is not recoverable.
    }
  }
  return false;
}

export class MacosStartupHandoffController {
  readonly #paths: GoalProgressPaths;
  readonly #inspectApp: NonNullable<MacosStartupHandoffControllerOptions["inspectApp"]>;
  readonly #inspectTargetProcess: typeof inspectProcess;
  readonly #listMainProcesses: typeof listCodexMainProcesses;
  readonly #readRuntimeState: typeof readCodexCdpRuntimeState;
  readonly #verifyExistingOwnership: typeof verifyCodexCdpListenerOwnership;
  readonly #allocatePort: typeof allocateRandomLoopbackPort;
  readonly #launchWithCdp: typeof launchCodexWithCdp;
  readonly #waitForOwnership: typeof waitForCodexCdpListenerOwnership;
  readonly #createRuntimeState: typeof createCodexCdpRuntimeState;
  readonly #writeRuntimeState: typeof writeCodexCdpRuntimeState;
  readonly #stopCdpProcess: typeof stopLaunchedCodexCdpProcess;
  readonly #launchNormal: typeof launchCodexNormally;
  readonly #signalProcess: (pid: number, signal: NodeJS.Signals) => void;
  readonly #now: () => number;
  readonly #sleep: (milliseconds: number) => Promise<void>;
  readonly #outcomes = new Map<string, MacosCodexStartupResponse>();
  readonly #reusedMainProcesses = new Map<number, string>();
  #operationSequence = 0;
  #runtimeWriteTail: Promise<void> = Promise.resolve();

  constructor(options: MacosStartupHandoffControllerOptions) {
    this.#paths = options.paths;
    this.#inspectApp = options.inspectApp ?? ((appPath) => inspectCodexMacosApp(appPath));
    this.#inspectTargetProcess = options.inspectTargetProcess ?? inspectProcess;
    this.#listMainProcesses = options.listMainProcesses ?? listCodexMainProcesses;
    this.#readRuntimeState = options.readRuntimeState ?? readCodexCdpRuntimeState;
    this.#verifyExistingOwnership =
      options.verifyExistingOwnership ?? verifyCodexCdpListenerOwnership;
    this.#allocatePort = options.allocatePort ?? allocateRandomLoopbackPort;
    this.#launchWithCdp = options.launchWithCdp ?? launchCodexWithCdp;
    this.#waitForOwnership = options.waitForOwnership ?? waitForCodexCdpListenerOwnership;
    this.#createRuntimeState = options.createRuntimeState ?? createCodexCdpRuntimeState;
    this.#writeRuntimeState = options.writeRuntimeState ?? writeCodexCdpRuntimeState;
    this.#stopCdpProcess = options.stopCdpProcess ?? stopLaunchedCodexCdpProcess;
    this.#launchNormal = options.launchNormal ?? launchCodexNormally;
    this.#signalProcess =
      options.signalProcess ??
      ((pid, signal) => {
        process.kill(pid, signal);
      });
    this.#now = options.now ?? Date.now;
    this.#sleep =
      options.sleep ??
      ((milliseconds) => new Promise((resolveDelay) => setTimeout(resolveDelay, milliseconds)));
  }

  #remember(key: string, response: MacosCodexStartupResponse): MacosCodexStartupResponse {
    this.#outcomes.set(key, response);
    while (this.#outcomes.size > STARTUP_EVENT_DEDUP_LIMIT) {
      const oldest = this.#outcomes.keys().next().value;
      if (oldest === undefined) {
        break;
      }
      this.#outcomes.delete(oldest);
    }
    return response;
  }

  async #existingInstanceResponse(
    event: MacosCodexStartupEvent,
    app: CodexMacosAppIdentity,
  ): Promise<MacosCodexStartupResponse | undefined> {
    try {
      const state = await this.#readRuntimeState(this.#paths.cdpRuntimePath);
      if (
        state.mainPid !== event.pid &&
        state.appPath === app.realAppPath &&
        state.executablePath === app.realExecutablePath &&
        state.bundleId === app.bundleId &&
        state.teamId === app.teamId
      ) {
        const ownership = await this.#verifyExistingOwnership(app, state.mainPid, state.port);
        if (
          ownership.mainProcess.startedAt === state.processStartedAt &&
          ownership.mainProcess.command === state.command
        ) {
          this.#rememberReusedMainProcess(ownership.mainProcess);
          return eventResponse(event, "continue", "STARTUP_EVENT_EXISTING_CDP", state);
        }
      }
    } catch {
      // A stale or unavailable runtime record does not prove that no main process exists.
    }

    let processes: readonly Awaited<ReturnType<typeof inspectProcess>>[];
    try {
      processes = await this.#listMainProcesses(app);
    } catch {
      return eventResponse(event, "continue", "STARTUP_EVENT_INSTANCE_CHECK_FAILED");
    }
    const existing = processes.find((process) => process.pid !== event.pid);
    if (existing) {
      this.#rememberReusedMainProcess(existing);
    }
    return existing
      ? {
          ...eventResponse(event, "continue", "STARTUP_EVENT_EXISTING_INSTANCE"),
          mainPid: existing.pid,
        }
      : undefined;
  }

  #processIdentity(process: { readonly startedAt: string; readonly command: string }): string {
    return `${process.startedAt}\n${process.command}`;
  }

  #rememberReusedMainProcess(process: Awaited<ReturnType<typeof inspectProcess>>): void {
    this.#reusedMainProcesses.set(process.pid, this.#processIdentity(process));
    while (this.#reusedMainProcesses.size > STARTUP_EVENT_DEDUP_LIMIT) {
      const oldest = this.#reusedMainProcesses.keys().next().value;
      if (oldest === undefined) {
        break;
      }
      this.#reusedMainProcesses.delete(oldest);
    }
  }

  #launchedProcessIdentity(launched: Awaited<ReturnType<typeof launchCodexWithCdp>>): string {
    return this.#processIdentity({
      startedAt: launched.processStartedAt,
      command: launched.command,
    });
  }

  #launchWasReused(launched: Awaited<ReturnType<typeof launchCodexWithCdp>>): boolean {
    return this.#reusedMainProcesses.get(launched.pid) === this.#launchedProcessIdentity(launched);
  }

  async #matchingLaunchedProcess(
    launched: Awaited<ReturnType<typeof launchCodexWithCdp>>,
  ): Promise<Awaited<ReturnType<typeof inspectProcess>> | null> {
    try {
      const current = await this.#inspectTargetProcess(launched.pid);
      return this.#processIdentity(current) === this.#launchedProcessIdentity(launched)
        ? current
        : null;
    } catch {
      return null;
    }
  }

  async #launchIsInUse(
    launched: Awaited<ReturnType<typeof launchCodexWithCdp>>,
    port: number,
  ): Promise<boolean> {
    const current = await this.#matchingLaunchedProcess(launched);
    if (!current) {
      this.#reusedMainProcesses.delete(launched.pid);
      return false;
    }
    if (this.#launchWasReused(launched)) {
      return true;
    }
    try {
      const state = await this.#readRuntimeState(this.#paths.cdpRuntimePath);
      return (
        state.mainPid === launched.pid &&
        state.port === port &&
        state.processStartedAt === launched.processStartedAt &&
        state.command === launched.command
      );
    } catch {
      return false;
    }
  }

  async #writeRuntimeIfCurrent(
    state: CodexCdpRuntimeState,
    isCurrent: () => boolean,
  ): Promise<boolean> {
    let written = false;
    const write = this.#runtimeWriteTail.then(async () => {
      if (!isCurrent()) {
        return;
      }
      await this.#writeRuntimeState(this.#paths.cdpRuntimePath, state);
      written = true;
    });
    this.#runtimeWriteTail = write.then(
      () => undefined,
      () => undefined,
    );
    await write;
    return written;
  }

  async #stopOwnedLaunch(
    app: CodexMacosAppIdentity,
    launched: Awaited<ReturnType<typeof launchCodexWithCdp>>,
    port: number,
    preserveForNewerOperation = false,
  ): Promise<boolean> {
    if (preserveForNewerOperation && (await this.#matchingLaunchedProcess(launched))) {
      return true;
    }
    if (await this.#launchIsInUse(launched, port)) {
      return true;
    }
    try {
      await this.#stopCdpProcess(app, launched, port);
    } catch {
      try {
        const current = await this.#inspectTargetProcess(launched.pid);
        if (
          current.startedAt === launched.processStartedAt &&
          current.command === launched.command
        ) {
          this.#signalProcess(launched.pid, "SIGTERM");
          await waitForProcessExit(launched.pid, this.#inspectTargetProcess, this.#sleep);
        }
      } catch {
        // The launched process already exited.
      }
    }
    return processStillExists(launched.pid, this.#inspectTargetProcess);
  }

  async #restoreNormalIfNoMain(
    app: CodexMacosAppIdentity,
    isStopped: () => boolean,
  ): Promise<boolean> {
    try {
      if ((await this.#listMainProcesses(app)).length > 0) {
        return false;
      }
      if (isStopped()) {
        return false;
      }
      await this.#launchNormal(app);
      return true;
    } catch {
      return false;
    }
  }

  async handle(
    eventInput: MacosCodexStartupEvent,
    recoverableProgress: boolean,
    context: MacosStartupHandoffContext = { isPending: () => true },
  ): Promise<MacosCodexStartupResponse> {
    const event = MacosCodexStartupEventSchema.parse(eventInput);
    const key = `${event.pid}:${event.launchedAt}:${event.executablePath}`;
    const duplicate = this.#outcomes.get(key);
    if (duplicate) {
      return duplicate;
    }
    const operationSequence = ++this.#operationSequence;
    const isSuperseded = () => operationSequence !== this.#operationSequence;
    const isStopped = () => context.isStopped?.() === true;
    const canFinish = () => !isSuperseded() && !isStopped();
    const canStart = () => canFinish() && context.isPending() && this.#now() < event.deadlineAtMs;
    if (!recoverableProgress) {
      return this.#remember(
        key,
        eventResponse(event, "continue", "STARTUP_EVENT_NO_RECOVERABLE_PROGRESS"),
      );
    }
    if (this.#now() >= event.deadlineAtMs) {
      return this.#remember(key, eventResponse(event, "continue", "STARTUP_EVENT_EXPIRED"));
    }

    const original = await this.#inspectTargetProcess(event.pid);
    const processStartedAt = Date.parse(original.startedAt);
    const eventLaunchedAt = Date.parse(event.launchedAt);
    if (
      (original.command !== event.executablePath &&
        !original.command.startsWith(`${event.executablePath} `)) ||
      !Number.isFinite(processStartedAt) ||
      !Number.isFinite(eventLaunchedAt) ||
      Math.abs(processStartedAt - eventLaunchedAt) > STARTUP_EVENT_MAX_CLOCK_SKEW_MS
    ) {
      return this.#remember(
        key,
        eventResponse(event, "continue", "STARTUP_EVENT_PROCESS_MISMATCH"),
      );
    }
    if (original.parentPid === process.pid) {
      return this.#remember(key, eventResponse(event, "continue", "STARTUP_EVENT_HELPER_LAUNCH"));
    }
    if (commandHasCdp(original.command)) {
      return this.#remember(key, eventResponse(event, "continue", "STARTUP_EVENT_ALREADY_CDP"));
    }
    if (original.command !== event.executablePath) {
      return this.#remember(
        key,
        eventResponse(event, "continue", "STARTUP_EVENT_PROCESS_MISMATCH"),
      );
    }
    if (!context.isPending()) {
      return this.#remember(key, eventResponse(event, "continue", "STARTUP_EVENT_RELEASED"));
    }
    if (this.#now() >= event.deadlineAtMs) {
      return this.#remember(key, eventResponse(event, "continue", "STARTUP_EVENT_EXPIRED"));
    }

    const app = await this.#inspectApp(event.appPath);
    if (
      event.bundleId !== app.bundleId ||
      event.appPath !== app.realAppPath ||
      event.executablePath !== app.realExecutablePath
    ) {
      return this.#remember(key, eventResponse(event, "continue", "STARTUP_EVENT_APP_MISMATCH"));
    }

    const existingInstance = await this.#existingInstanceResponse(event, app);
    if (existingInstance) {
      return this.#remember(key, existingInstance);
    }

    let launched: Awaited<ReturnType<typeof launchCodexWithCdp>> | undefined;
    let port: number | undefined;
    try {
      port = await this.#allocatePort();
      if (this.#now() >= event.deadlineAtMs) {
        return this.#remember(key, eventResponse(event, "continue", "STARTUP_EVENT_EXPIRED"));
      }
      if (!canStart()) {
        return this.#remember(key, eventResponse(event, "continue", "STARTUP_EVENT_RELEASED"));
      }
      this.#signalProcess(event.pid, "SIGTERM");
      this.#signalProcess(event.pid, "SIGCONT");
      if (!(await waitForProcessExit(event.pid, this.#inspectTargetProcess, this.#sleep))) {
        throw new Error("GOAL_PROGRESS_CODEX_CURRENT_PROCESS_STOP_TIMEOUT");
      }
      if (!canFinish()) {
        return this.#remember(key, eventResponse(event, "complete", "STARTUP_EVENT_RELEASED"));
      }
      const concurrentInstance = await this.#existingInstanceResponse(event, app);
      if (concurrentInstance) {
        return this.#remember(key, concurrentInstance);
      }
      if (!canFinish()) {
        return this.#remember(key, eventResponse(event, "complete", "STARTUP_EVENT_RELEASED"));
      }
      launched = await this.#launchWithCdp(app, { port });
      if (!canFinish()) {
        await this.#stopOwnedLaunch(app, launched, port, isSuperseded() && !isStopped());
        return this.#remember(key, eventResponse(event, "complete", "STARTUP_EVENT_RELEASED"));
      }
      const ownership = await this.#waitForOwnership(app, launched.pid, port);
      if (!canFinish()) {
        await this.#stopOwnedLaunch(app, launched, port, isSuperseded() && !isStopped());
        return this.#remember(key, eventResponse(event, "complete", "STARTUP_EVENT_RELEASED"));
      }
      const state = this.#createRuntimeState(app, launched, ownership, port);
      if (!(await this.#writeRuntimeIfCurrent(state, canFinish))) {
        await this.#stopOwnedLaunch(app, launched, port, isSuperseded() && !isStopped());
        return this.#remember(key, eventResponse(event, "complete", "STARTUP_EVENT_RELEASED"));
      }
      if (!canFinish()) {
        return this.#remember(key, eventResponse(event, "complete", "STARTUP_EVENT_RELEASED"));
      }
      return this.#remember(
        key,
        eventResponse(event, "complete", "STARTUP_HANDOFF_COMPLETE", state),
      );
    } catch {
      const reusedByNewerOperation = launched ? this.#launchWasReused(launched) : false;
      if (launched && port !== undefined) {
        if (await this.#stopOwnedLaunch(app, launched, port, isSuperseded() && !isStopped())) {
          return this.#remember(
            key,
            eventResponse(event, "complete", "STARTUP_HANDOFF_CDP_PROCESS_RETAINED"),
          );
        }
      }
      if (!canFinish()) {
        if (
          isSuperseded() &&
          !isStopped() &&
          reusedByNewerOperation &&
          (await this.#restoreNormalIfNoMain(app, isStopped))
        ) {
          return this.#remember(
            key,
            eventResponse(event, "complete", "STARTUP_HANDOFF_FALLBACK_NORMAL"),
          );
        }
        return this.#remember(key, eventResponse(event, "complete", "STARTUP_EVENT_RELEASED"));
      }
      if (await processStillExists(event.pid, this.#inspectTargetProcess)) {
        return this.#remember(
          key,
          eventResponse(event, "continue", "STARTUP_HANDOFF_CONTINUED_ORIGINAL"),
        );
      }
      if (!canFinish()) {
        return this.#remember(key, eventResponse(event, "complete", "STARTUP_EVENT_RELEASED"));
      }
      try {
        await this.#launchNormal(app);
        return this.#remember(
          key,
          eventResponse(event, "complete", "STARTUP_HANDOFF_FALLBACK_NORMAL"),
        );
      } catch {
        return this.#remember(key, eventResponse(event, "continue", "STARTUP_HANDOFF_FAILED"));
      }
    }
  }
}

export interface CreateMacosStartupListenerOptions {
  readonly executablePath: string;
  readonly bundleId: string;
  readonly appPath: string;
  readonly appExecutablePath: string;
  readonly spawnProcess?: typeof spawn;
  readonly restartDelaysMs?: readonly number[];
  readonly signalProcess?: (pid: number, signal: NodeJS.Signals) => void;
}

interface PendingStartupEvent {
  readonly pid: number;
  readonly timer: ReturnType<typeof setTimeout>;
}

export class MacosStartupListenerSupervisor implements GoalProgressStartupListener {
  readonly #options: CreateMacosStartupListenerOptions;
  readonly #spawnProcess: typeof spawn;
  readonly #restartDelaysMs: readonly number[];
  readonly #signalProcess: (pid: number, signal: NodeJS.Signals) => void;
  #child: ChildProcessWithoutNullStreams | undefined;
  #handler: ((event: MacosCodexStartupEvent) => Promise<MacosCodexStartupResponse>) | undefined;
  #restartTimer: ReturnType<typeof setTimeout> | undefined;
  #restartIndex = 0;
  #stopping = false;
  #ready = false;
  #listenerPid: number | null = null;
  #pending: PendingStartupEvent | undefined;
  readonly #readyWaiters = new Set<(ready: boolean) => void>();

  constructor(options: CreateMacosStartupListenerOptions) {
    this.#options = options;
    this.#spawnProcess = options.spawnProcess ?? spawn;
    this.#restartDelaysMs = options.restartDelaysMs ?? STARTUP_LISTENER_RESTART_DELAYS_MS;
    this.#signalProcess =
      options.signalProcess ??
      ((pid, signal) => {
        process.kill(pid, signal);
      });
  }

  start(handler: (event: MacosCodexStartupEvent) => Promise<MacosCodexStartupResponse>): void {
    if (this.#child || this.#handler) {
      return;
    }
    this.#handler = handler;
    this.#spawn();
  }

  health(): GoalProgressStartupListenerHealth {
    return {
      running:
        this.#child !== undefined &&
        this.#child.exitCode === null &&
        this.#child.signalCode === null,
      ready: this.#ready,
      pid: this.#listenerPid,
      pendingPid: this.#pending?.pid ?? null,
    };
  }

  isPending(pid: number): boolean {
    return this.#pending?.pid === pid;
  }

  async waitUntilReady(timeoutMs = STARTUP_LISTENER_READY_TIMEOUT_MS): Promise<boolean> {
    if (this.#ready) {
      return true;
    }
    return new Promise<boolean>((resolveReady) => {
      const finish = (ready: boolean) => {
        clearTimeout(timeout);
        this.#readyWaiters.delete(finish);
        resolveReady(ready);
      };
      const timeout = setTimeout(() => finish(false), timeoutMs);
      this.#readyWaiters.add(finish);
    });
  }

  #resolveReadyWaiters(ready: boolean): void {
    for (const resolveReady of [...this.#readyWaiters]) {
      resolveReady(ready);
    }
  }

  #clearPending(pid: number): boolean {
    if (this.#pending?.pid !== pid) {
      return false;
    }
    const pending = this.#pending;
    this.#pending = undefined;
    clearTimeout(pending.timer);
    return true;
  }

  #releasePending(pid: number = this.#pending?.pid ?? -1): boolean {
    if (!this.#clearPending(pid)) {
      return false;
    }
    try {
      this.#signalProcess(pid, "SIGCONT");
    } catch {
      // The process may already have exited during a completed handoff.
    }
    return true;
  }

  #invalidateChild(child: ChildProcessWithoutNullStreams): void {
    if (child !== this.#child) {
      return;
    }
    this.#ready = false;
    this.#listenerPid = null;
    this.#releasePending();
    child.kill("SIGTERM");
  }

  #writeResponse(child: ChildProcessWithoutNullStreams, response: MacosCodexStartupResponse): void {
    const normalized =
      response.action === "continue" ? { ...response, action: "complete" as const } : response;
    if (response.action === "continue") {
      this.#releasePending(response.pid);
    }
    try {
      child.stdin.write(`${JSON.stringify(normalized)}\n`, (error) => {
        if (error) {
          this.#invalidateChild(child);
          return;
        }
        this.#clearPending(response.pid);
      });
    } catch {
      this.#invalidateChild(child);
    }
  }

  #setPending(child: ChildProcessWithoutNullStreams, event: MacosCodexStartupEvent): boolean {
    if (this.#pending) {
      return false;
    }
    const delay = Math.max(0, event.deadlineAtMs - Date.now());
    const timer = setTimeout(() => {
      if (!this.#releasePending(event.pid)) {
        return;
      }
      this.#writeResponse(child, eventResponse(event, "complete", "STARTUP_HANDLER_TIMEOUT"));
    }, delay);
    timer.unref?.();
    this.#pending = { pid: event.pid, timer };
    return true;
  }

  #spawn(): void {
    if (this.#stopping || !this.#handler) {
      return;
    }
    const child = this.#spawnProcess(
      this.#options.executablePath,
      [this.#options.bundleId, this.#options.appPath, this.#options.appExecutablePath],
      {
        shell: false,
        stdio: ["pipe", "pipe", "pipe"],
      },
    );
    this.#child = child;
    this.#ready = false;
    this.#listenerPid = null;
    child.stdin.on("error", () => {
      this.#invalidateChild(child);
    });
    const lines = createInterface({ input: child.stdout });
    lines.on("line", (line) => {
      let input: unknown;
      try {
        input = JSON.parse(line);
      } catch {
        return;
      }
      const ready = MacosStartupListenerReadySchema.safeParse(input);
      if (ready.success && child === this.#child) {
        this.#ready = true;
        this.#listenerPid = ready.data.pid;
        this.#restartIndex = 0;
        this.#resolveReadyWaiters(true);
        return;
      }
      const parsed = MacosCodexStartupEventSchema.safeParse(input);
      if (
        !parsed.success ||
        !this.#ready ||
        !this.#handler ||
        child !== this.#child ||
        !this.#setPending(child, parsed.data)
      ) {
        return;
      }
      void (async () => {
        if (!this.#handler || child !== this.#child || !this.isPending(parsed.data.pid)) {
          return;
        }
        let response: MacosCodexStartupResponse;
        try {
          response = await this.#handler(parsed.data);
        } catch {
          response = eventResponse(parsed.data, "continue", "STARTUP_HANDLER_FAILED");
        }
        if (!this.isPending(parsed.data.pid)) {
          return;
        }
        this.#writeResponse(child, response);
      })();
    });
    child.once("error", () => {
      this.#invalidateChild(child);
    });
    child.once("close", () => {
      if (child !== this.#child) {
        return;
      }
      this.#releasePending();
      this.#child = undefined;
      this.#ready = false;
      this.#listenerPid = null;
      if (this.#stopping || this.#restartIndex >= this.#restartDelaysMs.length) {
        this.#resolveReadyWaiters(false);
        return;
      }
      const delay = this.#restartDelaysMs[this.#restartIndex] ?? 30_000;
      this.#restartIndex += 1;
      this.#restartTimer = setTimeout(() => {
        this.#restartTimer = undefined;
        this.#spawn();
      }, delay);
      this.#restartTimer.unref?.();
    });
  }

  async stop(): Promise<void> {
    this.#stopping = true;
    this.#handler = undefined;
    this.#releasePending();
    this.#resolveReadyWaiters(false);
    if (this.#restartTimer) {
      clearTimeout(this.#restartTimer);
      this.#restartTimer = undefined;
    }
    const child = this.#child;
    this.#child = undefined;
    if (!child) {
      return;
    }
    child.stdin.end();
    child.kill("SIGTERM");
    if (child.exitCode !== null || child.signalCode !== null) {
      return;
    }
    await new Promise<void>((resolveExit) => {
      const timeout = setTimeout(() => {
        child.kill("SIGKILL");
        resolveExit();
      }, 1_000);
      child.once("close", () => {
        clearTimeout(timeout);
        resolveExit();
      });
    });
  }
}

export function resolveStartupListenerExecutable(
  executablePath: string = process.execPath,
  configuredPath: string | undefined = process.env.GOAL_PROGRESS_STARTUP_LISTENER,
): string {
  const configured = configuredPath?.trim();
  return configured
    ? resolve(configured)
    : resolve(dirname(executablePath), "goal-progress-startup-listener");
}
