import { readdir, readlink, stat } from "node:fs/promises";
import { resolve } from "node:path";
import type { GoalProgressPaths } from "../../../packages/store/src/index.js";
import type { CdpController } from "./cdp-controller.js";
import { type MacosInstallationLayout, resolveMacosInstallationLayout } from "./install-layout.js";
import {
  type HelperHealthInspection,
  type InstalledHookInspection,
  inspectInstalledHook,
  startupListenerFileExists,
} from "./installed-inspection.js";
import type { LaunchAgentController } from "./launch-agent-controller.js";
import { isNotFound } from "./macos-errors.js";
import type { PluginController } from "./plugin-controller.js";
import {
  type CodexInstallIdentity,
  type InstalledManifest,
  type ParsedReleaseManifest,
  readInstalledManifest,
  readVerifiedRelease,
  validateCodexIdentity,
} from "./verified-release.js";

const releaseBackupNamePattern =
  /^[A-Za-z0-9][A-Za-z0-9._-]{0,99}\.rollback-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/u;

export async function inspectOrphanReleaseBackups(programReleasesRoot: string): Promise<string[]> {
  try {
    const entries = await readdir(programReleasesRoot, { withFileTypes: true });
    return entries
      .filter((entry) => entry.isDirectory() && releaseBackupNamePattern.test(entry.name))
      .map((entry) => entry.name)
      .sort();
  } catch (error) {
    if (isNotFound(error)) {
      return [];
    }
    throw error;
  }
}

export interface InstallationStateOptions {
  readonly homeDirectory: string;
  readonly releaseRoot: string;
  readonly goalPaths: GoalProgressPaths;
  readonly launchAgent: LaunchAgentController;
  readonly cdp: CdpController;
  readonly inspectHelper: (paths: GoalProgressPaths) => Promise<HelperHealthInspection>;
  readonly discoverCodex: () => Promise<CodexInstallIdentity>;
  readonly pluginFor: (codex: CodexInstallIdentity) => Promise<PluginController>;
}

export interface InstallationPermissionFacts {
  readonly configurationPath: string | null;
  readonly executablePath: string | null;
}

export class InstallationState {
  readonly #options: InstallationStateOptions;
  #release: Promise<ParsedReleaseManifest> | undefined;
  #layout: Promise<MacosInstallationLayout> | undefined;
  #installed: Promise<InstalledManifest | null> | undefined;
  #helperJobLoaded: Promise<boolean> | undefined;
  #helper: Promise<HelperHealthInspection> | undefined;
  #codex: Promise<CodexInstallIdentity> | undefined;
  #plugin: Promise<PluginController> | undefined;
  #cdpReady: Promise<boolean> | undefined;

  constructor(options: InstallationStateOptions) {
    this.#options = options;
  }

  release(): Promise<ParsedReleaseManifest> {
    this.#release ??= readVerifiedRelease(this.#options.releaseRoot);
    return this.#release;
  }

  layout(): Promise<MacosInstallationLayout> {
    this.#layout ??= this.release().then((release) =>
      resolveMacosInstallationLayout({
        homeDirectory: this.#options.homeDirectory,
        releaseVersion: release.releaseVersion,
      }),
    );
    return this.#layout;
  }

  installed(): Promise<InstalledManifest | null> {
    this.#installed ??= this.layout().then((layout) =>
      readInstalledManifest(layout.installManifestPath),
    );
    return this.#installed;
  }

  installedLayout(installed: InstalledManifest): MacosInstallationLayout {
    return resolveMacosInstallationLayout({
      homeDirectory: this.#options.homeDirectory,
      releaseVersion: installed.releaseVersion,
    });
  }

  helperJobLoaded(): Promise<boolean> {
    this.#helperJobLoaded ??= this.layout().then((layout) =>
      this.#options.launchAgent.isLoaded(layout.launchAgentLabel),
    );
    return this.#helperJobLoaded;
  }

  helper(): Promise<HelperHealthInspection> {
    this.#helper ??= this.#options.inspectHelper(this.#options.goalPaths);
    return this.#helper;
  }

  async startupListenerFileExists(): Promise<boolean> {
    return startupListenerFileExists(await this.layout(), await this.release());
  }

  codex(): Promise<CodexInstallIdentity> {
    this.#codex ??= this.#options.discoverCodex().then((codex) => {
      validateCodexIdentity(codex);
      return codex;
    });
    return this.#codex;
  }

  plugin(): Promise<PluginController> {
    this.#plugin ??= this.codex().then((codex) => this.#options.pluginFor(codex));
    return this.#plugin;
  }

  async pluginInstalled(
    installed: InstalledManifest,
    release: ParsedReleaseManifest,
  ): Promise<boolean> {
    return (await this.plugin()).verify(installed.releaseVersion, release.pluginTreeManifestSha256);
  }

  hook(installed: InstalledManifest): Promise<InstalledHookInspection> {
    return inspectInstalledHook(this.#options.homeDirectory, installed);
  }

  cdpReady(): Promise<boolean> {
    this.#cdpReady ??= this.#options.cdp.verify();
    return this.#cdpReady;
  }

  async cleanupBackups(): Promise<string[]> {
    return inspectOrphanReleaseBackups((await this.layout()).programReleasesRoot);
  }

  installedRelease(installed: InstalledManifest): Promise<ParsedReleaseManifest> {
    return readVerifiedRelease(installed.programReleaseRoot);
  }

  async currentReleaseTarget(layout: MacosInstallationLayout): Promise<string | null> {
    try {
      return await readlink(layout.currentReleasePath);
    } catch (error) {
      if (isNotFound(error)) {
        return null;
      }
      throw error;
    }
  }

  async permissionFacts(
    installed: InstalledManifest,
    release: ParsedReleaseManifest,
  ): Promise<InstallationPermissionFacts> {
    const layout = await this.layout();
    for (const path of [
      layout.installManifestPath,
      layout.launchAgentPath,
      resolve(installed.programReleaseRoot, release.files.renderer.path),
    ]) {
      if (((await stat(path)).mode & 0o777) !== 0o600) {
        return { configurationPath: path, executablePath: null };
      }
    }
    for (const executable of [
      release.files.helper,
      release.files.startupListener,
      release.files.installCommand,
      release.files.repairCommand,
      release.files.disableCommand,
      release.files.uninstallCommand,
    ]) {
      if (
        ((await stat(resolve(installed.programReleaseRoot, executable.path))).mode & 0o777) !==
        0o700
      ) {
        return { configurationPath: null, executablePath: executable.path };
      }
    }
    return { configurationPath: null, executablePath: null };
  }
}
