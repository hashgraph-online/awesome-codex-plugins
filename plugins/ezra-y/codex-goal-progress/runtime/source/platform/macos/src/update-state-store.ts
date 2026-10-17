import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import {
  type GoalProgressUpdateState,
  GoalProgressUpdateStateSchema,
} from "../../../packages/contracts/src/index.js";
import { atomicWriteFile, type GoalProgressPaths } from "../../../packages/store/src/index.js";

export interface GoalProgressUpdateStateStore {
  readonly path: string;
  read(): Promise<GoalProgressUpdateState | null>;
  write(state: GoalProgressUpdateState): Promise<GoalProgressUpdateState>;
}

function isNotFound(error: unknown): boolean {
  return (
    error instanceof Error && "code" in error && (error as NodeJS.ErrnoException).code === "ENOENT"
  );
}

export function resolveMacosUpdateStatePath(paths: GoalProgressPaths): string {
  return resolve(paths.installRoot, "update.json");
}

export class MacosGoalProgressUpdateStateStore implements GoalProgressUpdateStateStore {
  readonly path: string;

  constructor(paths: GoalProgressPaths) {
    this.path = resolveMacosUpdateStatePath(paths);
  }

  async read(): Promise<GoalProgressUpdateState | null> {
    let contents: string;
    try {
      contents = await readFile(this.path, "utf8");
    } catch (error) {
      if (isNotFound(error)) {
        return null;
      }
      throw error;
    }
    try {
      return GoalProgressUpdateStateSchema.parse(JSON.parse(contents));
    } catch {
      throw new Error("GOAL_PROGRESS_UPDATE_STATE_INVALID");
    }
  }

  async write(state: GoalProgressUpdateState): Promise<GoalProgressUpdateState> {
    const parsed = GoalProgressUpdateStateSchema.parse(state);
    await atomicWriteFile(this.path, `${JSON.stringify(parsed, null, 2)}\n`);
    return parsed;
  }
}
