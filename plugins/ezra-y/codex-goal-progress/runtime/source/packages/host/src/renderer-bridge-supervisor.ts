import type { GoalProgressRendererBridgeDoctor } from "../../codex-adapter/src/index.js";
import {
  classifyGoalProgressUpdateState,
  DEFAULT_GOAL_PROGRESS_UI_PREFERENCE,
  type GoalProgressUiPreference,
  type GoalProgressUpdateState,
  type GoalProgressViewModel,
} from "../../contracts/src/index.js";
import type { ViewModelPublisherSink } from "./view-model-publisher.js";

export const RENDERER_BRIDGE_RECONNECT_DELAYS_MS = [1_000, 2_000, 5_000, 10_000, 30_000] as const;

export interface RendererBridgeSupervisorConnection extends ViewModelPublisherSink {
  readonly visibleThreadLifecycleId?: string;
  doctor(expectedThreadId?: string): Promise<GoalProgressRendererBridgeDoctor>;
  close(): Promise<void>;
}

export interface RendererBridgeSupervisorOptions {
  readonly connector: () => Promise<RendererBridgeSupervisorConnection | undefined>;
  readonly now?: () => number;
  readonly reconnectDelaysMs?: readonly number[];
}

type BridgeOperation = "clear" | "doctor" | "preference" | "publish" | "update-state";

interface ConnectedBridge {
  readonly bridge: RendererBridgeSupervisorConnection;
  readonly newlyConnected: boolean;
}

function stableErrorCode(error: unknown): string {
  const value = error instanceof Error ? error.message : String(error);
  return /^[A-Z][A-Z0-9_]{2,127}/u.exec(value)?.[0] ?? "RENDERER_BRIDGE_UNAVAILABLE";
}

function retryableBridgeError(code: string): boolean {
  const fatalCodes = [
    "GOAL_PROGRESS_CDP_NON_LOOPBACK_LISTENER",
    "GOAL_PROGRESS_CDP_LISTENER_PROCESS_MISMATCH",
    "GOAL_PROGRESS_CDP_MAIN_EXECUTABLE_MISMATCH",
    "GOAL_PROGRESS_CDP_RUNTIME_APP_MISMATCH",
    "GOAL_PROGRESS_CDP_RUNTIME_OWNERSHIP_CHANGED",
    "GOAL_PROGRESS_CDP_RENDERER_AMBIGUOUS",
    "GOAL_PROGRESS_CDP_UNSAFE_PAGE_URL",
    "GOAL_PROGRESS_CDP_UNSAFE_WEBSOCKET_URL",
    "GOAL_PROGRESS_CODEX_APP_BUNDLE_ID_MISMATCH",
    "GOAL_PROGRESS_CODEX_APP_SIGNATURE_INVALID",
    "GOAL_PROGRESS_CODEX_APP_SIGNED_IDENTIFIER_MISMATCH",
    "GOAL_PROGRESS_CODEX_APP_TEAM_ID_MISMATCH",
    "GOAL_PROGRESS_RENDERER_BUNDLE_NOT_FOUND",
  ];
  return (
    !fatalCodes.includes(code) &&
    !code.startsWith("GOAL_PROGRESS_RENDERER_BUNDLE_") &&
    !code.startsWith("GOAL_PROGRESS_CODEX_APP_")
  );
}

export class RendererBridgeSupervisor implements ViewModelPublisherSink {
  readonly #connector: RendererBridgeSupervisorOptions["connector"];
  readonly #now: () => number;
  readonly #reconnectDelaysMs: readonly number[];
  #bridge: RendererBridgeSupervisorConnection | undefined;
  #uiPreference: GoalProgressUiPreference = DEFAULT_GOAL_PROGRESS_UI_PREFERENCE;
  #updateState: GoalProgressUpdateState | null = null;
  #nextAttemptAt = 0;
  #backoffIndex = 0;
  #lastErrorCode: string | null = null;
  #recoveredVisibleThreadId: string | undefined;
  #blocked = false;
  #closed = false;
  #queue: Promise<void> = Promise.resolve();

  constructor(options: RendererBridgeSupervisorOptions) {
    this.#connector = options.connector;
    this.#now = options.now ?? Date.now;
    this.#reconnectDelaysMs = options.reconnectDelaysMs ?? RENDERER_BRIDGE_RECONNECT_DELAYS_MS;
  }

  get lastErrorCode(): string | null {
    return this.#lastErrorCode;
  }

  get currentUpdateState(): GoalProgressUpdateState | null {
    return this.#updateState;
  }

  async clear(): Promise<void> {
    return this.#enqueue(() => this.#requireOperation("clear", (bridge) => bridge.clear()));
  }

  async handleDisconnect(code: string): Promise<void> {
    return this.#enqueue(async () => {
      await this.#dropBridge();
      if (retryableBridgeError(code)) {
        this.#recordRetryableFailure(code);
        return;
      }
      this.#blocked = true;
      this.#lastErrorCode = code;
    });
  }

  async publish(viewModel: GoalProgressViewModel): Promise<void> {
    return this.#enqueue(() =>
      this.#requireOperation("publish", (bridge) => bridge.publish(viewModel)),
    );
  }

  async recoverVisibleThreadId(): Promise<string | undefined> {
    let recovered: string | undefined;
    await this.#enqueue(async () => {
      const connected = await this.#ensureConnected(false);
      if (!connected) {
        throw new Error(this.#lastErrorCode ?? "RENDERER_BRIDGE_UNAVAILABLE");
      }
      recovered = this.#recoveredVisibleThreadId;
      this.#recoveredVisibleThreadId = undefined;
      if (recovered === undefined) {
        recovered = await connected.bridge.recoverVisibleThreadId?.();
      }
    });
    return recovered;
  }

  async reconnect(): Promise<string | undefined> {
    let recovered: string | undefined;
    await this.#enqueue(async () => {
      await this.#dropBridge();
      this.#blocked = false;
      this.#lastErrorCode = null;
      this.#nextAttemptAt = 0;
      this.#backoffIndex = 0;
      const connected = await this.#ensureConnected(true);
      if (!connected) {
        throw new Error(this.#lastErrorCode ?? "RENDERER_BRIDGE_UNAVAILABLE");
      }
      recovered = this.#recoveredVisibleThreadId;
      this.#recoveredVisibleThreadId = undefined;
      if (recovered === undefined) {
        recovered = await connected.bridge.recoverVisibleThreadId?.();
      }
    });
    return recovered;
  }

  async setUiPreference(uiPreference: GoalProgressUiPreference): Promise<void> {
    return this.#enqueue(async () => {
      this.#uiPreference = uiPreference;
      await this.#requireOperation(
        "preference",
        (bridge) => bridge.setUiPreference?.(uiPreference) ?? Promise.resolve(),
      );
    });
  }

  async setUpdateState(updateState: GoalProgressUpdateState | null): Promise<void> {
    return this.#enqueue(async () => {
      if (
        updateState === null ||
        classifyGoalProgressUpdateState(updateState, this.#updateState) !== "accept"
      ) {
        return;
      }
      this.#updateState = updateState;
      await this.#requireOperation(
        "update-state",
        (bridge) => bridge.setUpdateState?.(updateState) ?? Promise.resolve(),
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
    let result: GoalProgressRendererBridgeDoctor | undefined;
    await this.#enqueue(async () => {
      await this.#requireOperation("doctor", async (bridge) => {
        result = await bridge.doctor(expectedThreadId);
      });
    });
    if (result) {
      return result;
    }
    throw new Error(this.#lastErrorCode ?? "RENDERER_BRIDGE_UNAVAILABLE");
  }

  async close(): Promise<void> {
    return this.#enqueue(async () => {
      this.#closed = true;
      await this.#dropBridge();
    });
  }

  #enqueue(work: () => Promise<void>): Promise<void> {
    const run = this.#queue.then(work, work);
    this.#queue = run.catch(() => undefined);
    return run;
  }

  async #requireOperation(
    operation: BridgeOperation,
    work: (bridge: RendererBridgeSupervisorConnection) => Promise<void>,
  ): Promise<void> {
    if (!(await this.#perform(operation, work))) {
      throw new Error(this.#lastErrorCode ?? "RENDERER_BRIDGE_UNAVAILABLE");
    }
  }

  async #perform(
    operation: BridgeOperation,
    work: (bridge: RendererBridgeSupervisorConnection) => Promise<void>,
  ): Promise<boolean> {
    const connected = await this.#ensureConnected(false);
    if (!connected) {
      return false;
    }
    if (
      connected.newlyConnected &&
      (operation === "clear" || operation === "preference" || operation === "update-state")
    ) {
      return true;
    }
    try {
      await work(connected.bridge);
      return true;
    } catch (error) {
      const code = stableErrorCode(error);
      await this.#dropBridge();
      if (!retryableBridgeError(code)) {
        this.#blocked = true;
        this.#lastErrorCode = code;
        return false;
      }
      this.#recordRetryableFailure(code);
    }

    const replacement = await this.#ensureConnected(true);
    if (!replacement) {
      return false;
    }
    if (operation === "clear" || operation === "preference" || operation === "update-state") {
      return true;
    }
    try {
      await work(replacement.bridge);
      return true;
    } catch (error) {
      const code = stableErrorCode(error);
      await this.#dropBridge();
      if (retryableBridgeError(code)) {
        this.#recordRetryableFailure(code);
      } else {
        this.#blocked = true;
        this.#lastErrorCode = code;
      }
      return false;
    }
  }

  async #ensureConnected(force: boolean): Promise<ConnectedBridge | null> {
    if (this.#bridge) {
      return { bridge: this.#bridge, newlyConnected: false };
    }
    if (this.#closed || this.#blocked || (!force && this.#now() < this.#nextAttemptAt)) {
      return null;
    }
    let candidate: RendererBridgeSupervisorConnection | undefined;
    try {
      candidate = await this.#connector();
    } catch (error) {
      const code = stableErrorCode(error);
      if (retryableBridgeError(code)) {
        this.#recordRetryableFailure(code);
      } else {
        this.#blocked = true;
        this.#lastErrorCode = code;
      }
      return null;
    }
    if (!candidate) {
      this.#recordRetryableFailure("RENDERER_BRIDGE_UNAVAILABLE");
      return null;
    }
    try {
      this.#recoveredVisibleThreadId = await candidate.recoverVisibleThreadId?.();
      await candidate.clear();
      await candidate.setUiPreference?.(this.#uiPreference);
      await candidate.setUpdateState?.(this.#updateState).catch(() => undefined);
    } catch (error) {
      await candidate.close().catch(() => undefined);
      const code = stableErrorCode(error);
      if (retryableBridgeError(code)) {
        this.#recordRetryableFailure(code);
      } else {
        this.#blocked = true;
        this.#lastErrorCode = code;
      }
      return null;
    }
    this.#bridge = candidate;
    this.#backoffIndex = 0;
    this.#nextAttemptAt = 0;
    this.#lastErrorCode = null;
    return { bridge: candidate, newlyConnected: true };
  }

  async #dropBridge(): Promise<void> {
    const bridge = this.#bridge;
    this.#bridge = undefined;
    this.#recoveredVisibleThreadId = undefined;
    try {
      await bridge?.close();
    } catch {
      // Closing a stale Renderer transport must not block Helper recovery.
    }
  }

  #recordRetryableFailure(code: string): void {
    this.#lastErrorCode = code;
    const index = Math.min(this.#backoffIndex, Math.max(0, this.#reconnectDelaysMs.length - 1));
    const delay = this.#reconnectDelaysMs[index] ?? 30_000;
    this.#backoffIndex = Math.min(this.#backoffIndex + 1, this.#reconnectDelaysMs.length);
    this.#nextAttemptAt = this.#now() + delay;
  }
}
