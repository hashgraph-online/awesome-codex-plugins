import type { MacosCommandResult } from "./command-protocol.js";
import type { MacosCommandResultFactory } from "./install-command.js";
import type { InstallationState } from "./installation-state.js";
import { inspectOperationalHealth } from "./operational-health.js";

export interface DoctorCommandDependencies {
  readonly state: () => InstallationState;
  readonly commandResult: MacosCommandResultFactory;
}

export function createDoctorCommand(dependencies: DoctorCommandDependencies) {
  return async (): Promise<MacosCommandResult> => {
    const state = dependencies.state();
    const health = await inspectOperationalHealth(state);
    if (!health.ok) {
      const { facts, failure } = health;
      if (failure === "not-installed") {
        return dependencies.commandResult("doctor", {
          ok: false,
          code: "DOCTOR_NOT_INSTALLED",
          changed: false,
          nextStep: "Run install --json.",
        });
      }
      if (failure === "helper-job-not-loaded") {
        return dependencies.commandResult("doctor", {
          ok: false,
          code: "DOCTOR_HELPER_JOB_NOT_LOADED",
          changed: false,
          nextStep: "Run install --json to load the Helper job.",
          details: { helperJobLoaded: false },
        });
      }
      if (failure === "helper-unhealthy") {
        const helper = facts.helper;
        if (!helper) {
          throw new Error("GOAL_PROGRESS_HELPER_INSPECTION_MISSING");
        }
        const code = !helper.socketPathExists
          ? "DOCTOR_HELPER_SOCKET_MISSING"
          : !helper.protocolMatches && helper.code === "PROTOCOL_VERSION_MISMATCH"
            ? "DOCTOR_HELPER_PROTOCOL_MISMATCH"
            : !helper.pingOk
              ? "DOCTOR_HELPER_UNAVAILABLE"
              : !helper.pidMatches
                ? "DOCTOR_HELPER_PID_MISMATCH"
                : !helper.singleOwner
                  ? "DOCTOR_HELPER_OWNER_INVALID"
                  : !helper.storeReadOnly
                    ? "DOCTOR_STORE_READ_FAILED"
                    : "DOCTOR_HELPER_UNAVAILABLE";
        return dependencies.commandResult("doctor", {
          ok: false,
          code,
          changed: false,
          nextStep: "Run install --json to repair and restart the Helper.",
          details: {
            helperJobLoaded: facts.helperJobLoaded,
            helper,
          },
        });
      }
      if (failure === "startup-listener-missing") {
        return dependencies.commandResult("doctor", {
          ok: false,
          code: "DOCTOR_STARTUP_LISTENER_MISSING",
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
        return dependencies.commandResult("doctor", {
          ok: false,
          code:
            failure === "startup-listener-not-running"
              ? "DOCTOR_STARTUP_LISTENER_NOT_RUNNING"
              : "DOCTOR_STARTUP_LISTENER_NOT_READY",
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
        return dependencies.commandResult("doctor", {
          ok: false,
          code: "DOCTOR_PLUGIN_INVALID",
          changed: false,
          nextStep: "Run install --json to restore the Plugin.",
          details: {
            helperJobLoaded: facts.helperJobLoaded,
            helper: facts.helper,
            pluginInstalled: false,
            pluginCacheMatchesSource: false,
          },
        });
      }
      if (failure === "hook-invalid") {
        return dependencies.commandResult("doctor", {
          ok: false,
          code: "DOCTOR_HOOK_INVALID",
          changed: false,
          nextStep: "Run install --json to restore the Hook.",
          details: {
            helperJobLoaded: facts.helperJobLoaded,
            helper: facts.helper,
            pluginInstalled: true,
            pluginCacheMatchesSource: true,
          },
        });
      }
      if (
        failure === "hook-hash-mismatch" ||
        failure === "hook-command-unsafe" ||
        failure === "user-hook-present" ||
        failure === "hook-config-unsafe"
      ) {
        const codes = {
          "hook-hash-mismatch": "DOCTOR_HOOK_HASH_MISMATCH",
          "hook-command-unsafe": "DOCTOR_HOOK_COMMAND_UNSAFE",
          "user-hook-present": "DOCTOR_USER_HOOK_PRESENT",
          "hook-config-unsafe": "DOCTOR_HOOK_CONFIG_UNSAFE",
        } as const;
        return dependencies.commandResult("doctor", {
          ok: false,
          code: codes[failure],
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
      return dependencies.commandResult("doctor", {
        ok: false,
        code: "DOCTOR_CDP_NOT_READY",
        changed: false,
        nextStep: "After the user confirms a Codex restart, run install --json --restart-codex.",
        details: {
          helperJobLoaded: facts.helperJobLoaded,
          helper: facts.helper,
          pluginInstalled: true,
          pluginCacheMatchesSource: true,
          hook: facts.hook,
          cdpReady: false,
        },
      });
    }

    const { facts } = health;
    const cleanupBackups = await state.cleanupBackups().catch(() => []);
    return dependencies.commandResult("doctor", {
      ok: true,
      code: "DOCTOR_OK",
      changed: false,
      details: {
        releaseVersion: facts.installed.releaseVersion,
        helperJobLoaded: facts.helperJobLoaded,
        helper: facts.helper,
        startupListenerFileExists: true,
        startupListenerRunning: facts.helper.startupListenerRunning,
        startupListenerReady: facts.helper.startupListenerReady,
        startupListenerPid: facts.helper.startupListenerPid,
        codexAppPath: facts.codex.realAppPath,
        pluginInstalled: facts.pluginInstalled,
        pluginCacheMatchesSource: true,
        hook: facts.hook,
        hookSha256: facts.installed.hookSha256,
        cdpReady: facts.cdpReady,
        cleanupPending: cleanupBackups.length > 0,
        cleanupBackups,
      },
    });
  };
}
