import { execFile } from "node:child_process";
import { StrictSemverSchema } from "../../../packages/contracts/src/index.js";

export const GOAL_PROGRESS_RELEASE_URL_PREFIX =
  "https://github.com/Ezra-Y/codex-goal-progress/releases/tag/v";

export type MacosReleaseOpener = (url: string) => Promise<void>;

export function goalProgressReleaseUrl(version: string): string {
  return `${GOAL_PROGRESS_RELEASE_URL_PREFIX}${StrictSemverSchema.parse(version)}`;
}

export async function openMacosGoalProgressRelease(version: string): Promise<void> {
  const url = goalProgressReleaseUrl(version);
  await new Promise<void>((resolveOpen, rejectOpen) => {
    execFile("/usr/bin/open", [url], { windowsHide: true }, (error) => {
      if (error) {
        rejectOpen(new Error("GOAL_PROGRESS_UPDATE_RELEASE_OPEN_FAILED"));
        return;
      }
      resolveOpen();
    });
  });
}
