import { html, LitElement, nothing, type PropertyValues } from "lit";
import type {
  GoalProgressPlacement,
  GoalProgressUpdateIntent,
  GoalProgressUpdateState,
  GoalProgressViewModel,
} from "../../contracts/src/index.js";
import {
  GOAL_PROGRESS_FLOATING_LAYOUT_EVENT,
  GOAL_PROGRESS_LAYOUT_OFFSET_EVENT,
  GOAL_PROGRESS_REQUEST_DETACH_EVENT,
  GOAL_PROGRESS_REQUEST_RETRY_EVENT,
  GOAL_PROGRESS_SET_COLLAPSED_EVENT,
  GOAL_PROGRESS_SET_FLOATING_X_RATIO_EVENT,
} from "../../contracts/src/renderer-events.js";
import {
  GOAL_PROGRESS_UPDATE_INTENT_EVENT,
  isGoalProgressUpdateVersion,
} from "../../contracts/src/update-state-runtime.js";
import { renderErrorView, renderPreparingView } from "./components/states.js";
import { renderTrackingView } from "./components/tracking.js";
import { DisplaySettingsMenuController } from "./display-settings-menu-controller.js";
import { resolveGoalProgressLocale } from "./locale.js";
import { ObjectiveScrollController } from "./objective-scroll-controller.js";
import { codexThemeTokenStyles } from "./styles/codex-theme-tokens.js";
import { colorTokenStyles } from "./styles/color-tokens.js";
import { layoutAndTypographyStyles } from "./styles/layout-and-typography.js";
import { motionStyles } from "./styles/motion.js";
import { objectiveStyles } from "./styles/objectives.js";
import { placementStyles } from "./styles/placement.js";
import { progressStyles } from "./styles/progress.js";
import { stateStyles } from "./styles/states.js";
import { updateStyles } from "./styles/updates.js";

type RendererTheme = "auto" | "dark" | "light";

function objectiveScrollIdentity(
  viewModel: GoalProgressViewModel | null | undefined,
): string | null {
  return viewModel ? `${viewModel.sessionId}:${viewModel.contractId}` : null;
}

function activeObjectiveId(viewModel: GoalProgressViewModel | null | undefined): string | null {
  return viewModel?.objectives.find((objective) => objective.status === "active")?.id ?? null;
}

export class GoalProgressElement extends LitElement {
  static override properties = {
    viewModel: { attribute: false },
    updateState: { attribute: false },
    collapsed: { type: Boolean, reflect: true },
    motionPaused: { type: Boolean, attribute: "motion-paused", reflect: true },
    placement: { type: String, reflect: true },
    requestedPlacement: { type: String, attribute: "requested-placement", reflect: true },
    spaceConstrained: { type: Boolean, attribute: "space-constrained", reflect: true },
    floatingXRatio: { type: Number, attribute: false },
    floatingCenterAvailable: {
      type: Boolean,
      attribute: "floating-center-available",
      reflect: true,
    },
    floatingPanelConstrained: {
      type: Boolean,
      attribute: "floating-panel-constrained",
      reflect: true,
    },
    theme: { type: String, reflect: true },
    locale: { type: String, attribute: "lang", reflect: true },
    _scrolling: { state: true },
    _scrollable: { state: true },
    _scrollThumbSize: { state: true },
    _scrollThumbOffset: { state: true },
    _settingsOpen: { state: true },
    _updateSeenVersion: { state: true },
  };

  static override styles = [
    colorTokenStyles,
    codexThemeTokenStyles,
    layoutAndTypographyStyles,
    objectiveStyles,
    placementStyles,
    progressStyles,
    stateStyles,
    motionStyles,
    updateStyles,
  ];

  declare viewModel: GoalProgressViewModel | null;
  declare updateState: GoalProgressUpdateState | null;
  declare collapsed: boolean;
  declare motionPaused: boolean;
  declare placement: GoalProgressPlacement;
  declare requestedPlacement: GoalProgressPlacement;
  declare spaceConstrained: boolean;
  declare floatingXRatio: number;
  declare floatingCenterAvailable: boolean;
  declare floatingPanelConstrained: boolean;
  declare theme: RendererTheme;
  declare locale: string;
  protected declare _scrolling: boolean;
  protected declare _scrollable: boolean;
  protected declare _scrollThumbSize: number;
  protected declare _scrollThumbOffset: number;
  declare _settingsOpen: boolean;
  protected declare _updateSeenVersion: string | null;
  #lastLayoutOffset = -1;
  #floatingPointerId: number | null = null;
  #floatingPointerMoved = false;
  #floatingPointerStartRatio = 0.5;
  #floatingPointerTargetRatio = 0.5;
  #floatingPointerStartX = 0;

  get expandedLayoutOffset(): number {
    return Math.max(0, this.#lastLayoutOffset);
  }

  readonly #scrollController = new ObjectiveScrollController((state) => {
    this._scrolling = state.scrolling;
    this._scrollable = state.scrollable;
    this._scrollThumbSize = state.thumbSize;
    this._scrollThumbOffset = state.thumbOffset;
  });
  readonly #displaySettingsMenu = new DisplaySettingsMenuController(this);

  constructor() {
    super();
    this.viewModel = null;
    this.updateState = null;
    this.collapsed = false;
    this.motionPaused = false;
    this.placement = "inline";
    this.requestedPlacement = "inline";
    this.spaceConstrained = false;
    this.floatingXRatio = 0.5;
    this.floatingCenterAvailable = true;
    this.floatingPanelConstrained = false;
    this.theme = "auto";
    this.locale = "en";
    this._scrolling = false;
    this._scrollable = false;
    this._scrollThumbSize = 0;
    this._scrollThumbOffset = 0;
    this._settingsOpen = false;
    this._updateSeenVersion = null;
  }

  override connectedCallback(): void {
    if (!this.hasAttribute("lang")) {
      this.locale = this.ownerDocument.documentElement.lang || "en";
    }
    if (!this.hasAttribute("dir")) {
      this.dir = this.ownerDocument.documentElement.dir === "rtl" ? "rtl" : "ltr";
    }
    super.connectedCallback();
    this.ownerDocument.addEventListener("pointerdown", this.#onDocumentPointerDown, true);
    this.ownerDocument.addEventListener("keydown", this.#onDocumentKeyDown, true);
    void this.updateComplete.then(() => {
      if (this.isConnected) {
        this.#scrollController.bind(this.renderRoot, objectiveScrollIdentity(this.viewModel));
      }
    });
  }

  override disconnectedCallback(): void {
    this.ownerDocument.removeEventListener("pointerdown", this.#onDocumentPointerDown, true);
    this.ownerDocument.removeEventListener("keydown", this.#onDocumentKeyDown, true);
    this.#scrollController.release();
    super.disconnectedCallback();
  }

  protected override updated(changedProperties: PropertyValues<this>): void {
    if (changedProperties.has("_settingsOpen")) {
      this.toggleAttribute("settings-open", this._settingsOpen);
    }
    const identity = objectiveScrollIdentity(this.viewModel);
    this.#scrollController.bind(this.renderRoot, identity);
    if (changedProperties.has("viewModel")) {
      const previous = changedProperties.get("viewModel") as
        | GoalProgressViewModel
        | null
        | undefined;
      const previousIdentity = objectiveScrollIdentity(previous);
      const previousActiveObjectiveId = activeObjectiveId(previous);
      const nextActiveObjectiveId = activeObjectiveId(this.viewModel);
      if (
        nextActiveObjectiveId !== null &&
        (previousIdentity !== identity || previousActiveObjectiveId !== nextActiveObjectiveId)
      ) {
        this.#scrollController.scheduleActiveObjective(this.renderRoot);
      }
    }
    this.#publishLayoutOffset();
    if (this.placement === "floating") {
      this.dispatchEvent(
        new CustomEvent(GOAL_PROGRESS_FLOATING_LAYOUT_EVENT, {
          bubbles: true,
          composed: true,
        }),
      );
    }
  }

  protected override willUpdate(changedProperties: PropertyValues<this>): void {
    this.#scrollController.captureScrollPosition();
    if (changedProperties.has("viewModel")) {
      const previous = changedProperties.get("viewModel") as
        | GoalProgressViewModel
        | null
        | undefined;
      const next = this.viewModel;
      if (
        !next ||
        (previous &&
          (previous.contractId !== next.contractId ||
            previous.sessionId !== next.sessionId ||
            next.trackingPhase === "detached"))
      ) {
        this.#displaySettingsMenu.close();
      }
    }
  }

  #publishLayoutOffset(): void {
    const content = this.renderRoot.querySelector<HTMLElement>(".content");
    const expandedOffset =
      this.placement === "floating" || this.collapsed || !content
        ? 0
        : Math.ceil(content.getBoundingClientRect().height);
    if (expandedOffset === this.#lastLayoutOffset) {
      return;
    }
    this.#lastLayoutOffset = expandedOffset;
    this.dispatchEvent(
      new CustomEvent(GOAL_PROGRESS_LAYOUT_OFFSET_EVENT, {
        detail: { expandedOffset },
        bubbles: true,
        composed: true,
      }),
    );
  }

  #setCollapsed(collapsed: boolean, restoreFocus: boolean): void {
    this.collapsed = collapsed;
    this.#displaySettingsMenu.close();
    this.dispatchEvent(
      new CustomEvent(GOAL_PROGRESS_SET_COLLAPSED_EVENT, {
        detail: { collapsed: this.collapsed },
        bubbles: true,
        composed: true,
      }),
    );
    if (restoreFocus) {
      void this.updateComplete.then(() => {
        this.renderRoot.querySelector<HTMLButtonElement>(".collapse-toggle")?.focus();
      });
    }
  }

  #toggleCollapsed = (): void => {
    this.#setCollapsed(!this.collapsed, false);
  };

  readonly #onDocumentPointerDown = (event: PointerEvent): void => {
    if (this.#displaySettingsMenu.handleDocumentPointerDown(event)) {
      return;
    }
    if (this.placement === "floating" && !this.collapsed) {
      this.#setCollapsed(true, false);
    }
  };

  readonly #onDocumentKeyDown = (event: KeyboardEvent): void => {
    if (event.key !== "Escape") {
      return;
    }
    if (this.#displaySettingsMenu.handleDocumentKeyDown(event)) {
      return;
    }
    if (this.placement === "floating" && !this.collapsed) {
      event.preventDefault();
      this.#setCollapsed(true, true);
    }
  };

  #publishFloatingXRatio(commit: boolean): void {
    this.dispatchEvent(
      new CustomEvent(GOAL_PROGRESS_SET_FLOATING_X_RATIO_EVENT, {
        detail: { floatingXRatio: this.floatingXRatio, commit },
        bubbles: true,
        composed: true,
      }),
    );
  }

  #moveFloatingPointer(event: PointerEvent): void {
    const deltaX = event.clientX - this.#floatingPointerStartX;
    if (!this.#floatingPointerMoved && Math.abs(deltaX) < 3) {
      return;
    }
    this.#floatingPointerMoved = true;
    event.preventDefault();
    const surface = event.currentTarget as HTMLElement;
    const chip = this.renderRoot.querySelector<HTMLElement>(".floating-chip");
    const availableWidth = Math.max(
      1,
      surface.getBoundingClientRect().width - (chip?.getBoundingClientRect().width ?? 0),
    );
    const targetRatio = Math.max(
      0,
      Math.min(1, this.#floatingPointerStartRatio + deltaX / availableWidth),
    );
    if (targetRatio !== this.#floatingPointerTargetRatio) {
      this.#floatingPointerTargetRatio = targetRatio;
      this.floatingXRatio = targetRatio;
      this.#publishFloatingXRatio(false);
    }
  }

  #startFloatingPointer = (event: PointerEvent): void => {
    const interactive = event
      .composedPath()
      .some(
        (node) =>
          node instanceof Element &&
          node.matches(
            "button, a, input, select, textarea, [contenteditable], [role='menu'], .objective-list",
          ),
      );
    if (event.button !== 0 || interactive) {
      return;
    }
    if (this.getBoundingClientRect().width <= 0) {
      return;
    }
    this.#floatingPointerId = event.pointerId;
    this.#floatingPointerMoved = false;
    this.#floatingPointerStartRatio = this.floatingXRatio;
    this.#floatingPointerTargetRatio = this.floatingXRatio;
    this.#floatingPointerStartX = event.clientX;
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  };

  #moveFloatingPointerEvent = (event: PointerEvent): void => {
    if (this.#floatingPointerId !== event.pointerId) {
      return;
    }
    this.#moveFloatingPointer(event);
  };

  #endFloatingPointer = (event: PointerEvent): void => {
    if (this.#floatingPointerId !== event.pointerId) {
      return;
    }
    const target = event.currentTarget as HTMLElement;
    if (target.hasPointerCapture(event.pointerId)) {
      target.releasePointerCapture(event.pointerId);
    }
    this.#floatingPointerId = null;
    if (
      this.#floatingPointerMoved &&
      this.#floatingPointerTargetRatio !== this.#floatingPointerStartRatio
    ) {
      this.floatingXRatio = this.#floatingPointerTargetRatio;
      this.#publishFloatingXRatio(true);
    } else {
      this.floatingXRatio = this.#floatingPointerStartRatio;
    }
    this.#floatingPointerMoved = false;
  };

  #cancelFloatingPointer = (event: PointerEvent): void => {
    if (this.#floatingPointerId === event.pointerId) {
      if (this.floatingXRatio !== this.#floatingPointerStartRatio) {
        this.floatingXRatio = this.#floatingPointerStartRatio;
        this.#publishFloatingXRatio(false);
      }
      this.#floatingPointerId = null;
      this.#floatingPointerMoved = false;
    }
  };

  #moveFloatingWithKeyboard = (event: KeyboardEvent): void => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
      return;
    }
    event.preventDefault();
    const delta = event.key === "ArrowRight" ? 0.05 : -0.05;
    this.floatingXRatio = Math.max(0, Math.min(1, this.floatingXRatio + delta));
    this.#publishFloatingXRatio(true);
  };

  #requestRetry = (): void => {
    this.dispatchEvent(
      new CustomEvent(GOAL_PROGRESS_REQUEST_RETRY_EVENT, {
        bubbles: true,
        composed: true,
      }),
    );
  };

  #requestDetach = (): void => {
    this.dispatchEvent(
      new CustomEvent(GOAL_PROGRESS_REQUEST_DETACH_EVENT, {
        bubbles: true,
        composed: true,
      }),
    );
  };

  markUpdateSeen(): void {
    const latestVersion = this.updateState?.latestVersion;
    if (isGoalProgressUpdateVersion(latestVersion)) {
      this._updateSeenVersion = latestVersion;
    }
  }

  #dispatchUpdateIntent(intent: GoalProgressUpdateIntent): void {
    if ("version" in intent && !isGoalProgressUpdateVersion(intent.version)) {
      return;
    }
    this.dispatchEvent(
      new CustomEvent(GOAL_PROGRESS_UPDATE_INTENT_EVENT, {
        detail: intent,
        bubbles: true,
        composed: true,
      }),
    );
  }

  #checkUpdate = (): void => {
    if (!this.updateState || this.updateState.phase === "checking") {
      return;
    }
    this.#dispatchUpdateIntent({ type: "check" });
  };

  #openCurrentRelease = (): void => {
    const version = this.updateState?.currentVersion;
    if (isGoalProgressUpdateVersion(version)) {
      this.#dispatchUpdateIntent({ type: "open-release", version });
    }
  };

  #openLatestRelease = (): void => {
    const version = this.updateState?.latestVersion;
    if (isGoalProgressUpdateVersion(version)) {
      this.#dispatchUpdateIntent({ type: "open-release", version });
    }
  };

  #startUpdate = (): void => {
    const version = this.updateState?.latestVersion;
    if (!this.updateState || !isGoalProgressUpdateVersion(version)) {
      return;
    }
    this.markUpdateSeen();
    this.#dispatchUpdateIntent({ type: "start", version });
  };

  #retryUpdate = (): void => {
    const version = this.updateState?.latestVersion;
    if (!this.updateState || !isGoalProgressUpdateVersion(version)) {
      return;
    }
    this.#dispatchUpdateIntent({ type: "retry", version });
  };

  #restartNow = (): void => {
    const version = this.updateState?.latestVersion;
    if (isGoalProgressUpdateVersion(version)) {
      this.#dispatchUpdateIntent({ type: "restart-now", version });
    }
  };

  #restartLater = (): void => {
    const version = this.updateState?.latestVersion;
    if (!isGoalProgressUpdateVersion(version)) {
      return;
    }
    this.markUpdateSeen();
    this.#dispatchUpdateIntent({ type: "restart-later", version });
  };

  override render() {
    const viewModel = this.viewModel;
    const locale = resolveGoalProgressLocale(this.locale);
    if (!viewModel) {
      return html`<section class="panel phase-error placement-${this.placement}">
        ${renderErrorView(null, this.#requestRetry, this.#requestDetach, locale.messages)}
      </section>`;
    }
    if (viewModel.trackingPhase === "preparing") {
      return html`<section class="panel phase-preparing">
        ${renderPreparingView(viewModel, locale.messages)}
      </section>`;
    }
    if (viewModel.trackingPhase === "error") {
      return html`<section class="panel phase-error placement-${this.placement}">
        ${renderErrorView(viewModel, this.#requestRetry, this.#requestDetach, locale.messages)}
      </section>`;
    }
    if (viewModel.trackingPhase === "detached") {
      return nothing;
    }
    const latestVersion = this.updateState?.latestVersion;
    const updateUnread =
      this.updateState?.phase === "available" &&
      isGoalProgressUpdateVersion(latestVersion) &&
      latestVersion !== this.updateState.lastSeenUpdateVersion &&
      latestVersion !== this._updateSeenVersion;
    const updatePromptDismissed =
      isGoalProgressUpdateVersion(latestVersion) &&
      latestVersion === this.updateState?.promptDismissedForVersion;
    return html`<section class="panel phase-${viewModel.trackingPhase} placement-${this.placement}">
      ${renderTrackingView(viewModel, {
        collapsed: this.collapsed,
        motionPaused: this.motionPaused,
        placement: this.placement,
        requestedPlacement: this.requestedPlacement,
        spaceConstrained: this.spaceConstrained,
        floatingPanelConstrained: this.floatingPanelConstrained,
        settingsOpen: this._settingsOpen,
        scrolling: this._scrolling,
        scrollable: this._scrollable,
        thumbSize: this._scrollThumbSize,
        thumbOffset: this._scrollThumbOffset,
        messages: locale.messages,
        locale: locale.locale,
        onFloatingPointerCancel: this.#cancelFloatingPointer,
        onFloatingPointerDown: this.#startFloatingPointer,
        onFloatingKeyDown: this.#moveFloatingWithKeyboard,
        onFloatingPointerMove: this.#moveFloatingPointerEvent,
        onFloatingPointerUp: this.#endFloatingPointer,
        onSelectPlacement: this.#displaySettingsMenu.selectPlacement,
        onCheckUpdate: this.#checkUpdate,
        onOpenCurrentRelease: this.#openCurrentRelease,
        onOpenLatestRelease: this.#openLatestRelease,
        onStartUpdate: this.#startUpdate,
        onRetryUpdate: this.#retryUpdate,
        onRestartNow: this.#restartNow,
        onRestartLater: this.#restartLater,
        onToggleMotionPaused: this.#displaySettingsMenu.toggleMotionPaused,
        onTogglePlacementSettings: this.#displaySettingsMenu.toggle,
        onToggleCollapsed: this.#toggleCollapsed,
        updateState: this.updateState,
        updateUnread,
        updatePromptDismissed,
      })}
    </section>`;
  }
}
