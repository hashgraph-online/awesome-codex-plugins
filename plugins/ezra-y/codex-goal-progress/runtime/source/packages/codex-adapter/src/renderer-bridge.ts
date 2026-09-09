import { randomBytes } from "node:crypto";
import { z } from "zod";
import {
  classifyGoalProgressUpdateState,
  DEFAULT_GOAL_PROGRESS_UI_PREFERENCE,
  GOAL_PROGRESS_UI_INTENT_BINDING_PREFIX,
  GOAL_PROGRESS_UI_INTENT_MAX_BYTES,
  GOAL_PROGRESS_UI_INTENT_MAX_PER_SECOND,
  GOAL_PROGRESS_UI_INTENT_PROTOCOL_VERSION,
  GOAL_PROGRESS_UPDATE_INTENT_MAX_BYTES,
  GoalContractIdSchema,
  type GoalProgressUiIntent,
  GoalProgressUiIntentSchema,
  type GoalProgressUiPreference,
  type GoalProgressUpdateIntent,
  GoalProgressUpdateIntentEnvelopeSchema,
  type GoalProgressUpdateState,
  GoalProgressUpdateStateSchema,
  type GoalProgressViewModel,
} from "../../contracts/src/index.js";
import type { CodexHostPlatform } from "./anchor-adapter.js";
import {
  type CdpCommandSender,
  CdpProtocolClient,
  type CdpProtocolClientOptions,
  type CodexCdpTarget,
  discoverCodexCdp,
  evaluateGoalProgressPageBundle,
  type FetchLike,
  installGoalProgressPageBundle,
  installGoalProgressVisibleThreadWatcher,
  invokeGoalProgressPageApi,
  readGoalProgressVisibleThreadId,
  refreshGoalProgressVisibleThreadWatcher,
} from "./cdp.js";
import type { GoalProgressRendererBundle } from "./renderer-bundle.js";

export interface CdpEventSource {
  onEvent(method: string, listener: (params: unknown) => void): () => void;
}

export interface CdpFailureSource {
  onFailure(listener: (error: Error) => void): () => void;
}

export interface GoalProgressRendererBridgeOptions {
  readonly sender: CdpCommandSender & Partial<CdpEventSource & CdpFailureSource>;
  readonly bundle: GoalProgressRendererBundle;
  readonly platform: CodexHostPlatform;
  readonly appVersion: string;
  readonly closeSender?: () => Promise<void>;
  readonly onUiIntent?: (
    threadId: string,
    intent: GoalProgressUiIntent,
  ) => Promise<GoalProgressRendererUiIntentResult>;
  readonly onUpdateIntent?: (
    threadId: string,
    intent: GoalProgressUpdateIntent,
  ) => Promise<GoalProgressRendererUpdateIntentResult>;
  readonly onVisibleThreadChange?: (
    threadId: string | null,
    sequence?: number,
    lifecycleId?: string,
  ) => Promise<void> | void;
  readonly onDisconnected?: (code: string) => Promise<void> | void;
  readonly environment?: {
    readonly appPath?: string;
    readonly appSignatureValid?: boolean;
    readonly cdpPort?: number;
    readonly cdpLoopback?: boolean;
    readonly targetUrl?: string;
  };
}

export interface GoalProgressRendererUiIntentResult {
  readonly viewModel: GoalProgressViewModel;
  readonly uiPreference: GoalProgressUiPreference;
  readonly dismissed?: boolean;
}

export interface GoalProgressRendererUpdateIntentResult {
  readonly updateState: GoalProgressUpdateState;
}

export interface ConnectGoalProgressRendererBridgeOptions
  extends Omit<GoalProgressRendererBridgeOptions, "sender" | "closeSender"> {
  readonly port: number;
  readonly fetchImpl?: FetchLike;
  readonly clientOptions?: CdpProtocolClientOptions;
}

export interface ConnectedGoalProgressRendererBridge {
  readonly bridge: GoalProgressRendererBridge;
  readonly targetId: string;
}

export interface GoalProgressRendererBridgeDoctor {
  readonly appPath: string | null;
  readonly appSignatureValid: boolean | null;
  readonly cdpPort: number | null;
  readonly cdpLoopback: boolean | null;
  readonly targetUrl: string | null;
  readonly adapterId: string | null;
  readonly capabilitySupported: boolean | null;
  readonly capabilityReason: string | null;
  readonly anchorMatched: boolean | null;
  readonly displayMode: "native" | "fallback" | "hidden" | null;
  readonly nativeAnchorMatched: boolean | null;
  readonly componentVisible: boolean | null;
  readonly visibleThreadStatus: "matched" | "retained" | "unknown" | "mismatch" | null;
  readonly componentCount: number | null;
  readonly bundleReleaseVersion: string;
  readonly bundlePageHostVersion: number;
  readonly bundleSha256: string;
  readonly latestViewModelRevision: number | null;
  readonly currentThreadMatched: boolean | null;
  readonly lastErrorCode: string | null;
}

const GoalProgressPageMutationResultSchema = z
  .object({
    action: z.enum(["mounted", "updated", "unmounted", "none"]),
    reason: z.string().trim().min(1).max(128),
    hostCount: z.number().int().nonnegative(),
  })
  .passthrough();

export class GoalProgressRendererBridge {
  readonly #sender: CdpCommandSender & Partial<CdpEventSource>;
  readonly #bundle: GoalProgressRendererBundle;
  readonly #platform: CodexHostPlatform;
  readonly #appVersion: string;
  readonly #closeSender: (() => Promise<void>) | undefined;
  readonly #onUiIntent: GoalProgressRendererBridgeOptions["onUiIntent"];
  readonly #onUpdateIntent: GoalProgressRendererBridgeOptions["onUpdateIntent"];
  readonly #onVisibleThreadChange: GoalProgressRendererBridgeOptions["onVisibleThreadChange"];
  readonly #onDisconnected: GoalProgressRendererBridgeOptions["onDisconnected"];
  readonly #environment: GoalProgressRendererBridgeOptions["environment"];
  readonly #bridgeNonce = randomBytes(24).toString("base64url");
  readonly #bindingName = `${GOAL_PROGRESS_UI_INTENT_BINDING_PREFIX}${this.#bridgeNonce}`;
  readonly #visibleThreadBindingName = `__CODEX_GOAL_PROGRESS_VISIBLE_THREAD_${this.#bridgeNonce}`;
  readonly #unsubscribe: Array<() => void>;
  readonly #uiIntentTimestamps: number[] = [];
  #queue: Promise<void> = Promise.resolve();
  #latestViewModel: GoalProgressViewModel | undefined;
  #latestUpdateState: GoalProgressUpdateState | null = null;
  #uiPreference: GoalProgressUiPreference = DEFAULT_GOAL_PROGRESS_UI_PREFERENCE;
  #bindingRegistered = false;
  #visibleThreadWatcherRegistered = false;
  #visibleThreadLifecycleId = randomBytes(24).toString("base64url");
  #scriptRegistered = false;
  #installed = false;
  #configured = false;
  #lastErrorCode: string | null = null;

  constructor(options: GoalProgressRendererBridgeOptions) {
    this.#sender = options.sender;
    this.#bundle = options.bundle;
    this.#platform = options.platform;
    this.#appVersion = options.appVersion;
    this.#closeSender = options.closeSender;
    this.#onUiIntent = options.onUiIntent;
    this.#onUpdateIntent = options.onUpdateIntent;
    this.#onVisibleThreadChange = options.onVisibleThreadChange;
    this.#onDisconnected = options.onDisconnected;
    this.#environment = options.environment;
    this.#unsubscribe = [
      options.sender.onEvent?.("Page.loadEventFired", () => {
        void this.#enqueue(async () => {
          if (!this.#scriptRegistered) {
            return undefined;
          }
          this.#installed = false;
          this.#configured = false;
          if (this.#onVisibleThreadChange && this.#visibleThreadWatcherRegistered) {
            this.#visibleThreadLifecycleId = randomBytes(24).toString("base64url");
            await refreshGoalProgressVisibleThreadWatcher(
              this.#sender,
              this.#visibleThreadBindingName,
              this.#bridgeNonce,
              this.#visibleThreadLifecycleId,
            );
          }
          await this.#ensureInstalled();
          if (this.#latestViewModel) {
            await this.#mount(this.#latestViewModel);
          }
          if (!this.#onVisibleThreadChange) {
            return undefined;
          }
          return (await readGoalProgressVisibleThreadId(this.#sender)) ?? null;
        })
          .then((threadId) => {
            if (!this.#onVisibleThreadChange || threadId === undefined) {
              return;
            }
            try {
              void Promise.resolve(
                this.#onVisibleThreadChange(threadId, undefined, this.#visibleThreadLifecycleId),
              ).catch(() => undefined);
            } catch {
              // Page load only schedules Helper restore after the Bridge queue is free.
            }
          })
          .catch(() => undefined);
      }),
      options.sender.onEvent?.("Runtime.bindingCalled", (params) => {
        void this.#enqueue(async () => {
          if (await this.#handleVisibleThreadSignal(params)) {
            return;
          }
          if (await this.#handleUpdateIntent(params)) {
            return;
          }
          await this.#handleUiIntent(params);
        }).catch(() => undefined);
      }),
      options.sender.onFailure?.((error) => {
        try {
          void Promise.resolve(this.#onDisconnected?.(stableBridgeErrorCode(error))).catch(
            () => undefined,
          );
        } catch {
          // The transport is already closed; reporting cannot delay cleanup.
        }
      }),
    ].filter((unsubscribe): unsubscribe is () => void => unsubscribe !== undefined);
  }

  get currentUpdateState(): GoalProgressUpdateState | null {
    return this.#latestUpdateState;
  }

  get visibleThreadLifecycleId(): string {
    return this.#visibleThreadLifecycleId;
  }

  async publish(viewModel: GoalProgressViewModel): Promise<void> {
    return this.#enqueue(async () => {
      this.#latestViewModel = viewModel;
      await this.#ensureInstalled();
      if (this.#configured) {
        const result = GoalProgressPageMutationResultSchema.parse(
          await invokeGoalProgressPageApi(this.#sender, "update", viewModel),
        );
        if (result.reason === "ok" && result.hostCount === 1) {
          return;
        }
        if (result.reason === "not-configured") {
          this.#configured = false;
          await this.#mount(viewModel);
          return;
        }
        throw new Error("GOAL_PROGRESS_PAGE_HOST_UPDATE_FAILED");
      }
      await this.#mount(viewModel);
    });
  }

  async recoverVisibleThreadId(): Promise<string | undefined> {
    return this.#enqueue(() => readGoalProgressVisibleThreadId(this.#sender));
  }

  async clear(): Promise<void> {
    return this.#enqueue(async () => {
      this.#latestViewModel = undefined;
      await this.#ensureInstalled();
      await invokeGoalProgressPageApi(this.#sender, "unmount");
      this.#configured = false;
    });
  }

  async setUpdateState(updateState: GoalProgressUpdateState | null): Promise<void> {
    return this.#enqueue(async () => {
      const incoming = GoalProgressUpdateStateSchema.nullable().parse(updateState);
      if (
        incoming === null ||
        classifyGoalProgressUpdateState(incoming, this.#latestUpdateState) !== "accept"
      ) {
        return;
      }
      this.#latestUpdateState = incoming;
      await this.#writeLatestUpdateStateToPage();
    });
  }

  async setUiPreference(uiPreference: GoalProgressUiPreference): Promise<void> {
    return this.#enqueue(async () => {
      this.#uiPreference = uiPreference;
    });
  }

  async waitForIdle(): Promise<void> {
    await this.#queue;
  }

  async doctor(expectedThreadId?: string): Promise<GoalProgressRendererBridgeDoctor> {
    await this.waitForIdle();
    let health: Record<string, unknown> | null = null;
    try {
      const value = await invokeGoalProgressPageApi(this.#sender, "health");
      health =
        value !== null && typeof value === "object" ? (value as Record<string, unknown>) : null;
    } catch (error) {
      this.#lastErrorCode = stableBridgeErrorCode(error);
    }
    const runtime =
      health?.runtime !== null && typeof health?.runtime === "object"
        ? (health.runtime as Record<string, unknown>)
        : null;
    const reason = typeof health?.reason === "string" ? health.reason : null;
    const adapterId = typeof health?.adapterId === "string" ? health.adapterId : null;
    const displayMode =
      health?.displayMode === "native" ||
      health?.displayMode === "fallback" ||
      health?.displayMode === "hidden"
        ? health.displayMode
        : null;
    const nativeAnchorMatched =
      typeof health?.nativeAnchorMatched === "boolean" ? health.nativeAnchorMatched : null;
    const componentVisible =
      typeof health?.componentVisible === "boolean" ? health.componentVisible : null;
    const visibleThreadStatus =
      health?.visibleThreadStatus === "matched" ||
      health?.visibleThreadStatus === "retained" ||
      health?.visibleThreadStatus === "unknown" ||
      health?.visibleThreadStatus === "mismatch"
        ? health.visibleThreadStatus
        : null;
    const viewModelRevision =
      typeof health?.viewModelRevision === "number" &&
      Number.isSafeInteger(health.viewModelRevision)
        ? health.viewModelRevision
        : null;
    const latest = this.#latestViewModel;
    return {
      appPath: this.#environment?.appPath ?? null,
      appSignatureValid: this.#environment?.appSignatureValid ?? null,
      cdpPort: this.#environment?.cdpPort ?? null,
      cdpLoopback: this.#environment?.cdpLoopback ?? null,
      targetUrl: this.#environment?.targetUrl ?? null,
      adapterId,
      capabilitySupported: reason === null ? null : reason === "ok",
      capabilityReason: reason,
      anchorMatched: nativeAnchorMatched,
      displayMode,
      nativeAnchorMatched,
      componentVisible,
      visibleThreadStatus,
      componentCount:
        typeof health?.hostCount === "number" && Number.isSafeInteger(health.hostCount)
          ? health.hostCount
          : null,
      bundleReleaseVersion: this.#bundle.manifest.releaseVersion,
      bundlePageHostVersion: this.#bundle.manifest.pageHostVersion,
      bundleSha256: this.#bundle.manifest.sha256,
      latestViewModelRevision: viewModelRevision,
      currentThreadMatched:
        expectedThreadId === undefined || !latest || visibleThreadStatus === null
          ? null
          : latest.sessionId === expectedThreadId &&
            (visibleThreadStatus === "matched" || visibleThreadStatus === "retained"),
      lastErrorCode:
        this.#lastErrorCode ??
        (typeof runtime?.lastFailureReason === "string"
          ? stableBridgeErrorCode(runtime.lastFailureReason)
          : null),
    };
  }

  async close(): Promise<void> {
    for (const unsubscribe of this.#unsubscribe) {
      unsubscribe();
    }
    await this.waitForIdle();
    await this.#closeSender?.();
  }

  async #mount(viewModel: GoalProgressViewModel): Promise<void> {
    const result = GoalProgressPageMutationResultSchema.parse(
      await invokeGoalProgressPageApi(this.#sender, "mount", {
        platform: this.#platform,
        appVersion: this.#appVersion,
        viewModel,
        updateState: this.#latestUpdateState,
        uiPreference: this.#uiPreference,
        ...(this.#onUiIntent || this.#onUpdateIntent
          ? {
              bridgeNonce: this.#bridgeNonce,
              bridgeBindingName: this.#bindingName,
            }
          : {}),
      }),
    );
    if (result.reason !== "ok" || result.hostCount !== 1) {
      throw new Error("GOAL_PROGRESS_PAGE_HOST_MOUNT_FAILED");
    }
    this.#configured = true;
  }

  async #ensureInstalled(): Promise<void> {
    if (this.#onVisibleThreadChange && !this.#visibleThreadWatcherRegistered) {
      await installGoalProgressVisibleThreadWatcher(
        this.#sender,
        this.#visibleThreadBindingName,
        this.#bridgeNonce,
        this.#visibleThreadLifecycleId,
      );
      this.#visibleThreadWatcherRegistered = true;
    }
    if ((this.#onUiIntent || this.#onUpdateIntent) && !this.#bindingRegistered) {
      await this.#sender.send("Runtime.enable");
      await this.#sender.send("Runtime.addBinding", {
        name: this.#bindingName,
      });
      this.#bindingRegistered = true;
    }
    if (this.#installed) {
      return;
    }
    if (this.#scriptRegistered) {
      await evaluateGoalProgressPageBundle(this.#sender, this.#bundle);
    } else {
      await installGoalProgressPageBundle(this.#sender, this.#bundle);
      this.#scriptRegistered = true;
    }
    this.#installed = true;
  }

  async #handleVisibleThreadSignal(params: unknown): Promise<boolean> {
    if (!this.#onVisibleThreadChange) {
      return false;
    }
    const binding = z
      .object({
        name: z.string(),
        payload: z.string(),
      })
      .passthrough()
      .safeParse(params);
    if (
      !binding.success ||
      binding.data.name !== this.#visibleThreadBindingName ||
      Buffer.byteLength(binding.data.payload) > 512
    ) {
      return false;
    }
    let payload: unknown;
    try {
      payload = JSON.parse(binding.data.payload);
    } catch {
      return true;
    }
    const signal = z
      .object({
        protocolVersion: z.literal(1),
        bridgeNonce: z.string().regex(/^[A-Za-z0-9_-]{32}$/u),
        lifecycleId: z
          .string()
          .regex(/^[A-Za-z0-9_-]{32}$/u)
          .optional(),
        type: z.literal("visibleThreadChanged"),
        threadId: z
          .string()
          .trim()
          .min(1)
          .max(256)
          .refine((value) => !value.startsWith("client-new-thread:"))
          .nullable(),
        sequence: z.number().int().positive().max(Number.MAX_SAFE_INTEGER).optional(),
      })
      .strict()
      .safeParse(payload);
    if (!signal.success || signal.data.bridgeNonce !== this.#bridgeNonce) {
      return true;
    }
    if (
      signal.data.lifecycleId !== undefined &&
      signal.data.lifecycleId !== this.#visibleThreadLifecycleId
    ) {
      return true;
    }
    try {
      void Promise.resolve(
        this.#onVisibleThreadChange(
          signal.data.threadId,
          signal.data.sequence,
          signal.data.lifecycleId ?? this.#visibleThreadLifecycleId,
        ),
      ).catch(() => undefined);
    } catch {
      // A page signal only schedules Helper work; it never owns the Bridge queue.
    }
    return true;
  }

  async #handleUiIntent(params: unknown): Promise<void> {
    if (!this.#onUiIntent) {
      return;
    }
    const binding = z
      .object({
        name: z.string(),
        payload: z.string(),
      })
      .passthrough()
      .safeParse(params);
    if (
      !binding.success ||
      binding.data.name !== this.#bindingName ||
      Buffer.byteLength(binding.data.payload) > GOAL_PROGRESS_UI_INTENT_MAX_BYTES
    ) {
      return;
    }
    let payload: unknown;
    try {
      payload = JSON.parse(binding.data.payload);
    } catch {
      return;
    }
    const envelope = z
      .object({
        protocolVersion: z.literal(GOAL_PROGRESS_UI_INTENT_PROTOCOL_VERSION),
        bridgeNonce: z.string().regex(/^[A-Za-z0-9_-]{32}$/u),
        contractId: GoalContractIdSchema,
        threadId: z.string().trim().min(1).max(256),
        userActivated: z.boolean(),
        intent: GoalProgressUiIntentSchema,
      })
      .strict()
      .safeParse(payload);
    const current = this.#latestViewModel;
    if (
      !envelope.success ||
      !current ||
      envelope.data.bridgeNonce !== this.#bridgeNonce ||
      envelope.data.contractId !== current.contractId ||
      envelope.data.threadId !== current.sessionId ||
      (envelope.data.intent.type === "requestDetach" && !envelope.data.userActivated)
    ) {
      return;
    }
    const now = Date.now();
    while (
      this.#uiIntentTimestamps[0] !== undefined &&
      this.#uiIntentTimestamps[0] <= now - 1_000
    ) {
      this.#uiIntentTimestamps.shift();
    }
    if (this.#uiIntentTimestamps.length >= GOAL_PROGRESS_UI_INTENT_MAX_PER_SECOND) {
      return;
    }
    this.#uiIntentTimestamps.push(now);
    const result = await this.#onUiIntent(envelope.data.threadId, envelope.data.intent);
    if (
      result.viewModel.contractId !== current.contractId ||
      result.viewModel.sessionId !== current.sessionId
    ) {
      return;
    }
    this.#latestViewModel = result.viewModel;
    this.#uiPreference = result.uiPreference;
    await this.#ensureInstalled();
    if (result.dismissed) {
      this.#latestViewModel = undefined;
      await invokeGoalProgressPageApi(this.#sender, "unmount");
      this.#configured = false;
      return;
    }
    await this.#mount(result.viewModel);
  }

  async #handleUpdateIntent(params: unknown): Promise<boolean> {
    if (!this.#onUpdateIntent) {
      return false;
    }
    const binding = z
      .object({
        name: z.string(),
        payload: z.string(),
      })
      .passthrough()
      .safeParse(params);
    if (!binding.success || binding.data.name !== this.#bindingName) {
      return false;
    }
    if (Buffer.byteLength(binding.data.payload) > GOAL_PROGRESS_UPDATE_INTENT_MAX_BYTES) {
      return true;
    }
    let payload: unknown;
    try {
      payload = JSON.parse(binding.data.payload);
    } catch {
      return true;
    }
    const envelope = GoalProgressUpdateIntentEnvelopeSchema.safeParse(payload);
    if (!envelope.success) {
      return false;
    }
    const current = this.#latestViewModel;
    if (
      !current ||
      envelope.data.bridgeNonce !== this.#bridgeNonce ||
      envelope.data.contractId !== current.contractId ||
      envelope.data.threadId !== current.sessionId ||
      !envelope.data.userActivated
    ) {
      return true;
    }
    const now = Date.now();
    while (
      this.#uiIntentTimestamps[0] !== undefined &&
      this.#uiIntentTimestamps[0] <= now - 1_000
    ) {
      this.#uiIntentTimestamps.shift();
    }
    if (this.#uiIntentTimestamps.length >= GOAL_PROGRESS_UI_INTENT_MAX_PER_SECOND) {
      return true;
    }
    this.#uiIntentTimestamps.push(now);
    const result = await this.#onUpdateIntent(envelope.data.threadId, envelope.data.intent);
    const incoming = GoalProgressUpdateStateSchema.parse(result.updateState);
    if (classifyGoalProgressUpdateState(incoming, this.#latestUpdateState) !== "accept") {
      return true;
    }
    this.#latestUpdateState = incoming;
    await this.#writeLatestUpdateStateToPage();
    return true;
  }

  async #writeLatestUpdateStateToPage(): Promise<void> {
    const viewModel = this.#latestViewModel;
    if (!viewModel || !this.#configured) {
      return;
    }
    const pageResult = await invokeGoalProgressPageApi(
      this.#sender,
      "setUpdateState",
      this.#latestUpdateState,
    );
    const parsed = GoalProgressPageMutationResultSchema.safeParse(pageResult);
    if (!parsed.success) {
      this.#configured = false;
      throw new Error("GOAL_PROGRESS_PAGE_HOST_UPDATE_STATE_FAILED");
    }
    const result = parsed.data;
    if (result.reason === "ok" && result.hostCount === 1) {
      return;
    }
    this.#configured = false;
    if (result.reason === "not-configured") {
      await this.#mount(viewModel);
      return;
    }
    throw new Error("GOAL_PROGRESS_PAGE_HOST_UPDATE_STATE_FAILED");
  }

  #enqueue<T>(work: () => Promise<T>): Promise<T> {
    const run = this.#queue.then(work, work).catch((error: unknown) => {
      this.#lastErrorCode = stableBridgeErrorCode(error);
      throw error;
    });
    this.#queue = run.then(
      () => undefined,
      () => undefined,
    );
    return run;
  }
}

function stableBridgeErrorCode(error: unknown): string {
  const value = error instanceof Error ? error.message : String(error);
  const stable = /^[A-Z][A-Z0-9_]{2,127}/u.exec(value)?.[0];
  if (stable) {
    return stable;
  }
  const normalized = value
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]+/gu, "_")
    .replace(/^_+|_+$/gu, "")
    .slice(0, 128);
  return normalized || "RENDERER_BRIDGE_ERROR";
}

export async function connectGoalProgressRendererBridge(
  options: ConnectGoalProgressRendererBridgeOptions,
): Promise<ConnectedGoalProgressRendererBridge> {
  const discovery = await discoverCodexCdp(options.port, options.fetchImpl);
  if (discovery.targets.length !== 1) {
    throw new Error(`GOAL_PROGRESS_CDP_RENDERER_AMBIGUOUS: count=${discovery.targets.length}`);
  }
  const target = discovery.targets[0];
  if (!target) {
    throw new Error("GOAL_PROGRESS_CDP_APP_RENDERER_NOT_FOUND");
  }
  return connectGoalProgressRendererBridgeTarget(options, target);
}

export async function connectGoalProgressRendererBridgeTarget(
  options: ConnectGoalProgressRendererBridgeOptions,
  target: CodexCdpTarget,
): Promise<ConnectedGoalProgressRendererBridge> {
  const client = await CdpProtocolClient.connect(
    target.webSocketDebuggerUrl,
    options.clientOptions,
  );
  return {
    bridge: new GoalProgressRendererBridge({
      sender: client,
      bundle: options.bundle,
      platform: options.platform,
      appVersion: options.appVersion,
      closeSender: () => client.close(),
      ...(options.onUiIntent === undefined ? {} : { onUiIntent: options.onUiIntent }),
      ...(options.onUpdateIntent === undefined ? {} : { onUpdateIntent: options.onUpdateIntent }),
      ...(options.onVisibleThreadChange === undefined
        ? {}
        : { onVisibleThreadChange: options.onVisibleThreadChange }),
      ...(options.onDisconnected === undefined ? {} : { onDisconnected: options.onDisconnected }),
      environment: {
        ...options.environment,
        cdpPort: options.port,
        cdpLoopback: true,
        targetUrl: target.url,
      },
    }),
    targetId: target.id,
  };
}
