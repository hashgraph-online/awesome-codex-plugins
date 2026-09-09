import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { z } from "zod";
import {
  type RuntimeContext,
  RuntimeContextSchema,
  type RuntimeProof,
  RuntimeProofSchema,
} from "../../packages/contracts/src/index.js";
import {
  type GoalProgressActivationResumeResult,
  GoalProgressActivationResumeResultSchema,
  GoalProgressIpcClient,
} from "../../packages/ipc/src/index.js";
import { resolveGoalProgressPaths } from "../../packages/store/src/index.js";

export const GOAL_PROGRESS_TOOL_PATTERN =
  "^(?:goal_progress_|.*[^A-Za-z0-9]goal_progress[^A-Za-z0-9]+goal_progress_)(?:activate|initialize|get|update|rescope|set_phase)$";
export const GOAL_PROGRESS_TOOL_MATCHER = new RegExp(GOAL_PROGRESS_TOOL_PATTERN);
export const GOAL_PROGRESS_POST_TOOL_PATTERN = "^update_goal$";
export const GOAL_PROGRESS_HOOK_STDIN_PROTOCOL_VERSION = 1 as const;
export const GOAL_PROGRESS_HOOK_EVENT_POLICY = Object.freeze({
  SessionStart: Object.freeze({
    timeoutSeconds: 3,
    async: false,
    failureMode: "fail-open",
  }),
  PreToolUse: Object.freeze({
    timeoutSeconds: 1,
    async: false,
    failureMode: "deny-own-tool",
  }),
  PostToolUse: Object.freeze({
    timeoutSeconds: 2,
    async: true,
    failureMode: "fail-open",
  }),
});
export const GOAL_PROGRESS_RESUME_CONTEXT =
  "Goal Progress is active for this session. Continue automatically: load Goal Progress tools with tool_search if deferred, call goal_progress_get before writes, and do not ask the user to invoke the Skill again.";
const GOAL_PROGRESS_AUDIT_CLIENT_TIMEOUT_MS = 100;
const GOAL_PROGRESS_AUDIT_MAX_WAIT_MS = 150;
export const GOAL_PROGRESS_RESUME_CLIENT_TIMEOUT_MS = 25;
export const GOAL_PROGRESS_RESUME_DIAGNOSTIC_MAX_WAIT_MS = 50;
export const GOAL_PROGRESS_RESUME_RETRY_DELAYS_MS = [0, 100, 250, 500, 900] as const;
export const GOAL_PROGRESS_RESUME_MAX_BLOCKING_MS = 2_400;

const commonHookFields = {
  session_id: z.string().trim().min(1),
  cwd: z.string().trim().min(1),
  model: z.string().trim().min(1),
};

const SessionStartSchema = z
  .object({
    ...commonHookFields,
    hook_event_name: z.literal("SessionStart"),
    source: z.enum(["startup", "resume", "clear", "compact"]),
  })
  .passthrough();

const PreToolUseSchema = z
  .object({
    ...commonHookFields,
    hook_event_name: z.literal("PreToolUse"),
    turn_id: z.string().trim().min(1),
    tool_name: z.string().trim().min(1),
    tool_use_id: z.string().trim().min(1),
    tool_input: z.record(z.string(), z.unknown()),
  })
  .passthrough();

const PostToolUseSchema = z
  .object({
    ...commonHookFields,
    hook_event_name: z.literal("PostToolUse"),
    turn_id: z.string().trim().min(1),
    tool_name: z.string().trim().min(1),
    tool_use_id: z.string().trim().min(1),
    tool_input: z.unknown(),
    tool_response: z.unknown(),
  })
  .passthrough();

const HookEnvelopeSchema = z
  .object({
    hook_event_name: z.string(),
  })
  .passthrough();

const PreToolUseEnvelopeSchema = z
  .object({
    hook_event_name: z.literal("PreToolUse"),
    tool_name: z.string(),
  })
  .passthrough();

const PostToolUseEnvelopeSchema = z
  .object({
    hook_event_name: z.literal("PostToolUse"),
    tool_name: z.string(),
  })
  .passthrough();

export type HookAuditEntry =
  | {
      readonly event: "NativeGoalCompleted";
      readonly hookSessionId: string;
      readonly turnId: string;
      readonly model: string;
      readonly cwd: string;
      readonly toolUseId: string;
    }
  | {
      readonly event: "ResumeTemporarilyUnavailable";
      readonly hookSessionId: string;
      readonly reasonCode: string;
    };

interface HookDependencies {
  readonly appendAuditEntry: (entry: HookAuditEntry) => Promise<void>;
  readonly createRuntimeProof: (
    context: RuntimeContext,
    toolUseId: string,
  ) => Promise<RuntimeProof>;
  readonly resumeSession: (input: {
    readonly hookSessionId: string;
    readonly cwd: string;
    readonly model: string;
  }) => Promise<GoalProgressActivationResumeResult>;
  readonly sleep: (delayMs: number) => Promise<void>;
}

interface PreToolUseOutput {
  readonly hookSpecificOutput: {
    readonly hookEventName: "PreToolUse";
    readonly permissionDecision: "allow" | "deny";
    readonly permissionDecisionReason?: string;
    readonly updatedInput?: Record<string, unknown>;
  };
}

interface SessionStartOutput {
  readonly hookSpecificOutput: {
    readonly hookEventName: "SessionStart";
    readonly additionalContext: string;
  };
}

type HookOutput = PreToolUseOutput | SessionStartOutput;

const resumeOutput: SessionStartOutput = {
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: GOAL_PROGRESS_RESUME_CONTEXT,
  },
};

const invalidContextOutput: PreToolUseOutput = {
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason:
      "GOAL_PROGRESS_HOOK_CONTEXT_INVALID: current session identity is unavailable.",
  },
};

const unavailableProofOutput: PreToolUseOutput = {
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason:
      "GOAL_PROGRESS_HOOK_PROOF_UNAVAILABLE: runtime identity could not be signed.",
  },
};

const unavailableHookOutput: PreToolUseOutput = {
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason:
      "GOAL_PROGRESS_HOOK_UNAVAILABLE: runtime identity could not be prepared.",
  },
};

function helperSocketPath(): string {
  const configuredRoot = process.env.GOAL_PROGRESS_ROOT;
  return resolveGoalProgressPaths(
    configuredRoot === undefined ? {} : { root: resolve(configuredRoot) },
  ).helperSocketPath;
}

function helperClient(): GoalProgressIpcClient {
  return new GoalProgressIpcClient(helperSocketPath(), {
    clientKind: "hook",
  });
}

function auditHelperClient(): GoalProgressIpcClient {
  return new GoalProgressIpcClient(helperSocketPath(), {
    clientKind: "hook",
    timeoutMs: GOAL_PROGRESS_AUDIT_CLIENT_TIMEOUT_MS,
  });
}

function resumeHelperClient(): GoalProgressIpcClient {
  return new GoalProgressIpcClient(helperSocketPath(), {
    clientKind: "hook",
    timeoutMs: GOAL_PROGRESS_RESUME_CLIENT_TIMEOUT_MS,
  });
}

export async function appendAuditEntryToHelper(
  entry: HookAuditEntry,
  client: GoalProgressIpcClient = auditHelperClient(),
): Promise<void> {
  await client.request({
    method: "hook.audit",
    params: entry,
  });
}

async function appendAuditEntryBestEffort(
  entry: HookAuditEntry,
  appendAuditEntry: HookDependencies["appendAuditEntry"],
  maxWaitMs = GOAL_PROGRESS_AUDIT_MAX_WAIT_MS,
): Promise<void> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const deadline = new Promise<void>((resolveDeadline) => {
    timer = setTimeout(resolveDeadline, maxWaitMs);
  });
  try {
    await Promise.race([appendAuditEntry(entry).catch(() => undefined), deadline]);
  } finally {
    if (timer !== undefined) {
      clearTimeout(timer);
    }
  }
}

async function createRuntimeProofForHelper(
  context: RuntimeContext,
  toolUseId: string,
): Promise<RuntimeProof> {
  const response = await helperClient().request({
    method: "runtime-proof.issue",
    params: { runtimeContext: context, toolUseId },
  });
  if (
    response.result === null ||
    typeof response.result !== "object" ||
    !("runtimeProof" in response.result)
  ) {
    throw new Error("GOAL_PROGRESS_HOOK_PROOF_RESPONSE_INVALID");
  }
  return RuntimeProofSchema.parse(response.result.runtimeProof);
}

function resumeFailureCode(error: unknown): string {
  if (
    error !== null &&
    typeof error === "object" &&
    "code" in error &&
    typeof error.code === "string" &&
    error.code.trim()
  ) {
    return error.code.slice(0, 128);
  }
  return "IPC_UNAVAILABLE";
}

export async function resumeSessionInHelper(
  input: {
    readonly hookSessionId: string;
    readonly cwd: string;
    readonly model: string;
  },
  client: GoalProgressIpcClient = resumeHelperClient(),
): Promise<GoalProgressActivationResumeResult> {
  try {
    const response = await client.request({
      method: "activation.resume",
      params: input,
    });
    return GoalProgressActivationResumeResultSchema.parse(response.result);
  } catch (error) {
    return {
      status: "temporarily_unavailable",
      reasonCode: resumeFailureCode(error),
    };
  }
}

async function restoreSessionActivation(
  input: {
    readonly hookSessionId: string;
    readonly cwd: string;
    readonly model: string;
  },
  resumeSession: HookDependencies["resumeSession"],
  sleep: HookDependencies["sleep"],
  deadlineAtMs: number,
): Promise<GoalProgressActivationResumeResult> {
  let lastResult: GoalProgressActivationResumeResult = {
    status: "temporarily_unavailable",
    reasonCode: "IPC_UNAVAILABLE",
  };
  for (const delayMs of GOAL_PROGRESS_RESUME_RETRY_DELAYS_MS) {
    const remainingBeforeDelayMs =
      deadlineAtMs - Date.now() - GOAL_PROGRESS_RESUME_DIAGNOSTIC_MAX_WAIT_MS;
    if (
      remainingBeforeDelayMs < GOAL_PROGRESS_RESUME_CLIENT_TIMEOUT_MS ||
      delayMs + GOAL_PROGRESS_RESUME_CLIENT_TIMEOUT_MS > remainingBeforeDelayMs
    ) {
      break;
    }
    if (delayMs > 0) {
      await sleep(delayMs);
    }
    if (
      deadlineAtMs - Date.now() - GOAL_PROGRESS_RESUME_DIAGNOSTIC_MAX_WAIT_MS <
      GOAL_PROGRESS_RESUME_CLIENT_TIMEOUT_MS
    ) {
      break;
    }
    try {
      lastResult = await resumeSession(input);
    } catch (error) {
      lastResult = {
        status: "temporarily_unavailable",
        reasonCode: resumeFailureCode(error),
      };
    }
    if (lastResult.status !== "temporarily_unavailable") {
      return lastResult;
    }
  }
  return lastResult;
}

export async function handleHookInput(
  input: unknown,
  dependencies: Partial<HookDependencies> = {},
): Promise<HookOutput | undefined> {
  const envelope = HookEnvelopeSchema.safeParse(input);
  if (!envelope.success) {
    return undefined;
  }

  if (envelope.data.hook_event_name === "SessionStart") {
    const parsed = SessionStartSchema.safeParse(input);
    if (!parsed.success || parsed.data.source === "clear") {
      return undefined;
    }
    const resumeInput = {
      hookSessionId: parsed.data.session_id,
      cwd: parsed.data.cwd,
      model: parsed.data.model,
    };
    const deadlineAtMs = Date.now() + GOAL_PROGRESS_RESUME_MAX_BLOCKING_MS;
    const resumed = await restoreSessionActivation(
      resumeInput,
      dependencies.resumeSession ?? resumeSessionInHelper,
      dependencies.sleep ??
        ((delayMs) => new Promise((resolveDelay) => setTimeout(resolveDelay, delayMs))),
      deadlineAtMs,
    );
    if (resumed.status === "temporarily_unavailable") {
      const remainingMs = deadlineAtMs - Date.now();
      if (remainingMs > 0) {
        await appendAuditEntryBestEffort(
          {
            event: "ResumeTemporarilyUnavailable",
            hookSessionId: resumeInput.hookSessionId,
            reasonCode: resumed.reasonCode,
          },
          dependencies.appendAuditEntry ?? appendAuditEntryToHelper,
          Math.min(GOAL_PROGRESS_RESUME_DIAGNOSTIC_MAX_WAIT_MS, remainingMs),
        );
      }
    }
    return resumed.status === "active" ? resumeOutput : undefined;
  }

  if (envelope.data.hook_event_name === "PostToolUse") {
    const postToolEnvelope = PostToolUseEnvelopeSchema.safeParse(input);
    if (!postToolEnvelope.success) {
      return undefined;
    }

    const parsed = PostToolUseSchema.safeParse(input);
    if (!parsed.success) {
      return undefined;
    }

    if (postToolEnvelope.data.tool_name !== "update_goal") {
      return undefined;
    }
    const toolInput = z
      .object({
        status: z.literal("complete"),
      })
      .passthrough()
      .safeParse(parsed.data.tool_input);
    if (!toolInput.success) {
      return undefined;
    }
    await appendAuditEntryBestEffort(
      {
        event: "NativeGoalCompleted",
        hookSessionId: parsed.data.session_id,
        turnId: parsed.data.turn_id,
        model: parsed.data.model,
        cwd: parsed.data.cwd,
        toolUseId: parsed.data.tool_use_id,
      },
      dependencies.appendAuditEntry ?? appendAuditEntryToHelper,
    );
    return undefined;
  }

  if (envelope.data.hook_event_name !== "PreToolUse") {
    return undefined;
  }

  const preToolEnvelope = PreToolUseEnvelopeSchema.safeParse(input);
  if (
    !preToolEnvelope.success ||
    !GOAL_PROGRESS_TOOL_MATCHER.test(preToolEnvelope.data.tool_name)
  ) {
    return undefined;
  }

  const parsed = PreToolUseSchema.safeParse(input);
  if (!parsed.success) {
    return invalidContextOutput;
  }

  const runtimeContext = RuntimeContextSchema.safeParse({
    hookSessionId: parsed.data.session_id,
    turnId: parsed.data.turn_id,
    model: parsed.data.model,
    cwd: parsed.data.cwd,
  });
  if (!runtimeContext.success) {
    return invalidContextOutput;
  }

  let runtimeProof: RuntimeProof;
  try {
    runtimeProof = await (dependencies.createRuntimeProof ?? createRuntimeProofForHelper)(
      runtimeContext.data,
      parsed.data.tool_use_id,
    );
  } catch {
    return unavailableProofOutput;
  }

  return {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      updatedInput: {
        ...parsed.data.tool_input,
        _runtimeContext: runtimeContext.data,
        _runtimeProof: runtimeProof,
      },
    },
  };
}

async function readStandardInput(): Promise<string> {
  let input = "";
  for await (const chunk of process.stdin) {
    input += String(chunk);
  }
  return input;
}

export async function runHookCli(): Promise<void> {
  const rawInput = await readStandardInput();
  let input: unknown;
  try {
    input = JSON.parse(rawInput);
  } catch {
    return;
  }
  let output: HookOutput | undefined;
  try {
    output = await handleHookInput(input);
  } catch {
    const envelope = PreToolUseEnvelopeSchema.safeParse(input);
    output =
      envelope.success && GOAL_PROGRESS_TOOL_MATCHER.test(envelope.data.tool_name)
        ? unavailableHookOutput
        : undefined;
  }
  if (output) {
    process.stdout.write(JSON.stringify(output));
  }
}

const entryPath = process.argv[1];
if (entryPath && import.meta.url === pathToFileURL(resolve(entryPath)).href) {
  runHookCli().catch(() => undefined);
}
