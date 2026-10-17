export type CodexAnchorPlatform = "macos";
export type CodexHostPlatform = CodexAnchorPlatform | "windows";

export type CodexAnchorSignal =
  | "composer-root-unique"
  | "composer-textbox-unique"
  | "goal-button-above-composer"
  | "goal-control-area-present"
  | "goal-text-english"
  | "goal-text-chinese";

export type CodexAnchorRejectionReason =
  | "composer-root-missing"
  | "composer-root-ambiguous"
  | "composer-textbox-missing"
  | "composer-textbox-ambiguous"
  | "goal-anchor-missing"
  | "goal-anchor-ambiguous";

export type CodexVisibleThreadRejectionReason =
  | "visible-thread-marker-missing"
  | "visible-thread-marker-ambiguous"
  | "visible-thread-id-missing"
  | "visible-thread-mismatch";

export interface CapabilityProbeResult {
  readonly supported: boolean;
  readonly adapterId: string;
  readonly matchedSignals: readonly CodexAnchorSignal[];
  readonly rejectionReason: CodexAnchorRejectionReason | null;
  readonly candidateCount: number;
}

export type CodexVisibleThreadStatus = "matched" | "unknown" | "mismatch";

export interface CurrentVisibleThreadMatchResult {
  readonly status: CodexVisibleThreadStatus;
  readonly rejectionReason: CodexVisibleThreadRejectionReason | null;
  readonly candidateCount: number;
}

export interface NativeGoalTarget {
  readonly anchor: HTMLElement;
  readonly controlArea: HTMLElement | null;
  readonly goalIdentity: string | null;
  readonly goalTitleFontWeight?: number | null;
}

export interface NativeGoalLocationResult {
  readonly target: NativeGoalTarget | null;
  readonly rejectionReason: CodexAnchorRejectionReason | null;
  readonly candidateCount: number;
  readonly matchedSignals: readonly CodexAnchorSignal[];
}

export interface CodexNativeGoalLocator {
  readonly id: string;
  readonly platform: CodexAnchorPlatform;
  readonly verifiedVersions: ReadonlySet<string>;
  locate(document: Document, page?: CurrentCodexPage): NativeGoalLocationResult;
  findFloatingObstacles?(document: Document, page?: CurrentCodexPage): readonly HTMLElement[];
}

export interface CurrentCodexPage {
  readonly surface: ParentNode | null;
  readonly composer: HTMLElement | null;
  readonly textbox: HTMLElement | null;
  readonly composerCount: number;
  readonly textboxCount: number;
  readonly rejectionReason: CodexAnchorRejectionReason | null;
  readonly threadId: string | null;
  readonly hostId: string | null;
  readonly threadCandidateCount: number;
  readonly threadRejectionReason: Exclude<
    CodexVisibleThreadRejectionReason,
    "visible-thread-mismatch"
  > | null;
}

// 此函数完整携带依赖，CDP 可以直接序列化后在页面执行。
export function readCurrentCodexPage(document: Document): CurrentCodexPage {
  const visibility = {
    exposed(element: HTMLElement): boolean {
      for (let current: HTMLElement | null = element; current; current = current.parentElement) {
        const style = document.defaultView?.getComputedStyle(current);
        if (
          current.hasAttribute("hidden") ||
          current.hasAttribute("inert") ||
          current.getAttribute("aria-hidden") === "true" ||
          style?.display === "none" ||
          style?.visibility === "hidden" ||
          style?.visibility === "collapse"
        )
          return false;
      }
      return true;
    },
  };
  const surfaces = Array.from(
    document.querySelectorAll<HTMLElement>("[data-app-shell-page-surface]"),
  );
  const exposed = surfaces.filter(visibility.exposed);
  const active = exposed.filter(
    (surface) => !exposed.some((other) => other !== surface && surface.contains(other)),
  );
  const surface = active.length === 0 ? document : active.length === 1 ? (active[0] ?? null) : null;
  const composers = Array.from(
    (surface ?? document).querySelectorAll<HTMLElement>("[data-codex-composer-root]"),
  ).filter(visibility.exposed);
  const composer = surface && composers.length === 1 ? (composers[0] ?? null) : null;
  const textboxes = Array.from(
    composer?.querySelectorAll<HTMLElement>('[role="textbox"][data-codex-composer]') ?? [],
  ).filter(visibility.exposed);
  const textbox = textboxes.length === 1 ? (textboxes[0] ?? null) : null;
  const rejectionReason =
    active.length > 1 || composers.length > 1
      ? "composer-root-ambiguous"
      : !composer
        ? "composer-root-missing"
        : textboxes.length > 1
          ? "composer-textbox-ambiguous"
          : !textbox
            ? "composer-textbox-missing"
            : null;
  // 侧栏折叠和离屏仍保留身份；仅排除属于隐藏缓存页面的任务行。
  const rows = Array.from(
    document.querySelectorAll<HTMLElement>("[data-app-action-sidebar-thread-row]"),
  ).filter((row) => {
    for (let current: HTMLElement | null = row; current; current = current.parentElement) {
      if (current.hasAttribute("data-app-shell-page-surface") && !visibility.exposed(current))
        return false;
    }
    return (
      row.getAttribute("aria-current") === "page" &&
      row.getAttribute("data-app-action-sidebar-thread-active") === "true" &&
      row.getAttribute("data-app-action-sidebar-thread-selected") === "true"
    );
  });
  const identities = new Map<string, { threadId: string; hostId: string }>();
  let invalidId = false;
  for (const row of rows) {
    const raw = row.getAttribute("data-app-action-sidebar-thread-id");
    const hostId = row.getAttribute("data-app-action-sidebar-thread-host-id") ?? "";
    const threadId = hostId && raw?.startsWith(`${hostId}:`) ? raw.slice(hostId.length + 1) : raw;
    if (!threadId || threadId.length > 256) {
      invalidId = true;
      continue;
    }
    identities.set(JSON.stringify([hostId, threadId]), { hostId, threadId });
  }
  let identity = identities.size === 1 ? identities.values().next().value : undefined;
  let threadRejectionReason: CurrentCodexPage["threadRejectionReason"] =
    identities.size > 1
      ? "visible-thread-marker-ambiguous"
      : invalidId
        ? "visible-thread-id-missing"
        : rows.length === 0
          ? "visible-thread-marker-missing"
          : null;
  if (identity?.threadId.startsWith("client-new-thread:") || rows.length === 0) {
    const main = Array.from(
      surface?.querySelectorAll<HTMLElement>(
        '[data-app-shell-main-content-layout="thread-edge-scroll"]',
      ) ?? [],
    ).filter(visibility.exposed);
    const ids = new Set(
      Array.from(
        main.length === 1
          ? (main[0]?.querySelectorAll<HTMLElement>("[data-response-annotation-conversation]") ??
              [])
          : [],
      )
        .filter(visibility.exposed)
        .map((element) => element.getAttribute("data-response-annotation-conversation"))
        .filter(
          (id): id is string => !!id && id.length <= 256 && !id.startsWith("client-new-thread:"),
        ),
    );
    const threadId = ids.size === 1 ? ids.values().next().value : undefined;
    identity = threadId ? { hostId: identity?.hostId ?? "", threadId } : undefined;
    if (identity) threadRejectionReason = null;
    else if (rows.length > 0) threadRejectionReason = "visible-thread-id-missing";
  }
  return {
    surface,
    composer,
    textbox,
    composerCount: composers.length,
    textboxCount: textboxes.length,
    rejectionReason,
    threadId: threadRejectionReason === null ? (identity?.threadId ?? null) : null,
    hostId: threadRejectionReason === null ? (identity?.hostId ?? null) : null,
    threadCandidateCount: identities.size || (identity ? 1 : rows.length),
    threadRejectionReason,
  };
}

interface LocatedGoalAnchor {
  readonly anchor: HTMLElement;
  readonly controlArea: HTMLElement;
  readonly goalButton: HTMLElement;
}

interface AnchorLocationResult {
  readonly located: LocatedGoalAnchor | null;
  readonly probe: CapabilityProbeResult;
}

function elements<T extends Element>(root: ParentNode, selector: string): T[] {
  return Array.from(root.querySelectorAll<T>(selector));
}

function rectVisible(rect: DOMRect): boolean {
  return (
    Number.isFinite(rect.top) &&
    Number.isFinite(rect.right) &&
    Number.isFinite(rect.bottom) &&
    Number.isFinite(rect.left) &&
    rect.width > 0 &&
    rect.height > 0
  );
}

function verticallyOverlaps(left: DOMRect, right: DOMRect): boolean {
  return Math.min(left.bottom, right.bottom) > Math.max(left.top, right.top);
}

function textSignals(element: HTMLElement): CodexAnchorSignal[] {
  const text = (element.textContent ?? "").replace(/\s+/gu, " ").trim();
  const signals: CodexAnchorSignal[] = [];
  if (/(^|\s)goal(?=\s|:|$)/iu.test(text)) {
    signals.push("goal-text-english");
  }
  if (text.includes("目标")) {
    signals.push("goal-text-chinese");
  }
  return signals;
}

function readGoalButtonIdentity(goalButton: HTMLElement): string | null {
  const content = goalButton.children[1];
  if (!content) {
    return null;
  }
  const objective = content.children.length >= 3 ? content.children[1] : content;
  if (!objective) {
    return null;
  }
  const normalized = (objective.textContent ?? "")
    .replace(/\s+/gu, " ")
    .replace(/\s*•\s*$/u, "")
    .trim();
  return normalized || null;
}

function readGoalTitleFontWeight(document: Document, goalButton: HTMLElement): number | null {
  const title = goalButton.children[0];
  const view = document.defaultView;
  if (!view || !(title instanceof view.HTMLElement)) {
    return null;
  }
  const fontWeight = Number.parseFloat(view.getComputedStyle(title).fontWeight);
  return Number.isFinite(fontWeight) && fontWeight >= 1 && fontWeight <= 1_000 ? fontWeight : null;
}

function findNativeStepSurfaces(
  document: Document,
  page: CurrentCodexPage,
): readonly HTMLElement[] {
  const surfaces = new Set<HTMLElement>();
  const markers = (page.surface ? elements<HTMLElement>(page.surface, "span") : []).filter(
    (element) => {
      const text = (element.textContent ?? "").replace(/\s+/gu, " ").trim();
      return /^第\s*\d+\s*\/\s*\d+\s*步$/u.test(text) || /^Step\s+\d+\s*\/\s*\d+$/iu.test(text);
    },
  );
  for (const marker of markers) {
    let ancestor = marker.parentElement;
    for (let depth = 0; ancestor && depth < 6; depth += 1, ancestor = ancestor.parentElement) {
      const rect = ancestor.getBoundingClientRect();
      const radius =
        Number.parseFloat(document.defaultView?.getComputedStyle(ancestor).borderRadius ?? "0") ||
        0;
      if (rect.width >= 300 && rect.height >= 24 && rect.height <= 420 && radius >= 8) {
        surfaces.add(ancestor);
        break;
      }
    }
  }
  return [...surfaces];
}

function auxiliaryControlButtons(container: HTMLElement, goalButton: HTMLElement): HTMLElement[] {
  const goalRect = goalButton.getBoundingClientRect();
  return elements<HTMLElement>(container, 'button[type="button"][aria-label]').filter((button) => {
    if (button === goalButton) {
      return false;
    }
    const rect = button.getBoundingClientRect();
    return (
      rectVisible(rect) &&
      verticallyOverlaps(rect, goalRect) &&
      rect.width <= goalRect.width * 0.25 &&
      rect.height <= Math.max(goalRect.height * 2, 72)
    );
  });
}

function findGoalRow(
  composerRoot: HTMLElement,
  goalButton: HTMLElement,
): { readonly anchor: HTMLElement; readonly controlArea: HTMLElement } | null {
  let ancestor = goalButton.parentElement;
  while (ancestor && ancestor !== composerRoot) {
    const directChildren = Array.from(ancestor.children).filter(
      (child): child is HTMLElement => "getBoundingClientRect" in child,
    );
    const goalBranch = directChildren.filter(
      (child) => child === goalButton || child.contains(goalButton),
    );
    const controlBranches = directChildren.filter(
      (child) =>
        !goalBranch.includes(child) && auxiliaryControlButtons(child, goalButton).length >= 2,
    );
    if (goalBranch.length === 1 && controlBranches.length === 1) {
      let mountAnchor = ancestor;
      while (mountAnchor.parentElement && mountAnchor.parentElement !== composerRoot) {
        mountAnchor = mountAnchor.parentElement;
      }
      if (mountAnchor.parentElement !== composerRoot) {
        return null;
      }
      return {
        anchor: mountAnchor,
        controlArea: controlBranches[0] as HTMLElement,
      };
    }
    ancestor = ancestor.parentElement;
  }
  return null;
}

function result(
  adapterId: string,
  supported: boolean,
  matchedSignals: readonly CodexAnchorSignal[],
  rejectionReason: CodexAnchorRejectionReason | null,
  candidateCount: number,
): CapabilityProbeResult {
  return {
    supported,
    adapterId,
    matchedSignals,
    rejectionReason,
    candidateCount,
  };
}

export function resolveCurrentMacosVisibleThreadId(document: Document): string | null {
  return readCurrentCodexPage(document).threadId;
}

export function matchCurrentVisibleThread(
  document: Document,
  expectedThreadId: string,
  page: CurrentCodexPage = readCurrentCodexPage(document),
): CurrentVisibleThreadMatchResult {
  return {
    status:
      page.threadId === null
        ? "unknown"
        : page.threadId === expectedThreadId
          ? "matched"
          : "mismatch",
    rejectionReason:
      page.threadRejectionReason ??
      (page.threadId === expectedThreadId ? null : "visible-thread-mismatch"),
    candidateCount: page.threadCandidateCount,
  };
}

function locateCurrentMacosGoalAnchor(
  adapterId: string,
  page: CurrentCodexPage,
): AnchorLocationResult {
  const matchedSignals: CodexAnchorSignal[] = [];
  if (page.composer) matchedSignals.push("composer-root-unique");
  if (page.textbox) matchedSignals.push("composer-textbox-unique");
  if (page.rejectionReason || !page.composer || !page.textbox) {
    return {
      located: null,
      probe: result(
        adapterId,
        false,
        matchedSignals,
        page.rejectionReason,
        page.rejectionReason?.startsWith("composer-root") ? page.composerCount : page.textboxCount,
      ),
    };
  }
  const composerRoot = page.composer;
  const composerRect = composerRoot.getBoundingClientRect();
  const textboxRect = page.textbox.getBoundingClientRect();
  const managedHosts = elements<HTMLElement>(composerRoot, '[data-codex-goal-progress-host="v1"]');
  const managedAnchor = managedHosts.length === 1 ? managedHosts[0]?.previousElementSibling : null;
  const candidates = elements<HTMLElement>(composerRoot, 'button[type="button"]').flatMap(
    (button) => {
      const buttonRect = button.getBoundingClientRect();
      const label = button.getAttribute("aria-label");
      const hasDisclosure = elements<HTMLElement>(button, '[aria-hidden="true"]').length > 0;
      const structurallyPossible =
        rectVisible(composerRect) &&
        rectVisible(textboxRect) &&
        rectVisible(buttonRect) &&
        button.children.length >= 2 &&
        hasDisclosure &&
        buttonRect.width >= Math.min(composerRect.width * 0.5, 240) &&
        (buttonRect.top >= composerRect.top ||
          (managedAnchor instanceof HTMLElement && managedAnchor.contains(button))) &&
        buttonRect.bottom <= textboxRect.top &&
        (label === null || /goal|目标/iu.test(label));
      if (!structurallyPossible) {
        return [];
      }
      const row = findGoalRow(composerRoot, button);
      if (!row) {
        return [];
      }
      return [
        {
          ...row,
          goalButton: button,
        },
      ];
    },
  );

  if (candidates.length === 0) {
    return {
      located: null,
      probe: result(adapterId, false, matchedSignals, "goal-anchor-missing", 0),
    };
  }
  if (candidates.length !== 1) {
    return {
      located: null,
      probe: result(adapterId, false, matchedSignals, "goal-anchor-ambiguous", candidates.length),
    };
  }
  matchedSignals.push("goal-button-above-composer", "goal-control-area-present");
  const located = candidates[0] as LocatedGoalAnchor;
  matchedSignals.push(...textSignals(located.goalButton));
  return {
    located,
    probe: result(adapterId, true, matchedSignals, null, 1),
  };
}

const MACOS_GOAL_ROW_V1_VERIFIED_VERSIONS = new Set([
  "26.818.21641",
  "26.818.31338",
  "26.818.41509",
  "26.818.61809",
  "26.820.60940",
]);

export const macosGoalRowV1Locator: CodexNativeGoalLocator = {
  id: "macos-goal-row-v1",
  platform: "macos",
  verifiedVersions: MACOS_GOAL_ROW_V1_VERIFIED_VERSIONS,
  locate(document, page = readCurrentCodexPage(document)) {
    const located = locateCurrentMacosGoalAnchor(this.id, page);
    return {
      target: located.located
        ? {
            anchor: located.located.anchor,
            controlArea: located.located.controlArea,
            goalIdentity: readGoalButtonIdentity(located.located.goalButton),
            goalTitleFontWeight: readGoalTitleFontWeight(document, located.located.goalButton),
          }
        : null,
      rejectionReason: located.probe.rejectionReason,
      candidateCount: located.probe.candidateCount,
      matchedSignals: located.probe.matchedSignals,
    };
  },
  findFloatingObstacles(document, page = readCurrentCodexPage(document)) {
    return findNativeStepSurfaces(document, page);
  },
};

export class CodexNativeGoalLocatorRegistry {
  readonly #locators: readonly CodexNativeGoalLocator[];

  constructor(locators: readonly CodexNativeGoalLocator[]) {
    const ids = new Set<string>();
    const platforms = new Set<CodexAnchorPlatform>();
    for (const locator of locators) {
      if (ids.has(locator.id)) {
        throw new Error(`GOAL_PROGRESS_NATIVE_GOAL_LOCATOR_ID_DUPLICATE: ${locator.id}`);
      }
      if (platforms.has(locator.platform)) {
        throw new Error(
          `GOAL_PROGRESS_NATIVE_GOAL_LOCATOR_PLATFORM_DUPLICATE: ${locator.platform}`,
        );
      }
      ids.add(locator.id);
      platforms.add(locator.platform);
    }
    this.#locators = [...locators];
  }

  resolvePlatform(platform: CodexHostPlatform): CodexNativeGoalLocator | null {
    return this.#locators.find((locator) => locator.platform === platform) ?? null;
  }
}

export function createDefaultCodexNativeGoalLocatorRegistry(): CodexNativeGoalLocatorRegistry {
  return new CodexNativeGoalLocatorRegistry([macosGoalRowV1Locator]);
}
