import { lstat, readFile, stat } from "node:fs/promises";
import { resolve } from "node:path";
import {
  GOAL_PROGRESS_IPC_PROTOCOL_VERSION,
  GoalProgressIpcClient,
} from "../../../packages/ipc/src/index.js";
import {
  type GoalProgressPaths,
  inspectCurrentHelperOwners,
  readCurrentHelperIdentity,
} from "../../../packages/store/src/index.js";
import type { MacosInstallationLayout } from "./install-layout.js";
import { isNotFound, stableErrorCode } from "./macos-errors.js";
import { GOAL_PROGRESS_STABLE_HOOK_COMMAND } from "./plugin-release.js";
import {
  fileSha256,
  type InstalledManifest,
  type ParsedReleaseManifest,
} from "./verified-release.js";

export interface HelperHealthInspection {
  readonly ok: boolean;
  readonly socketPathExists: boolean;
  readonly socketIsSocket: boolean;
  readonly socketMode: number | null;
  readonly pingOk: boolean;
  readonly protocolVersion: number | null;
  readonly protocolMatches: boolean;
  readonly pid: number | null;
  readonly identityPid: number | null;
  readonly pidMatches: boolean;
  readonly ownerCount: number;
  readonly singleOwner: boolean;
  readonly storeReadOnly: boolean;
  readonly startupListenerRunning: boolean;
  readonly startupListenerReady: boolean;
  readonly startupListenerPid: number | null;
  readonly code: string | null;
}

export interface HelperReadinessInspection {
  readonly pingOk: boolean;
  readonly ready: boolean;
  readonly code: string | null;
}

export interface InstalledHookInspection {
  readonly hashMatchesManifest: boolean;
  readonly stableCommand: boolean;
  readonly userLevelHookAbsent: boolean;
  readonly embeddedTrustStateAbsent: boolean;
}

export async function inspectInstalledHelperReadiness(
  paths: GoalProgressPaths,
  timeoutMs = 1_000,
): Promise<HelperReadinessInspection> {
  const client = new GoalProgressIpcClient(paths.helperSocketPath, {
    clientKind: "doctor",
    timeoutMs,
  });
  try {
    const ping = await client.request({ method: "ping", params: {} });
    const result =
      ping.result !== null && typeof ping.result === "object"
        ? (ping.result as Record<string, unknown>)
        : {};
    const pingOk =
      ping.protocolVersion === GOAL_PROGRESS_IPC_PROTOCOL_VERSION &&
      result.status === "ok" &&
      Number.isInteger(result.pid);
    return {
      pingOk,
      ready: pingOk && result.ready === true,
      code: pingOk ? null : "HELPER_PING_INVALID",
    };
  } catch (error) {
    return {
      pingOk: false,
      ready: false,
      code: stableErrorCode(error),
    };
  }
}

export async function inspectInstalledHelper(
  paths: GoalProgressPaths,
): Promise<HelperHealthInspection> {
  let socketPathExists = false;
  let socketIsSocket = false;
  let socketMode: number | null = null;
  try {
    const metadata = await lstat(paths.helperSocketPath);
    socketPathExists = true;
    socketIsSocket = metadata.isSocket();
    socketMode = metadata.mode & 0o777;
  } catch (error) {
    if (!isNotFound(error)) {
      return {
        ok: false,
        socketPathExists: false,
        socketIsSocket: false,
        socketMode: null,
        pingOk: false,
        protocolVersion: null,
        protocolMatches: false,
        pid: null,
        identityPid: null,
        pidMatches: false,
        ownerCount: 0,
        singleOwner: false,
        storeReadOnly: false,
        startupListenerRunning: false,
        startupListenerReady: false,
        startupListenerPid: null,
        code: stableErrorCode(error),
      };
    }
  }

  const [identity, owners] = await Promise.all([
    readCurrentHelperIdentity(paths).catch(() => null),
    inspectCurrentHelperOwners(paths).catch(() => []),
  ]);
  let pingOk = false;
  let protocolVersion: number | null = null;
  let protocolMatches = false;
  let pid: number | null = null;
  let instanceId: string | null = null;
  let storeReadOnly = false;
  let startupListenerRunning = false;
  let startupListenerReady = false;
  let startupListenerPid: number | null = null;
  let code: string | null = socketPathExists ? null : "HELPER_SOCKET_MISSING";
  if (socketIsSocket) {
    const client = new GoalProgressIpcClient(paths.helperSocketPath, {
      clientKind: "doctor",
      timeoutMs: 1_000,
    });
    try {
      const ping = await client.request({ method: "ping", params: {} });
      protocolVersion = ping.protocolVersion;
      protocolMatches = ping.protocolVersion === GOAL_PROGRESS_IPC_PROTOCOL_VERSION;
      const result =
        ping.result !== null && typeof ping.result === "object"
          ? (ping.result as Record<string, unknown>)
          : {};
      pingOk = result.status === "ok" && Number.isInteger(result.pid);
      pid = pingOk ? Number(result.pid) : null;
      instanceId = typeof result.instanceId === "string" ? result.instanceId : null;
      if (!pingOk) {
        code = "HELPER_PING_INVALID";
      } else if (!protocolMatches) {
        code = "PROTOCOL_VERSION_MISMATCH";
      } else {
        const doctor = await client.request({ method: "doctor", params: {} });
        const doctorResult =
          doctor.result !== null && typeof doctor.result === "object"
            ? (doctor.result as Record<string, unknown>)
            : {};
        const storeSmoke =
          doctorResult.storeSmoke !== null && typeof doctorResult.storeSmoke === "object"
            ? (doctorResult.storeSmoke as Record<string, unknown>)
            : {};
        storeReadOnly =
          storeSmoke.checked === true && storeSmoke.readable === true && storeSmoke.code === null;
        const runtime =
          doctorResult.runtime !== null && typeof doctorResult.runtime === "object"
            ? (doctorResult.runtime as Record<string, unknown>)
            : {};
        const startupListener =
          runtime.startupListener !== null && typeof runtime.startupListener === "object"
            ? (runtime.startupListener as Record<string, unknown>)
            : {};
        startupListenerRunning = startupListener.running === true;
        startupListenerReady = startupListener.ready === true;
        startupListenerPid = Number.isInteger(startupListener.pid)
          ? Number(startupListener.pid)
          : null;
        if (!storeReadOnly) {
          code = "HELPER_STORE_READ_FAILED";
        }
      }
    } catch (error) {
      code = stableErrorCode(error);
    }
  } else if (socketPathExists) {
    code = "HELPER_SOCKET_INVALID";
  }

  const owner = owners[0];
  const singleOwner =
    owners.length === 1 &&
    identity !== null &&
    owner?.instanceId === identity.instanceId &&
    owner.pid === identity.pid;
  const pidMatches =
    pingOk && identity !== null && pid === identity.pid && instanceId === identity.instanceId;
  const ok =
    socketIsSocket && pingOk && protocolMatches && pidMatches && singleOwner && storeReadOnly;
  if (!code && !pidMatches) {
    code = "HELPER_PID_MISMATCH";
  }
  if (!code && !singleOwner) {
    code = "HELPER_OWNER_INVALID";
  }
  return {
    ok,
    socketPathExists,
    socketIsSocket,
    socketMode,
    pingOk,
    protocolVersion,
    protocolMatches,
    pid,
    identityPid: identity?.pid ?? null,
    pidMatches,
    ownerCount: owners.length,
    singleOwner,
    storeReadOnly,
    startupListenerRunning,
    startupListenerReady,
    startupListenerPid,
    code: ok ? null : code,
  };
}

export async function inspectInstalledHook(
  homeDirectory: string,
  installed: InstalledManifest,
): Promise<InstalledHookInspection> {
  const hookPath = resolve(
    installed.programReleaseRoot,
    "plugin-marketplace/plugins/codex-goal-progress/hooks/hooks.json",
  );
  const hookText = await readFile(hookPath, "utf8");
  const hookDocument = JSON.parse(hookText) as {
    hooks?: Record<string, Array<{ hooks?: Array<{ command?: unknown }> }>>;
  };
  const commands = Object.values(hookDocument.hooks ?? {}).flatMap((groups) =>
    groups.flatMap((group) => (group.hooks ?? []).map((hook) => hook.command)),
  );
  let userLevelHookAbsent = true;
  try {
    const userHookText = (
      await readFile(resolve(homeDirectory, ".codex/hooks.json"), "utf8")
    ).toLowerCase();
    userLevelHookAbsent =
      !userHookText.includes("goal_progress") &&
      !userHookText.includes("goal-progress") &&
      !userHookText.includes("codexgoalprogress");
  } catch (error) {
    if (!isNotFound(error)) {
      throw error;
    }
  }
  return {
    hashMatchesManifest: (await fileSha256(hookPath)) === installed.hookSha256,
    stableCommand:
      commands.length > 0 &&
      commands.every((command) => command === GOAL_PROGRESS_STABLE_HOOK_COMMAND),
    userLevelHookAbsent,
    embeddedTrustStateAbsent:
      !hookText.includes("trusted_hash") &&
      !Object.hasOwn(hookDocument.hooks ?? {}, "UserPromptSubmit"),
  };
}

export async function startupListenerFileExists(
  layout: MacosInstallationLayout,
  release: ParsedReleaseManifest,
): Promise<boolean> {
  try {
    return (
      await stat(resolve(layout.programReleaseRoot, release.files.startupListener.path))
    ).isFile();
  } catch {
    return false;
  }
}
