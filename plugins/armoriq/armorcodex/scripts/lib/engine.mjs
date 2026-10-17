import { isPlainObject, normalizeToolName, nowEpochSeconds, redactSecrets, sanitizeParams } from "./common.mjs";
import { addPromptContext, blockPrompt, denyPermissionRequest, denyPreTool } from "./hook-output.mjs";
import {
  checkIntentTokenPlan,
  checkToolAgainstPlan,
  extractAllowedActions,
  findPlanStepIndices,
  getSessionTokenUsedStepIndices,
  parseCsrgProofHeaders,
  recordSessionTokenUsedStepIndices,
  requestIntent,
  resolveCsrgProofsFromToken,
  validateCsrgProofHeaders
} from "./intent.mjs";
import { createIapService } from "./iap-service.mjs";
import {
  applyPolicyCommand,
  computePolicyHash,
  evaluatePolicy,
  loadPolicyState,
  parsePolicyTextCommand
} from "./policy.mjs";
import { readJson } from "./fs-store.mjs";
import { unlink } from "node:fs/promises";
import path from "node:path";
import {
  getSession,
  loadRuntimeState,
  saveRuntimeState,
  upsertDiscoveredTool,
  upsertSession
} from "./runtime-state.mjs";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function shouldDeny(config) {
  return config.mode === "enforce";
}

function buildPolicyContextHints() {
  return "For policy changes call `policy_update` (mode: replace rewrites the full ruleset; empty rules clears policy).";
}

function actorCandidates(input) {
  const out = [];
  for (const key of ["session_id", "user_id", "actor_id", "cwd"]) {
    const value = input && typeof input[key] === "string" ? input[key].trim() : "";
    if (value) {
      out.push(value);
    }
  }
  return out;
}

function policyCommandLooksLikePrompt(prompt) {
  return typeof prompt === "string" && /^\s*policy\b/i.test(prompt);
}

function isPolicyUpdateAllowed(config, input) {
  if (!config.policyUpdateEnabled) {
    return { allowed: false, reason: "ArmorCodex policy updates disabled" };
  }
  const allowList = config.policyUpdateAllowList;
  if (!Array.isArray(allowList) || allowList.length === 0 || allowList.includes("*")) {
    return { allowed: true };
  }
  const candidates = actorCandidates(input);
  const allowed = candidates.some((entry) => allowList.includes(entry));
  return allowed
    ? { allowed: true }
    : {
        allowed: false,
        reason: "ArmorCodex policy update denied",
        candidates
      };
}

function mergeIntentIntoSession(session, intentResponse) {
  if (!intentResponse || intentResponse.skipped) {
    return session;
  }
  const next = { ...session };
  if (typeof intentResponse.tokenRaw === "string") {
    next.intentTokenRaw = intentResponse.tokenRaw;
  }
  if (intentResponse.plan && typeof intentResponse.plan === "object") {
    next.plan = intentResponse.plan;
    next.allowedActions = Array.from(extractAllowedActions(intentResponse.plan));
  }
  if (Number.isFinite(intentResponse.expiresAt)) {
    next.expiresAt = intentResponse.expiresAt;
  }
  return next;
}

function readIntentTokenRaw(input, session) {
  const candidates = [
    input.intentTokenRaw,
    input.intent_token_raw,
    input.intent_token,
    input.intentToken,
    session.intentTokenRaw
  ];
  for (const value of candidates) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  return "";
}

function denyOrAllow(config, reason) {
  if (shouldDeny(config)) {
    return denyPreTool(reason);
  }
  return null;
}

function debugLog(config, message) {
  if (config.debug) {
    process.stderr.write(`[armorcodex] ${message}\n`);
  }
}

/**
 * Pick the best matching step index in the plan for a given tool call.
 * Prefers a step that matches BOTH tool name and parameters, falls back to
 * tool name only, then to step 0. Used to populate audit log step_index so
 * the backend can advance plan execution state to 'completed'.
 */
function pickStepIndex(plan, toolName, toolInput) {
  if (!plan || typeof plan !== "object") return 0;
  const { matches, paramMatches } = findPlanStepIndices(plan, toolName, toolInput);
  if (paramMatches.length > 0) return paramMatches[0];
  if (matches.length > 0) return matches[0];
  return 0;
}

// ---------------------------------------------------------------------------
// SessionStart
// ---------------------------------------------------------------------------

export async function handleSessionStart(input, config) {
  const sessionId = typeof input.session_id === "string" ? input.session_id : "";
  if (!sessionId) return null;

  const runtimeState = await loadRuntimeState(config.runtimeFile);
  upsertSession(runtimeState, sessionId, {
    startedAt: nowEpochSeconds(),
    discoveredTools: []
  });
  await saveRuntimeState(config.runtimeFile, runtimeState);

  debugLog(config, `session started: ${sessionId}, mode=${config.mode}`);

  const modeLabel = config.mode === "enforce" ? "ENFORCING" : "MONITORING";
  const intentLabel = config.intentRequired ? "required" : "optional";
  return addPromptContext(
    `ArmorCodex active (${modeLabel}, intent=${intentLabel})`,
    "SessionStart"
  );
}

// ---------------------------------------------------------------------------
// UserPromptSubmit
// ---------------------------------------------------------------------------

export async function handleUserPromptSubmit(input, config) {
  const prompt = typeof input.prompt === "string" ? input.prompt : "";
  const sessionId = typeof input.session_id === "string" ? input.session_id : "";
  if (!prompt || !sessionId) {
    return null;
  }

  // --- Policy command handling ---
  if (policyCommandLooksLikePrompt(prompt)) {
    const allowed = isPolicyUpdateAllowed(config, input);
    if (!allowed.allowed) {
      return blockPrompt(allowed.reason || "ArmorCodex policy update denied");
    }
    const policyState = await loadPolicyState(config.policyFile);
    const command = parsePolicyTextCommand(prompt, policyState);
    const actor = actorCandidates(input)[0] || "unknown";
    const result = await applyPolicyCommand({
      policyFilePath: config.policyFile,
      state: policyState,
      command,
      actor
    });
    return blockPrompt(result.message);
  }

  // --- Store prompt in session ---
  const runtimeState = await loadRuntimeState(config.runtimeFile);
  upsertSession(runtimeState, sessionId, {
    lastPrompt: prompt,
    lastPromptAt: nowEpochSeconds()
  });
  await saveRuntimeState(config.runtimeFile, runtimeState);

  // --- Inject directive: tell Codex to register its intent plan ---
  // Codex will call the `register_intent_plan` MCP tool as its first action.
  // The MCP tool's inputSchema already describes the JSON shape, so we don't
  // duplicate it here — keeps the visible prompt context short.
  const parts = [];
  if (config.planningEnabled) {
    parts.push(
      "ArmorCodex active. Call `register_intent_plan` first; step `action` = tool name, `metadata.inputs` = `{}` matches by name only."
    );
  }
  if (config.contextHintsEnabled && config.policyUpdateEnabled) {
    parts.push(buildPolicyContextHints());
  }
  if (parts.length > 0) {
    return addPromptContext(parts.join("\n\n"));
  }
  return null;
}

// ---------------------------------------------------------------------------
// PreToolUse
// ---------------------------------------------------------------------------

export async function handlePreToolUse(input, config) {
  const sessionId = typeof input.session_id === "string" ? input.session_id : "";
  const toolName = typeof input.tool_name === "string" ? input.tool_name : "";
  const toolInput = sanitizeParams(input.tool_input, config.sanitize);
  if (!toolName) {
    // Missing tool_name on a PreToolUse event means the payload shape is
    // unexpected. Fail-closed in enforce mode instead of silently allowing.
    return denyOrAllow(config, "ArmorCodex: missing tool_name on PreToolUse");
  }

  // --- Whitelist: ArmorCodex's own MCP tools must never be blocked,
  //     otherwise the agent can't register a plan or read/update policy.
  //     Match the exact MCP prefix from .mcp.json (armorcodex-policy),
  //     not any suffix — an evil server called evil__policy_update would
  //     previously have been whitelisted. ---
  const norm = normalizeToolName(toolName);
  const armorTools = ["register_intent_plan", "policy_read", "policy_update"];
  // Codex MCP namespace is `mcp__<server>__` and the underlying MCP server name
  // can carry hyphens (`armorcodex-policy`) or be sanitized to underscores
  // (`armorcodex_policy`). Codex's TUI display also surfaces `<server>.<tool>`
  // in user-facing strings. Match all reasonable forms — but only accept names
  // anchored to our own server identifier so this can't whitelist a malicious
  // MCP server that happens to expose a same-named tool.
  const ARMOR_SERVER_RE = /(mcp__armorcodex[-_]policy__|armorcodex[-_]policy[._])/;
  if (
    armorTools.some(
      (t) =>
        norm === t ||
        (norm.endsWith(t) && ARMOR_SERVER_RE.test(norm))
    )
  ) {
    return null;
  }

  // --- Whitelist: Codex introspection / coordination tools that have
  //     no side effects on user files or systems. Blocking these makes the
  //     agent fight itself (e.g. ToolSearch is needed to fetch deferred MCP
  //     tool schemas before they can be called). ---
  const safeInternalTools = new Set([
    "toolsearch",
    "todowrite",
    "listmcpresourcestool",
    "readmcpresourcetool",
    "read",
    "grep",
    "glob",
    "websearch",
    "webfetch"
  ]);
  if (safeInternalTools.has(norm)) {
    return null;
  }

  // --- Consume pending plan from register_intent_plan MCP tool ---
  // Always consume if a pending file exists — the MCP handler only writes
  // it when Codex has registered a NEW plan, and stale plans must be
  // overwritten so each prompt gets its own plan boundary.
  // This load is reused for the rest of the PreToolUse handler instead of
  // reloading from disk below (fewer disk reads on the hot path).
  const runtimeState = await loadRuntimeState(config.runtimeFile);
  // Per-session plan file so concurrent Codex windows don't clobber each
  // other. Fall back to the legacy global path for installs that still have
  // a write from a pre-upgrade MCP server.
  const sessionPendingPath = sessionId
    ? path.join(config.dataDir, `pending-plan.${sessionId}.json`)
    : null;
  const legacyPendingPath = path.join(config.dataDir, "pending-plan.json");
  let pendingPath = sessionPendingPath;
  let pending = sessionPendingPath ? await readJson(sessionPendingPath, null) : null;
  if (!pending) {
    pending = await readJson(legacyPendingPath, null);
    if (pending) pendingPath = legacyPendingPath;
  }
  if (pending && (pending.tokenRaw || pending.plan)) {
    upsertSession(runtimeState, sessionId, {
      intentTokenRaw: pending.tokenRaw || "",
      plan: pending.plan,
      allowedActions: Array.isArray(pending.allowedActions) ? pending.allowedActions : [],
      expiresAt: pending.expiresAt,
      // Reset per-token execution tracking when a new plan replaces the old.
      intentExecution: undefined
    });
    await saveRuntimeState(config.runtimeFile, runtimeState);
    if (pendingPath) await unlink(pendingPath).catch(() => {});
    debugLog(config, "consumed pending plan from register_intent_plan");
  }

  // --- Static policy evaluation ---
  const policyState = await loadPolicyState(config.policyFile);

  // Crypto policy digest check (Phase 4 integration point)
  if (config.cryptoPolicyEnabled) {
    try {
      const { createCryptoPolicyService } = await import("./crypto-policy.mjs");
      const cryptoService = createCryptoPolicyService(config);
      const currentDigest = computePolicyHash(policyState.policy);
      const cachedState = await cryptoService.loadCachedState();
      if (cachedState?.policyDigest) {
        const check = cryptoService.verifyPolicyDigest(currentDigest, cachedState.policyDigest);
        if (!check.valid) {
          return denyOrAllow(config, `ArmorCodex crypto policy mismatch: ${check.reason}`);
        }
      }
    } catch (error) {
      debugLog(config, `crypto policy check error: ${error}`);
    }
  }

  const policyDecision = evaluatePolicy({
    policy: policyState.policy,
    toolName,
    toolParams: toolInput
  });
  if (!policyDecision.allowed) {
    return denyPreTool(policyDecision.reason || "ArmorCodex policy denied");
  }

  // --- Intent token verification ---
  // Reuse the runtimeState loaded above instead of re-reading from disk.
  const session = getSession(runtimeState, sessionId) || {};
  let intentTokenRaw = readIntentTokenRaw(input, session);
  let localPlan = session.plan;
  let localExpiresAt = session.expiresAt;
  let remoteAllowed = false;
  let tokenCheckMatched = false;
  let usedStepIndices =
    intentTokenRaw && localPlan
      ? getSessionTokenUsedStepIndices(session, intentTokenRaw)
      : undefined;

  // Proactive refresh: if the token is about to expire and we still have the
  // plan, re-issue silently so the user never sees a "token expired" deny in
  // the middle of a multi-step turn. If the refresh fails, flow falls through
  // to the existing expiry check below.
  const refreshThreshold = Number.isFinite(config.refreshThresholdSeconds)
    ? config.refreshThresholdSeconds
    : 30;
  if (
    intentTokenRaw &&
    isPlainObject(localPlan) &&
    Number.isFinite(localExpiresAt) &&
    localExpiresAt - nowEpochSeconds() < refreshThreshold &&
    (config.intentEndpoint || (config.useSdkIntent && config.apiKey))
  ) {
    try {
      const policyHash = computePolicyHash(policyState.policy);
      const refreshed = await requestIntent(config, {
        prompt: session.lastPrompt || `Refresh intent for ${toolName}`,
        plan: localPlan,
        session_id: sessionId,
        toolName,
        toolInput,
        policy_hash: policyHash,
        policy: policyState.policy,
        validitySeconds: config.validitySeconds,
        metadata: { source: "codex", trigger: "auto_refresh" }
      });
      if (!refreshed.skipped) {
        const merged = mergeIntentIntoSession(session, refreshed);
        upsertSession(runtimeState, sessionId, merged);
        intentTokenRaw =
          typeof merged.intentTokenRaw === "string"
            ? merged.intentTokenRaw
            : intentTokenRaw;
        localPlan = merged.plan || localPlan;
        localExpiresAt = merged.expiresAt || localExpiresAt;
        debugLog(config, "intent token auto-refreshed near expiry");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      debugLog(config, `auto-refresh failed: ${message}`);
    }
  }

  // If no token, try to acquire one
  if (!intentTokenRaw && (config.intentEndpoint || (config.useSdkIntent && config.apiKey))) {
    try {
      const policyHash = computePolicyHash(policyState.policy);
      const intentResponse = await requestIntent(config, {
        prompt: session.lastPrompt || `Use tool ${toolName}`,
        session_id: sessionId,
        toolName,
        toolInput,
        policy_hash: policyHash,
        policy: policyState.policy,
        validitySeconds: config.validitySeconds,
        metadata: {
          source: "codex",
          trigger: "pre_tool_use"
        }
      });
      const merged = mergeIntentIntoSession(session, intentResponse);
      upsertSession(runtimeState, sessionId, merged);
      intentTokenRaw =
        typeof merged.intentTokenRaw === "string" ? merged.intentTokenRaw : "";
      localPlan = merged.plan || localPlan;
      localExpiresAt = merged.expiresAt || localExpiresAt;
      usedStepIndices =
        intentTokenRaw && localPlan
          ? getSessionTokenUsedStepIndices(merged, intentTokenRaw)
          : undefined;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (config.intentRequired && shouldDeny(config)) {
        return denyPreTool(`ArmorCodex intent planning failed: ${message}`);
      }
    }
  }

  // Validate tool against intent token plan
  if (intentTokenRaw) {
    const tokenCheck = checkIntentTokenPlan({
      intentTokenRaw,
      toolName,
      toolParams: toolInput
    });
    if (tokenCheck.matched) {
      tokenCheckMatched = true;
      if (tokenCheck.blockReason) {
        return denyOrAllow(config, tokenCheck.blockReason);
      }
      localPlan = tokenCheck.plan || localPlan;
      remoteAllowed = true;
    }
  }

  // --- CSRG proof handling ---
  const parsedProofs = parseCsrgProofHeaders(input);
  if (parsedProofs.error) {
    return denyOrAllow(config, parsedProofs.error);
  }
  let csrgProofs = parsedProofs.proofs;
  if (!csrgProofs && intentTokenRaw && localPlan && typeof localPlan === "object") {
    const resolved = resolveCsrgProofsFromToken({
      intentTokenRaw,
      plan: localPlan,
      toolName,
      toolParams: toolInput,
      usedStepIndices
    });
    if (resolved) {
      csrgProofs = resolved;
    }
  }
  const proofError = validateCsrgProofHeaders(
    csrgProofs,
    config.requireCsrgProofs &&
      config.csrgVerifyEnabled &&
      Boolean(config.verifyStepEndpoint) &&
      Boolean(intentTokenRaw)
  );
  if (proofError) {
    return denyOrAllow(config, proofError);
  }

  // --- Remote step verification ---
  if (intentTokenRaw && config.verifyStepEndpoint && config.csrgVerifyEnabled) {
    try {
      const iapService = createIapService(config);
      const verifyResult = await iapService.verifyStep(intentTokenRaw, csrgProofs, toolName);
      if (!verifyResult.skipped) {
        remoteAllowed = verifyResult.allowed === true;
      }
      if (verifyResult.allowed === false) {
        return denyOrAllow(
          config,
          verifyResult.reason || `ArmorCodex intent verification denied for ${toolName}`
        );
      }
      const merged = mergeIntentIntoSession(session, verifyResult);
      upsertSession(runtimeState, sessionId, merged);
      localPlan = merged.plan || localPlan;
      localExpiresAt = merged.expiresAt || localExpiresAt;
      if (typeof verifyResult.stepIndex === "number") {
        const indices = usedStepIndices || new Set();
        indices.add(verifyResult.stepIndex);
        recordSessionTokenUsedStepIndices(merged, intentTokenRaw, indices);
      } else if (usedStepIndices && intentTokenRaw) {
        recordSessionTokenUsedStepIndices(merged, intentTokenRaw, usedStepIndices);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const deny = denyOrAllow(config, `ArmorCodex verify-step failed: ${message}`);
      if (deny) {
        return deny;
      }
    }
  }

  // --- Expiry check ---
  if (Number.isFinite(localExpiresAt) && nowEpochSeconds() > localExpiresAt) {
    const deny = denyOrAllow(
      config,
      "ArmorCodex intent token expired — call register_intent_plan with your current plan to refresh, then retry the tool"
    );
    if (deny) {
      return deny;
    }
  }

  // --- Local plan enforcement (no backend / no token) ---
  // When a plan was registered via register_intent_plan but ArmorIQ is not
  // configured, enforce the plan locally: tool must be in plan, and params
  // (if declared in step.metadata.inputs) must match.
  let localPlanMatched = false;
  if (!intentTokenRaw && localPlan && typeof localPlan === "object") {
    const localCheck = checkToolAgainstPlan({
      plan: localPlan,
      toolName,
      toolInput
    });
    if (localCheck.allowed) {
      localPlanMatched = true;
    } else {
      const deny = denyOrAllow(config, localCheck.reason || "ArmorCodex intent drift");
      if (deny) {
        return deny;
      }
    }
  }

  // --- Enforce intent requirement ---
  if (config.intentRequired && !remoteAllowed && !tokenCheckMatched && !localPlanMatched) {
    const deny = denyOrAllow(config, "ArmorCodex intent plan missing for this session");
    if (deny) {
      return deny;
    }
  }

  // --- Record tool for discovery ---
  upsertDiscoveredTool(runtimeState, toolName);
  await saveRuntimeState(config.runtimeFile, runtimeState);
  return null;
}

// ---------------------------------------------------------------------------
// PermissionRequest
// ---------------------------------------------------------------------------

export async function handlePermissionRequest(input, config) {
  const toolName = typeof input.tool_name === "string" ? input.tool_name : "";
  const toolInput = sanitizeParams(input.tool_input, config.sanitize);
  if (!toolName) {
    return null;
  }

  const policyState = await loadPolicyState(config.policyFile);
  const policyDecision = evaluatePolicy({
    policy: policyState.policy,
    toolName,
    toolParams: toolInput
  });
  if (!policyDecision.allowed && shouldDeny(config)) {
    return denyPermissionRequest(policyDecision.reason || "ArmorCodex policy denied approval request");
  }

  return null;
}

// ---------------------------------------------------------------------------
// PostToolUse — audit logging
// ---------------------------------------------------------------------------

export async function handlePostToolUse(input, config) {
  if (!config.auditEnabled || !config.apiKey) {
    return null;
  }

  const sessionId = typeof input.session_id === "string" ? input.session_id : "";
  const toolName = typeof input.tool_name === "string" ? input.tool_name : "";
  if (!toolName) return null;

  try {
    const runtimeState = await loadRuntimeState(config.runtimeFile);
    const session = getSession(runtimeState, sessionId) || {};
    const iapService = createIapService(config);

    const intentTokenRaw = session.intentTokenRaw || "";
    let token = intentTokenRaw;
    // Extract JWT if embedded in JSON envelope
    if (intentTokenRaw.startsWith("{")) {
      try {
        const parsed = JSON.parse(intentTokenRaw);
        token = parsed.jwtToken || parsed.jwt_token || intentTokenRaw;
      } catch { /* use raw */ }
    }

    // Compute the real step index from the registered plan so the backend's
    // updateExecutionProgress can advance plan status to 'completed'.
    const inputs = sanitizeParams(input.tool_input, config.sanitize);
    const stepIdx = pickStepIndex(session.plan, toolName, inputs);

    const dto = {
      token,
      step_index: stepIdx,
      action: toolName,
      tool: toolName,
      input: redactSecrets(inputs),
      output: redactSecrets(sanitizeParams(input.tool_response, config.sanitize)),
      status: "success",
      executed_at: new Date().toISOString(),
      duration_ms: 0
    };

    // Await the WAL disk write (~1-2ms) so the row is durable before the
    // hook returns. Without the await a crash between read and write loses
    // the audit row even though the WAL exists for exactly this reason.
    // The slow HTTP ship to /iap/audit/batch still happens async via the
    // embedded flusher in policy-mcp.mjs. Mirrors armorClaude#46 fix #5.
    try {
      await iapService.enqueueAudit(dto);
    } catch (error) {
      debugLog(config, `audit enqueue failed: ${error}`);
    }
    debugLog(config, `audit log enqueued for ${toolName} step=${stepIdx}`);
  } catch (error) {
    // Audit is best-effort — don't block
    debugLog(config, `audit log failed: ${error}`);
  }

  return null;
}

// ---------------------------------------------------------------------------
// PostToolUseFailure — audit logging for failed tool calls
// ---------------------------------------------------------------------------

export async function handlePostToolUseFailure(input, config) {
  if (!config.auditEnabled || !config.apiKey) {
    return null;
  }

  const sessionId = typeof input.session_id === "string" ? input.session_id : "";
  const toolName = typeof input.tool_name === "string" ? input.tool_name : "";
  if (!toolName) return null;

  try {
    const runtimeState = await loadRuntimeState(config.runtimeFile);
    const session = getSession(runtimeState, sessionId) || {};
    const iapService = createIapService(config);

    const intentTokenRaw = session.intentTokenRaw || "";
    let token = intentTokenRaw;
    if (intentTokenRaw.startsWith("{")) {
      try {
        const parsed = JSON.parse(intentTokenRaw);
        token = parsed.jwtToken || parsed.jwt_token || intentTokenRaw;
      } catch { /* use raw */ }
    }

    const inputs = sanitizeParams(input.tool_input, config.sanitize);
    const stepIdx = pickStepIndex(session.plan, toolName, inputs);
    const dto = {
      token,
      step_index: stepIdx,
      action: toolName,
      tool: toolName,
      input: redactSecrets(inputs),
      output: null,
      status: "failed",
      error_message: typeof input.error === "string" ? redactSecrets(input.error) : "Unknown error",
      executed_at: new Date().toISOString(),
      duration_ms: 0
    };

    // Same await rationale as the success path above — see armorClaude#46 fix #5.
    try {
      await iapService.enqueueAudit(dto);
    } catch (error) {
      debugLog(config, `audit enqueue (failure) failed: ${error}`);
    }
    debugLog(config, `audit log (failure) enqueued for ${toolName}`);
  } catch (error) {
    debugLog(config, `audit log (failure) failed: ${error}`);
  }

  return null;
}

// ---------------------------------------------------------------------------
// Stop — end of turn
// ---------------------------------------------------------------------------

export async function handleStop(input, config) {
  const sessionId = typeof input.session_id === "string" ? input.session_id : "";
  if (!sessionId) return null;

  const runtimeState = await loadRuntimeState(config.runtimeFile);
  const session = getSession(runtimeState, sessionId);
  if (!session) return null;

  // Check if token expired mid-turn
  if (Number.isFinite(session.expiresAt) && nowEpochSeconds() > session.expiresAt) {
    debugLog(config, "intent token expired during turn");
  }

  upsertSession(runtimeState, sessionId, {
    lastStopAt: nowEpochSeconds()
  });
  await saveRuntimeState(config.runtimeFile, runtimeState);
  return null;
}

// ---------------------------------------------------------------------------
// SessionEnd — cleanup
// ---------------------------------------------------------------------------

export async function handleSessionEnd(input, config) {
  const sessionId = typeof input.session_id === "string" ? input.session_id : "";
  if (!sessionId) return null;

  const runtimeState = await loadRuntimeState(config.runtimeFile);
  // Remove the session entirely
  if (runtimeState.sessions && runtimeState.sessions[sessionId]) {
    delete runtimeState.sessions[sessionId];
  }
  await saveRuntimeState(config.runtimeFile, runtimeState);

  debugLog(config, `session ended: ${sessionId}`);
  return null;
}
