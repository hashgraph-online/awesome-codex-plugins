import {
  GOAL_PROGRESS_LAYOUT_OFFSET_EVENT,
  GOAL_PROGRESS_SET_COLLAPSED_EVENT,
  GOAL_PROGRESS_SET_FLOATING_X_RATIO_EVENT,
  GOAL_PROGRESS_SET_MOTION_PAUSED_EVENT,
  GOAL_PROGRESS_SET_PLACEMENT_EVENT,
} from "../../contracts/src/renderer-events.js";
import type { GoalProgressUiIntent } from "../../contracts/src/ui-preference.js";

const GOAL_PROGRESS_MAX_EXPANDED_OFFSET_PX = 1_200;

function eventDetail(event: Event): unknown {
  return "detail" in event ? (event as CustomEvent<unknown>).detail : undefined;
}

function booleanDetail(event: Event, key: "collapsed" | "motionPaused"): boolean | null {
  const detail = eventDetail(event);
  if (detail === null || typeof detail !== "object" || Array.isArray(detail)) {
    return null;
  }
  const value = (detail as Record<string, unknown>)[key];
  return typeof value === "boolean" ? value : null;
}

function placementDetail(event: Event): "inline" | "floating" | null {
  const detail = eventDetail(event);
  if (detail === null || typeof detail !== "object" || Array.isArray(detail)) {
    return null;
  }
  const value = (detail as Record<string, unknown>).placement;
  return value === "inline" || value === "floating" ? value : null;
}

function floatingXRatioDetail(event: Event): number | null {
  const detail = eventDetail(event);
  if (detail === null || typeof detail !== "object" || Array.isArray(detail)) {
    return null;
  }
  const value = (detail as Record<string, unknown>).floatingXRatio;
  return typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= 1
    ? value
    : null;
}

export type ParsedSidecarUiIntent =
  | { readonly intent: Extract<GoalProgressUiIntent, { type: "setCollapsed" }> }
  | { readonly intent: Extract<GoalProgressUiIntent, { type: "setMotionPaused" }> }
  | { readonly intent: Extract<GoalProgressUiIntent, { type: "setPlacement" }> }
  | {
      readonly intent: Extract<GoalProgressUiIntent, { type: "setFloatingXRatio" }>;
      readonly commit: boolean;
    };

export function parseSidecarUiIntent(event: Event): ParsedSidecarUiIntent | null {
  if (event.type === GOAL_PROGRESS_SET_COLLAPSED_EVENT) {
    const collapsed = booleanDetail(event, "collapsed");
    return collapsed === null ? null : { intent: { type: "setCollapsed", collapsed } };
  }
  if (event.type === GOAL_PROGRESS_SET_MOTION_PAUSED_EVENT) {
    const motionPaused = booleanDetail(event, "motionPaused");
    return motionPaused === null ? null : { intent: { type: "setMotionPaused", motionPaused } };
  }
  if (event.type === GOAL_PROGRESS_SET_PLACEMENT_EVENT) {
    const placement = placementDetail(event);
    return placement === null ? null : { intent: { type: "setPlacement", placement } };
  }
  if (event.type === GOAL_PROGRESS_SET_FLOATING_X_RATIO_EVENT) {
    const floatingXRatio = floatingXRatioDetail(event);
    if (floatingXRatio === null) {
      return null;
    }
    const detail = eventDetail(event);
    const commit =
      detail === null ||
      typeof detail !== "object" ||
      Array.isArray(detail) ||
      (detail as Record<string, unknown>).commit !== false;
    return {
      intent: { type: "setFloatingXRatio", floatingXRatio },
      commit,
    };
  }
  return null;
}

export function parseExpandedLayoutOffset(event: Event): number | null {
  if (event.type !== GOAL_PROGRESS_LAYOUT_OFFSET_EVENT) {
    return null;
  }
  const detail = eventDetail(event);
  if (detail === null || typeof detail !== "object" || Array.isArray(detail)) {
    return null;
  }
  const value = (detail as Record<string, unknown>).expandedOffset;
  return typeof value === "number" &&
    Number.isFinite(value) &&
    value >= 0 &&
    value <= GOAL_PROGRESS_MAX_EXPANDED_OFFSET_PX
    ? Math.ceil(value)
    : null;
}
