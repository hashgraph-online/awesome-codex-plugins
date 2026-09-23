import { resolve } from "node:path";
import type { CdpController } from "./cdp-controller.js";
import type { MacosCommandInput, MacosCommandResult } from "./command-protocol.js";
import type { MacosCommandResultFactory } from "./install-command.js";
import type { InstallationState } from "./installation-state.js";
import {
  type LaunchAgentController,
  launchAgentPlist,
  writeIfChanged,
} from "./launch-agent-controller.js";
import { stableErrorCode } from "./macos-errors.js";
import { replaceCurrentReleaseLink } from "./verified-release.js";

export interface RepairCommandDependencies {
  readonly state: () => InstallationState;
  readonly launchAgent: LaunchAgentController;
  readonly cdp: CdpController;
  readonly commandResult: MacosCommandResultFactory;
  readonly installOrUpgrade: (
    command: "install" | "upgrade",
    input: MacosCommandInput,
  ) => Promise<MacosCommandResult>;
  readonly doctor: () => Promise<MacosCommandResult>;
}

export function createRepairCommand(dependencies: RepairCommandDependencies) {
  return async (input: MacosCommandInput): Promise<MacosCommandResult> => {
    let current = await dependencies.doctor();
    const doctorCodes = [current.code];
    if (current.ok) {
      return dependencies.commandResult("repair", {
        ok: true,
        code: "REPAIR_NOT_NEEDED",
        changed: false,
        details: {
          doctorCodeBefore: current.code,
          doctorCodes,
          contractPreserved: true,
          tokenPreserved: true,
        },
      });
    }
    const state = dependencies.state();
    const installed = await state.installed();
    if (!installed) {
      return dependencies.commandResult("repair", {
        ok: false,
        code: "REPAIR_NOT_INSTALLED",
        changed: false,
        nextStep: "Run install --json.",
      });
    }
    const layout = state.installedLayout(installed);
    const installedRelease = await state.installedRelease(installed);
    const helperCodes = new Set([
      "DOCTOR_HELPER_JOB_NOT_LOADED",
      "DOCTOR_HELPER_SOCKET_MISSING",
      "DOCTOR_HELPER_UNAVAILABLE",
      "DOCTOR_HELPER_PROTOCOL_MISMATCH",
      "DOCTOR_HELPER_PID_MISMATCH",
      "DOCTOR_HELPER_OWNER_INVALID",
      "DOCTOR_STORE_READ_FAILED",
    ]);
    const hookCodes = new Set([
      "DOCTOR_HOOK_HASH_MISMATCH",
      "DOCTOR_HOOK_COMMAND_UNSAFE",
      "DOCTOR_HOOK_CONFIG_UNSAFE",
      "DOCTOR_HOOK_INVALID",
    ]);
    const visited = new Set<string>();
    let changed = false;

    for (let round = 0; round < 5; round += 1) {
      if (visited.has(current.code)) {
        return dependencies.commandResult("repair", {
          ok: false,
          code: "REPAIR_CYCLE_DETECTED",
          changed,
          nextStep: "Run doctor --json and inspect the reported Repair code cycle.",
          details: {
            doctorCodes,
            contractPreserved: true,
            tokenPreserved: true,
          },
        });
      }
      visited.add(current.code);

      let actionChanged = false;
      try {
        if (helperCodes.has(current.code)) {
          const codex = await state.codex();
          if ((await state.currentReleaseTarget(layout)) !== installed.programReleaseRoot) {
            await replaceCurrentReleaseLink(
              layout.currentReleasePath,
              installed.programReleaseRoot,
            );
            actionChanged = true;
          }
          actionChanged =
            (await writeIfChanged(layout.launchAgentPath, launchAgentPlist(layout, codex))) ||
            actionChanged;
          actionChanged =
            (await dependencies.launchAgent.ensure(
              layout.launchAgentLabel,
              layout.launchAgentPath,
              true,
            )) || actionChanged;
        } else if (current.code === "DOCTOR_PLUGIN_INVALID") {
          actionChanged = await (await state.plugin()).ensure(
            resolve(installed.programReleaseRoot, "plugin-marketplace.zip"),
            resolve(installed.programReleaseRoot, "plugin-marketplace"),
            true,
            installedRelease.pluginTreeManifestSha256,
          );
        } else if (hookCodes.has(current.code)) {
          const installedAgain = await dependencies.installOrUpgrade("install", input);
          return dependencies.commandResult("repair", {
            ...installedAgain,
            changed: changed || installedAgain.changed,
            code: installedAgain.ok ? "REPAIR_OK" : installedAgain.code,
            details: {
              ...installedAgain.details,
              doctorCodeBefore: doctorCodes[0],
              doctorCodes,
              contractPreserved: true,
              tokenPreserved: true,
            },
          });
        } else if (current.code === "DOCTOR_CDP_NOT_READY") {
          if (!input.restartCodex) {
            return dependencies.commandResult("repair", {
              ok: true,
              code: "REPAIR_RESTART_REQUIRED",
              changed,
              nextStep:
                "After the user confirms a Codex restart, run repair --json --restart-codex.",
              details: { doctorCodes },
            });
          }
          actionChanged = await dependencies.cdp.ensure(true);
          if (!(await dependencies.cdp.verify())) {
            return dependencies.commandResult("repair", {
              ok: true,
              code: "REPAIR_RESTART_PENDING",
              changed: changed || actionChanged,
              nextStep: "After Codex reopens, run repair --json again.",
              details: { doctorCodes },
            });
          }
        } else {
          return dependencies.commandResult("repair", {
            ok: false,
            code: "REPAIR_MANUAL_ACTION_REQUIRED",
            changed,
            nextStep: current.nextStep,
            details: {
              doctorCodeBefore: doctorCodes[0],
              doctorCodes,
              contractPreserved: true,
              tokenPreserved: true,
            },
          });
        }
      } catch (error) {
        const errorCode = stableErrorCode(error);
        return dependencies.commandResult("repair", {
          ok: false,
          code: "REPAIR_ACTION_FAILED",
          changed,
          nextStep: `Fix ${errorCode}, then retry repair --json.`,
          details: {
            doctorCodes,
            errorCode,
            contractPreserved: true,
            tokenPreserved: true,
          },
        });
      }

      changed = changed || actionChanged;
      if (!actionChanged) {
        return dependencies.commandResult("repair", {
          ok: false,
          code: "REPAIR_INCOMPLETE",
          changed,
          nextStep: current.nextStep,
          details: {
            doctorCodeBefore: doctorCodes[0],
            doctorCodeAfter: current.code,
            doctorCodes,
            contractPreserved: true,
            tokenPreserved: true,
          },
        });
      }

      current = await dependencies.doctor();
      doctorCodes.push(current.code);
      if (current.ok) {
        return dependencies.commandResult("repair", {
          ok: true,
          code: "REPAIR_OK",
          changed,
          details: {
            doctorCodeBefore: doctorCodes[0],
            doctorCodeAfter: current.code,
            doctorCodes,
            contractPreserved: true,
            tokenPreserved: true,
          },
        });
      }
    }

    if (visited.has(current.code)) {
      return dependencies.commandResult("repair", {
        ok: false,
        code: "REPAIR_CYCLE_DETECTED",
        changed,
        nextStep: "Run doctor --json and inspect the reported Repair code cycle.",
        details: {
          doctorCodes,
          contractPreserved: true,
          tokenPreserved: true,
        },
      });
    }
    return dependencies.commandResult("repair", {
      ok: false,
      code: "REPAIR_LIMIT_REACHED",
      changed,
      nextStep: "Run doctor --json; automatic Repair reached its five-round limit.",
      details: {
        doctorCodes,
        contractPreserved: true,
        tokenPreserved: true,
      },
    });
  };
}
