import { createHash } from "node:crypto";
import { homedir } from "node:os";
import { isAbsolute, resolve } from "node:path";
import { GoalProgressStoreError } from "./errors.js";

export interface GoalProgressPathOptions {
  readonly root?: string;
  readonly homeDirectory?: string;
  readonly platform?: NodeJS.Platform;
  readonly appDataDirectory?: string;
  readonly xdgDataDirectory?: string;
}

export interface GoalProgressPaths {
  readonly root: string;
  readonly stateRoot: string;
  readonly runtimeRoot: string;
  readonly logsRoot: string;
  readonly preferencesRoot: string;
  readonly installRoot: string;
  readonly programReleasesRoot: string;
  readonly helperSocketPath: string;
  readonly helperLocksRoot: string;
  readonly helperPidPath: string;
  readonly runtimeProofKeyPath: string;
  readonly runtimeProofConsumedRoot: string;
  readonly cdpRuntimePath: string;
  readonly helperLogPath: string;
  readonly installManifestPath: string;
  readonly uiPreferencePath: string;
  readonly legacyUiPreferencePath: string;
}

export interface GoalProgressSessionPaths {
  readonly sessionKey: string;
  readonly directory: string;
  readonly snapshotPath: string;
  readonly eventsPath: string;
  readonly overlayPath: string;
}

function defaultRoot(options: GoalProgressPathOptions): string {
  const platform = options.platform ?? process.platform;
  const homeDirectory = resolve(options.homeDirectory ?? homedir());
  if (platform === "darwin") {
    return resolve(homeDirectory, "Library", "Application Support", "CodexGoalProgress");
  }
  if (platform === "win32") {
    return resolve(
      options.appDataDirectory ?? resolve(homeDirectory, "AppData", "Roaming"),
      "CodexGoalProgress",
    );
  }
  return resolve(
    options.xdgDataDirectory ?? resolve(homeDirectory, ".local", "share"),
    "CodexGoalProgress",
  );
}

export function resolveGoalProgressPaths(options: GoalProgressPathOptions = {}): GoalProgressPaths {
  if (options.root !== undefined && !isAbsolute(options.root)) {
    throw new GoalProgressStoreError("STORE_PATH_INVALID", "Goal Progress root must be absolute");
  }
  const root = resolve(options.root ?? defaultRoot(options));
  const stateRoot = resolve(root, "state", "v1");
  const runtimeRoot = resolve(root, "runtime");
  const logsRoot = resolve(root, "logs");
  const preferencesRoot = resolve(root, "preferences", "v1");
  const installRoot = resolve(root, "install");
  const programReleasesRoot = resolve(installRoot, "releases");
  return {
    root,
    stateRoot,
    runtimeRoot,
    logsRoot,
    preferencesRoot,
    installRoot,
    programReleasesRoot,
    helperSocketPath: resolve(runtimeRoot, "helper.sock"),
    helperLocksRoot: resolve(runtimeRoot, "helper-locks"),
    helperPidPath: resolve(runtimeRoot, "helper.pid.json"),
    runtimeProofKeyPath: resolve(runtimeRoot, "runtime-context.key"),
    runtimeProofConsumedRoot: resolve(runtimeRoot, "runtime-proof-consumed"),
    cdpRuntimePath: resolve(runtimeRoot, "cdp.json"),
    helperLogPath: resolve(logsRoot, "helper.log"),
    installManifestPath: resolve(installRoot, "manifest.json"),
    uiPreferencePath: resolve(preferencesRoot, "ui-preferences.json"),
    legacyUiPreferencePath: resolve(stateRoot, "ui-preferences.json"),
  };
}

export function hashGoalProgressIdentity(value: string): string {
  if (!value.trim()) {
    throw new GoalProgressStoreError("STORE_PATH_INVALID", "Identity value must not be blank");
  }
  return createHash("sha256").update(value).digest("hex");
}

export function resolveGoalProgressSessionPaths(
  paths: GoalProgressPaths,
  threadId: string,
): GoalProgressSessionPaths {
  if (!threadId.trim()) {
    throw new GoalProgressStoreError("STORE_PATH_INVALID", "Thread ID must not be blank");
  }
  const sessionKey = hashGoalProgressIdentity(threadId);
  const directory = resolve(paths.stateRoot, sessionKey);
  return {
    sessionKey,
    directory,
    snapshotPath: resolve(directory, "snapshot.json"),
    eventsPath: resolve(directory, "events.jsonl"),
    overlayPath: resolve(directory, "overlay.json"),
  };
}
