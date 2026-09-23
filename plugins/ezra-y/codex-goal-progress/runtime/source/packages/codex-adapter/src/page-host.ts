import type { GoalProgressViewModel } from "../../contracts/src/goal-contract.js";
import pageHostVersionManifest from "../../contracts/src/page-host-version.json" with {
  type: "json",
};
import { GOAL_PROGRESS_RELEASE_VERSION } from "../../contracts/src/release-version.js";
import {
  GOAL_PROGRESS_HOT_ELEMENT_NAME,
  GOAL_PROGRESS_UI_INTENT_BINDING_PREFIX,
  GOAL_PROGRESS_UI_INTENT_PROTOCOL_VERSION,
  type GoalProgressUiIntentEnvelope,
} from "../../contracts/src/renderer-events.js";
import type {
  GoalProgressUiIntent,
  GoalProgressUiPreference,
} from "../../contracts/src/ui-preference.js";
import type {
  GoalProgressUpdateIntent,
  GoalProgressUpdateIntentEnvelope,
  GoalProgressUpdateState,
} from "../../contracts/src/update-state.js";
import {
  GOAL_PROGRESS_UPDATE_INTENT_PROTOCOL_VERSION,
  parseGoalProgressUpdateState,
} from "../../contracts/src/update-state-runtime.js";
import {
  type CodexHostPlatform,
  type CodexNativeGoalLocatorRegistry,
  type CodexVisibleThreadRejectionReason,
  createDefaultCodexNativeGoalLocatorRegistry,
  matchCurrentVisibleThread,
} from "./anchor-adapter.js";
import {
  GOAL_PROGRESS_ELEMENT_NAME,
  removeManagedGoalProgressHosts,
  type SidecarHealthResult,
  type SidecarLayoutDiagnostics,
  SidecarMountController,
  type SidecarMountResult,
} from "./sidecar-mount.js";

export const GOAL_PROGRESS_PAGE_HOST_GLOBAL = "__CODEX_GOAL_PROGRESS__";
export const GOAL_PROGRESS_PAGE_HOST_VERSION = pageHostVersionManifest.pageHostVersion;
export const GOAL_PROGRESS_OBSERVER_DEBOUNCE_MS = 150;
export const GOAL_PROGRESS_OBSERVER_RETRY_DELAYS_MS = Object.freeze([
  250, 500, 1_000, 2_000, 4_000,
] as const);

const OBSERVED_REGION_SELECTOR = "[data-codex-composer-root], [data-app-action-sidebar-thread-row]";
const GOAL_PROGRESS_HOST_SELECTOR = `${GOAL_PROGRESS_ELEMENT_NAME},${GOAL_PROGRESS_HOT_ELEMENT_NAME}`;
const OBSERVED_ATTRIBUTES = [
  "aria-hidden",
  "aria-current",
  "class",
  "data-app-action-sidebar-thread-active",
  "data-app-action-sidebar-thread-host-id",
  "data-app-action-sidebar-thread-id",
  "data-app-action-sidebar-thread-selected",
  "data-codex-composer",
  "data-codex-composer-root",
  "dir",
  "hidden",
  "lang",
  "style",
] as const;

type PageHostFailureReason =
  | "invalid-input"
  | "not-configured"
  | "platform-unsupported"
  | CodexVisibleThreadRejectionReason;

export interface GoalProgressPageHostFailure {
  readonly action: "none";
  readonly reason: PageHostFailureReason;
  readonly adapterId: null;
  readonly adapterRejectionReason: null;
  readonly hostCount: number;
  readonly threadChanged: false;
  readonly displayMode: "hidden";
  readonly nativeAnchorMatched: false;
  readonly visibleThreadStatus: "unknown" | "mismatch" | null;
  readonly componentVisible: false;
  readonly viewModelRevision: null;
}

export interface GoalProgressPageRuntimeDiagnostics {
  readonly uiIntentBindingActive: boolean;
  readonly observerActive: boolean;
  readonly locatorId: string | null;
  readonly appVersionVerified: boolean | null;
  readonly debounceDelayMs: typeof GOAL_PROGRESS_OBSERVER_DEBOUNCE_MS;
  readonly retryDelaysMs: typeof GOAL_PROGRESS_OBSERVER_RETRY_DELAYS_MS;
  readonly mutationBatches: number;
  readonly debounceRuns: number;
  readonly retryRuns: number;
  readonly retryScheduled: number;
  readonly reconcileRuns: number;
  readonly mountActions: number;
  readonly updateActions: number;
  readonly unmountActions: number;
  readonly failureCount: number;
  readonly lastFailureReason: string | null;
  readonly retryExhausted: boolean;
  readonly lastReconcileCause:
    | "none"
    | "initial-mount"
    | "view-model-update"
    | "relevant-mutation"
    | "retry";
  readonly lastMutationKind: "none" | "attributes" | "child-list" | "mixed";
  readonly layout: SidecarLayoutDiagnostics;
}

export type GoalProgressPageHealthResult = (
  | SidecarHealthResult
  | (GoalProgressPageHostFailure & { readonly status: "unmounted" })
) & {
  readonly runtime: GoalProgressPageRuntimeDiagnostics;
};

export interface GoalProgressPageMountInput {
  readonly platform: CodexHostPlatform;
  readonly appVersion: string;
  readonly viewModel: GoalProgressViewModel;
  readonly updateState: GoalProgressUpdateState | null;
  readonly bridgeNonce?: string;
  readonly bridgeBindingName?: string;
  readonly uiPreference: GoalProgressUiPreference;
}

export interface GoalProgressPageHostApi {
  readonly namespace: "codex-goal-progress";
  readonly version: typeof GOAL_PROGRESS_PAGE_HOST_VERSION;
  readonly releaseVersion: typeof GOAL_PROGRESS_RELEASE_VERSION;
  mount(input: unknown): SidecarMountResult | GoalProgressPageHostFailure;
  update(viewModel: unknown): SidecarMountResult | GoalProgressPageHostFailure;
  setUpdateState(updateState: unknown): SidecarMountResult | GoalProgressPageHostFailure;
  unmount(): SidecarMountResult | GoalProgressPageHostFailure;
  health(): GoalProgressPageHealthResult;
}

export interface GoalProgressPageHostOptions {
  readonly elementName?: string;
  readonly registry?: CodexNativeGoalLocatorRegistry;
}

type GoalProgressPageWindow = Window &
  typeof globalThis & {
    [GOAL_PROGRESS_PAGE_HOST_GLOBAL]?: unknown;
  };

const trackingPhases = new Set([
  "preparing",
  "active",
  "paused",
  "blocked",
  "completed",
  "error",
  "detached",
]);

const defaultUiPreference: GoalProgressUiPreference = {
  schemaVersion: 2,
  collapsed: false,
  motionPaused: false,
  hidden: false,
  placement: "inline",
  floatingXRatio: 0.5,
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function parseUiPreference(value: unknown): GoalProgressUiPreference | null {
  if (
    !isRecord(value) ||
    typeof value.collapsed !== "boolean" ||
    typeof value.motionPaused !== "boolean" ||
    typeof value.hidden !== "boolean"
  ) {
    return null;
  }
  if (value.schemaVersion === 1) {
    return {
      ...defaultUiPreference,
      collapsed: value.collapsed,
      motionPaused: value.motionPaused,
      hidden: value.hidden,
    };
  }
  if (
    value.schemaVersion !== 2 ||
    (value.placement !== "inline" && value.placement !== "floating") ||
    typeof value.floatingXRatio !== "number" ||
    !Number.isFinite(value.floatingXRatio) ||
    value.floatingXRatio < 0 ||
    value.floatingXRatio > 1
  ) {
    return null;
  }
  return value as GoalProgressUiPreference;
}

function applyLocalUiIntent(
  preference: GoalProgressUiPreference,
  intent: GoalProgressUiIntent,
): GoalProgressUiPreference {
  if (intent.type === "setCollapsed") {
    return { ...preference, collapsed: intent.collapsed };
  }
  if (intent.type === "setMotionPaused") {
    return { ...preference, motionPaused: intent.motionPaused };
  }
  if (intent.type === "setPlacement") {
    return { ...preference, placement: intent.placement };
  }
  if (intent.type === "setFloatingXRatio") {
    return { ...preference, floatingXRatio: intent.floatingXRatio };
  }
  return preference;
}

function isViewModelEnvelope(value: unknown): value is GoalProgressViewModel {
  if (!isRecord(value)) {
    return false;
  }
  return (
    value.schemaVersion === 2 &&
    typeof value.contractId === "string" &&
    value.contractId.length > 0 &&
    value.contractId.length <= 128 &&
    typeof value.sessionId === "string" &&
    value.sessionId.length > 0 &&
    value.sessionId.length <= 256 &&
    Number.isSafeInteger(value.revision) &&
    Number.isSafeInteger(value.scopeRevision) &&
    typeof value.trackingPhase === "string" &&
    trackingPhases.has(value.trackingPhase) &&
    typeof value.objective === "string" &&
    Array.isArray(value.objectives) &&
    (value.optionalObjectives === undefined || Array.isArray(value.optionalObjectives)) &&
    value.maxVisibleObjectives === 3
  );
}

function parseMountInput(value: unknown): GoalProgressPageMountInput | null {
  if (!isRecord(value)) {
    return null;
  }
  const platform = value.platform;
  const appVersion = value.appVersion;
  const bridgeNonce = value.bridgeNonce;
  const bridgeBindingName = value.bridgeBindingName;
  const uiPreference =
    value.uiPreference === undefined ? defaultUiPreference : parseUiPreference(value.uiPreference);
  const updateState =
    value.updateState === null || value.updateState === undefined
      ? null
      : parseGoalProgressUpdateState(value.updateState);
  if (
    (platform !== "macos" && platform !== "windows") ||
    typeof appVersion !== "string" ||
    !/^[0-9]+(?:\.[0-9]+){1,5}$/u.test(appVersion) ||
    !isViewModelEnvelope(value.viewModel) ||
    (bridgeNonce === undefined) !== (bridgeBindingName === undefined) ||
    (bridgeBindingName !== undefined && typeof bridgeBindingName !== "string") ||
    (bridgeNonce !== undefined &&
      (typeof bridgeNonce !== "string" ||
        !/^[A-Za-z0-9_-]{32}$/u.test(bridgeNonce) ||
        bridgeBindingName !== `${GOAL_PROGRESS_UI_INTENT_BINDING_PREFIX}${bridgeNonce}`)) ||
    uiPreference === null ||
    (value.updateState !== null && value.updateState !== undefined && updateState === null)
  ) {
    return null;
  }
  return {
    platform,
    appVersion,
    viewModel: value.viewModel,
    updateState,
    ...(bridgeNonce === undefined ? {} : { bridgeNonce }),
    ...(bridgeBindingName === undefined ? {} : { bridgeBindingName }),
    uiPreference,
  };
}

function hostCount(document: Document): number {
  return document.querySelectorAll(
    `${GOAL_PROGRESS_ELEMENT_NAME},${GOAL_PROGRESS_HOT_ELEMENT_NAME}`,
  ).length;
}

function hasRetainableTaskSurface(document: Document): boolean {
  const composers = document.querySelectorAll<HTMLElement>("[data-codex-composer-root]");
  return (
    composers.length === 1 &&
    composers[0]?.querySelectorAll('[role="textbox"][data-codex-composer]').length === 1
  );
}

function failure(document: Document, reason: PageHostFailureReason): GoalProgressPageHostFailure {
  const visibleThreadStatus =
    reason === "visible-thread-mismatch"
      ? "mismatch"
      : reason === "visible-thread-marker-missing" ||
          reason === "visible-thread-marker-ambiguous" ||
          reason === "visible-thread-id-missing"
        ? "unknown"
        : null;
  return {
    action: "none",
    reason,
    adapterId: null,
    adapterRejectionReason: null,
    hostCount: hostCount(document),
    threadChanged: false,
    displayMode: "hidden",
    nativeAnchorMatched: false,
    visibleThreadStatus,
    componentVisible: false,
    viewModelRevision: null,
  };
}

function emptyLayoutDiagnostics(): SidecarLayoutDiagnostics {
  return {
    lastAnchorState: "none",
    lastConstraintTransition: "none",
    lastCollapsedTransition: "none",
    lastPlacementTransition: "none",
    layoutReadCount: 0,
    layoutWriteCount: 0,
    nativeGeometryFingerprint: null,
    sidecarGeometryFingerprint: null,
    continuityModeActive: false,
    requestedPlacement: "inline",
    effectivePlacement: "none",
    floatingFallbackReason: null,
    lastHostRemovalReason: null,
    visibility: {
      composerRectFingerprint: null,
      textboxRectFingerprint: null,
      hostRectFingerprint: null,
      textboxClientHeight: null,
      textboxScrollHeight: null,
      textboxScrollTop: null,
      textboxOverflowY: null,
      composerClassTokenCount: 0,
      composerInlineStylePropertyCount: 0,
      clippingAncestorFingerprint: null,
      clippingOverflow: null,
      hostViewportIntersectionRatio: 0,
      hostClippedIntersectionRatio: 0,
      anchorConnected: false,
      composerCount: 0,
      textboxCount: 0,
      surface: "none",
      lastObserverReason: "none",
    },
  };
}

function isElement(node: Node): node is Element {
  return node.nodeType === 1;
}

function isInsideObservedRegion(node: Node): boolean {
  if (!isElement(node)) {
    return false;
  }
  if (
    node.matches(GOAL_PROGRESS_HOST_SELECTOR) ||
    node.closest(GOAL_PROGRESS_HOST_SELECTOR) !== null
  ) {
    return false;
  }
  return node.matches(OBSERVED_REGION_SELECTOR) || node.closest(OBSERVED_REGION_SELECTOR) !== null;
}

function containsObservedRegion(node: Node): boolean {
  if (!isElement(node)) {
    return false;
  }
  if (
    node.matches(GOAL_PROGRESS_HOST_SELECTOR) ||
    node.closest(GOAL_PROGRESS_HOST_SELECTOR) !== null
  ) {
    return false;
  }
  return (
    node.matches(OBSERVED_REGION_SELECTOR) || node.querySelector(OBSERVED_REGION_SELECTOR) !== null
  );
}

function containsForeignGoalProgressHost(node: Node, managedHost: HTMLElement | null): boolean {
  if (!isElement(node)) {
    return false;
  }
  const candidates = [
    ...(node.matches(GOAL_PROGRESS_HOST_SELECTOR) ? [node] : []),
    ...node.querySelectorAll<HTMLElement>(GOAL_PROGRESS_HOST_SELECTOR),
  ];
  return candidates.some((candidate) => candidate !== managedHost);
}

function relevantMutation(record: MutationRecord, managedHost: HTMLElement | null): boolean {
  if (record.type === "attributes") {
    if (
      record.target === record.target.ownerDocument?.documentElement &&
      (record.attributeName === "lang" || record.attributeName === "dir")
    ) {
      return true;
    }
    return isInsideObservedRegion(record.target);
  }
  const changedNodes = [...record.addedNodes, ...record.removedNodes];
  if (changedNodes.some((node) => containsForeignGoalProgressHost(node, managedHost))) {
    return true;
  }
  if (
    changedNodes.length > 0 &&
    managedHost !== null &&
    changedNodes.every((node) => node === managedHost)
  ) {
    return false;
  }
  if (isInsideObservedRegion(record.target)) {
    return true;
  }
  return changedNodes.some(containsObservedRegion);
}

class GoalProgressPageHost implements GoalProgressPageHostApi {
  readonly namespace = "codex-goal-progress";
  readonly version = GOAL_PROGRESS_PAGE_HOST_VERSION;
  readonly releaseVersion = GOAL_PROGRESS_RELEASE_VERSION;
  readonly #document: Document;
  readonly #elementName: string;
  readonly #registry: CodexNativeGoalLocatorRegistry;
  #uiIntentBinding: ((payload: string) => void) | undefined;
  #uiIntentBindingName: string | undefined;
  #controller: SidecarMountController | null = null;
  #lastManagedHost: HTMLElement | null = null;
  #configuration: GoalProgressPageMountInput | null = null;
  #observer: MutationObserver | null = null;
  #debounceTimer: ReturnType<typeof setTimeout> | null = null;
  #retryTimer: ReturnType<typeof setTimeout> | null = null;
  #retryIndex = 0;
  #retryExhausted = false;
  #retainingUnknown = false;
  #unknownRetentionExpired = false;
  #mutationBatches = 0;
  #debounceRuns = 0;
  #retryRuns = 0;
  #retryScheduled = 0;
  #reconcileRuns = 0;
  #mountActions = 0;
  #updateActions = 0;
  #unmountActions = 0;
  #failureCount = 0;
  #lastFailureReason: string | null = null;
  #lastLayoutDiagnostics: SidecarLayoutDiagnostics = emptyLayoutDiagnostics();
  #locatorId: string | null = null;
  #appVersionVerified: boolean | null = null;
  #lastVisibleThreadStatus: "matched" | "unknown" | "mismatch" | null = null;
  #lastVisibleThreadReason: CodexVisibleThreadRejectionReason | null = null;
  #lastReconcileCause: GoalProgressPageRuntimeDiagnostics["lastReconcileCause"] = "none";
  #lastMutationKind: GoalProgressPageRuntimeDiagnostics["lastMutationKind"] = "none";

  constructor(document: Document, options: GoalProgressPageHostOptions) {
    this.#document = document;
    this.#elementName = options.elementName ?? GOAL_PROGRESS_ELEMENT_NAME;
    this.#registry = options.registry ?? createDefaultCodexNativeGoalLocatorRegistry();
  }

  mount(input: unknown): SidecarMountResult | GoalProgressPageHostFailure {
    const parsed = parseMountInput(input);
    if (!parsed) {
      this.#stopRuntime();
      return failure(this.#document, "invalid-input");
    }
    const current = this.#configuration;
    const sameView =
      current?.viewModel.contractId === parsed.viewModel.contractId &&
      current.viewModel.sessionId === parsed.viewModel.sessionId;
    if (!sameView) {
      this.#unknownRetentionExpired = false;
    }
    this.#captureUiIntentBinding(parsed.bridgeBindingName);
    this.#configuration = sameView
      ? {
          ...parsed,
          uiPreference: current.uiPreference,
        }
      : parsed;
    this.#startObserver();
    this.#lastReconcileCause = "initial-mount";
    return this.#reconcile();
  }

  update(viewModel: unknown): SidecarMountResult | GoalProgressPageHostFailure {
    if (!this.#configuration) {
      return failure(this.#document, "not-configured");
    }
    if (!isViewModelEnvelope(viewModel)) {
      this.#stopRuntime();
      return failure(this.#document, "invalid-input");
    }
    this.#configuration = {
      ...this.#configuration,
      viewModel,
    };
    this.#lastReconcileCause = "view-model-update";
    return this.#reconcile();
  }

  setUpdateState(updateState: unknown): SidecarMountResult | GoalProgressPageHostFailure {
    if (!this.#configuration) {
      return failure(this.#document, "not-configured");
    }
    const parsed = updateState === null ? null : parseGoalProgressUpdateState(updateState);
    if (updateState !== null && parsed === null) {
      return failure(this.#document, "invalid-input");
    }
    this.#configuration = {
      ...this.#configuration,
      updateState: parsed,
    };
    return this.#controller?.setUpdateState(parsed) ?? failure(this.#document, "not-configured");
  }

  unmount(): SidecarMountResult | GoalProgressPageHostFailure {
    if (!this.#configuration && !this.#controller) {
      removeManagedGoalProgressHosts(this.#document);
      return failure(this.#document, "not-configured");
    }
    const result = this.#controller?.unmount() ?? failure(this.#document, "not-configured");
    this.#recordResult(result);
    this.#captureControllerLayout();
    this.#controller = null;
    this.#stopRuntime();
    return result;
  }

  health(): GoalProgressPageHealthResult {
    const hiddenReason =
      this.#lastVisibleThreadStatus === "mismatch"
        ? (this.#lastVisibleThreadReason ?? "visible-thread-mismatch")
        : this.#lastVisibleThreadStatus === "unknown"
          ? (this.#lastVisibleThreadReason ?? "visible-thread-id-missing")
          : "not-configured";
    const result =
      this.#controller?.health() ??
      ({
        ...failure(this.#document, hiddenReason),
        status: "unmounted",
      } as const);
    return {
      ...result,
      runtime: this.#diagnostics(),
    };
  }

  #reconcile(): SidecarMountResult | GoalProgressPageHostFailure {
    const parsed = this.#configuration;
    if (!parsed) {
      return failure(this.#document, "not-configured");
    }
    this.#reconcileRuns += 1;
    const visibleThread = matchCurrentVisibleThread(this.#document, parsed.viewModel.sessionId);
    this.#lastVisibleThreadStatus = visibleThread.status;
    this.#lastVisibleThreadReason = visibleThread.rejectionReason;
    if (visibleThread.status === "mismatch") {
      this.#retainingUnknown = false;
      this.#unknownRetentionExpired = false;
      if (this.#controller) {
        this.#recordResult(this.#controller.unmount());
      }
      this.#captureControllerLayout();
      this.#controller = null;
      const result = failure(
        this.#document,
        visibleThread.rejectionReason ?? "visible-thread-mismatch",
      );
      this.#recordResult(result);
      this.#cancelRetry();
      this.#retryIndex = 0;
      this.#retryExhausted = false;
      return result;
    }
    if (visibleThread.status === "unknown") {
      const unknownReason = visibleThread.rejectionReason ?? "visible-thread-id-missing";
      if (this.#controller && !hasRetainableTaskSurface(this.#document)) {
        this.#retainingUnknown = false;
        this.#unknownRetentionExpired = true;
        this.#recordResult(this.#controller.unmount());
        this.#captureControllerLayout();
        this.#controller = null;
        this.#cancelRetry();
        this.#retryIndex = 0;
        this.#retryExhausted = false;
        const result = failure(this.#document, unknownReason);
        this.#recordResult(result);
        return result;
      }
      if (this.#controller) {
        const retained = this.#controller.retainCurrentSession(
          parsed.viewModel,
          parsed.uiPreference,
          parsed.updateState,
        );
        this.#recordResult(retained);
        this.#lastManagedHost = this.#controller.managedHostElement() ?? this.#lastManagedHost;
        if (retained.reason === "ok") {
          this.#retainingUnknown = true;
          this.#scheduleRetry();
          if (this.#retryExhausted) {
            this.#retainingUnknown = false;
            this.#unknownRetentionExpired = true;
            this.#recordResult(this.#controller.unmount());
            this.#captureControllerLayout();
            this.#controller = null;
            const result = failure(this.#document, unknownReason);
            this.#recordResult(result);
            return result;
          }
          return retained;
        }
        if (retained.reason === "host-ambiguous" || retained.reason === "host-unmanaged") {
          this.#retainingUnknown = false;
          this.#unknownRetentionExpired = false;
          this.#cancelRetry();
          this.#retryIndex = 0;
          this.#retryExhausted = false;
          return retained;
        }
        if (retained.action === "unmounted") {
          this.#retainingUnknown = false;
          this.#captureControllerLayout();
          this.#controller = null;
          this.#scheduleRetry();
          return retained;
        }
      }
      if (this.#controller) {
        this.#recordResult(this.#controller.unmount());
      }
      this.#captureControllerLayout();
      this.#controller = null;
      this.#retainingUnknown = false;
      const result = failure(this.#document, unknownReason);
      this.#recordResult(result);
      if (!this.#unknownRetentionExpired) {
        this.#scheduleRetry();
      }
      return result;
    }
    this.#retainingUnknown = false;
    this.#unknownRetentionExpired = false;
    const locator = this.#registry.resolvePlatform(parsed.platform);
    if (!locator) {
      if (this.#controller) {
        this.#recordResult(this.#controller.unmount());
      }
      this.#captureControllerLayout();
      this.#controller = null;
      this.#locatorId = null;
      this.#appVersionVerified = null;
      const result = failure(this.#document, "platform-unsupported");
      this.#recordResult(result);
      this.#cancelRetry();
      this.#retryIndex = 0;
      this.#retryExhausted = false;
      return result;
    }
    this.#locatorId = locator.id;
    this.#appVersionVerified = locator.verifiedVersions.has(parsed.appVersion);
    if (!this.#controller) {
      this.#controller = new SidecarMountController(this.#document, {
        nativeGoalLocator: locator,
        elementName: this.#elementName,
        onUiIntent: (intent, context) => this.#forwardUiIntent(intent, context.userActivated),
        onUpdateIntent: (intent, context) =>
          this.#forwardUpdateIntent(intent, context.userActivated),
      });
    }
    const location = locator.locate(this.#document);
    const result = this.#controller.ensureMounted(parsed.viewModel, parsed.uiPreference, {
      displayTarget: location.target
        ? {
            kind: "native",
            ...location.target,
          }
        : { kind: "fallback" },
      environmentChanged: this.#lastReconcileCause === "relevant-mutation",
      nativeGoalRejectionReason: location.rejectionReason,
      updateState: parsed.updateState,
    });
    this.#lastManagedHost = this.#controller.managedHostElement() ?? this.#lastManagedHost;
    this.#recordResult(result);
    if (result.reason === "native-goal-changed") {
      this.#stopRuntime();
      return result;
    }
    if (result.reason === "ok") {
      this.#cancelRetry();
      this.#retryIndex = 0;
      this.#retryExhausted = false;
    } else {
      this.#scheduleRetry();
    }
    return result;
  }

  #forwardUiIntent(intent: GoalProgressUiIntent, userActivated: boolean): void {
    const configuration = this.#configuration;
    if (!configuration) {
      return;
    }
    this.#configuration = {
      ...configuration,
      uiPreference: applyLocalUiIntent(configuration.uiPreference, intent),
    };
    if (!configuration.bridgeNonce || !this.#uiIntentBinding) {
      return;
    }
    const envelope: GoalProgressUiIntentEnvelope = {
      protocolVersion: GOAL_PROGRESS_UI_INTENT_PROTOCOL_VERSION,
      bridgeNonce: configuration.bridgeNonce,
      contractId: configuration.viewModel.contractId,
      threadId: configuration.viewModel.sessionId,
      userActivated,
      intent,
    };
    this.#uiIntentBinding(JSON.stringify(envelope));
  }

  #forwardUpdateIntent(intent: GoalProgressUpdateIntent, userActivated: boolean): void {
    const configuration = this.#configuration;
    if (!configuration?.bridgeNonce || !this.#uiIntentBinding) {
      return;
    }
    const envelope: GoalProgressUpdateIntentEnvelope = {
      protocolVersion: GOAL_PROGRESS_UPDATE_INTENT_PROTOCOL_VERSION,
      intentKind: "update",
      bridgeNonce: configuration.bridgeNonce,
      contractId: configuration.viewModel.contractId,
      threadId: configuration.viewModel.sessionId,
      userActivated,
      intent,
    };
    this.#uiIntentBinding(JSON.stringify(envelope));
  }

  #captureUiIntentBinding(bindingName: string | undefined): void {
    if (!bindingName || bindingName === this.#uiIntentBindingName) {
      return;
    }
    const target = this.#document.defaultView as (Window & Record<string, unknown>) | null;
    const binding = target?.[bindingName];
    if (!target || typeof binding !== "function") {
      return;
    }
    this.#uiIntentBinding = (payload: string) =>
      (binding as (this: Window, value: string) => void).call(target, payload);
    this.#uiIntentBindingName = bindingName;
    delete target[bindingName];
  }

  #startObserver(): void {
    if (this.#observer) {
      return;
    }
    this.#observer = new MutationObserver((records) => {
      const managedHost = this.#controller?.managedHostElement() ?? this.#lastManagedHost;
      const relevant = records.filter((record) => relevantMutation(record, managedHost));
      if (relevant.length === 0) {
        return;
      }
      const kinds = new Set(relevant.map((record) => record.type));
      this.#lastMutationKind =
        kinds.size > 1 ? "mixed" : relevant[0]?.type === "attributes" ? "attributes" : "child-list";
      this.#mutationBatches += 1;
      if (this.#controller?.health().reason === "native-goal-changed") {
        this.#retainingUnknown = false;
        this.#unknownRetentionExpired = false;
        if (this.#debounceTimer) {
          clearTimeout(this.#debounceTimer);
          this.#debounceTimer = null;
        }
        this.#cancelRetry();
        this.#retryIndex = 0;
        this.#retryExhausted = false;
        this.#lastReconcileCause = "relevant-mutation";
        this.#reconcile();
        return;
      }
      if (this.#debounceTimer) {
        clearTimeout(this.#debounceTimer);
      }
      this.#debounceTimer = setTimeout(() => {
        this.#debounceTimer = null;
        this.#debounceRuns += 1;
        if (!this.#retainingUnknown && !this.#unknownRetentionExpired) {
          this.#cancelRetry();
          this.#retryIndex = 0;
          this.#retryExhausted = false;
        }
        this.#lastReconcileCause = "relevant-mutation";
        this.#reconcile();
      }, GOAL_PROGRESS_OBSERVER_DEBOUNCE_MS);
    });
    this.#observer.observe(this.#document.documentElement, {
      attributes: true,
      attributeFilter: [...OBSERVED_ATTRIBUTES],
      childList: true,
      subtree: true,
    });
  }

  #scheduleRetry(): void {
    if (this.#retryTimer || !this.#configuration) {
      return;
    }
    const delay = GOAL_PROGRESS_OBSERVER_RETRY_DELAYS_MS[this.#retryIndex];
    if (delay === undefined) {
      this.#retryExhausted = true;
      return;
    }
    this.#retryIndex += 1;
    this.#retryScheduled += 1;
    this.#retryTimer = setTimeout(() => {
      this.#retryTimer = null;
      this.#retryRuns += 1;
      this.#lastReconcileCause = "retry";
      this.#reconcile();
    }, delay);
  }

  #cancelRetry(): void {
    if (this.#retryTimer) {
      clearTimeout(this.#retryTimer);
      this.#retryTimer = null;
    }
  }

  #stopRuntime(): void {
    this.#observer?.disconnect();
    this.#observer = null;
    if (this.#debounceTimer) {
      clearTimeout(this.#debounceTimer);
      this.#debounceTimer = null;
    }
    this.#cancelRetry();
    this.#controller?.unmount();
    this.#captureControllerLayout();
    this.#controller = null;
    this.#configuration = null;
    this.#locatorId = null;
    this.#appVersionVerified = null;
    this.#lastVisibleThreadStatus = null;
    this.#lastVisibleThreadReason = null;
    this.#retryIndex = 0;
    this.#retryExhausted = false;
    this.#retainingUnknown = false;
    this.#unknownRetentionExpired = false;
  }

  #recordResult(result: SidecarMountResult | GoalProgressPageHostFailure): void {
    if (result.action === "mounted") {
      this.#mountActions += 1;
    } else if (result.action === "updated") {
      this.#updateActions += 1;
    } else if (result.action === "unmounted") {
      this.#unmountActions += 1;
    }
    if (result.reason !== "ok") {
      this.#failureCount += 1;
      this.#lastFailureReason = result.reason;
    }
  }

  #captureControllerLayout(): void {
    if (this.#controller) {
      this.#lastLayoutDiagnostics = this.#controller.diagnostics();
    }
  }

  #diagnostics(): GoalProgressPageRuntimeDiagnostics {
    return {
      uiIntentBindingActive: this.#uiIntentBinding !== undefined,
      observerActive: this.#observer !== null,
      locatorId: this.#locatorId,
      appVersionVerified: this.#appVersionVerified,
      debounceDelayMs: GOAL_PROGRESS_OBSERVER_DEBOUNCE_MS,
      retryDelaysMs: GOAL_PROGRESS_OBSERVER_RETRY_DELAYS_MS,
      mutationBatches: this.#mutationBatches,
      debounceRuns: this.#debounceRuns,
      retryRuns: this.#retryRuns,
      retryScheduled: this.#retryScheduled,
      reconcileRuns: this.#reconcileRuns,
      mountActions: this.#mountActions,
      updateActions: this.#updateActions,
      unmountActions: this.#unmountActions,
      failureCount: this.#failureCount,
      lastFailureReason: this.#lastFailureReason,
      retryExhausted: this.#retryExhausted,
      lastReconcileCause: this.#lastReconcileCause,
      lastMutationKind: this.#lastMutationKind,
      layout: this.#controller?.diagnostics() ?? this.#lastLayoutDiagnostics,
    };
  }
}

function isInstalledApi(value: unknown): value is GoalProgressPageHostApi {
  return (
    isRecord(value) &&
    value.namespace === "codex-goal-progress" &&
    value.version === GOAL_PROGRESS_PAGE_HOST_VERSION &&
    value.releaseVersion === GOAL_PROGRESS_RELEASE_VERSION &&
    typeof value.mount === "function" &&
    typeof value.update === "function" &&
    typeof value.setUpdateState === "function" &&
    typeof value.unmount === "function" &&
    typeof value.health === "function"
  );
}

function isReplaceableApi(
  value: unknown,
): value is { readonly version: number; readonly releaseVersion?: string; unmount(): unknown } {
  return (
    isRecord(value) &&
    value.namespace === "codex-goal-progress" &&
    Number.isSafeInteger(value.version) &&
    (value.version as number) > 0 &&
    ((value.version as number) < GOAL_PROGRESS_PAGE_HOST_VERSION ||
      (value.version === GOAL_PROGRESS_PAGE_HOST_VERSION &&
        value.releaseVersion !== GOAL_PROGRESS_RELEASE_VERSION)) &&
    typeof value.unmount === "function"
  );
}

export function installGoalProgressPageHost(
  target: GoalProgressPageWindow,
  options: GoalProgressPageHostOptions = {},
): GoalProgressPageHostApi | null {
  const existing = target[GOAL_PROGRESS_PAGE_HOST_GLOBAL];
  if (isInstalledApi(existing)) {
    return existing;
  }
  if (existing !== undefined) {
    if (!isReplaceableApi(existing)) {
      return null;
    }
    try {
      existing.unmount();
      if (!delete target[GOAL_PROGRESS_PAGE_HOST_GLOBAL]) {
        return null;
      }
    } catch {
      return null;
    }
  }
  const api = Object.freeze(new GoalProgressPageHost(target.document, options));
  Object.defineProperty(target, GOAL_PROGRESS_PAGE_HOST_GLOBAL, {
    value: api,
    configurable: true,
    enumerable: false,
    writable: false,
  });
  return api;
}
