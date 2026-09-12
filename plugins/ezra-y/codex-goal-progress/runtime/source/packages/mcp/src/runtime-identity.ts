import { createHash } from "node:crypto";
import type { RequestHandlerExtra } from "@modelcontextprotocol/sdk/shared/protocol.js";
import type { ServerNotification, ServerRequest } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { RuntimeContextSchema, RuntimeProofSchema } from "../../contracts/src/index.js";
import {
  type CodexRequestIdentity,
  CodexRequestIdentitySchema,
  type GoalProgressIpcAuthorization,
  GoalProgressMcpToolNameSchema,
} from "../../ipc/src/index.js";

// The launcher supplies the installation identity; request arguments never choose it.
const EXPECTED_PLUGIN_ID = `codex-goal-progress@${
  process.env.GOAL_PROGRESS_PLUGIN_MARKETPLACE?.trim() || "codex-goal-progress-local"
}`;
const boundedId = z.string().trim().min(1).max(512);
const boundedModel = z.string().trim().min(1).max(256);
const boundedCwd = z.string().trim().min(1).max(4_096);
const looseRecordSchema = z.record(z.string(), z.unknown());
const turnMetadataSchema = z
  .object({
    session_id: boundedId,
    thread_id: boundedId,
    turn_id: boundedId,
    model: boundedModel,
    thread_source: boundedId,
    cwd: boundedCwd.optional(),
    subagent_kind: z.unknown().optional(),
    agentRole: z.unknown().optional(),
    agent_role: z.unknown().optional(),
  })
  .passthrough();
const requestMetadataSchema = z
  .object({
    threadId: boundedId,
    callId: boundedId,
    plugin_id: boundedId.optional(),
    "x-codex-turn-metadata": turnMetadataSchema,
  })
  .passthrough();

export type GoalProgressMcpRequestExtra = Pick<
  RequestHandlerExtra<ServerRequest, ServerNotification>,
  "_meta"
>;

export type RuntimeIdentityErrorCode =
  | "CODEX_REQUEST_IDENTITY_CONFLICT"
  | "CODEX_REQUEST_METADATA_REQUIRED"
  | "CODEX_REQUEST_THREAD_UNTRUSTED"
  | "HOOK_CONTEXT_REQUIRED";

export type TrustedToolAuthorization =
  | {
      readonly ok: true;
      readonly source: "hook" | "request-metadata";
      readonly auth: GoalProgressIpcAuthorization;
      readonly sessionId: string;
      readonly turnId: string;
      readonly callId: string;
      readonly occurredAtMs: number;
    }
  | {
      readonly ok: false;
      readonly code: RuntimeIdentityErrorCode;
    };

interface RuntimeIdentityDiagnostic {
  readonly durationMs: number;
  readonly hookContextPresent: boolean;
  readonly hookProofPresent: boolean;
  readonly metadataPresent: boolean;
  readonly metadataValid: boolean;
  readonly requestMetaKeys: readonly string[];
  readonly result: "hook" | "request-metadata" | RuntimeIdentityErrorCode;
  readonly threadIdsMatch: boolean | null;
  readonly threadKey: string | null;
  readonly toolName: string;
  readonly turnKey: string | null;
  readonly turnMetadataKeys: readonly string[];
}

export interface RuntimeIdentityResolverDependencies {
  readonly now?: () => number;
  readonly recordDiagnostic?: (diagnostic: RuntimeIdentityDiagnostic) => void;
}

type ParsedRequestMetadata =
  | {
      readonly ok: true;
      readonly identity: CodexRequestIdentity;
    }
  | {
      readonly ok: false;
      readonly code:
        | "CODEX_REQUEST_IDENTITY_CONFLICT"
        | "CODEX_REQUEST_METADATA_REQUIRED"
        | "CODEX_REQUEST_THREAD_UNTRUSTED";
    };

function shortHash(value: string | undefined): string | null {
  return value ? createHash("sha256").update(value).digest("hex").slice(0, 12) : null;
}

function record(value: unknown): Record<string, unknown> | null {
  const parsed = looseRecordSchema.safeParse(value);
  return parsed.success ? parsed.data : null;
}

function sortedKeys(value: unknown): readonly string[] {
  return Object.keys(record(value) ?? {}).sort();
}

function stringField(value: unknown, field: string): string | undefined {
  const candidate = record(value)?.[field];
  return typeof candidate === "string" && candidate.trim() ? candidate : undefined;
}

function hasAgentMarker(value: unknown): boolean {
  return typeof value === "string"
    ? value.trim().length > 0
    : value !== undefined && value !== null;
}

function parseRequestMetadata(extra: GoalProgressMcpRequestExtra): ParsedRequestMetadata {
  const parsed = requestMetadataSchema.safeParse(extra._meta);
  if (!parsed.success) {
    return { ok: false, code: "CODEX_REQUEST_METADATA_REQUIRED" };
  }
  const turnMetadata = parsed.data["x-codex-turn-metadata"];
  if (
    parsed.data.threadId !== turnMetadata.thread_id ||
    turnMetadata.session_id !== turnMetadata.thread_id ||
    (parsed.data.plugin_id !== undefined && parsed.data.plugin_id !== EXPECTED_PLUGIN_ID)
  ) {
    return { ok: false, code: "CODEX_REQUEST_IDENTITY_CONFLICT" };
  }
  if (
    turnMetadata.thread_source !== "user" ||
    hasAgentMarker(turnMetadata.subagent_kind) ||
    hasAgentMarker(turnMetadata.agentRole) ||
    hasAgentMarker(turnMetadata.agent_role)
  ) {
    return { ok: false, code: "CODEX_REQUEST_THREAD_UNTRUSTED" };
  }
  return {
    ok: true,
    identity: CodexRequestIdentitySchema.parse({
      threadId: parsed.data.threadId,
      sessionId: turnMetadata.session_id,
      turnId: turnMetadata.turn_id,
      callId: parsed.data.callId,
      model: turnMetadata.model,
      threadSource: turnMetadata.thread_source,
      ...(turnMetadata.cwd === undefined ? {} : { cwd: turnMetadata.cwd }),
      ...(parsed.data.plugin_id === undefined ? {} : { pluginId: parsed.data.plugin_id }),
    }),
  };
}

function hookIdentityMatchesMetadata(
  runtimeContext: z.infer<typeof RuntimeContextSchema>,
  runtimeProof: z.infer<typeof RuntimeProofSchema>,
  metadata: Extract<ParsedRequestMetadata, { readonly ok: true }>,
): boolean {
  const requestIdentity = metadata.identity;
  return (
    runtimeContext.hookSessionId === requestIdentity.threadId &&
    runtimeContext.hookSessionId === requestIdentity.sessionId &&
    runtimeContext.turnId === requestIdentity.turnId &&
    runtimeContext.model === requestIdentity.model &&
    runtimeProof.toolUseId === requestIdentity.callId &&
    (requestIdentity.cwd === undefined || runtimeContext.cwd === requestIdentity.cwd)
  );
}

function defaultRecordDiagnostic(diagnostic: RuntimeIdentityDiagnostic): void {
  process.stderr.write(
    `${JSON.stringify({ level: "info", event: "mcp.runtime-identity", ...diagnostic })}\n`,
  );
}

export function resolveTrustedToolAuthorization(
  toolName: string,
  input: {
    readonly _runtimeContext?: unknown;
    readonly _runtimeProof?: unknown;
  },
  extra: GoalProgressMcpRequestExtra,
  dependencies: RuntimeIdentityResolverDependencies = {},
): TrustedToolAuthorization {
  const startedAt = Date.now();
  const now = dependencies.now ?? Date.now;
  const requestMeta = record(extra._meta);
  const turnMetadata = record(requestMeta?.["x-codex-turn-metadata"]);
  const metadata = parseRequestMetadata(extra);
  const hookContextPresent = input._runtimeContext !== undefined;
  const hookProofPresent = input._runtimeProof !== undefined;
  const hookContext = RuntimeContextSchema.safeParse(input._runtimeContext);
  const hookProof = RuntimeProofSchema.safeParse(input._runtimeProof);
  const metadataThreadId = stringField(turnMetadata, "thread_id");
  const metadataTurnId = stringField(turnMetadata, "turn_id");
  const recordDiagnostic = dependencies.recordDiagnostic ?? defaultRecordDiagnostic;
  const finish = (result: TrustedToolAuthorization): TrustedToolAuthorization => {
    if (extra._meta !== undefined || !result.ok) {
      recordDiagnostic({
        durationMs: Date.now() - startedAt,
        hookContextPresent,
        hookProofPresent,
        metadataPresent: extra._meta !== undefined,
        metadataValid: metadata.ok,
        requestMetaKeys: sortedKeys(extra._meta),
        result: result.ok ? result.source : result.code,
        threadIdsMatch:
          requestMeta && metadataThreadId
            ? stringField(requestMeta, "threadId") === metadataThreadId
            : null,
        threadKey: shortHash(
          metadata.ok
            ? metadata.identity.threadId
            : hookContext.success
              ? hookContext.data.hookSessionId
              : metadataThreadId,
        ),
        toolName,
        turnKey: shortHash(
          metadata.ok
            ? metadata.identity.turnId
            : hookContext.success
              ? hookContext.data.turnId
              : metadataTurnId,
        ),
        turnMetadataKeys: sortedKeys(requestMeta?.["x-codex-turn-metadata"]),
      });
    }
    return result;
  };

  const parsedToolName = GoalProgressMcpToolNameSchema.safeParse(toolName);
  if (!parsedToolName.success) {
    return finish({ ok: false, code: "CODEX_REQUEST_METADATA_REQUIRED" });
  }

  if (hookContextPresent || hookProofPresent) {
    if (!hookContext.success || !hookProof.success) {
      return finish({ ok: false, code: "HOOK_CONTEXT_REQUIRED" });
    }
    if (extra._meta !== undefined) {
      if (!metadata.ok) {
        return finish(metadata);
      }
      if (!hookIdentityMatchesMetadata(hookContext.data, hookProof.data, metadata)) {
        return finish({ ok: false, code: "CODEX_REQUEST_IDENTITY_CONFLICT" });
      }
    }
    return finish({
      ok: true,
      source: "hook",
      auth: {
        kind: "hook-proof",
        runtimeContext: hookContext.data,
        runtimeProof: hookProof.data,
      },
      sessionId: hookContext.data.hookSessionId,
      turnId: hookContext.data.turnId,
      callId: hookProof.data.toolUseId,
      occurredAtMs: hookProof.data.issuedAtMs,
    });
  }

  if (!metadata.ok) {
    return finish(metadata);
  }
  return finish({
    ok: true,
    source: "request-metadata",
    auth: {
      kind: "codex-request",
      identity: metadata.identity,
      toolName: parsedToolName.data,
    },
    sessionId: metadata.identity.threadId,
    turnId: metadata.identity.turnId,
    callId: metadata.identity.callId,
    occurredAtMs: now(),
  });
}
