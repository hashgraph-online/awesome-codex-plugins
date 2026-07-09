import armoriqSdk from "@armoriq/sdk";
import {
  buildAuthHeaders,
  isPlainObject,
  isSubsetValue,
  normalizeToolName,
  parseStepIndex,
  postJson,
  readString,
  sha256Hex
} from "./common.mjs";

const { ArmorIQClient } = armoriqSdk;
const sdkClientCache = new Map();

function buildSdkClientKey(config) {
  return [
    config.apiKey,
    config.userId,
    config.agentId,
    config.contextId,
    config.iapEndpoint,
    config.proxyEndpoint,
    config.backendEndpoint,
    config.useProduction ? "prod" : "dev"
  ].join("|");
}

function getSdkClient(config) {
  const key = buildSdkClientKey(config);
  const cached = sdkClientCache.get(key);
  if (cached) {
    return cached;
  }
  const client = new ArmorIQClient({
    apiKey: config.apiKey,
    userId: config.userId,
    agentId: config.agentId,
    contextId: config.contextId,
    useProduction: config.useProduction,
    iapEndpoint: config.iapEndpoint,
    proxyEndpoint: config.proxyEndpoint,
    backendEndpoint: config.backendEndpoint,
    timeout: config.timeoutMs,
    maxRetries: config.maxRetries,
    verifySsl: config.verifySsl
  });
  sdkClientCache.set(key, client);
  return client;
}

function buildFallbackPlan(payload) {
  const goal = typeof payload.prompt === "string" ? payload.prompt : "ArmorCodex intent";
  const plan = { steps: [], metadata: { goal, source: "codex" } };
  if (typeof payload.toolName === "string" && payload.toolName.trim()) {
    plan.steps.push({
      action: payload.toolName.trim(),
      mcp: payload.mcpName || "codex",
      metadata: isPlainObject(payload.toolInput) ? { inputs: payload.toolInput } : {}
    });
  }
  return plan;
}

function resolvePlan(payload) {
  if (isPlainObject(payload.plan)) {
    return payload.plan;
  }
  return buildFallbackPlan(payload);
}

export function extractPlanFromIntentToken(raw) {
  if (typeof raw !== "string" || !raw.trim()) {
    return null;
  }
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }
  if (!isPlainObject(parsed)) {
    return null;
  }
  const rawToken = isPlainObject(parsed.rawToken) ? parsed.rawToken : undefined;
  const planCandidate =
    (rawToken && isPlainObject(rawToken.plan) ? rawToken.plan : undefined) ||
    (isPlainObject(parsed.plan) ? parsed.plan : undefined) ||
    (isPlainObject(parsed.token) && isPlainObject(parsed.token.plan) ? parsed.token.plan : undefined);
  if (!planCandidate) {
    return null;
  }
  const expiresAt =
    Number.isFinite(parsed.expiresAt)
      ? parsed.expiresAt
      : isPlainObject(parsed.token) && Number.isFinite(parsed.token.expires_at)
        ? parsed.token.expires_at
        : undefined;
  return { plan: planCandidate, expiresAt };
}

export function extractAllowedActions(plan) {
  const allowed = new Set();
  const steps = Array.isArray(plan?.steps) ? plan.steps : [];
  for (const step of steps) {
    if (!isPlainObject(step)) {
      continue;
    }
    const action =
      typeof step.action === "string"
        ? step.action
        : typeof step.tool === "string"
          ? step.tool
          : "";
    if (action.trim()) {
      allowed.add(normalizeToolName(action));
    }
  }
  return allowed;
}

function findPlanStep(plan, toolName) {
  const steps = Array.isArray(plan?.steps) ? plan.steps : [];
  const normalizedTool = normalizeToolName(toolName);
  for (const step of steps) {
    if (!isPlainObject(step)) {
      continue;
    }
    const action =
      typeof step.action === "string"
        ? step.action
        : typeof step.tool === "string"
          ? step.tool
          : "";
    if (normalizeToolName(action) === normalizedTool) {
      return step;
    }
  }
  return null;
}

function getStepInputCandidates(step) {
  const candidates = [];
  if (isPlainObject(step.metadata) && isPlainObject(step.metadata.inputs)) {
    candidates.push(step.metadata.inputs);
  }
  if (isPlainObject(step.params)) {
    candidates.push(step.params);
  }
  if (isPlainObject(step.arguments)) {
    candidates.push(step.arguments);
  }
  return candidates;
}

export function findPlanStepIndices(plan, toolName, toolParams) {
  const steps = Array.isArray(plan?.steps) ? plan.steps : [];
  const normalizedTool = normalizeToolName(toolName);
  const matches = [];
  const paramMatches = [];
  for (let idx = 0; idx < steps.length; idx += 1) {
    const step = steps[idx];
    if (!isPlainObject(step)) {
      continue;
    }
    const action =
      typeof step.action === "string"
        ? step.action
        : typeof step.tool === "string"
          ? step.tool
          : "";
    if (normalizeToolName(action) !== normalizedTool) {
      continue;
    }
    matches.push(idx);
    if (toolParams) {
      const inputCandidates = getStepInputCandidates(step);
      if (inputCandidates.some((inputs) => isSubsetValue(inputs, toolParams))) {
        paramMatches.push(idx);
      }
    }
  }
  return { matches, paramMatches };
}

export function checkToolAgainstPlan({ plan, toolName, toolInput }) {
  const normalizedTool = normalizeToolName(toolName);
  const steps = Array.isArray(plan?.steps) ? plan.steps : [];
  if (!steps.length) {
    return { allowed: false, reason: "ArmorCodex intent plan is empty" };
  }
  const matches = [];
  for (const step of steps) {
    if (!isPlainObject(step)) {
      continue;
    }
    const action =
      typeof step.action === "string"
        ? step.action
        : typeof step.tool === "string"
          ? step.tool
          : "";
    if (normalizeToolName(action) === normalizedTool) {
      matches.push(step);
    }
  }
  if (!matches.length) {
    return { allowed: false, reason: `ArmorCodex intent drift: tool not in plan (${toolName})` };
  }
  if (!isPlainObject(toolInput)) {
    return { allowed: true };
  }
  let sawConstrainedMatch = false;
  for (const step of matches) {
    const inputCandidates = getStepInputCandidates(step);
    if (inputCandidates.length === 0) {
      return { allowed: true };
    }
    sawConstrainedMatch = true;
    for (const candidate of inputCandidates) {
      // Strict subset: every key in declared candidate matches actual input.
      if (isSubsetValue(candidate, toolInput)) {
        return { allowed: true };
      }
      // Lenient fallback: agents (especially gpt-5.4) often declare inputs
      // with field names that don't match the real tool (e.g. `cmd` instead
      // of Codex's `command`). If NONE of the declared keys exist on the
      // real input, treat it as an over-eager declaration and allow.
      // The tool name itself was already matched; the parameter declaration
      // was simply wrong-fielded, not a security violation.
      if (isPlainObject(candidate) && isPlainObject(toolInput)) {
        const declaredKeys = Object.keys(candidate);
        if (declaredKeys.length > 0) {
          const overlappingKeys = declaredKeys.filter((k) => k in toolInput);
          if (overlappingKeys.length === 0) {
            return { allowed: true };
          }
        }
      }
    }
  }
  if (sawConstrainedMatch) {
    return {
      allowed: false,
      reason: `ArmorCodex intent mismatch: parameters not allowed for ${toolName}`
    };
  }
  return { allowed: true };
}

export function checkIntentTokenPlan({ intentTokenRaw, toolName, toolParams }) {
  const parsed = extractPlanFromIntentToken(intentTokenRaw);
  if (!parsed) {
    return { matched: false };
  }
  if (parsed.expiresAt && Date.now() / 1000 > parsed.expiresAt) {
    return {
      matched: true,
      blockReason:
        "ArmorIQ intent token expired — call register_intent_plan to refresh, then retry",
      plan: parsed.plan
    };
  }
  const allowedActions = extractAllowedActions(parsed.plan);
  if (!allowedActions.has(normalizeToolName(toolName))) {
    return {
      matched: true,
      blockReason: `ArmorIQ intent drift: tool not in plan (${toolName})`,
      plan: parsed.plan
    };
  }

  // Parameter-level enforcement: check tool params against plan step constraints
  if (isPlainObject(toolParams)) {
    const paramCheck = checkToolAgainstPlan({
      plan: parsed.plan,
      toolName,
      toolInput: toolParams
    });
    if (!paramCheck.allowed) {
      return {
        matched: true,
        blockReason: paramCheck.reason,
        plan: parsed.plan
      };
    }
  }

  return {
    matched: true,
    params: isPlainObject(toolParams) ? toolParams : undefined,
    plan: parsed.plan
  };
}

export function parseStepIndexFromPath(path) {
  if (!path) {
    return null;
  }
  const match = path.match(/\/steps\/\[(\d+)\]/);
  if (!match) {
    return null;
  }
  const index = Number.parseInt(match[1] || "", 10);
  return Number.isFinite(index) ? index : null;
}

function readStepProofsFromToken(tokenObj) {
  if (Array.isArray(tokenObj.stepProofs)) {
    return tokenObj.stepProofs;
  }
  if (Array.isArray(tokenObj.step_proofs)) {
    return tokenObj.step_proofs;
  }
  if (isPlainObject(tokenObj.rawToken)) {
    if (Array.isArray(tokenObj.rawToken.stepProofs)) {
      return tokenObj.rawToken.stepProofs;
    }
    if (Array.isArray(tokenObj.rawToken.step_proofs)) {
      return tokenObj.rawToken.step_proofs;
    }
  }
  return null;
}

function resolveStepProofEntry(stepProofs, stepIndex) {
  const entry = stepProofs[stepIndex];
  if (!entry) {
    return null;
  }
  if (Array.isArray(entry)) {
    return { proof: entry, stepIndex };
  }
  if (!isPlainObject(entry)) {
    return null;
  }
  const proof = Array.isArray(entry.proof) ? entry.proof : undefined;
  const path =
    readString(entry.path) ||
    readString(entry.step_path) ||
    readString(entry.csrg_path) ||
    undefined;
  const indexFromField = parseStepIndex(entry.step_index) ?? parseStepIndex(entry.stepIndex);
  const indexFromPath = parseStepIndexFromPath(path);
  const resolvedStepIndex = indexFromField ?? indexFromPath ?? stepIndex;
  const valueDigest =
    readString(entry.value_digest) ||
    readString(entry.valueDigest) ||
    readString(entry.csrg_value_digest) ||
    undefined;
  return { proof, path, valueDigest, stepIndex: resolvedStepIndex };
}

function scoreProofPath(path) {
  if (!path) {
    return 0;
  }
  if (/\/(action|tool)$/i.test(path)) {
    return 3;
  }
  if (/\/(arguments|params|metadata)$/i.test(path)) {
    return 1;
  }
  return 2;
}

function chooseProofEntry(entries, usedStepIndices) {
  if (!entries.length) {
    return null;
  }
  const stepGroups = new Map();
  for (const entry of entries) {
    const list = stepGroups.get(entry.stepIndex) || [];
    list.push(entry);
    stepGroups.set(entry.stepIndex, list);
  }
  const orderedStepIndices = Array.from(stepGroups.keys()).sort((a, b) => {
    const aUsed = usedStepIndices?.has(a) ? 1 : 0;
    const bUsed = usedStepIndices?.has(b) ? 1 : 0;
    if (aUsed !== bUsed) {
      return aUsed - bUsed;
    }
    return a - b;
  });
  const selectedStepIndex = orderedStepIndices[0];
  if (selectedStepIndex === undefined) {
    return null;
  }
  const candidates = stepGroups.get(selectedStepIndex) || [];
  candidates.sort((a, b) => {
    const pathScore = scoreProofPath(b.path) - scoreProofPath(a.path);
    if (pathScore !== 0) {
      return pathScore;
    }
    const digestScore = Number(Boolean(b.valueDigest)) - Number(Boolean(a.valueDigest));
    if (digestScore !== 0) {
      return digestScore;
    }
    return 0;
  });
  return candidates[0] || null;
}

export function resolveCsrgProofsFromToken({
  intentTokenRaw,
  plan,
  toolName,
  toolParams,
  usedStepIndices
}) {
  let parsed;
  try {
    parsed = JSON.parse(intentTokenRaw);
  } catch {
    return null;
  }
  if (!isPlainObject(parsed)) {
    return null;
  }
  const stepProofs = readStepProofsFromToken(parsed);
  if (!stepProofs || stepProofs.length === 0) {
    return null;
  }
  const normalizedParams = isPlainObject(toolParams) ? toolParams : undefined;
  const { matches, paramMatches } = findPlanStepIndices(plan, toolName, normalizedParams);
  if (matches.length === 0) {
    return null;
  }
  const resolvedEntries = [];
  for (let idx = 0; idx < stepProofs.length; idx += 1) {
    const entry = resolveStepProofEntry(stepProofs, idx);
    if (!entry?.proof || !Array.isArray(entry.proof)) {
      continue;
    }
    resolvedEntries.push(entry);
  }
  const entriesMatchingTool = resolvedEntries.filter((entry) => matches.includes(entry.stepIndex));
  if (!entriesMatchingTool.length) {
    return null;
  }
  const entriesMatchingParams =
    paramMatches.length > 0
      ? entriesMatchingTool.filter((entry) => paramMatches.includes(entry.stepIndex))
      : [];
  const selected = chooseProofEntry(
    entriesMatchingParams.length > 0 ? entriesMatchingParams : entriesMatchingTool,
    usedStepIndices
  );
  if (!selected || !Array.isArray(selected.proof)) {
    return null;
  }
  const steps = Array.isArray(plan?.steps) ? plan.steps : [];
  const stepIndex = selected.stepIndex;
  const stepObj = steps[stepIndex];
  const action =
    isPlainObject(stepObj) && typeof stepObj.action === "string"
      ? stepObj.action
      : isPlainObject(stepObj) && typeof stepObj.tool === "string"
        ? stepObj.tool
        : toolName;
  return {
    path: selected.path || `/steps/[${stepIndex}]/action`,
    proof: selected.proof,
    valueDigest: selected.valueDigest || sha256Hex(JSON.stringify(action)),
    stepIndex
  };
}

function parseProofValue(raw) {
  if (Array.isArray(raw)) {
    return raw;
  }
  if (typeof raw === "string") {
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        return parsed;
      }
      return { error: "ArmorIQ CSRG proof header must be a JSON array" };
    } catch {
      return { error: "ArmorIQ CSRG proof header invalid JSON" };
    }
  }
  return undefined;
}

function readFromHeaderMap(headers, keys) {
  if (!isPlainObject(headers)) {
    return undefined;
  }
  for (const key of keys) {
    const value = readString(headers[key]);
    if (value) {
      return value;
    }
  }
  return undefined;
}

export function parseCsrgProofHeaders(input) {
  const headers = isPlainObject(input.headers) ? input.headers : undefined;
  const path =
    readString(input.csrgPath) ||
    readString(input.csrg_path) ||
    readString(input["x-csrg-path"]) ||
    readFromHeaderMap(headers, ["x-csrg-path", "X-CSRG-Path"]) ||
    undefined;
  const valueDigest =
    readString(input.csrgValueDigest) ||
    readString(input.csrg_value_digest) ||
    readString(input["x-csrg-value-digest"]) ||
    readFromHeaderMap(headers, ["x-csrg-value-digest", "X-CSRG-Value-Digest"]) ||
    undefined;
  const proofRaw =
    input.csrgProofRaw ??
    input.csrg_proof ??
    input["x-csrg-proof"] ??
    (headers ? headers["x-csrg-proof"] ?? headers["X-CSRG-Proof"] : undefined);

  if (!path && !valueDigest && proofRaw === undefined) {
    return {};
  }
  const parsedProof = parseProofValue(proofRaw);
  if (isPlainObject(parsedProof) && parsedProof.error) {
    return { error: parsedProof.error };
  }
  return {
    proofs: {
      path,
      valueDigest,
      proof: parsedProof
    }
  };
}

export function validateCsrgProofHeaders(proofs, required) {
  if (!required) {
    return null;
  }
  if (!proofs) {
    return "ArmorIQ CSRG proof headers missing";
  }
  if (!proofs.path) {
    return "ArmorIQ CSRG path header missing";
  }
  if (!proofs.valueDigest) {
    return "ArmorIQ CSRG value digest header missing";
  }
  if (!proofs.proof || !Array.isArray(proofs.proof)) {
    return "ArmorIQ CSRG proof header missing";
  }
  return null;
}

export async function requestIntent(config, payload) {
  if (config.intentEndpoint) {
    const response = await postJson(
      config.intentEndpoint,
      payload,
      buildAuthHeaders(config),
      config.timeoutMs
    );
    if (!response.ok) {
      throw new Error(response.text || `Intent request failed: ${response.status}`);
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
    const parsedFromToken = tokenRaw ? extractPlanFromIntentToken(tokenRaw) : null;
    const plan = isPlainObject(data.plan) ? data.plan : parsedFromToken?.plan;
    const expiresAt =
      Number.isFinite(data.expiresAt)
        ? data.expiresAt
        : Number.isFinite(data.expires_at)
          ? data.expires_at
          : parsedFromToken?.expiresAt;
    return {
      skipped: false,
      source: "custom-endpoint",
      tokenRaw,
      plan,
      expiresAt
    };
  }

  if (!config.useSdkIntent || !config.apiKey) {
    return { skipped: true };
  }
  const client = getSdkClient(config);
  const plan = resolvePlan({ ...payload, mcpName: config.mcpName });
  const metadata = {
    source: "codex",
    session_id: payload.session_id,
    policy_hash: payload.policy_hash,
    ...payload.metadata
  };
  const capture = client.capturePlan(config.llmId, payload.prompt || "", plan, metadata);
  const token = await client.getIntentToken(capture, payload.policy, payload.validitySeconds);
  const tokenRaw = JSON.stringify(token);
  const parsedFromToken = extractPlanFromIntentToken(tokenRaw);
  return {
    skipped: false,
    source: "armoriq-sdk",
    tokenRaw,
    plan: parsedFromToken?.plan || plan,
    expiresAt: Number.isFinite(token.expiresAt) ? token.expiresAt : parsedFromToken?.expiresAt
  };
}

export function getSessionTokenUsedStepIndices(session, intentTokenRaw) {
  if (!session || typeof intentTokenRaw !== "string" || !intentTokenRaw.trim()) {
    return undefined;
  }
  const tokenHash = sha256Hex(intentTokenRaw);
  const tracker = isPlainObject(session.intentExecution) ? session.intentExecution : {};
  if (tracker.tokenHash !== tokenHash) {
    tracker.tokenHash = tokenHash;
    tracker.usedStepIndices = [];
    session.intentExecution = tracker;
  }
  const used = Array.isArray(tracker.usedStepIndices) ? tracker.usedStepIndices : [];
  tracker.usedStepIndices = used.filter((value) => Number.isFinite(value));
  session.intentExecution = tracker;
  return new Set(tracker.usedStepIndices);
}

export function recordSessionTokenUsedStepIndices(session, intentTokenRaw, usedStepIndices) {
  if (!session || typeof intentTokenRaw !== "string" || !intentTokenRaw.trim()) {
    return;
  }
  const tokenHash = sha256Hex(intentTokenRaw);
  session.intentExecution = {
    tokenHash,
    usedStepIndices: Array.from(usedStepIndices || []).filter((value) => Number.isFinite(value))
  };
}
