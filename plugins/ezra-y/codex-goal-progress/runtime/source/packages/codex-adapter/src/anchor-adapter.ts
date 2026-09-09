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
  locate(document: Document): NativeGoalLocationResult;
  findFloatingObstacles?(document: Document): readonly HTMLElement[];
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

function findNativeStepSurfaces(document: Document): readonly HTMLElement[] {
  const surfaces = new Set<HTMLElement>();
  const markers = elements<HTMLElement>(document, "span").filter((element) => {
    const text = (element.textContent ?? "").replace(/\s+/gu, " ").trim();
    return /^第\s*\d+\s*\/\s*\d+\s*步$/u.test(text) || /^Step\s+\d+\s*\/\s*\d+$/iu.test(text);
  });
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
  const rows = Array.from(
    document.querySelectorAll<HTMLElement>("[data-app-action-sidebar-thread-row]"),
  ).filter(
    (row) =>
      row.getAttribute("aria-current") === "page" &&
      row.getAttribute("data-app-action-sidebar-thread-active") === "true" &&
      row.getAttribute("data-app-action-sidebar-thread-selected") === "true",
  );
  if (rows.length !== 1) {
    return null;
  }
  const visibleThreadId = rows[0]?.getAttribute("data-app-action-sidebar-thread-id");
  if (!visibleThreadId) {
    return null;
  }
  const visibleThreadHostId = rows[0]?.getAttribute("data-app-action-sidebar-thread-host-id");
  const hostPrefix =
    typeof visibleThreadHostId === "string" && visibleThreadHostId.length > 0
      ? `${visibleThreadHostId}:`
      : "";
  const normalizedVisibleThreadId =
    hostPrefix.length > 0 && visibleThreadId.startsWith(hostPrefix)
      ? visibleThreadId.slice(hostPrefix.length)
      : visibleThreadId;
  if (normalizedVisibleThreadId.length < 1 || normalizedVisibleThreadId.length > 256) {
    return null;
  }
  if (!normalizedVisibleThreadId.startsWith("client-new-thread:")) {
    return normalizedVisibleThreadId;
  }
  const mainContent = Array.from(
    document.querySelectorAll<HTMLElement>(
      '[data-app-shell-main-content-layout="thread-edge-scroll"]',
    ),
  );
  if (mainContent.length !== 1) {
    return null;
  }
  const conversationThreadIds = new Set(
    Array.from(
      mainContent[0]?.querySelectorAll<HTMLElement>("[data-response-annotation-conversation]") ??
        [],
    )
      .map((element) => element.getAttribute("data-response-annotation-conversation"))
      .filter(
        (threadId): threadId is string =>
          typeof threadId === "string" &&
          threadId.length > 0 &&
          threadId.length <= 256 &&
          !threadId.startsWith("client-new-thread:"),
      ),
  );
  if (conversationThreadIds.size !== 1) {
    return null;
  }
  return conversationThreadIds.values().next().value ?? null;
}

export function matchCurrentVisibleThread(
  document: Document,
  expectedThreadId: string,
): CurrentVisibleThreadMatchResult {
  const currentRows = elements<HTMLElement>(
    document,
    "[data-app-action-sidebar-thread-row]",
  ).filter(
    (row) =>
      row.getAttribute("aria-current") === "page" &&
      row.getAttribute("data-app-action-sidebar-thread-active") === "true" &&
      row.getAttribute("data-app-action-sidebar-thread-selected") === "true",
  );
  if (currentRows.length === 0) {
    return {
      status: "unknown",
      rejectionReason: "visible-thread-marker-missing",
      candidateCount: 0,
    };
  }
  if (currentRows.length !== 1) {
    return {
      status: "unknown",
      rejectionReason: "visible-thread-marker-ambiguous",
      candidateCount: currentRows.length,
    };
  }
  if (!currentRows[0]?.getAttribute("data-app-action-sidebar-thread-id")) {
    return {
      status: "unknown",
      rejectionReason: "visible-thread-id-missing",
      candidateCount: 1,
    };
  }
  const visibleThreadId = resolveCurrentMacosVisibleThreadId(document);
  if (visibleThreadId === null) {
    return {
      status: "unknown",
      rejectionReason: "visible-thread-id-missing",
      candidateCount: 1,
    };
  }
  if (visibleThreadId !== expectedThreadId) {
    return {
      status: "mismatch",
      rejectionReason: "visible-thread-mismatch",
      candidateCount: 1,
    };
  }
  return {
    status: "matched",
    rejectionReason: null,
    candidateCount: 1,
  };
}

function locateCurrentMacosGoalAnchor(adapterId: string, document: Document): AnchorLocationResult {
  const matchedSignals: CodexAnchorSignal[] = [];
  const composerRoots = elements<HTMLElement>(document, "[data-codex-composer-root]");
  if (composerRoots.length === 0) {
    return {
      located: null,
      probe: result(adapterId, false, matchedSignals, "composer-root-missing", 0),
    };
  }
  if (composerRoots.length !== 1) {
    return {
      located: null,
      probe: result(
        adapterId,
        false,
        matchedSignals,
        "composer-root-ambiguous",
        composerRoots.length,
      ),
    };
  }
  matchedSignals.push("composer-root-unique");
  const composerRoot = composerRoots[0] as HTMLElement;
  const textboxes = elements<HTMLElement>(composerRoot, '[role="textbox"][data-codex-composer]');
  if (textboxes.length === 0) {
    return {
      located: null,
      probe: result(adapterId, false, matchedSignals, "composer-textbox-missing", 0),
    };
  }
  if (textboxes.length !== 1) {
    return {
      located: null,
      probe: result(
        adapterId,
        false,
        matchedSignals,
        "composer-textbox-ambiguous",
        textboxes.length,
      ),
    };
  }
  matchedSignals.push("composer-textbox-unique");
  const composerRect = composerRoot.getBoundingClientRect();
  const textboxRect = (textboxes[0] as HTMLElement).getBoundingClientRect();
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
  locate(document) {
    const located = locateCurrentMacosGoalAnchor(this.id, document);
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
  findFloatingObstacles(document) {
    return findNativeStepSurfaces(document);
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
