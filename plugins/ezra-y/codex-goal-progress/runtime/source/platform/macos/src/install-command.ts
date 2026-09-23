import { randomUUID } from "node:crypto";
import { constants } from "node:fs";
import { access, chmod, cp, lstat, readFile, readlink, rename, rm, stat } from "node:fs/promises";
import { basename, resolve } from "node:path";
import { atomicWriteFile, type GoalProgressPaths } from "../../../packages/store/src/index.js";
import type { CdpController, RestoreCdpResult } from "./cdp-controller.js";
import type {
  MacosCommandInput,
  MacosCommandName,
  MacosCommandResult,
} from "./command-protocol.js";
import { resolveMacosInstallationLayout } from "./install-layout.js";
import { InstallTransaction } from "./install-transaction.js";
import { inspectOrphanReleaseBackups } from "./installation-state.js";
import type { HelperHealthInspection, HelperReadinessInspection } from "./installed-inspection.js";
import { inspectInstalledHook } from "./installed-inspection.js";
import {
  type LaunchAgentController,
  launchAgentPlist,
  writeIfChanged,
} from "./launch-agent-controller.js";
import { isNotFound, stableErrorCode } from "./macos-errors.js";
import type { PluginController } from "./plugin-controller.js";
import {
  type CodexInstallIdentity,
  copyRelease,
  currentLinkMatches,
  fileSha256,
  type InstalledManifest,
  installedReleaseMatches,
  readInstalledManifest,
  readVerifiedRelease,
  replaceCurrentReleaseLink,
  validateCodexIdentity,
} from "./verified-release.js";

interface FileSnapshot {
  readonly exists: boolean;
  readonly contents: string | null;
  readonly mode: number | null;
}

export type MacosCommandResultFactory = (
  command: MacosCommandName,
  input: {
    readonly ok: boolean;
    readonly code: string;
    readonly changed: boolean;
    readonly nextStep?: string | null;
    readonly details?: Readonly<Record<string, unknown>>;
  },
) => MacosCommandResult;

export interface InstallCommandDependencies {
  readonly homeDirectory: string;
  readonly releaseRoot: string;
  readonly launchAgent: LaunchAgentController;
  readonly cdp: CdpController;
  readonly inspectHelper: (paths: GoalProgressPaths) => Promise<HelperHealthInspection>;
  readonly inspectHelperReadiness: (
    paths: GoalProgressPaths,
    timeoutMs: number,
  ) => Promise<HelperReadinessInspection>;
  readonly waitForHelperReady: (
    inspect: (timeoutMs: number) => Promise<HelperReadinessInspection>,
  ) => Promise<boolean>;
  readonly goalPaths: GoalProgressPaths;
  readonly discoverCodex: () => Promise<CodexInstallIdentity>;
  readonly pluginFor: (codex: CodexInstallIdentity) => Promise<PluginController>;
  readonly restoreCdp: (restartCodex: boolean) => Promise<RestoreCdpResult>;
  readonly now: () => Date;
  readonly commandResult: MacosCommandResultFactory;
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

export { type HelperReadyClock, waitForHelperReady } from "./helper-wait.js";

async function cleanupOrphanReleaseBackups(programReleasesRoot: string): Promise<{
  readonly removed: readonly string[];
  readonly warningCode: string | null;
}> {
  const candidates = await inspectOrphanReleaseBackups(programReleasesRoot).catch(() => []);
  const removed: string[] = [];
  let warningCode: string | null = null;
  for (const name of candidates) {
    const path = resolve(programReleasesRoot, name);
    try {
      const metadata = await lstat(path);
      if (!metadata.isDirectory() || metadata.isSymbolicLink()) {
        continue;
      }
      await rm(path, { recursive: true, force: true });
      removed.push(name);
    } catch (error) {
      if (!isNotFound(error)) {
        warningCode ??= stableErrorCode(error);
      }
    }
  }
  return { removed, warningCode };
}

async function captureFile(path: string): Promise<FileSnapshot> {
  try {
    const [contents, metadata] = await Promise.all([readFile(path, "utf8"), stat(path)]);
    return {
      exists: true,
      contents,
      mode: metadata.mode & 0o777,
    };
  } catch (error) {
    if (isNotFound(error)) {
      return { exists: false, contents: null, mode: null };
    }
    throw error;
  }
}

async function restoreFile(path: string, snapshot: FileSnapshot): Promise<void> {
  if (!snapshot.exists) {
    await rm(path, { force: true });
    return;
  }
  await atomicWriteFile(path, snapshot.contents ?? "");
  await chmod(path, snapshot.mode ?? 0o600);
}

async function captureLink(path: string): Promise<string | null> {
  try {
    return await readlink(path);
  } catch (error) {
    if (isNotFound(error)) {
      return null;
    }
    throw error;
  }
}

async function restoreLink(path: string, target: string | null): Promise<void> {
  if (target === null) {
    await rm(path, { recursive: true, force: true });
    return;
  }
  await replaceCurrentReleaseLink(path, target);
}

export function createInstallCommand(dependencies: InstallCommandDependencies) {
  return async (
    command: "install" | "upgrade",
    input: MacosCommandInput,
  ): Promise<MacosCommandResult> => {
    const release = await readVerifiedRelease(dependencies.releaseRoot);
    const layout = resolveMacosInstallationLayout({
      homeDirectory: dependencies.homeDirectory,
      releaseVersion: release.releaseVersion,
    });
    const cleanupBeforeInstall = await cleanupOrphanReleaseBackups(layout.programReleasesRoot);
    const codex = await dependencies.discoverCodex();
    validateCodexIdentity(codex);
    const plugin = await dependencies.pluginFor(codex);
    const installed = await readInstalledManifest(layout.installManifestPath);
    const installedRelease = installed
      ? await readVerifiedRelease(installed.programReleaseRoot).catch(() => null)
      : null;
    const transaction = new InstallTransaction();
    const alreadyCurrent =
      installed?.releaseVersion === release.releaseVersion &&
      installed.helperSha256 === release.files.helper.sha256 &&
      installed.pluginVersion === release.releaseVersion &&
      /^[0-9a-f]{64}$/u.test(installed.hookSha256) &&
      (await currentLinkMatches(layout)) &&
      (await installedReleaseMatches(layout, release));
    const currentTarget = await captureLink(layout.currentReleasePath);
    const plistSnapshot = await captureFile(layout.launchAgentPath);
    const manifestSnapshot = await captureFile(layout.installManifestPath);
    const helperJobWasLoaded = await dependencies.launchAgent.isLoaded(layout.launchAgentLabel);
    const pluginWasHealthy =
      installed !== null &&
      installedRelease !== null &&
      (await plugin
        .verify(installed.releaseVersion, installedRelease.pluginTreeManifestSha256)
        .catch(() => false));
    const pluginNeedsReinstall =
      !pluginWasHealthy ||
      installedRelease?.pluginTreeManifestSha256 !== release.pluginTreeManifestSha256;
    const releaseBackupPath = `${layout.programReleaseRoot}.rollback-${randomUUID()}`;
    let releaseBackupCreated = false;
    try {
      const cdpInitiallyReady = await dependencies.cdp.verify();
      const cdpChanged = await transaction.step(
        "ensure-cdp",
        async () => {
          if (cdpInitiallyReady || !input.restartCodex) {
            return { changed: false, value: false };
          }
          const changed = await dependencies.cdp.ensure(true);
          await dependencies.installFaultForTest?.("after-cdp");
          return { changed, value: changed };
        },
        async () => {
          if (dependencies.cdp.rollback) {
            await dependencies.cdp.rollback();
            return;
          }
          const restored = await dependencies.restoreCdp(true);
          if (restored.scheduled) {
            throw new Error("GOAL_PROGRESS_CDP_ROLLBACK_PENDING");
          }
        },
      );
      const cdpReady = await dependencies.cdp.verify();
      if (!cdpReady) {
        transaction.commit();
        return dependencies.commandResult(command, {
          ok: true,
          code: input.restartCodex ? "INSTALL_RESTART_PENDING" : "INSTALL_RESTART_REQUIRED",
          changed: cdpChanged,
          nextStep: input.restartCodex
            ? "After Codex reopens, run install --json again."
            : `After the user confirms a Codex restart, run ${command} --json --restart-codex.`,
          details: {
            releaseVersion: release.releaseVersion,
            cdpReady: false,
            restartScheduled: cdpChanged,
            states: ["pending_restart"],
            partialState: transaction.partialState,
          },
        });
      }

      await transaction.step(
        "copy-release",
        async () => {
          if (alreadyCurrent) {
            return { changed: false, value: undefined };
          }
          try {
            await lstat(layout.programReleaseRoot);
            await rm(releaseBackupPath, { recursive: true, force: true });
            await rename(layout.programReleaseRoot, releaseBackupPath);
            releaseBackupCreated = true;
          } catch (error) {
            if (!isNotFound(error)) {
              throw error;
            }
          }
          await copyRelease(dependencies.releaseRoot, layout, release);
          if (!pluginNeedsReinstall && releaseBackupCreated) {
            await cp(
              resolve(releaseBackupPath, "plugin-marketplace"),
              resolve(layout.programReleaseRoot, "plugin-marketplace"),
              {
                recursive: true,
                force: true,
                preserveTimestamps: true,
              },
            );
          }
          await readVerifiedRelease(layout.programReleaseRoot);
          const helperPath = resolve(layout.programReleaseRoot, release.files.helper.path);
          if (((await stat(helperPath)).mode & 0o777) !== 0o700) {
            throw new Error("GOAL_PROGRESS_HELPER_PERMISSION_INVALID");
          }
          await access(helperPath, constants.X_OK);
          await dependencies.installFaultForTest?.("after-copy-release");
          return { changed: true, value: undefined };
        },
        async () => {
          if (alreadyCurrent) {
            return;
          }
          await rm(layout.programReleaseRoot, { recursive: true, force: true });
          if (releaseBackupCreated) {
            await rename(releaseBackupPath, layout.programReleaseRoot);
            releaseBackupCreated = false;
          }
        },
      );

      const plistChanged = await transaction.step(
        "write-launchd-plist",
        async () => {
          const changed = await writeIfChanged(
            layout.launchAgentPath,
            launchAgentPlist(layout, codex),
          );
          await dependencies.installFaultForTest?.("after-plist");
          return { changed, value: changed };
        },
        async () => restoreFile(layout.launchAgentPath, plistSnapshot),
      );

      await transaction.step(
        "install-plugin",
        async () => {
          const changed = await plugin.ensure(
            resolve(layout.programReleaseRoot, release.files.pluginArchive.path),
            resolve(layout.programReleaseRoot, "plugin-marketplace"),
            pluginNeedsReinstall,
            release.pluginTreeManifestSha256,
          );
          await dependencies.installFaultForTest?.("after-plugin");
          return { changed, value: undefined };
        },
        async () => {
          if (!pluginWasHealthy || !installed || !installedRelease) {
            await plugin.remove();
            return;
          }
          const oldReleaseRoot =
            installed.programReleaseRoot === layout.programReleaseRoot && releaseBackupCreated
              ? releaseBackupPath
              : installed.programReleaseRoot;
          await plugin.ensure(
            resolve(oldReleaseRoot, "plugin-marketplace.zip"),
            resolve(
              installed.programReleaseRoot === layout.programReleaseRoot
                ? layout.programReleaseRoot
                : installed.programReleaseRoot,
              "plugin-marketplace",
            ),
            true,
            installedRelease.pluginTreeManifestSha256,
          );
        },
      );

      await transaction.step(
        "switch-current",
        async () => {
          if (alreadyCurrent) {
            return { changed: false, value: undefined };
          }
          await replaceCurrentReleaseLink(layout.currentReleasePath, layout.programReleaseRoot);
          await dependencies.installFaultForTest?.("after-current");
          return { changed: true, value: undefined };
        },
        async () => restoreLink(layout.currentReleasePath, currentTarget),
      );

      await transaction.step(
        "start-helper",
        async () => {
          const changed = await dependencies.launchAgent.ensure(
            layout.launchAgentLabel,
            layout.launchAgentPath,
            !alreadyCurrent || plistChanged,
          );
          await dependencies.installFaultForTest?.("after-helper");
          return { changed, value: undefined };
        },
        async () => {
          await restoreFile(layout.launchAgentPath, plistSnapshot);
          if (helperJobWasLoaded) {
            await dependencies.launchAgent.ensure(
              layout.launchAgentLabel,
              layout.launchAgentPath,
              true,
            );
          } else {
            await dependencies.launchAgent.remove(layout.launchAgentLabel, layout.launchAgentPath);
          }
        },
      );

      const hookSha256 = await fileSha256(
        resolve(
          layout.programReleaseRoot,
          "plugin-marketplace/plugins/codex-goal-progress/hooks/hooks.json",
        ),
      );
      const installManifest: InstalledManifest = {
        schemaVersion: 1,
        releaseVersion: release.releaseVersion,
        installedAt:
          alreadyCurrent && installed ? installed.installedAt : dependencies.now().toISOString(),
        helperSha256: release.files.helper.sha256,
        pluginVersion: release.releaseVersion,
        hookSha256,
        programReleaseRoot: layout.programReleaseRoot,
        currentReleasePath: layout.currentReleasePath,
        launchAgentLabel: layout.launchAgentLabel,
        launchAgentPath: layout.launchAgentPath,
        codex,
      };

      await transaction.step(
        "doctor",
        async () => {
          const helperReady = await dependencies.waitForHelperReady((timeoutMs) =>
            dependencies.inspectHelperReadiness(dependencies.goalPaths, timeoutMs),
          );
          const helper = helperReady
            ? await dependencies.inspectHelper(dependencies.goalPaths)
            : null;
          const [jobLoaded, pluginInstalled, hook, cdpReadyNow] = await Promise.all([
            dependencies.launchAgent.isLoaded(layout.launchAgentLabel),
            plugin.verify(release.releaseVersion, release.pluginTreeManifestSha256),
            inspectInstalledHook(dependencies.homeDirectory, installManifest),
            dependencies.cdp.verify(),
          ]);
          if (
            !jobLoaded ||
            !helper?.ok ||
            !helper.startupListenerRunning ||
            !helper.startupListenerReady ||
            !pluginInstalled ||
            !hook.hashMatchesManifest ||
            !hook.stableCommand ||
            !hook.userLevelHookAbsent ||
            !hook.embeddedTrustStateAbsent ||
            !cdpReadyNow
          ) {
            throw new Error("GOAL_PROGRESS_INSTALL_DOCTOR_FAILED");
          }
          return { changed: false, value: undefined };
        },
        async () => undefined,
      );

      await transaction.step(
        "verify",
        async () => {
          await readVerifiedRelease(layout.programReleaseRoot);
          if (
            ((await stat(layout.launchAgentPath)).mode & 0o777) !== 0o600 ||
            ((await stat(resolve(layout.programReleaseRoot, release.files.helper.path))).mode &
              0o777) !==
              0o700 ||
            ((await stat(resolve(layout.programReleaseRoot, release.files.startupListener.path)))
              .mode &
              0o777) !==
              0o700
          ) {
            throw new Error("GOAL_PROGRESS_INSTALL_VERIFY_FAILED");
          }
          return { changed: false, value: undefined };
        },
        async () => undefined,
      );

      await transaction.step(
        "write-manifest",
        async () => {
          const changed = await writeIfChanged(
            layout.installManifestPath,
            `${JSON.stringify(installManifest, null, 2)}\n`,
          );
          await dependencies.installFaultForTest?.("after-manifest");
          return { changed, value: undefined };
        },
        async () => restoreFile(layout.installManifestPath, manifestSnapshot),
      );
      transaction.commit();
      let cleanupWarningCode = cleanupBeforeInstall.warningCode;
      if (releaseBackupCreated) {
        try {
          await dependencies.installFaultForTest?.("before-backup-cleanup");
          await rm(releaseBackupPath, { recursive: true, force: true });
          releaseBackupCreated = false;
        } catch (error) {
          cleanupWarningCode ??= stableErrorCode(error);
        }
      }
      const cleanupBackups = await inspectOrphanReleaseBackups(layout.programReleasesRoot).catch(
        () => (releaseBackupCreated ? [basename(releaseBackupPath)] : []),
      );
      const cleanupPending = cleanupBackups.length > 0;
      const changed =
        transaction.partialState.changedSteps.length > 0 || cleanupBeforeInstall.removed.length > 0;
      const codexSessionReconnectRequired =
        changed &&
        transaction.partialState.changedSteps.some(
          (step) => step === "copy-release" || step === "install-plugin",
        );
      return dependencies.commandResult(command, {
        ok: true,
        code:
          command === "install"
            ? changed
              ? "INSTALL_OK"
              : "INSTALL_ALREADY_CURRENT"
            : changed
              ? "UPGRADE_OK"
              : "UPGRADE_ALREADY_CURRENT",
        changed,
        nextStep: codexSessionReconnectRequired
          ? "Close and reopen the current Codex session so MCP loads this release."
          : null,
        details: {
          releaseVersion: release.releaseVersion,
          applicationSupportRoot: layout.applicationSupportRoot,
          launchAgentLabel: layout.launchAgentLabel,
          codexAppPath: codex.realAppPath,
          pluginInstalled: true,
          codexSessionReconnectRequired,
          hookSha256,
          cdpReady: true,
          restartScheduled: false,
          cleanupPending,
          cleanupBackups,
          cleanupWarningCode,
          states: changed
            ? [
                "installed",
                ...(codexSessionReconnectRequired ? ["session_reconnect_required"] : []),
              ]
            : ["already_current"],
          transaction: transaction.partialState,
        },
      });
    } catch (error) {
      const partialState = transaction.partialState;
      const rollback = await transaction.rollback();
      const rollbackOk = rollback.every((result) => result.ok);
      return dependencies.commandResult(command, {
        ok: false,
        code: rollbackOk ? "INSTALL_ROLLED_BACK" : "INSTALL_PARTIAL_STATE",
        changed: !rollbackOk,
        nextStep: rollbackOk
          ? `Fix ${stableErrorCode(error)}, then retry ${command} --json.`
          : `Run goal-progress restore --json --restart-codex, then inspect ${layout.installRoot}.`,
        details: {
          errorCode: stableErrorCode(error),
          partialState,
          rollback,
          previousRelease: currentTarget,
          preservedRelease: releaseBackupCreated ? releaseBackupPath : null,
          states: [rollbackOk ? "partial_failure_rolled_back" : "partial_failure"],
        },
      });
    }
  };
}
