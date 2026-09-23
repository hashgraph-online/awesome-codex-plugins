import { resolve } from "node:path";
import {
  type GoalProgressPaths,
  resolveGoalProgressPaths,
} from "../../../packages/store/src/index.js";
import { requireSingleCodexMacosApp } from "./app-discovery.js";
import {
  type CdpController,
  createCdpController,
  createDefaultRestoreCdp,
  type RestoreCdpResult,
} from "./cdp-controller.js";
import type {
  MacosCommandHandlers,
  MacosCommandInput,
  MacosCommandName,
  MacosCommandResult,
} from "./command-protocol.js";
import { createHealthCommands } from "./health-commands.js";
import { waitForHelperReady } from "./helper-wait.js";
import { createInstallCommand, type MacosCommandResultFactory } from "./install-command.js";
import { InstallationState } from "./installation-state.js";
import {
  type HelperHealthInspection,
  type HelperReadinessInspection,
  inspectInstalledHelper,
  inspectInstalledHelperReadiness,
} from "./installed-inspection.js";
import {
  createLaunchAgentController,
  type LaunchAgentController,
} from "./launch-agent-controller.js";
import { createMaintenanceCommands } from "./maintenance-commands.js";
import {
  createPluginController,
  type PluginController,
  resolveVerifiedCodexCli,
} from "./plugin-controller.js";
import type { CodexInstallIdentity } from "./verified-release.js";

export {
  type CdpController,
  createCdpController,
  createCodexCdpHandoffInvocation,
  createCodexNormalRelaunchInvocation,
  createCodexRestoreHandoffInvocation,
  decideCodexCdpRestart,
  GOAL_PROGRESS_CDP_HANDOFF_COMMAND,
  GOAL_PROGRESS_CDP_HANDOFF_LABEL,
  GOAL_PROGRESS_CDP_SCHEDULE_COMMAND,
  GOAL_PROGRESS_RESTORE_HANDOFF_COMMAND,
  GOAL_PROGRESS_RESTORE_HANDOFF_LABEL,
  type RestoreCdpResult,
  recordCdpHandoffFailure,
  runCdpRestartWithFallback,
  runCodexCdpHandoff,
  runCodexRestoreHandoff,
  scheduleCodexCdpHandoff,
} from "./cdp-controller.js";
export {
  type HelperHealthInspection,
  inspectInstalledHelper,
} from "./installed-inspection.js";
export {
  createLaunchAgentController,
  type LaunchAgentController,
  restartLoadedLaunchAgent,
} from "./launch-agent-controller.js";
export {
  createPluginController,
  type PluginController,
  resolveVerifiedCodexCli,
} from "./plugin-controller.js";

export interface CreateMacosCommandHandlersOptions {
  readonly homeDirectory: string;
  readonly releaseRoot: string;
  readonly launchAgent?: LaunchAgentController;
  readonly plugin?: PluginController;
  readonly cdp?: CdpController;
  readonly inspectHelper?: (paths: GoalProgressPaths) => Promise<HelperHealthInspection>;
  readonly inspectHelperReadiness?: (
    paths: GoalProgressPaths,
    timeoutMs: number,
  ) => Promise<HelperReadinessInspection>;
  readonly waitForHelperReadyForTest?: (
    inspect: (timeoutMs: number) => Promise<HelperReadinessInspection>,
  ) => Promise<boolean>;
  readonly codexHomeDirectory?: string;
  readonly discoverCodex?: () => Promise<CodexInstallIdentity>;
  readonly restoreCdp?: (restartCodex: boolean) => Promise<RestoreCdpResult>;
  readonly now?: () => Date;
  readonly installFaultForTest?: (
    point:
      | "after-cdp"
      | "after-copy-release"
      | "after-plist"
      | "after-plugin"
      | "after-current"
      | "after-helper"
      | "after-manifest"
      | "before-backup-cleanup",
  ) => void | Promise<void>;
}

const commandResult: MacosCommandResultFactory = (
  command: MacosCommandName,
  input: {
    readonly ok: boolean;
    readonly code: string;
    readonly changed: boolean;
    readonly nextStep?: string | null;
    readonly details?: Readonly<Record<string, unknown>>;
  },
): MacosCommandResult => ({
  schemaVersion: 1,
  command,
  ok: input.ok,
  code: input.code,
  changed: input.changed,
  nextStep: input.nextStep ?? null,
  details: input.details ?? {},
});

export function createMacosCommandHandlers(
  options: CreateMacosCommandHandlersOptions,
): MacosCommandHandlers {
  const launchAgent = options.launchAgent ?? createLaunchAgentController();
  const pluginFor = async (codex: CodexInstallIdentity): Promise<PluginController> =>
    options.plugin ??
    createPluginController({
      codexHomeDirectory: options.codexHomeDirectory ?? resolve(options.homeDirectory, ".codex"),
      codexCommand: await resolveVerifiedCodexCli(codex),
    });
  const cdp = options.cdp ?? createCdpController(options.homeDirectory);
  const inspectHelper = options.inspectHelper ?? inspectInstalledHelper;
  const inspectHelperReadiness =
    options.inspectHelperReadiness ??
    (options.inspectHelper
      ? async (): Promise<HelperReadinessInspection> => ({
          pingOk: true,
          ready: true,
          code: null,
        })
      : inspectInstalledHelperReadiness);
  const goalPaths = resolveGoalProgressPaths({
    platform: "darwin",
    homeDirectory: options.homeDirectory,
  });
  const discoverCodex =
    options.discoverCodex ??
    (async () => {
      const app = await requireSingleCodexMacosApp();
      return {
        realAppPath: app.realAppPath,
        bundleId: app.bundleId,
        teamId: app.teamId,
      };
    });
  const restoreCdp = options.restoreCdp ?? createDefaultRestoreCdp(options.homeDirectory);
  const shared = {
    homeDirectory: options.homeDirectory,
    releaseRoot: options.releaseRoot,
    launchAgent,
    cdp,
    inspectHelper,
    inspectHelperReadiness,
    goalPaths,
    discoverCodex,
    pluginFor,
  };
  const installOrUpgrade = createInstallCommand({
    ...shared,
    restoreCdp,
    now: options.now ?? (() => new Date()),
    commandResult,
    waitForHelperReady: options.waitForHelperReadyForTest ?? waitForHelperReady,
    ...(options.installFaultForTest === undefined
      ? {}
      : { installFaultForTest: options.installFaultForTest }),
  });
  const state = () => new InstallationState(shared);
  const health = createHealthCommands({
    state,
    launchAgent,
    cdp,
    commandResult,
    installOrUpgrade,
  });
  const maintenance = createMaintenanceCommands({
    homeDirectory: options.homeDirectory,
    releaseRoot: options.releaseRoot,
    launchAgent,
    discoverCodex,
    pluginFor,
    restoreCdp,
    commandResult,
  });

  return {
    install: (input: MacosCommandInput) => installOrUpgrade("install", input),
    doctor: health.doctor,
    "emergency-disable": maintenance.emergencyDisable,
    repair: health.repair,
    verify: health.verify,
    restore: maintenance.restore,
    uninstall: maintenance.uninstall,
    upgrade: (input: MacosCommandInput) => installOrUpgrade("upgrade", input),
  };
}
