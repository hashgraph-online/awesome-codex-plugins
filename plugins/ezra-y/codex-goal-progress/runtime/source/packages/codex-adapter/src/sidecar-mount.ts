import type { GoalProgressViewModel } from "../../contracts/src/goal-contract.js";
import {
  GOAL_PROGRESS_ELEMENT_NAME,
  GOAL_PROGRESS_FLOATING_LAYOUT_EVENT,
  GOAL_PROGRESS_HOT_ELEMENT_NAME,
  GOAL_PROGRESS_LAYOUT_OFFSET_EVENT,
  GOAL_PROGRESS_REQUEST_DETACH_EVENT,
  GOAL_PROGRESS_REQUEST_RETRY_EVENT,
  GOAL_PROGRESS_SET_COLLAPSED_EVENT,
  GOAL_PROGRESS_SET_FLOATING_X_RATIO_EVENT,
  GOAL_PROGRESS_SET_MOTION_PAUSED_EVENT,
  GOAL_PROGRESS_SET_PLACEMENT_EVENT,
} from "../../contracts/src/renderer-events.js";
import type {
  GoalProgressUiIntent,
  GoalProgressUiPreference,
} from "../../contracts/src/ui-preference.js";
import type {
  GoalProgressUpdateIntent,
  GoalProgressUpdateState,
} from "../../contracts/src/update-state.js";
import {
  GOAL_PROGRESS_UPDATE_INTENT_EVENT,
  parseGoalProgressUpdateIntent,
} from "../../contracts/src/update-state-runtime.js";
import type {
  CodexAnchorRejectionReason,
  CodexNativeGoalLocator,
  CodexVisibleThreadRejectionReason,
  NativeGoalTarget,
} from "./anchor-adapter.js";
import { projectFloatingCenter } from "./floating-placement.js";
import {
  type GoalProgressDisplayMode,
  projectSidecarDiagnostics,
  projectSidecarHealth,
  rectFingerprint,
  type SidecarHealthReason,
  type SidecarHealthResult,
  type SidecarHealthStatus,
  type SidecarLayoutDiagnostics,
  type SidecarVisibilityDiagnostics,
} from "./sidecar-diagnostics.js";
import { parseExpandedLayoutOffset, parseSidecarUiIntent } from "./sidecar-ui-intent-adapter.js";

export {
  GOAL_PROGRESS_ELEMENT_NAME,
  GOAL_PROGRESS_REQUEST_DETACH_EVENT,
  GOAL_PROGRESS_REQUEST_RETRY_EVENT,
  GOAL_PROGRESS_SET_COLLAPSED_EVENT,
  GOAL_PROGRESS_SET_FLOATING_X_RATIO_EVENT,
  GOAL_PROGRESS_SET_MOTION_PAUSED_EVENT,
  GOAL_PROGRESS_SET_PLACEMENT_EVENT,
} from "../../contracts/src/renderer-events.js";
export type {
  GoalProgressDisplayMode,
  SidecarHealthReason,
  SidecarHealthResult,
  SidecarHealthStatus,
  SidecarLayoutDiagnostics,
  SidecarVisibilityDiagnostics,
} from "./sidecar-diagnostics.js";

export const GOAL_PROGRESS_HOST_ATTRIBUTE = "data-codex-goal-progress-host";
export const GOAL_PROGRESS_HOST_ATTRIBUTE_VALUE = "v1";
export const GOAL_PROGRESS_FLOATING_FALLBACK_ATTRIBUTE =
  "data-codex-goal-progress-floating-fallback";
const GOAL_PROGRESS_ANCHOR_ORIGINAL_TRANSLATE_ATTRIBUTE =
  "data-codex-goal-progress-original-translate";
const GOAL_PROGRESS_FLOATING_FALLBACK_RETRY_DELAYS_MS = [250, 500, 1_000, 2_000, 4_000] as const;

export type GoalProgressLocalUiIntent = GoalProgressUiIntent;

export interface GoalProgressLocalUiIntentContext {
  readonly userActivated: boolean;
}

export type SidecarMountAction = "mounted" | "updated" | "unmounted" | "none";

export type GoalProgressDisplayTarget =
  | ({ readonly kind: "native" } & NativeGoalTarget)
  | { readonly kind: "fallback" };

export type SidecarMountReason =
  | "ok"
  | "anchor-unavailable"
  | "native-goal-changed"
  | "host-missing"
  | "host-ambiguous"
  | "host-unmanaged"
  | CodexVisibleThreadRejectionReason;

export interface SidecarMountResult {
  readonly action: SidecarMountAction;
  readonly reason: SidecarMountReason;
  readonly adapterId: string;
  readonly adapterRejectionReason: CodexAnchorRejectionReason | null;
  readonly hostCount: number;
  readonly threadChanged: boolean;
  readonly displayMode: GoalProgressDisplayMode;
  readonly nativeAnchorMatched: boolean;
  readonly visibleThreadStatus: "matched" | "retained";
}

export interface SidecarMountControllerOptions {
  readonly nativeGoalLocator: CodexNativeGoalLocator;
  readonly elementName?: string;
  readonly onUiIntent?: (
    intent: GoalProgressLocalUiIntent,
    context: GoalProgressLocalUiIntentContext,
  ) => void;
  readonly onUpdateIntent?: (
    intent: GoalProgressUpdateIntent,
    context: GoalProgressLocalUiIntentContext,
  ) => void;
}

export interface SidecarEnsureMountedOptions {
  readonly displayTarget: GoalProgressDisplayTarget;
  readonly environmentChanged?: boolean;
  readonly nativeGoalRejectionReason?: CodexAnchorRejectionReason | null;
  readonly updateState?: GoalProgressUpdateState | null;
}

interface GoalProgressHostElement extends HTMLElement {
  viewModel: GoalProgressViewModel | null;
  updateState: GoalProgressUpdateState | null;
  collapsed: boolean;
  readonly expandedLayoutOffset?: number;
  floatingCenterAvailable: boolean;
  floatingPanelConstrained: boolean;
  floatingXRatio: number;
  motionPaused: boolean;
  placement: "inline" | "floating";
  requestedPlacement: "inline" | "floating";
  spaceConstrained: boolean;
}

function clampFloatingDockRatio(value: number): number {
  return Math.max(0, Math.min(1, value));
}

const RTL_DOCUMENT_LANGUAGES = new Set(["ar", "fa", "ur"]);

function documentDirection(document: Document, language: string): "ltr" | "rtl" {
  const declared = document.documentElement.getAttribute("dir")?.trim().toLowerCase();
  if (declared === "rtl" || declared === "ltr") {
    return declared;
  }
  try {
    const locale = new Intl.Locale(language);
    return RTL_DOCUMENT_LANGUAGES.has(locale.language) ? "rtl" : "ltr";
  } catch {
    return "ltr";
  }
}

function syncHostLocale(host: GoalProgressHostElement, document: Document): void {
  const language = (document.documentElement.lang ?? "").trim();
  host.lang = language || "en";
  host.dir = documentDirection(document, host.lang);
}

function floatingGoalBlockRect(anchor: HTMLElement): DOMRect {
  const anchorRect = anchor.getBoundingClientRect();
  const block = anchor.firstElementChild;
  if (!(block instanceof HTMLElement)) {
    return anchorRect;
  }
  const blockRect = block.getBoundingClientRect();
  const isContained =
    blockRect.left >= anchorRect.left &&
    blockRect.right <= anchorRect.right &&
    blockRect.top >= anchorRect.top &&
    blockRect.bottom <= anchorRect.bottom;
  const isRepresentative =
    blockRect.width >= anchorRect.width * 0.5 && blockRect.height >= anchorRect.height * 0.5;
  return isContained && isRepresentative ? blockRect : anchorRect;
}

const GOAL_PROGRESS_KNOWN_ELEMENT_SELECTOR = `${GOAL_PROGRESS_ELEMENT_NAME},${GOAL_PROGRESS_HOT_ELEMENT_NAME}`;

function hosts(document: Document): GoalProgressHostElement[] {
  return Array.from(
    document.querySelectorAll<GoalProgressHostElement>(GOAL_PROGRESS_KNOWN_ELEMENT_SELECTOR),
  );
}

function isManagedHost(host: GoalProgressHostElement): boolean {
  return host.getAttribute(GOAL_PROGRESS_HOST_ATTRIBUTE) === GOAL_PROGRESS_HOST_ATTRIBUTE_VALUE;
}

export function removeManagedGoalProgressHosts(document: Document): number {
  const managedHosts = hosts(document).filter(isManagedHost);
  for (const host of managedHosts) {
    host.viewModel = null;
    host.updateState = null;
    host.remove();
  }
  return managedHosts.length;
}

function requiresInlineState(viewModel: GoalProgressViewModel | null | undefined): boolean {
  return viewModel?.trackingPhase === "preparing";
}

function preparingViewMatchesGoalIdentity(
  viewModel: GoalProgressViewModel,
  goalIdentity: string | null,
): boolean {
  if (viewModel.trackingPhase !== "preparing" || goalIdentity === null) {
    return false;
  }
  const objective = viewModel.objective
    .replace(/\s+/gu, " ")
    .replace(/\s*•\s*$/u, "")
    .trim();
  return objective.length > 0 && objective === goalIdentity;
}

function findFloatingObstacle(
  document: Document,
  host: HTMLElement,
  anchor: HTMLElement,
  chip: HTMLElement | null,
  panel: HTMLElement | null,
  safeLeft: number,
  safeRight: number,
  knownObstacles?: readonly HTMLElement[],
): DOMRect | null {
  const composer = anchor.closest<HTMLElement>("[data-codex-composer-root]");
  const view = document.defaultView;
  if (!composer || !view || (!chip && !panel)) {
    return null;
  }
  const anchorRect = anchor.getBoundingClientRect();
  const composerRect = composer.getBoundingClientRect();
  const floatingRects = [chip, panel].flatMap((element) =>
    element ? [element.getBoundingClientRect()] : [],
  );
  const floatingTop = Math.min(...floatingRects.map((rect) => rect.top));
  const floatingBottom = Math.max(...floatingRects.map((rect) => rect.bottom));
  const sampleYs = [
    ...Array.from(
      { length: 5 },
      (_, index) => floatingTop + ((floatingBottom - floatingTop) * (index + 1)) / 6,
    ),
    ...[16, 32, 48, 64, 80].map((offset) => anchorRect.top - offset),
  ].filter((y) => y >= 0 && y <= view.innerHeight);
  const candidates = new Set<HTMLElement>(knownObstacles);
  if (knownObstacles === undefined) {
    for (let xIndex = 0; xIndex <= 10; xIndex += 1) {
      const x = safeLeft + ((safeRight - safeLeft) * xIndex) / 10;
      for (const y of sampleYs) {
        for (const element of document.elementsFromPoint(x, y)) {
          if (element instanceof HTMLElement) {
            candidates.add(element);
          }
        }
      }
    }
  }
  return (
    [...candidates]
      .filter((element) => {
        if (element === host || element === anchor || element.contains(composer)) {
          return false;
        }
        const rect = element.getBoundingClientRect();
        const style = view.getComputedStyle(element);
        const centerX = rect.left + rect.width / 2;
        const gapToGoal = anchorRect.top - rect.bottom;
        return (
          rect.width >= 300 &&
          rect.width <= composerRect.width &&
          rect.height >= 24 &&
          rect.height <= 420 &&
          centerX >= composerRect.left &&
          centerX <= composerRect.right &&
          Math.abs(centerX - (composerRect.left + composerRect.width / 2)) <=
            composerRect.width * 0.25 &&
          gapToGoal >= 0 &&
          gapToGoal <= 420 &&
          Number.parseFloat(style.borderRadius) >= 8 &&
          (style.borderWidth !== "0px" ||
            style.boxShadow !== "none" ||
            style.backgroundColor !== "rgba(0, 0, 0, 0)")
        );
      })
      .sort(
        (left, right) => right.getBoundingClientRect().bottom - left.getBoundingClientRect().bottom,
      )[0]
      ?.getBoundingClientRect() ?? null
  );
}

export class SidecarMountController {
  readonly #document: Document;
  readonly #nativeGoalLocator: CodexNativeGoalLocator;
  readonly #elementName: string;
  readonly #onUiIntent:
    | ((intent: GoalProgressLocalUiIntent, context: GoalProgressLocalUiIntentContext) => void)
    | undefined;
  readonly #onUpdateIntent:
    | ((intent: GoalProgressUpdateIntent, context: GoalProgressLocalUiIntentContext) => void)
    | undefined;
  #host: GoalProgressHostElement | null = null;
  #anchor: HTMLElement | null = null;
  #controlArea: HTMLElement | null = null;
  #displayMode: GoalProgressDisplayMode = "hidden";
  #nativeGoalRejectionReason: CodexAnchorRejectionReason | null = null;
  #validatedGoalIdentity: string | null = null;
  #continuityModeActive = false;
  #fallbackInlineOriginRetained = false;
  #floatingActive = false;
  #floatingFallbackActive = false;
  #floatingFallbackRetryIndex = 0;
  #floatingFallbackRetryTimer: ReturnType<typeof setTimeout> | null = null;
  #floatingFrame: number | null = null;
  #floatingViewportTop: number | null = null;
  #floatingChecklistAligned = false;
  #floatingResizeObserver: ResizeObserver | null = null;
  #floatingObstacleObserver: MutationObserver | null = null;
  #observedFloatingObstacles = new Set<HTMLElement>();
  #floatingPreviewRatio: number | null = null;
  #lastFloatingPanelHeight = 0;
  #inlineConstraintFrame: number | null = null;
  #inlineResizeObserver: ResizeObserver | null = null;
  #inlineObservedSizeFingerprint: string | null = null;
  #observedTextbox: HTMLElement | null = null;
  #pendingInlineObserverReason: "inline-resize" | "textbox-input" | "textbox-scroll" | null = null;
  #requestedFloatingXRatio = 0.5;
  #requestedPlacement: "inline" | "floating" = "inline";
  #sessionId: string | null = null;
  #userClickActive = false;
  #userClickTimer: ReturnType<typeof setTimeout> | null = null;
  #lastAnchorState: SidecarLayoutDiagnostics["lastAnchorState"] = "none";
  #lastConstraintTransition: SidecarLayoutDiagnostics["lastConstraintTransition"] = "none";
  #lastCollapsedTransition: SidecarLayoutDiagnostics["lastCollapsedTransition"] = "none";
  #lastPlacementTransition: SidecarLayoutDiagnostics["lastPlacementTransition"] = "none";
  #layoutReadCount = 0;
  #layoutWriteCount = 0;
  #nativeGeometryFingerprint: string | null = null;
  #sidecarGeometryFingerprint: string | null = null;
  #lastHostRemovalReason: string | null = null;
  #lastObserverReason: SidecarVisibilityDiagnostics["lastObserverReason"] = "none";

  readonly #onTextboxInput = (): void => {
    this.#pendingInlineObserverReason = "textbox-input";
    this.#scheduleInlineConstraint();
  };

  readonly #onTextboxScroll = (): void => {
    this.#pendingInlineObserverReason = "textbox-scroll";
    this.#scheduleInlineConstraint();
  };

  readonly #onDocumentClick = (event: Event): void => {
    this.#userClickActive =
      event.isTrusted && this.#host !== null && event.composedPath().includes(this.#host);
    if (this.#userClickTimer) {
      clearTimeout(this.#userClickTimer);
    }
    this.#userClickTimer = setTimeout(() => {
      this.#userClickActive = false;
      this.#userClickTimer = null;
    }, 0);
  };

  readonly #onCollapsed = (event: Event): void => {
    const parsed = parseSidecarUiIntent(event);
    if (parsed?.intent.type === "setCollapsed") {
      const { collapsed } = parsed.intent;
      this.#lastCollapsedTransition = collapsed ? "user-collapsed" : "user-expanded";
      this.#emitUiIntent(parsed.intent);
    }
  };

  readonly #onMotionPaused = (event: Event): void => {
    const parsed = parseSidecarUiIntent(event);
    if (parsed?.intent.type === "setMotionPaused") {
      this.#emitUiIntent(parsed.intent);
    }
  };

  readonly #onPlacement = (event: Event): void => {
    const parsed = parseSidecarUiIntent(event);
    if (parsed?.intent.type === "setPlacement") {
      const { placement } = parsed.intent;
      this.#lastPlacementTransition = placement === "floating" ? "user-floating" : "user-inline";
      this.#requestedPlacement = placement;
      if (this.#host) {
        const wasFallback = this.#floatingFallbackActive;
        if (placement === "floating") {
          this.#floatingFallbackActive = false;
          this.#floatingViewportTop = null;
          this.#host.removeAttribute(GOAL_PROGRESS_FLOATING_FALLBACK_ATTRIBUTE);
        }
        this.#host.requestedPlacement = placement;
        this.#host.placement = placement;
        this.#syncPlacement();
        if (placement === "inline") {
          if (wasFallback) {
            this.#clearFloatingLayout();
          }
          this.#floatingFallbackActive = false;
          this.#host.removeAttribute(GOAL_PROGRESS_FLOATING_FALLBACK_ATTRIBUTE);
        }
      }
      this.#emitUiIntent(parsed.intent);
    }
  };

  readonly #onFloatingXRatio = (event: Event): void => {
    const parsed = parseSidecarUiIntent(event);
    if (parsed?.intent.type === "setFloatingXRatio") {
      const { floatingXRatio } = parsed.intent;
      const ratio = clampFloatingDockRatio(floatingXRatio);
      const commit = "commit" in parsed ? parsed.commit : true;
      if (commit) {
        this.#requestedFloatingXRatio = ratio;
        this.#floatingPreviewRatio = null;
      } else {
        this.#floatingPreviewRatio = ratio;
      }
      if (this.#host) {
        this.#host.floatingXRatio = ratio;
        this.#scheduleFloatingLayout();
      }
      if (commit) {
        this.#emitUiIntent({ ...parsed.intent, floatingXRatio: ratio });
      }
    }
  };

  readonly #onFloatingLayout = (): void => {
    this.#syncPlacement();
  };

  readonly #onWindowResize = (): void => {
    if (this.#floatingFallbackActive && this.#requestedPlacement === "floating") {
      this.#retryFloatingPlacement();
      return;
    }
    if (this.#host?.placement === "floating") {
      this.#floatingViewportTop = null;
    }
    this.#syncInlineInsets();
    this.#scheduleInlineConstraint();
    this.#scheduleFloatingLayout();
  };

  readonly #onWindowScroll = (): void => {
    if (this.#floatingFallbackActive && this.#requestedPlacement === "floating") {
      this.#retryFloatingPlacement();
      return;
    }
    this.#syncInlineInsets();
    this.#scheduleInlineConstraint();
    this.#scheduleFloatingLayout();
  };

  readonly #onLayoutOffset = (event: Event): void => {
    if (event.target !== this.#host) {
      return;
    }
    const expandedOffset = parseExpandedLayoutOffset(event);
    if (expandedOffset !== null) {
      this.#applyLayoutOffset(expandedOffset);
      this.#scheduleInlineConstraint();
    }
  };

  readonly #onRetry = (): void => {
    this.#emitUiIntent({ type: "requestRetry" });
  };

  readonly #onDetach = (): void => {
    this.#emitUiIntent({ type: "requestDetach" });
  };

  readonly #onUpdate = (event: Event): void => {
    const intent = parseGoalProgressUpdateIntent(
      "detail" in event ? (event as CustomEvent<unknown>).detail : undefined,
    );
    if (!intent) {
      return;
    }
    this.#onUpdateIntent?.(intent, {
      userActivated: this.#userClickActive,
    });
  };

  constructor(document: Document, options: SidecarMountControllerOptions) {
    this.#document = document;
    this.#nativeGoalLocator = options.nativeGoalLocator;
    this.#elementName = options.elementName ?? GOAL_PROGRESS_ELEMENT_NAME;
    this.#onUiIntent = options.onUiIntent;
    this.#onUpdateIntent = options.onUpdateIntent;
  }

  ensureMounted(
    viewModel: GoalProgressViewModel,
    uiPreference: GoalProgressUiPreference | undefined,
    options: SidecarEnsureMountedOptions,
  ): SidecarMountResult {
    const existingHosts = hosts(this.#document);
    if (existingHosts.length > 1) {
      return this.#result("none", "host-ambiguous", existingHosts.length, false, null);
    }
    const existingHost = existingHosts[0] ?? null;
    if (existingHost && !isManagedHost(existingHost)) {
      return this.#result("none", "host-unmanaged", 1, false, null);
    }
    if (
      options.environmentChanged &&
      this.#floatingFallbackActive &&
      this.#floatingFallbackRetryTimer === null &&
      this.#floatingFallbackRetryIndex >= GOAL_PROGRESS_FLOATING_FALLBACK_RETRY_DELAYS_MS.length
    ) {
      this.#floatingFallbackRetryIndex = 0;
      this.#retryFloatingPlacement();
    }

    this.#nativeGoalRejectionReason = options.nativeGoalRejectionReason ?? null;
    if (options.displayTarget.kind === "fallback") {
      return this.#ensureFallbackMounted(
        viewModel,
        uiPreference,
        existingHost,
        options.updateState ?? null,
      );
    }

    const anchor = options.displayTarget.anchor;
    if (existingHost && anchor && (this.#anchor || this.#displayMode === "fallback")) {
      const identityFailure = this.#continuityIdentityFailure(
        anchor,
        options.displayTarget.goalIdentity,
      );
      if (
        identityFailure &&
        !preparingViewMatchesGoalIdentity(viewModel, options.displayTarget.goalIdentity)
      ) {
        this.#lastAnchorState = "unavailable";
        this.#lastHostRemovalReason = identityFailure;
        this.#adoptHost(existingHost);
        this.#releaseHost(true);
        return this.#result(
          "unmounted",
          "native-goal-changed",
          hosts(this.#document).length,
          false,
          this.#nativeGoalRejectionReason,
        );
      }
    }
    if (!anchor?.parentElement) {
      this.#lastAnchorState = "unavailable";
      this.#lastHostRemovalReason = "anchor-unavailable";
      const action = existingHost ? "unmounted" : "none";
      if (existingHost) {
        this.#adoptHost(existingHost);
      }
      this.#releaseHost(true);
      return this.#result(
        action,
        "anchor-unavailable",
        hosts(this.#document).length,
        false,
        this.#nativeGoalRejectionReason,
      );
    }
    this.#lastAnchorState = "live";
    this.#lastHostRemovalReason = null;
    this.#continuityModeActive = false;

    let host = existingHost;
    let action: SidecarMountAction = "updated";
    if (!host) {
      this.#releaseHost(false);
      host = this.#document.createElement(this.#elementName) as GoalProgressHostElement;
      host.setAttribute(GOAL_PROGRESS_HOST_ATTRIBUTE, GOAL_PROGRESS_HOST_ATTRIBUTE_VALUE);
      action = "mounted";
    }
    this.#adoptHost(host);
    syncHostLocale(host, this.#document);
    const preserveVisibleCollapsed =
      action === "updated" && this.#sessionId === viewModel.sessionId;
    const visibleCollapsed = host.collapsed;

    if (anchor.nextSibling !== host) {
      anchor.parentElement.insertBefore(host, anchor.nextSibling);
    }
    this.#clearFallbackLayout();
    this.#fallbackInlineOriginRetained = false;
    this.#displayMode = "native";
    this.#controlArea = options.displayTarget.controlArea;
    this.#syncNativeTitleFontWeight(options.displayTarget.goalTitleFontWeight ?? null);
    this.#adoptAnchor(anchor, options.displayTarget.goalIdentity);

    const threadChanged = this.#sessionId !== null && this.#sessionId !== viewModel.sessionId;
    if (threadChanged) {
      host.viewModel = null;
    }
    host.viewModel = viewModel;
    host.updateState = options.updateState ?? null;
    if (uiPreference) {
      const requestedPlacement = uiPreference.placement;
      const preserveFallback = this.#floatingFallbackActive && requestedPlacement === "floating";
      if (this.#floatingFallbackActive && !preserveFallback) {
        this.#clearFloatingLayout();
      }
      this.#requestedPlacement = requestedPlacement;
      const requestedFloatingXRatio = clampFloatingDockRatio(uiPreference.floatingXRatio);
      this.#requestedFloatingXRatio = requestedFloatingXRatio;
      this.#floatingPreviewRatio = null;
      this.#lastCollapsedTransition = uiPreference.collapsed
        ? "preference-collapsed"
        : "preference-expanded";
      this.#lastPlacementTransition =
        requestedPlacement === "floating" ? "preference-floating" : "preference-inline";
      if (!preserveFallback) {
        this.#floatingFallbackActive = false;
        host.removeAttribute(GOAL_PROGRESS_FLOATING_FALLBACK_ATTRIBUTE);
      }
      host.collapsed = preserveVisibleCollapsed ? visibleCollapsed : uiPreference.collapsed;
      host.motionPaused = uiPreference.motionPaused;
      host.hidden = uiPreference.hidden;
      host.requestedPlacement = requestedPlacement;
      host.placement =
        preserveFallback || requiresInlineState(viewModel) ? "inline" : requestedPlacement;
      host.floatingXRatio = requestedFloatingXRatio;
    }
    if (host.placement !== "inline" || host.collapsed) {
      host.spaceConstrained = false;
    }
    if (options.environmentChanged && host.placement === "inline") {
      this.#pendingInlineObserverReason ??= "inline-resize";
    }
    this.#syncPlacement();
    this.#sessionId = viewModel.sessionId;
    return this.#result(
      action,
      "ok",
      hosts(this.#document).length,
      threadChanged,
      this.#nativeGoalRejectionReason,
    );
  }

  canRetainCurrentSession(sessionId: string): boolean {
    return this.#retentionFailureReason(sessionId) === null;
  }

  managedHostElement(): HTMLElement | null {
    return this.#host;
  }

  retainCurrentSession(
    viewModel: GoalProgressViewModel,
    uiPreference?: GoalProgressUiPreference,
    updateState?: GoalProgressUpdateState | null,
  ): SidecarMountResult {
    const retentionFailure = this.#retentionFailureReason(viewModel.sessionId);
    if (retentionFailure) {
      return this.#result(
        "none",
        retentionFailure,
        hosts(this.#document).length,
        false,
        this.#nativeGoalRejectionReason,
      );
    }
    const host = this.#host as GoalProgressHostElement;
    if (this.#displayMode === "native" && this.#anchor) {
      const location = this.#nativeGoalLocator.locate(this.#document);
      if (
        location.target &&
        this.#continuityIdentityFailure(location.target.anchor, location.target.goalIdentity)
      ) {
        this.#lastAnchorState = "unavailable";
        this.#lastHostRemovalReason = "continuity-goal-changed";
        this.#releaseHost(true);
        return this.#result(
          "unmounted",
          "visible-thread-marker-missing",
          hosts(this.#document).length,
          false,
          location.rejectionReason,
        );
      }
    }
    syncHostLocale(host, this.#document);
    host.viewModel = viewModel;
    host.updateState = updateState ?? null;
    if (uiPreference) {
      host.motionPaused = uiPreference.motionPaused;
      host.hidden = uiPreference.hidden;
    }
    this.#continuityModeActive = true;
    this.#sessionId = viewModel.sessionId;
    return this.#result("updated", "ok", hosts(this.#document).length, false, null);
  }

  #retentionFailureReason(
    sessionId: string,
  ): "host-ambiguous" | "host-unmanaged" | "host-missing" | null {
    const existingHosts = hosts(this.#document);
    if (existingHosts.length > 1) {
      return "host-ambiguous";
    }
    const existingHost = existingHosts[0] ?? null;
    if (!existingHost) {
      return "host-missing";
    }
    if (!isManagedHost(existingHost)) {
      return "host-unmanaged";
    }
    if (
      this.#host !== existingHost ||
      !existingHost.isConnected ||
      this.#sessionId !== sessionId ||
      existingHost.viewModel?.sessionId !== sessionId
    ) {
      return "host-missing";
    }
    return null;
  }

  #ensureFallbackMounted(
    viewModel: GoalProgressViewModel,
    uiPreference: GoalProgressUiPreference | undefined,
    existingHost: GoalProgressHostElement | null,
    updateState: GoalProgressUpdateState | null,
  ): SidecarMountResult {
    const threadChanged = this.#sessionId !== null && this.#sessionId !== viewModel.sessionId;
    const nativeOriginWasVerified =
      this.#displayMode === "native" || this.#displayMode === "fallback";
    if (!existingHost || threadChanged || !nativeOriginWasVerified) {
      if (existingHost) {
        this.#adoptHost(existingHost);
      }
      this.#lastAnchorState = "unavailable";
      this.#lastHostRemovalReason = "anchor-unavailable";
      const action = existingHost || this.#host ? "unmounted" : "none";
      this.#releaseHost(true);
      return this.#result(
        action,
        "anchor-unavailable",
        hosts(this.#document).length,
        threadChanged,
        this.#nativeGoalRejectionReason,
      );
    }
    const host = existingHost;
    const action: SidecarMountAction = "updated";
    this.#adoptHost(host);
    this.#syncNativeTitleFontWeight(null);
    syncHostLocale(host, this.#document);
    const preserveVisibleCollapsed =
      action === "updated" && this.#sessionId === viewModel.sessionId;
    const visibleCollapsed = host.collapsed;
    host.viewModel = viewModel;
    host.updateState = updateState;
    if (uiPreference) {
      this.#requestedPlacement = uiPreference.placement;
      this.#requestedFloatingXRatio = clampFloatingDockRatio(uiPreference.floatingXRatio);
      this.#floatingPreviewRatio = null;
      this.#lastCollapsedTransition = uiPreference.collapsed
        ? "preference-collapsed"
        : "preference-expanded";
      host.collapsed = preserveVisibleCollapsed ? visibleCollapsed : uiPreference.collapsed;
      host.motionPaused = uiPreference.motionPaused;
      host.hidden = uiPreference.hidden;
      host.requestedPlacement = uiPreference.placement;
      host.floatingXRatio = this.#requestedFloatingXRatio;
    }
    const canRetainInlineOrigin =
      this.#requestedPlacement === "inline" &&
      !threadChanged &&
      (this.#displayMode === "native" || this.#fallbackInlineOriginRetained);
    host.placement = requiresInlineState(host.viewModel) ? "inline" : this.#requestedPlacement;
    host.spaceConstrained = false;
    host.floatingPanelConstrained = false;
    const retainInlineOrigin =
      canRetainInlineOrigin &&
      host.parentElement !== null &&
      host.parentElement !== this.#document.body;
    if (this.#requestedPlacement === "inline" && !retainInlineOrigin) {
      this.#lastAnchorState = "unavailable";
      this.#lastHostRemovalReason = "anchor-unavailable";
      this.#releaseHost(true);
      return this.#result(
        "unmounted",
        "anchor-unavailable",
        hosts(this.#document).length,
        false,
        this.#nativeGoalRejectionReason,
      );
    }
    this.#clearInlineConstraintObserver();
    this.#clearFloatingLayout();
    this.#restoreAnchor(true);
    this.#controlArea = null;
    this.#fallbackInlineOriginRetained = retainInlineOrigin;
    if (retainInlineOrigin) {
      this.#clearFallbackLayout();
    } else {
      this.#document.body.append(host);
      this.#applyFallbackLayout();
    }
    this.#lastAnchorState = "unavailable";
    this.#lastHostRemovalReason = null;
    this.#continuityModeActive = false;
    this.#displayMode = "fallback";
    this.#sessionId = viewModel.sessionId;
    return this.#result(
      action,
      "ok",
      hosts(this.#document).length,
      threadChanged,
      this.#nativeGoalRejectionReason,
    );
  }

  unmount(): SidecarMountResult {
    const existingHosts = hosts(this.#document);
    if (existingHosts.length > 1) {
      return this.#result("none", "host-ambiguous", existingHosts.length, false, null);
    }
    const existingHost = existingHosts[0] ?? null;
    if (existingHost && !isManagedHost(existingHost)) {
      return this.#result("none", "host-unmanaged", 1, false, null);
    }
    if (existingHost) {
      this.#adoptHost(existingHost);
    }
    this.#lastHostRemovalReason = "explicit-unmount";
    const action = existingHost || this.#host ? "unmounted" : "none";
    this.#releaseHost(true);
    return this.#result(action, "ok", hosts(this.#document).length, false, null);
  }

  setUpdateState(updateState: GoalProgressUpdateState | null): SidecarMountResult {
    const existingHosts = hosts(this.#document);
    if (existingHosts.length > 1) {
      return this.#result("none", "host-ambiguous", existingHosts.length, false, null);
    }
    const host = existingHosts[0] ?? null;
    if (!host) {
      return this.#result("none", "host-missing", 0, false, null);
    }
    if (!isManagedHost(host)) {
      return this.#result("none", "host-unmanaged", 1, false, null);
    }
    this.#adoptHost(host);
    host.updateState = updateState;
    return this.#result("updated", "ok", 1, false, this.#nativeGoalRejectionReason);
  }

  health(): SidecarHealthResult {
    const existingHosts = hosts(this.#document);
    if (existingHosts.length > 1) {
      return this.#healthResult("blocked", "host-ambiguous", existingHosts.length, null);
    }
    const host = existingHosts[0] ?? null;
    if (host && !isManagedHost(host)) {
      return this.#healthResult("blocked", "host-unmanaged", 1, null);
    }
    if (
      this.#continuityModeActive &&
      this.#sessionId !== null &&
      this.#retentionFailureReason(this.#sessionId) === null
    ) {
      return this.#healthResult("mounted", "ok", 1, this.#nativeGoalRejectionReason);
    }
    if (this.#displayMode === "fallback") {
      if (!host) {
        return this.#healthResult("unmounted", "host-missing", 0, this.#nativeGoalRejectionReason);
      }
      if (!this.#fallbackInlineOriginRetained && host.parentElement !== this.#document.body) {
        return this.#healthResult("blocked", "host-misplaced", 1, this.#nativeGoalRejectionReason);
      }
      return this.#healthResult("mounted", "ok", 1, this.#nativeGoalRejectionReason);
    }
    const location = this.#nativeGoalLocator.locate(this.#document);
    const anchor = location.target?.anchor ?? null;
    if (!anchor?.parentElement) {
      return this.#healthResult(
        "unmounted",
        "anchor-unavailable",
        existingHosts.length,
        location.rejectionReason,
      );
    }
    if (!host) {
      return this.#healthResult("unmounted", "host-missing", 0, null);
    }
    if (
      this.#anchor &&
      this.#continuityIdentityFailure(anchor, location.target?.goalIdentity ?? null)
    ) {
      return this.#healthResult("blocked", "native-goal-changed", 1, null);
    }
    if (anchor.nextSibling !== host) {
      return this.#healthResult("blocked", "host-misplaced", 1, null);
    }
    return this.#healthResult("mounted", "ok", 1, null);
  }

  diagnostics(): SidecarLayoutDiagnostics {
    return projectSidecarDiagnostics({
      host: this.#host,
      anchor: this.#anchor,
      document: this.#document,
      lastAnchorState: this.#lastAnchorState,
      lastConstraintTransition: this.#lastConstraintTransition,
      lastCollapsedTransition: this.#lastCollapsedTransition,
      lastPlacementTransition: this.#lastPlacementTransition,
      layoutReadCount: this.#layoutReadCount,
      layoutWriteCount: this.#layoutWriteCount,
      nativeGeometryFingerprint: this.#nativeGeometryFingerprint,
      sidecarGeometryFingerprint: this.#sidecarGeometryFingerprint,
      continuityModeActive: this.#continuityModeActive,
      requestedPlacement: this.#requestedPlacement,
      floatingFallbackActive: this.#floatingFallbackActive,
      lastHostRemovalReason: this.#lastHostRemovalReason,
      lastObserverReason: this.#lastObserverReason,
    });
  }

  #adoptHost(host: GoalProgressHostElement): void {
    if (this.#host === host) {
      return;
    }
    this.#releaseHost(false);
    this.#host = host;
    host.addEventListener(GOAL_PROGRESS_LAYOUT_OFFSET_EVENT, this.#onLayoutOffset);
    host.addEventListener(GOAL_PROGRESS_FLOATING_LAYOUT_EVENT, this.#onFloatingLayout);
    host.addEventListener(GOAL_PROGRESS_SET_PLACEMENT_EVENT, this.#onPlacement);
    host.addEventListener(GOAL_PROGRESS_SET_FLOATING_X_RATIO_EVENT, this.#onFloatingXRatio);
    this.#sessionId =
      host.viewModel && typeof host.viewModel.sessionId === "string"
        ? host.viewModel.sessionId
        : null;
    if (this.#onUiIntent) {
      this.#document.addEventListener("click", this.#onDocumentClick, true);
      host.addEventListener(GOAL_PROGRESS_SET_COLLAPSED_EVENT, this.#onCollapsed);
      host.addEventListener(GOAL_PROGRESS_SET_MOTION_PAUSED_EVENT, this.#onMotionPaused);
      host.addEventListener(GOAL_PROGRESS_REQUEST_RETRY_EVENT, this.#onRetry);
      host.addEventListener(GOAL_PROGRESS_REQUEST_DETACH_EVENT, this.#onDetach);
    }
    if (this.#onUpdateIntent) {
      this.#document.addEventListener("click", this.#onDocumentClick, true);
      host.addEventListener(GOAL_PROGRESS_UPDATE_INTENT_EVENT, this.#onUpdate);
    }
  }

  #adoptAnchor(anchor: HTMLElement, goalIdentity: string | null): void {
    if (this.#anchor === anchor) {
      this.#validatedGoalIdentity ??= goalIdentity;
      return;
    }
    this.#restoreAnchor();
    this.#anchor = anchor;
    this.#validatedGoalIdentity = goalIdentity;
    const expandedOffset = this.#host?.expandedLayoutOffset;
    this.#applyLayoutOffset(
      typeof expandedOffset === "number" && Number.isFinite(expandedOffset) ? expandedOffset : 0,
    );
    this.#observeInlineConstraint();
  }

  #continuityIdentityFailure(
    anchor: HTMLElement,
    currentGoalIdentity: string | null,
  ): string | null {
    if (anchor === this.#anchor) {
      if (this.#validatedGoalIdentity === null || currentGoalIdentity === null) {
        return null;
      }
      return currentGoalIdentity === this.#validatedGoalIdentity ? null : "continuity-goal-changed";
    }
    if (this.#validatedGoalIdentity === null || currentGoalIdentity === null) {
      return "continuity-goal-unavailable";
    }
    return currentGoalIdentity === this.#validatedGoalIdentity ? null : "continuity-goal-changed";
  }

  #applyLayoutOffset(_expandedOffset: number): void {
    const host = this.#host;
    const anchor = this.#anchor;
    if (!host || !anchor) {
      return;
    }
    if (host.placement === "floating") {
      host.style.marginBlockStart = "";
      this.#clearInlineInsets();
      this.#resetAnchorTranslate(anchor);
      this.#scheduleFloatingLayout();
      return;
    }
    this.#clearFloatingLayout(this.#floatingFallbackActive);
    const parentGap = anchor.parentElement
      ? Number.parseFloat(
          this.#document.defaultView?.getComputedStyle(anchor.parentElement).rowGap ?? "0",
        ) || 0
      : 0;
    host.style.marginBlockStart = `${-(Math.max(0, parentGap) + 1)}px`;
    this.#syncInlineInsets();
    this.#resetAnchorTranslate(anchor);
  }

  #syncInlineInsets(): void {
    const host = this.#host;
    const anchor = this.#anchor;
    const view = this.#document.defaultView;
    if (!host || !anchor || !view) {
      return;
    }
    this.#layoutReadCount += 1;
    const style = view.getComputedStyle(anchor);
    const anchorRect = anchor.getBoundingClientRect();
    const composer = anchor.closest<HTMLElement>("[data-codex-composer-root]");
    const composerRect = composer?.getBoundingClientRect() ?? null;
    const hostRect = host.getBoundingClientRect();
    const hostCssWidth = Number.parseFloat(view.getComputedStyle(host).width);
    const scale =
      Number.isFinite(hostCssWidth) &&
      hostCssWidth > 0 &&
      Number.isFinite(hostRect.width) &&
      hostRect.width > 0
        ? hostRect.width / hostCssWidth
        : 1;
    const controlArea = this.#controlArea;
    const controlRect = controlArea?.getBoundingClientRect() ?? null;
    this.#nativeGeometryFingerprint = [
      rectFingerprint(anchorRect),
      rectFingerprint(composerRect),
      rectFingerprint(controlRect),
    ].join("|");
    const direction = style.direction === "rtl" ? "rtl" : "ltr";
    const composerStyle = composer ? view.getComputedStyle(composer) : null;
    const composerContentLeft =
      composerRect === null
        ? null
        : composerRect.left +
          ((Number.parseFloat(composerStyle?.borderLeftWidth ?? "0") || 0) +
            (Number.parseFloat(composerStyle?.paddingLeft ?? "0") || 0)) *
            scale;
    const composerContentRight =
      composerRect === null
        ? null
        : composerRect.right -
          ((Number.parseFloat(composerStyle?.borderRightWidth ?? "0") || 0) +
            (Number.parseFloat(composerStyle?.paddingRight ?? "0") || 0)) *
            scale;
    const startBoundaryGap =
      composerContentLeft === null || composerContentRight === null
        ? 0
        : direction === "rtl"
          ? composerContentRight - anchorRect.right
          : anchorRect.left - composerContentLeft;
    const endBoundaryGap =
      composerContentLeft === null || composerContentRight === null
        ? 0
        : direction === "rtl"
          ? anchorRect.left - composerContentLeft
          : composerContentRight - anchorRect.right;
    const start =
      Math.max(0, startBoundaryGap / scale) + (Number.parseFloat(style.paddingInlineStart) || 0);
    const end =
      Math.max(0, endBoundaryGap / scale) + (Number.parseFloat(style.paddingInlineEnd) || 0);
    const availableWidth =
      composerContentLeft === null || composerContentRight === null
        ? anchorRect.width / scale
        : (composerContentRight - composerContentLeft) / scale;
    const valid =
      Number.isFinite(scale) &&
      scale > 0 &&
      Number.isFinite(start) &&
      Number.isFinite(end) &&
      start >= 0 &&
      end >= 0 &&
      Number.isFinite(availableWidth) &&
      availableWidth > 0 &&
      start + end < availableWidth * 0.5;
    if (!valid) {
      return;
    }
    this.#layoutWriteCount += 1;
    host.style.marginInlineStart = valid && start > 0 ? `${start}px` : "";
    host.style.marginInlineEnd = valid && end > 0 ? `${end}px` : "";
    if (controlArea) {
      const hostRect = host.getBoundingClientRect();
      const controlRect = controlArea.getBoundingClientRect();
      const controlStart = controlRect.left - hostRect.left;
      if (Number.isFinite(controlStart) && controlStart >= 0 && controlStart <= hostRect.width) {
        host.style.setProperty("--gp-native-control-start", `${controlStart}px`);
      } else {
        host.style.removeProperty("--gp-native-control-start");
      }
      const lastControl = [...controlArea.querySelectorAll<HTMLElement>('button[type="button"]')]
        .filter((button) => button.getBoundingClientRect().width > 0)
        .sort(
          (left, right) => left.getBoundingClientRect().left - right.getBoundingClientRect().left,
        )
        .at(-1);
      if (lastControl) {
        const lastRect = lastControl.getBoundingClientRect();
        const overall = host.shadowRoot?.querySelector<HTMLElement>(".overall") ?? null;
        const overallRect = overall?.getBoundingClientRect();
        const overallWidth = overall
          ? Number.parseFloat(view.getComputedStyle(overall).width)
          : Number.NaN;
        const scale =
          overallRect && Number.isFinite(overallWidth) && overallWidth > 0
            ? overallRect.width / overallWidth
            : Number.NaN;
        const center =
          overallRect === undefined || !Number.isFinite(scale) || scale <= 0
            ? Number.NaN
            : (lastRect.left + lastRect.width / 2 - overallRect.left) / scale;
        if (overallRect && Number.isFinite(center) && center >= 0 && center <= overallWidth) {
          host.style.setProperty("--gp-native-last-control-center", `${center}px`);
        } else {
          host.style.removeProperty("--gp-native-last-control-center");
        }
      } else {
        host.style.removeProperty("--gp-native-last-control-center");
      }
    } else {
      host.style.removeProperty("--gp-native-control-start");
      host.style.removeProperty("--gp-native-last-control-center");
    }
    const overallRect =
      host.shadowRoot?.querySelector<HTMLElement>(".overall")?.getBoundingClientRect() ?? null;
    this.#sidecarGeometryFingerprint = [
      rectFingerprint(host.getBoundingClientRect()),
      rectFingerprint(overallRect),
    ].join("|");
  }

  #clearInlineInsets(): void {
    if (!this.#host) {
      return;
    }
    this.#host.style.marginInlineStart = "";
    this.#host.style.marginInlineEnd = "";
  }

  #syncNativeTitleFontWeight(fontWeight: number | null): void {
    const host = this.#host;
    if (!host) {
      return;
    }
    if (
      fontWeight !== null &&
      Number.isFinite(fontWeight) &&
      fontWeight >= 1 &&
      fontWeight <= 1_000
    ) {
      host.style.setProperty("--gp-native-title-font-weight", String(fontWeight));
      return;
    }
    host.style.removeProperty("--gp-native-title-font-weight");
  }

  #clearMeasuredInlineGeometry(): void {
    const host = this.#host;
    if (!host) {
      return;
    }
    const hadMeasuredGeometry =
      host.style.marginInlineStart !== "" ||
      host.style.marginInlineEnd !== "" ||
      host.style.getPropertyValue("--gp-native-control-start") !== "" ||
      host.style.getPropertyValue("--gp-native-last-control-center") !== "";
    host.style.marginInlineStart = "";
    host.style.marginInlineEnd = "";
    host.style.removeProperty("--gp-native-control-start");
    host.style.removeProperty("--gp-native-last-control-center");
    this.#sidecarGeometryFingerprint = null;
    if (hadMeasuredGeometry) {
      this.#layoutWriteCount += 1;
    }
  }

  #applyFallbackLayout(): void {
    const host = this.#host;
    if (!host) {
      return;
    }
    const view = this.#document.defaultView;
    const composers = this.#document.querySelectorAll<HTMLElement>("[data-codex-composer-root]");
    const composer = composers.length === 1 ? (composers[0] ?? null) : null;
    const composerRect =
      composer && typeof composer.getBoundingClientRect === "function"
        ? composer.getBoundingClientRect()
        : null;
    const surfaceHeight =
      host.shadowRoot
        ?.querySelector<HTMLElement>(".floating-chip, .phase-error .state")
        ?.getBoundingClientRect().height ?? 38;
    const fallbackBottom =
      view && composerRect
        ? Math.max(
            8,
            view.innerHeight -
              Math.max(surfaceHeight + 8, Math.min(view.innerHeight - 8, composerRect.top - 8)),
          )
        : 96;
    host.style.position = "fixed";
    host.style.insetInlineEnd = "16px";
    host.style.bottom = `${fallbackBottom}px`;
    host.style.left = "";
    host.style.top = "";
    host.style.width = "min(420px, calc(100vw - 32px))";
    host.style.maxWidth = "calc(100vw - 32px)";
    host.style.height = "";
    host.style.zIndex = "30";
    host.style.pointerEvents = "auto";
    host.style.marginBlockStart = "";
    host.style.removeProperty("--gp-native-title-font-weight");
    this.#clearMeasuredInlineGeometry();
    this.#layoutWriteCount += 1;
  }

  #clearFallbackLayout(): void {
    const host = this.#host;
    if (!host) {
      return;
    }
    host.style.insetInlineEnd = "";
    host.style.bottom = "";
    host.style.maxWidth = "";
    host.style.position = "";
    host.style.left = "";
    host.style.width = "";
    host.style.zIndex = "";
    host.style.pointerEvents = "";
  }

  #syncPlacement(): void {
    const host = this.#host;
    if (!host) {
      return;
    }
    // Preparing state uses normal height; errors retain the user's compact floating position.
    if (requiresInlineState(host.viewModel)) {
      host.placement = "inline";
    }
    if (this.#displayMode === "fallback") {
      host.placement = requiresInlineState(host.viewModel) ? "inline" : this.#requestedPlacement;
      host.spaceConstrained = false;
      if (
        this.#fallbackInlineOriginRetained &&
        this.#requestedPlacement === "inline" &&
        host.parentElement !== this.#document.body
      ) {
        this.#clearFallbackLayout();
        return;
      }
      if (this.#requestedPlacement === "inline") {
        this.#releaseHost(true);
        return;
      }
      this.#fallbackInlineOriginRetained = false;
      if (host.parentElement !== this.#document.body) {
        this.#document.body.append(host);
      }
      this.#applyFallbackLayout();
      return;
    }
    if (host.placement === "floating") {
      host.style.marginBlockStart = "";
      this.#clearInlineInsets();
      if (this.#anchor) {
        this.#resetAnchorTranslate(this.#anchor);
      }
      this.#observeFloatingLayout();
      this.#scheduleFloatingLayout();
      return;
    }
    host.floatingPanelConstrained = false;
    this.#clearFloatingLayout(this.#floatingFallbackActive);
    const expandedOffset = host.expandedLayoutOffset;
    this.#applyLayoutOffset(
      typeof expandedOffset === "number" && Number.isFinite(expandedOffset) ? expandedOffset : 0,
    );
    this.#observeInlineConstraint();
    this.#scheduleInlineConstraint();
  }

  #observeInlineConstraint(): void {
    const host = this.#host;
    const anchor = this.#anchor;
    const view = this.#document.defaultView;
    if (!host || !anchor || !view || host.placement !== "inline") {
      this.#clearInlineConstraintObserver();
      return;
    }
    const composer = anchor.closest<HTMLElement>("[data-codex-composer-root]");
    const textbox = composer?.querySelector<HTMLElement>('[role="textbox"][data-codex-composer]');
    const ResizeObserverCtor = view.ResizeObserver;
    if (!composer || !textbox) {
      this.#clearInlineConstraintObserver();
      return;
    }
    if (this.#observedTextbox !== textbox) {
      this.#observedTextbox?.removeEventListener("input", this.#onTextboxInput);
      this.#observedTextbox?.removeEventListener("scroll", this.#onTextboxScroll);
      this.#observedTextbox = textbox;
      textbox.addEventListener("input", this.#onTextboxInput);
      textbox.addEventListener("scroll", this.#onTextboxScroll);
    }
    if (ResizeObserverCtor) {
      this.#inlineObservedSizeFingerprint = [
        composer.clientWidth,
        composer.clientHeight,
        textbox.clientWidth,
        textbox.clientHeight,
      ].join(",");
      this.#inlineResizeObserver ??= new ResizeObserverCtor(() => {
        const currentComposer = this.#anchor?.closest<HTMLElement>("[data-codex-composer-root]");
        const currentTextbox = currentComposer?.querySelector<HTMLElement>(
          '[role="textbox"][data-codex-composer]',
        );
        if (!currentComposer || !currentTextbox) {
          return;
        }
        const nextSizeFingerprint = [
          currentComposer.clientWidth,
          currentComposer.clientHeight,
          currentTextbox.clientWidth,
          currentTextbox.clientHeight,
        ].join(",");
        if (nextSizeFingerprint === this.#inlineObservedSizeFingerprint) {
          return;
        }
        this.#inlineObservedSizeFingerprint = nextSizeFingerprint;
        this.#pendingInlineObserverReason ??= "inline-resize";
        this.#syncInlineInsets();
        this.#scheduleInlineConstraint();
      });
      this.#inlineResizeObserver.disconnect();
      this.#inlineResizeObserver.observe(composer);
      this.#inlineResizeObserver.observe(textbox);
    }
  }

  #scheduleInlineConstraint(): void {
    const host = this.#host;
    const view = this.#document.defaultView;
    if (!host || !view || host.placement !== "inline" || this.#inlineConstraintFrame !== null) {
      return;
    }
    this.#inlineConstraintFrame = view.requestAnimationFrame(() => {
      this.#inlineConstraintFrame = null;
      if (this.#pendingInlineObserverReason) {
        this.#lastObserverReason = this.#pendingInlineObserverReason;
        this.#pendingInlineObserverReason = null;
      }
      this.#syncInlineInsets();
      this.#syncInlineConstraint();
    });
  }

  #syncInlineConstraint(): void {
    const host = this.#host;
    if (host?.placement !== "inline" || !host.spaceConstrained) {
      return;
    }
    host.spaceConstrained = false;
    this.#layoutWriteCount += 1;
    this.#lastConstraintTransition = "exited";
  }

  #clearInlineConstraintObserver(): void {
    const view = this.#document.defaultView;
    if (view && this.#inlineConstraintFrame !== null) {
      view.cancelAnimationFrame(this.#inlineConstraintFrame);
    }
    this.#inlineConstraintFrame = null;
    this.#inlineResizeObserver?.disconnect();
    this.#inlineResizeObserver = null;
    this.#inlineObservedSizeFingerprint = null;
    this.#observedTextbox?.removeEventListener("input", this.#onTextboxInput);
    this.#observedTextbox?.removeEventListener("scroll", this.#onTextboxScroll);
    this.#observedTextbox = null;
    this.#pendingInlineObserverReason = null;
  }

  #scheduleFloatingLayout(): void {
    if (this.#host?.placement !== "floating") {
      return;
    }
    const view = this.#document.defaultView;
    if (!view || this.#floatingFrame !== null) {
      return;
    }
    this.#floatingFrame = view.requestAnimationFrame(() => {
      this.#floatingFrame = null;
      this.#applyFloatingLayout();
    });
  }

  #observeFloatingLayout(chip: HTMLElement | null = null, panel: HTMLElement | null = null): void {
    const host = this.#host;
    const anchor = this.#anchor;
    const view = this.#document.defaultView;
    if (!host || !anchor || !view || host.placement !== "floating") {
      return;
    }
    const ResizeObserverCtor = view.ResizeObserver;
    if (!ResizeObserverCtor) {
      return;
    }
    this.#floatingResizeObserver ??= new ResizeObserverCtor((entries) => {
      this.#lastObserverReason = "floating-resize";
      const composer = this.#anchor?.closest<HTMLElement>("[data-codex-composer-root]");
      const textbox = composer?.querySelector<HTMLElement>('[role="textbox"][data-codex-composer]');
      if (entries.some((entry) => entry.target === composer || entry.target === textbox)) {
        this.#floatingViewportTop = null;
      }
      if (!this.#floatingFallbackActive) {
        this.#scheduleFloatingLayout();
      }
    });
    const composer = anchor.closest<HTMLElement>("[data-codex-composer-root]");
    const textbox = composer?.querySelector<HTMLElement>('[role="textbox"][data-codex-composer]');
    this.#floatingResizeObserver.observe(anchor);
    if (composer) {
      this.#floatingResizeObserver.observe(composer);
    }
    if (textbox) {
      this.#floatingResizeObserver.observe(textbox);
    }
    if (chip) {
      this.#floatingResizeObserver.observe(chip);
    }
    if (panel) {
      this.#floatingResizeObserver.observe(panel);
    }
    this.#observeFloatingObstacleChanges();
  }

  #readFloatingObstacles(): readonly HTMLElement[] {
    return (this.#nativeGoalLocator.findFloatingObstacles?.(this.#document) ?? []).filter(
      (element) => element.isConnected,
    );
  }

  #observeFloatingObstacleChanges(): void {
    const host = this.#host;
    const view = this.#document.defaultView;
    const MutationObserverCtor = view?.MutationObserver;
    if (!host || !view || !MutationObserverCtor || host.placement !== "floating") {
      return;
    }
    this.#observedFloatingObstacles = new Set(this.#readFloatingObstacles());
    if (this.#floatingObstacleObserver) {
      return;
    }
    this.#floatingObstacleObserver = new MutationObserverCtor((records) => {
      const previous = this.#observedFloatingObstacles;
      const next = new Set(this.#readFloatingObstacles());
      const membershipChanged =
        previous.size !== next.size ||
        [...previous].some((element) => !next.has(element)) ||
        [...next].some((element) => !previous.has(element));
      const known = new Set([...previous, ...next]);
      const touchesKnownObstacle = records.some((record) => {
        const changedNodes = [record.target, ...record.addedNodes, ...record.removedNodes];
        return changedNodes.some((node) =>
          [...known].some(
            (obstacle) =>
              node === obstacle ||
              (node instanceof Element && (node.contains(obstacle) || obstacle.contains(node))),
          ),
        );
      });
      this.#observedFloatingObstacles = next;
      if (membershipChanged || touchesKnownObstacle) {
        this.#scheduleFloatingLayout();
      }
    });
    this.#floatingObstacleObserver.observe(this.#document.body, {
      attributes: true,
      attributeFilter: ["aria-hidden", "class", "hidden", "style"],
      childList: true,
      subtree: true,
    });
  }

  #applyFloatingLayout(): void {
    const host = this.#host;
    const anchor = this.#anchor;
    const view = this.#document.defaultView;
    if (!host || !anchor || !view || host.placement !== "floating") {
      return;
    }
    this.#layoutReadCount += 1;
    this.#clearInlineInsets();
    const anchorRect = anchor.getBoundingClientRect();
    const goalBlockRect = floatingGoalBlockRect(anchor);
    const left = Math.max(8, goalBlockRect.left);
    const right = Math.min(view.innerWidth - 8, goalBlockRect.right);
    const width = Math.max(0, right - left);
    if (width <= 0) {
      return;
    }
    const knownObstacles = this.#readFloatingObstacles();
    const checklistRect = knownObstacles
      .map((element) => element.getBoundingClientRect())
      .filter(
        (rect) =>
          rect.bottom <= anchorRect.top &&
          anchorRect.top - rect.bottom <= 64 &&
          rect.width >= 100 &&
          rect.height >= 24,
      )
      .sort((first, second) => second.bottom - first.bottom)[0];
    this.#floatingActive = true;
    this.#layoutWriteCount += 1;
    host.style.position = "fixed";
    host.style.height = "0";
    host.style.zIndex = "30";
    host.style.pointerEvents = "none";
    if (!checklistRect && this.#floatingChecklistAligned) {
      this.#floatingViewportTop = null;
    }
    const targetTop = checklistRect?.bottom ?? this.#floatingViewportTop ?? anchorRect.top - 12;
    this.#floatingChecklistAligned = checklistRect !== undefined;
    const hostScale = this.#positionFloatingHost(host, left, targetTop, width);
    this.#floatingViewportTop = targetTop;

    const chip =
      host.shadowRoot?.querySelector<HTMLElement>(".floating-chip, .phase-error .state") ?? null;
    const panel = host.shadowRoot?.querySelector<HTMLElement>(".floating-panel") ?? null;
    if (
      host.floatingPanelConstrained &&
      this.#lastFloatingPanelHeight > 0 &&
      targetTop - 82 - this.#lastFloatingPanelHeight >= 8
    ) {
      host.floatingPanelConstrained = false;
      this.#scheduleFloatingLayout();
      return;
    }
    if (
      !chip ||
      (host.viewModel?.trackingPhase !== "error" &&
        !host.collapsed &&
        !host.floatingPanelConstrained &&
        !panel)
    ) {
      return;
    }
    const chipRect = chip?.getBoundingClientRect() ?? null;
    const panelRect = panel?.getBoundingClientRect() ?? null;
    if (panelRect && panelRect.height > 0) {
      this.#lastFloatingPanelHeight = panelRect.height;
    }
    const chipWidth = Math.min(width, chipRect?.width ?? 0);
    const panelWidth = Math.min(width, panelRect?.width ?? 0);
    const centerAvailable = knownObstacles.length === 0;
    if (host.floatingCenterAvailable !== centerAvailable) {
      host.floatingCenterAvailable = centerAvailable;
    }
    const requestedRatio = clampFloatingDockRatio(this.#requestedFloatingXRatio);
    const ratio = this.#floatingPreviewRatio ?? requestedRatio;
    if (host.floatingXRatio !== ratio) {
      host.floatingXRatio = ratio;
    }
    const obstacle = findFloatingObstacle(
      this.#document,
      host,
      anchor,
      chip,
      panel,
      left,
      right,
      knownObstacles,
    );
    const currentStackLift =
      Number.parseFloat(host.style.getPropertyValue("--gp-floating-stack-lift")) || 0;
    const chipBaseTop = chipRect ? chipRect.top + currentStackLift * hostScale : 0;
    const chipBaseBottom = chipRect ? chipRect.bottom + currentStackLift * hostScale : 0;
    const chipObstacle =
      obstacle && chipRect && obstacle.top < chipBaseBottom && obstacle.bottom > chipBaseTop
        ? obstacle
        : null;
    let chipProjection = projectFloatingCenter({
      safeLeft: left,
      safeRight: right,
      boundaryWidth: chipWidth,
      ratio,
      ...(chipObstacle
        ? { obstacleLeft: chipObstacle.left, obstacleRight: chipObstacle.right }
        : {}),
    });
    if (chipProjection.blocked) {
      chipProjection = projectFloatingCenter({
        safeLeft: left,
        safeRight: right,
        boundaryWidth: chipWidth,
        ratio,
      });
    }
    const stackLift = 0;
    const panelHalfWidth = panelWidth / 2;
    const panelMinimumCenter = left + panelHalfWidth;
    const panelMaximumCenter = Math.max(panelMinimumCenter, right - panelHalfWidth);
    const panelCenter = Math.max(
      panelMinimumCenter,
      Math.min(panelMaximumCenter, chipProjection.center),
    );
    host.style.setProperty(
      "--gp-floating-chip-center",
      `${(chipProjection.center - left) / hostScale}px`,
    );
    host.style.setProperty("--gp-floating-panel-center", `${(panelCenter - left) / hostScale}px`);
    host.style.setProperty("--gp-floating-stack-lift", `${stackLift}px`);
    const currentPanelLift =
      Number.parseFloat(host.style.getPropertyValue("--gp-floating-panel-lift")) || 0;
    const panelBaseBottom = panelRect
      ? panelRect.bottom + (currentPanelLift + currentStackLift) * hostScale
      : 0;
    const requiredTotalPanelLift =
      obstacle && panelRect ? Math.max(0, panelBaseBottom - obstacle.top + 8) / hostScale : 0;
    const requiredPanelLift = Math.max(0, requiredTotalPanelLift - stackLift);
    const panelLift = obstacle && panelRect ? Math.max(currentPanelLift, requiredPanelLift) : 0;
    const panelTopAfterLift = panelRect
      ? panelRect.top + (currentPanelLift + currentStackLift - panelLift - stackLift) * hostScale
      : null;
    const chipTopAfterLift = chipRect
      ? chipRect.top + (currentStackLift - stackLift) * hostScale
      : null;
    if (panelTopAfterLift !== null && panelTopAfterLift < 8 && !host.collapsed) {
      host.floatingPanelConstrained = true;
      host.style.setProperty("--gp-floating-panel-lift", "0px");
      this.#scheduleFloatingLayout();
      return;
    }
    if (
      chipProjection.blocked ||
      chipRect === null ||
      (chipTopAfterLift !== null && chipTopAfterLift < 8)
    ) {
      this.#fallbackToInline();
      return;
    }
    this.#floatingFallbackActive = false;
    host.removeAttribute(GOAL_PROGRESS_FLOATING_FALLBACK_ATTRIBUTE);
    this.#cancelFloatingFallbackRetry(true);
    host.style.setProperty("--gp-floating-panel-lift", `${panelLift}px`);

    this.#observeFloatingLayout(chip, panel);
    view.removeEventListener("resize", this.#onWindowResize);
    view.addEventListener("resize", this.#onWindowResize);
    view.removeEventListener("scroll", this.#onWindowScroll, true);
    view.addEventListener("scroll", this.#onWindowScroll, true);
  }

  #positionFloatingHost(
    host: HTMLElement,
    targetLeft: number,
    targetTop: number,
    targetWidth: number,
  ): number {
    host.style.left = "0px";
    host.style.top = "0px";
    host.style.width = `${targetWidth}px`;
    let rect = host.getBoundingClientRect();
    let scale = rect.width > 0 ? rect.width / targetWidth : 1;
    if (!Number.isFinite(scale) || scale <= 0) {
      scale = 1;
    }
    let cssLeft = (targetLeft - rect.left) / scale;
    let cssTop = (targetTop - rect.top) / scale;
    let cssWidth = targetWidth / scale;
    for (let attempt = 0; attempt < 2; attempt += 1) {
      host.style.left = `${cssLeft}px`;
      host.style.top = `${cssTop}px`;
      host.style.width = `${cssWidth}px`;
      rect = host.getBoundingClientRect();
      const measuredScale = rect.width > 0 ? rect.width / cssWidth : scale;
      if (Number.isFinite(measuredScale) && measuredScale > 0) {
        scale = measuredScale;
      }
      cssLeft += (targetLeft - rect.left) / scale;
      cssTop += (targetTop - rect.top) / scale;
      if (rect.width > 0) {
        cssWidth *= targetWidth / rect.width;
      }
    }
    host.style.left = `${cssLeft}px`;
    host.style.top = `${cssTop}px`;
    host.style.width = `${cssWidth}px`;
    return scale;
  }

  #fallbackToInline(): void {
    const host = this.#host;
    const view = this.#document.defaultView;
    if (!host || !view) {
      return;
    }
    this.#floatingFallbackActive = true;
    this.#lastPlacementTransition = "fallback-inline";
    host.floatingPanelConstrained = false;
    host.setAttribute(GOAL_PROGRESS_FLOATING_FALLBACK_ATTRIBUTE, "insufficient-space");
    this.#clearFloatingLayout(true);
    host.placement = "inline";
    view.removeEventListener("resize", this.#onWindowResize);
    view.addEventListener("resize", this.#onWindowResize);
    view.removeEventListener("scroll", this.#onWindowScroll, true);
    view.addEventListener("scroll", this.#onWindowScroll, true);
    this.#scheduleFloatingFallbackRetry();
  }

  #retryFloatingPlacement(): void {
    const host = this.#host;
    if (!host || this.#requestedPlacement !== "floating" || requiresInlineState(host.viewModel)) {
      return;
    }
    this.#floatingFallbackActive = false;
    this.#floatingViewportTop = null;
    host.removeAttribute(GOAL_PROGRESS_FLOATING_FALLBACK_ATTRIBUTE);
    host.floatingXRatio = this.#requestedFloatingXRatio;
    host.placement = "floating";
    this.#scheduleFloatingLayout();
  }

  #scheduleFloatingFallbackRetry(): void {
    if (
      this.#floatingFallbackRetryTimer ||
      !this.#floatingFallbackActive ||
      this.#requestedPlacement !== "floating"
    ) {
      return;
    }
    const delay = GOAL_PROGRESS_FLOATING_FALLBACK_RETRY_DELAYS_MS[this.#floatingFallbackRetryIndex];
    if (delay === undefined) {
      return;
    }
    this.#floatingFallbackRetryIndex += 1;
    this.#floatingFallbackRetryTimer = setTimeout(() => {
      this.#floatingFallbackRetryTimer = null;
      this.#retryFloatingPlacement();
      if (this.#floatingFallbackActive) {
        this.#scheduleFloatingFallbackRetry();
      }
    }, delay);
  }

  #cancelFloatingFallbackRetry(resetIndex: boolean): void {
    if (this.#floatingFallbackRetryTimer) {
      clearTimeout(this.#floatingFallbackRetryTimer);
      this.#floatingFallbackRetryTimer = null;
    }
    if (resetIndex) {
      this.#floatingFallbackRetryIndex = 0;
    }
  }

  #clearFloatingLayout(preserveFallbackRetry = false): void {
    if (!this.#floatingActive && !this.#floatingFallbackActive && !preserveFallbackRetry) {
      return;
    }
    const host = this.#host;
    const view = this.#document.defaultView;
    if (view && this.#floatingFrame !== null) {
      view.cancelAnimationFrame(this.#floatingFrame);
    }
    this.#floatingFrame = null;
    if (!preserveFallbackRetry) {
      this.#cancelFloatingFallbackRetry(true);
      this.#floatingResizeObserver?.disconnect();
      this.#floatingResizeObserver = null;
      this.#floatingObstacleObserver?.disconnect();
      this.#floatingObstacleObserver = null;
      this.#observedFloatingObstacles.clear();
      view?.removeEventListener("resize", this.#onWindowResize);
      view?.removeEventListener("scroll", this.#onWindowScroll, true);
    }
    if (host) {
      host.style.position = "";
      host.style.left = "";
      host.style.top = "";
      host.style.width = "";
      host.style.height = "";
      host.style.zIndex = "";
      host.style.pointerEvents = "";
      host.style.removeProperty("--gp-floating-chip-center");
      host.style.removeProperty("--gp-floating-panel-center");
      host.style.removeProperty("--gp-floating-stack-lift");
      host.style.removeProperty("--gp-floating-panel-lift");
    }
    this.#floatingViewportTop = null;
    this.#floatingChecklistAligned = false;
    this.#floatingActive = false;
  }

  #restoreAnchor(preserveGoalIdentity = false): void {
    const anchor = this.#anchor;
    if (anchor) {
      this.#resetAnchorTranslate(anchor);
      this.#clearInlineConstraintObserver();
    }
    this.#anchor = null;
    if (!preserveGoalIdentity) {
      this.#validatedGoalIdentity = null;
    }
  }

  #resetAnchorTranslate(anchor: HTMLElement): void {
    if (anchor.hasAttribute(GOAL_PROGRESS_ANCHOR_ORIGINAL_TRANSLATE_ATTRIBUTE)) {
      anchor.style.translate =
        anchor.getAttribute(GOAL_PROGRESS_ANCHOR_ORIGINAL_TRANSLATE_ATTRIBUTE) ?? "";
      anchor.removeAttribute(GOAL_PROGRESS_ANCHOR_ORIGINAL_TRANSLATE_ATTRIBUTE);
    }
  }

  #emitUiIntent(intent: GoalProgressLocalUiIntent): void {
    this.#onUiIntent?.(intent, {
      userActivated: this.#userClickActive,
    });
  }

  #releaseHost(remove: boolean): void {
    const host = this.#host;
    if (!host) {
      this.#restoreAnchor();
      return;
    }
    host.removeEventListener(GOAL_PROGRESS_LAYOUT_OFFSET_EVENT, this.#onLayoutOffset);
    host.removeEventListener(GOAL_PROGRESS_FLOATING_LAYOUT_EVENT, this.#onFloatingLayout);
    host.removeEventListener(GOAL_PROGRESS_SET_PLACEMENT_EVENT, this.#onPlacement);
    host.removeEventListener(GOAL_PROGRESS_SET_FLOATING_X_RATIO_EVENT, this.#onFloatingXRatio);
    if (this.#onUiIntent) {
      this.#document.removeEventListener("click", this.#onDocumentClick, true);
      host.removeEventListener(GOAL_PROGRESS_SET_COLLAPSED_EVENT, this.#onCollapsed);
      host.removeEventListener(GOAL_PROGRESS_SET_MOTION_PAUSED_EVENT, this.#onMotionPaused);
      host.removeEventListener(GOAL_PROGRESS_REQUEST_RETRY_EVENT, this.#onRetry);
      host.removeEventListener(GOAL_PROGRESS_REQUEST_DETACH_EVENT, this.#onDetach);
    }
    if (this.#onUpdateIntent) {
      this.#document.removeEventListener("click", this.#onDocumentClick, true);
      host.removeEventListener(GOAL_PROGRESS_UPDATE_INTENT_EVENT, this.#onUpdate);
    }
    host.viewModel = null;
    host.updateState = null;
    host.spaceConstrained = false;
    host.floatingPanelConstrained = false;
    host.style.marginBlockStart = "";
    this.#clearInlineInsets();
    this.#clearFallbackLayout();
    this.#clearFloatingLayout();
    this.#restoreAnchor();
    if (remove) {
      host.remove();
    }
    this.#host = null;
    this.#controlArea = null;
    this.#displayMode = "hidden";
    this.#continuityModeActive = false;
    this.#fallbackInlineOriginRetained = false;
    this.#sessionId = null;
    this.#floatingFallbackActive = false;
    this.#cancelFloatingFallbackRetry(true);
    this.#requestedPlacement = "inline";
    this.#requestedFloatingXRatio = 0.5;
    this.#floatingPreviewRatio = null;
    this.#lastFloatingPanelHeight = 0;
    if (this.#userClickTimer) {
      clearTimeout(this.#userClickTimer);
      this.#userClickTimer = null;
    }
    this.#userClickActive = false;
  }

  #result(
    action: SidecarMountAction,
    reason: SidecarMountReason,
    hostCount: number,
    threadChanged: boolean,
    adapterRejectionReason: CodexAnchorRejectionReason | null,
  ): SidecarMountResult {
    return {
      action,
      reason,
      adapterId: this.#nativeGoalLocator.id,
      adapterRejectionReason,
      hostCount,
      threadChanged,
      displayMode: this.#displayMode,
      nativeAnchorMatched: this.#displayMode === "native" && this.#anchor?.isConnected === true,
      visibleThreadStatus: this.#continuityModeActive ? "retained" : "matched",
    };
  }

  #healthResult(
    status: SidecarHealthStatus,
    reason: SidecarHealthReason,
    hostCount: number,
    adapterRejectionReason: CodexAnchorRejectionReason | null,
  ): SidecarHealthResult {
    return projectSidecarHealth({
      status,
      reason,
      adapterId: this.#nativeGoalLocator.id,
      adapterRejectionReason,
      hostCount,
      displayMode: this.#displayMode,
      anchor: this.#anchor,
      continuityModeActive: this.#continuityModeActive,
      host: this.#host,
      document: this.#document,
    });
  }
}
