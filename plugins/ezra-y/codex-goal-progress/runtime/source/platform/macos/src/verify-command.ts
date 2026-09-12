import type { MacosCommandResult } from "./command-protocol.js";
import type { MacosCommandResultFactory } from "./install-command.js";
import type { InstallationState } from "./installation-state.js";
import { inspectOperationalHealth } from "./operational-health.js";

export interface VerifyCommandDependencies {
  readonly state: () => InstallationState;
  readonly commandResult: MacosCommandResultFactory;
}

export function createVerifyCommand(dependencies: VerifyCommandDependencies) {
  return async (): Promise<MacosCommandResult> => {
    const state = dependencies.state();
    const health = await inspectOperationalHealth(state);
    if (!health.ok) {
      const { facts, failure } = health;
      if (failure === "not-installed") {
        return dependencies.commandResult("verify", {
          ok: false,
          code: "VERIFY_NOT_INSTALLED",
          changed: false,
          nextStep: "Run install --json.",
        });
      }
      if (failure === "helper-job-not-loaded" || failure === "helper-unhealthy") {
        const helper = facts.helper ?? null;
        return dependencies.commandResult("verify", {
          ok: false,
          code: "VERIFY_HELPER_UNAVAILABLE",
          changed: false,
          nextStep: "Run install --json to repair and restart the Helper.",
          details: {
            helperJobLoaded: facts.helperJobLoaded,
            helper,
            helperPing: helper?.pingOk ?? false,
            ipcRoundTrip: helper?.pingOk === true && helper.protocolMatches,
            storeReadOnly: helper?.storeReadOnly ?? false,
          },
        });
      }
      if (failure === "startup-listener-missing") {
        return dependencies.commandResult("verify", {
          ok: false,
          code: "VERIFY_STARTUP_LISTENER_MISSING",
          changed: false,
          nextStep: "Run install --json to restore the startup listener.",
          details: {
            helperJobLoaded: facts.helperJobLoaded,
            helper: facts.helper,
            startupListenerFileExists: false,
          },
        });
      }
      if (failure === "startup-listener-not-running" || failure === "startup-listener-not-ready") {
        return dependencies.commandResult("verify", {
          ok: false,
          code:
            failure === "startup-listener-not-running"
              ? "VERIFY_STARTUP_LISTENER_NOT_RUNNING"
              : "VERIFY_STARTUP_LISTENER_NOT_READY",
          changed: false,
          nextStep: "Run install --json to restart the Helper and startup listener.",
          details: {
            helperJobLoaded: facts.helperJobLoaded,
            helper: facts.helper,
            startupListenerFileExists: true,
          },
        });
      }
      if (failure === "plugin-invalid") {
        return dependencies.commandResult("verify", {
          ok: false,
          code: "VERIFY_PLUGIN_INVALID",
          changed: false,
          nextStep: "Run install --json to restore the Plugin cache.",
          details: {
            helperJobLoaded: facts.helperJobLoaded,
            helper: facts.helper,
            pluginInstalled: false,
            pluginCacheMatchesSource: false,
          },
        });
      }
      if (failure === "hook-invalid") {
        return dependencies.commandResult("verify", {
          ok: false,
          code: "VERIFY_HOOK_INVALID",
          changed: false,
          nextStep: "Run install --json to restore the Hook.",
          details: {
            helperJobLoaded: facts.helperJobLoaded,
            helper: facts.helper,
          },
        });
      }
      if (
        failure === "hook-hash-mismatch" ||
        failure === "hook-command-unsafe" ||
        failure === "user-hook-present" ||
        failure === "hook-config-unsafe"
      ) {
        return dependencies.commandResult("verify", {
          ok: false,
          code: "VERIFY_HOOK_INVALID",
          changed: false,
          nextStep: "Run install --json to restore the Hook.",
          details: {
            helperJobLoaded: facts.helperJobLoaded,
            helper: facts.helper,
            pluginInstalled: true,
            pluginCacheMatchesSource: true,
            hook: facts.hook,
          },
        });
      }
      return dependencies.commandResult("verify", {
        ok: false,
        code: "VERIFY_CDP_NOT_READY",
        changed: false,
        nextStep: "Restart Codex through install --json --restart-codex.",
        details: {
          helperJobLoaded: facts.helperJobLoaded,
          helper: facts.helper,
          cdpOwnership: false,
        },
      });
    }

    const { facts } = health;
    await state.installedRelease(facts.installed);
    const permissions = await state.permissionFacts(facts.installed, facts.release);
    if (permissions.configurationPath) {
      throw new Error(`GOAL_PROGRESS_INSTALL_PERMISSION_INVALID: ${permissions.configurationPath}`);
    }
    if (permissions.executablePath) {
      throw new Error(`GOAL_PROGRESS_EXECUTABLE_PERMISSION_INVALID: ${permissions.executablePath}`);
    }
    return dependencies.commandResult("verify", {
      ok: true,
      code: "VERIFY_OK",
      changed: false,
      details: {
        releaseVersion: facts.installed.releaseVersion,
        checksumsValid: true,
        permissionsValid: true,
        pluginInstalled: true,
        pluginCacheMatchesSource: true,
        hookSha256: facts.installed.hookSha256,
        helperPing: true,
        ipcRoundTrip: true,
        storeReadOnly: true,
        helperPid: facts.helper.pid,
        helperOwnerCount: facts.helper.ownerCount,
        startupListenerFileExists: true,
        startupListenerRunning: facts.helper.startupListenerRunning,
        startupListenerReady: facts.helper.startupListenerReady,
        startupListenerPid: facts.helper.startupListenerPid,
        cdpOwnership: true,
        cdpReady: true,
      },
    });
  };
}
