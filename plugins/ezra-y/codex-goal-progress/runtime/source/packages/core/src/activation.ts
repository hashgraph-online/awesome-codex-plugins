export type GoalProgressActivationContractState = "none" | "matched" | "changed";

export interface GoalProgressActivationInput {
  readonly nativeGoalPresent: boolean;
  readonly contractState: GoalProgressActivationContractState;
}

export type GoalProgressActivationPlan =
  | {
      readonly progressAction: "none";
      readonly preparing: false;
      readonly code: "NATIVE_GOAL_REQUIRED";
    }
  | {
      readonly progressAction: "initialize";
      readonly preparing: true;
      readonly code: "ACTIVATION_INITIALIZE";
    }
  | {
      readonly progressAction: "get";
      readonly preparing: false;
      readonly code: "ACTIVATION_GET";
    }
  | {
      readonly progressAction: "rescope-or-replace";
      readonly preparing: true;
      readonly code: "NATIVE_GOAL_UPDATED";
    };

export function planGoalProgressActivation(
  input: GoalProgressActivationInput,
): GoalProgressActivationPlan {
  if (!input.nativeGoalPresent) {
    return {
      progressAction: "none",
      preparing: false,
      code: "NATIVE_GOAL_REQUIRED",
    };
  }
  if (input.contractState === "none") {
    return {
      progressAction: "initialize",
      preparing: true,
      code: "ACTIVATION_INITIALIZE",
    };
  }
  if (input.contractState === "matched") {
    return {
      progressAction: "get",
      preparing: false,
      code: "ACTIVATION_GET",
    };
  }
  return {
    progressAction: "rescope-or-replace",
    preparing: true,
    code: "NATIVE_GOAL_UPDATED",
  };
}
