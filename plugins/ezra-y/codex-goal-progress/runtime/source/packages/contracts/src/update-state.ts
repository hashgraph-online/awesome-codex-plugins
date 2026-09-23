import { z } from "zod";
import { GoalContractIdSchema } from "./goal-contract.js";
import {
  GOAL_PROGRESS_UPDATE_INTENT_PROTOCOL_VERSION,
  type GOAL_PROGRESS_UPDATE_STATE_SCHEMA_VERSION,
  isGoalProgressUpdateVersion,
  parseGoalProgressUpdateIntent,
  parseGoalProgressUpdateState,
} from "./update-state-runtime.js";

export {
  GOAL_PROGRESS_UPDATE_INTENT_EVENT,
  GOAL_PROGRESS_UPDATE_INTENT_MAX_BYTES,
  GOAL_PROGRESS_UPDATE_INTENT_PROTOCOL_VERSION,
  GOAL_PROGRESS_UPDATE_STATE_SCHEMA_VERSION,
  isGoalProgressUpdateVersion,
} from "./update-state-runtime.js";

export type GoalProgressUpdatePhase =
  | "up-to-date"
  | "checking"
  | "available"
  | "check-failed"
  | "preparing"
  | "downloading"
  | "verifying"
  | "installing"
  | "download-failed"
  | "update-failed"
  | "restart-required"
  | "restarting";

export type GoalProgressUpdateNextStep = "check" | "download" | "retry" | "restart" | null;

export interface GoalProgressUpdateState {
  readonly deliveryMode?: "prebuilt-release" | "plugin-marketplace";
  readonly schemaVersion: typeof GOAL_PROGRESS_UPDATE_STATE_SCHEMA_VERSION;
  readonly stateRevision: number;
  readonly currentVersion: string;
  readonly latestVersion: string | null;
  readonly phase: GoalProgressUpdatePhase;
  readonly checkedAt: string | null;
  readonly lastSeenUpdateVersion: string | null;
  readonly promptDismissedForVersion: string | null;
  readonly downloadedBytes: number;
  readonly totalBytes: number | null;
  readonly downloadPercent: number | null;
  readonly restartRequired: boolean;
  readonly lastErrorCode: string | null;
  readonly nextStep: GoalProgressUpdateNextStep;
  readonly updatedAt: string;
}

export type GoalProgressUpdateIntent =
  | { readonly type: "check" }
  | { readonly type: "start"; readonly version: string }
  | { readonly type: "retry"; readonly version: string }
  | { readonly type: "restart-now"; readonly version: string }
  | { readonly type: "restart-later"; readonly version: string }
  | { readonly type: "open-release"; readonly version: string };

export const StrictSemverSchema = z.custom<string>(isGoalProgressUpdateVersion);

export const GoalProgressUpdatePhaseSchema = z.enum([
  "up-to-date",
  "checking",
  "available",
  "check-failed",
  "preparing",
  "downloading",
  "verifying",
  "installing",
  "download-failed",
  "update-failed",
  "restart-required",
  "restarting",
]);

export const GoalProgressUpdateNextStepSchema = z
  .enum(["check", "download", "retry", "restart"])
  .nullable();

export const GoalProgressUpdateStateSchema = z.custom<GoalProgressUpdateState>(
  (value) => parseGoalProgressUpdateState(value) !== null,
);

export const GOAL_PROGRESS_UPDATE_STATE_REVISION_CONFLICT =
  "GOAL_PROGRESS_UPDATE_STATE_REVISION_CONFLICT";

const updateStateFields: readonly (keyof GoalProgressUpdateState)[] = [
  "deliveryMode",
  "schemaVersion",
  "stateRevision",
  "currentVersion",
  "latestVersion",
  "phase",
  "checkedAt",
  "lastSeenUpdateVersion",
  "promptDismissedForVersion",
  "downloadedBytes",
  "totalBytes",
  "downloadPercent",
  "restartRequired",
  "lastErrorCode",
  "nextStep",
  "updatedAt",
];

export type GoalProgressUpdateStateOrder = "accept" | "ignore" | "noop";

export function classifyGoalProgressUpdateState(
  incomingInput: GoalProgressUpdateState,
  currentInput: GoalProgressUpdateState | null,
): GoalProgressUpdateStateOrder {
  const incoming = GoalProgressUpdateStateSchema.parse(incomingInput);
  if (currentInput === null) {
    return "accept";
  }
  const current = GoalProgressUpdateStateSchema.parse(currentInput);
  if (incoming.stateRevision > current.stateRevision) {
    return "accept";
  }
  if (incoming.stateRevision < current.stateRevision) {
    return "ignore";
  }
  if (updateStateFields.every((field) => Object.is(incoming[field], current[field]))) {
    return "noop";
  }
  throw new Error(GOAL_PROGRESS_UPDATE_STATE_REVISION_CONFLICT);
}

export const GoalProgressUpdateIntentSchema = z.custom<GoalProgressUpdateIntent>(
  (value) => parseGoalProgressUpdateIntent(value) !== null,
);

export const GoalProgressUpdateIntentEnvelopeSchema = z
  .object({
    protocolVersion: z.literal(GOAL_PROGRESS_UPDATE_INTENT_PROTOCOL_VERSION),
    intentKind: z.literal("update"),
    bridgeNonce: z.string().regex(/^[A-Za-z0-9_-]{32}$/u),
    contractId: GoalContractIdSchema,
    threadId: z.string().trim().min(1).max(256),
    userActivated: z.boolean(),
    intent: GoalProgressUpdateIntentSchema,
  })
  .strict();

export type GoalProgressUpdateIntentEnvelope = z.infer<
  typeof GoalProgressUpdateIntentEnvelopeSchema
>;

export const GoalProgressUpdateWorkerResultSchema = z
  .object({
    operationId: z.string().uuid(),
    targetVersion: StrictSemverSchema,
    status: z.enum(["succeeded", "failed"]),
    errorCode: z
      .string()
      .regex(/^[A-Z][A-Z0-9_]{2,127}$/u)
      .nullable(),
    finishedAt: z.string().datetime({ offset: true }),
  })
  .strict()
  .superRefine((result, context) => {
    if (
      (result.status === "succeeded" && result.errorCode !== null) ||
      (result.status === "failed" && result.errorCode === null)
    ) {
      context.addIssue({
        code: "custom",
        message: "Update worker errorCode does not match status",
      });
    }
  });

export type GoalProgressUpdateWorkerResult = z.infer<typeof GoalProgressUpdateWorkerResultSchema>;

export const GoalProgressUpdateRestartResultSchema = z
  .object({
    operationId: z.string().uuid(),
    targetVersion: StrictSemverSchema,
    status: z.enum(["launched", "failed"]),
    errorCode: z
      .string()
      .regex(/^[A-Z][A-Z0-9_]{2,127}$/u)
      .nullable(),
    finishedAt: z.string().datetime({ offset: true }),
  })
  .strict()
  .superRefine((result, context) => {
    if (
      (result.status === "launched" && result.errorCode !== null) ||
      (result.status === "failed" && result.errorCode === null)
    ) {
      context.addIssue({
        code: "custom",
        message: "Update restart result errorCode does not match status",
      });
    }
  });

export type GoalProgressUpdateRestartResult = z.infer<typeof GoalProgressUpdateRestartResultSchema>;
