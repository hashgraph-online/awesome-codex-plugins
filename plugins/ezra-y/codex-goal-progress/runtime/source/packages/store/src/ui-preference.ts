import { readFile } from "node:fs/promises";
import {
  DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
  DEFAULT_GOAL_PROGRESS_UI_PREFERENCE,
  type GoalProgressTrackingOverlay,
  GoalProgressTrackingOverlaySchema,
  type GoalProgressUiPreference,
  GoalProgressUiPreferenceSchema,
  migrateGoalProgressUiPreference,
} from "../../contracts/src/index.js";
import { atomicWriteFile } from "./atomic.js";
import type { GoalProgressPaths, GoalProgressSessionPaths } from "./paths.js";

function isNotFound(error: unknown): boolean {
  return (
    error instanceof Error && "code" in error && (error as NodeJS.ErrnoException).code === "ENOENT"
  );
}

export async function readGoalProgressUiPreference(
  paths: GoalProgressPaths,
): Promise<GoalProgressUiPreference> {
  let contents: string;
  try {
    contents = await readFile(paths.uiPreferencePath, "utf8");
  } catch (error) {
    if (!isNotFound(error)) {
      throw error;
    }
    try {
      contents = await readFile(paths.legacyUiPreferencePath, "utf8");
    } catch (legacyError) {
      if (isNotFound(legacyError)) {
        return DEFAULT_GOAL_PROGRESS_UI_PREFERENCE;
      }
      throw legacyError;
    }
  }
  return (
    migrateGoalProgressUiPreference(JSON.parse(contents)) ?? DEFAULT_GOAL_PROGRESS_UI_PREFERENCE
  );
}

export async function writeGoalProgressUiPreference(
  paths: GoalProgressPaths,
  preference: GoalProgressUiPreference,
): Promise<GoalProgressUiPreference> {
  const parsed = GoalProgressUiPreferenceSchema.parse(preference);
  await atomicWriteFile(paths.uiPreferencePath, `${JSON.stringify(parsed, null, 2)}\n`);
  return parsed;
}

export async function readGoalProgressTrackingOverlay(
  sessionPaths: GoalProgressSessionPaths,
): Promise<GoalProgressTrackingOverlay> {
  try {
    const parsed = GoalProgressTrackingOverlaySchema.safeParse(
      JSON.parse(await readFile(sessionPaths.overlayPath, "utf8")),
    );
    return parsed.success ? parsed.data : DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY;
  } catch (error) {
    if (isNotFound(error)) {
      return DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY;
    }
    throw error;
  }
}

export async function writeGoalProgressTrackingOverlay(
  sessionPaths: GoalProgressSessionPaths,
  overlay: GoalProgressTrackingOverlay,
): Promise<GoalProgressTrackingOverlay> {
  const parsed = GoalProgressTrackingOverlaySchema.parse(overlay);
  await atomicWriteFile(sessionPaths.overlayPath, `${JSON.stringify(parsed, null, 2)}\n`);
  return parsed;
}
