import { isAbsolute, resolve } from "node:path";
import {
  ensurePrivateDirectory,
  resolveGoalProgressPaths,
} from "../../../packages/store/src/index.js";

export const GOAL_PROGRESS_LAUNCH_AGENT_LABEL = "com.codexgoalprogress.helper" as const;
export const MACOS_PRIVATE_DIRECTORY_MODE = 0o700 as const;
export const MACOS_PRIVATE_FILE_MODE = 0o600 as const;

export interface ResolveMacosInstallationLayoutInput {
  readonly homeDirectory: string;
  readonly releaseVersion: string;
}

export interface MacosInstallationLayout {
  readonly applicationSupportRoot: string;
  readonly installRoot: string;
  readonly programReleasesRoot: string;
  readonly programReleaseRoot: string;
  readonly currentReleasePath: string;
  readonly installManifestPath: string;
  readonly stateRoot: string;
  readonly logsRoot: string;
  readonly preferencesRoot: string;
  readonly runtimeRoot: string;
  readonly launchAgentLabel: typeof GOAL_PROGRESS_LAUNCH_AGENT_LABEL;
  readonly launchAgentPath: string;
}

export function resolveMacosInstallationLayout(
  input: ResolveMacosInstallationLayoutInput,
): MacosInstallationLayout {
  if (!isAbsolute(input.homeDirectory)) {
    throw new Error("GOAL_PROGRESS_HOME_DIRECTORY_INVALID");
  }
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$/u.test(input.releaseVersion)) {
    throw new Error("GOAL_PROGRESS_RELEASE_VERSION_INVALID");
  }
  const paths = resolveGoalProgressPaths({
    platform: "darwin",
    homeDirectory: input.homeDirectory,
  });
  return {
    applicationSupportRoot: paths.root,
    installRoot: paths.installRoot,
    programReleasesRoot: paths.programReleasesRoot,
    programReleaseRoot: resolve(paths.programReleasesRoot, input.releaseVersion),
    currentReleasePath: resolve(paths.installRoot, "current"),
    installManifestPath: paths.installManifestPath,
    stateRoot: paths.stateRoot,
    logsRoot: paths.logsRoot,
    preferencesRoot: paths.preferencesRoot,
    runtimeRoot: paths.runtimeRoot,
    launchAgentLabel: GOAL_PROGRESS_LAUNCH_AGENT_LABEL,
    launchAgentPath: resolve(
      input.homeDirectory,
      "Library",
      "LaunchAgents",
      `${GOAL_PROGRESS_LAUNCH_AGENT_LABEL}.plist`,
    ),
  };
}

export async function ensureMacosInstallationDirectories(
  layout: MacosInstallationLayout,
): Promise<void> {
  for (const directory of [
    layout.applicationSupportRoot,
    layout.installRoot,
    layout.programReleasesRoot,
    layout.programReleaseRoot,
    layout.stateRoot,
    layout.logsRoot,
    layout.preferencesRoot,
    layout.runtimeRoot,
  ]) {
    await ensurePrivateDirectory(directory);
  }
}
