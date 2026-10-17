import type {
  GoalProgressUpdateIntent,
  GoalProgressUpdateNextStep,
  GoalProgressUpdatePhase,
  GoalProgressUpdateState,
} from "./update-state.js";

export const GOAL_PROGRESS_UPDATE_STATE_SCHEMA_VERSION = 1 as const;
export const GOAL_PROGRESS_UPDATE_INTENT_PROTOCOL_VERSION = 1 as const;
export const GOAL_PROGRESS_UPDATE_INTENT_MAX_BYTES = 1_024;
export const GOAL_PROGRESS_UPDATE_INTENT_EVENT = "goal-progress-update-intent";

const strictSemverPattern =
  /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$/u;
const timestampPattern = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/u;
const errorCodePattern = /^[A-Z][A-Z0-9_]{2,127}$/u;
const phases: readonly GoalProgressUpdatePhase[] = [
  "up-to-date",
  "checking",
  "available",
  "check-failed",
  "preparing",
  "downloading",
  "verifying",
  "installing",
  "download-failed",
  "update-failed",
  "restart-required",
  "restarting",
] as const;
const nextSteps: readonly Exclude<GoalProgressUpdateNextStep, null>[] = [
  "check",
  "download",
  "retry",
  "restart",
] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isTimestamp(value: unknown): value is string {
  return (
    typeof value === "string" && timestampPattern.test(value) && Number.isFinite(Date.parse(value))
  );
}

function isNullableVersion(value: unknown): value is string | null {
  return value === null || isGoalProgressUpdateVersion(value);
}

export function isGoalProgressUpdateVersion(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length >= 5 &&
    value.length <= 64 &&
    value.trim() === value &&
    strictSemverPattern.test(value)
  );
}

function compareNumericIdentifier(left: string, right: string): -1 | 0 | 1 {
  if (left.length !== right.length) {
    return left.length > right.length ? 1 : -1;
  }
  return left === right ? 0 : left > right ? 1 : -1;
}

function isNumericIdentifier(value: string): boolean {
  return [...value].every((character) => character >= "0" && character <= "9");
}

export function compareGoalProgressUpdateVersions(left: string, right: string): -1 | 0 | 1 {
  const leftMatch = strictSemverPattern.exec(left);
  const rightMatch = strictSemverPattern.exec(right);
  if (!leftMatch || !rightMatch) {
    throw new Error("GOAL_PROGRESS_UPDATE_VERSION_INVALID");
  }
  for (let index = 1; index <= 3; index += 1) {
    const comparison = compareNumericIdentifier(leftMatch[index] ?? "", rightMatch[index] ?? "");
    if (comparison !== 0) {
      return comparison;
    }
  }
  const leftPreRelease = leftMatch[4];
  const rightPreRelease = rightMatch[4];
  if (leftPreRelease === undefined || rightPreRelease === undefined) {
    return leftPreRelease === rightPreRelease ? 0 : leftPreRelease === undefined ? 1 : -1;
  }
  const leftParts = leftPreRelease.split(".");
  const rightParts = rightPreRelease.split(".");
  const length = Math.max(leftParts.length, rightParts.length);
  for (let index = 0; index < length; index += 1) {
    const leftPart = leftParts[index];
    const rightPart = rightParts[index];
    if (leftPart === undefined || rightPart === undefined) {
      return leftPart === rightPart ? 0 : leftPart === undefined ? -1 : 1;
    }
    if (leftPart === rightPart) {
      continue;
    }
    const leftNumeric = isNumericIdentifier(leftPart);
    const rightNumeric = isNumericIdentifier(rightPart);
    if (leftNumeric && rightNumeric) {
      return compareNumericIdentifier(leftPart, rightPart);
    }
    if (leftNumeric !== rightNumeric) {
      return leftNumeric ? -1 : 1;
    }
    return leftPart > rightPart ? 1 : -1;
  }
  return 0;
}

export function parseGoalProgressUpdateState(value: unknown): GoalProgressUpdateState | null {
  if (
    !isRecord(value) ||
    Object.keys(value).length !== (Object.hasOwn(value, "deliveryMode") ? 16 : 15) ||
    (Object.hasOwn(value, "deliveryMode") &&
      value.deliveryMode !== "plugin-marketplace" &&
      value.deliveryMode !== "prebuilt-release")
  ) {
    return null;
  }
  const phase = value.phase;
  const nextStep = value.nextStep;
  if (
    value.schemaVersion !== GOAL_PROGRESS_UPDATE_STATE_SCHEMA_VERSION ||
    !Number.isSafeInteger(value.stateRevision) ||
    (value.stateRevision as number) < 1 ||
    !isGoalProgressUpdateVersion(value.currentVersion) ||
    !isNullableVersion(value.latestVersion) ||
    typeof phase !== "string" ||
    !phases.includes(phase as GoalProgressUpdatePhase) ||
    (value.checkedAt !== null && !isTimestamp(value.checkedAt)) ||
    !isNullableVersion(value.lastSeenUpdateVersion) ||
    !isNullableVersion(value.promptDismissedForVersion) ||
    !Number.isSafeInteger(value.downloadedBytes) ||
    (value.downloadedBytes as number) < 0 ||
    (value.totalBytes !== null &&
      (!Number.isSafeInteger(value.totalBytes) || (value.totalBytes as number) <= 0)) ||
    (value.downloadPercent !== null &&
      (typeof value.downloadPercent !== "number" ||
        !Number.isFinite(value.downloadPercent) ||
        value.downloadPercent < 0 ||
        value.downloadPercent > 100)) ||
    typeof value.restartRequired !== "boolean" ||
    (value.lastErrorCode !== null &&
      (typeof value.lastErrorCode !== "string" || !errorCodePattern.test(value.lastErrorCode))) ||
    (nextStep !== null &&
      (typeof nextStep !== "string" ||
        !nextSteps.includes(nextStep as Exclude<GoalProgressUpdateNextStep, null>))) ||
    !isTimestamp(value.updatedAt)
  ) {
    return null;
  }
  const typedPhase = phase as GoalProgressUpdatePhase;
  if (
    (typedPhase !== "up-to-date" &&
      typedPhase !== "checking" &&
      typedPhase !== "check-failed" &&
      value.latestVersion === null) ||
    value.restartRequired !== (typedPhase === "restart-required" || typedPhase === "restarting") ||
    (value.totalBytes !== null &&
      (value.downloadedBytes as number) > (value.totalBytes as number)) ||
    (value.downloadPercent !== null && value.totalBytes === null)
  ) {
    return null;
  }
  return value as unknown as GoalProgressUpdateState;
}

export function parseGoalProgressUpdateIntent(value: unknown): GoalProgressUpdateIntent | null {
  if (!isRecord(value) || typeof value.type !== "string") {
    return null;
  }
  if (value.type === "check") {
    return Object.keys(value).length === 1 ? { type: "check" } : null;
  }
  if (
    value.type !== "start" &&
    value.type !== "retry" &&
    value.type !== "restart-now" &&
    value.type !== "restart-later" &&
    value.type !== "open-release"
  ) {
    return null;
  }
  if (Object.keys(value).length !== 2 || !isGoalProgressUpdateVersion(value.version)) {
    return null;
  }
  return { type: value.type, version: value.version };
}
