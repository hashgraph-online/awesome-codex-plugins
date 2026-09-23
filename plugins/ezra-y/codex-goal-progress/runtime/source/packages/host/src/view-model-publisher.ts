import {
  classifyGoalProgressUpdateState,
  type GoalProgressUiPreference,
  type GoalProgressUpdateState,
  type GoalProgressViewModel,
} from "../../contracts/src/index.js";

export interface ViewModelPublisherSink {
  clear(): Promise<void>;
  clearTarget?(targetId: string): Promise<void>;
  handleDisconnect?(code: string): Promise<void> | void;
  handleTargetDisconnect?(targetId: string, code: string): Promise<void> | void;
  hasTarget?(targetId: string): boolean;
  publish(viewModel: GoalProgressViewModel): Promise<void>;
  publishTarget?(targetId: string, viewModel: GoalProgressViewModel): Promise<void>;
  rememberUpdateState?(updateState: GoalProgressUpdateState | null): void;
  reconnect?(): Promise<string | undefined>;
  recoverTargetThreadId?(targetId: string): Promise<string | null | undefined>;
  recoverVisibleTargets?(): Promise<
    readonly { readonly targetId: string; readonly threadId: string | null }[]
  >;
  recoverVisibleThreadId?(): Promise<string | undefined>;
  setTargetThread?(targetId: string, threadId: string | null): Promise<void>;
  setUpdateState?(updateState: GoalProgressUpdateState | null): Promise<void>;
  setUiPreference?(uiPreference: GoalProgressUiPreference): Promise<void>;
  close?(options?: ViewModelPublisherCloseOptions): Promise<void> | void;
}

export interface ViewModelPublisherCloseOptions {
  readonly preservePage?: boolean;
}

interface TargetDeliveryState {
  readonly targetId: string;
  threadId: string | null;
  deliveredFingerprint: string | undefined;
}

interface ThreadSnapshot {
  readonly viewModel: GoalProgressViewModel;
  readonly fingerprint: string;
}

function viewModelFingerprint(viewModel: GoalProgressViewModel): string {
  return JSON.stringify(viewModel);
}

export class ViewModelPublisher {
  #sink: ViewModelPublisherSink | undefined;
  #currentThreadId: string | undefined;
  #latestViewModel: GoalProgressViewModel | undefined;
  #latestFingerprint: string | undefined;
  #deliveredFingerprint: string | undefined;
  #latestUpdateState: GoalProgressUpdateState | null = null;
  #clearRequired = false;
  readonly #targetDelivery = new Map<string, TargetDeliveryState>();
  readonly #threadSnapshots = new Map<string, ThreadSnapshot>();
  #queue: Promise<void> = Promise.resolve();

  constructor(sink?: ViewModelPublisherSink) {
    this.#sink = sink;
  }

  get currentThreadId(): string | undefined {
    return this.#currentThreadId;
  }

  get currentRevision(): number | undefined {
    return this.#latestViewModel?.revision;
  }

  get currentViewModel(): GoalProgressViewModel | undefined {
    return this.#latestViewModel;
  }

  get hasPublishedViewModel(): boolean {
    return this.#targetAware()
      ? this.#threadSnapshots.size > 0
      : this.#latestViewModel !== undefined;
  }

  get currentUpdateState(): GoalProgressUpdateState | null {
    return this.#latestUpdateState;
  }

  get deliveryCurrent(): boolean {
    return (
      this.#latestFingerprint !== undefined &&
      this.#latestFingerprint === this.#deliveredFingerprint
    );
  }

  get visibleThreadAwarenessAvailable(): boolean {
    return (
      this.#sink?.recoverVisibleTargets !== undefined ||
      this.#sink?.recoverVisibleThreadId !== undefined
    );
  }

  get multiTargetAwarenessAvailable(): boolean {
    return this.#targetAware();
  }

  get hasCurrentDelivery(): boolean {
    if (!this.#targetAware()) {
      return this.deliveryCurrent;
    }
    return [...this.#targetDelivery.keys()].some((targetId) =>
      this.deliveryCurrentForTarget(targetId),
    );
  }

  targetIdsForThread(threadId: string): string[] {
    return [...this.#targetDelivery.values()]
      .filter((target) => target.threadId === threadId)
      .map((target) => target.targetId)
      .sort();
  }

  hasTarget(targetId: string): boolean {
    return (this.#sink?.hasTarget?.(targetId) ?? false) || this.#targetDelivery.has(targetId);
  }

  deliveryCurrentForTarget(targetId: string): boolean {
    const target = this.#targetDelivery.get(targetId);
    if (!target?.threadId) {
      return false;
    }
    return (
      target.deliveredFingerprint !== undefined &&
      target.deliveredFingerprint === this.#threadSnapshots.get(target.threadId)?.fingerprint
    );
  }

  currentRevisionForTarget(targetId: string): number | undefined {
    const threadId = this.#targetDelivery.get(targetId)?.threadId;
    return threadId ? this.#threadSnapshots.get(threadId)?.viewModel.revision : undefined;
  }

  currentViewModelForTarget(targetId: string): GoalProgressViewModel | undefined {
    const threadId = this.#targetDelivery.get(targetId)?.threadId;
    return threadId ? this.#threadSnapshots.get(threadId)?.viewModel : undefined;
  }

  currentThreadIdForTarget(targetId: string): string | null | undefined {
    return this.#targetDelivery.get(targetId)?.threadId;
  }

  async recoverTargetThreadId(targetId: string): Promise<string | null | undefined> {
    let recovered: string | null | undefined;
    await this.#enqueue(async () => {
      recovered = await this.#sink?.recoverTargetThreadId?.(targetId);
    });
    return recovered;
  }

  async initialize(): Promise<void> {
    return this.#enqueue(async () => {
      if (!this.#sink) {
        return;
      }
      if (this.#targetAware()) {
        await this.#recoverTargets();
        return;
      }
      this.#clearRequired = true;
      await this.#clearSink();
    });
  }

  async recoverVisibleTargets(): Promise<
    readonly { readonly targetId: string; readonly threadId: string | null }[]
  > {
    let recovered: readonly { readonly targetId: string; readonly threadId: string | null }[] = [];
    await this.#enqueue(async () => {
      recovered = await this.#recoverTargets();
    });
    return recovered;
  }

  async recoverVisibleThreadId(): Promise<string | undefined> {
    if (this.#targetAware()) {
      return (
        (await this.recoverVisibleTargets()).find((target) => target.threadId)?.threadId ??
        undefined
      );
    }
    let recovered: string | undefined;
    await this.#enqueue(async () => {
      try {
        recovered = await this.#sink?.recoverVisibleThreadId?.();
      } catch {
        recovered = undefined;
      }
    });
    return recovered;
  }

  async reconnect(): Promise<string | undefined> {
    if (this.#targetAware()) {
      return (
        (await this.reconnectTargets()).find((target) => target.threadId)?.threadId ?? undefined
      );
    }
    let recovered: string | undefined;
    await this.#enqueue(async () => {
      this.#deliveredFingerprint = undefined;
      const reconnect = this.#sink?.reconnect;
      if (!reconnect) {
        return;
      }
      const sink = this.#sink;
      if (!sink) {
        return;
      }
      try {
        recovered = await reconnect.call(sink);
        this.#clearRequired = false;
      } catch {
        recovered = undefined;
        return;
      }
      try {
        await sink.setUpdateState?.(this.#latestUpdateState);
      } catch {
        // Update UI transport cannot block Renderer recovery.
      }
    });
    return recovered;
  }

  async reconnectTargets(): Promise<
    readonly { readonly targetId: string; readonly threadId: string | null }[]
  > {
    let recovered: readonly { readonly targetId: string; readonly threadId: string | null }[] = [];
    await this.#enqueue(async () => {
      this.#targetDelivery.clear();
      this.#threadSnapshots.clear();
      const reconnect = this.#sink?.reconnect;
      if (reconnect) {
        await reconnect.call(this.#sink);
      }
      recovered = await this.#recoverTargets();
      try {
        await this.#sink?.setUpdateState?.(this.#latestUpdateState);
      } catch {
        // Update UI transport cannot block Renderer recovery.
      }
    });
    return recovered;
  }

  async markDeliveryStale(): Promise<void> {
    return this.#enqueue(async () => {
      this.#deliveredFingerprint = undefined;
    });
  }

  async handleDisconnect(code: string): Promise<void> {
    return this.#enqueue(async () => {
      this.#deliveredFingerprint = undefined;
      await this.#sink?.handleDisconnect?.(code);
    });
  }

  async handleTargetDisconnect(targetId: string, code: string): Promise<void> {
    return this.#enqueue(async () => {
      if (!this.hasTarget(targetId)) {
        throw new Error("RENDERER_TARGET_UNKNOWN");
      }
      this.#targetDelivery.delete(targetId);
      if (this.#sink?.hasTarget?.(targetId) !== false) {
        await this.#sink?.handleTargetDisconnect?.(targetId, code);
      }
    });
  }

  async activateTarget(targetId: string, threadId: string | null): Promise<void> {
    return this.#enqueue(async () => {
      if (!this.hasTarget(targetId)) {
        throw new Error("RENDERER_TARGET_UNKNOWN");
      }
      const existing = this.#targetDelivery.get(targetId);
      if (existing?.threadId === threadId) {
        return;
      }
      await this.#sink?.setTargetThread?.(targetId, threadId);
      const target: TargetDeliveryState = {
        targetId,
        threadId,
        deliveredFingerprint: undefined,
      };
      this.#targetDelivery.set(targetId, target);
      if (!threadId) {
        return;
      }
      const snapshot = this.#threadSnapshots.get(threadId);
      if (snapshot) {
        await this.#deliverTarget(target, snapshot);
      }
    });
  }

  async activateThread(threadId: string): Promise<void> {
    if (this.#targetAware()) {
      throw new Error("RENDERER_TARGET_ID_REQUIRED");
    }
    return this.#enqueue(async () => {
      if (!threadId) {
        throw new Error("GOAL_PROGRESS_PUBLISHER_THREAD_REQUIRED");
      }
      if (threadId === this.#currentThreadId) {
        return;
      }
      const hadCurrentThread = this.#currentThreadId !== undefined;
      this.#latestViewModel = undefined;
      this.#latestFingerprint = undefined;
      this.#deliveredFingerprint = undefined;
      this.#clearRequired = hadCurrentThread;
      if (hadCurrentThread) {
        await this.#clearSink();
      }
      this.#currentThreadId = threadId;
    });
  }

  async publish(threadId: string, viewModel: GoalProgressViewModel): Promise<void> {
    return this.#enqueue(async () => {
      if (this.#targetAware()) {
        const snapshot = {
          viewModel,
          fingerprint: viewModelFingerprint(viewModel),
        } satisfies ThreadSnapshot;
        this.#threadSnapshots.set(threadId, snapshot);
        for (const target of this.#targetDelivery.values()) {
          if (target.threadId === threadId) {
            await this.#deliverTarget(target, snapshot);
          }
        }
        return;
      }
      if (threadId !== this.#currentThreadId) {
        return;
      }
      const fingerprint = viewModelFingerprint(viewModel);
      this.#latestViewModel = viewModel;
      this.#latestFingerprint = fingerprint;
      if (!this.#sink || fingerprint === this.#deliveredFingerprint) {
        return;
      }
      if (this.#clearRequired) {
        await this.#clearSink();
      }
      if (!this.#sink || this.#clearRequired) {
        return;
      }
      try {
        await this.#sink.publish(viewModel);
        this.#deliveredFingerprint = fingerprint;
      } catch {
        this.#deliveredFingerprint = undefined;
      }
    });
  }

  async setSink(sink?: ViewModelPublisherSink): Promise<void> {
    return this.#enqueue(async () => {
      this.#sink = sink;
      this.#targetDelivery.clear();
      this.#threadSnapshots.clear();
      this.#deliveredFingerprint = undefined;
      if (!sink) {
        return;
      }
      if (this.#targetAware()) {
        await this.#recoverTargets();
        try {
          await sink.setUpdateState?.(this.#latestUpdateState);
        } catch {
          // Update UI transport cannot block Renderer recovery.
        }
        return;
      }
      this.#clearRequired = true;
      await this.#clearSink();
      try {
        await sink.setUpdateState?.(this.#latestUpdateState);
      } catch {
        // Update UI transport cannot block the current Goal snapshot.
      }
      if (!this.#clearRequired && this.#latestViewModel && this.#latestFingerprint) {
        try {
          await sink.publish(this.#latestViewModel);
          this.#deliveredFingerprint = this.#latestFingerprint;
        } catch {
          this.#deliveredFingerprint = undefined;
        }
      }
    });
  }

  async setUiPreference(uiPreference: GoalProgressUiPreference): Promise<void> {
    return this.#enqueue(async () => {
      try {
        await this.#sink?.setUiPreference?.(uiPreference);
      } catch {
        // UI preference transport cannot block Store or MCP.
      }
    });
  }

  async setUpdateState(updateState: GoalProgressUpdateState | null): Promise<void> {
    return this.#enqueue(async () => {
      if (
        updateState === null ||
        classifyGoalProgressUpdateState(updateState, this.#latestUpdateState) !== "accept"
      ) {
        return;
      }
      this.#latestUpdateState = updateState;
      try {
        await this.#sink?.setUpdateState?.(updateState);
      } catch {
        // Update UI transport cannot block Goal tracking.
      }
    });
  }

  rememberUpdateState(updateState: GoalProgressUpdateState | null): void {
    if (
      updateState === null ||
      classifyGoalProgressUpdateState(updateState, this.#latestUpdateState) !== "accept"
    ) {
      return;
    }
    this.#latestUpdateState = updateState;
    this.#sink?.rememberUpdateState?.(updateState);
  }

  async clear(threadId: string): Promise<void> {
    return this.#enqueue(async () => {
      if (this.#targetAware()) {
        this.#threadSnapshots.delete(threadId);
        for (const target of this.#targetDelivery.values()) {
          if (target.threadId !== threadId) {
            continue;
          }
          await this.#sink?.clearTarget?.(target.targetId);
          target.deliveredFingerprint = undefined;
        }
        return;
      }
      if (threadId !== this.#currentThreadId) {
        return;
      }
      this.#latestViewModel = undefined;
      this.#latestFingerprint = undefined;
      this.#deliveredFingerprint = undefined;
      this.#clearRequired = true;
      await this.#clearSink();
    });
  }

  async close(options?: ViewModelPublisherCloseOptions): Promise<void> {
    return this.#enqueue(async () => {
      const sink = this.#sink;
      this.#sink = undefined;
      this.#targetDelivery.clear();
      this.#threadSnapshots.clear();
      this.#deliveredFingerprint = undefined;
      try {
        await sink?.close?.(options);
      } catch {
        // Renderer transport shutdown cannot block Helper shutdown.
      }
    });
  }

  #enqueue(work: () => Promise<void>): Promise<void> {
    const run = this.#queue.then(work, work);
    this.#queue = run.catch(() => undefined);
    return run;
  }

  async #clearSink(): Promise<void> {
    if (!this.#sink) {
      return;
    }
    try {
      await this.#sink.clear();
      this.#clearRequired = false;
    } catch {
      this.#clearRequired = true;
    }
  }

  #targetAware(): boolean {
    return (
      this.#sink?.publishTarget !== undefined &&
      this.#sink.clearTarget !== undefined &&
      this.#sink.setTargetThread !== undefined
    );
  }

  async #recoverTargets(): Promise<
    readonly { readonly targetId: string; readonly threadId: string | null }[]
  > {
    const recovered =
      (await this.#sink?.recoverVisibleTargets?.()) ??
      (this.#sink?.recoverVisibleThreadId
        ? [
            {
              targetId: "legacy-renderer",
              threadId: (await this.#sink.recoverVisibleThreadId()) ?? null,
            },
          ]
        : []);
    for (const target of recovered) {
      this.#targetDelivery.set(target.targetId, {
        targetId: target.targetId,
        threadId: target.threadId,
        deliveredFingerprint: undefined,
      });
    }
    return recovered;
  }

  async #deliverTarget(target: TargetDeliveryState, snapshot: ThreadSnapshot): Promise<void> {
    if (!this.#sink?.publishTarget || target.deliveredFingerprint === snapshot.fingerprint) {
      return;
    }
    try {
      await this.#sink.publishTarget(target.targetId, snapshot.viewModel);
      target.deliveredFingerprint = snapshot.fingerprint;
    } catch {
      target.deliveredFingerprint = undefined;
    }
  }
}
