/**
 * IAP Verification Service
 *
 * Abstraction over ArmorIQ IAP backend operations:
 *  - verifyStep:    POST /iap/verify-step
 *  - verifyWithCsrg: POST /verify/action (CSRG Merkle proof)
 *  - createAuditLog: POST /iap/audit
 *
 * Ported from ArmorClaw's IAPVerificationService (iap-verfication.service.ts).
 */

import {
  buildAuthHeaders,
  isPlainObject,
  parseStepIndex,
  postJson,
  readString
} from "./common.mjs";
import { createAuditWal } from "./audit-wal.mjs";

// Shared WAL instance per dataDir. The MCP server, hook handlers, and any
// fire-and-forget background flusher all enqueue to the same on-disk JSONL
// so the audit pipeline is crash-safe and concurrent-safe.
const walCache = new Map();
function getAuditWal(config) {
  const key = config.dataDir;
  let wal = walCache.get(key);
  if (!wal) {
    wal = createAuditWal({ dataDir: config.dataDir });
    walCache.set(key, wal);
  }
  return wal;
}

/**
 * Create an IAP service instance from config.
 */
export function createIapService(config) {
  const backendEndpoint = config.backendEndpoint || config.verifyStepEndpoint?.replace(/\/iap\/verify-step$/, "") || "";
  const csrgEndpoint = config.csrgEndpoint || config.iapEndpoint || "";
  const timeoutMs = config.timeoutMs || 8000;
  const headers = buildAuthHeaders(config);

  return {
    /**
     * Verify a tool execution step with the IAP backend.
     * Equivalent to ArmorClaw IAPVerificationService.verifyStep()
     */
    async verifyStep(intentTokenRaw, csrgProofs, toolName) {
      const endpoint = config.verifyStepEndpoint;
      if (!endpoint || !config.csrgVerifyEnabled) {
        return { skipped: true };
      }

      const { token, tokenObj } = getTokenForVerification(intentTokenRaw);
      if (!token) {
        return { skipped: false, allowed: false, reason: "ArmorIQ intent token missing" };
      }

      const payload = { token };
      if (csrgProofs?.path) {
        payload.path = csrgProofs.path;
        const stepMatch = csrgProofs.path.match(/\/steps\/\[(\d+)\]/);
        if (stepMatch) {
          payload.step_index = Number.parseInt(stepMatch[1] || "0", 10);
        }
      }
      if (toolName) {
        payload.tool_name = toolName;
      }
      if (Array.isArray(csrgProofs?.proof)) {
        payload.proof = csrgProofs.proof;
      }
      if (csrgProofs?.valueDigest) {
        payload.context = {
          csrg_value_digest: csrgProofs.valueDigest,
          proof_source: "client"
        };
      }

      const response = await postJson(endpoint, payload, headers, timeoutMs);
      if (!response.ok && !isPlainObject(response.data)) {
        throw new Error(
          response.text || `IAP verify-step failed with status ${response.status}`
        );
      }

      const data = isPlainObject(response.data) ? response.data : {};
      const tokenRaw =
        typeof data.intentTokenRaw === "string"
          ? data.intentTokenRaw
          : typeof data.tokenRaw === "string"
            ? data.tokenRaw
            : isPlainObject(data.token)
              ? JSON.stringify(data.token)
              : undefined;
      const parsedFromResponse = tokenRaw ? extractPlanFromResponse(tokenRaw) : null;
      const fallbackPlan = isPlainObject(tokenObj?.plan)
        ? tokenObj.plan
        : isPlainObject(tokenObj?.rawToken?.plan)
          ? tokenObj.rawToken.plan
          : undefined;
      const stepIndex =
        parseStepIndex(data?.step?.step_index) ??
        parseStepIndex(data?.execution_state?.current_step) ??
        parseStepIndexFromPath(csrgProofs?.path) ??
        undefined;

      return {
        skipped: false,
        allowed: data.allowed !== false,
        reason: typeof data.reason === "string" ? data.reason : "",
        tokenRaw,
        plan: isPlainObject(data.plan) ? data.plan : parsedFromResponse?.plan || fallbackPlan,
        expiresAt: Number.isFinite(data.expiresAt) ? data.expiresAt : parsedFromResponse?.expiresAt,
        stepIndex
      };
    },

    /**
     * Verify action directly with CSRG service using Merkle proof.
     * Equivalent to ArmorClaw IAPVerificationService.verifyWithCsrg()
     */
    async verifyWithCsrg(path, value, proof, token, context) {
      if (!config.csrgVerifyEnabled) {
        throw new Error("CSRG verification is disabled");
      }

      const payload = { path, value, proof, token, context };
      const response = await postJson(
        `${csrgEndpoint}/verify/action`,
        payload,
        { "Content-Type": "application/json" },
        Math.min(timeoutMs, 15000)
      );

      if (response.ok && response.data) {
        return response.data;
      }

      if (response.data) {
        return {
          allowed: false,
          reason:
            response.data.reason ||
            `CSRG verification failed: ${response.text || "unknown error"}`
        };
      }

      return {
        allowed: false,
        reason: response.text
          ? `CSRG verification failed: ${response.text}`
          : `CSRG verification failed with status ${response.status}`
      };
    },

    /**
     * Create an audit log entry in the IAP service.
     * Equivalent to ArmorClaw IAPVerificationService.createAuditLog()
     */
    async createAuditLog(dto) {
      const response = await postJson(
        `${backendEndpoint}/iap/audit`,
        dto,
        headers,
        timeoutMs
      );

      if (!response.ok || !response.data) {
        const message = response.text
          ? `IAP audit creation failed: ${response.text}`
          : `IAP audit creation failed with status ${response.status}`;
        throw new Error(message);
      }

      return response.data;
    },

    /**
     * Enqueue an audit DTO to the local WAL. Returns immediately after the
     * disk append (~1-2ms). A background flusher in policy-mcp.mjs drains
     * the WAL in batches and POSTs to /iap/audit. Fire-and-forget callers
     * use this to keep hook latency low.
     */
    async enqueueAudit(dto) {
      const wal = getAuditWal(config);
      await wal.appendLine(dto);
    },

    /**
     * Ship a batch of audit rows via POST /iap/audit/batch (one HTTP call
     * for N rows, ~N× faster than per-row POSTs). Matches armorClaude's
     * createAuditLogBatch — same backend endpoint, same payload shape.
     *
     * Failures throw — caller should NOT advance the WAL offset on failure
     * so the next tick retries the same rows. Backend idempotency
     * (planId, to_hash unique) keeps retries safe.
     */
    async shipAuditBatch(rows) {
      if (!Array.isArray(rows) || rows.length === 0) {
        return { written: 0, failures: [] };
      }
      const response = await postJson(
        `${backendEndpoint}/iap/audit/batch`,
        { rows },
        headers,
        timeoutMs
      );
      if (!response.ok || !response.data) {
        const message = response.text
          ? `IAP audit batch failed: ${response.text}`
          : `IAP audit batch failed with status ${response.status}`;
        throw new Error(message);
      }
      return response.data;
    },

    csrgProofsRequired() {
      return Boolean(config.requireCsrgProofs);
    },

    csrgVerifyIsEnabled() {
      return Boolean(config.csrgVerifyEnabled);
    }
  };
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

function getTokenForVerification(intentTokenRaw) {
  if (typeof intentTokenRaw !== "string") {
    return { token: "", tokenObj: null };
  }
  try {
    const parsed = JSON.parse(intentTokenRaw);
    if (isPlainObject(parsed)) {
      const jwtToken = readString(parsed.jwtToken) || readString(parsed.jwt_token);
      if (jwtToken) {
        return { token: jwtToken, tokenObj: parsed };
      }
      return { token: intentTokenRaw, tokenObj: parsed };
    }
    return { token: intentTokenRaw, tokenObj: null };
  } catch {
    return { token: intentTokenRaw, tokenObj: null };
  }
}

function extractPlanFromResponse(tokenRaw) {
  try {
    const parsed = JSON.parse(tokenRaw);
    if (!isPlainObject(parsed)) return null;
    const plan =
      isPlainObject(parsed.plan)
        ? parsed.plan
        : isPlainObject(parsed.rawToken?.plan)
          ? parsed.rawToken.plan
          : null;
    const expiresAt =
      Number.isFinite(parsed.expiresAt) ? parsed.expiresAt :
      Number.isFinite(parsed.token?.expires_at) ? parsed.token.expires_at :
      undefined;
    return plan ? { plan, expiresAt } : null;
  } catch {
    return null;
  }
}

function parseStepIndexFromPath(path) {
  if (!path) return null;
  const match = path.match(/\/steps\/\[(\d+)\]/);
  if (!match) return null;
  const index = Number.parseInt(match[1] || "", 10);
  return Number.isFinite(index) ? index : null;
}
