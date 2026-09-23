import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { z } from "zod";
import {
  type CodexThreadIdentity,
  CurrentThreadResolverError,
  type CurrentThreadResolverInput,
} from "../../codex-adapter/src/index.js";
import {
  GOAL_NATIVE_OBJECTIVE_MAX_LENGTH,
  type GoalContract,
  type GoalContractAny,
  type GoalContractInitialization,
  type GoalEvidence,
  type GoalObjective,
  type RuntimeContext,
  type RuntimeIdentity,
  type RuntimeProof,
  type ThreadGoal,
} from "../../contracts/src/index.js";
import { hashNativeGoalObjective, migrateGoalContractV1ToV2 } from "../../core/src/index.js";
import {
  type CodexRequestIdentity,
  type GoalProgressIpcAuthorization,
  GoalProgressIpcHandlerError,
} from "../../ipc/src/index.js";
import {
  atomicWriteFile,
  type GoalEventStore,
  type GoalProgressLogInput,
  type GoalProgressPaths,
  hashGoalProgressIdentity,
  resolveGoalProgressSessionPaths,
} from "../../store/src/index.js";

export interface TrustedNativeGoal {
  readonly threadId: string;
  readonly objective: string;
  readonly status: ThreadGoal["status"];
  readonly createdAt: number;
  readonly tokenBudget?: number | null;
}

export type NativeGoalResolver = (threadId: string) => Promise<TrustedNativeGoal | null>;
export type ResolveCurrentThread = (input: CurrentThreadResolverInput) => Promise<RuntimeIdentity>;
export type ReadThreadIdentity = (threadId: string) => Promise<CodexThreadIdentity>;

const CODEX_REQUEST_REPLAY_RETENTION_MS = 60_000;
const CODEX_REQUEST_REPLAY_MAX_ENTRIES = 1_024;

const GoalProgressDetachReasonSchema = z.enum([
  "user-dismissed-preparation",
  "user-detached-tracking",
  "native-goal-ended",
  "native-goal-replaced",
  "stale-contract",
  "unavailable",
]);
export type GoalProgressDetachReason = z.infer<typeof GoalProgressDetachReasonSchema>;

const GoalProgressActivationStateSchema = z
  .object({
    schemaVersion: z.literal(1),
    detachReason: GoalProgressDetachReasonSchema.nullable(),
  })
  .strict();
export type GoalProgressActivationState = z.infer<typeof GoalProgressActivationStateSchema>;

export const DEFAULT_GOAL_PROGRESS_ACTIVATION_STATE: GoalProgressActivationState = {
  schemaVersion: 1,
  detachReason: null,
};

export interface GoalProgressActivationStateSnapshot {
  readonly state: GoalProgressActivationState;
  readonly exists: boolean;
}

function activationStatePath(threadId: string, paths: GoalProgressPaths): string {
  return resolve(resolveGoalProgressSessionPaths(paths, threadId).directory, "activation.json");
}

export async function readGoalProgressActivationStateSnapshot(
  threadId: string,
  paths: GoalProgressPaths,
): Promise<GoalProgressActivationStateSnapshot> {
  try {
    const parsed = GoalProgressActivationStateSchema.safeParse(
      JSON.parse(await readFile(activationStatePath(threadId, paths), "utf8")),
    );
    return {
      state: parsed.success ? parsed.data : DEFAULT_GOAL_PROGRESS_ACTIVATION_STATE,
      exists: true,
    };
  } catch (error) {
    if (
      error instanceof Error &&
      "code" in error &&
      (error as NodeJS.ErrnoException).code === "ENOENT"
    ) {
      return {
        state: DEFAULT_GOAL_PROGRESS_ACTIVATION_STATE,
        exists: false,
      };
    }
    throw error;
  }
}

export async function readGoalProgressActivationState(
  threadId: string,
  paths: GoalProgressPaths,
): Promise<GoalProgressActivationState> {
  return (await readGoalProgressActivationStateSnapshot(threadId, paths)).state;
}

export function isUserDetachedActivationState(state: GoalProgressActivationState): boolean {
  return (
    state.detachReason === "user-dismissed-preparation" ||
    state.detachReason === "user-detached-tracking"
  );
}

export async function writeGoalProgressActivationState(
  threadId: string,
  paths: GoalProgressPaths,
  state: GoalProgressActivationState,
): Promise<GoalProgressActivationState> {
  const parsed = GoalProgressActivationStateSchema.parse(state);
  await atomicWriteFile(
    activationStatePath(threadId, paths),
    `${JSON.stringify(parsed, null, 2)}\n`,
  );
  return parsed;
}

export function sanitizeModelEvidence(evidence: GoalEvidence): GoalEvidence {
  return {
    ...evidence,
    source: "model",
    verification: "reported",
  };
}

export function sanitizeModelObjective(
  objective: GoalObjective,
  previous?: GoalObjective,
): GoalObjective {
  const sameResult = (
    next: { id: string; title: string; status: string },
    stored?: { id: string; title: string; status: string },
  ) =>
    stored !== undefined &&
    next.id === stored.id &&
    next.title === stored.title &&
    next.status === stored.status;
  const previousItems = new Map(
    (previous?.id === objective.id ? previous.items : []).map((item) => [item.id, item]),
  );
  const unchanged =
    sameResult(objective, previous) &&
    previous?.items.length === objective.items.length &&
    objective.items.every((item) => sameResult(item, previousItems.get(item.id)));
  return {
    ...objective,
    // A rescope copies existing facts; only changed results bring new model reports.
    evidence:
      unchanged && previous ? previous.evidence : objective.evidence.map(sanitizeModelEvidence),
    items: objective.items.map((item) => {
      const stored = previousItems.get(item.id);
      return {
        ...item,
        evidence:
          sameResult(item, stored) && stored
            ? stored.evidence
            : item.evidence.map(sanitizeModelEvidence),
      };
    }),
  };
}

function mapNativeGoalStatus(
  status: TrustedNativeGoal["status"],
): GoalContract["nativeGoal"]["status"] {
  if (status === "complete") {
    return "complete";
  }
  if (status === "paused") {
    return "paused";
  }
  if (status === "blocked" || status === "usageLimited" || status === "budgetLimited") {
    return "blocked";
  }
  return "active";
}

function mapNativeGoalBlockedReason(
  status: TrustedNativeGoal["status"],
): GoalContract["nativeGoal"]["blockedReason"] {
  if (status === "usageLimited") {
    return "usage-limit";
  }
  if (status === "budgetLimited") {
    return "budget-limit";
  }
  return status === "blocked" ? "native-goal" : undefined;
}

export function contractNativeGoal(nativeGoal: TrustedNativeGoal): GoalContract["nativeGoal"] {
  const blockedReason = mapNativeGoalBlockedReason(nativeGoal.status);
  return {
    objective: nativeGoal.objective,
    status: mapNativeGoalStatus(nativeGoal.status),
    ...(blockedReason ? { blockedReason } : {}),
    ...(nativeGoal.tokenBudget === null || nativeGoal.tokenBudget === undefined
      ? {}
      : { tokenBudget: nativeGoal.tokenBudget }),
  };
}

export function createModelContract(
  initialization: GoalContractInitialization,
  nativeGoal: TrustedNativeGoal,
  identity: RuntimeIdentity,
  occurredAt: string,
): GoalContract {
  const nativeGoalStatus = mapNativeGoalStatus(nativeGoal.status);
  return {
    schemaVersion: 2,
    contractId: initialization.contractId,
    sessionId: identity.threadId,
    sessionTreeId: identity.sessionTreeId,
    threadId: identity.threadId,
    nativeGoalBinding: {
      threadId: identity.threadId,
      createdAt: nativeGoal.createdAt,
      objectiveHash: hashNativeGoalObjective(nativeGoal.objective),
    },
    nativeGoal: contractNativeGoal(nativeGoal),
    phase: nativeGoalStatus === "paused" ? "paused" : "active",
    revision: 1,
    scopeRevision: 0,
    source: initialization.source,
    objectives: initialization.objectives.map((objective) => sanitizeModelObjective(objective)),
    createdAt: occurredAt,
    updatedAt: occurredAt,
  };
}

export function trustedNativeGoalFromThreadGoal(goal: ThreadGoal | null): TrustedNativeGoal | null {
  if (!goal) {
    return null;
  }
  return {
    threadId: goal.threadId,
    objective: goal.objective,
    status: goal.status,
    createdAt: goal.createdAt,
    ...(goal.tokenBudget === undefined ? {} : { tokenBudget: goal.tokenBudget }),
  };
}

export function claimedSessionMatchesIdentity(
  claimedSessionId: string,
  identity: RuntimeIdentity,
): boolean {
  return claimedSessionId === identity.threadId || claimedSessionId === identity.sessionTreeId;
}

export function assertBoundNativeGoal(
  contract: GoalContract,
  nativeGoal: TrustedNativeGoal | null,
  revision: number | null,
): TrustedNativeGoal {
  if (!nativeGoal) {
    throw new GoalProgressIpcHandlerError(
      "NATIVE_GOAL_DETACHED",
      "Native Goal is missing; do not keep writing the previous Contract",
      revision,
    );
  }
  if (nativeGoal.threadId !== contract.threadId) {
    throw new GoalProgressIpcHandlerError(
      "NATIVE_GOAL_MISMATCH",
      "Current Session native Goal is unavailable or mismatched",
      revision,
    );
  }
  if (nativeGoal.createdAt !== contract.nativeGoalBinding.createdAt) {
    throw new GoalProgressIpcHandlerError(
      "NATIVE_GOAL_REPLACED",
      "Native Goal was replaced even if the objective text matches",
      revision,
    );
  }
  if (hashNativeGoalObjective(nativeGoal.objective) !== contract.nativeGoalBinding.objectiveHash) {
    throw new GoalProgressIpcHandlerError(
      "NATIVE_GOAL_OBJECTIVE_CHANGED",
      "Native Goal objective no longer matches the bound Contract",
      revision,
    );
  }
  if (nativeGoal.objective.length > GOAL_NATIVE_OBJECTIVE_MAX_LENGTH) {
    throw new GoalProgressIpcHandlerError(
      "NATIVE_GOAL_OBJECTIVE_TOO_LONG",
      `Native Goal objective exceeds ${GOAL_NATIVE_OBJECTIVE_MAX_LENGTH} characters`,
      revision,
    );
  }
  return nativeGoal;
}

export function nativeGoalErrorDetachesContract(error: unknown): boolean {
  return (
    error instanceof GoalProgressIpcHandlerError &&
    [
      "NATIVE_GOAL_DETACHED",
      "NATIVE_GOAL_MISMATCH",
      "NATIVE_GOAL_REPLACED",
      "NATIVE_GOAL_OBJECTIVE_CHANGED",
    ].includes(error.code)
  );
}

export function detachReasonForNativeGoalError(error: unknown): GoalProgressDetachReason {
  if (!(error instanceof GoalProgressIpcHandlerError)) {
    return "stale-contract";
  }
  switch (error.code) {
    case "NATIVE_GOAL_DETACHED":
      return "native-goal-ended";
    case "NATIVE_GOAL_REPLACED":
      return "native-goal-replaced";
    case "NATIVE_GOAL_MISMATCH":
    case "NATIVE_GOAL_OBJECTIVE_CHANGED":
      return "stale-contract";
    default:
      return "stale-contract";
  }
}

export function identityLogFields(identity: RuntimeIdentity): {
  readonly sessionKey: string;
  readonly sessionTreeKey: string;
  readonly threadKey: string;
} {
  const threadKey = hashGoalProgressIdentity(identity.threadId);
  return {
    sessionKey: threadKey,
    sessionTreeKey: hashGoalProgressIdentity(identity.sessionTreeId),
    threadKey,
  };
}

export interface GoalProgressSessionCoordinatorOptions {
  readonly store: GoalEventStore;
  readonly resolveNativeGoal: NativeGoalResolver;
  readonly resolveCurrentThread: ResolveCurrentThread;
  readonly readThreadIdentity: ReadThreadIdentity;
  readonly consumeRuntimeProof: (
    runtimeContext: RuntimeContext,
    runtimeProof: RuntimeProof,
  ) => Promise<boolean>;
  readonly log: (input: GoalProgressLogInput) => Promise<void>;
  readonly now?: () => number;
}

export class GoalProgressSessionCoordinator {
  readonly #store: GoalEventStore;
  readonly #resolveNativeGoal: NativeGoalResolver;
  readonly #resolveCurrentThread: ResolveCurrentThread;
  readonly #readThreadIdentity: ReadThreadIdentity;
  readonly #consumeRuntimeProof: GoalProgressSessionCoordinatorOptions["consumeRuntimeProof"];
  readonly #log: GoalProgressSessionCoordinatorOptions["log"];
  readonly #now: () => number;
  readonly #consumedCodexRequests = new Map<string, number>();

  constructor(options: GoalProgressSessionCoordinatorOptions) {
    this.#store = options.store;
    this.#resolveNativeGoal = options.resolveNativeGoal;
    this.#resolveCurrentThread = options.resolveCurrentThread;
    this.#readThreadIdentity = options.readThreadIdentity;
    this.#consumeRuntimeProof = options.consumeRuntimeProof;
    this.#log = options.log;
    this.#now = options.now ?? Date.now;
  }

  async resolveCurrentThread(input: CurrentThreadResolverInput): Promise<RuntimeIdentity> {
    return this.#resolveCurrentThread(input);
  }

  async resolveIdentity(runtimeContext: RuntimeContext): Promise<RuntimeIdentity> {
    try {
      return await this.#resolveCurrentThread({
        sessionTreeId: runtimeContext.hookSessionId,
        turnId: runtimeContext.turnId,
        cwd: runtimeContext.cwd,
        model: runtimeContext.model,
      });
    } catch (error) {
      if (error instanceof CurrentThreadResolverError) {
        throw new GoalProgressIpcHandlerError(error.code, error.message);
      }
      throw new GoalProgressIpcHandlerError(
        "CURRENT_THREAD_UNAVAILABLE",
        "Could not resolve the current Goal thread",
        null,
        undefined,
        error,
      );
    }
  }

  async authorizeSessionRequest(
    auth: GoalProgressIpcAuthorization,
    claimedSessionId?: string,
    turnId?: string,
  ): Promise<RuntimeIdentity> {
    if (auth.kind === "codex-request") {
      return this.#authorizeCodexRequest(auth.identity, auth.toolName, claimedSessionId, turnId);
    }
    return this.#authorizeHookRequest(
      auth.runtimeContext,
      auth.runtimeProof,
      claimedSessionId ?? auth.runtimeContext.hookSessionId,
      turnId,
    );
  }

  async #authorizeHookRequest(
    runtimeContext: RuntimeContext,
    runtimeProof: RuntimeProof,
    claimedSessionId: string,
    turnId?: string,
  ): Promise<RuntimeIdentity> {
    if (!(await this.#consumeRuntimeProof(runtimeContext, runtimeProof))) {
      throw new GoalProgressIpcHandlerError(
        "RUNTIME_PROOF_INVALID",
        "Write request does not have a valid runtime proof",
      );
    }
    if (turnId !== undefined && runtimeContext.turnId !== turnId) {
      throw new GoalProgressIpcHandlerError(
        "THREAD_MISMATCH",
        "Write request identity does not match its Session and turn",
      );
    }
    const identity = await this.resolveIdentity(runtimeContext);
    if (!claimedSessionMatchesIdentity(claimedSessionId, identity)) {
      throw new GoalProgressIpcHandlerError(
        "THREAD_MISMATCH",
        "Write request identity does not match its Session and turn",
      );
    }
    await this.#log({
      level: "info",
      event: "ipc.request",
      ...identityLogFields(identity),
    });
    return identity;
  }

  async #authorizeCodexRequest(
    requestIdentity: CodexRequestIdentity,
    toolName: string,
    claimedSessionId?: string,
    turnId?: string,
  ): Promise<RuntimeIdentity> {
    if (
      (claimedSessionId !== undefined && claimedSessionId !== requestIdentity.threadId) ||
      (turnId !== undefined && turnId !== requestIdentity.turnId)
    ) {
      throw new GoalProgressIpcHandlerError(
        "THREAD_MISMATCH",
        "Write request identity does not match its Session and turn",
      );
    }
    if (!this.#consumeCodexRequest(requestIdentity, toolName)) {
      throw new GoalProgressIpcHandlerError(
        "CODEX_REQUEST_REPLAYED",
        "Codex request identity was already consumed",
      );
    }

    let thread: CodexThreadIdentity;
    try {
      thread = await this.#readThreadIdentity(requestIdentity.threadId);
    } catch (error) {
      throw new GoalProgressIpcHandlerError(
        "CODEX_REQUEST_THREAD_UNAVAILABLE",
        "Could not read the exact Codex thread for this request",
        null,
        undefined,
        error,
      );
    }

    if (
      thread.id !== requestIdentity.threadId ||
      thread.sessionId !== requestIdentity.sessionId ||
      thread.threadSource !== requestIdentity.threadSource ||
      (requestIdentity.cwd !== undefined && requestIdentity.cwd !== thread.cwd)
    ) {
      throw new GoalProgressIpcHandlerError(
        "CODEX_REQUEST_IDENTITY_CONFLICT",
        "Codex request identity conflicts with the exact thread record",
      );
    }
    if (thread.threadSource !== "user" || thread.agentRole !== null || thread.ephemeral) {
      throw new GoalProgressIpcHandlerError(
        "CODEX_REQUEST_THREAD_UNTRUSTED",
        "Codex request does not belong to a supported main user thread",
      );
    }

    const identity: RuntimeIdentity = {
      sessionTreeId: thread.id,
      threadId: thread.id,
      turnId: requestIdentity.turnId,
      model: requestIdentity.model,
      cwd: thread.cwd,
    };
    await this.#log({
      level: "info",
      event: "ipc.request",
      ...identityLogFields(identity),
    });
    return identity;
  }

  #consumeCodexRequest(identity: CodexRequestIdentity, toolName: string): boolean {
    const now = this.#now();
    for (const [key, consumedAt] of this.#consumedCodexRequests) {
      if (now - consumedAt >= CODEX_REQUEST_REPLAY_RETENTION_MS) {
        this.#consumedCodexRequests.delete(key);
      }
    }
    const key = [identity.threadId, identity.turnId, identity.callId, toolName].join("\0");
    if (this.#consumedCodexRequests.has(key)) {
      return false;
    }
    this.#consumedCodexRequests.set(key, now);
    while (this.#consumedCodexRequests.size > CODEX_REQUEST_REPLAY_MAX_ENTRIES) {
      const oldest = this.#consumedCodexRequests.keys().next().value;
      if (oldest === undefined) {
        break;
      }
      this.#consumedCodexRequests.delete(oldest);
    }
    return true;
  }

  async trustedNativeGoal(
    sessionId: string,
    revision: number | null = null,
  ): Promise<TrustedNativeGoal> {
    const nativeGoal = await this.readNativeGoal(sessionId, revision);
    if (!nativeGoal) {
      throw new GoalProgressIpcHandlerError(
        "NATIVE_GOAL_DETACHED",
        "Native Goal is missing; do not keep writing the previous Contract",
        revision,
      );
    }
    if (nativeGoal.threadId !== sessionId || !nativeGoal.objective.trim()) {
      throw new GoalProgressIpcHandlerError(
        "NATIVE_GOAL_MISMATCH",
        "Current Session native Goal is unavailable or mismatched",
        revision,
      );
    }
    if (nativeGoal.objective.length > GOAL_NATIVE_OBJECTIVE_MAX_LENGTH) {
      throw new GoalProgressIpcHandlerError(
        "NATIVE_GOAL_OBJECTIVE_TOO_LONG",
        `Native Goal objective exceeds ${GOAL_NATIVE_OBJECTIVE_MAX_LENGTH} characters`,
        revision,
      );
    }
    return nativeGoal;
  }

  async readNativeGoal(
    threadId: string,
    revision: number | null = null,
  ): Promise<TrustedNativeGoal | null> {
    try {
      return await this.#resolveNativeGoal(threadId);
    } catch (error) {
      throw new GoalProgressIpcHandlerError(
        "NATIVE_GOAL_READ_UNAVAILABLE",
        "Could not read the current Session native Goal",
        revision,
        undefined,
        error,
      );
    }
  }

  async contractForWrite(
    identity: RuntimeIdentity,
    contract: GoalContractAny | null,
    revision: number | null,
    trustedNativeGoal?: TrustedNativeGoal | null,
  ): Promise<GoalContract | null> {
    if (!contract) {
      return null;
    }
    if (contract.schemaVersion === 2) {
      return contract;
    }
    const nativeGoal =
      trustedNativeGoal === undefined
        ? await this.readNativeGoal(identity.threadId, revision)
        : trustedNativeGoal;
    const migrated = migrateGoalContractV1ToV2({
      contract,
      identity,
      nativeGoal,
    });
    if (!migrated.ok) {
      throw new GoalProgressIpcHandlerError(migrated.code, migrated.message, revision);
    }
    const migrateKey = hashGoalProgressIdentity(`${identity.threadId}:${contract.revision}`);
    const persisted = await this.#store.persistMigrated(migrated.contract, {
      eventId: `evt-migrate-${migrateKey}`,
      requestId: `req-migrate-${migrateKey}`,
      turnId: identity.turnId,
      occurredAt: new Date().toISOString(),
      source: "system",
    });
    if (persisted.contract.schemaVersion !== 2) {
      throw new GoalProgressIpcHandlerError(
        "REBIND_REQUIRED",
        "Migrated Contract is not schema v2",
        revision,
      );
    }
    return persisted.contract;
  }
}
