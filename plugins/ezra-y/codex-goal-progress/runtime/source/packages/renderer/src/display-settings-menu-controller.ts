import type { GoalProgressPlacement } from "../../contracts/src/index.js";
import {
  GOAL_PROGRESS_SET_MOTION_PAUSED_EVENT,
  GOAL_PROGRESS_SET_PLACEMENT_EVENT,
} from "../../contracts/src/renderer-events.js";

export interface DisplaySettingsMenuHost extends EventTarget {
  _settingsOpen: boolean;
  motionPaused: boolean;
  placement: GoalProgressPlacement;
  requestedPlacement: GoalProgressPlacement;
  markUpdateSeen(): void;
  readonly shadowRoot: ShadowRoot | null;
  readonly updateComplete: Promise<unknown>;
}

export class DisplaySettingsMenuController {
  readonly #host: DisplaySettingsMenuHost;

  constructor(host: DisplaySettingsMenuHost) {
    this.#host = host;
  }

  close(): void {
    this.#host._settingsOpen = false;
  }

  readonly position = (): void => {
    if (!this.#host._settingsOpen) return;
    const menu = this.#host.shadowRoot?.querySelector<HTMLElement>(".placement-menu");
    const trigger = this.#host.shadowRoot?.querySelector<HTMLElement>(
      ".placement-settings-trigger",
    );
    const view = menu?.ownerDocument.defaultView;
    if (!menu || !trigger || !view) return;
    menu.style.removeProperty("translate");
    const rect = menu.getBoundingClientRect();
    const scale = rect.width / Number.parseFloat(view.getComputedStyle(menu).width);
    const gap = 6 * scale;
    const top =
      rect.bottom > view.innerHeight - gap
        ? trigger.getBoundingClientRect().top - gap - rect.height
        : rect.top;
    const left = Math.max(gap, Math.min(rect.left, view.innerWidth - gap - rect.width));
    const clampedTop = Math.max(gap, Math.min(top, view.innerHeight - gap - rect.height));
    // 布局尺寸使用 CSS 像素，窗口测量包含页面 zoom，需要换算后移动菜单。
    menu.style.translate = `${(left - rect.left) / scale}px ${(clampedTop - rect.top) / scale}px`;
  };

  handleDocumentPointerDown(event: PointerEvent): boolean {
    if (event.composedPath().includes(this.#host)) {
      return true;
    }
    this.close();
    return false;
  }

  handleDocumentKeyDown(event: KeyboardEvent): boolean {
    if (event.key !== "Escape" || !this.#host._settingsOpen) {
      return false;
    }
    event.preventDefault();
    this.close();
    void this.#host.updateComplete.then(() =>
      this.#host.shadowRoot
        ?.querySelector<HTMLButtonElement>(".placement-settings-trigger")
        ?.focus(),
    );
    return true;
  }

  readonly toggle = (event: MouseEvent): void => {
    if (!event.isTrusted) {
      this.close();
      return;
    }
    this.#host._settingsOpen = !this.#host._settingsOpen;
    if (this.#host._settingsOpen) {
      this.#host.markUpdateSeen();
    }
  };

  readonly selectPlacement = (placement: GoalProgressPlacement): void => {
    this.#host.requestedPlacement = placement;
    this.#host.placement = placement;
    this.close();
    this.#host.dispatchEvent(
      new CustomEvent(GOAL_PROGRESS_SET_PLACEMENT_EVENT, {
        detail: { placement },
        bubbles: true,
        composed: true,
      }),
    );
  };

  readonly toggleMotionPaused = (): void => {
    this.#host.motionPaused = !this.#host.motionPaused;
    this.#host.dispatchEvent(
      new CustomEvent(GOAL_PROGRESS_SET_MOTION_PAUSED_EVENT, {
        detail: { motionPaused: this.#host.motionPaused },
        bubbles: true,
        composed: true,
      }),
    );
  };
}
