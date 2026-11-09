import type { MacosCommandResult } from "./command-protocol.js";
import type { MacosCommandResultFactory } from "./install-command.js";
import type { InstallationState } from "./installation-state.js";
import {
  type HelperHealthInspection,
  inspectDisplayVerification,
  inspectHelperDiagnosticFailure,
} from "./installed-inspection.js";
import { inspectOperationalHealth, type OperationalHealthFailure } from "./operational-health.js";

export interface DoctorCommandDependencies {
  readonly state: () => InstallationState;
  readonly commandResult: MacosCommandResultFactory;
}

const doctorHookCodes = {
  "hook-invalid": "DOCTOR_HOOK_INVALID",
  "hook-hash-mismatch": "DOCTOR_HOOK_HASH_MISMATCH",
  "hook-command-unsafe": "DOCTOR_HOOK_COMMAND_UNSAFE",
  "user-hook-present": "DOCTOR_USER_HOOK_PRESENT",
  "hook-config-unsafe": "DOCTOR_HOOK_CONFIG_UNSAFE",
} as const;

function doctorHelperCode(helper: HelperHealthInspection): string {
  const diagnosticFailure = inspectHelperDiagnosticFailure(helper);
  if (!helper.socketPathExists) return "DOCTOR_HELPER_SOCKET_MISSING";
  if (!helper.protocolMatches && helper.code === "PROTOCOL_VERSION_MISMATCH") {
    return "DOCTOR_HELPER_PROTOCOL_MISMATCH";
  }
  if (!helper.pingOk) return "DOCTOR_HELPER_UNAVAILABLE";
  if (!helper.pidMatches) return "DOCTOR_HELPER_PID_MISMATCH";
  if (!helper.singleOwner) return "DOCTOR_HELPER_OWNER_INVALID";
  if (diagnosticFailure) {
    return diagnosticFailure === "timeout"
      ? "DOCTOR_DIAGNOSTIC_TIMEOUT"
      : "DOCTOR_DIAGNOSTIC_FAILED";
  }
  return !helper.storeReadOnly ? "DOCTOR_STORE_READ_FAILED" : "DOCTOR_HELPER_UNAVAILABLE";
}

function createHealthInspectionCommand(
  command: "doctor" | "verify",
  dependencies: DoctorCommandDependencies,
) {
  const prefix = command === "doctor" ? "DOCTOR" : "VERIFY";
  return async (): Promise<MacosCommandResult> => {
    const state = dependencies.state();
    const health = await inspectOperationalHealth(state);
    if (!health.ok) {
      const { facts, failure } = health;
      if (failure === "not-installed") {
        return dependencies.commandResult(command, {
          ok: false,
          code: `${prefix}_NOT_INSTALLED`,
          changed: false,
          nextStep: "Run install --json.",
        });
      }
      if (command === "doctor" && failure === "helper-job-not-loaded") {
        return dependencies.commandResult(command, {
          ok: false,
          code: "DOCTOR_HELPER_JOB_NOT_LOADED",
          changed: false,
          nextStep: "Run install --json to load the Helper job.",
          details: { helperJobLoaded: false },
        });
      }
      if (failure === "helper-job-not-loaded" || failure === "helper-unhealthy") {
        const helper = facts.helper ?? null;
        if (command === "doctor") {
          if (!helper) throw new Error("GOAL_PROGRESS_HELPER_INSPECTION_MISSING");
          const code = doctorHelperCode(helper);
          return dependencies.commandResult(command, {
            ok: false,
            code,
            changed: false,
            nextStep: code.startsWith("DOCTOR_DIAGNOSTIC_")
              ? "Retry doctor --json; the diagnostic request did not complete."
              : "Run install --json to repair and restart the Helper.",
            details: { helperJobLoaded: facts.helperJobLoaded, helper },
          });
        }
        const diagnosticFailure = helper ? inspectHelperDiagnosticFailure(helper) : null;
        return dependencies.commandResult(command, {
          ok: false,
          code: diagnosticFailure
            ? diagnosticFailure === "timeout"
              ? "VERIFY_DIAGNOSTIC_TIMEOUT"
              : "VERIFY_DIAGNOSTIC_FAILED"
            : "VERIFY_HELPER_UNAVAILABLE",
          changed: false,
          nextStep: diagnosticFailure
            ? "Retry verify --json; the diagnostic request did not complete."
            : "Run install --json to repair and restart the Helper.",
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
        return dependencies.commandResult(command, {
          ok: false,
          code: `${prefix}_STARTUP_LISTENER_MISSING`,
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
        return dependencies.commandResult(command, {
          ok: false,
          code:
            failure === "startup-listener-not-running"
              ? `${prefix}_STARTUP_LISTENER_NOT_RUNNING`
              : `${prefix}_STARTUP_LISTENER_NOT_READY`,
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
        return dependencies.commandResult(command, {
          ok: false,
          code: `${prefix}_PLUGIN_INVALID`,
          changed: false,
          nextStep:
            command === "doctor"
              ? "Run install --json to restore the Plugin."
              : "Run install --json to restore the Plugin cache.",
          details: {
            helperJobLoaded: facts.helperJobLoaded,
            helper: facts.helper,
            pluginInstalled: false,
            pluginCacheMatchesSource: false,
          },
        });
      }
      if (failure in doctorHookCodes) {
        const hookFailure = failure as keyof typeof doctorHookCodes & OperationalHealthFailure;
        return dependencies.commandResult(command, {
          ok: false,
          code: command === "doctor" ? doctorHookCodes[hookFailure] : "VERIFY_HOOK_INVALID",
          changed: false,
          nextStep: "Run install --json to restore the Hook.",
          details:
            command === "verify" && hookFailure === "hook-invalid"
              ? { helperJobLoaded: facts.helperJobLoaded, helper: facts.helper }
              : {
                  helperJobLoaded: facts.helperJobLoaded,
                  helper: facts.helper,
                  pluginInstalled: true,
                  pluginCacheMatchesSource: true,
                  ...(facts.hook ? { hook: facts.hook } : {}),
                },
        });
      }
      return dependencies.commandResult(command, {
        ok: false,
        code: `${prefix}_CDP_NOT_READY`,
        changed: false,
        nextStep:
          command === "doctor"
            ? "After the user confirms a Codex restart, run install --json --restart-codex."
            : "Restart Codex through install --json --restart-codex.",
        details:
          command === "doctor"
            ? {
                helperJobLoaded: facts.helperJobLoaded,
                helper: facts.helper,
                pluginInstalled: true,
                pluginCacheMatchesSource: true,
                hook: facts.hook,
                cdpReady: false,
              }
            : {
                helperJobLoaded: facts.helperJobLoaded,
                helper: facts.helper,
                cdpOwnership: false,
              },
      });
    }

    const { facts } = health;
    const verification = inspectDisplayVerification(facts.helper);
    if (command === "verify") {
      const permissions = await state.permissionFacts(facts.installed, facts.release);
      if (permissions.configurationPath) {
        throw new Error(
          `GOAL_PROGRESS_INSTALL_PERMISSION_INVALID: ${permissions.configurationPath}`,
        );
      }
      if (permissions.executablePath) {
        throw new Error(
          `GOAL_PROGRESS_EXECUTABLE_PERMISSION_INVALID: ${permissions.executablePath}`,
        );
      }
      return dependencies.commandResult("verify", {
        ok: verification.currentDisplay !== "fail",
        code: verification.currentDisplay === "fail" ? "VERIFY_DISPLAY_MISSING" : "VERIFY_OK",
        changed: false,
        details: {
          verification,
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
    }

    const cleanupBackups = await state.cleanupBackups().catch(() => []);
    return dependencies.commandResult("doctor", {
      ok: verification.currentDisplay !== "fail",
      code: verification.currentDisplay === "fail" ? "DOCTOR_DISPLAY_MISSING" : "DOCTOR_OK",
      changed: false,
      details: {
        verification,
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

export function createDoctorCommand(dependencies: DoctorCommandDependencies) {
  return createHealthInspectionCommand("doctor", dependencies);
}

export function createVerifyCommand(dependencies: DoctorCommandDependencies) {
  return createHealthInspectionCommand("verify", dependencies);
}
