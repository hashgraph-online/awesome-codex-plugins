import { isCodexRendererPageUrl } from "../../codex-adapter/src/cdp.js";
import type { GoalProgressRendererBridgeDoctor } from "../../codex-adapter/src/index.js";
import {
  classifyGoalProgressUpdateState,
  DEFAULT_GOAL_PROGRESS_UI_PREFERENCE,
  type GoalProgressUiPreference,
  type GoalProgressUpdateState,
  type GoalProgressViewModel,
} from "../../contracts/src/index.js";
import { GoalProgressRendererTargetIdSchema } from "../../ipc/src/index.js";
import type { RendererBridgeSupervisorConnection } from "./renderer-bridge-supervisor.js";
import type {
  ViewModelPublisherCloseOptions,
  ViewModelPublisherSink,
} from "./view-model-publisher.js";

export interface RendererTargetInfo {
  readonly targetId: string;
  readonly type: string;
  readonly url: string;
}

export interface RendererTargetSource {
  readonly initialTargets: readonly RendererTargetInfo[];
  onTargetInfo(listener: (target: RendererTargetInfo) => void): () => void;
  onTargetDestroyed(listener: (targetId: string) => void): () => void;
  onFailure?(listener: (error: Error) => void): () => void;
  connectTarget(target: RendererTargetInfo): Promise<RendererBridgeSupervisorConnection>;
  close(): Promise<void>;
}

export const RENDERER_TARGET_SOURCE_RECONNECT_DELAYS_MS = [
  0, 1_000, 2_000, 5_000, 10_000, 30_000,
] as const;

export interface RendererTargetManagerOptions {
  readonly connector: () => Promise<RendererTargetSource | undefined>;
  readonly onTargetReady?: (
    targetId: string,
    threadId: string | null,
    lifecycleId?: string,
  ) => Promise<void> | void;
  readonly onTargetDestroyed?: (targetId: string, code?: string) => Promise<void> | void;
  readonly sourceReconnectDelaysMs?: readonly number[];
  readonly sleep?: (delayMs: number) => Promise<void>;
}

export interface RendererTargetState {
  readonly targetId: string;
  readonly visibleThreadId: string | null;
  readonly revision: number | null;
  readonly deliveryCurrent: boolean;
  readonly doctor: GoalProgressRendererBridgeDoctor | null;
  readonly lastErrorCode: string | null;
  readonly closed: boolean;
}

interface ManagedRendererTarget {
  info: RendererTargetInfo;
  bridge: RendererBridgeSupervisorConnection | undefined;
  visibleThreadId: string | null;
  revision: number | null;
  deliveryCurrent: boolean;
  doctor: GoalProgressRendererBridgeDoctor | null;
  lastErrorCode: string | null;
  closed: boolean;
}

function stableTargetError(error: unknown): string {
  const value = error instanceof Error ? error.message : String(error);
  return /^[A-Z][A-Z0-9_]{2,127}/u.exec(value)?.[0] ?? "RENDERER_TARGET_UNAVAILABLE";
}

function acceptedTarget(info: RendererTargetInfo): boolean {
  return (
    GoalProgressRendererTargetIdSchema.safeParse(info.targetId).success &&
    info.type === "page" &&
    isCodexRendererPageUrl(info.url)
  );
}

export class RendererTargetManager implements ViewModelPublisherSink {
  readonly #connector: RendererTargetManagerOptions["connector"];
  readonly #onTargetReady: RendererTargetManagerOptions["onTargetReady"];
  readonly #onTargetDestroyed: RendererTargetManagerOptions["onTargetDestroyed"];
  readonly #sourceReconnectDelaysMs: readonly number[];
  readonly #sleep: (delayMs: number) => Promise<void>;
  readonly #targets = new Map<string, ManagedRendererTarget>();
  #source: RendererTargetSource | undefined;
  #removeInfoListener: (() => void) | undefined;
  #removeDestroyedListener: (() => void) | undefined;
  #removeFailureListener: (() => void) | undefined;
  #sourceRecovery: Promise<void> | undefined;
  #uiPreference: GoalProgressUiPreference = DEFAULT_GOAL_PROGRESS_UI_PREFERENCE;
  #updateState: GoalProgressUpdateState | null = null;
  #closed = false;
  #queue: Promise<void> = Promise.resolve();

  constructor(options: RendererTargetManagerOptions) {
    this.#connector = options.connector;
    this.#onTargetReady = options.onTargetReady;
    this.#onTargetDestroyed = options.onTargetDestroyed;
    this.#sourceReconnectDelaysMs =
      options.sourceReconnectDelaysMs ?? RENDERER_TARGET_SOURCE_RECONNECT_DELAYS_MS;
    this.#sleep =
      options.sleep ??
      ((delayMs) =>
        new Promise((resolveDelay) => {
          const timer = setTimeout(resolveDelay, delayMs);
          timer.unref();
        }));
  }

  get currentUpdateState(): GoalProgressUpdateState | null {
    return this.#updateState;
  }

  targetIds(): string[] {
    return [...this.#targets.keys()].sort();
  }

  hasTarget(targetId: string): boolean {
    return this.#targets.has(targetId);
  }

  targetState(targetId: string): RendererTargetState | undefined {
    const target = this.#targets.get(targetId);
    if (!target) {
      return undefined;
    }
    return {
      targetId,
      visibleThreadId: target.visibleThreadId,
      revision: target.revision,
      deliveryCurrent: target.deliveryCurrent,
      doctor: target.doctor,
      lastErrorCode: target.lastErrorCode,
      closed: target.closed,
    };
  }

  async start(): Promise<void> {
    await this.#enqueue(async () => {
      if (this.#closed || this.#source) {
        return;
      }
      const source = await this.#connector();
      if (!source) {
        throw new Error("RENDERER_TARGET_SOURCE_UNAVAILABLE");
      }
      this.#source = source;
      this.#removeInfoListener = source.onTargetInfo((target) => {
        void this.#enqueue(() => this.#connectTarget(target));
      });
      this.#removeDestroyedListener = source.onTargetDestroyed((targetId) => {
        void this.#enqueue(() =>
          this.#destroyTarget(targetId, true, "GOAL_PROGRESS_CDP_TARGET_DESTROYED"),
        );
      });
      this.#removeFailureListener = source.onFailure?.((error) => {
        this.#beginSourceRecovery(source, error);
      });
      for (const target of source.initialTargets) {
        await this.#connectTarget(target);
      }
    });
  }

  async settle(): Promise<void> {
    await this.#queue;
  }

  async recoverVisibleTargets(): Promise<
    readonly { readonly targetId: string; readonly threadId: string | null }[]
  > {
    await this.start();
    return this.targetIds().map((targetId) => ({
      targetId,
      threadId: this.#targets.get(targetId)?.visibleThreadId ?? null,
    }));
  }

  async recoverVisibleThreadId(): Promise<string | undefined> {
    return (
      (await this.recoverVisibleTargets()).find((target) => target.threadId)?.threadId ?? undefined
    );
  }

  async recoverTargetThreadId(targetId: string): Promise<string | null | undefined> {
    let recovered: string | null | undefined;
    await this.#enqueue(async () => {
      const target = this.#requireTarget(targetId);
      if (!target.bridge?.recoverVisibleThreadId) {
        return;
      }
      recovered = (await target.bridge.recoverVisibleThreadId()) ?? null;
    });
    return recovered;
  }

  async reconnect(): Promise<string | undefined> {
    await this.#enqueue(async () => {
      await this.#closeSourceAndTargets();
      this.#closed = false;
    });
    return (
      (await this.recoverVisibleTargets()).find((target) => target.threadId)?.threadId ?? undefined
    );
  }

  async setTargetThread(targetId: string, threadId: string | null): Promise<void> {
    await this.#enqueue(async () => {
      const target = this.#requireTarget(targetId);
      if (target.visibleThreadId === threadId) {
        return;
      }
      target.visibleThreadId = threadId;
      target.revision = null;
      target.deliveryCurrent = false;
      target.doctor = null;
      await target.bridge?.clear();
    });
  }

  async clearTarget(targetId: string): Promise<void> {
    await this.#enqueue(async () => {
      const target = this.#requireTarget(targetId);
      await target.bridge?.clear();
      target.revision = null;
      target.deliveryCurrent = false;
      target.doctor = null;
    });
  }

  async publishTarget(targetId: string, viewModel: GoalProgressViewModel): Promise<void> {
    await this.#enqueue(async () => {
      const target = this.#requireTarget(targetId);
      if (!target.bridge || target.visibleThreadId !== viewModel.sessionId) {
        throw new Error("RENDERER_TARGET_THREAD_MISMATCH");
      }
      try {
        await target.bridge.publish(viewModel);
        target.revision = viewModel.revision;
        target.deliveryCurrent = true;
        target.lastErrorCode = null;
      } catch (error) {
        target.lastErrorCode = stableTargetError(error);
        await this.#destroyTarget(targetId);
        throw error;
      }
    });
  }

  async doctorTarget(
    targetId: string,
    expectedThreadId?: string,
  ): Promise<GoalProgressRendererBridgeDoctor> {
    let doctor: GoalProgressRendererBridgeDoctor | undefined;
    await this.#enqueue(async () => {
      const target = this.#requireTarget(targetId);
      if (!target.bridge) {
        throw new Error(target.lastErrorCode ?? "RENDERER_TARGET_UNAVAILABLE");
      }
      doctor = await target.bridge.doctor(expectedThreadId);
      target.doctor = doctor;
    });
    if (!doctor) {
      throw new Error("RENDERER_TARGET_UNAVAILABLE");
    }
    return doctor;
  }

  async handleTargetDisconnect(targetId: string, code: string): Promise<void> {
    await this.#enqueue(async () => {
      const target = this.#requireTarget(targetId);
      target.lastErrorCode = code;
      await this.#destroyTarget(targetId);
    });
  }

  async clear(): Promise<void> {
    await this.#enqueue(async () => {
      await Promise.all(
        [...this.#targets.values()].map(async (target) => {
          await target.bridge?.clear();
          target.revision = null;
          target.deliveryCurrent = false;
          target.doctor = null;
        }),
      );
    });
  }

  async publish(viewModel: GoalProgressViewModel): Promise<void> {
    for (const targetId of this.targetIds()) {
      if (this.#targets.get(targetId)?.visibleThreadId === viewModel.sessionId) {
        await this.publishTarget(targetId, viewModel);
      }
    }
  }

  async setUiPreference(uiPreference: GoalProgressUiPreference): Promise<void> {
    await this.#enqueue(async () => {
      this.#uiPreference = uiPreference;
      await Promise.allSettled(
        [...this.#targets.values()].map((target) => target.bridge?.setUiPreference?.(uiPreference)),
      );
    });
  }

  async setUpdateState(updateState: GoalProgressUpdateState | null): Promise<void> {
    await this.#enqueue(async () => {
      if (
        updateState === null ||
        classifyGoalProgressUpdateState(updateState, this.#updateState) !== "accept"
      ) {
        return;
      }
      this.#updateState = updateState;
      await Promise.allSettled(
        [...this.#targets.values()].map((target) => target.bridge?.setUpdateState?.(updateState)),
      );
    });
  }

  rememberUpdateState(updateState: GoalProgressUpdateState | null): void {
    if (
      updateState === null ||
      classifyGoalProgressUpdateState(updateState, this.#updateState) !== "accept"
    ) {
      return;
    }
    this.#updateState = updateState;
  }

  async doctor(expectedThreadId?: string): Promise<GoalProgressRendererBridgeDoctor> {
    let lastError: unknown;
    for (const targetId of this.targetIds()) {
      if (
        expectedThreadId !== undefined &&
        this.#targets.get(targetId)?.visibleThreadId !== expectedThreadId
      ) {
        continue;
      }
      try {
        return await this.doctorTarget(targetId, expectedThreadId);
      } catch (error) {
        lastError = error;
      }
    }
    throw lastError ?? new Error("RENDERER_TARGET_UNAVAILABLE");
  }

  async handleDisconnect(code: string): Promise<void> {
    for (const targetId of this.targetIds()) {
      await this.handleTargetDisconnect(targetId, code);
    }
  }

  async close(options?: ViewModelPublisherCloseOptions): Promise<void> {
    await this.#enqueue(async () => {
      this.#closed = true;
      await this.#closeSourceAndTargets(options?.preservePage === true);
    });
  }

  #enqueue(work: () => Promise<void>): Promise<void> {
    const run = this.#queue.then(work, work);
    this.#queue = run.catch(() => undefined);
    return run;
  }

  async #connectTarget(info: RendererTargetInfo): Promise<void> {
    if (!acceptedTarget(info) || this.#closed) {
      return;
    }
    const existing = this.#targets.get(info.targetId);
    if (existing?.bridge || (existing && !existing.closed)) {
      existing.info = info;
      return;
    }
    const source = this.#source;
    if (!source) {
      return;
    }
    const target: ManagedRendererTarget =
      existing ??
      ({
        info,
        bridge: undefined,
        visibleThreadId: null,
        revision: null,
        deliveryCurrent: false,
        doctor: null,
        lastErrorCode: null,
        closed: false,
      } satisfies ManagedRendererTarget);
    target.info = info;
    target.closed = false;
    this.#targets.set(info.targetId, target);
    try {
      const bridge = await source.connectTarget(info);
      target.bridge = bridge;
      await bridge.clear();
      target.visibleThreadId = (await bridge.recoverVisibleThreadId?.()) ?? null;
      await bridge.setUiPreference?.(this.#uiPreference);
      await bridge.setUpdateState?.(this.#updateState);
      await this.#onTargetReady?.(
        info.targetId,
        target.visibleThreadId,
        bridge.visibleThreadLifecycleId,
      );
    } catch (error) {
      target.lastErrorCode = stableTargetError(error);
      await target.bridge?.close().catch(() => undefined);
      this.#targets.delete(info.targetId);
    }
  }

  async #destroyTarget(targetId: string, notify = false, code?: string): Promise<void> {
    const target = this.#targets.get(targetId);
    if (!target) {
      return;
    }
    this.#targets.delete(targetId);
    target.closed = true;
    target.deliveryCurrent = false;
    await target.bridge?.close().catch(() => undefined);
    target.bridge = undefined;
    if (notify) {
      await this.#onTargetDestroyed?.(targetId, code);
    }
  }

  #requireTarget(targetId: string): ManagedRendererTarget {
    if (!GoalProgressRendererTargetIdSchema.safeParse(targetId).success) {
      throw new Error("RENDERER_TARGET_ID_INVALID");
    }
    const target = this.#targets.get(targetId);
    if (!target || target.closed) {
      throw new Error("RENDERER_TARGET_UNKNOWN");
    }
    return target;
  }

  #beginSourceRecovery(source: RendererTargetSource, error: Error): void {
    if (this.#closed || this.#source !== source) {
      return;
    }
    if (this.#sourceRecovery) {
      const currentRecovery = this.#sourceRecovery;
      void currentRecovery.then(
        () => {
          if (!this.#closed && this.#source === source) {
            this.#beginSourceRecovery(source, error);
          }
        },
        () => undefined,
      );
      return;
    }
    const recovery = this.#recoverSource(source, stableTargetError(error));
    this.#sourceRecovery = recovery;
    void recovery.then(
      () => {
        if (this.#sourceRecovery === recovery) {
          this.#sourceRecovery = undefined;
        }
      },
      () => {
        if (this.#sourceRecovery === recovery) {
          this.#sourceRecovery = undefined;
        }
      },
    );
  }

  async #recoverSource(source: RendererTargetSource, code: string): Promise<void> {
    await this.#enqueue(async () => {
      if (this.#closed || this.#source !== source) {
        return;
      }
      for (const target of this.#targets.values()) {
        target.lastErrorCode = code;
      }
      await this.#closeSourceAndTargets(true, code);
    });
    for (const delayMs of this.#sourceReconnectDelaysMs) {
      if (this.#closed) {
        return;
      }
      if (delayMs > 0) {
        await this.#sleep(delayMs);
      }
      if (this.#closed) {
        return;
      }
      try {
        await this.start();
        if (this.#source) {
          return;
        }
      } catch {
        // A Codex update can replace the process before cdp.json is refreshed. Retry only this event.
      }
    }
  }

  async #closeSourceAndTargets(preservePage = false, notifyCode?: string): Promise<void> {
    this.#removeInfoListener?.();
    this.#removeDestroyedListener?.();
    this.#removeFailureListener?.();
    this.#removeInfoListener = undefined;
    this.#removeDestroyedListener = undefined;
    this.#removeFailureListener = undefined;
    for (const targetId of this.targetIds()) {
      if (!preservePage) {
        await this.#targets
          .get(targetId)
          ?.bridge?.clear()
          .catch(() => undefined);
      }
      await this.#destroyTarget(targetId, notifyCode !== undefined, notifyCode);
    }
    const source = this.#source;
    this.#source = undefined;
    await source?.close().catch(() => undefined);
  }
}
