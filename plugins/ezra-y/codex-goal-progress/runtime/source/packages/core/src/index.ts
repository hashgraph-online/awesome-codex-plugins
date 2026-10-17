import { createHash } from "node:crypto";
import {
  GOAL_CONTRACT_SCHEMA_VERSION,
  GOAL_NATIVE_OBJECTIVE_MAX_LENGTH,
  GOAL_PROGRESS_BPS_TOTAL,
  type GoalContract,
  type GoalContractAny,
  GoalContractSchema,
  type GoalContractV1,
  GoalContractV1Schema,
  type GoalEvidence,
  type GoalObjective,
  type GoalProgressCommand as GoalProgressCommandContract,
  type GoalProgressCommandMetadata as GoalProgressCommandMetadataContract,
  GoalProgressCommandSchema,
  type GoalProgressCorrection,
  type GoalProgressEvent,
  GoalProgressEventSchema,
  type GoalProgressItemChange,
  GoalProgressItemChangeSchema,
  type GoalProgressViewModel,
  GoalProgressViewModelSchema,
  type NativeGoalTokenUsage,
  NativeGoalTokenUsageSchema,
  parseGoalContractAny,
} from "../../contracts/src/index.js";

export * from "./activation.js";

const FINAL_VERIFICATION_CAP_BPS = 9_500;

export function hashNativeGoalObjective(objective: string): string {
  return createHash("sha256").update(objective, "utf8").digest("hex");
}

export type GoalProgressCoreErrorCode =
  | "REVISION_CONFLICT"
  | "INVALID_COMMAND"
  | "DUPLICATE_TARGET"
  | "TARGET_NOT_FOUND"
  | "CANCELLED_TARGET"
  | "INVALID_SCOPE"
  | "INVALID_TRANSITION"
  | "CORRECTION_REASON_REQUIRED"
  | "EVENT_SEQUENCE"
  | "CONTRACT_MISMATCH";

export type GoalProgressCommand = GoalProgressCommandContract;
export type GoalProgressCommandMetadata = GoalProgressCommandMetadataContract;

export interface GoalProgressCoreSuccess {
  readonly ok: true;
  readonly contract: GoalContractAny;
  readonly event: GoalProgressEvent;
}

export interface GoalProgressCoreFailure {
  readonly ok: false;
  readonly code: GoalProgressCoreErrorCode;
  readonly currentRevision: number | null;
  readonly message: string;
}

export type GoalProgressCoreResult = GoalProgressCoreSuccess | GoalProgressCoreFailure;

export interface GoalProgressCalculation {
  readonly objectiveProgressBps: Readonly<Record<string, number>>;
  readonly rawProgressBps: number;
  readonly displayProgressBps: number;
  readonly contractComplete: boolean;
  readonly nativeGoalComplete: boolean;
  readonly completionConfirmed: boolean;
  readonly finalVerificationPending: boolean;
}

export type GoalProgressCalculationResult =
  | { readonly ok: true; readonly calculation: GoalProgressCalculation }
  | {
      readonly ok: false;
      readonly code: "INVALID_CONTRACT";
      readonly message: string;
    };

export type GoalProgressViewModelResult =
  | { readonly ok: true; readonly viewModel: GoalProgressViewModel }
  | {
      readonly ok: false;
      readonly code: "INVALID_CONTRACT" | "INVALID_VIEW_MODEL";
      readonly message: string;
    };

export const TOKEN_TEMPORARILY_UNAVAILABLE_LABEL = "Token 暂不可用";

export interface ProjectViewModelOptions {
  readonly tokenUsage?: NativeGoalTokenUsage;
  readonly tokenStale?: boolean;
  readonly tokenUnavailable?: boolean;
  readonly detached?: boolean;
  readonly errorCode?: string;
}

export type GoalContractMigrationErrorCode =
  | "REBIND_REQUIRED"
  | "NATIVE_GOAL_DETACHED"
  | "NATIVE_GOAL_OBJECTIVE_TOO_LONG";

export interface NativeGoalMigrationSource {
  readonly threadId: string;
  readonly objective: string;
  readonly createdAt: number;
  readonly status: GoalContract["nativeGoal"]["status"] | "usageLimited" | "budgetLimited";
  readonly tokenBudget?: number | null;
}

export type GoalContractMigrationResult =
  | { readonly ok: true; readonly contract: GoalContract }
  | {
      readonly ok: false;
      readonly code: GoalContractMigrationErrorCode;
      readonly message: string;
    };

export function migrateGoalContractV1ToV2(input: {
  readonly contract: GoalContractV1;
  readonly identity: { readonly sessionTreeId: string; readonly threadId: string } | null;
  readonly nativeGoal: NativeGoalMigrationSource | null;
  readonly threadResolveCode?: "CURRENT_THREAD_NOT_FOUND" | "CURRENT_THREAD_AMBIGUOUS";
}): GoalContractMigrationResult {
  if (
    input.threadResolveCode === "CURRENT_THREAD_AMBIGUOUS" ||
    input.threadResolveCode === "CURRENT_THREAD_NOT_FOUND" ||
    input.identity === null
  ) {
    return {
      ok: false,
      code: "REBIND_REQUIRED",
      message: "Current Goal thread is not uniquely bound; do not guess a Contract mapping",
    };
  }
  if (!input.nativeGoal) {
    return {
      ok: false,
      code: "NATIVE_GOAL_DETACHED",
      message: "Native Goal is missing; do not keep writing the previous Contract",
    };
  }
  if (
    input.identity.threadId !== input.contract.sessionId ||
    input.nativeGoal.threadId !== input.identity.threadId
  ) {
    return {
      ok: false,
      code: "REBIND_REQUIRED",
      message: "Proven thread does not uniquely match the stored Contract",
    };
  }
  if (input.nativeGoal.objective !== input.contract.nativeGoal.objective) {
    return {
      ok: false,
      code: "REBIND_REQUIRED",
      message: "Current native Goal objective does not match the stored Contract",
    };
  }
  if (input.nativeGoal.objective.length > GOAL_NATIVE_OBJECTIVE_MAX_LENGTH) {
    return {
      ok: false,
      code: "NATIVE_GOAL_OBJECTIVE_TOO_LONG",
      message: `Native Goal objective exceeds ${GOAL_NATIVE_OBJECTIVE_MAX_LENGTH} characters`,
    };
  }
  const nativeStatus =
    input.nativeGoal.status === "complete"
      ? "complete"
      : input.nativeGoal.status === "paused"
        ? "paused"
        : input.nativeGoal.status === "blocked" ||
            input.nativeGoal.status === "usageLimited" ||
            input.nativeGoal.status === "budgetLimited"
          ? "blocked"
          : "active";
  const blockedReason =
    input.nativeGoal.status === "usageLimited"
      ? "usage-limit"
      : input.nativeGoal.status === "budgetLimited"
        ? "budget-limit"
        : nativeStatus === "blocked"
          ? "native-goal"
          : undefined;
  const migrated = GoalContractSchema.safeParse({
    ...input.contract,
    schemaVersion: GOAL_CONTRACT_SCHEMA_VERSION,
    sessionId: input.identity.threadId,
    sessionTreeId: input.identity.sessionTreeId,
    threadId: input.identity.threadId,
    nativeGoalBinding: {
      threadId: input.identity.threadId,
      createdAt: input.nativeGoal.createdAt,
      objectiveHash: hashNativeGoalObjective(input.nativeGoal.objective),
    },
    nativeGoal: {
      objective: input.nativeGoal.objective,
      status: nativeStatus,
      ...(blockedReason ? { blockedReason } : {}),
      ...(input.nativeGoal.tokenBudget === null || input.nativeGoal.tokenBudget === undefined
        ? input.contract.nativeGoal.tokenBudget === undefined
          ? {}
          : { tokenBudget: input.contract.nativeGoal.tokenBudget }
        : { tokenBudget: input.nativeGoal.tokenBudget }),
    },
    phase:
      nativeStatus === "paused"
        ? "paused"
        : input.contract.phase === "paused"
          ? "active"
          : input.contract.phase,
    objectives: input.contract.objectives.map((objective) => ({
      ...objective,
      requirement: "required" as const,
    })),
  });
  if (!migrated.success) {
    return {
      ok: false,
      code: "REBIND_REQUIRED",
      message: migrated.error.issues[0]?.message ?? "Migrated Contract is invalid",
    };
  }
  return { ok: true, contract: migrated.data };
}

function failure(
  code: GoalProgressCoreErrorCode,
  currentRevision: number | null,
  message: string,
): GoalProgressCoreFailure {
  return { ok: false, code, currentRevision, message };
}

function objectiveIsOptional(objective: { readonly requirement?: string } | object): boolean {
  return "requirement" in objective && objective.requirement === "optional";
}

function countableItems(objective: { readonly items: GoalObjective["items"] }) {
  return objective.items.filter((item) => item.status !== "cancelled");
}

function mergeEvidence(
  current: readonly GoalEvidence[],
  incoming: readonly GoalEvidence[],
): GoalEvidence[] {
  const merged = new Map(current.map((evidence) => [evidence.id, evidence]));
  for (const evidence of incoming) {
    merged.set(evidence.id, evidence);
  }
  return [...merged.values()];
}

function objectiveCompletion(objective: {
  readonly status: GoalObjective["status"];
  readonly items: GoalObjective["items"];
}): {
  readonly completed: number;
  readonly countable: number;
} {
  if (objective.status === "cancelled") {
    return { completed: 0, countable: 1 };
  }
  const items = countableItems(objective);
  if (items.length === 0) {
    return {
      completed: objective.status === "completed" ? 1 : 0,
      countable: 1,
    };
  }
  return {
    completed: items.filter((item) => item.status === "completed").length,
    countable: items.length,
  };
}

function calculateObjectiveProgressBps(objective: {
  readonly status: GoalObjective["status"];
  readonly items: GoalObjective["items"];
}): number {
  const completion = objectiveCompletion(objective);
  return Math.floor((completion.completed * GOAL_PROGRESS_BPS_TOTAL) / completion.countable);
}

function objectiveCompletionVerification(
  objective: {
    readonly evidence: readonly GoalEvidence[];
    readonly items: GoalObjective["items"];
  },
  progressBps: number,
): "reported" | "verified" | null {
  if (progressBps !== GOAL_PROGRESS_BPS_TOTAL) {
    return null;
  }
  const items = countableItems(objective);
  const verified =
    items.length === 0
      ? objective.evidence.some((evidence) => evidence.verification === "verified")
      : items.every((item) =>
          item.evidence.some((evidence) => evidence.verification === "verified"),
        );
  return verified ? "verified" : "reported";
}

function requiredObjectivesComplete(objectives: GoalContractAny["objectives"]): boolean {
  const requiredObjectives = objectives.filter(
    (objective) => objective.status !== "cancelled" && !objectiveIsOptional(objective),
  );
  return (
    requiredObjectives.length > 0 &&
    requiredObjectives.every(
      (objective) => calculateObjectiveProgressBps(objective) === GOAL_PROGRESS_BPS_TOTAL,
    )
  );
}

function calculateValidatedGoalProgress(contract: GoalContractAny): GoalProgressCalculation {
  const objectiveProgressBps: Record<string, number> = {};
  let rawProgressBps = 0;

  for (const objective of contract.objectives) {
    if (objective.status === "cancelled") {
      continue;
    }
    const completion = objectiveCompletion(objective);
    const progressBps = calculateObjectiveProgressBps(objective);
    objectiveProgressBps[objective.id] = progressBps;
    if (objectiveIsOptional(objective)) {
      continue;
    }
    rawProgressBps += Math.floor(
      (objective.contributionBps * completion.completed) / completion.countable,
    );
  }

  rawProgressBps = Math.min(GOAL_PROGRESS_BPS_TOTAL, rawProgressBps);
  const contractComplete = requiredObjectivesComplete(contract.objectives);
  const nativeGoalComplete = contract.nativeGoal.status === "complete";
  const completionConfirmed = contractComplete && nativeGoalComplete;
  const displayProgressBps = completionConfirmed
    ? GOAL_PROGRESS_BPS_TOTAL
    : Math.min(rawProgressBps, FINAL_VERIFICATION_CAP_BPS);

  return {
    objectiveProgressBps,
    rawProgressBps,
    displayProgressBps,
    contractComplete,
    nativeGoalComplete,
    completionConfirmed,
    finalVerificationPending: contractComplete && !nativeGoalComplete,
  };
}

export function calculateGoalProgress(contractInput: unknown): GoalProgressCalculationResult {
  const contract = parseGoalContractAny(contractInput);
  if (!contract.success) {
    return {
      ok: false,
      code: "INVALID_CONTRACT",
      message: contract.error.issues[0]?.message ?? "The Goal Contract is invalid",
    };
  }
  return {
    ok: true,
    calculation: calculateValidatedGoalProgress(contract.data),
  };
}

function formatTokenCount(value: number): string {
  if (value < 1_000) {
    return String(value);
  }
  const scale = value < 1_000_000 ? 1_000 : 1_000_000;
  const suffix = value < 1_000_000 ? "K" : "M";
  const exact = value / scale;
  if (Number.isInteger(exact)) {
    return `${exact}${suffix}`;
  }
  return `${Math.round(value / (scale / 10)) / 10}${suffix}`;
}

function projectTokenView(
  tokenUsage: Extract<NativeGoalTokenUsage, { availability: "available" }> | undefined,
  options: ProjectViewModelOptions,
): GoalProgressViewModel["token"] | undefined {
  if (!tokenUsage) {
    return undefined;
  }
  const flags = {
    ...(options.tokenStale ? { stale: true } : {}),
    ...(options.tokenUnavailable ? { unavailable: true } : {}),
  };
  if (options.tokenUnavailable) {
    return {
      used: tokenUsage.tokensUsed,
      budget: tokenUsage.tokenBudget,
      label: TOKEN_TEMPORARILY_UNAVAILABLE_LABEL,
      ...flags,
    };
  }
  return {
    used: tokenUsage.tokensUsed,
    budget: tokenUsage.tokenBudget,
    ...(tokenUsage.inputTokens !== undefined && tokenUsage.outputTokens !== undefined
      ? {
          inputTokens: tokenUsage.inputTokens,
          outputTokens: tokenUsage.outputTokens,
        }
      : {}),
    label:
      tokenUsage.inputTokens !== undefined && tokenUsage.outputTokens !== undefined
        ? `输入 ${formatTokenCount(tokenUsage.inputTokens)} · 输出 ${formatTokenCount(
            tokenUsage.outputTokens,
          )}`
        : `Token ${formatTokenCount(tokenUsage.tokensUsed)}`,
    ...flags,
  };
}

function viewPhase(
  contract: GoalContractAny,
  calculation: GoalProgressCalculation,
): Exclude<GoalProgressViewModel["trackingPhase"], "detached"> {
  if (contract.phase === "preparing") {
    return "preparing";
  }
  if (calculation.completionConfirmed) {
    return "completed";
  }
  if (contract.nativeGoal.status === "paused") {
    return "paused";
  }
  if (contract.nativeGoal.status === "blocked") {
    return "blocked";
  }
  if (contract.phase === "error" && contract.objectives.length === 0) {
    return "error";
  }
  return "active";
}

export function projectGoalProgressViewModel(
  contractInput: unknown,
  options: ProjectViewModelOptions = {},
): GoalProgressViewModelResult {
  const contractResult = parseGoalContractAny(contractInput);
  if (!contractResult.success) {
    return {
      ok: false,
      code: "INVALID_CONTRACT",
      message: contractResult.error.issues[0]?.message ?? "The Goal Contract is invalid",
    };
  }
  const contract = contractResult.data;
  const calculation = calculateValidatedGoalProgress(contract);
  const trackingPhase: GoalProgressViewModel["trackingPhase"] = options.detached
    ? "detached"
    : viewPhase(contract, calculation);
  const tracksProgress =
    trackingPhase === "active" ||
    trackingPhase === "paused" ||
    trackingPhase === "blocked" ||
    trackingPhase === "completed";
  const tokenResult =
    options.tokenUsage === undefined
      ? undefined
      : NativeGoalTokenUsageSchema.safeParse(options.tokenUsage);
  const tokenUsage =
    tracksProgress &&
    tokenResult?.success &&
    tokenResult.data.availability === "available" &&
    tokenResult.data.threadId === contract.sessionId
      ? tokenResult.data
      : undefined;

  const toObjectiveView = (
    objective: (typeof contract.objectives)[number],
  ): GoalProgressViewModel["objectives"][number] => {
    const progressBps = calculation.objectiveProgressBps[objective.id] ?? 0;
    const countableItems = objective.items.filter((item) => item.status !== "cancelled");
    const status =
      progressBps === GOAL_PROGRESS_BPS_TOTAL
        ? "completed"
        : countableItems.some((item) => item.status === "active")
          ? "active"
          : countableItems.some((item) => item.status === "blocked")
            ? "blocked"
            : objective.status === "blocked"
              ? "blocked"
              : objective.status === "active"
                ? "active"
                : "pending";
    const currentItem =
      objective.items.find((item) => item.status === "active") ??
      objective.items.find((item) => item.status === "blocked") ??
      objective.items.find((item) => item.status === "pending");
    return {
      id: objective.id,
      title: objective.title,
      ...(currentItem ? { currentItemTitle: currentItem.title } : {}),
      status,
      progressBps,
      progressPercent: Math.floor(progressBps / 100),
      completionVerification: objectiveCompletionVerification(objective, progressBps),
    };
  };
  const visibleObjectives = tracksProgress
    ? contract.objectives.filter((objective) => objective.status !== "cancelled")
    : [];
  const tokenView = projectTokenView(tokenUsage, options);

  const viewModel = GoalProgressViewModelSchema.safeParse({
    schemaVersion: GOAL_CONTRACT_SCHEMA_VERSION,
    contractId: contract.contractId,
    sessionId: contract.sessionId,
    revision: contract.revision,
    scopeRevision: contract.scopeRevision,
    trackingPhase,
    ...(trackingPhase === "blocked"
      ? {
          blockedReason:
            ("blockedReason" in contract.nativeGoal
              ? contract.nativeGoal.blockedReason
              : undefined) ?? "native-goal",
        }
      : {}),
    objective: contract.nativeGoal.objective,
    overallProgressBps: tracksProgress ? calculation.displayProgressBps : null,
    overallPercent: tracksProgress ? Math.floor(calculation.displayProgressBps / 100) : null,
    finalVerificationPending: tracksProgress ? calculation.finalVerificationPending : false,
    objectives: visibleObjectives
      .filter((objective) => !objectiveIsOptional(objective))
      .map(toObjectiveView),
    optionalObjectives: visibleObjectives
      .filter((objective) => objectiveIsOptional(objective))
      .map(toObjectiveView),
    maxVisibleObjectives: 3,
    ...(tokenView ? { token: tokenView } : {}),
    ...(contract.lastScopeChange ? { scopeChangeNotice: contract.lastScopeChange } : {}),
    ...(contract.lastProgressCorrection
      ? { progressCorrectionNotice: contract.lastProgressCorrection }
      : {}),
    ...(trackingPhase === "error"
      ? { errorCode: options.errorCode ?? "GOAL_PROGRESS_UNAVAILABLE" }
      : {}),
  });
  if (!viewModel.success) {
    return {
      ok: false,
      code: "INVALID_VIEW_MODEL",
      message: viewModel.error.issues[0]?.message ?? "The Goal Progress ViewModel is invalid",
    };
  }
  return { ok: true, viewModel: viewModel.data };
}

function findTarget(
  objectives: GoalContractAny["objectives"],
  targetId: string,
):
  | { readonly kind: "objective"; readonly objective: GoalContractAny["objectives"][number] }
  | {
      readonly kind: "item";
      readonly objective: GoalContractAny["objectives"][number];
      readonly item: GoalContractAny["objectives"][number]["items"][number];
    }
  | undefined {
  for (const objective of objectives) {
    if (objective.id === targetId) {
      return { kind: "objective", objective };
    }
    const item = objective.items.find((candidate) => candidate.id === targetId);
    if (item) {
      return { kind: "item", objective, item };
    }
  }
  return undefined;
}

function applyItemChanges(
  contract: GoalContractAny,
  changesInput: readonly GoalProgressItemChange[],
  activeObjectiveId: string | null | undefined,
):
  | { readonly ok: true; readonly objectives: GoalContractAny["objectives"] }
  | GoalProgressCoreFailure {
  if (changesInput.length === 0) {
    return failure("INVALID_COMMAND", contract.revision, "At least one item change is required");
  }
  const parsedChanges: GoalProgressItemChange[] = [];
  const changedTargets = new Set<string>();
  for (const input of changesInput) {
    const parsed = GoalProgressItemChangeSchema.safeParse(input);
    if (!parsed.success) {
      return failure("INVALID_COMMAND", contract.revision, "An item change is invalid");
    }
    if (changedTargets.has(parsed.data.targetId)) {
      return failure(
        "DUPLICATE_TARGET",
        contract.revision,
        `Target ${parsed.data.targetId} appears more than once`,
      );
    }
    changedTargets.add(parsed.data.targetId);
    const target = findTarget(contract.objectives, parsed.data.targetId);
    if (!target) {
      return failure(
        "TARGET_NOT_FOUND",
        contract.revision,
        `Target ${parsed.data.targetId} does not exist`,
      );
    }
    if (
      target.objective.status === "cancelled" ||
      (target.kind === "item" && target.item.status === "cancelled")
    ) {
      return failure(
        "CANCELLED_TARGET",
        contract.revision,
        `Target ${parsed.data.targetId} can change only through rescope`,
      );
    }
    parsedChanges.push(parsed.data);
  }

  if (activeObjectiveId !== undefined && activeObjectiveId !== null) {
    const activeObjective = contract.objectives.find(
      (objective) => objective.id === activeObjectiveId,
    );
    if (!activeObjective) {
      return failure(
        "TARGET_NOT_FOUND",
        contract.revision,
        `Active objective ${activeObjectiveId} does not exist`,
      );
    }
    if (activeObjective.status === "cancelled") {
      return failure(
        "CANCELLED_TARGET",
        contract.revision,
        `Active objective ${activeObjectiveId} is cancelled`,
      );
    }
  }

  const changes = new Map(parsedChanges.map((change) => [change.targetId, change]));
  const objectives = contract.objectives.map((objective) => {
    const objectiveChange = changes.get(objective.id);
    const nextObjectiveStatus =
      objectiveChange?.status ??
      (activeObjectiveId === objective.id
        ? "active"
        : activeObjectiveId !== undefined && objective.status === "active"
          ? "pending"
          : objective.status);
    return {
      ...objective,
      status: nextObjectiveStatus,
      ...(objectiveChange?.evidence === undefined
        ? {}
        : {
            evidence: mergeEvidence(objective.evidence, objectiveChange.evidence),
          }),
      items: objective.items.map((item) => {
        const itemChange = changes.get(item.id);
        if (!itemChange) {
          return item;
        }
        return {
          ...item,
          status: itemChange.status,
          ...(itemChange.evidence === undefined
            ? {}
            : { evidence: mergeEvidence(item.evidence, itemChange.evidence) }),
        };
      }),
    };
  });
  return { ok: true, objectives };
}

function resolveProgressCorrection(
  contract: GoalContractAny,
  objectives: GoalContractAny["objectives"],
  source: GoalProgressEvent["source"],
  reasonInput: string | undefined,
  revision: number,
  changedAt: string,
):
  | {
      readonly ok: true;
      readonly correction: GoalProgressCorrection | undefined;
    }
  | GoalProgressCoreFailure {
  const before = calculateValidatedGoalProgress(contract).rawProgressBps;
  const after = calculateValidatedGoalProgress({
    ...contract,
    objectives: [...objectives],
  } as GoalContractAny).rawProgressBps;
  if (after >= before) {
    return { ok: true, correction: undefined };
  }
  const reason =
    reasonInput?.trim() || (source === "user" ? "User explicitly reopened completed work" : "");
  if (!reason) {
    return failure(
      "CORRECTION_REASON_REQUIRED",
      contract.revision,
      "A non-user progress regression requires a correction reason",
    );
  }
  return {
    ok: true,
    correction: {
      revision,
      reason,
      changedAt,
      source,
    },
  };
}

function validPhaseTransition(
  current: GoalContractAny["phase"],
  next: GoalContractAny["phase"],
): boolean {
  if (current === next) {
    return true;
  }
  const transitions: Record<GoalContractAny["phase"], readonly GoalContractAny["phase"][]> = {
    preparing: ["active", "error"],
    active: ["paused", "completed", "error"],
    paused: ["active", "completed", "error"],
    completed: ["active", "error"],
    error: ["preparing", "active"],
  };
  return transitions[current].includes(next);
}

function eventEnvelope(command: GoalProgressCommand, revision: number) {
  return {
    schemaVersion: GOAL_CONTRACT_SCHEMA_VERSION,
    eventId: command.eventId,
    requestId: command.requestId,
    contractId: command.contractId,
    sessionId: command.sessionId,
    turnId: command.turnId,
    revision,
    occurredAt: command.occurredAt,
    source: command.source,
  };
}

function parseContractVersion(input: unknown, schemaVersion: 1 | 2) {
  return schemaVersion === 1
    ? GoalContractV1Schema.safeParse(input)
    : GoalContractSchema.safeParse(input);
}

function finalizeCommand(
  previous: GoalContractAny,
  candidateInput: unknown,
  eventInput: unknown,
  candidateErrorCode: GoalProgressCoreErrorCode = "INVALID_COMMAND",
  schemaVersion: 1 | 2 = previous.schemaVersion,
): GoalProgressCoreResult {
  const candidate = parseContractVersion(candidateInput, schemaVersion);
  if (!candidate.success) {
    return failure(
      candidateErrorCode,
      previous.revision,
      candidate.error.issues[0]?.message ?? "The resulting contract is invalid",
    );
  }
  const event = GoalProgressEventSchema.safeParse(eventInput);
  if (!event.success) {
    return failure(
      "INVALID_COMMAND",
      previous.revision,
      event.error.issues[0]?.message ?? "The resulting event is invalid",
    );
  }
  return { ok: true, contract: candidate.data, event: event.data };
}

export function applyGoalProgressCommand(
  contractInput: GoalContractAny,
  commandInput: GoalProgressCommand,
): GoalProgressCoreResult {
  const contractResult = GoalContractSchema.safeParse(contractInput);
  if (!contractResult.success) {
    return failure("INVALID_COMMAND", null, "The current contract is invalid");
  }
  const contract = contractResult.data;
  const commandResult = GoalProgressCommandSchema.safeParse(commandInput);
  if (!commandResult.success) {
    return failure(
      commandInput?.type === "rescope" || commandInput?.type === "retarget-rescope"
        ? "INVALID_SCOPE"
        : "INVALID_COMMAND",
      contract.revision,
      commandResult.error.issues[0]?.message ?? "Command is invalid",
    );
  }
  const command = commandResult.data;
  if (command.contractId !== contract.contractId || command.sessionId !== contract.sessionId) {
    return failure(
      "CONTRACT_MISMATCH",
      contract.revision,
      "Command identity does not match the current contract",
    );
  }
  if (
    !Number.isInteger(command.expectedRevision) ||
    command.expectedRevision !== contract.revision
  ) {
    return failure(
      "REVISION_CONFLICT",
      contract.revision,
      `Expected revision ${command.expectedRevision}; current revision is ${contract.revision}`,
    );
  }
  if (
    !Number.isFinite(Date.parse(command.occurredAt)) ||
    Date.parse(command.occurredAt) < Date.parse(contract.updatedAt)
  ) {
    return failure(
      "INVALID_COMMAND",
      contract.revision,
      "Command time cannot be before the current contract",
    );
  }
  const nextRevision = contract.revision + 1;
  const envelope = eventEnvelope(command, nextRevision);

  if (command.type === "update-items") {
    const applied = applyItemChanges(contract, command.changes, command.activeObjectiveId);
    if (!applied.ok) {
      return applied;
    }
    const correction = resolveProgressCorrection(
      contract,
      applied.objectives,
      command.source,
      command.correctionReason,
      nextRevision,
      command.occurredAt,
    );
    if (!correction.ok) {
      return correction;
    }
    const updatedContract = {
      ...contract,
      objectives: applied.objectives,
      revision: nextRevision,
      updatedAt: command.occurredAt,
      ...(correction.correction ? { lastProgressCorrection: correction.correction } : {}),
    };
    const candidate = {
      ...updatedContract,
      phase:
        requiredObjectivesComplete(applied.objectives) &&
        updatedContract.nativeGoal.status === "complete"
          ? ("completed" as const)
          : updatedContract.phase,
    };
    return finalizeCommand(contract, candidate, {
      ...envelope,
      type: "contract.items-updated",
      payload: {
        changes: command.changes,
        ...(command.activeObjectiveId === undefined
          ? {}
          : { activeObjectiveId: command.activeObjectiveId }),
        ...(command.correctionReason === undefined
          ? {}
          : { correctionReason: command.correctionReason }),
      },
    });
  }

  if (command.type === "rescope") {
    const reason = command.reason.trim();
    if (!reason) {
      return failure("INVALID_SCOPE", contract.revision, "Rescope requires a reason");
    }
    const scopeRevision = contract.scopeRevision + 1;
    const phase = contract.nativeGoal.status === "paused" ? "paused" : "active";
    const candidate = {
      ...contract,
      objectives: [...command.objectives],
      phase,
      revision: nextRevision,
      scopeRevision,
      lastScopeChange: {
        scopeRevision,
        reason,
        changedAt: command.occurredAt,
      },
      updatedAt: command.occurredAt,
    };
    return finalizeCommand(
      contract,
      candidate,
      {
        ...envelope,
        type: "contract.rescoped",
        payload: {
          reason,
          objectives: command.objectives,
          scopeRevision,
        },
      },
      "INVALID_SCOPE",
    );
  }

  if (command.type === "retarget-rescope") {
    const reason = command.reason.trim();
    const bindingChanged =
      command.nativeGoalBinding.createdAt !== contract.nativeGoalBinding.createdAt ||
      command.nativeGoalBinding.objectiveHash !== contract.nativeGoalBinding.objectiveHash;
    if (
      !reason.startsWith("当前方向：") ||
      command.nativeGoalBinding.threadId !== contract.threadId ||
      command.nativeGoalBinding.objectiveHash !==
        hashNativeGoalObjective(command.nativeGoal.objective) ||
      !bindingChanged
    ) {
      return failure(
        "INVALID_SCOPE",
        contract.revision,
        "Retarget rescope requires a changed trusted native Goal and 当前方向 reason",
      );
    }
    const scopeRevision = contract.scopeRevision + 1;
    const phase = command.nativeGoal.status === "paused" ? "paused" : "active";
    const candidate = {
      ...contract,
      nativeGoalBinding: command.nativeGoalBinding,
      nativeGoal: command.nativeGoal,
      objectives: [...command.objectives],
      phase,
      revision: nextRevision,
      scopeRevision,
      lastScopeChange: {
        scopeRevision,
        reason,
        changedAt: command.occurredAt,
      },
      updatedAt: command.occurredAt,
    };
    return finalizeCommand(
      contract,
      candidate,
      {
        ...envelope,
        type: "contract.retargeted",
        payload: {
          reason,
          nativeGoalBinding: command.nativeGoalBinding,
          nativeGoal: command.nativeGoal,
          objectives: command.objectives,
          scopeRevision,
        },
      },
      "INVALID_SCOPE",
    );
  }

  if (command.type === "set-phase") {
    if (command.phase === "paused" || command.phase === "error") {
      return failure(
        "INVALID_TRANSITION",
        contract.revision,
        "Pause and error states are not model-controlled Contract phases",
      );
    }
    if (!validPhaseTransition(contract.phase, command.phase)) {
      return failure(
        "INVALID_TRANSITION",
        contract.revision,
        `Cannot change phase from ${contract.phase} to ${command.phase}`,
      );
    }
    if (
      command.phase === "completed" &&
      !calculateValidatedGoalProgress(contract).completionConfirmed
    ) {
      return failure(
        "INVALID_TRANSITION",
        contract.revision,
        "Completion requires a complete Contract and native Goal",
      );
    }
    const candidate = {
      ...contract,
      phase: command.phase,
      revision: nextRevision,
      updatedAt: command.occurredAt,
    };
    return finalizeCommand(contract, candidate, {
      ...envelope,
      type: "contract.phase-changed",
      payload: { phase: command.phase },
    });
  }

  if (command.nativeGoal.objective !== contract.nativeGoal.objective) {
    return failure(
      "CONTRACT_MISMATCH",
      contract.revision,
      "Native Goal objective does not match the bound contract",
    );
  }
  const syncedContractResult = GoalContractSchema.safeParse({
    ...contract,
    nativeGoal: command.nativeGoal,
    phase:
      command.nativeGoal.status === "paused"
        ? "paused"
        : contract.phase === "paused" ||
            (contract.phase === "completed" && command.nativeGoal.status !== "complete")
          ? "active"
          : contract.phase,
  });
  if (!syncedContractResult.success) {
    return failure(
      "INVALID_COMMAND",
      contract.revision,
      syncedContractResult.error.issues[0]?.message ?? "Native Goal is invalid",
    );
  }
  const syncedContract = syncedContractResult.data;
  const calculation = calculateValidatedGoalProgress(syncedContract);
  const candidate = {
    ...syncedContract,
    phase: calculation.completionConfirmed ? "completed" : syncedContract.phase,
    revision: nextRevision,
    updatedAt: command.occurredAt,
  };
  return finalizeCommand(contract, candidate, {
    ...envelope,
    type: "native-goal.synced",
    payload: { nativeGoal: command.nativeGoal },
  });
}

function objectivesForContract(
  current: GoalContractAny,
  objectives: GoalContractAny["objectives"] | GoalContract["objectives"],
): unknown {
  if (current.schemaVersion === 1) {
    return objectives.map((objective) => {
      const { requirement: _requirement, ...rest } = objective as typeof objective & {
        requirement?: string;
      };
      return rest;
    });
  }
  return objectives.map((objective) => ({
    ...objective,
    requirement:
      "requirement" in objective && objective.requirement ? objective.requirement : "required",
  }));
}

function validateEventSequence(
  current: GoalContractAny,
  event: GoalProgressEvent,
  options: { readonly sameRevision?: boolean } = {},
): GoalProgressCoreFailure | undefined {
  if (event.contractId !== current.contractId || event.sessionId !== current.sessionId) {
    return failure(
      "CONTRACT_MISMATCH",
      current.revision,
      "Event identity does not match the current contract",
    );
  }
  const expectedRevision = options.sameRevision ? current.revision : current.revision + 1;
  if (event.revision !== expectedRevision) {
    return failure(
      "EVENT_SEQUENCE",
      current.revision,
      `Expected event revision ${expectedRevision}; received ${event.revision}`,
    );
  }
  if (Date.parse(event.occurredAt) < Date.parse(current.updatedAt)) {
    return failure(
      "EVENT_SEQUENCE",
      current.revision,
      "Event time cannot be before the current contract",
    );
  }
  return undefined;
}

export function reduceGoalProgressEvent(
  currentInput: GoalContractAny | null,
  eventInput: GoalProgressEvent,
): GoalProgressCoreResult {
  const eventResult = GoalProgressEventSchema.safeParse(eventInput);
  if (!eventResult.success) {
    return failure("INVALID_COMMAND", currentInput?.revision ?? null, "Event is invalid");
  }
  const event = eventResult.data;
  if (event.type === "contract.initialized") {
    if (currentInput !== null) {
      return failure(
        "EVENT_SEQUENCE",
        currentInput.revision,
        "Initialization can be applied only to an empty state",
      );
    }
    if (
      event.payload.contract.contractId !== event.contractId ||
      event.payload.contract.sessionId !== event.sessionId ||
      event.payload.contract.revision !== event.revision
    ) {
      return failure("CONTRACT_MISMATCH", null, "Initialization event does not match its contract");
    }
    return {
      ok: true,
      contract: event.payload.contract,
      event,
    };
  }
  if (currentInput === null) {
    return failure("EVENT_SEQUENCE", null, "The first event must initialize the contract");
  }
  const currentResult = parseGoalContractAny(currentInput);
  if (!currentResult.success) {
    return failure("INVALID_COMMAND", null, "The current contract is invalid");
  }
  const current = currentResult.data;
  if (event.type === "contract.replaced") {
    const replacement = event.payload.contract;
    const nativeGoalBindingChanged =
      current.schemaVersion === 2 &&
      (replacement.nativeGoalBinding.createdAt !== current.nativeGoalBinding.createdAt ||
        replacement.nativeGoalBinding.objectiveHash !== current.nativeGoalBinding.objectiveHash);
    if (
      current.schemaVersion !== 2 ||
      event.payload.previousContractId !== current.contractId ||
      event.payload.previousRevision !== current.revision ||
      event.contractId !== replacement.contractId ||
      event.sessionId !== replacement.sessionId ||
      event.revision !== replacement.revision ||
      replacement.revision !== 1 ||
      replacement.contractId === current.contractId ||
      replacement.threadId !== current.threadId ||
      !nativeGoalBindingChanged ||
      Date.parse(event.occurredAt) < Date.parse(current.updatedAt)
    ) {
      return failure(
        "EVENT_SEQUENCE",
        current.revision,
        "Replacement event does not establish a new native Goal baseline",
      );
    }
    return {
      ok: true,
      contract: replacement,
      event,
    };
  }
  if (event.type === "contract.migrated") {
    const sequenceFailure = validateEventSequence(current, event, { sameRevision: true });
    if (sequenceFailure) {
      return sequenceFailure;
    }
    if (current.schemaVersion !== 1) {
      return failure("EVENT_SEQUENCE", current.revision, "Migration applies only to a v1 Contract");
    }
    if (
      event.payload.contract.contractId !== current.contractId ||
      event.payload.contract.sessionId !== current.sessionId ||
      event.payload.contract.revision !== current.revision
    ) {
      return failure(
        "CONTRACT_MISMATCH",
        current.revision,
        "Migration event does not match the current contract",
      );
    }
    return { ok: true, contract: event.payload.contract, event };
  }
  const sequenceFailure = validateEventSequence(current, event);
  if (sequenceFailure) {
    return sequenceFailure;
  }

  let candidate: unknown;
  if (event.type === "contract.items-updated") {
    const applied = applyItemChanges(
      current,
      event.payload.changes,
      event.payload.activeObjectiveId,
    );
    if (!applied.ok) {
      return applied;
    }
    const correction = resolveProgressCorrection(
      current,
      applied.objectives,
      event.source,
      event.payload.correctionReason,
      event.revision,
      event.occurredAt,
    );
    if (!correction.ok) {
      return correction;
    }
    const updatedContract = {
      ...current,
      objectives: applied.objectives,
      revision: event.revision,
      updatedAt: event.occurredAt,
      ...(correction.correction ? { lastProgressCorrection: correction.correction } : {}),
    };
    candidate = {
      ...updatedContract,
      phase:
        requiredObjectivesComplete(applied.objectives) &&
        updatedContract.nativeGoal.status === "complete"
          ? "completed"
          : updatedContract.phase,
    };
  } else if (event.type === "contract.rescoped") {
    if (event.payload.scopeRevision !== current.scopeRevision + 1) {
      return failure(
        "EVENT_SEQUENCE",
        current.revision,
        "Rescope event has an invalid scope revision",
      );
    }
    candidate = {
      ...current,
      objectives: objectivesForContract(current, event.payload.objectives),
      phase: current.nativeGoal.status === "paused" ? "paused" : "active",
      revision: event.revision,
      scopeRevision: event.payload.scopeRevision,
      lastScopeChange: {
        scopeRevision: event.payload.scopeRevision,
        reason: event.payload.reason,
        changedAt: event.occurredAt,
      },
      updatedAt: event.occurredAt,
    };
  } else if (event.type === "contract.retargeted") {
    const bindingChanged =
      current.schemaVersion === 2 &&
      (event.payload.nativeGoalBinding.createdAt !== current.nativeGoalBinding.createdAt ||
        event.payload.nativeGoalBinding.objectiveHash !== current.nativeGoalBinding.objectiveHash);
    if (
      current.schemaVersion !== 2 ||
      event.payload.scopeRevision !== current.scopeRevision + 1 ||
      event.payload.nativeGoalBinding.threadId !== current.threadId ||
      event.payload.nativeGoalBinding.objectiveHash !==
        hashNativeGoalObjective(event.payload.nativeGoal.objective) ||
      !event.payload.reason.startsWith("当前方向：") ||
      !bindingChanged
    ) {
      return failure(
        "EVENT_SEQUENCE",
        current.revision,
        "Retarget event does not establish a changed native Goal scope",
      );
    }
    candidate = {
      ...current,
      nativeGoalBinding: event.payload.nativeGoalBinding,
      nativeGoal: event.payload.nativeGoal,
      objectives: event.payload.objectives,
      phase: event.payload.nativeGoal.status === "paused" ? "paused" : "active",
      revision: event.revision,
      scopeRevision: event.payload.scopeRevision,
      lastScopeChange: {
        scopeRevision: event.payload.scopeRevision,
        reason: event.payload.reason,
        changedAt: event.occurredAt,
      },
      updatedAt: event.occurredAt,
    };
  } else if (event.type === "contract.phase-changed") {
    if (!validPhaseTransition(current.phase, event.payload.phase)) {
      return failure(
        "INVALID_TRANSITION",
        current.revision,
        `Cannot change phase from ${current.phase} to ${event.payload.phase}`,
      );
    }
    if (
      event.payload.phase === "completed" &&
      !calculateValidatedGoalProgress(current).completionConfirmed
    ) {
      return failure(
        "INVALID_TRANSITION",
        current.revision,
        "Completion requires a complete Contract and native Goal",
      );
    }
    candidate = {
      ...current,
      phase: event.payload.phase,
      revision: event.revision,
      updatedAt: event.occurredAt,
    };
  } else if (event.type === "native-goal.synced") {
    if (event.payload.nativeGoal.objective !== current.nativeGoal.objective) {
      return failure(
        "CONTRACT_MISMATCH",
        current.revision,
        "Native Goal event objective does not match the bound contract",
      );
    }
    const syncedResult = parseContractVersion(
      {
        ...current,
        nativeGoal: event.payload.nativeGoal,
        phase:
          event.payload.nativeGoal.status === "paused"
            ? "paused"
            : current.phase === "paused" ||
                (current.phase === "completed" && event.payload.nativeGoal.status !== "complete")
              ? "active"
              : current.phase,
      },
      current.schemaVersion,
    );
    if (!syncedResult.success) {
      return failure("INVALID_COMMAND", current.revision, "Native Goal event is invalid");
    }
    const synced = syncedResult.data;
    const completionConfirmed = calculateValidatedGoalProgress(synced).completionConfirmed;
    candidate = {
      ...synced,
      phase: completionConfirmed ? "completed" : synced.phase,
      revision: event.revision,
      updatedAt: event.occurredAt,
    };
  } else {
    return failure("EVENT_SEQUENCE", current.revision, "Unsupported Goal Progress event");
  }
  const parsedCandidate = parseContractVersion(candidate, current.schemaVersion);
  if (!parsedCandidate.success) {
    return failure(
      "INVALID_SCOPE",
      current.revision,
      parsedCandidate.error.issues[0]?.message ?? "Event produced an invalid contract",
    );
  }
  return { ok: true, contract: parsedCandidate.data, event };
}
