import { z } from "zod";

export * from "./goal-contract.js";
export * from "./release-version.js";
export * from "./renderer-events.js";
export * from "./ui-preference.js";
export * from "./update-state.js";

const nonEmptyRuntimeField = z.string().trim().min(1);

export const GOAL_PROGRESS_RUNTIME_PROOF_VERSION = 2 as const;

export const RuntimeContextSchema = z
  .object({
    hookSessionId: nonEmptyRuntimeField,
    turnId: nonEmptyRuntimeField,
    model: nonEmptyRuntimeField,
    cwd: nonEmptyRuntimeField,
  })
  .strict();

export const RuntimeContextArgumentSchema = RuntimeContextSchema.describe(
  "禁止手填。此字段只能由 Codex PreToolUse Hook 注入。",
);

export type RuntimeContext = z.infer<typeof RuntimeContextSchema>;

export const RuntimeIdentitySchema = z
  .object({
    sessionTreeId: nonEmptyRuntimeField,
    threadId: nonEmptyRuntimeField,
    turnId: nonEmptyRuntimeField,
    model: nonEmptyRuntimeField,
    cwd: nonEmptyRuntimeField,
  })
  .strict();

export type RuntimeIdentity = z.infer<typeof RuntimeIdentitySchema>;

export const RuntimeProofSchema = z
  .object({
    version: z.literal(GOAL_PROGRESS_RUNTIME_PROOF_VERSION),
    toolUseId: nonEmptyRuntimeField,
    issuedAtMs: z.number().int().nonnegative(),
    nonce: z.string().regex(/^[0-9a-f]{32}$/),
    signature: z.string().regex(/^[0-9a-f]{64}$/),
  })
  .strict();

export const RuntimeProofArgumentSchema = RuntimeProofSchema.describe(
  "禁止手填。此证明只能由受信任的 Codex PreToolUse Hook 生成。",
);

export type RuntimeProof = z.infer<typeof RuntimeProofSchema>;

export const ThreadGoalStatusSchema = z.enum([
  "active",
  "paused",
  "blocked",
  "usageLimited",
  "budgetLimited",
  "complete",
]);

export const ThreadGoalObjectiveSchema = z
  .string()
  .trim()
  .min(1, "Goal objective must not be blank");

export const ThreadGoalSchema = z
  .object({
    threadId: z.string().trim().min(1),
    objective: ThreadGoalObjectiveSchema,
    status: ThreadGoalStatusSchema,
    tokenBudget: z.number().int().nonnegative().nullable().optional(),
    tokensUsed: z.number().int().nonnegative(),
    timeUsedSeconds: z.number().int().nonnegative(),
    createdAt: z.number().int().nonnegative(),
    updatedAt: z.number().int().nonnegative(),
  })
  .strict();

export const ThreadGoalGetResponseSchema = z
  .object({
    goal: ThreadGoalSchema.nullable(),
  })
  .strict();

export const ThreadGoalSetResponseSchema = z
  .object({
    goal: ThreadGoalSchema,
  })
  .strict();

export type ThreadGoal = z.infer<typeof ThreadGoalSchema>;

export const TokenUsageBreakdownSchema = z.object({
  inputTokens: z.number().int().nonnegative(),
  cachedInputTokens: z.number().int().nonnegative(),
  outputTokens: z.number().int().nonnegative(),
  reasoningOutputTokens: z.number().int().nonnegative(),
  totalTokens: z.number().int().nonnegative(),
  cacheWriteInputTokens: z.number().int().nonnegative().optional(),
});

export const ThreadTokenUsageSchema = z.object({
  total: TokenUsageBreakdownSchema,
  last: TokenUsageBreakdownSchema,
  modelContextWindow: z.number().int().positive().nullable().optional(),
});

export const ThreadTokenUsageUpdatedNotificationSchema = z.object({
  threadId: z.string().min(1),
  turnId: z.string().min(1),
  tokenUsage: ThreadTokenUsageSchema,
});

export type ThreadTokenUsageUpdatedNotification = z.infer<
  typeof ThreadTokenUsageUpdatedNotificationSchema
>;

const NativeGoalTokenUsageAvailableSchema = z
  .object({
    schemaVersion: z.literal(1),
    availability: z.literal("available"),
    source: z.literal("native-goal"),
    threadId: z.string().min(1),
    tokensUsed: z.number().int().nonnegative(),
    inputTokens: z.number().int().nonnegative().optional(),
    outputTokens: z.number().int().nonnegative().optional(),
    tokenBudget: z.number().int().nonnegative().nullable(),
    goalUpdatedAt: z.number().int().nonnegative(),
  })
  .strict()
  .superRefine((usage, context) => {
    if ((usage.inputTokens === undefined) !== (usage.outputTokens === undefined)) {
      context.addIssue({
        code: "custom",
        message: "inputTokens and outputTokens must be provided together",
      });
    }
  });

const NativeGoalTokenUsageUnavailableSchema = z
  .object({
    schemaVersion: z.literal(1),
    availability: z.literal("unavailable"),
    source: z.literal("unavailable"),
    threadId: z.string().min(1),
    reason: z.enum(["goal-not-found", "thread-mismatch", "read-failed"]),
  })
  .strict();

export const NativeGoalTokenUsageSchema = z.discriminatedUnion("availability", [
  NativeGoalTokenUsageAvailableSchema,
  NativeGoalTokenUsageUnavailableSchema,
]);

export type NativeGoalTokenUsage = z.infer<typeof NativeGoalTokenUsageSchema>;
export type ThreadGoalObjective = z.infer<typeof ThreadGoalObjectiveSchema>;
export type ThreadGoalStatus = z.infer<typeof ThreadGoalStatusSchema>;

interface RuntimeProofOptions {
  readonly nowMs?: number;
  readonly nonce?: string;
}

const RUNTIME_PROOF_MAX_AGE_MS = 30_000;
const RUNTIME_PROOF_MAX_FUTURE_SKEW_MS = 5_000;

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function hexToBytes(value: string): Uint8Array {
  const bytes = new Uint8Array(value.length / 2);
  for (let index = 0; index < bytes.length; index += 1) {
    bytes[index] = Number.parseInt(value.slice(index * 2, index * 2 + 2), 16);
  }
  return bytes;
}

function randomNonce(): string {
  const bytes = new Uint8Array(16);
  globalThis.crypto.getRandomValues(bytes);
  return bytesToHex(bytes);
}

function proofPayload(context: RuntimeContext, proof: Omit<RuntimeProof, "signature">): string {
  return JSON.stringify({
    version: proof.version,
    hookSessionId: context.hookSessionId,
    turnId: context.turnId,
    model: context.model,
    cwd: context.cwd,
    toolUseId: proof.toolUseId,
    issuedAtMs: proof.issuedAtMs,
    nonce: proof.nonce,
  });
}

async function importHmacKey(secret: Uint8Array): Promise<CryptoKey> {
  const secretCopy = Uint8Array.from(secret);
  return globalThis.crypto.subtle.importKey(
    "raw",
    secretCopy.buffer,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"],
  );
}

export async function issueRuntimeProof(
  contextInput: RuntimeContext,
  toolUseId: string,
  secret: Uint8Array,
  options: RuntimeProofOptions = {},
): Promise<RuntimeProof> {
  const context = RuntimeContextSchema.parse(contextInput);
  const unsignedProof = RuntimeProofSchema.omit({ signature: true }).parse({
    version: GOAL_PROGRESS_RUNTIME_PROOF_VERSION,
    toolUseId,
    issuedAtMs: options.nowMs ?? Date.now(),
    nonce: options.nonce ?? randomNonce(),
  });
  const key = await importHmacKey(secret);
  const signature = await globalThis.crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(proofPayload(context, unsignedProof)),
  );
  return RuntimeProofSchema.parse({
    ...unsignedProof,
    signature: bytesToHex(new Uint8Array(signature)),
  });
}

export async function verifyRuntimeProof(
  contextInput: RuntimeContext,
  proofInput: RuntimeProof,
  secret: Uint8Array,
  nowMs = Date.now(),
): Promise<boolean> {
  const context = RuntimeContextSchema.safeParse(contextInput);
  const proof = RuntimeProofSchema.safeParse(proofInput);
  if (!context.success || !proof.success) {
    return false;
  }
  const ageMs = nowMs - proof.data.issuedAtMs;
  if (ageMs > RUNTIME_PROOF_MAX_AGE_MS || ageMs < -RUNTIME_PROOF_MAX_FUTURE_SKEW_MS) {
    return false;
  }

  const { signature, ...unsignedProof } = proof.data;
  const key = await importHmacKey(secret);
  return globalThis.crypto.subtle.verify(
    "HMAC",
    key,
    Uint8Array.from(hexToBytes(signature)).buffer,
    new TextEncoder().encode(proofPayload(context.data, unsignedProof)),
  );
}
