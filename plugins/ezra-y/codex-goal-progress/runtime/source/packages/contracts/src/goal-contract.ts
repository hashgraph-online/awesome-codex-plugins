import { z } from "zod";

export const GOAL_CONTRACT_SCHEMA_VERSION_V1 = 1 as const;
export const GOAL_CONTRACT_SCHEMA_VERSION = 2 as const;
export const GOAL_PROGRESS_BPS_TOTAL = 10_000 as const;
export const GOAL_NATIVE_OBJECTIVE_MAX_LENGTH = 4_000 as const;

const NonEmptyTextSchema = z.string().trim().min(1);
const IsoTimestampSchema = z.iso.datetime({ offset: true });

export const GoalContractIdSchema = z
  .string()
  .regex(/^gp_[A-Za-z0-9][A-Za-z0-9_-]{7,127}$/)
  .describe(
    "Contract ID returned by the plugin. Starts with gp_ followed by 8-128 ASCII letters, digits, underscores or hyphens; the first suffix character is alphanumeric. Copy unchanged; not a bare UUID.",
  );
export const GoalObjectiveIdSchema = z
  .string()
  .max(64)
  .regex(/^C[1-9]\d*$/)
  .describe(
    "Objective ID: C followed by a positive integer, e.g. C1 or C2. Preserve existing IDs when updating or reordering.",
  );
export const GoalChecklistItemIdSchema = z
  .string()
  .max(128)
  .regex(/^C[1-9]\d*\.[1-9]\d*$/)
  .describe(
    "Child item ID: parent objective ID plus a dot and a positive integer, e.g. C1.1 or C1.2. Do not use letters after the dot.",
  );
export const GoalProgressTargetIdSchema = z.union([
  GoalObjectiveIdSchema,
  GoalChecklistItemIdSchema,
]);

export const GoalProgressItemStatusSchema = z.enum([
  "pending",
  "active",
  "completed",
  "blocked",
  "cancelled",
]);
export const GoalProgressMutableStatusSchema = z.enum([
  "pending",
  "active",
  "completed",
  "blocked",
]);
export const GoalProgressPhaseSchema = z.enum([
  "preparing",
  "active",
  "paused",
  "completed",
  "error",
]);
export const GoalProgressTrackingPhaseSchema = z.enum([
  "preparing",
  "active",
  "paused",
  "blocked",
  "completed",
  "error",
  "detached",
]);
export const GoalNativeBlockedReasonSchema = z.enum(["native-goal", "usage-limit", "budget-limit"]);
export const GoalProgressSourceSchema = z.enum(["existing-checklist", "model-generated"]);
export const GoalProgressActorSchema = z.enum(["model", "user", "local-validator", "system"]);

export const GoalEvidenceSchema = z
  .object({
    id: z.string().trim().min(1).max(128),
    kind: z.enum(["model-report", "test", "build", "file", "manual", "other"]),
    verification: z.enum(["reported", "verified"]),
    summary: NonEmptyTextSchema.max(500),
    reference: z.string().trim().min(1).max(2_048).optional(),
    observedAt: IsoTimestampSchema,
    source: GoalProgressActorSchema.exclude(["system"]),
  })
  .strict();

export const GoalChecklistItemSchema = z
  .object({
    id: GoalChecklistItemIdSchema,
    title: NonEmptyTextSchema.max(500),
    status: GoalProgressItemStatusSchema,
    evidence: z.array(GoalEvidenceSchema).max(100).default([]),
  })
  .strict();

export const GoalObjectiveRequirementSchema = z.enum(["required", "optional"]);

export const GoalObjectiveV1Schema = z
  .object({
    id: GoalObjectiveIdSchema,
    title: NonEmptyTextSchema.max(500),
    contributionBps: z.number().int().min(1).max(GOAL_PROGRESS_BPS_TOTAL),
    contributionReason: NonEmptyTextSchema.max(500),
    status: GoalProgressItemStatusSchema,
    evidence: z.array(GoalEvidenceSchema).max(100).default([]),
    items: z.array(GoalChecklistItemSchema).max(500),
  })
  .strict();

export const GoalObjectiveSchema = z
  .object({
    id: GoalObjectiveIdSchema,
    title: NonEmptyTextSchema.max(500),
    requirement: GoalObjectiveRequirementSchema.default("required"),
    contributionBps: z
      .number()
      .int()
      .min(0)
      .max(GOAL_PROGRESS_BPS_TOTAL)
      .describe(
        "Non-cancelled required objectives: 1-10000, total 10000. Optional: 0. Cancelled required objectives may use 0 or retain a previous weight; they do not count toward progress.",
      ),
    contributionReason: NonEmptyTextSchema.max(500),
    status: GoalProgressItemStatusSchema,
    evidence: z.array(GoalEvidenceSchema).max(100).default([]),
    items: z.array(GoalChecklistItemSchema).max(500),
  })
  .strict()
  .superRefine((objective, context) => {
    if (objective.requirement === "optional") {
      if (objective.contributionBps !== 0) {
        context.addIssue({
          code: "custom",
          message: "Optional objectives must contribute 0 bps",
          path: ["contributionBps"],
        });
      }
      return;
    }
    if (objective.status !== "cancelled" && objective.contributionBps < 1) {
      context.addIssue({
        code: "custom",
        message: "Non-cancelled required objectives must contribute at least 1 bps",
        path: ["contributionBps"],
      });
    }
  });

export const NativeGoalBindingSchema = z
  .object({
    threadId: z.string().trim().min(1).max(256),
    createdAt: z.number().int().nonnegative(),
    objectiveHash: z.string().regex(/^[0-9a-f]{64}$/),
  })
  .strict();

export const GoalContractNativeGoalV1Schema = z
  .object({
    objective: NonEmptyTextSchema.max(20_000),
    status: z.enum(["active", "paused", "complete", "blocked"]),
    tokenBudget: z.number().int().nonnegative().optional(),
  })
  .strict();

export const GoalContractNativeGoalSchema = z
  .object({
    objective: NonEmptyTextSchema.max(GOAL_NATIVE_OBJECTIVE_MAX_LENGTH),
    status: z.enum(["active", "paused", "complete", "blocked"]),
    blockedReason: GoalNativeBlockedReasonSchema.optional(),
    tokenBudget: z.number().int().nonnegative().optional(),
  })
  .strict()
  .superRefine((goal, context) => {
    if (goal.status !== "blocked" && goal.blockedReason) {
      context.addIssue({
        code: "custom",
        message: "blockedReason is valid only for a blocked native Goal",
        path: ["blockedReason"],
      });
    }
  });

export const GoalScopeChangeSchema = z
  .object({
    scopeRevision: z.number().int().positive(),
    reason: NonEmptyTextSchema.max(2_000),
    changedAt: IsoTimestampSchema,
  })
  .strict();

export const GoalProgressCorrectionSchema = z
  .object({
    revision: z.number().int().positive(),
    reason: NonEmptyTextSchema.max(2_000),
    changedAt: IsoTimestampSchema,
    source: GoalProgressActorSchema,
  })
  .strict();

export const GoalContractV1Schema = z
  .object({
    schemaVersion: z.literal(GOAL_CONTRACT_SCHEMA_VERSION_V1),
    contractId: GoalContractIdSchema,
    sessionId: z.string().trim().min(1).max(256),
    nativeGoal: GoalContractNativeGoalV1Schema,
    phase: GoalProgressPhaseSchema,
    revision: z.number().int().nonnegative(),
    scopeRevision: z.number().int().nonnegative(),
    source: GoalProgressSourceSchema,
    objectives: z.array(GoalObjectiveV1Schema).max(100),
    lastScopeChange: GoalScopeChangeSchema.optional(),
    lastProgressCorrection: GoalProgressCorrectionSchema.optional(),
    createdAt: IsoTimestampSchema,
    updatedAt: IsoTimestampSchema,
  })
  .strict()
  .superRefine((contract, context) => {
    const objectiveIds = new Set<string>();
    const targetIds = new Set<string>();
    const evidenceIds = new Set<string>();
    let activeContributionBps = 0;

    for (const [objectiveIndex, objective] of contract.objectives.entries()) {
      if (objectiveIds.has(objective.id)) {
        context.addIssue({
          code: "custom",
          message: `Duplicate objective ID: ${objective.id}`,
          path: ["objectives", objectiveIndex, "id"],
        });
      }
      objectiveIds.add(objective.id);
      targetIds.add(objective.id);
      if (objective.status !== "cancelled") {
        activeContributionBps += objective.contributionBps;
      }
      for (const [evidenceIndex, evidence] of objective.evidence.entries()) {
        if (evidenceIds.has(evidence.id)) {
          context.addIssue({
            code: "custom",
            message: `Duplicate evidence ID: ${evidence.id}`,
            path: ["objectives", objectiveIndex, "evidence", evidenceIndex, "id"],
          });
        }
        evidenceIds.add(evidence.id);
      }
      const countableItems = objective.items.filter((item) => item.status !== "cancelled");
      if (
        objective.status === "completed" &&
        countableItems.length > 0 &&
        countableItems.some((item) => item.status !== "completed")
      ) {
        context.addIssue({
          code: "custom",
          message: "A completed objective cannot contain incomplete active items",
          path: ["objectives", objectiveIndex, "status"],
        });
      }

      for (const [itemIndex, item] of objective.items.entries()) {
        if (!item.id.startsWith(`${objective.id}.`)) {
          context.addIssue({
            code: "custom",
            message: `Checklist item ${item.id} does not belong to ${objective.id}`,
            path: ["objectives", objectiveIndex, "items", itemIndex, "id"],
          });
        }
        if (targetIds.has(item.id)) {
          context.addIssue({
            code: "custom",
            message: `Duplicate target ID: ${item.id}`,
            path: ["objectives", objectiveIndex, "items", itemIndex, "id"],
          });
        }
        targetIds.add(item.id);
        for (const [evidenceIndex, evidence] of item.evidence.entries()) {
          if (evidenceIds.has(evidence.id)) {
            context.addIssue({
              code: "custom",
              message: `Duplicate evidence ID: ${evidence.id}`,
              path: [
                "objectives",
                objectiveIndex,
                "items",
                itemIndex,
                "evidence",
                evidenceIndex,
                "id",
              ],
            });
          }
          evidenceIds.add(evidence.id);
        }
      }
    }

    if (contract.objectives.length > 0 && activeContributionBps !== GOAL_PROGRESS_BPS_TOTAL) {
      context.addIssue({
        code: "custom",
        message: `Active objective contributions must total ${GOAL_PROGRESS_BPS_TOTAL}`,
        path: ["objectives"],
      });
    }
    if (
      contract.objectives.length === 0 &&
      contract.phase !== "preparing" &&
      contract.phase !== "error"
    ) {
      context.addIssue({
        code: "custom",
        message: "A tracking contract must contain at least one objective",
        path: ["objectives"],
      });
    }
    if (contract.scopeRevision > contract.revision) {
      context.addIssue({
        code: "custom",
        message: "scopeRevision cannot exceed revision",
        path: ["scopeRevision"],
      });
    }
    if (contract.scopeRevision > 0 && !contract.lastScopeChange) {
      context.addIssue({
        code: "custom",
        message: "A scoped contract requires the latest scope change reason",
        path: ["lastScopeChange"],
      });
    }
    if (
      contract.lastScopeChange &&
      contract.lastScopeChange.scopeRevision !== contract.scopeRevision
    ) {
      context.addIssue({
        code: "custom",
        message: "lastScopeChange must describe the current scope revision",
        path: ["lastScopeChange", "scopeRevision"],
      });
    }
    if (
      contract.lastProgressCorrection &&
      contract.lastProgressCorrection.revision > contract.revision
    ) {
      context.addIssue({
        code: "custom",
        message: "A progress correction cannot be newer than the contract",
        path: ["lastProgressCorrection", "revision"],
      });
    }
    if (Date.parse(contract.updatedAt) < Date.parse(contract.createdAt)) {
      context.addIssue({
        code: "custom",
        message: "updatedAt cannot be before createdAt",
        path: ["updatedAt"],
      });
    }
    if (contract.phase === "completed") {
      if (contract.nativeGoal.status !== "complete") {
        context.addIssue({
          code: "custom",
          message: "A completed contract requires a complete native Goal",
          path: ["nativeGoal", "status"],
        });
      }
      const incompleteObjectiveIndex = contract.objectives.findIndex((objective) => {
        if (objective.status === "cancelled") {
          return false;
        }
        const items = objective.items.filter((item) => item.status !== "cancelled");
        return items.length === 0
          ? objective.status !== "completed"
          : items.some((item) => item.status !== "completed");
      });
      if (incompleteObjectiveIndex >= 0) {
        context.addIssue({
          code: "custom",
          message: "A completed contract requires every active objective to be complete",
          path: ["objectives", incompleteObjectiveIndex],
        });
      }
    }
  });

export const GoalContractV2Schema = z
  .object({
    schemaVersion: z.literal(GOAL_CONTRACT_SCHEMA_VERSION),
    contractId: GoalContractIdSchema,
    sessionId: z.string().trim().min(1).max(256),
    sessionTreeId: z.string().trim().min(1).max(256),
    threadId: z.string().trim().min(1).max(256),
    nativeGoalBinding: NativeGoalBindingSchema,
    nativeGoal: GoalContractNativeGoalSchema,
    phase: GoalProgressPhaseSchema,
    revision: z.number().int().nonnegative(),
    scopeRevision: z.number().int().nonnegative(),
    source: GoalProgressSourceSchema,
    objectives: z.array(GoalObjectiveSchema).max(100),
    lastScopeChange: GoalScopeChangeSchema.optional(),
    lastProgressCorrection: GoalProgressCorrectionSchema.optional(),
    createdAt: IsoTimestampSchema,
    updatedAt: IsoTimestampSchema,
  })
  .strict()
  .superRefine((contract, context) => {
    if (contract.sessionId !== contract.threadId) {
      context.addIssue({
        code: "custom",
        message: "sessionId must equal the bound threadId",
        path: ["sessionId"],
      });
    }
    if (contract.nativeGoalBinding.threadId !== contract.threadId) {
      context.addIssue({
        code: "custom",
        message: "nativeGoalBinding.threadId must match contract.threadId",
        path: ["nativeGoalBinding", "threadId"],
      });
    }
    const objectiveIds = new Set<string>();
    const targetIds = new Set<string>();
    const evidenceIds = new Set<string>();
    let requiredContributionBps = 0;

    for (const [objectiveIndex, objective] of contract.objectives.entries()) {
      if (objectiveIds.has(objective.id)) {
        context.addIssue({
          code: "custom",
          message: `Duplicate objective ID: ${objective.id}`,
          path: ["objectives", objectiveIndex, "id"],
        });
      }
      objectiveIds.add(objective.id);
      targetIds.add(objective.id);
      if (objective.status !== "cancelled" && objective.requirement === "required") {
        requiredContributionBps += objective.contributionBps;
      }
      for (const [evidenceIndex, evidence] of objective.evidence.entries()) {
        if (evidenceIds.has(evidence.id)) {
          context.addIssue({
            code: "custom",
            message: `Duplicate evidence ID: ${evidence.id}`,
            path: ["objectives", objectiveIndex, "evidence", evidenceIndex, "id"],
          });
        }
        evidenceIds.add(evidence.id);
      }
      const countableItems = objective.items.filter((item) => item.status !== "cancelled");
      if (
        objective.status === "completed" &&
        countableItems.length > 0 &&
        countableItems.some((item) => item.status !== "completed")
      ) {
        context.addIssue({
          code: "custom",
          message: "A completed objective cannot contain incomplete active items",
          path: ["objectives", objectiveIndex, "status"],
        });
      }

      for (const [itemIndex, item] of objective.items.entries()) {
        if (!item.id.startsWith(`${objective.id}.`)) {
          context.addIssue({
            code: "custom",
            message: `Checklist item ${item.id} does not belong to ${objective.id}`,
            path: ["objectives", objectiveIndex, "items", itemIndex, "id"],
          });
        }
        if (targetIds.has(item.id)) {
          context.addIssue({
            code: "custom",
            message: `Duplicate target ID: ${item.id}`,
            path: ["objectives", objectiveIndex, "items", itemIndex, "id"],
          });
        }
        targetIds.add(item.id);
        for (const [evidenceIndex, evidence] of item.evidence.entries()) {
          if (evidenceIds.has(evidence.id)) {
            context.addIssue({
              code: "custom",
              message: `Duplicate evidence ID: ${evidence.id}`,
              path: [
                "objectives",
                objectiveIndex,
                "items",
                itemIndex,
                "evidence",
                evidenceIndex,
                "id",
              ],
            });
          }
          evidenceIds.add(evidence.id);
        }
      }
    }

    if (contract.objectives.length > 0 && requiredContributionBps !== GOAL_PROGRESS_BPS_TOTAL) {
      context.addIssue({
        code: "custom",
        message: `Required objective contributions must total ${GOAL_PROGRESS_BPS_TOTAL}`,
        path: ["objectives"],
      });
    }
    if (
      contract.objectives.length === 0 &&
      contract.phase !== "preparing" &&
      contract.phase !== "error"
    ) {
      context.addIssue({
        code: "custom",
        message: "A tracking contract must contain at least one objective",
        path: ["objectives"],
      });
    }
    if (contract.scopeRevision > contract.revision) {
      context.addIssue({
        code: "custom",
        message: "scopeRevision cannot exceed revision",
        path: ["scopeRevision"],
      });
    }
    if (contract.scopeRevision > 0 && !contract.lastScopeChange) {
      context.addIssue({
        code: "custom",
        message: "A scoped contract requires the latest scope change reason",
        path: ["lastScopeChange"],
      });
    }
    if (
      contract.lastScopeChange &&
      contract.lastScopeChange.scopeRevision !== contract.scopeRevision
    ) {
      context.addIssue({
        code: "custom",
        message: "lastScopeChange must describe the current scope revision",
        path: ["lastScopeChange", "scopeRevision"],
      });
    }
    if (
      contract.lastProgressCorrection &&
      contract.lastProgressCorrection.revision > contract.revision
    ) {
      context.addIssue({
        code: "custom",
        message: "A progress correction cannot be newer than the contract",
        path: ["lastProgressCorrection", "revision"],
      });
    }
    if (Date.parse(contract.updatedAt) < Date.parse(contract.createdAt)) {
      context.addIssue({
        code: "custom",
        message: "updatedAt cannot be before createdAt",
        path: ["updatedAt"],
      });
    }
    if (contract.phase === "completed") {
      if (contract.nativeGoal.status !== "complete") {
        context.addIssue({
          code: "custom",
          message: "A completed contract requires a complete native Goal",
          path: ["nativeGoal", "status"],
        });
      }
      const incompleteObjectiveIndex = contract.objectives.findIndex((objective) => {
        if (objective.status === "cancelled" || objective.requirement === "optional") {
          return false;
        }
        const items = objective.items.filter((item) => item.status !== "cancelled");
        return items.length === 0
          ? objective.status !== "completed"
          : items.some((item) => item.status !== "completed");
      });
      if (incompleteObjectiveIndex >= 0) {
        context.addIssue({
          code: "custom",
          message: "A completed contract requires every required objective to be complete",
          path: ["objectives", incompleteObjectiveIndex],
        });
      }
    }
  });

export const GoalContractSchema = GoalContractV2Schema;

export const GoalProgressItemChangeSchema = z
  .object({
    targetId: GoalProgressTargetIdSchema,
    status: GoalProgressMutableStatusSchema,
    evidence: z.array(GoalEvidenceSchema).max(100).optional(),
  })
  .strict();

export const GoalProgressCommandMetadataSchema = z
  .object({
    contractId: GoalContractIdSchema,
    sessionId: z.string().trim().min(1).max(256),
    expectedRevision: z.number().int().nonnegative(),
    eventId: z.string().trim().min(1).max(128),
    requestId: z.string().trim().min(1).max(128),
    turnId: z.string().trim().min(1).max(256),
    occurredAt: IsoTimestampSchema,
    source: GoalProgressActorSchema,
  })
  .strict();

export const GoalContractInitializationSchema = z
  .object({
    contractId: GoalContractIdSchema,
    source: GoalProgressSourceSchema,
    objectives: z.array(GoalObjectiveSchema).max(100),
  })
  .strict();

export const GoalProgressCommandSchema = z.discriminatedUnion("type", [
  GoalProgressCommandMetadataSchema.extend({
    type: z.literal("update-items"),
    changes: z.array(GoalProgressItemChangeSchema).min(1).max(500),
    activeObjectiveId: GoalObjectiveIdSchema.nullable().optional(),
    correctionReason: NonEmptyTextSchema.max(2_000).optional(),
  }).strict(),
  GoalProgressCommandMetadataSchema.extend({
    type: z.literal("rescope"),
    reason: NonEmptyTextSchema.max(2_000),
    objectives: z.array(GoalObjectiveSchema).max(100),
  }).strict(),
  GoalProgressCommandMetadataSchema.extend({
    type: z.literal("retarget-rescope"),
    reason: NonEmptyTextSchema.max(2_000),
    nativeGoalBinding: NativeGoalBindingSchema,
    nativeGoal: GoalContractNativeGoalSchema,
    objectives: z.array(GoalObjectiveSchema).max(100),
  }).strict(),
  GoalProgressCommandMetadataSchema.extend({
    type: z.literal("set-phase"),
    phase: GoalProgressPhaseSchema,
  }).strict(),
  GoalProgressCommandMetadataSchema.extend({
    type: z.literal("sync-native-goal"),
    nativeGoal: GoalContractNativeGoalSchema,
  }).strict(),
]);

const GoalProgressEventEnvelopeSchema = z.object({
  schemaVersion: z.union([
    z.literal(GOAL_CONTRACT_SCHEMA_VERSION_V1),
    z.literal(GOAL_CONTRACT_SCHEMA_VERSION),
  ]),
  eventId: z.string().trim().min(1).max(128),
  requestId: z.string().trim().min(1).max(128),
  contractId: GoalContractIdSchema,
  sessionId: z.string().trim().min(1).max(256),
  turnId: z.string().trim().min(1).max(256),
  revision: z.number().int().nonnegative(),
  occurredAt: IsoTimestampSchema,
  source: GoalProgressActorSchema,
});

export const GoalProgressEventSchema = z.discriminatedUnion("type", [
  GoalProgressEventEnvelopeSchema.extend({
    type: z.literal("contract.initialized"),
    payload: z.object({ contract: z.union([GoalContractV1Schema, GoalContractV2Schema]) }).strict(),
  }).strict(),
  GoalProgressEventEnvelopeSchema.extend({
    schemaVersion: z.literal(GOAL_CONTRACT_SCHEMA_VERSION),
    type: z.literal("contract.replaced"),
    payload: z
      .object({
        previousContractId: GoalContractIdSchema,
        previousRevision: z.number().int().nonnegative(),
        contract: GoalContractV2Schema,
      })
      .strict(),
  }).strict(),
  GoalProgressEventEnvelopeSchema.extend({
    type: z.literal("contract.items-updated"),
    payload: z
      .object({
        changes: z.array(GoalProgressItemChangeSchema).min(1).max(500),
        activeObjectiveId: GoalObjectiveIdSchema.nullable().optional(),
        correctionReason: NonEmptyTextSchema.max(2_000).optional(),
      })
      .strict(),
  }).strict(),
  GoalProgressEventEnvelopeSchema.extend({
    type: z.literal("contract.rescoped"),
    payload: z
      .object({
        reason: NonEmptyTextSchema.max(2_000),
        objectives: z.array(z.union([GoalObjectiveV1Schema, GoalObjectiveSchema])).max(100),
        scopeRevision: z.number().int().positive(),
      })
      .strict(),
  }).strict(),
  GoalProgressEventEnvelopeSchema.extend({
    schemaVersion: z.literal(GOAL_CONTRACT_SCHEMA_VERSION),
    type: z.literal("contract.retargeted"),
    payload: z
      .object({
        reason: NonEmptyTextSchema.max(2_000),
        nativeGoalBinding: NativeGoalBindingSchema,
        nativeGoal: GoalContractNativeGoalSchema,
        objectives: z.array(GoalObjectiveSchema).max(100),
        scopeRevision: z.number().int().positive(),
      })
      .strict(),
  }).strict(),
  GoalProgressEventEnvelopeSchema.extend({
    type: z.literal("contract.phase-changed"),
    payload: z.object({ phase: GoalProgressPhaseSchema }).strict(),
  }).strict(),
  GoalProgressEventEnvelopeSchema.extend({
    type: z.literal("native-goal.synced"),
    payload: z
      .object({
        nativeGoal: z.union([GoalContractNativeGoalV1Schema, GoalContractNativeGoalSchema]),
      })
      .strict(),
  }).strict(),
  GoalProgressEventEnvelopeSchema.extend({
    type: z.literal("contract.migrated"),
    payload: z
      .object({
        fromVersion: z.literal(GOAL_CONTRACT_SCHEMA_VERSION_V1),
        toVersion: z.literal(GOAL_CONTRACT_SCHEMA_VERSION),
        contract: GoalContractV2Schema,
      })
      .strict(),
  }).strict(),
]);

export const GoalProgressObjectiveViewSchema = z
  .object({
    id: GoalObjectiveIdSchema,
    title: NonEmptyTextSchema.max(500),
    currentItemTitle: NonEmptyTextSchema.max(500).optional(),
    status: GoalProgressMutableStatusSchema,
    progressBps: z.number().int().min(0).max(GOAL_PROGRESS_BPS_TOTAL),
    progressPercent: z.number().int().min(0).max(100),
    completionVerification: z.enum(["reported", "verified"]).nullable(),
  })
  .strict()
  .superRefine((objective, context) => {
    if (objective.progressPercent !== Math.floor(objective.progressBps / 100)) {
      context.addIssue({
        code: "custom",
        message: "progressPercent must be derived from progressBps",
        path: ["progressPercent"],
      });
    }
    if (
      (objective.progressBps === GOAL_PROGRESS_BPS_TOTAL) !==
      (objective.completionVerification !== null)
    ) {
      context.addIssue({
        code: "custom",
        message: "Only completed objective views have a completion verification level",
        path: ["completionVerification"],
      });
    }
  });

export const GoalProgressTokenViewSchema = z
  .object({
    used: z.number().int().nonnegative(),
    budget: z.number().int().nonnegative().nullable(),
    inputTokens: z.number().int().nonnegative().optional(),
    outputTokens: z.number().int().nonnegative().optional(),
    label: NonEmptyTextSchema.max(100),
    stale: z.boolean().optional(),
    unavailable: z.boolean().optional(),
  })
  .strict()
  .superRefine((usage, context) => {
    if ((usage.inputTokens === undefined) !== (usage.outputTokens === undefined)) {
      context.addIssue({
        code: "custom",
        message: "inputTokens and outputTokens must be provided together",
        path: ["inputTokens"],
      });
    }
  });

export const GoalProgressViewModelSchema = z
  .object({
    schemaVersion: z.literal(GOAL_CONTRACT_SCHEMA_VERSION),
    contractId: GoalContractIdSchema,
    sessionId: z.string().trim().min(1).max(256),
    revision: z.number().int().nonnegative(),
    scopeRevision: z.number().int().nonnegative(),
    trackingPhase: GoalProgressTrackingPhaseSchema,
    blockedReason: GoalNativeBlockedReasonSchema.optional(),
    preparingStep: z
      .enum(["reading-goal", "preparing-checklist", "establishing-baseline"])
      .optional(),
    objective: NonEmptyTextSchema.max(GOAL_NATIVE_OBJECTIVE_MAX_LENGTH),
    overallProgressBps: z.number().int().min(0).max(GOAL_PROGRESS_BPS_TOTAL).nullable(),
    overallPercent: z.number().int().min(0).max(100).nullable(),
    finalVerificationPending: z.boolean(),
    objectives: z.array(GoalProgressObjectiveViewSchema).max(100),
    optionalObjectives: z.array(GoalProgressObjectiveViewSchema).max(100).default([]),
    maxVisibleObjectives: z.literal(3),
    token: GoalProgressTokenViewSchema.optional(),
    scopeChangeNotice: GoalScopeChangeSchema.optional(),
    progressCorrectionNotice: GoalProgressCorrectionSchema.optional(),
    errorCode: z.string().trim().min(1).max(128).optional(),
  })
  .strict()
  .superRefine((viewModel, context) => {
    const objectiveIds = new Set<string>();
    for (const [index, objective] of viewModel.objectives.entries()) {
      if (objectiveIds.has(objective.id)) {
        context.addIssue({
          code: "custom",
          message: `Duplicate objective view ID: ${objective.id}`,
          path: ["objectives", index, "id"],
        });
      }
      objectiveIds.add(objective.id);
    }
    for (const [index, objective] of viewModel.optionalObjectives.entries()) {
      if (objectiveIds.has(objective.id)) {
        context.addIssue({
          code: "custom",
          message: `Duplicate objective view ID: ${objective.id}`,
          path: ["optionalObjectives", index, "id"],
        });
      }
      objectiveIds.add(objective.id);
    }
    if (viewModel.scopeRevision > viewModel.revision) {
      context.addIssue({
        code: "custom",
        message: "scopeRevision cannot exceed revision",
        path: ["scopeRevision"],
      });
    }
    const hasProgress = viewModel.overallProgressBps !== null && viewModel.overallPercent !== null;
    const tracksProgress =
      viewModel.trackingPhase === "active" ||
      viewModel.trackingPhase === "paused" ||
      viewModel.trackingPhase === "blocked" ||
      viewModel.trackingPhase === "completed";
    if (
      (viewModel.overallProgressBps === null) !== (viewModel.overallPercent === null) ||
      (tracksProgress && !hasProgress) ||
      (!tracksProgress && viewModel.trackingPhase !== "error" && hasProgress)
    ) {
      context.addIssue({
        code: "custom",
        message: "Tracking views require progress; error views may retain confirmed progress",
        path: ["overallProgressBps"],
      });
    }
    if (
      hasProgress &&
      viewModel.overallPercent !== Math.floor((viewModel.overallProgressBps ?? 0) / 100)
    ) {
      context.addIssue({
        code: "custom",
        message: "overallPercent must be derived from overallProgressBps",
        path: ["overallPercent"],
      });
    }
    if (
      (viewModel.trackingPhase === "preparing" ||
        viewModel.trackingPhase === "error" ||
        viewModel.trackingPhase === "detached") &&
      (viewModel.objectives.length > 0 || viewModel.optionalObjectives.length > 0)
    ) {
      context.addIssue({
        code: "custom",
        message: "Non-tracking views must not expose objective progress",
        path: ["objectives"],
      });
    }
    if (viewModel.trackingPhase === "completed") {
      if (
        viewModel.overallProgressBps !== GOAL_PROGRESS_BPS_TOTAL ||
        viewModel.overallPercent !== 100
      ) {
        context.addIssue({
          code: "custom",
          message: "Completed views must show 100 percent",
          path: ["overallProgressBps"],
        });
      }
      if (viewModel.finalVerificationPending) {
        context.addIssue({
          code: "custom",
          message: "A completed view cannot be waiting for final verification",
          path: ["finalVerificationPending"],
        });
      }
    }
    if (viewModel.finalVerificationPending && viewModel.overallProgressBps !== 9_500) {
      context.addIssue({
        code: "custom",
        message: "Final verification waits at 95 percent",
        path: ["finalVerificationPending"],
      });
    }
    if (viewModel.trackingPhase === "error" && !viewModel.errorCode) {
      context.addIssue({
        code: "custom",
        message: "Error views require an errorCode",
        path: ["errorCode"],
      });
    }
    if (viewModel.trackingPhase !== "error" && viewModel.errorCode) {
      context.addIssue({
        code: "custom",
        message: "errorCode is valid only for error views",
        path: ["errorCode"],
      });
    }
    if (viewModel.trackingPhase === "blocked" && !viewModel.blockedReason) {
      context.addIssue({
        code: "custom",
        message: "Blocked views require a blockedReason",
        path: ["blockedReason"],
      });
    }
    if (viewModel.trackingPhase !== "blocked" && viewModel.blockedReason) {
      context.addIssue({
        code: "custom",
        message: "blockedReason is valid only for blocked views",
        path: ["blockedReason"],
      });
    }
    if (viewModel.trackingPhase !== "preparing" && viewModel.preparingStep) {
      context.addIssue({
        code: "custom",
        message: "preparingStep is valid only for preparing views",
        path: ["preparingStep"],
      });
    }
  });

export interface GoalContractMigration {
  readonly fromVersion: number;
  readonly toVersion: number;
  migrate(input: unknown): unknown;
}

export type GoalEvidence = z.infer<typeof GoalEvidenceSchema>;
export type GoalChecklistItem = z.infer<typeof GoalChecklistItemSchema>;
export type GoalObjective = z.infer<typeof GoalObjectiveSchema>;
export type GoalContractNativeGoal = z.infer<typeof GoalContractNativeGoalSchema>;
export type GoalContractInitialization = z.infer<typeof GoalContractInitializationSchema>;
export type GoalContractV1 = z.infer<typeof GoalContractV1Schema>;
export type GoalContractV2 = z.infer<typeof GoalContractV2Schema>;
export type GoalContract = GoalContractV2;
export type GoalContractAny = GoalContractV1 | GoalContract;
export type NativeGoalBinding = z.infer<typeof NativeGoalBindingSchema>;
export type GoalProgressItemChange = z.infer<typeof GoalProgressItemChangeSchema>;
export type GoalProgressCorrection = z.infer<typeof GoalProgressCorrectionSchema>;
export type GoalProgressCommandMetadata = z.infer<typeof GoalProgressCommandMetadataSchema>;
export type GoalProgressCommand = z.infer<typeof GoalProgressCommandSchema>;
export type GoalProgressEvent = z.infer<typeof GoalProgressEventSchema>;
export type GoalProgressViewModel = z.infer<typeof GoalProgressViewModelSchema>;
export type GoalProgressTrackingPhase = z.infer<typeof GoalProgressTrackingPhaseSchema>;

export function parseGoalContractAny(input: unknown) {
  const v2 = GoalContractV2Schema.safeParse(input);
  if (v2.success) {
    return v2;
  }
  return GoalContractV1Schema.safeParse(input);
}
