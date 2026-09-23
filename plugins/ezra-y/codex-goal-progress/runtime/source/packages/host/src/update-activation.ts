export interface GoalProgressUpdateActivationRendererProof {
  readonly componentVisible: boolean | null;
  readonly componentCount: number | null;
  readonly currentThreadMatched: boolean | null;
  readonly latestViewModelRevision: number | null;
  readonly bundleReleaseVersion: string | null;
}

export interface GoalProgressUpdateActivationProof {
  readonly targetVersion: string;
  readonly previousLaunchId: string | null;
  readonly currentLaunchId: string | null;
  readonly installedVerified: boolean;
  readonly startupHandoffCode: string | null;
  readonly viewModelRevision: number | null;
  readonly taskRecovered: boolean;
  readonly deliveryCurrent: boolean;
  readonly renderer: GoalProgressUpdateActivationRendererProof;
}

export type GoalProgressUpdateActivationResult =
  | {
      readonly complete: true;
      readonly code: "GOAL_PROGRESS_UPDATE_ACTIVATION_COMPLETE";
    }
  | {
      readonly complete: false;
      readonly code: string;
    };

export function evaluateGoalProgressUpdateActivation(
  proof: GoalProgressUpdateActivationProof,
): GoalProgressUpdateActivationResult {
  if (!proof.installedVerified) {
    return { complete: false, code: "GOAL_PROGRESS_UPDATE_INSTALL_VERIFY_FAILED" };
  }
  if (
    proof.previousLaunchId === null ||
    proof.currentLaunchId === null ||
    proof.currentLaunchId === proof.previousLaunchId
  ) {
    return { complete: false, code: "GOAL_PROGRESS_UPDATE_LAUNCH_NOT_REPLACED" };
  }
  if (proof.startupHandoffCode !== "STARTUP_HANDOFF_COMPLETE") {
    return { complete: false, code: "GOAL_PROGRESS_UPDATE_STARTUP_HANDOFF_INCOMPLETE" };
  }
  if (proof.viewModelRevision === null || !proof.taskRecovered || !proof.deliveryCurrent) {
    return { complete: false, code: "GOAL_PROGRESS_UPDATE_TASK_RECOVERY_INCOMPLETE" };
  }
  if (
    proof.renderer.componentVisible !== true ||
    proof.renderer.componentCount !== 1 ||
    proof.renderer.currentThreadMatched !== true ||
    proof.renderer.latestViewModelRevision !== proof.viewModelRevision
  ) {
    return { complete: false, code: "GOAL_PROGRESS_UPDATE_RENDERER_RECOVERY_INCOMPLETE" };
  }
  if (proof.renderer.bundleReleaseVersion !== proof.targetVersion) {
    return { complete: false, code: "GOAL_PROGRESS_UPDATE_RENDERER_VERSION_MISMATCH" };
  }
  return { complete: true, code: "GOAL_PROGRESS_UPDATE_ACTIVATION_COMPLETE" };
}
