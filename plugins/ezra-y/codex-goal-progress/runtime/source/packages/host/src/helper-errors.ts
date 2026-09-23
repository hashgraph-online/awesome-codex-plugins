import { GoalProgressIpcClientError, GoalProgressIpcHandlerError } from "../../ipc/src/index.js";
import { GoalProgressStoreError } from "../../store/src/index.js";

export function helperErrorCode(error: unknown): string {
  if (
    error instanceof GoalProgressStoreError ||
    error instanceof GoalProgressIpcClientError ||
    error instanceof GoalProgressIpcHandlerError
  ) {
    return error.code;
  }
  return "INTERNAL_ERROR";
}

export function helperDiagnosticCauseCode(error: unknown): string {
  const candidate = error instanceof Error && error.cause !== undefined ? error.cause : error;
  if (
    candidate !== null &&
    typeof candidate === "object" &&
    "code" in candidate &&
    typeof candidate.code === "string" &&
    candidate.code.trim()
  ) {
    return candidate.code.slice(0, 128);
  }
  if (candidate instanceof Error) {
    const stablePrefix = /^([A-Z][A-Z0-9_]{2,127})/.exec(candidate.message)?.[1];
    return stablePrefix ?? candidate.name.slice(0, 128);
  }
  return `UNKNOWN_${typeof candidate}`.slice(0, 128);
}

export function toHelperHandlerError(error: unknown): GoalProgressIpcHandlerError {
  if (error instanceof GoalProgressIpcHandlerError) {
    return error;
  }
  if (error instanceof GoalProgressStoreError) {
    return new GoalProgressIpcHandlerError(
      error.code,
      error.message,
      error.committedRevision ?? null,
    );
  }
  return new GoalProgressIpcHandlerError(
    "INTERNAL_ERROR",
    "Goal Progress Helper request failed",
    null,
    undefined,
    error,
  );
}
