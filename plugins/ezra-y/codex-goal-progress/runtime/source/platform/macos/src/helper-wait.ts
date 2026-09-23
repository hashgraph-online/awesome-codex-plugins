import { rm } from "node:fs/promises";
import {
  type GoalProgressPaths,
  readCurrentHelperIdentity,
} from "../../../packages/store/src/index.js";
import type { HelperReadinessInspection } from "./installed-inspection.js";

export const HELPER_READY_TIMEOUT_MS = 45_000;
export const HELPER_READY_INTERVAL_MS = 250;
export const HELPER_READY_PING_TIMEOUT_MS = 1_000;
export const HELPER_STOP_TIMEOUT_MS = 1_750;
export const HELPER_STOP_INTERVAL_MS = 100;

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolveDelay) => setTimeout(resolveDelay, milliseconds));
}

export interface HelperReadyClock {
  readonly now: () => number;
  readonly wait: (milliseconds: number) => Promise<void>;
}

export interface HelperStoppedClock {
  readonly now: () => number;
  readonly wait: (milliseconds: number) => Promise<void>;
}

export async function waitForHelperReady(
  inspect: (timeoutMs: number) => Promise<HelperReadinessInspection>,
  clock: HelperReadyClock = {
    now: Date.now,
    wait: delay,
  },
): Promise<boolean> {
  const deadline = clock.now() + HELPER_READY_TIMEOUT_MS;
  while (clock.now() < deadline) {
    const remainingBeforePing = deadline - clock.now();
    const inspection = await inspect(Math.min(HELPER_READY_PING_TIMEOUT_MS, remainingBeforePing));
    if (inspection.ready) {
      return true;
    }
    const remainingAfterPing = deadline - clock.now();
    if (remainingAfterPing <= 0) {
      return false;
    }
    await clock.wait(Math.min(HELPER_READY_INTERVAL_MS, remainingAfterPing));
  }
  return false;
}

export async function waitForHelperStopped(
  paths: GoalProgressPaths,
  clock: HelperStoppedClock = {
    now: Date.now,
    wait: delay,
  },
  operations: {
    readonly isStopped: () => Promise<boolean>;
    readonly removeSocket: () => Promise<void>;
  } = {
    isStopped: async () => (await readCurrentHelperIdentity(paths).catch(() => null)) === null,
    removeSocket: async () => rm(paths.helperSocketPath, { force: true }),
  },
): Promise<void> {
  const deadline = clock.now() + HELPER_STOP_TIMEOUT_MS;
  for (;;) {
    if (await operations.isStopped()) {
      await operations.removeSocket();
      return;
    }
    const remaining = deadline - clock.now();
    if (remaining <= 0) {
      throw new Error("GOAL_PROGRESS_HELPER_STOP_TIMEOUT");
    }
    await clock.wait(Math.min(HELPER_STOP_INTERVAL_MS, remaining));
  }
}
