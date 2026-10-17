import { createHash } from "node:crypto";
import {
  isMatcherSpec,
  isPlainObject,
  isSubsetValue,
  matchParams,
  matchesAnyStringField,
  matchesScalar,
  normalizeToolName
} from "./common.mjs";
import { readJson, writeJson } from "./fs-store.mjs";

const POLICY_ACTIONS = new Set(["allow", "deny", "require_approval"]);
const POLICY_DATA_CLASSES = new Set(["PCI", "PAYMENT", "PHI", "PII"]);

function normalizeRule(rule) {
  if (!isPlainObject(rule)) {
    return null;
  }
  const id = typeof rule.id === "string" ? rule.id.trim() : "";
  const action = typeof rule.action === "string" ? rule.action.trim() : "";
  const tool = typeof rule.tool === "string" ? rule.tool.trim() : "";
  if (!id || !tool || !POLICY_ACTIONS.has(action)) {
    return null;
  }
  const normalized = {
    id,
    action,
    tool
  };
  if (typeof rule.dataClass === "string" && POLICY_DATA_CLASSES.has(rule.dataClass.trim())) {
    normalized.dataClass = rule.dataClass.trim();
  }
  if (isPlainObject(rule.params)) {
    normalized.params = rule.params;
  }
  // anyParam: matcher applied across any string field in the tool input.
  // Useful for free-text intents like "deny ~/.ssh" where we don't know
  // which key the tool will store the path under.
  if (isMatcherSpec(rule.anyParam) || typeof rule.anyParam === "string") {
    normalized.anyParam =
      typeof rule.anyParam === "string"
        ? { $contains: rule.anyParam }
        : rule.anyParam;
  }
  return normalized;
}

function normalizePolicy(policyLike) {
  const input = isPlainObject(policyLike) ? policyLike : {};
  const rulesInput = Array.isArray(input.rules) ? input.rules : [];
  const rules = rulesInput.map((rule) => normalizeRule(rule)).filter(Boolean);
  return { rules };
}

export async function loadPolicyState(policyFilePath) {
  const initial = {
    version: 0,
    updatedAt: new Date().toISOString(),
    policy: { rules: [] },
    history: []
  };
  const raw = await readJson(policyFilePath, initial);
  const state = isPlainObject(raw) ? raw : initial;
  return {
    version: Number.isFinite(state.version) ? state.version : 0,
    updatedAt: typeof state.updatedAt === "string" ? state.updatedAt : new Date().toISOString(),
    updatedBy: typeof state.updatedBy === "string" ? state.updatedBy : undefined,
    policy: normalizePolicy(state.policy || state),
    history: Array.isArray(state.history) ? state.history : []
  };
}

export async function savePolicyState(policyFilePath, state) {
  await writeJson(policyFilePath, state);
}

export function computePolicyHash(policy) {
  return createHash("sha256").update(JSON.stringify(normalizePolicy(policy))).digest("hex");
}

function toolMatches(ruleTool, toolName) {
  if (ruleTool === "*") {
    return true;
  }
  return normalizeToolName(ruleTool) === normalizeToolName(toolName);
}

function extractStrings(value, depth, texts, keys) {
  if (depth > 4) {
    return;
  }
  if (typeof value === "string") {
    texts.push(value);
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((entry) => extractStrings(entry, depth + 1, texts, keys));
    return;
  }
  if (isPlainObject(value)) {
    for (const [key, entry] of Object.entries(value)) {
      keys.push(key);
      extractStrings(entry, depth + 1, texts, keys);
    }
  }
}

function luhnCheck(value) {
  let sum = 0;
  let doubleDigit = false;
  for (let i = value.length - 1; i >= 0; i -= 1) {
    let digit = Number.parseInt(value[i] || "", 10);
    if (!Number.isFinite(digit)) {
      return false;
    }
    if (doubleDigit) {
      digit *= 2;
      if (digit > 9) {
        digit -= 9;
      }
    }
    sum += digit;
    doubleDigit = !doubleDigit;
  }
  return sum % 10 === 0;
}

function hasCardNumber(texts) {
  const regex = /\b(?:\d[ -]*?){13,19}\b/g;
  for (const text of texts) {
    const matches = text.match(regex);
    if (!matches) {
      continue;
    }
    for (const match of matches) {
      const digits = match.replace(/[^\d]/g, "");
      if (digits.length >= 13 && digits.length <= 19 && luhnCheck(digits)) {
        return true;
      }
    }
  }
  return false;
}

function hasPaymentKeywords(texts, keys) {
  const keywords = ["card", "credit", "payment", "cvv", "iban", "swift", "bank", "routing"];
  const haystack = [...texts, ...keys].join(" ").toLowerCase();
  return keywords.some((keyword) => haystack.includes(keyword));
}

function isPaymentTool(toolName) {
  return /pay|payment|transfer|charge|crypto|bank|card|stripe|billing/i.test(toolName);
}

export function detectDataClasses(toolName, toolParams) {
  const texts = [];
  const keys = [];
  extractStrings(toolParams || {}, 0, texts, keys);
  const classes = new Set();
  if (hasCardNumber(texts) || hasPaymentKeywords(texts, keys)) {
    classes.add("PCI");
  }
  if (isPaymentTool(toolName) || hasPaymentKeywords(texts, keys)) {
    classes.add("PAYMENT");
  }
  return classes;
}

export function evaluatePolicy({ policy, toolName, toolParams }) {
  const rules = normalizePolicy(policy).rules;
  const dataClasses = detectDataClasses(toolName, toolParams);
  const warnings = [];

  for (const rule of rules) {
    if (!toolMatches(rule.tool, toolName)) {
      continue;
    }
    if (rule.dataClass && !dataClasses.has(rule.dataClass)) {
      continue;
    }
    let paramsMatched = true;
    if (rule.params) {
      const result = matchParams(rule.params, toolParams || {});
      paramsMatched = result.matched;
      // Surface "rule probably won't fire": rule references keys absent from
      // this tool's input, which usually means the user's intent isn't
      // expressible as-is.
      if (!result.matched && result.missingKeys.length > 0) {
        warnings.push({
          ruleId: rule.id,
          tool: rule.tool,
          missingKeys: result.missingKeys,
          message: `Rule ${rule.id} references keys absent from ${toolName} input: ${result.missingKeys.join(", ")}. Consider using anyParam or operator-based matchers.`
        });
      }
    }
    if (!paramsMatched) {
      continue;
    }
    // anyParam matches if ANY string field in the tool input satisfies the
    // matcher. Useful when the user doesn't know which key holds the path.
    if (rule.anyParam) {
      if (!matchesAnyStringField(rule.anyParam, toolParams || {})) {
        continue;
      }
    }
    if (rule.action === "allow") {
      return { allowed: true, matchedRule: rule, dataClasses: Array.from(dataClasses), warnings };
    }
    if (rule.action === "deny") {
      return {
        allowed: false,
        reason: `ArmorCodex policy deny: ${rule.id}`,
        matchedRule: rule,
        dataClasses: Array.from(dataClasses),
        warnings
      };
    }
    if (rule.action === "require_approval") {
      return {
        allowed: false,
        reason: `ArmorCodex policy requires approval: ${rule.id}`,
        matchedRule: rule,
        dataClasses: Array.from(dataClasses),
        warnings
      };
    }
  }

  return { allowed: true, dataClasses: Array.from(dataClasses), warnings };
}

function truncateReason(text, max = 160) {
  const trimmed = text.trim();
  if (trimmed.length <= max) {
    return trimmed;
  }
  return `${trimmed.slice(0, max)}...`;
}

function formatRule(rule) {
  const parts = [`id=${rule.id}`, `action=${rule.action}`, `tool=${rule.tool}`];
  if (rule.dataClass) {
    parts.push(`dataClass=${rule.dataClass}`);
  }
  if (rule.anyParam) {
    const op = Object.keys(rule.anyParam)[0];
    const val = rule.anyParam[op];
    parts.push(`match=${op}:${val}`);
  }
  if (rule.params) {
    parts.push(`params=${JSON.stringify(rule.params)}`);
  }
  return parts.join(" ");
}

function nextPolicyId(state) {
  const ids = state.policy.rules
    .map((rule) => rule.id)
    .map((id) => {
      const match = id.match(/^policy(\d+)$/i);
      return match ? Number.parseInt(match[1] || "", 10) : null;
    })
    .filter((value) => Number.isFinite(value));
  const max = ids.length ? Math.max(...ids) : 0;
  return `policy${max + 1}`;
}

function inferPolicyAction(text) {
  const lower = text.toLowerCase();
  if (/(require\s+approval|needs\s+approval|approval\s+required)/i.test(lower)) {
    return "require_approval";
  }
  if (/(allow|permit|enable|whitelist)/i.test(lower)) {
    return "allow";
  }
  if (/(deny|block|disallow|prevent|prohibit|stop)/i.test(lower)) {
    return "deny";
  }
  return "deny";
}

function inferPolicyDataClass(text) {
  const lower = text.toLowerCase();
  if (/(credit\s*card|card\s*number|pci)/i.test(lower)) {
    return "PCI";
  }
  if (/(payment|billing|bank|iban|swift|routing)/i.test(lower)) {
    return "PAYMENT";
  }
  if (/(phi|health|patient|medical)/i.test(lower)) {
    return "PHI";
  }
  if (/(pii|ssn|personal\s+data|identity)/i.test(lower)) {
    return "PII";
  }
  return undefined;
}

// A tool name must look like a real identifier — letters, digits, underscore,
// hyphen, dot, colon — OR exactly "*". Anything else is rejected so free-text
// like "all tools" or regex fragments can't become rule matchers.
const VALID_TOOL_NAME = /^(?:\*|[A-Za-z][\w.:\-]{0,80})$/;

function sanitizeToolName(candidate) {
  if (typeof candidate !== "string") return null;
  const trimmed = candidate.trim();
  if (!trimmed) return null;
  return VALID_TOOL_NAME.test(trimmed) ? trimmed : null;
}

// Detect a path or substring the user wants to block. Looks for things like
// ~/.ssh, /etc/passwd, or quoted/backticked snippets after "block"/"deny".
function inferAnyParamMatcher(text) {
  // Quoted snippets first: most explicit.
  const quoted =
    text.match(/"([^"\n]{2,80})"/) ||
    text.match(/'([^'\n]{2,80})'/);
  if (quoted && quoted[1]) {
    return inferMatcherForPhrase(quoted[1]);
  }
  // Path-like tokens: ~/..., /xxx/yyy, $HOME/...
  const pathMatch = text.match(/((?:~|\$\{?HOME\}?|\/)[\w./@\-+~]{2,120})/);
  if (pathMatch && pathMatch[1]) {
    const candidate = pathMatch[1].replace(/[.,;:)\]}]+$/, "");
    if (candidate.length >= 2) {
      return { $pathContains: candidate };
    }
  }
  return null;
}

function inferMatcherForPhrase(phrase) {
  const trimmed = phrase.trim();
  if (!trimmed) return null;
  if (/^(?:~|\$\{?HOME\}?|\/)/.test(trimmed)) {
    return { $pathContains: trimmed };
  }
  // Looks like a regex: leave operator-based match.
  if (/[\\^$+?(){}[\]|]/.test(trimmed)) {
    return { $matches: trimmed };
  }
  return { $contains: trimmed };
}

// Real Codex tools we recognize. Used to disambiguate "block X for Y" where X
// may or may not be a tool name. Falls back to "*" when X isn't here.
const KNOWN_CODEX_TOOLS = new Set([
  "*",
  "bash", "apply_patch", "list_dir", "view_image", "mcp_resource",
  "update_plan", "create_goal", "update_goal", "get_goal",
  "spawn_agents_on_csv", "tool_search", "tool_suggest",
  "register_intent_plan", "policy_read", "policy_update"
]);

function inferPolicyTool(text) {
  const lower = text.toLowerCase();
  if (/(all\s+tools|any\s+tool|\*\b)/i.test(lower)) {
    return "*";
  }
  const backtickMatch = text.match(/`([A-Za-z][\w.:\-]{0,80})`/);
  const backtickName = sanitizeToolName(backtickMatch?.[1]);
  if (backtickName) {
    return backtickName;
  }
  const toolMatch = text.match(/\btool\s*[:=]?\s*([A-Za-z][\w.:\-]{0,80})/i);
  const toolName = sanitizeToolName(toolMatch?.[1]);
  if (toolName) {
    return toolName;
  }
  const actionMatch = text.match(/\b(?:block|deny|allow|disallow|permit|require)\s+([A-Za-z][\w.:\-]{0,80})/i);
  const actionName = sanitizeToolName(actionMatch?.[1]);
  if (actionName) {
    return actionName;
  }
  return "*";
}

function buildPolicyUpdateFromText(text, state, forceNewId = false) {
  const explicitIdMatch = text.match(/\bpolicy[-_]?(\d+)\b/i);
  const explicitId = explicitIdMatch && explicitIdMatch[1] ? `policy${explicitIdMatch[1]}` : "";
  const id = forceNewId ? nextPolicyId(state) : explicitId || nextPolicyId(state);
  const inferredTool = inferPolicyTool(text);
  const anyParam = inferAnyParamMatcher(text);

  // If we found a path/phrase to match AND the inferred tool is a verb like
  // "access" or any unknown name, the user means "block this content across
  // all tools": promote tool to "*". A real tool name (Bash, apply_patch...)
  // stays as-is so users can scope rules to a specific tool when they want.
  let tool = inferredTool;
  if (anyParam && tool !== "*") {
    const normalized = tool.toLowerCase();
    if (!KNOWN_CODEX_TOOLS.has(normalized)) {
      tool = "*";
    }
  }

  const rule = {
    id,
    action: inferPolicyAction(text),
    tool,
    dataClass: inferPolicyDataClass(text)
  };
  if (anyParam) {
    rule.anyParam = anyParam;
  }
  return {
    reason: truncateReason(`User policy update: ${text}`),
    mode: /replace/i.test(text) ? "replace" : "merge",
    rules: [rule]
  };
}

export function parsePolicyTextCommand(text, state) {
  const trimmed = text.trim();
  const lower = trimmed.toLowerCase();

  if (!/^policy\b/i.test(trimmed)) {
    return { kind: "none" };
  }

  // Only the bare "Policy help" / "Policy commands" form triggers help.
  // Otherwise "Bash commands containing curl" inside a rule body would
  // wrongly route here.
  if (/^\s*policy\s+(help|commands)\s*$/i.test(trimmed)) {
    return { kind: "help" };
  }
  if (/^\s*policy\s+(list|show|view)\s*$/i.test(trimmed)) {
    return { kind: "list" };
  }
  if (/\breset|clear\s+all|wipe\b/i.test(lower)) {
    return { kind: "reset", reason: truncateReason(`Policy reset: ${trimmed}`) };
  }
  const reorderMatch = trimmed.match(
    /\bpolicy\s*(?:priorit(?:y|ize|ise)|reorder|move)\s+(policy\d+|[a-z0-9][\w.-]*)\s+(?:to\s+)?(\d+)\b/i
  );
  if (reorderMatch && reorderMatch[1] && reorderMatch[2]) {
    return {
      kind: "reorder",
      id: reorderMatch[1],
      position: Number.parseInt(reorderMatch[2], 10),
      reason: truncateReason(`Policy reorder: ${trimmed}`)
    };
  }
  const deleteMatch = trimmed.match(/\bpolicy\s+delete\s+([a-z0-9][\w.-]*)\b/i);
  if (deleteMatch && deleteMatch[1]) {
    return {
      kind: "delete",
      id: deleteMatch[1],
      reason: truncateReason(`Policy delete: ${trimmed}`)
    };
  }
  const getMatch = trimmed.match(/\bpolicy\s+get\s+([a-z0-9][\w.-]*)\b/i);
  if (getMatch && getMatch[1]) {
    return { kind: "get", id: getMatch[1] };
  }
  const newMatch = trimmed.match(/\bpolicy\s+new\s*:\s*(.+)$/i);
  if (newMatch && newMatch[1]) {
    return { kind: "update", update: buildPolicyUpdateFromText(newMatch[1], state, true) };
  }
  const updateMatch = trimmed.match(/\bpolicy\s+update(?:\s+([a-z0-9][\w.-]*))?\s*:\s*(.+)$/i);
  if (updateMatch && updateMatch[2]) {
    const [_, maybeId, body] = updateMatch;
    const full = maybeId ? `${maybeId} ${body}` : body;
    return { kind: "update", update: buildPolicyUpdateFromText(full, state, false), hasId: Boolean(maybeId) };
  }

  return { kind: "help" };
}

function mergeRules(existing, updates) {
  const byId = new Map();
  for (const rule of existing) {
    byId.set(rule.id, rule);
  }
  const newRules = [];
  for (const rule of updates) {
    if (byId.has(rule.id)) {
      byId.set(rule.id, rule);
    } else {
      newRules.push(rule);
    }
  }
  return [...newRules, ...Array.from(byId.values())];
}

async function persistNextState(policyFilePath, oldState, nextPolicy, actor, reason) {
  const version = oldState.version + 1;
  const updatedAt = new Date().toISOString();
  const entry = {
    version,
    updatedAt,
    updatedBy: actor,
    reason,
    policy: nextPolicy
  };
  const nextState = {
    version,
    updatedAt,
    updatedBy: actor,
    policy: nextPolicy,
    history: [...oldState.history, entry]
  };
  await savePolicyState(policyFilePath, nextState);
  return nextState;
}

function formatPolicyHelp() {
  return [
    "Policy commands:",
    "1. Policy list",
    "2. Policy get policy1",
    "3. Policy delete policy1",
    "4. Policy reset",
    "5. Policy update policy1: block send_email for payment data",
    "6. Policy new: block web_fetch for PII",
    "7. Policy prioritize policy2 1"
  ].join("\n");
}

export async function applyPolicyCommand({ policyFilePath, state, command, actor }) {
  if (command.kind === "none") {
    return { state, message: "" };
  }
  if (command.kind === "help") {
    return { state, message: formatPolicyHelp() };
  }
  if (command.kind === "list") {
    if (!state.policy.rules.length) {
      return { state, message: `Policy version ${state.version}. No explicit rules.` };
    }
    const lines = state.policy.rules.map((rule, idx) => `${idx + 1}. ${formatRule(rule)}`);
    return { state, message: `Policy version ${state.version}:\n${lines.join("\n")}` };
  }
  if (command.kind === "get") {
    const rule = state.policy.rules.find((entry) => entry.id === command.id);
    return {
      state,
      message: rule ? `Policy rule:\n- ${formatRule(rule)}` : `Policy rule not found: ${command.id}`
    };
  }
  if (command.kind === "reset") {
    const nextState = await persistNextState(
      policyFilePath,
      state,
      { rules: [] },
      actor,
      command.reason || "Policy reset"
    );
    return { state: nextState, message: `Policy reset. Version ${nextState.version}.` };
  }
  if (command.kind === "delete") {
    const rules = state.policy.rules.filter((rule) => rule.id !== command.id);
    const nextState = await persistNextState(
      policyFilePath,
      state,
      { rules },
      actor,
      command.reason || `Policy delete: ${command.id}`
    );
    return {
      state: nextState,
      message:
        rules.length === state.policy.rules.length
          ? `No matching rule removed (${command.id}).`
          : `Policy rule removed: ${command.id}. Version ${nextState.version}.`
    };
  }
  if (command.kind === "reorder") {
    const rules = [...state.policy.rules];
    const index = rules.findIndex((rule) => rule.id === command.id);
    if (index === -1) {
      return { state, message: `Policy rule not found: ${command.id}` };
    }
    const clamped = Math.min(Math.max(command.position, 1), rules.length);
    const [rule] = rules.splice(index, 1);
    rules.splice(clamped - 1, 0, rule);
    const nextState = await persistNextState(
      policyFilePath,
      state,
      { rules },
      actor,
      command.reason || `Policy reorder: ${command.id}`
    );
    return { state: nextState, message: `Policy ${command.id} moved to position ${clamped}.` };
  }
  if (command.kind === "update") {
    if (!isPlainObject(command.update)) {
      return { state, message: "Policy update rejected: invalid payload." };
    }
    const mode = command.update.mode === "replace" ? "replace" : "merge";
    const updates = Array.isArray(command.update.rules)
      ? command.update.rules.map((rule) => normalizeRule(rule)).filter(Boolean)
      : [];
    // Allow empty rules in `replace` mode: this is how callers clear all
    // policy rules atomically. Reject only when merge-mode update has nothing
    // to add, since that would be a no-op.
    if (!updates.length && mode !== "replace") {
      return { state, message: "Policy update rejected: no valid rules." };
    }
    const nextRules = mode === "replace" ? updates : mergeRules(state.policy.rules, updates);
    const action = mode === "replace" && updates.length === 0 ? "cleared" : "updated";
    const nextState = await persistNextState(
      policyFilePath,
      state,
      { rules: nextRules },
      actor,
      command.update.reason || "Policy update"
    );
    return { state: nextState, message: `Policy ${action}. Version ${nextState.version}.` };
  }
  return { state, message: "No policy changes applied." };
}

