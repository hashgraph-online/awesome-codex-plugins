import type { GoalProgressViewModel } from "../../contracts/src/goal-contract.js";
import type {
  CodexAnchorRejectionReason,
  CodexVisibleThreadRejectionReason,
} from "./anchor-adapter.js";

export type GoalProgressDisplayMode = "native" | "fallback" | "hidden";

export type SidecarHealthStatus = "mounted" | "unmounted" | "blocked";

export type SidecarHealthReason =
  | "ok"
  | "anchor-unavailable"
  | "native-goal-changed"
  | "host-missing"
  | "host-misplaced"
  | "host-ambiguous"
  | "host-unmanaged"
  | CodexVisibleThreadRejectionReason;

export interface SidecarHealthResult {
  readonly status: SidecarHealthStatus;
  readonly reason: SidecarHealthReason;
  readonly adapterId: string;
  readonly adapterRejectionReason: CodexAnchorRejectionReason | null;
  readonly hostCount: number;
  readonly displayMode: GoalProgressDisplayMode;
  readonly nativeAnchorMatched: boolean;
  readonly visibleThreadStatus: "matched" | "retained";
  readonly componentVisible: boolean;
  readonly viewModelRevision: number | null;
}

export interface SidecarLayoutDiagnostics {
  readonly lastAnchorState: "none" | "live" | "unavailable";
  readonly lastConstraintTransition: "none" | "entered" | "exited";
  readonly lastCollapsedTransition:
    | "none"
    | "preference-collapsed"
    | "preference-expanded"
    | "user-collapsed"
    | "user-expanded";
  readonly lastPlacementTransition:
    | "none"
    | "preference-inline"
    | "preference-floating"
    | "user-inline"
    | "user-floating"
    | "fallback-inline";
  readonly layoutReadCount: number;
  readonly layoutWriteCount: number;
  readonly nativeGeometryFingerprint: string | null;
  readonly sidecarGeometryFingerprint: string | null;
  readonly continuityModeActive: boolean;
  readonly requestedPlacement: "inline" | "floating";
  readonly effectivePlacement: "none" | "inline" | "floating";
  readonly floatingFallbackReason: "insufficient-space" | null;
  readonly lastHostRemovalReason: string | null;
  readonly visibility: SidecarVisibilityDiagnostics;
}

export interface SidecarVisibilityDiagnostics {
  readonly composerRectFingerprint: string | null;
  readonly textboxRectFingerprint: string | null;
  readonly hostRectFingerprint: string | null;
  readonly textboxClientHeight: number | null;
  readonly textboxScrollHeight: number | null;
  readonly textboxScrollTop: number | null;
  readonly textboxOverflowY: string | null;
  readonly composerClassTokenCount: number;
  readonly composerInlineStylePropertyCount: number;
  readonly clippingAncestorFingerprint: string | null;
  readonly clippingOverflow: string | null;
  readonly hostViewportIntersectionRatio: number;
  readonly hostClippedIntersectionRatio: number;
  readonly anchorConnected: boolean;
  readonly composerCount: number;
  readonly textboxCount: number;
  readonly surface: "none" | "expanded" | "compact";
  readonly lastObserverReason:
    | "none"
    | "inline-resize"
    | "floating-resize"
    | "textbox-input"
    | "textbox-scroll";
}

export interface SidecarDiagnosticHost extends HTMLElement {
  readonly viewModel: GoalProgressViewModel | null;
  readonly collapsed: boolean;
  readonly placement: "inline" | "floating";
  readonly spaceConstrained: boolean;
}

export function rectFingerprint(rect: DOMRect | null): string {
  if (!rect) {
    return "none";
  }
  const bounded = [rect.left, rect.top, rect.right, rect.bottom, rect.width, rect.height].map(
    (value) => (Number.isFinite(value) ? Math.round(value * 10) / 10 : null),
  );
  return bounded.join(",");
}

function intersectionRatio(rect: DOMRect | null, bounds: readonly DOMRect[]): number {
  if (!rect || rect.width <= 0 || rect.height <= 0) {
    return 0;
  }
  let left = rect.left;
  let top = rect.top;
  let right = rect.right;
  let bottom = rect.bottom;
  for (const bound of bounds) {
    left = Math.max(left, bound.left);
    top = Math.max(top, bound.top);
    right = Math.min(right, bound.right);
    bottom = Math.min(bottom, bound.bottom);
  }
  const visibleArea = Math.max(0, right - left) * Math.max(0, bottom - top);
  return Math.round((visibleArea / (rect.width * rect.height)) * 10_000) / 10_000;
}

function clippingAncestors(element: HTMLElement, view: Window): HTMLElement[] {
  const ancestors: HTMLElement[] = [];
  for (let current = element.parentElement; current; current = current.parentElement) {
    const style = view.getComputedStyle(current);
    if (/(auto|clip|hidden|scroll)/u.test(`${style.overflowX} ${style.overflowY}`)) {
      ancestors.push(current);
    }
  }
  return ancestors;
}

function componentIsVisible(host: SidecarDiagnosticHost | null, document: Document): boolean {
  const view = document.defaultView;
  if (!host?.isConnected || host.hidden) {
    return false;
  }
  if (!view) {
    return true;
  }
  const surface =
    host.placement === "floating"
      ? host.shadowRoot?.querySelector<HTMLElement>(".floating-panel,.floating-chip")
      : host;
  if (!surface) {
    return false;
  }
  const bounds = [
    new DOMRect(0, 0, Math.max(0, view.innerWidth), Math.max(0, view.innerHeight)),
    ...clippingAncestors(host, view).map((element) => element.getBoundingClientRect()),
  ];
  return intersectionRatio(surface.getBoundingClientRect(), bounds) >= 0.99;
}

export interface SidecarHealthProjectionInput {
  readonly status: SidecarHealthStatus;
  readonly reason: SidecarHealthReason;
  readonly adapterId: string;
  readonly adapterRejectionReason: CodexAnchorRejectionReason | null;
  readonly hostCount: number;
  readonly displayMode: GoalProgressDisplayMode;
  readonly anchor: HTMLElement | null;
  readonly continuityModeActive: boolean;
  readonly host: SidecarDiagnosticHost | null;
  readonly document: Document;
}

export function projectSidecarHealth(input: SidecarHealthProjectionInput): SidecarHealthResult {
  return {
    status: input.status,
    reason: input.reason,
    adapterId: input.adapterId,
    adapterRejectionReason: input.adapterRejectionReason,
    hostCount: input.hostCount,
    displayMode: input.displayMode,
    nativeAnchorMatched: input.displayMode === "native" && input.anchor?.isConnected === true,
    visibleThreadStatus: input.continuityModeActive ? "retained" : "matched",
    componentVisible: input.status === "mounted" && componentIsVisible(input.host, input.document),
    viewModelRevision:
      input.host?.viewModel && Number.isSafeInteger(input.host.viewModel.revision)
        ? input.host.viewModel.revision
        : null,
  };
}

export interface SidecarDiagnosticsProjectionInput {
  readonly host: SidecarDiagnosticHost | null;
  readonly anchor: HTMLElement | null;
  readonly document: Document;
  readonly lastAnchorState: SidecarLayoutDiagnostics["lastAnchorState"];
  readonly lastConstraintTransition: SidecarLayoutDiagnostics["lastConstraintTransition"];
  readonly lastCollapsedTransition: SidecarLayoutDiagnostics["lastCollapsedTransition"];
  readonly lastPlacementTransition: SidecarLayoutDiagnostics["lastPlacementTransition"];
  readonly layoutReadCount: number;
  readonly layoutWriteCount: number;
  readonly nativeGeometryFingerprint: string | null;
  readonly sidecarGeometryFingerprint: string | null;
  readonly continuityModeActive: boolean;
  readonly requestedPlacement: "inline" | "floating";
  readonly floatingFallbackActive: boolean;
  readonly lastHostRemovalReason: string | null;
  readonly lastObserverReason: SidecarVisibilityDiagnostics["lastObserverReason"];
}

export function projectSidecarDiagnostics(
  input: SidecarDiagnosticsProjectionInput,
): SidecarLayoutDiagnostics {
  const { host, anchor, document } = input;
  const view = document.defaultView;
  const composer = anchor?.closest<HTMLElement>("[data-codex-composer-root]") ?? null;
  const textbox =
    composer?.querySelector<HTMLElement>('[role="textbox"][data-codex-composer]') ?? null;
  const hostRect = host?.getBoundingClientRect() ?? null;
  const clipping = host && view ? clippingAncestors(host, view) : [];
  const viewport =
    view === null
      ? []
      : [new DOMRect(0, 0, Math.max(0, view.innerWidth), Math.max(0, view.innerHeight))];
  const nearestClipping = clipping[0] ?? null;
  const nearestClippingStyle =
    nearestClipping && view ? view.getComputedStyle(nearestClipping) : null;
  return {
    lastAnchorState: input.lastAnchorState,
    lastConstraintTransition: input.lastConstraintTransition,
    lastCollapsedTransition: input.lastCollapsedTransition,
    lastPlacementTransition: input.lastPlacementTransition,
    layoutReadCount: input.layoutReadCount,
    layoutWriteCount: input.layoutWriteCount,
    nativeGeometryFingerprint: input.nativeGeometryFingerprint,
    sidecarGeometryFingerprint: input.sidecarGeometryFingerprint,
    continuityModeActive: input.continuityModeActive,
    requestedPlacement: input.requestedPlacement,
    effectivePlacement: host?.placement ?? "none",
    floatingFallbackReason: input.floatingFallbackActive ? "insufficient-space" : null,
    lastHostRemovalReason: input.lastHostRemovalReason,
    visibility: {
      composerRectFingerprint: composer ? rectFingerprint(composer.getBoundingClientRect()) : null,
      textboxRectFingerprint: textbox ? rectFingerprint(textbox.getBoundingClientRect()) : null,
      hostRectFingerprint: hostRect ? rectFingerprint(hostRect) : null,
      textboxClientHeight: textbox?.clientHeight ?? null,
      textboxScrollHeight: textbox?.scrollHeight ?? null,
      textboxScrollTop: textbox?.scrollTop ?? null,
      textboxOverflowY: textbox && view ? view.getComputedStyle(textbox).overflowY : null,
      composerClassTokenCount: composer?.classList.length ?? 0,
      composerInlineStylePropertyCount: composer?.style.length ?? 0,
      clippingAncestorFingerprint: nearestClipping
        ? rectFingerprint(nearestClipping.getBoundingClientRect())
        : null,
      clippingOverflow: nearestClippingStyle
        ? `${nearestClippingStyle.overflowX}/${nearestClippingStyle.overflowY}`
        : null,
      hostViewportIntersectionRatio: intersectionRatio(hostRect, viewport),
      hostClippedIntersectionRatio: intersectionRatio(hostRect, [
        ...viewport,
        ...clipping.map((element) => element.getBoundingClientRect()),
      ]),
      anchorConnected: anchor?.isConnected === true,
      composerCount: document.querySelectorAll("[data-codex-composer-root]").length,
      textboxCount: document.querySelectorAll('[role="textbox"][data-codex-composer]').length,
      surface:
        host === null ? "none" : host.collapsed || host.spaceConstrained ? "compact" : "expanded",
      lastObserverReason: input.lastObserverReason,
    },
  };
}
