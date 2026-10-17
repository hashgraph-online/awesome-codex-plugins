import { createHash } from "node:crypto";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import {
  GOAL_NATIVE_OBJECTIVE_MAX_LENGTH,
  GOAL_PROGRESS_RELEASE_VERSION,
  GoalContractIdSchema,
  GoalObjectiveIdSchema,
  GoalObjectiveSchema,
  GoalProgressItemChangeSchema,
  GoalProgressPhaseSchema,
  GoalProgressSourceSchema,
  GoalProgressTargetIdSchema,
  type GoalProgressViewModel,
  GoalProgressViewModelSchema,
  RuntimeContextArgumentSchema,
  RuntimeProofArgumentSchema,
} from "../../contracts/src/index.js";
import { selectProgressTarget } from "../../contracts/src/progress-focus.js";
import {
  GOAL_PROGRESS_IPC_MAX_MESSAGE_BYTES,
  GoalProgressIpcClient,
  GoalProgressIpcClientError,
  type GoalProgressIpcRequestInput,
  goalProgressIpcRequestBytes,
} from "../../ipc/src/index.js";
import { resolveGoalProgressPaths } from "../../store/src/index.js";
import { completeInitialization, GoalProgressInitializeBusinessSchema } from "./initialization.js";
import {
  type GoalProgressMcpRequestExtra,
  type RuntimeIdentityErrorCode,
  resolveTrustedToolAuthorization,
  type TrustedToolAuthorization,
} from "./runtime-identity.js";
import { scheduleSourceUninstall } from "./uninstall.js";

export const GOAL_PROGRESS_INITIALIZE_TOOL_NAME = "goal_progress_initialize";
export const GOAL_PROGRESS_ACTIVATE_TOOL_NAME = "goal_progress_activate";
export const GOAL_PROGRESS_GET_TOOL_NAME = "goal_progress_get";
export const GOAL_PROGRESS_UPDATE_TOOL_NAME = "goal_progress_update";
export const GOAL_PROGRESS_RESCOPE_TOOL_NAME = "goal_progress_rescope";
export const GOAL_PROGRESS_SET_PHASE_TOOL_NAME = "goal_progress_set_phase";

const LooseJsonValueSchema = z.union([
  z.string(),
  z.number(),
  z.boolean(),
  z.null(),
  z.array(z.unknown()),
  z.record(z.string(), z.unknown()),
]);
const RuntimeContextTransportSchema = z
  .union([RuntimeContextArgumentSchema, LooseJsonValueSchema])
  .optional()
  .describe("禁止手填。此字段只能由 Codex PreToolUse Hook 注入。");
const RuntimeProofTransportSchema = z
  .union([RuntimeProofArgumentSchema, LooseJsonValueSchema])
  .optional()
  .describe("禁止手填。此证明只能由受信任的 Codex PreToolUse Hook 生成。");

function businessTransportField<T extends z.ZodType>(schema: T) {
  const { $schema: _schemaDeclaration, ...publishedSchema } = z.toJSONSchema(schema, {
    target: "draft-07",
    io: "input",
  });
  return z
    .union([schema, LooseJsonValueSchema])
    .optional()
    .meta({ anyOf: undefined, ...publishedSchema });
}

export const GoalProgressToolOutputSchema = z
  .object({
    ok: z.boolean(),
    code: z.string().trim().min(1).max(128),
    contractId: GoalContractIdSchema.nullable(),
    revision: z.number().int().nonnegative().nullable(),
    currentRevision: z.number().int().nonnegative().nullable(),
    overallPercent: z.number().int().min(0).max(100).nullable(),
    currentObjectiveId: GoalObjectiveIdSchema.nullable(),
    currentObjectivePercent: z.number().int().min(0).max(100).nullable(),
    summary: z.string().max(500),
    nextStep: z.string().max(200),
    duplicate: z.boolean().nullable(),
    progressAction: z.enum(["initialize", "get", "rescope-or-replace", "none"]).optional(),
    preparing: z.boolean().optional(),
    currentNativeGoal: z.string().trim().min(1).max(GOAL_NATIVE_OBJECTIVE_MAX_LENGTH).optional(),
  })
  .strict();

// Accept missing business fields so the handler can consume the one-time proof before rejecting them.
export const GoalProgressInitializeInputSchema = z
  .object({
    contractId: businessTransportField(GoalProgressInitializeBusinessSchema.shape.contractId),
    source: businessTransportField(GoalProgressSourceSchema),
    objectives: businessTransportField(z.array(GoalObjectiveSchema).max(100)),
    _runtimeContext: RuntimeContextTransportSchema,
    _runtimeProof: RuntimeProofTransportSchema,
  })
  .passthrough()
  .meta({ required: ["source", "objectives"] });

export const GoalProgressActivateInputSchema = z
  .object({
    _runtimeContext: RuntimeContextTransportSchema,
    _runtimeProof: RuntimeProofTransportSchema,
  })
  .strict();

export const GoalProgressGetInputSchema = z
  .object({
    _runtimeContext: RuntimeContextTransportSchema,
    _runtimeProof: RuntimeProofTransportSchema,
  })
  .passthrough();

export const GoalProgressUpdateInputSchema = z
  .object({
    contractId: businessTransportField(GoalContractIdSchema),
    expectedRevision: businessTransportField(z.number().int().nonnegative()),
    changes: businessTransportField(z.array(GoalProgressItemChangeSchema).min(1).max(500)),
    activeObjectiveId: businessTransportField(GoalObjectiveIdSchema.nullable()),
    correctionReason: businessTransportField(z.string().trim().min(1).max(2_000)),
    _runtimeContext: RuntimeContextTransportSchema,
    _runtimeProof: RuntimeProofTransportSchema,
  })
  .passthrough()
  .meta({ required: ["contractId", "expectedRevision", "changes"] });

export const GoalProgressRescopeInputSchema = z
  .object({
    contractId: businessTransportField(GoalContractIdSchema),
    expectedRevision: businessTransportField(z.number().int().nonnegative()),
    reason: businessTransportField(z.string().trim().min(1).max(2_000)),
    objectives: businessTransportField(z.array(GoalObjectiveSchema).max(100)),
    _runtimeContext: RuntimeContextTransportSchema,
    _runtimeProof: RuntimeProofTransportSchema,
  })
  .passthrough()
  .meta({ required: ["contractId", "expectedRevision", "reason", "objectives"] });

const GoalProgressModelPhaseSchema = GoalProgressPhaseSchema.exclude(["paused", "error"]);

export const GoalProgressSetPhaseInputSchema = z
  .object({
    contractId: businessTransportField(GoalContractIdSchema),
    expectedRevision: businessTransportField(z.number().int().nonnegative()),
    phase: businessTransportField(GoalProgressModelPhaseSchema),
    _runtimeContext: RuntimeContextTransportSchema,
    _runtimeProof: RuntimeProofTransportSchema,
  })
  .passthrough()
  .meta({ required: ["contractId", "expectedRevision", "phase"] });

const GoalProgressUpdateBusinessSchema = z
  .object({
    contractId: GoalContractIdSchema,
    expectedRevision: z.number().int().nonnegative(),
    changes: z.array(GoalProgressItemChangeSchema).min(1).max(500),
    activeObjectiveId: GoalObjectiveIdSchema.nullable().optional(),
    correctionReason: z.string().trim().min(1).max(2_000).optional(),
  })
  .strict();

const GoalProgressActivateBusinessSchema = z.object({}).strict();

const GoalProgressRescopeBusinessSchema = z
  .object({
    contractId: GoalContractIdSchema,
    expectedRevision: z.number().int().nonnegative(),
    reason: z.string().trim().min(1).max(2_000),
    objectives: z.array(GoalObjectiveSchema).max(100),
  })
  .strict();

const GoalProgressSetPhaseBusinessSchema = z
  .object({
    contractId: GoalContractIdSchema,
    expectedRevision: z.number().int().nonnegative(),
    phase: GoalProgressModelPhaseSchema,
  })
  .strict();

const EmptyBusinessSchema = z.object({}).strict();

function businessInput(input: Record<string, unknown>): Record<string, unknown> {
  const {
    _runtimeContext: _ignoredRuntimeContext,
    _runtimeProof: _ignoredRuntimeProof,
    ...business
  } = input;
  return business;
}

const IpcWriteResultSchema = z
  .object({
    viewModel: GoalProgressViewModelSchema,
    nextTargetId: GoalProgressTargetIdSchema.nullable(),
    duplicate: z.boolean(),
  })
  .strict();

const IpcLoadResultSchema = z
  .object({
    viewModel: GoalProgressViewModelSchema.nullable(),
    nextTargetId: GoalProgressTargetIdSchema.nullable(),
    eventCount: z.number().int().nonnegative(),
    previousContractId: GoalContractIdSchema.optional(),
    previousRevision: z.number().int().nonnegative().optional(),
    currentNativeGoal: z.string().trim().min(1).max(GOAL_NATIVE_OBJECTIVE_MAX_LENGTH).optional(),
  })
  .passthrough();

const IpcActivationResultSchema = z
  .object({
    progressAction: z.enum(["initialize", "get", "rescope-or-replace", "none"]),
    preparing: z.boolean(),
    code: z.string().trim().min(1).max(128),
    contractId: GoalContractIdSchema.nullable(),
    revision: z.number().int().nonnegative().nullable(),
    currentNativeGoal: z.string().trim().min(1).max(GOAL_NATIVE_OBJECTIVE_MAX_LENGTH).optional(),
  })
  .strict();

const RuntimeProofConsumeResultSchema = z.object({ valid: z.boolean() }).strict();

interface GoalProgressMcpServerOptions {
  readonly ipcClient?: GoalProgressIpcClient;
  readonly uninstall?: () => Promise<{ code: string; statusFile: string }>;
}

function truncateText(value: string, maximumLength: number): string {
  return value.length <= maximumLength
    ? value
    : `${value.slice(0, Math.max(0, maximumLength - 3))}...`;
}

function currentObjective(viewModel: GoalProgressViewModel) {
  return selectProgressTarget(viewModel.objectives) ?? null;
}

function progressOutput(viewModel?: GoalProgressViewModel) {
  const objective = viewModel ? currentObjective(viewModel) : null;
  return {
    overallPercent: viewModel?.overallPercent ?? null,
    currentObjectiveId: objective?.id ?? null,
    currentObjectivePercent: objective?.progressPercent ?? null,
  };
}

function compactSummary(viewModel: GoalProgressViewModel): string {
  const visible = viewModel.objectives
    .slice(0, 6)
    .map((objective) => `${objective.id}:${objective.progressPercent}%(${objective.status})`);
  const remaining = viewModel.objectives.length - visible.length;
  const objectives =
    remaining > 0 ? `${visible.join(", ")}; +${remaining} more` : visible.join(", ");
  const overall =
    viewModel.overallPercent === null
      ? "overall=unavailable"
      : `overall=${viewModel.overallPercent}%`;
  return truncateText(
    objectives
      ? `trackingPhase=${viewModel.trackingPhase}; ${overall}; ${objectives}`
      : `trackingPhase=${viewModel.trackingPhase}; ${overall}`,
    500,
  );
}

function successSummary(viewModel: GoalProgressViewModel): string {
  const details = compactSummary(viewModel);
  if (viewModel.trackingPhase === "preparing") {
    return truncateText(`Preparing Contract. ${details}`, 500);
  }
  if (viewModel.trackingPhase === "active") {
    return truncateText(`Contract active. ${details}`, 500);
  }
  return details;
}

function nextStep(viewModel: GoalProgressViewModel, nextTargetId: string | null): string {
  if (viewModel.trackingPhase === "preparing") {
    return "Finish checklist preparation.";
  }
  if (viewModel.trackingPhase === "paused") {
    return "Resume tracking when work continues.";
  }
  if (viewModel.trackingPhase === "error") {
    return "Run doctor before continuing.";
  }
  if (viewModel.trackingPhase === "completed") {
    return "Goal Progress is complete.";
  }
  if (viewModel.trackingPhase === "detached") {
    return "Tracking is detached; native Goal is unchanged.";
  }
  if (viewModel.trackingPhase === "blocked") {
    if (viewModel.blockedReason === "usage-limit") {
      return "Wait for Codex usage limits to reset.";
    }
    if (viewModel.blockedReason === "budget-limit") {
      return "Adjust or wait for the Goal token budget.";
    }
    return "Wait for or resolve the native Goal block.";
  }
  const objective = currentObjective(viewModel);
  if (
    nextTargetId &&
    objective &&
    (objective.status === "active" || objective.status === "pending")
  ) {
    return truncateText(`Continue ${nextTargetId}.`, 200);
  }
  if (objective?.status === "blocked") {
    return truncateText(`Resolve ${nextTargetId ?? objective.id}.`, 200);
  }
  return viewModel.finalVerificationPending
    ? "Complete the native Goal final verification."
    : "No remaining progress action.";
}

function toolContent(output: z.infer<typeof GoalProgressToolOutputSchema>) {
  return {
    content: [{ type: "text" as const, text: JSON.stringify(output) }],
    structuredContent: output,
    ...(!output.ok ? { isError: true as const } : {}),
  };
}

function runtimeContextError(
  code: RuntimeIdentityErrorCode | "HOOK_PROOF_INVALID" = "HOOK_CONTEXT_REQUIRED",
) {
  const message =
    code === "CODEX_REQUEST_METADATA_REQUIRED"
      ? {
          summary: "Trusted Codex request metadata is required when Hook identity is unavailable.",
          nextStep: "Reload the current task so Codex supplies complete MCP request metadata.",
        }
      : code === "CODEX_REQUEST_IDENTITY_CONFLICT"
        ? {
            summary: "Trusted request identity fields do not match.",
            nextStep: "Stop this tool call and reload the current task identity.",
          }
        : code === "CODEX_REQUEST_THREAD_UNTRUSTED"
          ? {
              summary: "Goal Progress only accepts a main user task.",
              nextStep: "Use Goal Progress from the main Codex task.",
            }
          : {
              summary: "Trusted Hook identity is required.",
              nextStep:
                "Reload the current task so Codex refreshes Goal Progress identity, then retry.",
            };
  return toolContent({
    ok: false,
    code,
    contractId: null,
    revision: null,
    currentRevision: null,
    ...progressOutput(),
    ...message,
    duplicate: null,
  });
}

type InputErrorCode =
  | "INVALID_ID"
  | "INVALID_STATUS"
  | "INVALID_CONTRIBUTION_TOTAL"
  | "IPC_MESSAGE_TOO_LARGE"
  | "INVALID_INPUT";

interface InputRejection {
  readonly code: InputErrorCode;
  readonly summary: string;
  readonly nextStep: string;
}

const INVALID_CONTRIBUTION_TOTAL_REJECTION: InputRejection = {
  code: "INVALID_CONTRIBUTION_TOTAL",
  summary: "Required objective contributions must total 10000.",
  nextStep: "Adjust contributionBps, then retry.",
};

const IPC_MESSAGE_TOO_LARGE_REJECTION: InputRejection = {
  code: "IPC_MESSAGE_TOO_LARGE",
  summary: "Goal Progress request exceeds the local IPC size limit.",
  nextStep: "Reduce checklist or evidence detail, then retry.",
};

function inputError(rejection: InputRejection) {
  return toolContent({
    ok: false,
    code: rejection.code,
    contractId: null,
    revision: null,
    currentRevision: null,
    ...progressOutput(),
    summary: rejection.summary,
    nextStep: rejection.nextStep,
    duplicate: null,
  });
}

function idCorrection(path: readonly PropertyKey[]): string {
  const field = path.at(-1);
  if (field === "contractId") {
    return "Initialize: omit contractId. Later writes: copy the returned contractId unchanged (gp_ prefix). A bare UUID is not a Contract ID.";
  }
  if (path.includes("evidence")) return "Use a non-empty evidence ID with at most 128 characters.";
  if (field === "targetId")
    return "Copy an existing target ID: C1 for an objective or C1.1 for a child item. Do not use a UUID.";
  if (path.includes("items"))
    return "Use the parent objective ID, a dot, then a positive integer: C1.1, C1.2. Keep IDs unchanged on later calls.";
  return "Use C followed by a positive integer: C1, C2. Keep existing IDs unchanged; do not use a UUID or the title.";
}

function inputRejection(error: z.ZodError): InputRejection {
  for (const issue of error.issues) {
    const field = issue.path.at(-1);
    if (field === "status" || field === "phase") {
      const path = issue.path.join(".");
      return {
        code: "INVALID_STATUS",
        summary: `Invalid status at ${path || "input"}.`,
        nextStep: "Use one of the status values in the tool schema.",
      };
    }
    if (
      field === "contractId" ||
      field === "targetId" ||
      field === "activeObjectiveId" ||
      field === "id"
    ) {
      const path = issue.path.join(".");
      return {
        code: "INVALID_ID",
        summary: `Invalid ID at ${path || "input"}.`,
        nextStep: idCorrection(issue.path),
      };
    }
  }
  const firstIssue = error.issues[0];
  const path = firstIssue?.path.join(".") || "input";
  return {
    code: "INVALID_INPUT",
    summary: truncateText(
      `Invalid input at ${path}: ${firstIssue?.message ?? "invalid value"}`,
      500,
    ),
    nextStep: "Fix that field using the tool schema, then retry.",
  };
}

function contributionTotalIsValid(
  objectives: readonly {
    readonly status: string;
    readonly contributionBps: number;
    readonly requirement?: "required" | "optional";
  }[],
): boolean {
  return (
    objectives.length > 0 &&
    objectives
      .filter(
        (objective) => objective.status !== "cancelled" && objective.requirement !== "optional",
      )
      .reduce((total, objective) => total + objective.contributionBps, 0) === 10_000
  );
}

function requestError(error: unknown) {
  if (error instanceof GoalProgressIpcClientError) {
    const viewModel = error.currentViewModel;
    return toolContent({
      ok: false,
      code: error.code,
      contractId: viewModel?.contractId ?? null,
      revision: null,
      currentRevision: viewModel?.revision ?? error.revision,
      ...progressOutput(viewModel),
      summary:
        error.code === "REVISION_CONFLICT" && viewModel
          ? compactSummary(viewModel)
          : truncateText(error.message, 500),
      nextStep: errorNextStep(error.code),
      duplicate: null,
    });
  }
  const diagnostic =
    error instanceof Error
      ? { name: error.name, message: truncateText(error.message, 500) }
      : { name: "UnknownError", message: "Unknown MCP failure" };
  process.stderr.write(
    `${JSON.stringify({ level: "error", event: "mcp.internal-error", ...diagnostic })}\n`,
  );
  return toolContent({
    ok: false,
    code: "MCP_INTERNAL_ERROR",
    contractId: null,
    revision: null,
    currentRevision: null,
    ...progressOutput(),
    summary: "Goal Progress MCP returned an internal error.",
    nextStep: "Check Helper status with doctor.",
    duplicate: null,
  });
}

function errorNextStep(code: string): string {
  switch (code) {
    case "REVISION_CONFLICT":
      return "Retry with currentRevision after reviewing this latest summary.";
    case "TARGET_NOT_FOUND":
      return "Call goal_progress_get and use an existing target ID.";
    case "INVALID_TRANSITION":
      return "Use an allowed phase transition.";
    case "CORRECTION_REASON_REQUIRED":
      return "Add correctionReason, then retry the progress decrease.";
    case "CONTRACT_MISMATCH":
    case "THREAD_MISMATCH":
      return "Call goal_progress_get in the current Goal session.";
    case "STORE_NOT_INITIALIZED":
      return "Call goal_progress_initialize after the checklist is ready.";
    case "STORE_ALREADY_INITIALIZED":
      return "Call goal_progress_get and reuse the existing Contract.";
    case "ACTIVATION_CANCELLED":
      return "Wait until the user explicitly selects Goal Progress again.";
    case "RUNTIME_PROOF_INVALID":
    case "HOOK_PROOF_INVALID":
      return "Reload the current task so Codex refreshes Goal Progress identity, then retry.";
    case "IPC_UNAVAILABLE":
    case "IPC_CLOSED":
    case "IPC_TIMEOUT":
      return "Run doctor and start the Helper before retrying.";
    case "IPC_MESSAGE_TOO_LARGE":
      return "Reduce checklist or evidence detail, then retry.";
    case "CLIENT_RECONNECT_REQUIRED":
      return "Start a new Codex session or restart Codex so Goal Progress MCP loads the current release.";
    case "CURRENT_THREAD_NOT_FOUND":
    case "CURRENT_THREAD_AMBIGUOUS":
    case "CURRENT_THREAD_UNAVAILABLE":
      return "Stay in the current Goal thread and retry after the host identity is unique.";
    case "CODEX_REQUEST_IDENTITY_CONFLICT":
    case "CODEX_REQUEST_REPLAYED":
    case "CODEX_REQUEST_THREAD_UNTRUSTED":
      return "Stop this tool call and retry from the same main Codex task.";
    case "CODEX_REQUEST_THREAD_UNAVAILABLE":
      return "Retry after Codex can read this task.";
    case "NATIVE_GOAL_READ_UNAVAILABLE":
      return "Run doctor and verify the current native Goal, then retry.";
    case "NATIVE_GOAL_DETACHED":
      return "The native Goal ended or is missing; do not keep writing the previous Contract.";
    case "NATIVE_GOAL_REPLACED":
      return "The native Goal was replaced. Rebind only if the new Goal should be tracked.";
    case "NATIVE_GOAL_OBJECTIVE_CHANGED":
      return "The native Goal objective changed. Rescope or rebind, then retry.";
    case "NATIVE_GOAL_OBJECTIVE_TOO_LONG":
      return "Shorten the native Goal objective to 4000 characters, then retry.";
    case "REBIND_REQUIRED":
      return "Stay in the current Goal thread until it can be uniquely bound, then retry.";
    case "INTERNAL_ERROR":
      return "Run doctor and inspect Helper logs before changing the request.";
    default:
      return "Use the error code and summary to fix the request, then retry.";
  }
}

async function consumeProofForRejectedInput(
  client: GoalProgressIpcClient,
  authorization: Extract<TrustedToolAuthorization, { readonly ok: true }>,
  rejection: InputRejection,
) {
  if (authorization.auth.kind !== "hook-proof") {
    return inputError(rejection);
  }
  const { runtimeContext, runtimeProof } = authorization.auth;
  try {
    const response = await client.request({
      method: "runtime-proof.consume",
      params: { runtimeContext, runtimeProof },
    });
    const result = RuntimeProofConsumeResultSchema.parse(response.result);
    return result.valid ? inputError(rejection) : runtimeContextError("HOOK_PROOF_INVALID");
  } catch (error) {
    return requestError(error);
  }
}

async function rejectOversizedRequest(
  client: GoalProgressIpcClient,
  request: GoalProgressIpcRequestInput,
  authorization: Extract<TrustedToolAuthorization, { readonly ok: true }>,
) {
  if (goalProgressIpcRequestBytes(request) <= GOAL_PROGRESS_IPC_MAX_MESSAGE_BYTES) {
    return undefined;
  }
  return consumeProofForRejectedInput(client, authorization, IPC_MESSAGE_TOO_LARGE_REJECTION);
}

function toolRequestIds(toolUseId: string): { eventId: string; requestId: string } {
  const digest = createHash("sha256").update(toolUseId).digest("hex");
  return {
    eventId: `evt-${digest}`,
    requestId: `req-${digest}`,
  };
}

function successContent(
  viewModel: GoalProgressViewModel,
  nextTargetId: string | null,
  duplicate: boolean | null,
) {
  return toolContent({
    ok: true,
    code: "OK",
    contractId: viewModel.contractId,
    revision: viewModel.revision,
    currentRevision: null,
    ...progressOutput(viewModel),
    summary: successSummary(viewModel),
    nextStep: nextStep(viewModel, nextTargetId),
    duplicate,
  });
}

function activationNextStep(result: z.infer<typeof IpcActivationResultSchema>): string {
  if (result.code === "NATIVE_GOAL_REQUIRED") {
    return "Create a native Goal with Codex, then call goal_progress_activate again.";
  }
  if (result.progressAction === "rescope-or-replace") {
    return "Compare the existing Checklist with the current native Goal. Rescope only affected objectives, or initialize a new Contract for a major change.";
  }
  return result.progressAction === "get"
    ? "Call goal_progress_get and continue with the existing Contract."
    : "Call goal_progress_initialize with source and objectives. Omit contractId; use C1, C2 for objectives and C1.1 for child items.";
}

export function createGoalProgressMcpServer(options: GoalProgressMcpServerOptions = {}): McpServer {
  const server = new McpServer({
    name: "codex-goal-progress",
    version: GOAL_PROGRESS_RELEASE_VERSION,
  });
  let ipcClient = options.ipcClient;
  const getIpcClient = (): GoalProgressIpcClient => {
    if (!ipcClient) {
      const configuredRoot = process.env.GOAL_PROGRESS_ROOT;
      const { helperSocketPath } = resolveGoalProgressPaths(
        configuredRoot === undefined ? {} : { root: resolve(configuredRoot) },
      );
      ipcClient = new GoalProgressIpcClient(helperSocketPath, {
        clientKind: "mcp",
      });
    }
    return ipcClient;
  };
  const resolveToolIdentity = (
    toolName: string,
    input: {
      readonly _runtimeContext?: unknown;
      readonly _runtimeProof?: unknown;
    },
    extra: GoalProgressMcpRequestExtra,
  ) => resolveTrustedToolAuthorization(toolName, input, extra);

  server.registerTool(
    GOAL_PROGRESS_ACTIVATE_TOOL_NAME,
    {
      title: "Plan Goal Progress Activation",
      description:
        "Internal first step after explicit Goal Progress Skill invocation. Plan activation only. Do not create or change a native Goal or Contract.",
      inputSchema: GoalProgressActivateInputSchema,
      outputSchema: GoalProgressToolOutputSchema,
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
      },
    },
    async (input, extra) => {
      const identity = await resolveToolIdentity(GOAL_PROGRESS_ACTIVATE_TOOL_NAME, input, extra);
      if (!identity.ok) {
        return runtimeContextError(identity.code);
      }
      const business = GoalProgressActivateBusinessSchema.safeParse(businessInput(input));
      if (!business.success) {
        return consumeProofForRejectedInput(
          getIpcClient(),
          identity,
          inputRejection(business.error),
        );
      }
      try {
        const response = await getIpcClient().request({
          method: "activation.plan",
          params: {
            auth: identity.auth,
          },
        });
        const result = IpcActivationResultSchema.parse(response.result);
        return toolContent({
          ok: true,
          code: result.code,
          contractId: result.contractId,
          revision: result.revision,
          currentRevision: null,
          ...progressOutput(),
          summary:
            result.code === "NATIVE_GOAL_REQUIRED"
              ? "A native Goal is required before Goal Progress can start."
              : result.code === "NATIVE_GOAL_UPDATED"
                ? "The native Goal changed. Goal Progress is waiting for Checklist adjustment."
                : result.progressAction === "get"
                  ? "The current native Goal already has an active Goal Progress Contract."
                  : "The current native Goal is ready for Goal Progress initialization.",
          nextStep: activationNextStep(result),
          duplicate: null,
          progressAction: result.progressAction,
          preparing: result.preparing,
          ...(result.currentNativeGoal ? { currentNativeGoal: result.currentNativeGoal } : {}),
        });
      } catch (error) {
        return requestError(error);
      }
    },
  );

  server.registerTool(
    GOAL_PROGRESS_INITIALIZE_TOOL_NAME,
    {
      title: "Initialize Goal Progress",
      description:
        "Create the first Contract or a replacement after a trusted major Goal change. Do not duplicate an unchanged Goal Contract.",
      inputSchema: GoalProgressInitializeInputSchema,
      outputSchema: GoalProgressToolOutputSchema,
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
      },
    },
    async (input, extra) => {
      const identity = await resolveToolIdentity(GOAL_PROGRESS_INITIALIZE_TOOL_NAME, input, extra);
      if (!identity.ok) {
        return runtimeContextError(identity.code);
      }
      const business = GoalProgressInitializeBusinessSchema.safeParse(businessInput(input));
      if (!business.success) {
        return consumeProofForRejectedInput(
          getIpcClient(),
          identity,
          inputRejection(business.error),
        );
      }
      if (!contributionTotalIsValid(business.data.objectives)) {
        return consumeProofForRejectedInput(
          getIpcClient(),
          identity,
          INVALID_CONTRIBUTION_TOTAL_REJECTION,
        );
      }
      try {
        const ids = toolRequestIds(identity.callId);
        const request = {
          method: "store.initialize",
          params: {
            initialization: completeInitialization(business.data, identity),
            metadata: {
              ...ids,
              turnId: identity.turnId,
              occurredAt: new Date(identity.occurredAtMs).toISOString(),
              source: "model",
            },
            auth: identity.auth,
          },
        } satisfies GoalProgressIpcRequestInput;
        const client = getIpcClient();
        const oversized = await rejectOversizedRequest(client, request, identity);
        if (oversized) {
          return oversized;
        }
        const response = await client.request(request);
        const result = IpcWriteResultSchema.parse(response.result);
        return successContent(result.viewModel, result.nextTargetId, result.duplicate);
      } catch (error) {
        return requestError(error);
      }
    },
  );

  server.registerTool(
    GOAL_PROGRESS_GET_TOOL_NAME,
    {
      title: "Get Goal Progress",
      description:
        "Read current progress before a write or after a conflict. Do not use it to estimate progress.",
      inputSchema: GoalProgressGetInputSchema,
      outputSchema: GoalProgressToolOutputSchema,
      annotations: {
        readOnlyHint: true,
        idempotentHint: true,
        openWorldHint: false,
      },
    },
    async (input, extra) => {
      const identity = await resolveToolIdentity(GOAL_PROGRESS_GET_TOOL_NAME, input, extra);
      if (!identity.ok) {
        return runtimeContextError(identity.code);
      }
      const business = EmptyBusinessSchema.safeParse(businessInput(input));
      if (!business.success) {
        return consumeProofForRejectedInput(
          getIpcClient(),
          identity,
          inputRejection(business.error),
        );
      }
      try {
        const response = await getIpcClient().request({
          method: "store.load",
          params: {
            sessionId: identity.sessionId,
            auth: identity.auth,
          },
        });
        const result = IpcLoadResultSchema.parse(response.result);
        if (!result.viewModel) {
          if (
            result.previousContractId &&
            result.previousRevision !== undefined &&
            result.currentNativeGoal
          ) {
            return toolContent({
              ok: true,
              code: "NATIVE_GOAL_UPDATED",
              contractId: result.previousContractId,
              revision: result.previousRevision,
              currentRevision: null,
              ...progressOutput(),
              summary:
                "The native Goal changed. Goal Progress is waiting for Checklist adjustment.",
              nextStep:
                "Compare the existing Checklist with the current native Goal. Rescope only affected objectives, or initialize a new Contract for a major change.",
              duplicate: null,
              currentNativeGoal: result.currentNativeGoal,
            });
          }
          return toolContent({
            ok: true,
            code: "NOT_INITIALIZED",
            contractId: null,
            revision: null,
            currentRevision: null,
            ...progressOutput(),
            summary: "Goal Progress is not initialized.",
            nextStep: "Call goal_progress_initialize after the checklist is ready.",
            duplicate: null,
          });
        }
        return successContent(result.viewModel, result.nextTargetId, null);
      } catch (error) {
        return requestError(error);
      }
    },
  );

  server.registerTool(
    GOAL_PROGRESS_UPDATE_TOOL_NAME,
    {
      title: "Update Goal Progress",
      description:
        "Update existing checklist states after work is verified. Do not change scope or weights.",
      inputSchema: GoalProgressUpdateInputSchema,
      outputSchema: GoalProgressToolOutputSchema,
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
      },
    },
    async (input, extra) => {
      const identity = await resolveToolIdentity(GOAL_PROGRESS_UPDATE_TOOL_NAME, input, extra);
      if (!identity.ok) {
        return runtimeContextError(identity.code);
      }
      const business = GoalProgressUpdateBusinessSchema.safeParse(businessInput(input));
      if (!business.success) {
        return consumeProofForRejectedInput(
          getIpcClient(),
          identity,
          inputRejection(business.error),
        );
      }
      try {
        const ids = toolRequestIds(identity.callId);
        const request = {
          method: "store.apply",
          params: {
            command: {
              type: "update-items",
              contractId: business.data.contractId,
              sessionId: identity.sessionId,
              expectedRevision: business.data.expectedRevision,
              ...ids,
              turnId: identity.turnId,
              occurredAt: new Date(identity.occurredAtMs).toISOString(),
              source: "model",
              changes: business.data.changes,
              ...(business.data.activeObjectiveId === undefined
                ? {}
                : { activeObjectiveId: business.data.activeObjectiveId }),
              ...(business.data.correctionReason === undefined
                ? {}
                : { correctionReason: business.data.correctionReason }),
            },
            auth: identity.auth,
          },
        } satisfies GoalProgressIpcRequestInput;
        const client = getIpcClient();
        const oversized = await rejectOversizedRequest(client, request, identity);
        if (oversized) {
          return oversized;
        }
        const response = await client.request(request);
        const result = IpcWriteResultSchema.parse(response.result);
        return successContent(result.viewModel, result.nextTargetId, result.duplicate);
      } catch (error) {
        return requestError(error);
      }
    },
  );

  server.registerTool(
    GOAL_PROGRESS_RESCOPE_TOOL_NAME,
    {
      title: "Rescope Goal Progress",
      description:
        "Replace checklist and weights after scope changes. Do not use for ordinary status updates.",
      inputSchema: GoalProgressRescopeInputSchema,
      outputSchema: GoalProgressToolOutputSchema,
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
      },
    },
    async (input, extra) => {
      const identity = await resolveToolIdentity(GOAL_PROGRESS_RESCOPE_TOOL_NAME, input, extra);
      if (!identity.ok) {
        return runtimeContextError(identity.code);
      }
      const business = GoalProgressRescopeBusinessSchema.safeParse(businessInput(input));
      if (!business.success) {
        return consumeProofForRejectedInput(
          getIpcClient(),
          identity,
          inputRejection(business.error),
        );
      }
      if (!contributionTotalIsValid(business.data.objectives)) {
        return consumeProofForRejectedInput(
          getIpcClient(),
          identity,
          INVALID_CONTRIBUTION_TOTAL_REJECTION,
        );
      }
      try {
        const ids = toolRequestIds(identity.callId);
        const request = {
          method: "store.apply",
          params: {
            command: {
              type: "rescope",
              contractId: business.data.contractId,
              sessionId: identity.sessionId,
              expectedRevision: business.data.expectedRevision,
              ...ids,
              turnId: identity.turnId,
              occurredAt: new Date(identity.occurredAtMs).toISOString(),
              source: "model",
              reason: business.data.reason,
              objectives: business.data.objectives,
            },
            auth: identity.auth,
          },
        } satisfies GoalProgressIpcRequestInput;
        const client = getIpcClient();
        const oversized = await rejectOversizedRequest(client, request, identity);
        if (oversized) {
          return oversized;
        }
        const response = await client.request(request);
        const result = IpcWriteResultSchema.parse(response.result);
        return successContent(result.viewModel, result.nextTargetId, result.duplicate);
      } catch (error) {
        return requestError(error);
      }
    },
  );

  server.registerTool(
    GOAL_PROGRESS_SET_PHASE_TOOL_NAME,
    {
      title: "Set Goal Progress Phase",
      description:
        "Set preparing, active, or completed. Do not report task failures as plugin errors; native pause is read-only. Use native Goal for blockers.",
      inputSchema: GoalProgressSetPhaseInputSchema,
      outputSchema: GoalProgressToolOutputSchema,
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
      },
    },
    async (input, extra) => {
      const identity = await resolveToolIdentity(GOAL_PROGRESS_SET_PHASE_TOOL_NAME, input, extra);
      if (!identity.ok) {
        return runtimeContextError(identity.code);
      }
      const business = GoalProgressSetPhaseBusinessSchema.safeParse(businessInput(input));
      if (!business.success) {
        return consumeProofForRejectedInput(
          getIpcClient(),
          identity,
          inputRejection(business.error),
        );
      }
      try {
        const ids = toolRequestIds(identity.callId);
        const request = {
          method: "store.apply",
          params: {
            command: {
              type: "set-phase",
              contractId: business.data.contractId,
              sessionId: identity.sessionId,
              expectedRevision: business.data.expectedRevision,
              ...ids,
              turnId: identity.turnId,
              occurredAt: new Date(identity.occurredAtMs).toISOString(),
              source: "model",
              phase: business.data.phase,
            },
            auth: identity.auth,
          },
        } satisfies GoalProgressIpcRequestInput;
        const client = getIpcClient();
        const oversized = await rejectOversizedRequest(client, request, identity);
        if (oversized) {
          return oversized;
        }
        const response = await client.request(request);
        const result = IpcWriteResultSchema.parse(response.result);
        return successContent(result.viewModel, result.nextTargetId, result.duplicate);
      } catch (error) {
        return requestError(error);
      }
    },
  );

  if (options.uninstall || process.env.GOAL_PROGRESS_SOURCE_RUNTIME === "1") {
    server.registerTool(
      "goal_progress_uninstall",
      {
        title: "Uninstall Goal Progress",
        description:
          "Only call when the user explicitly asks to uninstall Goal Progress. Removes this source plugin, its Helper and all its checklist data. Native Codex Goals and other plugins are kept. This is not a task progress action.",
        inputSchema: z.object({}).strict(),
        annotations: {
          readOnlyHint: false,
          destructiveHint: true,
          idempotentHint: true,
          openWorldHint: false,
        },
      },
      async () => {
        try {
          const result = await (options.uninstall ?? scheduleSourceUninstall)();
          return {
            content: [
              {
                type: "text" as const,
                text: JSON.stringify({
                  ok: true,
                  ...result,
                  summary: "Uninstall started. This acknowledgement is not a completion result.",
                }),
              },
            ],
          };
        } catch (error) {
          return {
            isError: true,
            content: [
              {
                type: "text" as const,
                text: error instanceof Error ? error.message : "UNINSTALL_START_FAILED",
              },
            ],
          };
        }
      },
    );
  }

  return server;
}

export async function runMcpServer(): Promise<void> {
  const server = createGoalProgressMcpServer();
  await server.connect(new StdioServerTransport());
}

const entryPath = process.argv[1];
if (entryPath && import.meta.url === pathToFileURL(resolve(entryPath)).href) {
  runMcpServer().catch((error: unknown) => {
    const message = error instanceof Error ? error.stack : "GOAL_PROGRESS_MCP_FAILED";
    process.stderr.write(`${message ?? "GOAL_PROGRESS_MCP_FAILED"}\n`);
    process.exitCode = 1;
  });
}
