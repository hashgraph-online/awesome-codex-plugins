import type { InstallationState } from "./installation-state.js";
import type { HelperHealthInspection, InstalledHookInspection } from "./installed-inspection.js";
import type {
  CodexInstallIdentity,
  InstalledManifest,
  ParsedReleaseManifest,
} from "./verified-release.js";

export type OperationalHealthFailure =
  | "not-installed"
  | "helper-job-not-loaded"
  | "helper-unhealthy"
  | "startup-listener-missing"
  | "startup-listener-not-running"
  | "startup-listener-not-ready"
  | "plugin-invalid"
  | "hook-invalid"
  | "hook-hash-mismatch"
  | "hook-command-unsafe"
  | "user-hook-present"
  | "hook-config-unsafe"
  | "cdp-not-ready";

export interface OperationalHealthFacts {
  readonly release: ParsedReleaseManifest;
  readonly installed: InstalledManifest | null;
  readonly helperJobLoaded?: boolean;
  readonly helper?: HelperHealthInspection;
  readonly startupListenerFileExists?: boolean;
  readonly codex?: CodexInstallIdentity;
  readonly pluginInstalled?: boolean;
  readonly hook?: InstalledHookInspection;
  readonly cdpReady?: boolean;
}

export interface OperationalHealthSuccessFacts extends OperationalHealthFacts {
  readonly installed: InstalledManifest;
  readonly helperJobLoaded: true;
  readonly helper: HelperHealthInspection;
  readonly startupListenerFileExists: true;
  readonly codex: CodexInstallIdentity;
  readonly pluginInstalled: true;
  readonly hook: InstalledHookInspection;
  readonly cdpReady: true;
}

export type OperationalHealthResult =
  | {
      readonly ok: false;
      readonly failure: OperationalHealthFailure;
      readonly facts: OperationalHealthFacts;
    }
  | {
      readonly ok: true;
      readonly facts: OperationalHealthSuccessFacts;
    };

function failure(
  reason: OperationalHealthFailure,
  facts: OperationalHealthFacts,
): OperationalHealthResult {
  return { ok: false, failure: reason, facts };
}

export async function inspectOperationalHealth(
  state: InstallationState,
): Promise<OperationalHealthResult> {
  const release = await state.release();
  const installed = await state.installed();
  let facts: OperationalHealthFacts = { release, installed };
  if (!installed) {
    return failure("not-installed", facts);
  }

  const helperJobLoaded = await state.helperJobLoaded();
  facts = { ...facts, helperJobLoaded };
  if (!helperJobLoaded) {
    return failure("helper-job-not-loaded", facts);
  }

  const helper = await state.helper();
  facts = { ...facts, helper };
  if (!helper.ok) {
    return failure("helper-unhealthy", facts);
  }

  const startupListenerFileExists = await state.startupListenerFileExists();
  facts = { ...facts, startupListenerFileExists };
  if (!startupListenerFileExists) {
    return failure("startup-listener-missing", facts);
  }
  if (!helper.startupListenerRunning) {
    return failure("startup-listener-not-running", facts);
  }
  if (!helper.startupListenerReady) {
    return failure("startup-listener-not-ready", facts);
  }

  const codex = await state.codex();
  facts = { ...facts, codex };
  const pluginInstalled = await state.pluginInstalled(installed, release);
  facts = { ...facts, pluginInstalled };
  if (!pluginInstalled) {
    return failure("plugin-invalid", facts);
  }

  let hook: InstalledHookInspection;
  try {
    hook = await state.hook(installed);
  } catch {
    return failure("hook-invalid", facts);
  }
  facts = { ...facts, hook };
  if (!hook.hashMatchesManifest) {
    return failure("hook-hash-mismatch", facts);
  }
  if (!hook.stableCommand) {
    return failure("hook-command-unsafe", facts);
  }
  if (!hook.userLevelHookAbsent) {
    return failure("user-hook-present", facts);
  }
  if (!hook.embeddedTrustStateAbsent) {
    return failure("hook-config-unsafe", facts);
  }

  const cdpReady = await state.cdpReady();
  facts = { ...facts, cdpReady };
  if (!cdpReady) {
    return failure("cdp-not-ready", facts);
  }

  return {
    ok: true,
    facts: facts as OperationalHealthSuccessFacts,
  };
}
