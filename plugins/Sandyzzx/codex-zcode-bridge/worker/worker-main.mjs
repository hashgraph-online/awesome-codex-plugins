// src/adapters/zcode-app-server-adapter.ts
import { spawn as spawn2 } from "node:child_process";
import { homedir as homedir3 } from "node:os";

// src/adapters/agent-report.ts
var TEST_STATUSES = /* @__PURE__ */ new Set(["passed", "failed", "not_run"]);
var MAX_SCAN_CHARS = 4e5;
function parseAgentReport(responseText) {
  let lastError = null;
  let lastCandidate = null;
  for (const candidate of extractJsonObjects(responseText)) {
    const validated = validateAgentReport(candidate);
    if (validated.ok) {
      return { report: validated.report, candidate: validated.report, error: null };
    }
    lastError = validated.error;
    lastCandidate = extractReportCandidate(candidate);
  }
  return {
    report: null,
    candidate: lastCandidate,
    error: lastError ?? "no JSON object found in the response text"
  };
}
function extractReportCandidate(value) {
  if (!isPlainObject(value)) return null;
  const candidate = {};
  if (typeof value["summary"] === "string") candidate.summary = value["summary"];
  if (isStringArray(value["files_changed"])) candidate.files_changed = value["files_changed"];
  if (isStringArray(value["issues"])) candidate.issues = value["issues"];
  if (typeof value["needs_master_decision"] === "boolean") candidate.needs_master_decision = value["needs_master_decision"];
  if (Array.isArray(value["tests"])) {
    const tests = [];
    for (const entry of value["tests"]) {
      const test = validateTestReport(entry);
      if (!test.ok) return candidate;
      tests.push(test.test);
    }
    candidate.tests = tests;
  }
  return Object.keys(candidate).length ? candidate : null;
}
function validateAgentReport(value) {
  if (!isPlainObject(value)) {
    return { ok: false, error: "report is not a JSON object" };
  }
  const summary = value["summary"];
  if (typeof summary !== "string" || summary.trim().length === 0) {
    return { ok: false, error: "report.summary must be a non-empty string" };
  }
  const filesChanged = value["files_changed"];
  if (!isStringArray(filesChanged)) {
    return { ok: false, error: "report.files_changed must be an array of strings" };
  }
  const testsRaw = value["tests"];
  if (!Array.isArray(testsRaw)) {
    return { ok: false, error: "report.tests must be an array" };
  }
  const tests = [];
  for (const entry of testsRaw) {
    const test = validateTestReport(entry);
    if (!test.ok) {
      return { ok: false, error: `report.tests entry invalid: ${test.error}` };
    }
    tests.push(test.test);
  }
  const issues = value["issues"];
  if (!isStringArray(issues)) {
    return { ok: false, error: "report.issues must be an array of strings" };
  }
  const needsMasterDecision = value["needs_master_decision"];
  if (typeof needsMasterDecision !== "boolean") {
    return { ok: false, error: "report.needs_master_decision must be a boolean" };
  }
  return {
    ok: true,
    report: {
      summary,
      files_changed: filesChanged,
      tests,
      issues,
      needs_master_decision: needsMasterDecision
    }
  };
}
function validateTestReport(value) {
  if (!isPlainObject(value)) {
    return { ok: false, error: "entry is not an object" };
  }
  const command = value["command"];
  if (typeof command !== "string") {
    return { ok: false, error: "command must be a string" };
  }
  const status = value["status"];
  if (typeof status !== "string" || !TEST_STATUSES.has(status)) {
    return { ok: false, error: "status must be one of passed|failed|not_run" };
  }
  const details = value["details"];
  if (details !== void 0 && typeof details !== "string") {
    return { ok: false, error: "details must be a string when present" };
  }
  return {
    ok: true,
    test: details === void 0 ? { command, status } : { command, status, details }
  };
}
function* extractJsonObjects(text) {
  if (text.trimStart().startsWith("{")) {
    try {
      yield JSON.parse(text);
    } catch {
    }
  }
  const limit = Math.min(text.length, MAX_SCAN_CHARS);
  let depth = 0;
  let inString = false;
  let escaped = false;
  let start = -1;
  for (let i = 0; i < limit; i++) {
    const ch = text[i];
    if (inString) {
      if (escaped) {
        escaped = false;
      } else if (ch === "\\") {
        escaped = true;
      } else if (ch === '"') {
        inString = false;
      }
      continue;
    }
    if (ch === '"') {
      inString = true;
      continue;
    }
    if (ch === "{") {
      if (depth === 0) start = i;
      depth++;
    } else if (ch === "}") {
      if (depth > 0) {
        depth--;
        if (depth === 0 && start >= 0) {
          const slice = text.slice(start, i + 1);
          try {
            yield JSON.parse(slice);
          } catch {
          }
          start = -1;
        }
      }
    }
  }
}
function isStringArray(value) {
  return Array.isArray(value) && value.every((entry) => typeof entry === "string");
}
function isPlainObject(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

// src/prompts/task-prompt.ts
var MAX_PROMPT_CHARS = 6e4;
var MAX_SECTION_CHARS = 4e3;
var MAX_CONTEXT_CHARS = 2e3;
function buildTaskPrompt(task) {
  const sections = [
    `TASK ID: ${task.task_id}`,
    "You are a subordinate coding agent executing one bounded task inside the current working directory. Stay inside the workspace; do not touch files outside it.",
    `PROJECT WORKSPACE: ${task.workspace}`,
    ...task.worktree_path ? [`HOST-SELECTED EXECUTION WORKTREE: ${task.worktree_path}. Make task changes in the current working directory, which is this worktree; the project workspace above identifies its parent project.`] : [],
    ...task.model ? [`REQUESTED ZCODE MODEL: ${task.model.provider_id}/${task.model.model_id}${task.model.reasoning_level ? ` (reasoning level: ${task.model.reasoning_level})` : ""}. The Bridge configures this model for the session.`] : [],
    ...task.timeout_ms ? [`EXECUTION TIME LIMIT: ${task.timeout_ms} ms for this attempt.`] : [],
    `OBJECTIVE
${task.objective}`,
    renderList("REQUIREMENTS", task.requirements),
    renderPaths("ALLOWED PATHS (write only inside these when provided)", task.allowed_paths),
    renderPaths("FORBIDDEN PATHS (never create, modify, or delete)", task.forbidden_paths),
    renderList(
      "ACCEPTANCE CRITERIA (the master verifies these independently; do not self-certify)",
      task.acceptance_criteria
    ),
    renderList(
      "TEST COMMANDS (run the applicable ones and report a status for each)",
      task.test_commands
    ),
    DECISION_RULE
  ];
  if (task.context && task.context.trim().length > 0) {
    sections.push(`CONTEXT
${bounded(task.context, MAX_CONTEXT_CHARS)}`);
  }
  return joinBoundedPreservingTail([...sections, OUTPUT_CONTRACT], OUTPUT_CONTRACT);
}
function buildContinuePrompt(input) {
  const { task, feedback, additionalRequirements, previousSessionId, previousResult } = input;
  const sections = [
    `TASK ID: ${task.task_id}`,
    "You are a subordinate coding agent continuing a previous task in the same workspace. Stay inside the workspace.",
    ...task.model ? [`REQUESTED ZCODE MODEL: ${task.model.provider_id}/${task.model.model_id}${task.model.reasoning_level ? ` (reasoning level: ${task.model.reasoning_level})` : ""}. The Bridge configures this model for the session.`] : []
  ];
  if (previousSessionId) {
    sections.push(
      `This run resumes persisted session ${previousSessionId}; earlier conversation context may be available.`
    );
  }
  if (previousResult) {
    sections.push(
      `PREVIOUS RESULT (normalized claims from the previous attempt)
${bounded(
        JSON.stringify(previousResult, null, 2),
        MAX_SECTION_CHARS
      )}`
    );
    if (previousResult.error_code === "invalid_agent_report") {
      sections.push(
        "REPORT REPAIR MODE: The previous attempt's execution has already ended; only its final report failed validation. Do not edit files, rerun tests, or repeat task work. Reconstruct the final JSON report from the previous response and report_candidate. Do not guess missing facts. If a required boolean or other fact cannot be established, set needs_master_decision=true and describe the uncertainty in issues."
      );
    }
  }
  sections.push(`MASTER FEEDBACK (address every point)
${feedback}`);
  if (additionalRequirements.length > 0) {
    sections.push(renderList("ADDITIONAL REQUIREMENTS", [...additionalRequirements]));
  }
  sections.push(`ORIGINAL TASK
${buildTaskPrompt(task)}`);
  return joinBoundedPreservingTail(sections, OUTPUT_CONTRACT);
}
var OUTPUT_CONTRACT = [
  "OUTPUT CONTRACT (mandatory)",
  "Your final response must be exactly one JSON object with no markdown fences and no text before or after it, matching this shape:",
  '{"summary": string, "files_changed": string[], "tests": [{"command": string, "status": "passed" | "failed" | "not_run", "details"?: string}], "issues": string[], "needs_master_decision": boolean}',
  "List every file you created or modified in files_changed (workspace-relative paths). Give one tests entry per applicable test command; use status not_run when a command was not applicable or could not run. Record problems in issues. Set needs_master_decision=true only when a required decision is outside your authority; never guess."
].join("\n");
var DECISION_RULE = [
  "DECISION RULE",
  "Use only this task package, this prompt, repository files you inspect, and available tools; do not assume access to the calling host's conversation.",
  "Do not choose unresolved items explicitly listed under OPEN DECISIONS; a later explicit Master Feedback decision resolves that item. Also escalate conflicting requirements or missing decisions that would materially change externally visible behavior, even when the calling host did not list them. Record the exact question in issues and set needs_master_decision=true. Continue independent work that does not depend on the decision. For low-impact implementation choices, use the simplest consistent option and state the assumption in issues."
].join("\n");
function renderList(title, items) {
  if (items.length === 0) {
    return `${title}
- (none)`;
  }
  return `${title}
${items.map((item) => `- ${item}`).join("\n")}`;
}
function renderPaths(title, paths) {
  if (paths.length === 0) {
    return `${title}
- (unspecified; still write only within the workspace)`;
  }
  return `${title}
${paths.map((item) => `- ${item}`).join("\n")}`;
}
function bounded(text, maxChars) {
  if (text.length <= maxChars) return text;
  return `${text.slice(0, maxChars)}\u2026[truncated]`;
}
function joinBoundedPreservingTail(sections, requiredTail) {
  const joined = sections.join("\n\n");
  if (joined.length <= MAX_PROMPT_CHARS) return joined;
  void requiredTail;
  throw new Error(`task prompt exceeds ${MAX_PROMPT_CHARS} characters; shorten the task package without dropping constraints`);
}

// src/runtime/errors.ts
var BridgeError = class extends Error {
  code;
  constructor(code, message, options) {
    super(message, options);
    this.name = "BridgeError";
    this.code = code;
  }
};

// src/runtime/resolver.ts
import { accessSync, existsSync, readFileSync, statSync } from "node:fs";
import { homedir as homedir2 } from "node:os";
import path2 from "node:path";
import { fileURLToPath } from "node:url";

// src/host/profile.ts
import { homedir } from "node:os";
import path from "node:path";
function codexHostProfile(homeDirectory = homedir()) {
  return { name: "codex-zcode-bridge", settingsDirectory: path.join(homeDirectory, ".codex", "codex-zcode-bridge") };
}
function validateHostProfile(host) {
  if (!host || typeof host.name !== "string" || !host.name.trim() || typeof host.settingsDirectory !== "string" || !path.isAbsolute(host.settingsDirectory)) throw new Error("invalid Bridge host profile");
  if (host.legacySettingsDirectories !== void 0 && (!Array.isArray(host.legacySettingsDirectories) || host.legacySettingsDirectories.some((directory) => typeof directory !== "string" || !path.isAbsolute(directory)))) throw new Error("host migration directories must be absolute");
  if (host.workerEntryPath !== void 0 && (typeof host.workerEntryPath !== "string" || !path.isAbsolute(host.workerEntryPath))) throw new Error("host worker entry must be absolute");
  if (host.instructions !== void 0 && typeof host.instructions !== "string") throw new Error("host instructions must be text");
  if (host.defaultDataRoot !== void 0 && (typeof host.defaultDataRoot !== "string" || !path.isAbsolute(host.defaultDataRoot))) throw new Error("host default data root must be absolute");
  return host;
}

// src/runtime/resolver.ts
var PERSISTED_RUNTIME_KEYS = [
  "ZCODE_BRIDGE_NODE",
  "ZCODE_BRIDGE_ZCODE_CJS",
  "ZCODE_BRIDGE_DATA_DIR",
  "ZCODE_BUILTIN_PROVIDER_CONFIG_FILE",
  "ZCODE_PERSONAL_PROVIDER_CONFIG_FILE",
  "ZCODE_HOME",
  "ZCODE_DATA_BASE_DIR",
  "ZCODE_WINDOWS_APP_INSTALL_DIR",
  "ZCODE_BRIDGE_DEFAULT_PROVIDER_ID",
  "ZCODE_BRIDGE_DEFAULT_MODEL_ID",
  "ZCODE_BRIDGE_DEFAULT_REASONING_LEVEL",
  "ZCODE_BRIDGE_MODE",
  "ZCODE_BRIDGE_MAX_CONCURRENT_WORKERS",
  "ZCODE_BRIDGE_TIMEOUT_MS"
];
function loadPersistedRuntimeEnvironment(source, homeDir = homedir2(), host = codexHostProfile(homeDir)) {
  validateHostProfile(host);
  const settingsPaths = [host.settingsDirectory, ...host.legacySettingsDirectories ?? []].map((directory) => path2.join(directory, "runtime-config.json"));
  const legacyDataRoot = source["ZCODE_BRIDGE_DATA_DIR"]?.trim();
  if (legacyDataRoot && path2.isAbsolute(legacyDataRoot)) {
    settingsPaths.push(path2.join(legacyDataRoot, "runtime-config.json"));
  }
  let parsed = null;
  const seenPaths = /* @__PURE__ */ new Set();
  for (const settingsPath of settingsPaths) {
    const normalized = path2.resolve(settingsPath);
    const identity = process.platform === "win32" ? normalized.toLocaleLowerCase("en-US") : normalized;
    if (seenPaths.has(identity)) continue;
    seenPaths.add(identity);
    try {
      if (statSync(normalized).size > 64 * 1024) throw new Error("runtime settings exceed 64 KB");
      const candidate = JSON.parse(readFileSync(normalized, "utf8"));
      if (isPlainObject2(candidate)) {
        parsed = candidate;
        break;
      }
      throw new Error("runtime settings must be an object");
    } catch (error) {
      if (error.code === "ENOENT") continue;
      throw new BridgeError("provider_config_invalid", `invalid Bridge runtime settings: ${normalized}`, { cause: error });
    }
  }
  if (!parsed) return { ...source };
  const env = { ...source };
  for (const key of PERSISTED_RUNTIME_KEYS) {
    if (!Object.prototype.hasOwnProperty.call(parsed, key)) continue;
    const value = parsed[key];
    if (typeof value === "string") env[key] = value.trim();
    else if (value === null) env[key] = "";
    else throw new BridgeError("provider_config_invalid", `Bridge runtime setting ${key} must be a string or null`);
  }
  return env;
}
var NodeRuntimeResolver = class {
  #env;
  #homeDir;
  #packageRoot;
  #host;
  constructor(options = {}) {
    this.#env = options.env ?? process.env;
    this.#homeDir = options.homeDir ?? homedir2();
    this.#packageRoot = options.packageRoot ?? null;
    this.#host = validateHostProfile(options.host ?? codexHostProfile(this.#homeDir));
  }
  async resolve() {
    const env = loadPersistedRuntimeEnvironment(this.#env, this.#homeDir, this.#host);
    const zcodeHome = resolveZcodeHome(env);
    let nodeExecutable = "node";
    const nodeOverride = env["ZCODE_BRIDGE_NODE"]?.trim();
    if (nodeOverride) {
      this.#assertReadableFile(
        nodeOverride,
        "ZCODE_BRIDGE_NODE is set but is not a readable file"
      );
      nodeExecutable = nodeOverride;
    }
    let zcodeEntrypoint;
    const entryOverride = env["ZCODE_BRIDGE_ZCODE_CJS"]?.trim();
    if (entryOverride) {
      this.#assertReadableFile(
        entryOverride,
        "ZCODE_BRIDGE_ZCODE_CJS is set but is not a readable file"
      );
      zcodeEntrypoint = entryOverride;
    } else {
      const candidates = installCandidates(env, ["resources", "glm", "zcode.cjs"]);
      const discovered = candidates.find(isReadableFile);
      if (!discovered) {
        throw new BridgeError(
          "runtime_not_found",
          `zcode.cjs was not found; searched: ${candidates.join(", ") || "(no installation roots available)"}`
        );
      }
      zcodeEntrypoint = discovered;
    }
    const builtinEnv = env["ZCODE_BUILTIN_PROVIDER_CONFIG_FILE"]?.trim() || null;
    const personalEnv = env["ZCODE_PERSONAL_PROVIDER_CONFIG_FILE"]?.trim() || null;
    let builtinConfigFile;
    let personalConfigFile;
    if (builtinEnv && personalEnv) {
      this.#validateBuiltinConfig(builtinEnv);
      this.#validatePersonalConfig(personalEnv);
      builtinConfigFile = builtinEnv;
      personalConfigFile = personalEnv;
    } else {
      if (builtinEnv) {
        this.#validateBuiltinConfig(builtinEnv);
        builtinConfigFile = builtinEnv;
      } else {
        const candidates = installCandidates(env, [
          "resources",
          "config",
          "provider",
          "zcode-builtin.json"
        ]);
        const discovered = candidates.find(isReadableFile);
        if (!discovered) {
          throw new BridgeError(
            "provider_config_missing",
            "ZCODE_BUILTIN_PROVIDER_CONFIG_FILE is not set and no builtin provider config was found in the ZCode installation; searched: " + (candidates.join(", ") || "(no installation roots available)")
          );
        }
        this.#validateBuiltinConfig(discovered);
        builtinConfigFile = discovered;
      }
      if (personalEnv) {
        this.#validatePersonalConfig(personalEnv);
        personalConfigFile = personalEnv;
      } else {
        const candidates = zcodeHome ? [path2.join(zcodeHome, "v2", "provider_config.json")] : [
          env["ZCODE_DATA_BASE_DIR"]?.trim(),
          ...configuredDataBaseDirs(this.#homeDir),
          this.#homeDir
        ].filter((base) => Boolean(base)).filter((base, index, values) => values.indexOf(base) === index).map((base) => path2.join(base, ".zcode", "v2", "provider_config.json"));
        const existing = candidates.filter((candidate) => existsSync(candidate));
        if (existing.length === 0) {
          throw new BridgeError(
            "provider_config_missing",
            "ZCODE_PERSONAL_PROVIDER_CONFIG_FILE is not set and no personal provider config exists at any of: " + candidates.join(", ")
          );
        }
        let accepted = null;
        let lastError = null;
        for (const candidate of existing) {
          try {
            this.#validatePersonalConfig(candidate);
            accepted = candidate;
            break;
          } catch (error) {
            lastError = error instanceof Error ? error.message : String(error);
          }
        }
        if (!accepted) {
          throw new BridgeError(
            "provider_config_invalid",
            `No usable personal provider config among: ${existing.join(", ")}; last validation failure: ${lastError ?? "unknown"}`
          );
        }
        personalConfigFile = accepted;
      }
    }
    if (zcodeHome && !samePath(personalConfigFile, path2.join(zcodeHome, "v2", "provider_config.json"))) {
      throw new BridgeError(
        "provider_config_invalid",
        `ZCODE_PERSONAL_PROVIDER_CONFIG_FILE must be ZCODE_HOME/v2/provider_config.json (${zcodeHome})`
      );
    }
    const dataOverride = env["ZCODE_BRIDGE_DATA_DIR"]?.trim();
    let dataRoot2;
    if (dataOverride) {
      if (!path2.isAbsolute(dataOverride)) {
        throw new Error(
          `ZCODE_BRIDGE_DATA_DIR must be an absolute path when set, got: ${dataOverride}`
        );
      }
      dataRoot2 = path2.normalize(dataOverride);
    } else {
      dataRoot2 = this.#packageRoot ?? findPackageRoot();
    }
    return {
      nodeExecutable,
      zcodeEntrypoint,
      providerBuiltinConfigFile: builtinConfigFile,
      providerPersonalConfigFile: personalConfigFile,
      dataRoot: dataRoot2
    };
  }
  #assertReadableFile(filePath, label) {
    if (!isReadableFile(filePath)) {
      throw new BridgeError("runtime_not_found", `${label}: ${filePath}`);
    }
  }
  /**
   * Structure validation only. The verified differential signal for the
   * CLI-created stub is an empty providerRules map (see docs/ZCODE_RUNTIME.md);
   * rejecting it implements "never silently select a known stub".
   */
  #validatePersonalConfig(filePath) {
    const parsed = this.#readJsonConfig(filePath, "personal provider config");
    const config = parsed["config"];
    if (!isPlainObject2(config)) {
      throw new BridgeError(
        "provider_config_invalid",
        `Personal provider config has no config object: ${filePath}`
      );
    }
    const providerConfigRules = config["providerConfigRules"];
    const rules = isPlainObject2(providerConfigRules) ? providerConfigRules["providerRules"] : void 0;
    if (!isNonEmptyCollection(rules)) {
      throw new BridgeError(
        "provider_config_invalid",
        `Personal provider config contains no provider rules (this matches the known CLI-created stub shape): ${filePath}`
      );
    }
  }
  #validateBuiltinConfig(filePath) {
    const parsed = this.#readJsonConfig(filePath, "builtin provider config");
    if (!isPlainObject2(parsed["config"])) {
      throw new BridgeError(
        "provider_config_invalid",
        `Builtin provider config has no config object: ${filePath}`
      );
    }
  }
  #readJsonConfig(filePath, label) {
    if (!isReadableFile(filePath)) {
      throw new BridgeError("provider_config_missing", `${label} not found: ${filePath}`);
    }
    let text;
    try {
      text = readFileSync(filePath, "utf8");
    } catch (error) {
      throw new BridgeError(
        "provider_config_invalid",
        `${label} is not readable: ${filePath} (${errorText(error)})`
      );
    }
    let parsed;
    try {
      parsed = JSON.parse(text);
    } catch (error) {
      throw new BridgeError(
        "provider_config_invalid",
        `${label} is not valid JSON: ${filePath}`
      );
    }
    if (!isPlainObject2(parsed)) {
      throw new BridgeError("provider_config_invalid", `${label} is not a JSON object: ${filePath}`);
    }
    return parsed;
  }
};
function installCandidates(env, relative) {
  const roots = [
    env["ZCODE_WINDOWS_APP_INSTALL_DIR"]?.trim(),
    env["LOCALAPPDATA"]?.trim() ? path2.join(env["LOCALAPPDATA"].trim(), "Programs", "ZCode") : null,
    env["ProgramFiles"]?.trim() ? path2.join(env["ProgramFiles"].trim(), "ZCode") : null
  ].filter((root) => Boolean(root));
  return roots.map((root) => path2.join(root, ...relative));
}
function configuredDataBaseDirs(homeDir) {
  const candidates = [path2.join(homeDir, ".zcode", "v2", "setting.json")];
  for (const settingPath of candidates) {
    try {
      const parsed = JSON.parse(readFileSync(settingPath, "utf8"));
      if (!isPlainObject2(parsed)) continue;
      const dataBaseDir = parsed["dataBaseDir"];
      if (typeof dataBaseDir === "string" && path2.isAbsolute(dataBaseDir.trim())) {
        return [path2.normalize(dataBaseDir.trim())];
      }
    } catch {
    }
  }
  return [];
}
function resolveZcodeHome(env) {
  const configured = env["ZCODE_HOME"]?.trim();
  if (!configured) return null;
  if (!path2.isAbsolute(configured)) {
    throw new BridgeError("provider_config_invalid", "ZCODE_HOME must be an absolute path");
  }
  const resolved = path2.normalize(configured);
  if (path2.basename(resolved).toLowerCase() !== ".zcode") {
    throw new BridgeError(
      "provider_config_invalid",
      "ZCODE_HOME must name a .zcode directory so app-server can use the same data root"
    );
  }
  try {
    if (!statSync(resolved).isDirectory()) {
      throw new BridgeError("provider_config_invalid", `ZCODE_HOME is not a directory: ${resolved}`);
    }
  } catch (error) {
    if (error instanceof BridgeError) throw error;
    throw new BridgeError("provider_config_missing", `ZCODE_HOME directory does not exist: ${resolved}`);
  }
  return resolved;
}
function samePath(left, right) {
  const resolvedLeft = path2.resolve(left);
  const resolvedRight = path2.resolve(right);
  return process.platform === "win32" ? resolvedLeft.toLowerCase() === resolvedRight.toLowerCase() : resolvedLeft === resolvedRight;
}
function isReadableFile(filePath) {
  try {
    if (!existsSync(filePath) || !statSync(filePath).isFile()) return false;
    accessSync(filePath);
    return true;
  } catch {
    return false;
  }
}
function findPackageRoot(startDir) {
  let current = startDir ?? path2.dirname(fileURLToPath(import.meta.url));
  for (let depth = 0; depth < 10; depth++) {
    if (existsSync(path2.join(current, "package.json"))) {
      return current;
    }
    const parent = path2.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  throw new Error(
    `Cannot locate the Bridge package root (no package.json above ${startDir ?? "module directory"})`
  );
}
function isPlainObject2(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
function isNonEmptyCollection(value) {
  if (Array.isArray(value)) return value.length > 0;
  if (isPlainObject2(value)) return Object.keys(value).length > 0;
  return false;
}
function errorText(error) {
  const message = error instanceof Error ? error.message : String(error);
  return message.length > 300 ? `${message.slice(0, 300)}\u2026` : message;
}

// src/adapters/process-spawn.ts
import { spawn } from "node:child_process";
function appendBounded(current, chunk, maxBytes) {
  if (!(maxBytes > 0)) return { value: current.value + chunk, truncated: current.truncated };
  const remaining = maxBytes - Buffer.byteLength(current.value, "utf8");
  if (remaining <= 0) return chunk ? { value: current.value, truncated: true } : current;
  const bytes = Buffer.from(chunk, "utf8");
  if (bytes.length <= remaining) {
    return { value: current.value + chunk, truncated: current.truncated };
  }
  return {
    value: current.value + bytes.subarray(0, remaining).toString("utf8"),
    truncated: true
  };
}
function isProcessRunning(pid) {
  if (!Number.isInteger(pid) || pid <= 0) return false;
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    if (error.code === "EPERM") return true;
    if (error.code === "ESRCH") return false;
    throw error;
  }
}
var terminateProcessTree = async (pid, options = {}) => {
  if (!Number.isInteger(pid) || pid <= 0) {
    throw new Error(`A positive integer PID is required, got: ${pid}`);
  }
  if (process.platform === "win32") {
    const result = await runCommand("taskkill", ["/PID", String(pid), "/T", "/F"], {
      timeoutMs: 15e3
    });
    if (result.code !== 0) {
      throw new Error(
        result.stderr.trim() || `taskkill exited with code ${String(result.code)}`
      );
    }
    if (!await waitForPidExit(pid, options.killWaitMs ?? 2e3)) {
      throw new Error(`Process tree ${pid} still running after taskkill reported success`);
    }
    return { pid, signal: "SIGKILL", verified: true };
  }
  signalProcessTree(pid, "SIGTERM");
  if (await waitForProcessTreeExit(pid, options.graceMs ?? 500)) {
    return { pid, signal: "SIGTERM", verified: true };
  }
  signalProcessTree(pid, "SIGKILL");
  if (!await waitForProcessTreeExit(pid, options.killWaitMs ?? 2e3)) {
    throw new Error(`Process tree ${pid} did not exit after SIGKILL`);
  }
  return { pid, signal: "SIGKILL", verified: true };
};
function runCommand(command, args, options) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      shell: false,
      windowsHide: true,
      stdio: ["ignore", "pipe", "pipe"]
    });
    let stdout = { value: "", truncated: false };
    let stderr = { value: "", truncated: false };
    child.stdout?.setEncoding("utf8");
    child.stderr?.setEncoding("utf8");
    child.stdout?.on("data", (chunk) => {
      stdout = appendBounded(stdout, chunk, options.maxOutputBytes ?? 1e6);
    });
    child.stderr?.on("data", (chunk) => {
      stderr = appendBounded(stderr, chunk, options.maxOutputBytes ?? 1e6);
    });
    let timedOut = false;
    const timer = options.timeoutMs && options.timeoutMs > 0 ? setTimeout(() => {
      timedOut = true;
      try {
        child.kill("SIGKILL");
      } catch {
      }
    }, options.timeoutMs) : null;
    timer?.unref();
    child.on("error", (error) => {
      if (timer) clearTimeout(timer);
      reject(error);
    });
    child.on("close", (code, signal) => {
      if (timer) clearTimeout(timer);
      resolve({
        code: timedOut ? null : code,
        signal: timedOut ? "SIGKILL" : signal,
        stdout: stdout.value,
        stderr: stderr.value
      });
    });
  });
}
function signalProcessTree(pid, signal) {
  try {
    process.kill(-pid, signal);
  } catch (error) {
    if (error.code === "ESRCH") {
      try {
        process.kill(pid, signal);
      } catch (inner) {
        if (inner.code !== "ESRCH") throw inner;
      }
    } else {
      throw error;
    }
  }
}
function isProcessTreeRunning(pid) {
  try {
    process.kill(-pid, 0);
    return true;
  } catch (error) {
    if (error.code === "EPERM") return true;
    if (error.code === "ESRCH") return isProcessRunning(pid);
    throw error;
  }
}
async function waitForPidExit(pid, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (isProcessRunning(pid) && Date.now() < deadline) {
    await sleep(20);
  }
  return !isProcessRunning(pid);
}
async function waitForProcessTreeExit(pid, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (isProcessTreeRunning(pid) && Date.now() < deadline) {
    await sleep(20);
  }
  return !isProcessTreeRunning(pid);
}
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// src/runtime/child-env.ts
var WINDOWS_OS_ENV = /* @__PURE__ */ new Set([
  "PATH",
  "SYSTEMROOT",
  "WINDIR",
  "COMSPEC",
  "PATHEXT",
  "TEMP",
  "TMP",
  "USERPROFILE",
  "HOMEDRIVE",
  "HOMEPATH",
  "APPDATA",
  "LOCALAPPDATA",
  "PROGRAMDATA",
  "OS",
  "PROCESSOR_ARCHITECTURE",
  "NUMBER_OF_PROCESSORS"
]);
var POSIX_OS_ENV = /* @__PURE__ */ new Set([
  "PATH",
  "HOME",
  "TMPDIR",
  "TMP",
  "TEMP",
  "LANG",
  "LC_ALL",
  "LC_CTYPE",
  "TERM",
  "XDG_CONFIG_HOME",
  "XDG_DATA_HOME",
  "XDG_CACHE_HOME"
]);
function createMinimalOsEnv(source) {
  const allowed = process.platform === "win32" ? WINDOWS_OS_ENV : POSIX_OS_ENV;
  const env = {};
  for (const [key, value] of Object.entries(source)) {
    if (allowed.has(key.toUpperCase()) && value !== void 0) env[key] = value;
  }
  return env;
}

// src/runtime/account-provider.ts
import { createHash } from "node:crypto";
import { existsSync as existsSync2, readFileSync as readFileSync2 } from "node:fs";
import path3 from "node:path";
function buildAccountProviderPayload(config) {
  const table = readJson(config.providerBuiltinConfigFile);
  const providerRules = readProviderRules(table).filter(isRecord).map((rule) => rule).filter((rule) => rule.config?.access?.type === "zhipu-account" && typeof rule.providerId === "string");
  if (!providerRules.length) return null;
  const dataDir = zcodeV2DataDir(config.providerPersonalConfigFile);
  if (!dataDir) return null;
  const credentials = readJson(path3.join(dataDir, "config.json"));
  const credentialProviders = asRecord(credentials?.provider);
  const cache = readJson(path3.join(dataDir, "coding-plan-cache.json"));
  const cacheItems = asRecord(asRecord(cache?.entryStatus).items);
  const providers = {};
  const states = {};
  for (const rule of providerRules) {
    const providerId = rule.providerId;
    const legacyId = configProviderId(providerId, rule);
    const cacheStatus = asRecord(cacheItems[legacyId]).status;
    const legacyConfig = asRecord(credentialProviders[legacyId]);
    const options = asRecord(legacyConfig.options);
    const entitled = cacheStatus === "available" || legacyConfig.enabled === true && typeof options.apiKey === "string" && options.apiKey.trim().length > 0;
    providers[providerId] = {
      ...Array.isArray(rule.config?.builtinModelIds) ? { builtinModelIds: rule.config.builtinModelIds } : {},
      access: { type: "zhipu-account", entitled }
    };
    states[providerId] = {
      availability: entitled ? "available" : "unavailable",
      entitled,
      current: entitled
    };
  }
  const revision = typeof table?.revision === "number" ? table.revision : 0;
  const resolvedBuiltinPath = path3.resolve(config.providerBuiltinConfigFile);
  return {
    revision: `account:codex-zcode-bridge:${Date.now()}`,
    basedOnZCodeBuiltinRevision: `zcode-builtin:${revision}:${createHash("sha256").update(resolvedBuiltinPath).digest("hex")}`,
    providers,
    states
  };
}
function accountProviderId(providerId, config) {
  if (providerId.startsWith("account:")) return providerId;
  const table = readJson(config.providerBuiltinConfigFile);
  for (const rawRule of readProviderRules(table)) {
    if (!isRecord(rawRule)) continue;
    const rule = rawRule;
    if (!providerId.startsWith("builtin:") && rule.providerId === providerId && rule.config?.access?.type === "zhipu-account") {
      return `account:${providerId}`;
    }
    if (typeof rule.providerId === "string" && configProviderId(rule.providerId, rule) === providerId) {
      return rule.providerId;
    }
  }
  return providerId;
}
function runtimeAuthReply(providerId, config) {
  const unavailable = {
    headersApplied: false,
    errorMessage: "Start Plan requires a ZCode desktop captcha session; this headless app-server bridge cannot provide it."
  };
  if (!providerId?.startsWith("account:")) return unavailable;
  const table = readJson(config.providerBuiltinConfigFile);
  const rule = readProviderRules(table).find(
    (candidate) => isRecord(candidate) && candidate.providerId === providerId
  );
  if (rule?.config?.access?.mode !== "individual-coding-plan") return unavailable;
  const legacyId = configProviderId(providerId, rule);
  const dataDir = zcodeV2DataDir(config.providerPersonalConfigFile);
  if (!dataDir) return unavailable;
  const credentials = readJson(path3.join(dataDir, "config.json"));
  const cache = readJson(path3.join(dataDir, "coding-plan-cache.json"));
  const status = asRecord(asRecord(asRecord(cache?.entryStatus).items)[legacyId]).status;
  const provider = asRecord(asRecord(credentials?.provider)[legacyId]);
  const options = asRecord(provider.options);
  const apiKey = typeof options.apiKey === "string" ? options.apiKey.trim() : "";
  if (!apiKey || status !== "available" && provider.enabled !== true) return unavailable;
  return { headersApplied: true, requestAuth: { apiKey } };
}
function zcodeDataBaseDir(personalProviderConfigFile) {
  const dataDir = zcodeV2DataDir(personalProviderConfigFile);
  return dataDir ? path3.dirname(path3.dirname(dataDir)) : null;
}
function zcodeTasksIndexPath(personalProviderConfigFile) {
  const dataDir = zcodeV2DataDir(personalProviderConfigFile);
  return dataDir ? path3.join(dataDir, "tasks-index.sqlite") : null;
}
function zcodeV2DataDir(personalProviderConfigFile) {
  const absolute = path3.resolve(personalProviderConfigFile);
  if (path3.basename(absolute).toLowerCase() !== "provider_config.json") return null;
  const v2Dir = path3.dirname(absolute);
  if (path3.basename(v2Dir).toLowerCase() !== "v2") return null;
  const zcodeDir = path3.dirname(v2Dir);
  if (path3.basename(zcodeDir).toLowerCase() !== ".zcode") return null;
  return v2Dir;
}
function configProviderId(providerId, rule) {
  const access = rule.config?.access;
  if (!providerId.startsWith("account:") || !access?.accountType || !access.mode) return providerId;
  const plan = access.mode === "individual-coding-plan" ? "coding-plan" : access.mode;
  return `builtin:${access.accountType}-${plan}`;
}
function readProviderRules(table) {
  const providerConfigRules = asRecord(asRecord(table?.config).providerConfigRules);
  return Array.isArray(providerConfigRules.providerRules) ? providerConfigRules.providerRules : [];
}
function readJson(filePath) {
  try {
    if (!existsSync2(filePath)) return null;
    const value = JSON.parse(readFileSync2(filePath, "utf8"));
    return isRecord(value) ? value : null;
  } catch {
    return null;
  }
}
function asRecord(value) {
  return isRecord(value) ? value : {};
}
function isRecord(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

// src/runtime/session-preferences.ts
var ZCODE_SESSION_MODES = ["plan", "build", "edit", "yolo"];
function resolveSessionPreferences(taskModel, env) {
  const providerId = env["ZCODE_BRIDGE_DEFAULT_PROVIDER_ID"]?.trim() ?? "";
  const modelId = env["ZCODE_BRIDGE_DEFAULT_MODEL_ID"]?.trim() ?? "";
  const reasoningLevel = env["ZCODE_BRIDGE_DEFAULT_REASONING_LEVEL"]?.trim() ?? "";
  const configuredMode = env["ZCODE_BRIDGE_MODE"]?.trim() || "yolo";
  if (Boolean(providerId) !== Boolean(modelId)) {
    throw new BridgeError(
      "provider_config_invalid",
      "ZCODE_BRIDGE_DEFAULT_PROVIDER_ID and ZCODE_BRIDGE_DEFAULT_MODEL_ID must be set together"
    );
  }
  if (!isSessionMode(configuredMode)) {
    throw new BridgeError(
      "provider_config_invalid",
      `ZCODE_BRIDGE_MODE must be one of: ${ZCODE_SESSION_MODES.join(", ")}`
    );
  }
  if (reasoningLevel && !taskModel && !providerId) {
    throw new BridgeError(
      "provider_config_invalid",
      "ZCODE_BRIDGE_DEFAULT_REASONING_LEVEL requires a default model pair or a per-task model"
    );
  }
  const inheritedReasoningLevel = taskModel && providerId && modelId && (providerId !== taskModel.provider_id.trim() || modelId !== taskModel.model_id.trim()) ? "" : reasoningLevel;
  const model = taskModel ? {
    provider_id: taskModel.provider_id.trim(),
    model_id: taskModel.model_id.trim(),
    ...taskModel.reasoning_level?.trim() || inheritedReasoningLevel ? { reasoning_level: taskModel.reasoning_level?.trim() || inheritedReasoningLevel } : {}
  } : providerId && modelId ? {
    provider_id: providerId,
    model_id: modelId,
    ...reasoningLevel ? { reasoning_level: reasoningLevel } : {}
  } : null;
  if (model && (!model.provider_id || !model.model_id)) {
    throw new BridgeError("provider_config_invalid", "Configured provider and model IDs must not be blank");
  }
  return {
    mode: configuredMode,
    model,
    modelSource: taskModel ? "task" : model ? "user_default" : "zcode_default"
  };
}
function isSessionMode(value) {
  return ZCODE_SESSION_MODES.includes(value);
}

// src/runtime/task-timeout.ts
var DEFAULT_TASK_TIMEOUT_MS = 60 * 60 * 1e3;
var MAX_TASK_TIMEOUT_MS = 4 * 60 * 60 * 1e3;
var MIN_TASK_TIMEOUT_MS = 60 * 1e3;
function resolveTaskTimeout(task, env) {
  if (task.timeout_ms !== void 0) return validateTaskTimeout(task.timeout_ms);
  const raw = env["ZCODE_BRIDGE_TIMEOUT_MS"]?.trim();
  if (!raw) return DEFAULT_TASK_TIMEOUT_MS;
  const value = Number(raw);
  if (!Number.isSafeInteger(value) || value < MIN_TASK_TIMEOUT_MS || value > MAX_TASK_TIMEOUT_MS) {
    return DEFAULT_TASK_TIMEOUT_MS;
  }
  return value;
}
function validateTaskTimeout(value) {
  if (!Number.isSafeInteger(value) || value < MIN_TASK_TIMEOUT_MS || value > MAX_TASK_TIMEOUT_MS) {
    throw new Error(`timeout_ms must be an integer from ${MIN_TASK_TIMEOUT_MS} to ${MAX_TASK_TIMEOUT_MS}`);
  }
  return value;
}

// src/adapters/task-index-sync.ts
import { existsSync as existsSync3 } from "node:fs";
var databaseSyncPromise = null;
async function loadDatabaseSync() {
  databaseSyncPromise ??= import("node:sqlite").then((module) => module.DatabaseSync).catch(() => null);
  return databaseSyncPromise;
}
async function registerDesktopTask(entry) {
  await withDatabase(entry.databasePath, (database) => {
    requireTaskTable(database);
    const now = Date.now();
    const title = entry.title.trim().slice(0, 80) || entry.bridgeTaskId;
    const metaJson = JSON.stringify({
      taskId: entry.sessionId,
      traceId: entry.bridgeTaskId,
      title,
      titleOverridden: false,
      workspaceKey: entry.workspaceKey,
      workspacePath: entry.workspacePath,
      createdAt: now,
      updatedAt: now,
      mode: entry.mode,
      model: entry.model,
      provider: entry.provider,
      status: "running",
      target: null
    });
    database.prepare(
      "INSERT OR IGNORE INTO tasks (workspace_key, workspace_path, workspace_identity, task_id, title, task_status, provider, mode, model, created_at, updated_at, unread_at, pinned, archived, deleted, title_overridden, meta_json, searchable_text) VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 0, 0, 0, 0, ?, ?)"
    ).run(
      entry.workspaceKey,
      entry.workspacePath,
      entry.sessionId,
      title,
      "running",
      entry.provider,
      entry.mode,
      entry.model,
      now,
      now,
      metaJson,
      entry.bridgeTaskId
    );
    if (!updateOwnedStatus(database, entry, "running")) {
      throw new Error("Desktop task row already exists and is not owned by this Bridge task");
    }
  });
}
async function updateDesktopTaskStatus(entry, status) {
  await withDatabase(entry.databasePath, (database) => {
    requireTaskTable(database);
    if (!updateOwnedStatus(database, entry, status)) {
      throw new Error("Desktop task row is missing or is not owned by this Bridge task");
    }
  });
}
function updateOwnedStatus(database, entry, status) {
  const row = database.prepare(
    "SELECT meta_json FROM tasks WHERE workspace_key = ? AND task_id = ?"
  ).get(entry.workspaceKey, entry.sessionId);
  if (!row || typeof row.meta_json !== "string") return false;
  let meta;
  try {
    const parsed = JSON.parse(row.meta_json);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) return false;
    meta = parsed;
  } catch {
    return false;
  }
  if (meta["traceId"] !== entry.bridgeTaskId || meta["taskId"] !== entry.sessionId) return false;
  const now = Date.now();
  meta["updatedAt"] = now;
  if (status === null) delete meta["status"];
  else meta["status"] = status;
  database.prepare(
    "UPDATE tasks SET task_status = ?, updated_at = ?, meta_json = ? WHERE workspace_key = ? AND task_id = ?"
  ).run(status, now, JSON.stringify(meta), entry.workspaceKey, entry.sessionId);
  return true;
}
function requireTaskTable(database) {
  const columns = new Set(
    database.prepare("PRAGMA table_info(tasks)").all().map((column) => column.name).filter((name) => typeof name === "string")
  );
  const required = [
    "workspace_key",
    "workspace_path",
    "workspace_identity",
    "task_id",
    "title",
    "task_status",
    "provider",
    "mode",
    "model",
    "created_at",
    "updated_at",
    "unread_at",
    "pinned",
    "archived",
    "deleted",
    "title_overridden",
    "meta_json",
    "searchable_text"
  ];
  const missing = required.filter((name) => !columns.has(name));
  if (missing.length > 0) {
    throw new Error(`ZCode tasks-index schema is missing columns: ${missing.join(", ")}`);
  }
}
async function withDatabase(databasePath, operation) {
  if (!existsSync3(databasePath)) {
    throw new Error("ZCode Desktop tasks-index database does not exist");
  }
  const DatabaseSync = await loadDatabaseSync();
  if (!DatabaseSync) throw new Error("node:sqlite is unavailable in the Bridge runtime");
  let lastError;
  for (let attempt = 0; attempt < 3; attempt++) {
    let database = null;
    try {
      database = new DatabaseSync(databasePath, { timeout: 1e3 });
      database.exec("BEGIN IMMEDIATE");
      try {
        const result = operation(database);
        database.exec("COMMIT");
        return result;
      } catch (error) {
        database.exec("ROLLBACK");
        throw error;
      }
    } catch (error) {
      lastError = error;
      if (attempt < 2 && isDatabaseBusy(error)) {
        await new Promise((resolve) => setTimeout(resolve, 200 * (attempt + 1)));
        continue;
      }
      throw error;
    } finally {
      database?.close();
    }
  }
  throw lastError instanceof Error ? lastError : new Error("ZCode tasks-index write failed");
}
function isDatabaseBusy(error) {
  const message = error instanceof Error ? error.message : String(error);
  return /database is (busy|locked)/i.test(message);
}

// src/adapters/zcode-app-server-adapter.ts
function publicUsage(value) {
  if (!isRecord2(value)) return null;
  const result = {};
  for (const key of ["inputTokens", "outputTokens", "totalTokens", "cachedInputTokens", "reasoningTokens", "input_tokens", "output_tokens", "total_tokens", "cost"]) {
    const item = value[key];
    if (typeof item === "number" && Number.isFinite(item) && item >= 0) result[key] = item;
  }
  return Object.keys(result).length ? result : null;
}
var RPC_TIMEOUT_MS = 3e4;
var MAX_CAPTURE_CHARS = 2e6;
var ZCodeAppServerAdapter = class {
  #resolver;
  #onEvent;
  #timeoutMs;
  #childEnvBase;
  #homeDir;
  #host;
  #now;
  #resolveInteraction;
  #onOutcomeCheckpoint;
  #onInteractionState;
  #turnBindingCompatMs;
  #replayIdleMs;
  #runs = /* @__PURE__ */ new Map();
  #workspaceByTask = /* @__PURE__ */ new Map();
  constructor(options = {}) {
    this.#resolver = options.resolver ?? new NodeRuntimeResolver({ env: options.childEnvBase, homeDir: options.homeDir, host: options.host });
    this.#onEvent = options.onEvent ?? (() => void 0);
    this.#timeoutMs = options.timeoutMs ?? null;
    this.#childEnvBase = options.childEnvBase ?? process.env;
    this.#homeDir = options.homeDir ?? homedir3();
    this.#host = validateHostProfile(options.host ?? codexHostProfile(this.#homeDir));
    this.#now = options.now ?? (() => /* @__PURE__ */ new Date());
    this.#resolveInteraction = options.resolveInteraction;
    this.#onOutcomeCheckpoint = options.onOutcomeCheckpoint;
    this.#onInteractionState = options.onInteractionState;
    this.#turnBindingCompatMs = options.turnBindingCompatMs ?? 5e3;
    this.#replayIdleMs = options.replayIdleMs ?? 1e4;
  }
  async startTask(input) {
    return this.#launch(input.task, input.workspace, input.attempt, buildTaskPrompt(input.task), null);
  }
  async continueTask(input) {
    const priorWorkspace = this.#workspaceByTask.get(input.task.task_id);
    if (priorWorkspace !== void 0 && priorWorkspace !== input.workspace.canonicalPath) {
      throw new Error(`continuation workspace mismatch for task ${input.task.task_id}`);
    }
    return this.#launch(
      input.task,
      input.workspace,
      input.attempt,
      buildContinuePrompt({
        task: input.task,
        feedback: input.feedback,
        additionalRequirements: input.additionalRequirements,
        previousSessionId: input.previousSessionId,
        previousResult: input.previousResult
      }),
      input.previousSessionId
    );
  }
  async getStatus(handle) {
    const entry = this.#require(handle, "getStatus");
    return {
      state: entry.finished ? "exited" : entry.child ? "running" : "starting",
      workerPid: handle.workerPid,
      zcodePid: entry.child?.pid ?? null,
      exitCode: entry.outcome?.exitCode ?? null,
      signal: entry.outcome?.signal ?? null
    };
  }
  async getResult(handle) {
    const entry = this.#require(handle, "getResult");
    if (entry.error) throw entry.error;
    if (entry.outcome) return entry.outcome;
    return entry.runPromise;
  }
  async cancelTask(handle) {
    const entry = this.#require(handle, "cancelTask");
    if (entry.finished) return;
    entry.cancelRequested = true;
    entry.abort.abort();
    entry.rejectTurn(new Error("ZCode task cancelled"));
    try {
      await entry.runPromise;
    } catch (error) {
      if (!(error instanceof BridgeError) || error.code !== "cancelled") throw error;
    }
  }
  async #launch(task, workspace, attempt, prompt, resumeSessionId) {
    const handle = {
      taskId: task.task_id,
      attempt,
      workerPid: process.pid,
      zcodePid: null,
      startedAt: this.#now().toISOString()
    };
    let resolveTurn;
    let rejectTurn;
    const turn = new Promise((resolve, reject) => {
      resolveTurn = resolve;
      rejectTurn = reject;
    });
    void turn.catch(() => void 0);
    const entry = {
      handle,
      child: null,
      client: null,
      sessionId: resumeSessionId,
      finished: false,
      timedOut: false,
      cancelRequested: false,
      outcome: null,
      error: null,
      runPromise: Promise.resolve(null),
      resolveTurn,
      rejectTurn,
      onEvent: this.#onEvent,
      textOutputStarted: false,
      selectedModel: null,
      selectedModelSelection: null,
      selectedReasoningLevel: null,
      reasoningLevelSource: "not_reported",
      modelSource: null,
      requestedModel: null,
      requestedReasoningLevel: null,
      lastEventSeq: 0,
      lastEventAt: Date.now(),
      interactions: /* @__PURE__ */ new Map(),
      abort: new AbortController(),
      acceptingTurn: false,
      turnId: null,
      awaitingTurnStart: false,
      rpcAcceptedAt: null,
      turnStartedAt: null,
      turnCompletedAt: null,
      turnBinding: "pending",
      pendingCompletion: null,
      bindingTimer: null,
      pendingTimer: null,
      replayConsecutiveFailures: 0
    };
    this.#runs.set(handle, entry);
    this.#workspaceByTask.set(task.task_id, workspace.canonicalPath);
    entry.runPromise = this.#execute(entry, task, workspace, prompt, resumeSessionId, turn);
    void entry.runPromise.then(
      (outcome) => {
        entry.outcome = outcome;
        entry.finished = true;
      },
      (error) => {
        entry.error = error;
        entry.finished = true;
      }
    );
    return handle;
  }
  async #execute(entry, task, workspace, prompt, resumeSessionId, turn) {
    const startedAt = this.#now();
    const projectPath = workspace.sourcePath ?? workspace.canonicalPath;
    let timer;
    let warningTimer;
    let desktopTask = null;
    try {
      const runtimeEnv = loadPersistedRuntimeEnvironment(this.#childEnvBase, this.#homeDir, this.#host);
      const timeoutMs = this.#timeoutMs ?? resolveTaskTimeout(task, runtimeEnv);
      const config = await this.#resolver.resolve();
      const preferences = resolveSessionPreferences(task.model, runtimeEnv);
      const childEnv = this.#buildChildEnv(config, runtimeEnv);
      entry.onEvent({ type: "zcode_starting", summary: "Starting ZCode streaming runtime" });
      const client = this.#startAppServer(config, workspace.canonicalPath, childEnv, entry);
      entry.client = client;
      entry.child = client.child;
      entry.onEvent({ type: "app_server_started", summary: "ZCode app-server process started", details: { pid: client.child.pid } });
      timer = setTimeout(() => {
        entry.timedOut = true;
        entry.abort.abort();
        entry.rejectTurn(new Error(`ZCode run exceeded ${timeoutMs}ms wall-clock budget`));
      }, timeoutMs);
      timer.unref();
      warningTimer = setTimeout(() => {
        entry.onEvent({
          type: "timeout_warning",
          summary: `Task is approaching its ${timeoutMs}ms execution limit`,
          details: { timeout_ms: timeoutMs, remaining_ms: Math.min(3e5, Math.floor(timeoutMs / 2)) }
        });
      }, Math.max(15e3, timeoutMs - Math.min(3e5, Math.floor(timeoutMs / 2))));
      warningTimer.unref();
      const accountProviderPayload = buildAccountProviderPayload(config);
      if (accountProviderPayload) {
        try {
          const syncResult = asRecord2(await client.request(
            "provider/updateAccountConfig",
            accountProviderPayload
          ));
          entry.onEvent({
            type: "account_provider_sync",
            summary: `Synchronized ${Object.keys(accountProviderPayload.providers).length} ZCode account provider(s)`,
            details: {
              provider_count: Object.keys(accountProviderPayload.providers).length,
              entitled_provider_count: Object.values(accountProviderPayload.states).filter((state) => state.entitled).length,
              runtime_status: typeof syncResult.status === "string" ? syncResult.status : "accepted"
            }
          });
        } catch (error) {
          entry.onEvent({
            type: "account_provider_sync_failed",
            summary: error instanceof Error ? error.message : "ZCode account provider synchronization failed"
          });
        }
      }
      let snapshot;
      if (resumeSessionId) {
        snapshot = asRecord2(await client.request("session/resume", {
          sessionId: resumeSessionId,
          workspace: { workspacePath: workspace.canonicalPath, workspaceKey: projectPath }
        }));
        const returnedId = nestedString(snapshot, ["session", "sessionId"]);
        if (returnedId && returnedId !== resumeSessionId) {
          throw new Error(`resume session mismatch: requested ${resumeSessionId}, runtime returned ${returnedId}`);
        }
        await client.request("session/setMode", { sessionId: resumeSessionId, mode: preferences.mode });
      } else {
        snapshot = asRecord2(await client.request("session/create", {
          workspace: { workspacePath: workspace.canonicalPath, workspaceKey: projectPath },
          mode: preferences.mode,
          persistence: "immediate"
        }));
      }
      const sessionId = nestedString(snapshot, ["session", "sessionId"]);
      if (!sessionId) throw new Error("ZCode app-server session snapshot did not contain session.sessionId");
      entry.sessionId = sessionId;
      let selectedReasoningLevel = null;
      if (preferences.model) {
        const requestedProviderId = accountProviderId(preferences.model.provider_id, config);
        const requested = `${requestedProviderId}/${preferences.model.model_id}`;
        const availableModels = readAvailableModels(snapshot);
        entry.onEvent({
          type: "model_catalog",
          summary: `ZCode runtime advertised ${availableModels.length} selectable model${availableModels.length === 1 ? "" : "s"}`,
          details: {
            session_id: sessionId,
            project_path: projectPath,
            execution_path: workspace.canonicalPath,
            requested_model: { provider_id: requestedProviderId, model_id: preferences.model.model_id },
            available_models: availableModels.slice(0, 100),
            truncated: availableModels.length > 100
          }
        });
        const current = readSelectedModelSelection(snapshot);
        const reasoningLevel = preferences.model.reasoning_level ?? readModelReasoningDefault(
          snapshot,
          requestedProviderId,
          preferences.model.model_id
        );
        const modelState = current?.providerId === requestedProviderId && current.modelId === preferences.model.model_id && !preferences.model.reasoning_level ? snapshot : asRecord2(await client.request("session/setModel", {
          sessionId,
          model: {
            providerId: requestedProviderId,
            modelId: preferences.model.model_id,
            ...reasoningLevel ? { options: { reasoningLevel } } : {}
          },
          // Keep the override scoped to this session; do not change the
          // user's project-wide last-used model.
          persistAsWorkspaceLastUsed: false
        }));
        const selected = readSelectedModelSelection(modelState);
        if (!selected) {
          throw new Error(`ZCode accepted model override ${requested} but did not report the selected model`);
        }
        if (selected.providerId !== requestedProviderId || selected.modelId !== preferences.model.model_id) {
          throw new Error(
            `ZCode model override mismatch: requested ${requested}, runtime selected ${selected.providerId}/${selected.modelId}`
          );
        }
        snapshot = modelState;
        entry.selectedModel = readSelectedModel(modelState) ?? requested;
        entry.selectedModelSelection = selected;
        entry.modelSource = preferences.modelSource;
        entry.requestedModel = requested;
        entry.requestedReasoningLevel = reasoningLevel;
        selectedReasoningLevel = readEffectiveReasoningLevel(modelState);
        entry.selectedReasoningLevel = selectedReasoningLevel;
        entry.reasoningLevelSource = selectedReasoningLevel ? "runtime" : "not_reported";
        entry.onEvent({
          type: "model_selected",
          summary: `ZCode selected requested model ${entry.selectedModel}${selectedReasoningLevel ? ` with reasoning level ${selectedReasoningLevel}` : "; runtime did not report its reasoning level"}`,
          details: {
            requested_model: requested,
            selected_model: entry.selectedModel,
            provider_id: selected.providerId,
            model_id: selected.modelId,
            model_source: preferences.modelSource,
            ...selectedReasoningLevel ? { reasoning_level: selectedReasoningLevel, reasoning_level_source: "runtime" } : {},
            ...reasoningLevel ? { requested_reasoning_level: reasoningLevel } : {}
          }
        });
      }
      const model = readSelectedModel(snapshot);
      entry.selectedModel = entry.selectedModel ?? model;
      const defaultSelection = readSelectedModelSelection(snapshot);
      entry.selectedModelSelection = entry.selectedModelSelection ?? defaultSelection;
      if (!entry.selectedModel) {
        const availableModels = readAvailableModels(snapshot);
        entry.onEvent({
          type: "model_unresolved",
          summary: "ZCode runtime did not report a selected model; task was stopped before sending the prompt",
          details: { session_id: sessionId, available_model_count: availableModels.length }
        });
        throw new BridgeError(
          "provider_config_invalid",
          "ZCode runtime did not report its selected model; refusing to start a task whose model cannot be identified."
        );
      }
      if (!preferences.model) {
        const selected = readSelectedModelSelection(snapshot);
        selectedReasoningLevel = readEffectiveReasoningLevel(snapshot);
        entry.selectedReasoningLevel = selectedReasoningLevel;
        entry.reasoningLevelSource = selectedReasoningLevel ? "runtime" : "not_reported";
        entry.modelSource = preferences.modelSource;
        entry.onEvent({
          type: "model_selected",
          summary: `ZCode runtime selected its session model ${entry.selectedModel}${selectedReasoningLevel ? ` with reasoning level ${selectedReasoningLevel}` : ""}`,
          details: {
            selected_model: entry.selectedModel,
            model_source: preferences.modelSource,
            ...selected ? { provider_id: selected.providerId, model_id: selected.modelId } : {},
            ...selectedReasoningLevel ? { reasoning_level: selectedReasoningLevel, reasoning_level_source: "runtime" } : {}
          }
        });
      }
      entry.onEvent({
        type: "session_ready",
        summary: `ZCode session ready; selected model ${entry.selectedModel}${selectedReasoningLevel ? `; reasoning level ${selectedReasoningLevel}` : "; reasoning level not reported"}`,
        details: {
          session_id: sessionId,
          project_path: projectPath,
          execution_path: workspace.canonicalPath,
          ...workspace.mode === "worktree" ? { worktree_path: workspace.canonicalPath } : {},
          execution_mode: preferences.mode,
          model_source: preferences.modelSource,
          ...entry.selectedModel ? { selected_model: entry.selectedModel } : {},
          ...selectedReasoningLevel ? { reasoning_level: selectedReasoningLevel, reasoning_level_source: "runtime" } : {}
        }
      });
      const indexPath = zcodeTasksIndexPath(config.providerPersonalConfigFile);
      if (indexPath) {
        const selected = readSelectedModelSelection(snapshot);
        desktopTask = {
          databasePath: indexPath,
          workspaceKey: projectPath,
          workspacePath: workspace.canonicalPath,
          sessionId,
          bridgeTaskId: task.task_id,
          title: task.task_id,
          model: selected ? `${selected.providerId}/${selected.modelId}` : null,
          provider: "glm",
          mode: preferences.mode
        };
        try {
          await registerDesktopTask(desktopTask);
          entry.onEvent({
            type: "desktop_task_registered",
            summary: "ZCode session registered in Desktop task index; refresh the task list to see it",
            details: { session_id: sessionId, project_path: projectPath, execution_path: workspace.canonicalPath }
          });
        } catch (error) {
          reportDesktopIndexIssue(entry.onEvent, error);
          desktopTask = null;
        }
      }
      const runtimeSeq = nestedNumber(snapshot, ["runtime", "eventSeq"]) ?? 0;
      entry.lastEventSeq = runtimeSeq;
      entry.awaitingTurnStart = runtimeSeq > 0;
      await client.request("session/subscribe", {
        sessionId,
        deliveryKind: "desktop-continuous",
        includeSnapshot: false,
        afterSeq: runtimeSeq
      });
      entry.acceptingTurn = true;
      await client.request("session/send", { sessionId, content: prompt });
      entry.rpcAcceptedAt = this.#now().toISOString();
      entry.onEvent({ type: "turn_started", summary: "ZCode accepted the task and started a turn", details: { rpc_accepted: true, ...entry.turnId ? { turn_id: entry.turnId } : {} } });
      entry.bindingTimer = setTimeout(() => {
        if (!entry.awaitingTurnStart) return;
        entry.awaitingTurnStart = false;
        entry.turnBinding = "compat";
        entry.onEvent({
          type: "turn_binding_compat",
          summary: "turn.started did not arrive after the accepted send; binding degraded to session-exclusivity compatibility mode"
        });
        this.#settlePendingCompletion(entry);
      }, Math.max(this.#turnBindingCompatMs, 5e3));
      entry.bindingTimer.unref();
      let replayInFlight = false;
      let replayDisabled = false;
      const replayTimer = setInterval(() => {
        if (!entry.acceptingTurn || replayInFlight || replayDisabled || Date.now() - entry.lastEventAt < this.#replayIdleMs) return;
        replayInFlight = true;
        void client.request("session/events", { sessionId, afterSeq: entry.lastEventSeq, limit: 500 }).then((value) => {
          entry.replayConsecutiveFailures = 0;
          const events = asRecord2(value).events;
          if (Array.isArray(events)) client.replayEvents(events);
        }).catch((error) => {
          const message = error instanceof Error ? error.message : String(error);
          if (message.includes("Unsupported ZCode app-server request")) {
            replayDisabled = true;
            entry.onEvent({ type: "session_event_replay_unavailable", summary: "ZCode session event replay is unsupported by this runtime; continuing with live event subscription" });
            return;
          }
          entry.replayConsecutiveFailures += 1;
          if (entry.replayConsecutiveFailures >= 3) {
            replayDisabled = true;
            entry.onEvent({ type: "session_event_replay_unavailable", summary: `ZCode session event replay failed ${String(entry.replayConsecutiveFailures)} times consecutively; continuing with live subscription` });
          }
        }).finally(() => {
          replayInFlight = false;
        });
      }, Math.max(50, Math.min(5e3, this.#replayIdleMs)));
      replayTimer.unref();
      let turnResult;
      try {
        turnResult = await turn;
      } finally {
        clearInterval(replayTimer);
        if (entry.bindingTimer) {
          clearTimeout(entry.bindingTimer);
          entry.bindingTimer = null;
        }
        if (entry.pendingTimer) {
          clearTimeout(entry.pendingTimer);
          entry.pendingTimer = null;
        }
      }
      entry.turnCompletedAt = turnResult.completedAt;
      const desktopStatus = turnResult.resultType === "cancelled" ? null : turnResult.resultType && turnResult.resultType !== "success" ? "error" : "completed";
      let outcome;
      if (turnResult.resultType && turnResult.resultType !== "success") {
        outcome = {
          attempts: 1,
          cancelled: turnResult.resultType === "cancelled",
          stdout: turnResult.response,
          stderr: "",
          exitCode: 1,
          signal: null,
          sessionId,
          response: turnResult.response,
          usage: turnResult.usage,
          timedOut: false,
          stdoutTruncated: false,
          stderrTruncated: false,
          agentReport: null,
          reportCandidate: null,
          reportError: `ZCode turn ended with resultType ${turnResult.resultType}`,
          errorCode: turnResult.resultType === "cancelled" ? "cancelled" : "zcode_nonzero_exit",
          phaseTimestamps: {
            rpc_accepted_at: turnResult.rpcAcceptedAt,
            turn_started_at: turnResult.startedAt,
            turn_completed_at: turnResult.completedAt
          },
          modelProfile: this.#modelProfile(entry)
        };
      } else if (turnResult.resultType === null) {
        const parsedUnknown = parseAgentReport(turnResult.response);
        outcome = {
          attempts: 1,
          cancelled: false,
          stdout: turnResult.response,
          stderr: "",
          exitCode: 1,
          signal: null,
          sessionId,
          response: turnResult.response,
          usage: turnResult.usage,
          timedOut: false,
          stdoutTruncated: false,
          stderrTruncated: false,
          agentReport: null,
          reportCandidate: parsedUnknown.candidate,
          reportError: `ZCode turn completed without a resultType (binding: ${turnResult.binding}); treated as an unknown terminal state, not a success`,
          errorCode: "unknown_turn_terminal",
          phaseTimestamps: {
            rpc_accepted_at: turnResult.rpcAcceptedAt,
            turn_started_at: turnResult.startedAt,
            turn_completed_at: turnResult.completedAt
          },
          modelProfile: this.#modelProfile(entry)
        };
      } else {
        const parsed = parseAgentReport(turnResult.response);
        const stdout = turnResult.response;
        const base = {
          attempts: 1,
          cancelled: false,
          stdoutTruncated: false,
          stderrTruncated: false,
          stdout,
          stderr: "",
          exitCode: 0,
          signal: null,
          sessionId,
          response: turnResult.response,
          usage: turnResult.usage,
          timedOut: false,
          reportCandidate: parsed.candidate
        };
        if (!parsed.report) {
          outcome = {
            ...base,
            agentReport: null,
            reportCandidate: parsed.candidate,
            reportError: parsed.error,
            errorCode: "invalid_agent_report",
            phaseTimestamps: {
              rpc_accepted_at: turnResult.rpcAcceptedAt,
              turn_started_at: turnResult.startedAt,
              turn_completed_at: turnResult.completedAt
            },
            modelProfile: this.#modelProfile(entry)
          };
        } else {
          entry.onEvent({
            type: "report_ready",
            summary: "ZCode produced its structured execution report",
            details: { needs_master_decision: parsed.report.needs_master_decision }
          });
          outcome = {
            ...base,
            agentReport: parsed.report,
            reportCandidate: parsed.report,
            reportError: null,
            errorCode: null,
            phaseTimestamps: {
              rpc_accepted_at: turnResult.rpcAcceptedAt,
              turn_started_at: turnResult.startedAt,
              turn_completed_at: turnResult.completedAt
            },
            modelProfile: this.#modelProfile(entry)
          };
        }
      }
      outcome = { ...outcome, cleanupVerified: false };
      try {
        this.#onOutcomeCheckpoint?.(outcome);
      } catch (error) {
        entry.onEvent({ type: "outcome_checkpoint_failed", summary: error instanceof Error ? error.message : String(error) });
      }
      try {
        await syncDesktopStatus(desktopTask, desktopStatus, entry.onEvent);
      } catch (error) {
        entry.onEvent({ type: "desktop_status_sync_failed", summary: error instanceof Error ? error.message : String(error) });
      }
      try {
        await client.close();
        entry.child = null;
        outcome = { ...outcome, cleanupVerified: true };
        try {
          this.#onOutcomeCheckpoint?.(outcome);
        } catch (error) {
          entry.onEvent({ type: "outcome_checkpoint_failed", summary: error instanceof Error ? error.message : String(error) });
        }
      } catch (error) {
        const cleanupError = error instanceof Error ? error.message : String(error);
        entry.onEvent({ type: "cleanup_unverified", summary: cleanupError.slice(0, 1500), details: { pid: client.child.pid } });
        outcome = { ...outcome, cleanupError, cleanupVerified: false };
        try {
          this.#onOutcomeCheckpoint?.(outcome);
        } catch (checkpointError) {
          entry.onEvent({ type: "outcome_checkpoint_failed", summary: checkpointError instanceof Error ? checkpointError.message : String(checkpointError) });
        }
      }
      return outcome;
    } catch (error) {
      await syncDesktopStatus(desktopTask, entry.cancelRequested ? null : "error", entry.onEvent);
      entry.abort.abort();
      try {
        if (entry.client) await entry.client.close();
        else if (entry.child?.pid) await terminateProcessTree(entry.child.pid);
      } catch (cleanupError) {
        throw new BridgeError("cleanup_failed", "ZCode process termination could not be verified; workspace remains occupied", { cause: cleanupError });
      }
      entry.child = null;
      const baseMessage = error instanceof Error ? error.message : String(error);
      const message = entry.timedOut ? "ZCode run exceeded its wall-clock budget" : entry.cancelRequested ? "ZCode task cancelled" : baseMessage;
      const code = entry.timedOut ? "timeout" : entry.cancelRequested ? "cancelled" : "zcode_nonzero_exit";
      entry.onEvent({ type: "error", summary: message.slice(0, 1500), details: { error_code: code } });
      if (error instanceof BridgeError) throw error;
      throw new BridgeError(code, message);
    } finally {
      if (timer) clearTimeout(timer);
      if (warningTimer) clearTimeout(warningTimer);
      entry.abort.abort();
      entry.finished = true;
      void startedAt;
    }
  }
  #startAppServer(config, cwd, env, entry) {
    const child = spawn2(config.nodeExecutable, [config.zcodeEntrypoint, "app-server", "--stdio"], {
      cwd,
      env,
      shell: false,
      windowsHide: true,
      detached: process.platform !== "win32",
      stdio: ["pipe", "pipe", "pipe"]
    });
    let stderr = "";
    let stdoutBuffer = "";
    let rpcId = 0;
    let closed = false;
    const pending = /* @__PURE__ */ new Map();
    entry.abort.signal.addEventListener("abort", () => {
      for (const call of pending.values()) {
        clearTimeout(call.timer);
        call.reject(new Error("ZCode task attempt ended"));
      }
      pending.clear();
    }, { once: true });
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      stdoutBuffer += chunk;
      if (stdoutBuffer.length > MAX_CAPTURE_CHARS) {
        entry.rejectTurn(new Error("ZCode protocol frame exceeded size limit"));
        return;
      }
      let newline;
      while ((newline = stdoutBuffer.indexOf("\n")) >= 0) {
        const line = stdoutBuffer.slice(0, newline).trim();
        stdoutBuffer = stdoutBuffer.slice(newline + 1);
        if (!line) continue;
        try {
          const message = JSON.parse(line);
          this.#handleMessage(message, entry, pending, config, (reply) => {
            child.stdin.write(`${JSON.stringify(reply)}
`);
          });
        } catch (error) {
          entry.rejectTurn(new Error("invalid ZCode app-server protocol message", { cause: error }));
        }
      }
    });
    child.stderr.on("data", (chunk) => {
      if (stderr.length < 64e3) stderr += chunk.slice(0, 64e3 - stderr.length);
    });
    child.on("error", (error) => {
      closed = true;
      for (const call of pending.values()) {
        clearTimeout(call.timer);
        call.reject(error);
      }
      pending.clear();
      entry.rejectTurn(error);
    });
    child.on("close", (code, signal) => {
      closed = true;
      for (const call of pending.values()) {
        clearTimeout(call.timer);
        call.reject(new Error(`ZCode app-server exited (${String(code)}${signal ? `, ${signal}` : ""})`));
      }
      pending.clear();
      if (!entry.finished && !entry.timedOut && !entry.cancelRequested) {
        entry.rejectTurn(new Error(`ZCode app-server exited before turn completion (${String(code)})`));
      }
    });
    const request = (method, params) => {
      if (entry.abort.signal.aborted) return Promise.reject(new Error("ZCode task attempt ended"));
      if (closed) return Promise.reject(new Error(`ZCode app-server is closed before ${method}`));
      const id = ++rpcId;
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          pending.delete(id);
          reject(new Error(`ZCode app-server request timed out: ${method}`));
        }, RPC_TIMEOUT_MS);
        timer.unref();
        pending.set(id, { method, resolve, reject, timer });
        child.stdin.write(`${JSON.stringify({ id, method, params })}
`, (error) => {
          if (!error) return;
          clearTimeout(timer);
          pending.delete(id);
          reject(error);
        });
      });
    };
    const replayEvents = (events) => {
      for (const event of events) {
        const params = asRecord2(event);
        if (typeof params.type !== "string") continue;
        this.#handleMessage({ method: "session/event", params }, entry, pending, config, (reply) => {
          child.stdin.write(`${JSON.stringify(reply)}
`);
        });
      }
    };
    const close = async () => {
      if (closed) {
        if (process.platform !== "win32" && child.pid) await terminateProcessTree(child.pid);
        return;
      }
      child.stdin.end();
      await new Promise((resolve) => {
        const timer = setTimeout(() => resolve(), 1e3);
        timer.unref();
        child.once("close", () => {
          clearTimeout(timer);
          resolve();
        });
      });
      if (closed) {
        if (process.platform !== "win32" && child.pid) await terminateProcessTree(child.pid);
        return;
      }
      if (child.pid && isProcessRunning(child.pid)) await terminateProcessTree(child.pid);
    };
    return { child, request, replayEvents, close, get stderr() {
      return stderr;
    } };
  }
  #handleMessage(message, entry, pending, config, write) {
    if (message.method === "session/requestRuntimePreferences") {
      const id = message.id;
      if (typeof id === "string" || typeof id === "number") {
        write({
          id,
          result: {
            nativeSearchEnhancementsEnabled: false,
            memoryEnabled: false,
            askUserQuestionAutoResolutionEnabled: false
          }
        });
      }
      return;
    }
    if (message.method === "interaction/requestProviderRuntimeHeaders") {
      const id = message.id;
      if (typeof id === "string" || typeof id === "number") {
        const params = asRecord2(message.params);
        const selection = asRecord2(params.modelSelection);
        const providerId = typeof selection.providerId === "string" ? selection.providerId : typeof params.providerId === "string" ? params.providerId : void 0;
        write({ id, result: runtimeAuthReply(providerId, config) });
      }
      return;
    }
    if (message.method === "interaction/requestPermission" || message.method === "interaction/requestUserInput") {
      if (typeof message.id === "string" || typeof message.id === "number") {
        this.#handleInteractionRequest(message, entry, write);
      }
      return;
    }
    if (message.id !== void 0 && message.method === void 0) {
      const id = message.id;
      const call = pending.get(id);
      if (!call) return;
      clearTimeout(call.timer);
      pending.delete(id);
      if (message.error && typeof message.error === "object") {
        const error = message.error;
        call.reject(new Error(`ZCode app-server request failed for ${call.method}${typeof error.code === "number" ? ` (code ${error.code})` : ""}`));
      } else {
        call.resolve(message.result);
      }
      return;
    }
    if (message.method === "session/event") {
      const params = asRecord2(message.params);
      if (params.sessionId !== void 0 && params.sessionId !== entry.sessionId) return;
      if (!entry.acceptingTurn) return;
      const type = typeof params.type === "string" ? params.type : "";
      const payload = asRecord2(params.payload);
      const turnId = typeof params.turnId === "string" ? params.turnId : typeof payload.turnId === "string" ? payload.turnId : null;
      if (entry.awaitingTurnStart && type !== "turn.started") return;
      if (entry.turnId && turnId && entry.turnId !== turnId) return;
      if (typeof params.seq === "number") {
        if (!Number.isSafeInteger(params.seq) || params.seq <= entry.lastEventSeq) return;
        entry.lastEventSeq = params.seq;
      }
      entry.lastEventAt = Date.now();
      if (type === "turn.started") {
        if (turnId) entry.turnId = turnId;
        entry.awaitingTurnStart = false;
        entry.turnStartedAt = this.#now().toISOString();
        if (entry.bindingTimer) {
          clearTimeout(entry.bindingTimer);
          entry.bindingTimer = null;
        }
      }
      if (type === "turn.completed") {
        if (entry.awaitingTurnStart) {
          entry.pendingCompletion = { payload, event: params, heldAt: Date.now() };
          entry.acceptingTurn = false;
          if (!entry.pendingTimer) {
            entry.pendingTimer = setTimeout(() => this.#settlePendingCompletion(entry), this.#turnBindingCompatMs);
            entry.pendingTimer.unref();
          }
          return;
        }
        entry.acceptingTurn = false;
        entry.turnCompletedAt = this.#now().toISOString();
        entry.turnBinding = entry.turnId ? "strict" : "compat";
        this.#publishSessionEvent(type, payload, entry, params);
        this.#resolveTurnCompleted(entry, payload, params);
        return;
      }
      if (type === "turn.failed") {
        entry.acceptingTurn = false;
        entry.turnCompletedAt = this.#now().toISOString();
        const problem = asRecord2(payload.error);
        void problem;
        this.#publishSessionEvent(type, payload, entry, params);
        entry.rejectTurn(new Error("ZCode turn failed"));
        return;
      }
      this.#publishSessionEvent(type, payload, entry, params);
      if (type === "turn.started" && entry.pendingCompletion) {
        this.#settlePendingCompletion(entry);
      }
    }
    if (message.method === "state.updated") {
      const params = asRecord2(message.params);
      const patch = asRecord2(params.patch);
      const state = typeof patch.status === "string" ? patch.status : void 0;
      if (state) entry.onEvent({ type: "runtime_state", summary: `ZCode runtime state: ${state}` });
      return;
    }
    if (message.id !== void 0 && typeof message.method === "string") {
      write({ id: message.id, error: { code: -32601, message: `Unsupported ZCode app-server request: ${message.method}` } });
    }
  }
  #handleInteractionRequest(message, entry, write) {
    const rpcId = message.id;
    const method = message.method;
    const params = asRecord2(message.params);
    if (entry.abort.signal.aborted || params.sessionId !== void 0 && params.sessionId !== entry.sessionId) {
      write({ id: rpcId, result: interactionDecline(method, "Interaction does not belong to the active task session") });
      return;
    }
    const suppliedId = typeof params.requestId === "string" ? params.requestId : "";
    const requestId = suppliedId || `rpc-${String(rpcId)}`;
    const paramsSignature = stableSerialize(params);
    let pending = entry.interactions.get(requestId);
    if (pending) {
      if (pending.method !== method || pending.paramsSignature !== paramsSignature) {
        write({ id: rpcId, result: interactionDecline(method, "Conflicting ZCode interaction request id") });
        entry.onEvent({
          type: "interaction_request_conflict",
          summary: "ZCode reused an interaction request id with different request data; the conflicting request was declined",
          details: { request_id: requestId, method }
        });
        return;
      }
      if (!pending.requestIds.includes(rpcId)) pending.requestIds.push(rpcId);
      if (pending.response) write({ id: rpcId, result: pending.response });
      return;
    }
    pending = { requestIds: [rpcId], method, paramsSignature, resolving: true };
    entry.interactions.set(requestId, pending);
    this.#onInteractionState?.("waiting");
    const request = { request_id: requestId, method, params };
    const fallback = interactionDecline(method, "Bridge interaction reply is unavailable");
    void (async () => {
      let response = fallback;
      try {
        if (this.#resolveInteraction) response = await this.#resolveInteraction(request, entry.abort.signal);
      } catch (error) {
        const messageText = error instanceof Error ? error.message : String(error);
        entry.onEvent({
          type: "interaction_reply_failed",
          summary: `Could not deliver the calling host's response to ZCode: ${messageText}`.slice(0, 1500),
          details: { request_id: requestId, method }
        });
      }
      pending.response = response;
      pending.resolving = false;
      if (entry.abort.signal.aborted) return;
      this.#onInteractionState?.("resumed");
      for (const id of pending.requestIds) write({ id, result: response });
      entry.onEvent({
        type: "interaction_replied",
        summary: `the calling host replied to ZCode ${method === "interaction/requestPermission" ? "permission request" : "user input request"}`,
        details: { request_id: requestId, method }
      });
      while (entry.interactions.size > 128) {
        const oldest = entry.interactions.keys().next().value;
        if (!oldest || entry.interactions.get(oldest)?.resolving) break;
        entry.interactions.delete(oldest);
      }
    })().catch(() => entry.rejectTurn(new Error("ZCode interaction delivery failed")));
  }
  /** Settles a completion that was held in the pending boundary. */
  #settlePendingCompletion(entry) {
    if (entry.pendingTimer) {
      clearTimeout(entry.pendingTimer);
      entry.pendingTimer = null;
    }
    const held = entry.pendingCompletion;
    if (!held) return;
    entry.pendingCompletion = null;
    if (entry.awaitingTurnStart) {
      entry.awaitingTurnStart = false;
      entry.turnBinding = "compat";
      entry.onEvent({
        type: "turn_binding_compat",
        summary: "turn.started never arrived for the accepted send; completion settled through the bounded compatibility window"
      });
    }
    entry.turnCompletedAt = this.#now().toISOString();
    this.#resolveTurnCompleted(entry, held.payload, held.event);
  }
  /** Single settle path for turn completions; resultType is validated here so
   * an unknown terminal is never mistaken for success (B2). */
  #resolveTurnCompleted(entry, payload, event) {
    if (entry.turnBinding === "pending") entry.turnBinding = entry.turnId ? "strict" : "compat";
    entry.resolveTurn({
      response: typeof payload.response === "string" ? payload.response : "",
      usage: publicUsage(payload.usage),
      resultType: typeof payload.resultType === "string" ? payload.resultType : null,
      binding: entry.turnBinding,
      startedAt: entry.turnStartedAt,
      completedAt: entry.turnCompletedAt ?? this.#now().toISOString(),
      rpcAcceptedAt: entry.rpcAcceptedAt
    });
    void event;
  }
  #modelProfile(entry) {
    if (!entry.selectedModel && !entry.selectedModelSelection) return null;
    return {
      executor: "zcode",
      provider_id: entry.selectedModelSelection?.providerId ?? null,
      model_id: entry.selectedModelSelection?.modelId ?? entry.selectedModel,
      requested_model: entry.requestedModel,
      requested_reasoning_level: entry.requestedReasoningLevel,
      effective_reasoning_level: entry.selectedReasoningLevel,
      effective_reasoning_level_source: entry.reasoningLevelSource,
      selection_source: entry.modelSource ?? "runtime",
      effective_at: entry.turnStartedAt ?? entry.rpcAcceptedAt ?? null,
      session_id: entry.sessionId,
      turn_id: entry.turnId
    };
  }
  #publishSessionEvent(type, payload, entry, event) {
    if (type === "turn.started") {
      entry.onEvent({
        type: "turn_started",
        summary: `ZCode turn started${entry.selectedModel ? ` with selected model ${entry.selectedModel}` : ""}`,
        details: {
          ...typeof event.turnId === "string" ? { turn_id: event.turnId } : typeof payload.turnId === "string" ? { turn_id: payload.turnId } : {},
          ...typeof event.seq === "number" ? { event_seq: event.seq } : {}
        }
      });
    } else if (type === "model.streaming") {
      const kind = payload.kind;
      const delta = typeof payload.delta === "string" ? payload.delta : "";
      if ((kind === "text_start" || kind === "text_delta") && !entry.textOutputStarted) {
        entry.textOutputStarted = true;
        entry.onEvent({
          type: "model_output_started",
          summary: `ZCode began returning visible model output${entry.selectedModel ? ` (${entry.selectedModel})` : ""}`,
          details: entry.selectedModel ? { selected_model: entry.selectedModel } : void 0
        });
      }
      if (kind === "text_delta" && delta) {
        entry.onEvent({ type: "model_output", summary: delta });
      } else if (kind === "tool_call") {
        const name = typeof payload.toolName === "string" ? payload.toolName : "tool";
        const callId = typeof payload.toolCallId === "string" ? payload.toolCallId : void 0;
        entry.onEvent({
          type: "model_tool_call",
          summary: `Model requested tool ${name}`,
          details: { tool_name: name, ...callId ? { tool_call_id: callId } : {} }
        });
      }
    } else if (type === "tool.updated") {
      const name = typeof payload.toolName === "string" ? payload.toolName : "tool";
      const state = typeof payload.kind === "string" ? payload.kind : "updated";
      const callId = typeof payload.toolCallId === "string" ? payload.toolCallId : void 0;
      entry.onEvent({
        type: "tool_status",
        summary: `${name}: ${state}`,
        details: { tool_name: name, state, ...callId ? { tool_call_id: callId } : {} }
      });
    } else if (type === "turn.completed") {
      entry.onEvent({
        type: "turn_completed",
        summary: "ZCode turn completed",
        details: {
          ...typeof payload.tokenCount === "number" ? { token_count: payload.tokenCount } : {},
          ...typeof payload.toolCallCount === "number" ? { tool_call_count: payload.toolCallCount } : {},
          ...typeof event.seq === "number" ? { event_seq: event.seq } : {},
          ...typeof event.turnId === "string" ? { turn_id: event.turnId } : {},
          ...publicUsage(payload.usage) ? { usage: publicUsage(payload.usage) } : {}
        }
      });
    } else if (type === "turn.failed") {
      entry.onEvent({
        type: "turn_failed",
        summary: "ZCode turn failed"
      });
    }
  }
  #buildChildEnv(config, source = this.#childEnvBase) {
    const env = createMinimalOsEnv(source);
    env.ZCODE_BUILTIN_PROVIDER_CONFIG_FILE = config.providerBuiltinConfigFile;
    env.ZCODE_PERSONAL_PROVIDER_CONFIG_FILE = config.providerPersonalConfigFile;
    if (source.ZCODE_HOME) env.ZCODE_HOME = source.ZCODE_HOME;
    const dataBaseDir = zcodeDataBaseDir(config.providerPersonalConfigFile);
    if (dataBaseDir) env.ZCODE_DATA_BASE_DIR = dataBaseDir;
    return env;
  }
  #require(handle, method) {
    const entry = this.#runs.get(handle);
    if (!entry) throw new Error(`${method}: unknown agent handle (task ${handle.taskId})`);
    return entry;
  }
};
function interactionDecline(method, reason) {
  return method === "interaction/requestPermission" ? { decision: "deny", reason } : { action: "decline", reason };
}
function readSelectedModel(snapshot) {
  const settings = asRecord2(snapshot.settings);
  const modelSettings = asRecord2(settings.model);
  const current = asRecord2(modelSettings.current);
  const modelId = typeof current.modelId === "string" ? current.modelId : null;
  const providerId = typeof current.providerId === "string" ? current.providerId : null;
  if (!modelId) return null;
  const available = Array.isArray(modelSettings.available) ? modelSettings.available : [];
  const match = available.find((entry) => {
    const ref = asRecord2(asRecord2(entry).ref);
    return ref.modelId === modelId && (providerId === null || ref.providerId === providerId);
  });
  const label = match && typeof asRecord2(match).label === "string" ? asRecord2(match).label : modelId;
  return providerId ? `${label} (${providerId}/${modelId})` : label;
}
function readSelectedModelSelection(snapshot) {
  const settings = asRecord2(snapshot.settings);
  const modelSettings = asRecord2(settings.model);
  const current = asRecord2(modelSettings.current);
  if (typeof current.providerId !== "string" || typeof current.modelId !== "string") return null;
  return { providerId: current.providerId, modelId: current.modelId };
}
function readAvailableModels(snapshot) {
  const settings = asRecord2(snapshot.settings);
  const modelSettings = asRecord2(settings.model);
  const available = Array.isArray(modelSettings.available) ? modelSettings.available : [];
  const refs = /* @__PURE__ */ new Map();
  for (const entry of available) {
    const ref = asRecord2(asRecord2(entry).ref);
    if (typeof ref.providerId !== "string" || typeof ref.modelId !== "string") continue;
    const key = `${ref.providerId}\0${ref.modelId}`;
    refs.set(key, { providerId: ref.providerId, modelId: ref.modelId });
  }
  return [...refs.values()];
}
function readModelReasoningDefault(snapshot, providerId, modelId) {
  const settings = asRecord2(snapshot.settings);
  const modelSettings = asRecord2(settings.model);
  const available = Array.isArray(modelSettings.available) ? modelSettings.available : [];
  for (const item of available) {
    const entry = asRecord2(item);
    const ref = asRecord2(entry.ref);
    if (ref.providerId !== providerId || ref.modelId !== modelId) continue;
    const reasoning = asRecord2(entry.reasoning);
    if (typeof reasoning.defaultLevel === "string" && reasoning.defaultLevel.trim()) {
      return reasoning.defaultLevel;
    }
    const levels = Array.isArray(reasoning.levels) ? reasoning.levels : [];
    if (levels.length === 1) {
      const value = asRecord2(levels[0]).value;
      if (typeof value === "string" && value.trim()) return value;
    }
  }
  return null;
}
function readEffectiveReasoningLevel(snapshot) {
  const settings = asRecord2(snapshot.settings);
  const modelSettings = asRecord2(settings.model);
  const current = asRecord2(modelSettings.current);
  const options = asRecord2(current.options);
  const currentOption = options.reasoningLevel;
  if (typeof currentOption === "string" && currentOption.trim()) return currentOption.trim();
  const thoughtLevel = asRecord2(settings.thoughtLevel);
  const level = thoughtLevel.current;
  return typeof level === "string" && level.trim() ? level.trim() : null;
}
function nestedString(record, path6) {
  let value = record;
  for (const part of path6) value = asRecord2(value)[part];
  return typeof value === "string" ? value : null;
}
function nestedNumber(record, path6) {
  let value = record;
  for (const part of path6) value = asRecord2(value)[part];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
function asRecord2(value) {
  return isRecord2(value) ? value : {};
}
async function syncDesktopStatus(entry, status, onEvent) {
  if (!entry) return;
  try {
    await updateDesktopTaskStatus(entry, status);
  } catch (error) {
    reportDesktopIndexIssue(onEvent, error);
  }
}
function reportDesktopIndexIssue(onEvent, error) {
  const message = error instanceof Error ? error.message : String(error);
  onEvent({
    type: "desktop_task_index_warning",
    summary: `ZCode Desktop task index could not be updated: ${message.slice(0, 500)}`
  });
}
function isRecord2(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
function stableSerialize(value) {
  if (Array.isArray(value)) return `[${value.map(stableSerialize).join(",")}]`;
  if (isRecord2(value)) {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableSerialize(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value) ?? "undefined";
}

// src/manager/normalize.ts
function buildTaskResult(input) {
  const { task, attempt, startedAt, finishedAt, outcome } = input;
  const base = {
    task_id: task.task_id,
    attempt,
    started_at: startedAt,
    finished_at: finishedAt,
    zcode_output: outcome?.response ?? "",
    exit_code: outcome?.exitCode ?? null,
    session_id: outcome?.sessionId ?? input.sessionId ?? null,
    ...input.usage !== void 0 ? { usage: input.usage } : {},
    ...input.model !== void 0 ? { model: input.model } : {},
    ...input.timing !== void 0 ? { timing: input.timing } : {}
  };
  if (input.cancelled || outcome?.cancelled) {
    return {
      ...base,
      status: "cancelled",
      summary: input.failure?.message ?? "cancelled by request",
      files_changed: [],
      tests: [],
      issues: [],
      needs_master_decision: false
    };
  }
  const failure = input.failure ?? (outcome ? null : { code: "worker_lost", message: "no adapter outcome was recorded" });
  if (failure || !outcome) {
    const resolved = failure ?? { code: "worker_lost", message: "no adapter outcome was recorded" };
    return {
      ...base,
      status: "failed",
      summary: truncate(`${resolved.code}: ${resolved.message}`, 2e3),
      files_changed: [],
      tests: [],
      issues: [truncate(resolved.message, 2e3)],
      needs_master_decision: true,
      error_code: resolved.code,
      ...resolved.code === "cleanup_failed" && outcome?.reportCandidate ? { report_candidate: outcome.reportCandidate } : {}
    };
  }
  if (outcome.errorCode || outcome.reportError) {
    const code = outcome.errorCode ?? "invalid_agent_report";
    const message = outcome.reportError ?? "the subordinate report was invalid";
    return {
      ...base,
      status: "failed",
      summary: truncate(`${code}: ${message}`, 2e3),
      files_changed: [],
      tests: [],
      issues: [truncate(message, 2e3)],
      needs_master_decision: true,
      error_code: code,
      ...outcome.reportCandidate ? { report_candidate: outcome.reportCandidate } : {}
    };
  }
  const report = outcome.agentReport;
  if (!report) {
    return {
      ...base,
      status: "failed",
      summary: "the adapter reported success without a normalized report",
      files_changed: [],
      tests: [],
      issues: ["missing AgentReport despite a clean exit"],
      needs_master_decision: true,
      error_code: "invalid_agent_report"
    };
  }
  return {
    ...base,
    status: report.needs_master_decision ? "waiting_for_master" : "completed",
    summary: report.summary,
    files_changed: report.files_changed,
    tests: report.tests,
    issues: report.issues,
    needs_master_decision: report.needs_master_decision
  };
}
function truncate(text, maxChars) {
  return text.length <= maxChars ? text : `${text.slice(0, maxChars)}\u2026[truncated]`;
}

// src/store/task-store.ts
import { appendFileSync, chmodSync, closeSync, copyFileSync, existsSync as existsSync5, mkdirSync as mkdirSync2, openSync, readFileSync as readFileSync4, readSync, readdirSync, rmSync, statSync as statSync3, writeFileSync as writeFileSync2 } from "node:fs";
import { createHash as createHash2, randomUUID as randomUUID2 } from "node:crypto";
import path5 from "node:path";
import { StringDecoder } from "node:string_decoder";

// src/store/process-lock.ts
import { existsSync as existsSync4, mkdirSync, readFileSync as readFileSync3, renameSync, rmdirSync, statSync as statSync2, unlinkSync, writeFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import path4 from "node:path";
var selfIdentity = null;
function tryAcquireProcessLock(directory) {
  return tryAcquireProcessLockWithRetry(directory, 0);
}
function tryAcquireProcessLockWithRetry(directory, retries) {
  const token = randomUUID();
  const staging = `${directory}.${process.pid}.${token}.pending`;
  const ownerRecord = {
    pid: process.pid,
    token,
    started_at: (/* @__PURE__ */ new Date()).toISOString(),
    // Fingerprint may be null before the async self-identity probe finishes;
    // null never authorizes binding a recycled PID to a prior owner.
    identity: selfIdentity ? { fingerprint: selfIdentity.fingerprint, identity_version: selfIdentity.identity_version, platform: selfIdentity.platform } : null
  };
  try {
    mkdirSync(staging, { mode: 448 });
    writeFileSync(path4.join(staging, "owner.json"), JSON.stringify(ownerRecord), { mode: 384, flag: "wx" });
    try {
      renameSync(staging, directory);
    } catch (error) {
      removeStagedLock(staging);
      if (!existsSync4(directory)) {
        const code = error.code;
        if (retries < 3 && (code === "EEXIST" || code === "EPERM" || code === "EACCES")) {
          return tryAcquireProcessLockWithRetry(directory, retries + 1);
        }
        throw error;
      }
      return acquireExistingLock(directory);
    }
  } catch (error) {
    removeStagedLock(staging);
    throw error;
  }
  return () => {
    const owner = JSON.parse(readFileSync3(path4.join(directory, "owner.json"), "utf8"));
    if (owner.token !== token) throw new Error("process lock ownership changed");
    unlinkSync(path4.join(directory, "owner.json"));
    rmdirSync(directory);
  };
}
function acquireExistingLock(directory) {
  try {
    const owner = JSON.parse(readFileSync3(path4.join(directory, "owner.json"), "utf8"));
    if (!Number.isSafeInteger(owner.pid) || owner.pid <= 0) throw new Error("invalid lock owner");
    try {
      process.kill(owner.pid, 0);
    } catch (failure) {
      if (failure.code === "ESRCH") {
        if (reclaimDeadOwner(directory)) return tryAcquireProcessLock(directory);
      }
    }
  } catch {
    try {
      if (Date.now() - statSync2(directory).mtimeMs > 3e4) throw new Error(`unreadable lock owner: ${directory}`);
    } catch (failure) {
      if (failure.code !== "ENOENT") throw failure;
    }
  }
  return null;
}
function removeStagedLock(directory) {
  try {
    unlinkSync(path4.join(directory, "owner.json"));
  } catch {
  }
  try {
    rmdirSync(directory);
  } catch {
  }
}
function reclaimDeadOwner(directory) {
  const guard = `${directory}.reclaim`;
  try {
    mkdirSync(guard);
  } catch (error) {
    if (error.code === "EEXIST") return false;
    throw error;
  }
  try {
    const owner = JSON.parse(readFileSync3(path4.join(directory, "owner.json"), "utf8"));
    if (!Number.isSafeInteger(owner.pid) || owner.pid <= 0) return false;
    try {
      process.kill(owner.pid, 0);
      return false;
    } catch (error) {
      if (error.code !== "ESRCH") return false;
    }
    const retired = `${directory}.${randomUUID()}.retired`;
    renameSync(directory, retired);
    unlinkSync(path4.join(retired, "owner.json"));
    rmdirSync(retired);
    return true;
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
    return false;
  } finally {
    rmdirSync(guard);
  }
}

// src/store/atomic-rename.ts
import { renameSync as renameSync2 } from "node:fs";
function retryable(error, deadline) {
  return process.platform === "win32" && Date.now() < deadline && ["EPERM", "EBUSY", "EACCES"].includes(error.code ?? "");
}
function atomicRenameSync(source, target) {
  const deadline = Date.now() + 2e3;
  while (true) {
    try {
      renameSync2(source, target);
      return;
    } catch (error) {
      if (!retryable(error, deadline)) throw error;
      Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 10);
    }
  }
}

// src/store/task-store.ts
var TASK_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/;
var DEFAULT_MAX_LOG_BYTES = 10 * 1024 * 1024;
var MAX_CRITICAL_EVENT_RESERVE_BYTES = 256 * 1024;
var CRITICAL_EVENT_TYPES = /* @__PURE__ */ new Set([
  "error",
  "task_finished",
  "turn_completed",
  "report_ready",
  "session_ready",
  "turn_started",
  "worker_started",
  "workspace_ready",
  "timeout_warning",
  "model_catalog",
  "account_provider_sync_failed",
  "interaction_requested",
  "interaction_reply_submitted",
  "cancelled",
  "cancel_failed",
  "cleanup_unverified",
  "outcome_checkpoint_failed",
  "outcome_recovered"
]);
var TaskStore = class {
  #dataRoot;
  #tasksRoot;
  #maxLogBytes;
  #maxEventBytes;
  constructor(dataRoot2, options = {}) {
    this.#dataRoot = dataRoot2;
    this.#tasksRoot = path5.join(dataRoot2, ".tasks");
    this.#maxLogBytes = options.maxLogBytes ?? DEFAULT_MAX_LOG_BYTES;
    this.#maxEventBytes = options.maxEventBytes ?? DEFAULT_MAX_LOG_BYTES;
    privateMkdir(this.#tasksRoot);
  }
  get dataRoot() {
    return this.#dataRoot;
  }
  get tasksRoot() {
    return this.#tasksRoot;
  }
  assertValidTaskId(taskId2) {
    if (typeof taskId2 !== "string" || !TASK_ID_PATTERN.test(taskId2)) {
      throw new Error(`invalid task_id (must match ${TASK_ID_PATTERN.source}): ${String(taskId2)}`);
    }
  }
  taskDir(taskId2) {
    this.assertValidTaskId(taskId2);
    return path5.join(this.#tasksRoot, taskId2);
  }
  hasTask(taskId2) {
    try {
      return existsSync5(path5.join(this.taskDir(taskId2), "status.json"));
    } catch {
      return false;
    }
  }
  listTaskIds() {
    if (!existsSync5(this.#tasksRoot)) return [];
    return readdirSync(this.#tasksRoot).filter(
      (entry) => existsSync5(path5.join(this.#tasksRoot, entry, "status.json"))
    );
  }
  createTask(task, createdAt) {
    this.assertValidTaskId(task.task_id);
    const dir = this.taskDir(task.task_id);
    if (existsSync5(path5.join(dir, "task.json"))) {
      throw new Error(`task already exists: ${task.task_id}`);
    }
    privateMkdir(path5.join(dir, "attempts"));
    this.#writeJsonAtomic(path5.join(dir, "task.json"), task);
    const status = {
      task_id: task.task_id,
      status: "queued",
      attempt: 1,
      created_at: createdAt,
      updated_at: createdAt,
      started_at: null,
      finished_at: null,
      worker_pid: null,
      zcode_session_id: null,
      exit_code: null
    };
    this.#writeJsonAtomic(path5.join(dir, "status.json"), status);
  }
  readTask(taskId2) {
    const file = path5.join(this.taskDir(taskId2), "task.json");
    const parsed = this.#readJson(file);
    const task = parsed;
    if (!task || task.task_id !== taskId2 || typeof task.workspace !== "string" || !task.workspace || typeof task.objective !== "string" || [task.requirements, task.allowed_paths, task.forbidden_paths, task.acceptance_criteria, task.test_commands].some((items) => !Array.isArray(items) || items.some((item) => typeof item !== "string"))) throw new Error(`corrupt task record: ${file}`);
    return task;
  }
  readSubmission(taskId2) {
    const file = path5.join(this.taskDir(taskId2), "submission.json");
    if (!existsSync5(file)) return null;
    return this.#readJson(file);
  }
  writeSubmission(taskId2, submission) {
    this.#writeJsonAtomic(path5.join(this.taskDir(taskId2), "submission.json"), submission);
  }
  writeWorkspaceRef(taskId2, workspace) {
    this.#writeJsonAtomic(path5.join(this.taskDir(taskId2), "workspace.json"), workspace);
  }
  readWorkspaceRef(taskId2) {
    const file = path5.join(this.taskDir(taskId2), "workspace.json");
    if (!existsSync5(file)) return null;
    const workspace = this.#readJson(file);
    if (!workspace || typeof workspace.canonicalPath !== "string" || typeof workspace.requestedPath !== "string" || !["direct", "worktree"].includes(workspace.mode)) throw new Error(`corrupt workspace record: ${file}`);
    return workspace;
  }
  readStatus(taskId2) {
    const file = path5.join(this.taskDir(taskId2), "status.json");
    const parsed = this.#readJson(file);
    if (!parsed || parsed.task_id !== taskId2 || !["queued", "running", "completed", "failed", "cancelled", "waiting_for_master"].includes(parsed.status) || !Number.isSafeInteger(parsed.attempt) || parsed.attempt < 1 || typeof parsed.created_at !== "string") {
      throw new Error(`corrupt status record: ${file}`);
    }
    return parsed;
  }
  /** Read-merge-write with an updated timestamp; atomic via temp file + rename. */
  writeStatus(taskId2, patch, expectedAttempt) {
    return withEventLock(path5.join(this.taskDir(taskId2), "state.lock"), () => {
      const current = this.readStatus(taskId2);
      if (expectedAttempt !== void 0 && (current.attempt !== expectedAttempt || isTerminalStatus(current.status))) throw new Error("stale or terminal worker status rejected");
      const next = {
        ...current,
        ...patch,
        task_id: current.task_id,
        updated_at: (/* @__PURE__ */ new Date()).toISOString()
      };
      this.#writeJsonAtomic(path5.join(this.taskDir(taskId2), "status.json"), next);
      return next;
    });
  }
  readResult(taskId2) {
    const file = path5.join(this.taskDir(taskId2), "result.json");
    if (!existsSync5(file)) return null;
    const result = this.#readJson(file);
    if (!result || result.task_id !== taskId2 || !Number.isSafeInteger(result.attempt) || !isTerminalStatus(result.status)) throw new Error(`corrupt result record: ${file}`);
    return result.attempt === this.readStatus(taskId2).attempt ? result : null;
  }
  writeResult(taskId2, result) {
    withEventLock(path5.join(this.taskDir(taskId2), "state.lock"), () => {
      if (this.readStatus(taskId2).attempt !== result.attempt) throw new Error("stale worker attempt result rejected");
      this.#writeJsonAtomic(path5.join(this.taskDir(taskId2), "result.json"), result);
    });
  }
  commitWorkerResult(taskId2, attempt, result, patch) {
    withEventLock(path5.join(this.taskDir(taskId2), "state.lock"), () => {
      this.assertWorkerAttempt(taskId2, attempt);
      this.#writeJsonAtomic(path5.join(this.taskDir(taskId2), "result.json"), result);
      const current = this.readStatus(taskId2);
      this.#writeJsonAtomic(path5.join(this.taskDir(taskId2), "status.json"), { ...current, ...patch, task_id: taskId2, attempt, updated_at: (/* @__PURE__ */ new Date()).toISOString() });
    });
  }
  patchRunningAttempt(taskId2, attempt, patch) {
    withEventLock(path5.join(this.taskDir(taskId2), "state.lock"), () => {
      const current = this.readStatus(taskId2);
      if (current.attempt !== attempt || current.status !== "running") return;
      this.#writeJsonAtomic(path5.join(this.taskDir(taskId2), "status.json"), { ...current, ...patch, updated_at: (/* @__PURE__ */ new Date()).toISOString() });
    });
  }
  /** Copies evidence before the continuation status commit; the old result remains recoverable. */
  archiveResultToAttempt(taskId2, attempt) {
    const dir = this.taskDir(taskId2);
    const source = path5.join(dir, "result.json");
    if (!existsSync5(source)) return;
    const targetDir = this.attemptDir(taskId2, attempt);
    privateMkdir(targetDir);
    copyFileSync(source, path5.join(targetDir, "result.json"));
    privateFile(path5.join(targetDir, "result.json"));
  }
  /** A claim is permanent: a started attempt must never execute again. */
  claimWorkerExecution(taskId2, attempt) {
    return withEventLock(path5.join(this.taskDir(taskId2), "state.lock"), () => {
      const status = this.readStatus(taskId2);
      if (status.attempt !== attempt || isTerminalStatus(status.status)) return false;
      privateMkdir(this.attemptDir(taskId2, attempt));
      try {
        writeFileSync2(path5.join(this.attemptDir(taskId2, attempt), "execution.claim"), JSON.stringify({ pid: process.pid }), { flag: "wx", mode: 384 });
        return true;
      } catch (error) {
        if (error.code === "EEXIST") return false;
        throw error;
      }
    });
  }
  assertWorkerAttempt(taskId2, attempt) {
    const status = this.readStatus(taskId2);
    if (status.attempt !== attempt || isTerminalStatus(status.status)) throw new Error("stale or terminal worker attempt rejected");
  }
  readArchivedResult(taskId2, attempt) {
    const file = path5.join(this.attemptDir(taskId2, attempt), "result.json");
    if (!existsSync5(file)) return null;
    return this.#readJson(file);
  }
  attemptDir(taskId2, attempt) {
    return path5.join(this.taskDir(taskId2), "attempts", String(attempt));
  }
  writeAttemptFile(taskId2, attempt, fileName, content) {
    const dir = this.attemptDir(taskId2, attempt);
    privateMkdir(dir);
    this.#writeTextAtomic(path5.join(dir, fileName), content);
  }
  writeAttemptMeta(taskId2, attempt, fileName, meta) {
    const dir = this.attemptDir(taskId2, attempt);
    privateMkdir(dir);
    this.#writeJsonAtomic(path5.join(dir, fileName), meta);
  }
  readAttemptMeta(taskId2, attempt, fileName) {
    const file = path5.join(this.attemptDir(taskId2, attempt), fileName);
    if (!existsSync5(file)) return null;
    return this.#readJson(file);
  }
  writeWorkerHeartbeat(taskId2, attempt, heartbeat) {
    withEventLock(path5.join(this.taskDir(taskId2), "state.lock"), () => {
      const status = this.readStatus(taskId2);
      const claim = this.readAttemptMeta(taskId2, attempt, "execution.claim");
      if (status.attempt !== attempt || status.status !== "running" || status.worker_pid !== heartbeat.worker_pid || claim?.pid !== heartbeat.worker_pid) {
        throw new Error("stale or unowned worker heartbeat rejected");
      }
      this.#writeJsonAtomic(path5.join(this.attemptDir(taskId2, attempt), "heartbeat.json"), heartbeat);
    });
  }
  readWorkerHeartbeat(taskId2, attempt) {
    const value = this.readAttemptMeta(taskId2, attempt, "heartbeat.json");
    if (!value || value.attempt !== attempt || !Number.isSafeInteger(value.worker_pid) || typeof value.heartbeat_at !== "string") return null;
    return value;
  }
  readAttemptText(taskId2, attempt, fileName) {
    const file = path5.join(this.attemptDir(taskId2, attempt), fileName);
    if (!existsSync5(file)) return null;
    return readFileSync4(file, "utf8");
  }
  // ---- A1 observation evidence (bounded reads, no task bodies) ----
  /** Bounded persisted evidence for the observation judger. */
  readObservationEvidence(taskId2, attempt) {
    const checkpointRaw = this.readAttemptMeta(taskId2, attempt, "outcome-checkpoint.json");
    const checkpoint = checkpointRaw && typeof checkpointRaw.recorded_at === "string" ? { recorded_at: checkpointRaw.recorded_at } : null;
    const heartbeat = this.readWorkerHeartbeat(taskId2, attempt);
    return {
      checkpoint,
      heartbeat,
      last_business_event: this.readLastBusinessEvent(taskId2),
      pending_interaction: this.readPendingInteraction(taskId2)
    };
  }
  /** Last complete event line, read from a bounded tail window. */
  readLastBusinessEvent(taskId2) {
    const file = path5.join(this.taskDir(taskId2), "events.jsonl");
    if (!existsSync5(file)) return null;
    let size = 0;
    try {
      size = statSync3(file).size;
    } catch {
      return null;
    }
    if (size === 0) return null;
    const window = Math.min(8192, size);
    const buffer = Buffer.allocUnsafe(window);
    let read = 0;
    try {
      const fd = openSync(file, "r");
      try {
        read = readSync(fd, buffer, 0, window, size - window);
      } finally {
        closeSync(fd);
      }
    } catch {
      return null;
    }
    const text = buffer.subarray(0, read).toString("utf8");
    const newline = text.indexOf("\n");
    const body = newline >= 0 && window < size ? text.slice(newline + 1) : text;
    const lines = body.split("\n").filter((line) => line.trim());
    for (let index = lines.length - 1; index >= 0; index -= 1) {
      const event = parseProgressEvent(lines[index]);
      if (event) return { at: event.at, type: event.type, seq: event.seq };
    }
    return null;
  }
  /** Distinct event types from a bounded tail window (A3 stage inference). */
  listRecentEventTypes(taskId2, maxLines) {
    const file = path5.join(this.taskDir(taskId2), "events.jsonl");
    if (!existsSync5(file)) return [];
    let size = 0;
    try {
      size = statSync3(file).size;
    } catch {
      return [];
    }
    const window = Math.min(256 * 1024, size);
    if (window === 0) return [];
    const buffer = Buffer.allocUnsafe(window);
    let read = 0;
    try {
      const fd = openSync(file, "r");
      try {
        read = readSync(fd, buffer, 0, window, size - window);
      } finally {
        closeSync(fd);
      }
    } catch {
      return [];
    }
    const text = buffer.subarray(0, read).toString("utf8");
    const newline = text.indexOf("\n");
    const body = newline >= 0 && window < size ? text.slice(newline + 1) : text;
    const types = /* @__PURE__ */ new Set();
    for (const line of body.split("\n").slice(-maxLines)) {
      const event = parseProgressEvent(line);
      if (event) types.add(event.type);
    }
    return [...types];
  }
  /** Newest unanswered interaction request (bounded directory scan). */
  readPendingInteraction(taskId2) {
    const directory = path5.join(this.taskDir(taskId2), "interactions");
    let entries;
    try {
      entries = readdirSync(directory);
    } catch {
      return null;
    }
    const files = entries.filter((entry) => entry.endsWith(".json")).slice(0, 64);
    let newest = null;
    for (const file of files) {
      try {
        const record = JSON.parse(readFileSync4(path5.join(directory, file), "utf8"));
        if (record.state === "pending" && typeof record.method === "string" && typeof record.created_at === "string") {
          if (!newest || record.created_at > newest.created_at) newest = { method: record.method, created_at: record.created_at };
        }
      } catch {
      }
    }
    return newest;
  }
  // ---- B3 attempt-scoped observation snapshot (fenced writer) ----
  /**
   * Writes worker-owned snapshot fields. Fenced twice: the attempt must still
   * be the current one, and the writer must own the attempt's execution claim,
   * so a replaced or stale worker can never overwrite current facts. Revision
   * is per writer and must strictly increase within one writer identity.
   */
  writeWorkerObservation(taskId2, attempt, writerPid, patch, revision, updatedAt = (/* @__PURE__ */ new Date()).toISOString()) {
    withEventLock(path5.join(this.taskDir(taskId2), "state.lock"), () => {
      const status = this.readStatus(taskId2);
      if (status.attempt !== attempt) throw new Error("stale attempt observation rejected");
      const claim = this.readAttemptMeta(taskId2, attempt, "execution.claim");
      if (claim?.pid !== writerPid) throw new Error("observation writer does not own the execution claim");
      this.#mergeObservationSnapshot(taskId2, attempt, "worker", revision, patch, updatedAt);
    });
  }
  /** Writes manager-owned snapshot fields (probe verdicts); worker business
   * phases are never overwritten from the manager side. */
  writeManagerObservation(taskId2, attempt, patch, revision, updatedAt = (/* @__PURE__ */ new Date()).toISOString()) {
    withEventLock(path5.join(this.taskDir(taskId2), "state.lock"), () => {
      const status = this.readStatus(taskId2);
      if (status.attempt !== attempt) throw new Error("stale attempt observation rejected");
      this.#mergeObservationSnapshot(taskId2, attempt, "manager", revision, patch, updatedAt);
    });
  }
  readObservationSnapshot(taskId2, attempt) {
    const file = path5.join(this.attemptDir(taskId2, attempt), "observation.json");
    if (!existsSync5(file)) return { snapshot: null, corrupt: false };
    try {
      const parsed = JSON.parse(readFileSync4(file, "utf8"));
      if (parsed.schema_version !== 1 || parsed.task_id !== taskId2 || parsed.attempt !== attempt) {
        return { snapshot: null, corrupt: true };
      }
      return { snapshot: parsed, corrupt: false };
    } catch {
      return { snapshot: null, corrupt: true };
    }
  }
  #mergeObservationSnapshot(taskId2, attempt, writer, revision, patch, updatedAt) {
    if (!Number.isSafeInteger(revision) || revision < 0) throw new Error("observation revision must be a non-negative integer");
    const current = this.readObservationSnapshot(taskId2, attempt).snapshot;
    const previousRevision = current?.writers?.[writer] ?? -1;
    if (revision <= previousRevision) throw new Error("stale observation revision rejected");
    const carried = current ?? {};
    const next = {
      schema_version: 1,
      task_id: taskId2,
      attempt,
      writers: { ...carried.writers, [writer]: revision },
      updated_at: updatedAt
    };
    const workerOwned = ["session_id", "turn_id", "last_runtime_seq", "activity_phase", "worker_identity", "runtime_identity"];
    const managerOwned = ["worker_probe", "runtime_probe"];
    for (const key of workerOwned) {
      if (key in patch) next[key] = patch[key];
      else if (key in carried) next[key] = carried[key];
    }
    for (const key of managerOwned) {
      if (key in patch) next[key] = patch[key];
      else if (key in carried) next[key] = carried[key];
    }
    this.writeAttemptMeta(taskId2, attempt, "observation.json", next);
  }
  // ---- A2 executor identity evidence ----
  writeExecutorIdentity(taskId2, attempt, identity) {
    const current = this.readAttemptMeta(taskId2, attempt, "executor-identity.json") ?? {};
    this.writeAttemptMeta(taskId2, attempt, "executor-identity.json", {
      ...current,
      ...identity
    });
  }
  readExecutorIdentity(taskId2, attempt) {
    return this.readAttemptMeta(taskId2, attempt, "executor-identity.json");
  }
  /**
   * Atomically claims the single worker-respawn slot for an attempt by
   * creating the marker file with an exclusive flag, so several Bridge
   * processes sharing this data root can never spawn two replacement
   * workers. Returns false when the slot is already claimed.
   */
  claimAttemptRespawn(taskId2, attempt) {
    const dir = this.attemptDir(taskId2, attempt);
    privateMkdir(dir);
    try {
      closeSync(openSync(path5.join(dir, "respawn.claim"), "wx"));
      return true;
    } catch (error) {
      if (error.code === "EEXIST") return false;
      throw error;
    }
  }
  /** File time of the respawn claim, or null when the attempt is unclaimed. */
  respawnClaimedAt(taskId2, attempt) {
    try {
      return statSync3(path5.join(this.attemptDir(taskId2, attempt), "respawn.claim")).mtime;
    } catch {
      return null;
    }
  }
  /** Append-only, byte-bounded. Returns whether the chunk was truncated. */
  appendLog(taskId2, kind, text) {
    if (!text) return { truncated: false };
    const dir = this.taskDir(taskId2);
    privateMkdir(dir);
    const file = path5.join(dir, `${kind}.log`);
    let currentBytes = 0;
    try {
      currentBytes = statSync3(file).size;
    } catch {
      currentBytes = 0;
    }
    const bytes = Buffer.from(text, "utf8");
    const room = this.#maxLogBytes - currentBytes;
    if (room <= 0) return { truncated: true };
    appendFileSync(file, bytes.length <= room ? bytes : bytes.subarray(0, room), { mode: 384 });
    privateFile(file);
    return { truncated: bytes.length > room };
  }
  readLog(taskId2, kind) {
    const file = path5.join(this.taskDir(taskId2), `${kind}.log`);
    return existsSync5(file) ? readFileSync4(file, "utf8") : "";
  }
  appendEvent(taskId2, type, summary, details, at = (/* @__PURE__ */ new Date()).toISOString()) {
    const dir = this.taskDir(taskId2);
    mkdirSync2(dir, { recursive: true });
    const lockDir = path5.join(dir, "events.lock");
    return withEventLock(lockDir, () => {
      const file = path5.join(dir, "events.jsonl");
      const seqFile = path5.join(dir, "events.seq");
      let bytes = 0;
      let previousSeq = 0;
      let needsSeparator = false;
      try {
        const info = statSync3(file);
        bytes = info.size;
        let lastByte;
        if (bytes > 0) {
          const fd = openSync(file, "r");
          try {
            const tail = Buffer.alloc(1);
            readSync(fd, tail, 0, 1, bytes - 1);
            lastByte = tail[0];
          } finally {
            closeSync(fd);
          }
        }
        needsSeparator = bytes > 0 && lastByte !== 10;
      } catch (error) {
        if (error.code !== "ENOENT") throw error;
        bytes = 0;
      }
      try {
        previousSeq = Number(readFileSync4(seqFile, "utf8"));
        if (!Number.isSafeInteger(previousSeq) || previousSeq < 0) previousSeq = readLastEventSeq(file);
      } catch {
        previousSeq = readLastEventSeq(file);
      }
      const event = {
        seq: previousSeq + 1,
        at,
        type: type.slice(0, 80),
        summary: summary.length <= 2e3 ? summary : `${summary.slice(0, 1970)}\u2026[output truncated]`,
        ...details && Object.keys(details).length ? { details } : {}
      };
      const line = `${JSON.stringify(event)}
`;
      const lineBytes = Buffer.byteLength(line, "utf8") + (needsSeparator ? 1 : 0);
      const critical = CRITICAL_EVENT_TYPES.has(type);
      const capacity = this.#maxEventBytes + (critical ? MAX_CRITICAL_EVENT_RESERVE_BYTES : 0);
      if (lineBytes > 64e3 || bytes + lineBytes > capacity) return null;
      this.#writeTextAtomic(seqFile, String(event.seq));
      const eventOffset = bytes + (needsSeparator ? 1 : 0);
      appendFileSync(file, `${needsSeparator ? "\n" : ""}${line}`, { encoding: "utf8", mode: 384 });
      privateFile(file);
      const genFile = path5.join(dir, "events.gen");
      if (!existsSync5(genFile)) {
        this.#writeTextAtomic(genFile, randomUUID2());
      }
      if (event.seq % 100 === 0) {
        const index = path5.join(dir, "events.index");
        appendFileSync(index, `${event.seq}	${eventOffset}
`, { encoding: "utf8", mode: 384 });
        privateFile(index);
      }
      return event;
    });
  }
  readEvents(taskId2, afterSeq = 0, limit = 100, view = "raw") {
    const file = path5.join(this.taskDir(taskId2), "events.jsonl");
    if (!existsSync5(file)) return { events: [], nextSeq: afterSeq, hasMore: false, omittedEvents: 0 };
    let offset = 0;
    const indexFile = path5.join(this.taskDir(taskId2), "events.index");
    if (existsSync5(indexFile)) {
      for (const row of readFileSync4(indexFile, "utf8").split(/\r?\n/u)) {
        const [seqText, offsetText] = row.split("	");
        const seq = Number(seqText);
        const candidateOffset = Number(offsetText);
        if (Number.isInteger(seq) && Number.isSafeInteger(candidateOffset) && seq <= afterSeq) offset = candidateOffset;
        if (seq > afterSeq) break;
      }
    }
    const fd = openSync(file, "r");
    const page = [];
    let hasMore = false;
    let position = offset;
    let pending = "";
    const decoder = new StringDecoder("utf8");
    const buffer = Buffer.allocUnsafe(64 * 1024);
    try {
      while (true) {
        const count = readSync(fd, buffer, 0, buffer.length, position);
        if (count <= 0) break;
        position += count;
        const lines = `${pending}${decoder.write(buffer.subarray(0, count))}`.split(/\r?\n/u);
        pending = lines.pop() ?? "";
        for (const line of lines) {
          const event = parseProgressEvent(line);
          if (!event || event.seq <= afterSeq) continue;
          if (page.length === limit) {
            hasMore = true;
            break;
          }
          page.push(event);
        }
        if (hasMore) break;
      }
      pending += decoder.end();
      if (!hasMore && pending) {
        const event = parseProgressEvent(pending);
        if (event && event.seq > afterSeq) {
          if (page.length === limit) hasMore = true;
          else page.push(event);
        }
      }
    } finally {
      closeSync(fd);
    }
    let events = page;
    let omittedEvents = 0;
    if (view === "summary") {
      events = [];
      for (const event of page) {
        const previous = events.at(-1);
        if (event.type === "model_output" && previous?.type === "model_output") {
          const combined = previous.summary + event.summary;
          events[events.length - 1] = {
            ...previous,
            seq: event.seq,
            at: event.at,
            summary: combined.length <= 5e3 ? combined : `${combined.slice(0, 4950)}\u2026[output compacted]`
          };
          omittedEvents += 1;
        } else {
          events.push(event);
        }
      }
    }
    return {
      events,
      nextSeq: page.at(-1)?.seq ?? afterSeq,
      hasMore,
      omittedEvents
    };
  }
  /**
   * B1 bounded scan: parses complete byte lines only; an unfinished trailing
   * line is not consumed and the cursor never passes it. Complete corrupt
   * lines are skipped but counted. The byte budget covers at most the
   * configured budget plus one read block; exhaustion reports scan_incomplete
   * and never a has_more=true page with an unchanged after_seq.
   */
  readEventsBounded(taskId2, input = {}) {
    const afterSeq = input.afterSeq ?? 0;
    const limit = input.limit ?? 100;
    const view = input.view ?? "raw";
    const budget = input.maxBytes ?? this.#maxEventBytes;
    const file = path5.join(this.taskDir(taskId2), "events.jsonl");
    const empty = {
      events: [],
      nextSeq: afterSeq,
      hasMore: false,
      omittedEvents: 0,
      scan_incomplete: false,
      scan_cursor: null,
      cursor_invalid: false,
      metrics: { bytes_read: 0, records_scanned: 0, invalid_lines: 0, corrupt_count: 0, first_corrupt_offset: null, index_fallback: false }
    };
    let size = 0;
    try {
      size = statSync3(file).size;
    } catch {
      return empty;
    }
    if (size === 0) return empty;
    let startOffset = 0;
    let cursorInvalid = false;
    if (input.cursor) {
      const generation = this.readEventGeneration(taskId2);
      const valid = input.cursor.v === 1 && input.cursor.task_id === taskId2 && generation !== null && input.cursor.generation === generation && Number.isSafeInteger(input.cursor.offset) && input.cursor.offset >= 0 && input.cursor.offset <= size;
      if (!valid) {
        return { ...empty, cursor_invalid: true };
      }
      startOffset = input.cursor.offset;
      if (input.cursor.first_seq !== null) {
        const firstSeq = this.readFirstEventSeq(file, size);
        if (firstSeq === null || firstSeq !== input.cursor.first_seq) {
          return { ...empty, cursor_invalid: true };
        }
      }
    }
    let indexFallback = false;
    if (startOffset === 0) {
      const indexFile = path5.join(this.taskDir(taskId2), "events.index");
      if (existsSync5(indexFile)) {
        try {
          let lastSeq = 0;
          let lastOffset = 0;
          for (const row of readFileSync4(indexFile, "utf8").split(/\r?\n/u)) {
            if (!row.trim()) continue;
            const [seqText, offsetText] = row.split("	");
            const seq = Number(seqText);
            const offset = Number(offsetText);
            if (!Number.isSafeInteger(seq) || !Number.isSafeInteger(offset) || seq <= lastSeq || offset < lastOffset || offset > size) {
              throw new Error("invalid index row");
            }
            lastSeq = seq;
            lastOffset = offset;
          }
          for (const row of readFileSync4(indexFile, "utf8").split(/\r?\n/u)) {
            const [seqText, offsetText] = row.split("	");
            const seq = Number(seqText);
            const offset = Number(offsetText);
            if (Number.isSafeInteger(seq) && Number.isSafeInteger(offset) && seq <= afterSeq && offset <= size) startOffset = offset;
            if (Number.isSafeInteger(seq) && seq > afterSeq) break;
          }
        } catch {
          indexFallback = true;
          startOffset = 0;
        }
      }
    }
    const events = [];
    let scanned = 0;
    let bytesRead = 0;
    let invalidLines = 0;
    let corruptCount = 0;
    let firstCorruptOffset = null;
    let hasMore = false;
    let position = startOffset;
    let lastCompleteOffset = startOffset;
    let pending = "";
    let pendingStartOffset = startOffset;
    let reachedEnd = false;
    const maxRead = budget + 64 * 1024;
    const decoder = new StringDecoder("utf8");
    const buffer = Buffer.allocUnsafe(64 * 1024);
    const fd = openSync(file, "r");
    const processLine = (line, lineOffset, lineEndOffset) => {
      lastCompleteOffset = lineEndOffset;
      if (!line.trim()) return true;
      const event = parseProgressEvent(line);
      if (!event) {
        invalidLines += 1;
        corruptCount += 1;
        if (firstCorruptOffset === null) firstCorruptOffset = lineOffset;
        return true;
      }
      scanned += 1;
      if (event.seq <= afterSeq) return true;
      if (events.length === limit) {
        hasMore = true;
        lastCompleteOffset = lineOffset;
        return false;
      }
      events.push(event);
      return true;
    };
    try {
      while (bytesRead < maxRead) {
        const count = readSync(fd, buffer, 0, buffer.length, position);
        if (count <= 0) {
          reachedEnd = true;
          break;
        }
        position += count;
        bytesRead += count;
        const text = pending + decoder.write(buffer.subarray(0, count));
        let searchFrom = 0;
        let consumedBytes = 0;
        let stopped = false;
        while (true) {
          const newline = text.indexOf("\n", searchFrom);
          if (newline < 0) break;
          const line = text.slice(searchFrom, newline).replace(/\r$/u, "");
          const lineBytes = Buffer.byteLength(text.slice(searchFrom, newline + 1), "utf8");
          const lineOffset = pendingStartOffset + consumedBytes;
          consumedBytes += lineBytes;
          searchFrom = newline + 1;
          if (!processLine(line, lineOffset, pendingStartOffset + consumedBytes)) {
            stopped = true;
            break;
          }
        }
        if (stopped) {
          pending = "";
          break;
        }
        pending = text.slice(searchFrom);
        pendingStartOffset += consumedBytes;
      }
      if (!hasMore) {
        const tail = pending + decoder.end();
        let searchFrom = 0;
        let consumedBytes = 0;
        while (true) {
          const newline = tail.indexOf("\n", searchFrom);
          if (newline < 0) break;
          const line = tail.slice(searchFrom, newline).replace(/\r$/u, "");
          const lineBytes = Buffer.byteLength(tail.slice(searchFrom, newline + 1), "utf8");
          const lineOffset = pendingStartOffset + consumedBytes;
          consumedBytes += lineBytes;
          searchFrom = newline + 1;
          if (!processLine(line, lineOffset, pendingStartOffset + consumedBytes)) break;
        }
        if (!hasMore && !reachedEnd && bytesRead >= maxRead) {
          lastCompleteOffset = pendingStartOffset + consumedBytes;
        }
      }
    } finally {
      closeSync(fd);
    }
    let page = events;
    let omittedEvents = 0;
    if (view === "summary") {
      page = [];
      for (const event of events) {
        const previous = page.at(-1);
        if (event.type === "model_output" && previous?.type === "model_output") {
          const combined = previous.summary + event.summary;
          page[page.length - 1] = {
            ...previous,
            seq: event.seq,
            at: event.at,
            summary: combined.length <= 5e3 ? combined : `${combined.slice(0, 4950)}\u2026[output compacted]`
          };
          omittedEvents += 1;
        } else {
          page.push(event);
        }
      }
    }
    const scanIncomplete = !reachedEnd && !hasMore;
    const nextSeq = page.at(-1)?.seq ?? afterSeq;
    if (hasMore && nextSeq === afterSeq && !input.cursor) hasMore = false;
    const cursor = this.readEventGeneration(taskId2) ? { v: 1, task_id: taskId2, generation: this.readEventGeneration(taskId2), offset: lastCompleteOffset, first_seq: input.cursor?.first_seq ?? this.readFirstEventSeq(file, size) } : null;
    return {
      events: page,
      nextSeq,
      hasMore,
      omittedEvents,
      scan_incomplete: scanIncomplete,
      scan_cursor: cursor,
      cursor_invalid: false,
      metrics: { bytes_read: bytesRead, records_scanned: scanned, invalid_lines: invalidLines, corrupt_count: corruptCount, first_corrupt_offset: firstCorruptOffset, index_fallback: indexFallback }
    };
  }
  /** Generation marker detecting log replacement/truncation across reads. */
  readEventGeneration(taskId2) {
    try {
      const value = readFileSync4(path5.join(this.taskDir(taskId2), "events.gen"), "utf8").trim();
      return value || null;
    } catch {
      return null;
    }
  }
  readFirstEventSeq(file, size) {
    const window = Math.min(64 * 1024, size);
    const buffer = Buffer.allocUnsafe(window);
    let read = 0;
    try {
      const fd = openSync(file, "r");
      try {
        read = readSync(fd, buffer, 0, window, 0);
      } finally {
        closeSync(fd);
      }
    } catch {
      return null;
    }
    const text = buffer.subarray(0, read).toString("utf8");
    const newline = text.indexOf("\n");
    if (newline < 0) return null;
    const event = parseProgressEvent(text.slice(0, newline).replace(/\r$/u, ""));
    return event ? event.seq : null;
  }
  writeInteractionRequest(taskId2, request, createdAt = (/* @__PURE__ */ new Date()).toISOString()) {
    const directory = path5.join(this.taskDir(taskId2), "interactions");
    privateMkdir(directory);
    const file = this.interactionFile(taskId2, request.request_id);
    return withEventLock(path5.join(this.taskDir(taskId2), "interactions.lock"), () => {
      if (existsSync5(file)) {
        const record2 = this.#readJson(file);
        if (record2.request_id !== request.request_id || record2.method !== request.method || stableJson(record2.params) !== stableJson(request.params)) {
          throw new Error("interaction request id collision");
        }
        return { record: record2, created: false };
      }
      if (Buffer.byteLength(JSON.stringify(request.params), "utf8") > 32e3) {
        throw new Error("ZCode interaction request exceeded the 32 KB persistence limit");
      }
      const record = {
        ...request,
        state: "pending",
        created_at: createdAt
      };
      this.#writeJsonAtomic(file, record);
      return { record, created: true };
    });
  }
  readInteractionRequest(taskId2, requestId) {
    const file = this.interactionFile(taskId2, requestId);
    if (!existsSync5(file)) return null;
    const record = this.#readJson(file);
    if (record.request_id !== requestId) throw new Error("interaction request id hash mismatch");
    return record;
  }
  answerInteractionRequest(taskId2, requestId, answer, answeredAt = (/* @__PURE__ */ new Date()).toISOString()) {
    const file = this.interactionFile(taskId2, requestId);
    return withEventLock(path5.join(this.taskDir(taskId2), "interactions.lock"), () => {
      if (!existsSync5(file)) throw new Error(`unknown ZCode interaction request: ${requestId}`);
      const current = this.#readJson(file);
      if (current.request_id !== requestId) throw new Error("interaction request id hash mismatch");
      if (current.state === "answered") return "already_answered";
      this.#writeJsonAtomic(file, {
        ...current,
        state: "answered",
        answer,
        answered_at: answeredAt
      });
      return "answered";
    });
  }
  interactionFile(taskId2, requestId) {
    if (!requestId || requestId.length > 512) throw new Error("invalid ZCode interaction request_id");
    const key = createHash2("sha256").update(requestId).digest("hex");
    return path5.join(this.taskDir(taskId2), "interactions", `${this.readStatus(taskId2).attempt}-${key}.json`);
  }
  #readJson(file) {
    try {
      return JSON.parse(readFileSync4(file, "utf8"));
    } catch (error) {
      throw new Error(`unreadable or corrupt JSON record: ${file}`, { cause: error });
    }
  }
  #writeJsonAtomic(file, value) {
    this.#writeTextAtomic(file, JSON.stringify(value, null, 2));
  }
  #writeTextAtomic(file, text) {
    const tmp = `${file}.${randomUUID2()}.tmp`;
    try {
      writeFileSync2(tmp, text, { encoding: "utf8", mode: 384 });
      privateFile(tmp);
      atomicRenameSync(tmp, file);
    } catch (error) {
      try {
        rmSync(tmp, { force: true });
      } catch {
      }
      throw error;
    }
  }
};
function stableJson(value) {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.entries(value).sort(([a], [b]) => a.localeCompare(b)).map(([key, item]) => `${JSON.stringify(key)}:${stableJson(item)}`).join(",")}}`;
  return JSON.stringify(value) ?? "null";
}
function withEventLock(lockDir, operation) {
  const deadline = Date.now() + 1e4;
  let release;
  while (!(release = tryAcquireProcessLock(lockDir))) {
    if (Date.now() >= deadline) throw new Error(`timed out waiting for task state/event lock: ${lockDir}`);
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 10);
  }
  try {
    return operation();
  } finally {
    release();
  }
}
function privateMkdir(directory) {
  mkdirSync2(directory, { recursive: true, mode: 448 });
  privateDirectory(directory);
}
function privateDirectory(directory) {
  if (process.platform !== "win32") chmodSync(directory, 448);
}
function privateFile(file) {
  if (process.platform !== "win32") chmodSync(file, 384);
}
function readLastEventSeq(file) {
  if (!existsSync5(file)) return 0;
  for (const line of readFileSync4(file, "utf8").trimEnd().split("\n").reverse()) {
    try {
      const event = JSON.parse(line);
      if (Number.isInteger(event.seq)) return event.seq;
    } catch {
    }
  }
  return 0;
}
function parseProgressEvent(line) {
  if (!line) return null;
  try {
    const event = JSON.parse(line);
    return Number.isInteger(event.seq) ? event : null;
  } catch {
    return null;
  }
}
function isTerminalStatus(status) {
  return status === "completed" || status === "failed" || status === "cancelled" || status === "waiting_for_master";
}

// src/runtime/process-probe.ts
import { readFile } from "node:fs/promises";
import { spawn as spawn3 } from "node:child_process";
var PROCESS_IDENTITY_VERSION = 1;
var DEFAULT_PROBE_TIMEOUT_MS = 5e3;
var DEFAULT_MAX_CONCURRENT = 2;
function identityOfFingerprint(pid, fingerprint, precision, now) {
  return {
    pid,
    fingerprint,
    fingerprint_precision: precision,
    identity_version: PROCESS_IDENTITY_VERSION,
    platform: process.platform,
    captured_at: new Date(now()).toISOString()
  };
}
function verdict(state, reason, now) {
  return { state, reason_code: reason, observed_at: new Date(now()).toISOString() };
}
function failedQuery(reason) {
  return { ok: false, reason, fingerprints: /* @__PURE__ */ new Map() };
}
function windowsBatchQuery(pids, timeoutMs) {
  return new Promise((resolve) => {
    const script = `Get-Process -Id ${pids.join(",")} -ErrorAction SilentlyContinue | ForEach-Object { "{0}|{1}" -f $_.Id, $_.StartTime.Ticks }`;
    const child = spawn3("powershell.exe", ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script], {
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
      shell: false
    });
    let stdout = "";
    let settled = false;
    const finish = (query) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(query);
    };
    const timer = setTimeout(() => {
      try {
        child.kill("SIGKILL");
      } catch {
      }
      finish(failedQuery("timeout"));
    }, timeoutMs);
    timer.unref();
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    let stderrBytes = 0;
    child.stderr.on("data", (chunk) => {
      stderrBytes = Math.min(64e3, stderrBytes + chunk.length);
    });
    child.stdout.on("data", (chunk) => {
      if (stdout.length < 1e6) stdout += chunk;
    });
    child.on("error", () => finish(failedQuery("spawn_error")));
    child.on("close", () => {
      const map = /* @__PURE__ */ new Map();
      for (const line of stdout.split(/\r?\n/u)) {
        const match = /^(\d+)\|(\d+)$/u.exec(line.trim());
        if (!match) continue;
        map.set(Number(match[1]), match[2]);
      }
      if (map.size === 0) {
        finish(stderrBytes > 0 ? failedQuery("query_error") : { ok: true, reason: "ok", fingerprints: map });
        return;
      }
      finish({ ok: true, reason: "ok", fingerprints: map });
    });
  });
}
async function darwinQuery(pids, timeoutMs) {
  return new Promise((resolve) => {
    const child = spawn3("ps", ["-o", "pid=,lstart=", "-p", pids.join(",")], {
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
      shell: false
    });
    let stdout = "";
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      try {
        child.kill("SIGKILL");
      } catch {
      }
      resolve(failedQuery("timeout"));
    }, timeoutMs);
    timer.unref();
    child.stdout.setEncoding("utf8");
    child.stdout.on("data", (chunk) => {
      if (stdout.length < 1e6) stdout += chunk;
    });
    child.on("error", () => {
      if (!settled) {
        settled = true;
        clearTimeout(timer);
        resolve(failedQuery("spawn_error"));
      }
    });
    child.on("close", () => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      const map = /* @__PURE__ */ new Map();
      for (const line of stdout.split(/\r?\n/u)) {
        const match = /^\s*(\d+)\s+(.+)$/u.exec(line);
        if (match) map.set(Number(match[1]), match[2].trim());
      }
      resolve({ ok: true, reason: "ok", fingerprints: map });
    });
  });
}
function createPlatformProbe(options = {}) {
  const timeoutMs = options.timeoutMs ?? DEFAULT_PROBE_TIMEOUT_MS;
  const maxConcurrent = options.maxConcurrent ?? DEFAULT_MAX_CONCURRENT;
  const now = options.now ?? Date.now;
  let chain = Promise.resolve();
  let inFlight = 0;
  let waiters = [];
  const schedule = async (operation) => {
    if (inFlight >= maxConcurrent) {
      await new Promise((resolve) => waiters.push(resolve));
    }
    inFlight += 1;
    try {
      return await operation();
    } finally {
      inFlight -= 1;
      const next = waiters.shift();
      if (next) next();
    }
  };
  const probe = async (requests) => {
    if (requests.length === 0) return [];
    const distinct = [...new Set(requests.map((request) => request.pid).filter((pid) => Number.isInteger(pid) && pid > 0))];
    const query = await schedule(async () => {
      if (process.platform === "win32") return windowsBatchQuery(distinct, timeoutMs);
      if (process.platform === "darwin") return darwinQuery(distinct, timeoutMs);
      if (process.platform === "linux") {
        const map = /* @__PURE__ */ new Map();
        for (const pid of distinct) {
          try {
            const stat = await readFile(`/proc/${pid}/stat`, "utf8");
            const afterComm = stat.slice(stat.lastIndexOf(")") + 2);
            const fields = afterComm.split(" ");
            const starttime = fields[19];
            if (starttime) map.set(pid, starttime.trim());
          } catch (error) {
            if (error.code === "ENOENT") continue;
            return failedQuery("proc_read_error");
          }
        }
        return { ok: true, reason: "ok", fingerprints: map };
      }
      return failedQuery("unsupported_platform");
    });
    return requests.map((request) => {
      if (!Number.isInteger(request.pid) || request.pid <= 0) return verdict("unknown", "invalid_pid", now);
      if (!query.ok) return verdict("unknown", `query_${query.reason}`, now);
      const fingerprint = query.fingerprints.get(request.pid);
      if (fingerprint === void 0) {
        return verdict("exited", "pid_absent", now);
      }
      if (!request.identity || request.identity.fingerprint === null) {
        return verdict("unknown", "live_pid_no_fingerprint", now);
      }
      if (request.identity.fingerprint_precision === "coarse") {
        return request.identity.fingerprint === fingerprint ? verdict("unknown", "coarse_fingerprint_match", now) : verdict("exited", "pid_reused_coarse", now);
      }
      if (request.identity.fingerprint !== fingerprint) {
        return verdict("exited", "pid_reused", now);
      }
      return verdict("alive", "pid_and_fingerprint_match", now);
    });
  };
  const fingerprintOfPid = async (pid) => {
    const query = await schedule(async () => {
      if (process.platform === "win32") return windowsBatchQuery([pid], timeoutMs);
      if (process.platform === "darwin") return darwinQuery([pid], timeoutMs);
      if (process.platform === "linux") {
        const map = /* @__PURE__ */ new Map();
        try {
          const stat = await readFile(`/proc/${pid}/stat`, "utf8");
          const afterComm = stat.slice(stat.lastIndexOf(")") + 2);
          const starttime = afterComm.split(" ")[19];
          if (starttime) map.set(pid, starttime.trim());
        } catch {
        }
        return { ok: true, reason: "ok", fingerprints: map };
      }
      return failedQuery("unsupported_platform");
    });
    const fingerprint = query.fingerprints.get(pid);
    if (!query.ok || !fingerprint) return identityOfFingerprint(pid, null, "unknown", now);
    const precision = process.platform === "darwin" ? "coarse" : "exact";
    return identityOfFingerprint(pid, fingerprint, precision, now);
  };
  return {
    platform: process.platform,
    identityOf: fingerprintOfPid,
    selfIdentity: () => fingerprintOfPid(process.pid),
    probe
  };
}

// src/usage/normalize.ts
var KNOWN_NUMERIC_FIELDS = [
  ["input_tokens", "inputTokens"],
  ["output_tokens", "outputTokens"],
  ["total_tokens", "totalTokens"],
  ["cached_input_tokens", "cachedInputTokens"],
  ["reasoning_tokens", "reasoningTokens"]
];
var SOURCE_FIELDS = ["source", "usage_source"];
function acceptNumber(value) {
  if (value === void 0 || value === null) return { value: null, conflict: null };
  if (typeof value !== "number") return { value: null, conflict: "non_numeric_rejected" };
  if (Number.isNaN(value)) return { value: null, conflict: "nan_rejected" };
  if (!Number.isFinite(value)) return { value: null, conflict: "non_finite_rejected" };
  if (!Number.isSafeInteger(value)) return { value: null, conflict: "unsafe_integer_rejected" };
  if (value < 0) return { value: null, conflict: "negative_rejected" };
  return { value, conflict: null };
}
function normalizeUsage(raw, options = {}) {
  if (raw === null || raw === void 0) return null;
  if (typeof raw !== "object" || Array.isArray(raw)) return null;
  const record = raw;
  const conflicts = /* @__PURE__ */ new Set();
  const result = {
    source: null,
    scope: null,
    observed_at: null,
    finality: "reported",
    input_tokens: null,
    output_tokens: null,
    total_tokens: null,
    cached_input_tokens: null,
    reasoning_tokens: null,
    conflicts: [],
    dropped_unknown_keys: 0
  };
  let knownKeys = 0;
  for (const [canonical, alias] of KNOWN_NUMERIC_FIELDS) {
    const snake = record[canonical];
    const camel = record[alias];
    const hasSnake = snake !== void 0;
    const hasCamel = camel !== void 0;
    if (!hasSnake && !hasCamel) continue;
    knownKeys += 1;
    if (hasSnake && hasCamel && snake !== camel) conflicts.add("duplicate_synonyms");
    const accepted = acceptNumber(hasSnake ? snake : camel);
    if (accepted.conflict) {
      conflicts.add(accepted.conflict);
      continue;
    }
    result[canonical] = accepted.value;
  }
  for (const key of Object.keys(record)) {
    const known = KNOWN_NUMERIC_FIELDS.some(([canonical, alias]) => key === canonical || key === alias);
    const source = SOURCE_FIELDS.some((candidate) => key === candidate);
    if (!known && !source) result.dropped_unknown_keys += 1;
  }
  for (const sourceField of SOURCE_FIELDS) {
    const value = record[sourceField];
    if (typeof value === "string" && value.trim()) {
      result.source = options.source ?? value.trim();
      break;
    }
  }
  if (result.source === null) result.source = options.source ?? null;
  result.scope = options.scope ?? null;
  result.observed_at = options.observedAt ?? null;
  const { input_tokens: input, output_tokens: output, total_tokens: total } = result;
  if (total !== null && input !== null && output !== null && total !== input + output) {
    conflicts.add("total_mismatch");
  }
  if (options.source?.includes("session_delta")) result.finality = "derived";
  if (conflicts.size > 0) result.finality = result.finality === "derived" ? "derived" : "partial";
  result.conflicts = [...conflicts];
  if (knownKeys === 0 && result.dropped_unknown_keys === 0) return null;
  return result;
}
function phaseDuration(startIso, endIso, notes) {
  if (!startIso || !endIso) return null;
  const start = Date.parse(startIso);
  const end = Date.parse(endIso);
  if (!Number.isFinite(start) || !Number.isFinite(end)) {
    notes.push("unparsable_timestamp");
    return null;
  }
  if (end < start) {
    notes.push("clock_regression_dropped");
    return null;
  }
  return end - start;
}

// src/worker/run-task.ts
async function runWorkerTask(options) {
  const store = new TaskStore(options.dataRoot);
  const now = options.now ?? (() => /* @__PURE__ */ new Date());
  const probe = options.probe ?? createPlatformProbe();
  const taskId2 = options.taskId;
  const task = store.readTask(taskId2);
  const initialStatus = store.readStatus(taskId2);
  const attempt = options.attempt;
  if (!store.claimWorkerExecution(taskId2, attempt)) throw new Error("worker attempt already claimed, stale, or terminal");
  let observationRevision = 0;
  let activityPhase = "preparing";
  const writePhase = () => {
    observationRevision += 1;
    try {
      store.writeWorkerObservation(taskId2, attempt, process.pid, { activity_phase: activityPhase }, observationRevision, now().toISOString());
    } catch {
    }
  };
  if (initialStatus.cancel_requested === true) {
    const finishedAt2 = now().toISOString();
    const result2 = buildTaskResult({
      task,
      attempt,
      startedAt: initialStatus.started_at,
      finishedAt: finishedAt2,
      outcome: null,
      failure: { code: "cancelled", message: "cancelled by request before the worker started the agent" },
      cancelled: true
    });
    store.commitWorkerResult(taskId2, attempt, result2, { status: "cancelled", finished_at: finishedAt2, worker_pid: null });
    return { status: result2.status, result: result2 };
  }
  const startedAt = initialStatus.started_at ?? now().toISOString();
  store.writeStatus(taskId2, { status: "running", started_at: startedAt, worker_pid: process.pid }, attempt);
  store.appendEvent(taskId2, "worker_running", "Task worker is preparing the ZCode runtime");
  store.writeAttemptMeta(taskId2, attempt, "started.json", {
    worker_pid: process.pid,
    started_at: startedAt
  });
  writePhase();
  void probe.selfIdentity().then(
    (identity) => {
      store.writeExecutorIdentity(taskId2, attempt, { worker: identity });
      observationRevision += 1;
      try {
        store.writeWorkerObservation(taskId2, attempt, process.pid, { worker_identity: identity }, observationRevision, now().toISOString());
      } catch {
      }
    },
    () => void 0
  );
  const heartbeat = {
    attempt,
    worker_pid: process.pid,
    started_at: startedAt,
    heartbeat_at: now().toISOString(),
    heartbeat_seq: 0,
    session_id: initialStatus.zcode_session_id ?? null,
    turn_id: null,
    last_event_seq: 0,
    last_event_type: "worker_running",
    zcode_event_seq: 0
  };
  const persistHeartbeat = () => {
    heartbeat.heartbeat_at = now().toISOString();
    heartbeat.heartbeat_seq += 1;
    store.writeWorkerHeartbeat(taskId2, attempt, heartbeat);
    writePhase();
  };
  persistHeartbeat();
  const heartbeatTimer = setInterval(() => {
    try {
      persistHeartbeat();
    } catch {
    }
  }, 3e3);
  heartbeatTimer.unref();
  const continueSpec = store.readAttemptMeta(taskId2, attempt, "continue.json");
  const previousResult = continueSpec ? store.readArchivedResult(taskId2, continueSpec.previous_attempt ?? attempt - 1) : null;
  const promptText = continueSpec ? buildContinuePrompt({
    task,
    feedback: continueSpec.feedback,
    additionalRequirements: continueSpec.additional_requirements ?? [],
    previousSessionId: continueSpec.previous_session_id,
    previousResult
  }) : buildTaskPrompt(task);
  store.writeAttemptFile(taskId2, attempt, "prompt.txt", promptText);
  const correlation = {
    rpc_accepted_at: null,
    turn_started_at: null,
    turn_completed_at: null,
    turn_id: null,
    session_id: initialStatus.zcode_session_id ?? null
  };
  const persistCorrelation = () => {
    try {
      store.writeAttemptMeta(taskId2, attempt, "turn-correlation.json", { ...correlation });
    } catch {
    }
  };
  const persistCorrelationTimer = setInterval(persistCorrelation, 5e3);
  persistCorrelationTimer.unref();
  const modelProfile = {
    executor: "zcode",
    provider_id: null,
    model_id: null,
    requested_model: task.model ? `${task.model.provider_id}/${task.model.model_id}` : null,
    requested_reasoning_level: task.model?.reasoning_level ?? null,
    effective_reasoning_level: null,
    effective_reasoning_level_source: "not_reported",
    selection_source: null,
    effective_at: null,
    session_id: initialStatus.zcode_session_id ?? null,
    turn_id: null
  };
  let outcome = null;
  let failure = null;
  let pendingModelOutput = "";
  let lastModelOutputAt = 0;
  const flushModelOutput = () => {
    if (!pendingModelOutput) return;
    store.assertWorkerAttempt(taskId2, attempt);
    for (let offset = 0; offset < pendingModelOutput.length; offset += 2e3) store.appendEvent(taskId2, "model_output", pendingModelOutput.slice(offset, offset + 2e3));
    pendingModelOutput = "";
    lastModelOutputAt = Date.now();
  };
  try {
    if (options.resolver) {
      await options.resolver.resolve();
    }
    const adapter = options.adapter ?? new ZCodeAppServerAdapter({
      host: options.host,
      onEvent: (event) => {
        store.assertWorkerAttempt(taskId2, attempt);
        if (event.type === "model_output") {
          pendingModelOutput += event.summary;
          if (pendingModelOutput.length >= 4e3 || Date.now() - lastModelOutputAt >= 500) flushModelOutput();
          return;
        }
        flushModelOutput();
        const persistedEvent = store.appendEvent(taskId2, event.type, event.summary, event.details);
        if (persistedEvent) {
          heartbeat.last_event_seq = persistedEvent.seq;
          heartbeat.last_event_type = event.type;
        }
        const sessionId = event.type === "session_ready" ? event.details?.["session_id"] : void 0;
        if (typeof sessionId === "string") {
          heartbeat.session_id = sessionId;
          correlation.session_id = sessionId;
          modelProfile.session_id = sessionId;
          store.writeStatus(taskId2, { zcode_session_id: sessionId }, attempt);
        }
        if (event.type === "turn_started") {
          correlation.rpc_accepted_at = correlation.rpc_accepted_at ?? now().toISOString();
          correlation.turn_started_at = now().toISOString();
          if (typeof event.details?.["turn_id"] === "string") {
            heartbeat.turn_id = event.details["turn_id"];
            correlation.turn_id = event.details["turn_id"];
            modelProfile.turn_id = event.details["turn_id"];
          }
          activityPhase = "executing";
          writePhase();
        }
        if (event.type === "turn_completed") {
          correlation.turn_completed_at = now().toISOString();
          activityPhase = "finalizing";
          writePhase();
        }
        if (event.type === "model_selected") {
          if (typeof event.details?.["provider_id"] === "string") modelProfile.provider_id = event.details["provider_id"];
          if (typeof event.details?.["model_id"] === "string") modelProfile.model_id = event.details["model_id"];
          if (typeof event.details?.["selected_model"] === "string" && modelProfile.model_id === null) {
            modelProfile.model_id = event.details["selected_model"];
          }
          if (typeof event.details?.["reasoning_level"] === "string") {
            modelProfile.effective_reasoning_level = event.details["reasoning_level"];
            modelProfile.effective_reasoning_level_source = "runtime";
          }
          if (typeof event.details?.["model_source"] === "string") modelProfile.selection_source = event.details["model_source"];
          modelProfile.effective_at = now().toISOString();
        }
        if (typeof event.details?.["event_seq"] === "number") heartbeat.zcode_event_seq = event.details["event_seq"];
        if (event.type === "app_server_started" && typeof event.details?.["pid"] === "number") {
          store.writeStatus(taskId2, { zcode_pid: event.details["pid"] }, attempt);
          void probe.identityOf(event.details["pid"]).then(
            (identity) => {
              store.writeExecutorIdentity(taskId2, attempt, { runtime: identity });
              observationRevision += 1;
              try {
                store.writeWorkerObservation(taskId2, attempt, process.pid, { runtime_identity: identity }, observationRevision, now().toISOString());
              } catch {
              }
            },
            () => void 0
          );
        }
      },
      onInteractionState: (state) => {
        activityPhase = state === "waiting" ? "waiting_for_permission" : "executing";
        writePhase();
      },
      onOutcomeCheckpoint: (checkpoint) => {
        store.writeAttemptMeta(taskId2, attempt, "outcome-checkpoint.json", {
          recorded_at: now().toISOString(),
          exit_code: checkpoint.exitCode,
          signal: checkpoint.signal,
          session_id: checkpoint.sessionId,
          response: checkpoint.response,
          usage: checkpoint.usage,
          error_code: checkpoint.errorCode,
          report_error: checkpoint.reportError,
          agent_report: checkpoint.agentReport,
          report_candidate: checkpoint.reportCandidate,
          cleanup_error: checkpoint.cleanupError ?? null,
          cleanup_verified: checkpoint.cleanupVerified === true,
          usage_normalized: normalizeUsage(checkpoint.usage, { source: "zcode_runtime_turn", scope: checkpoint.sessionId ? `session:${checkpoint.sessionId}` : null, observedAt: now().toISOString() }),
          model_profile: modelProfile
        });
      },
      resolveInteraction: async (request, signal) => {
        store.assertWorkerAttempt(taskId2, attempt);
        const safeRequest = sanitizeInteractionRequest({ ...request, request_id: `${attempt}:${request.request_id}` });
        const { record, created } = store.writeInteractionRequest(taskId2, safeRequest, now().toISOString());
        activityPhase = request.method === "interaction/requestPermission" ? "waiting_for_permission" : "waiting_for_user";
        writePhase();
        if (created) {
          const interactionEvent = store.appendEvent(
            taskId2,
            "interaction_requested",
            interactionSummary(safeRequest),
            { ...publicInteractionDetails(safeRequest) },
            record.created_at
          );
          if (!interactionEvent) {
            const fallback = interactionDecline2(request.method, "Bridge could not publish this request to the calling host");
            store.answerInteractionRequest(taskId2, safeRequest.request_id, fallback, now().toISOString());
            activityPhase = "executing";
            writePhase();
            return fallback;
          }
        }
        let answer = null;
        while (!signal.aborted) {
          store.assertWorkerAttempt(taskId2, attempt);
          const current = store.readInteractionRequest(taskId2, safeRequest.request_id);
          if (current?.state === "answered" && current.answer) {
            answer = current.answer;
            break;
          }
          await sleep2(250);
        }
        activityPhase = "executing";
        writePhase();
        if (answer) return answer;
        return interactionDecline2(request.method, "The task attempt ended");
      }
    });
    const workspaceRef = store.readWorkspaceRef(taskId2) ?? {
      requestedPath: task.workspace,
      canonicalPath: task.worktree_path ?? task.workspace,
      mode: task.worktree_path ? "worktree" : "direct",
      ...task.worktree_path ? { sourcePath: task.workspace } : {}
    };
    const handle = continueSpec ? await adapter.continueTask({
      task,
      workspace: workspaceRef,
      attempt,
      feedback: continueSpec.feedback,
      additionalRequirements: [...continueSpec.additional_requirements ?? []],
      previousSessionId: continueSpec.previous_session_id,
      previousResult
    }) : await adapter.startTask({ task, workspace: workspaceRef, attempt });
    let cancelTimer;
    const cancellation = new Promise((_resolve, reject) => {
      cancelTimer = setInterval(() => {
        try {
          const current = store.readStatus(taskId2);
          if (current.attempt !== attempt || !current.cancel_requested) return;
          clearInterval(cancelTimer);
          void adapter.cancelTask(handle).catch(reject);
        } catch (error) {
          clearInterval(cancelTimer);
          reject(error);
        }
      }, 50);
    });
    try {
      outcome = await Promise.race([adapter.getResult(handle), cancellation]);
    } finally {
      clearInterval(cancelTimer);
    }
    if (outcome.cleanupError) failure = { code: "cleanup_failed", message: `ZCode returned a turn result, but process cleanup could not be verified: ${outcome.cleanupError}` };
    flushModelOutput();
  } catch (error) {
    flushModelOutput();
    failure = {
      code: error instanceof BridgeError ? error.code : "worker_error",
      message: error instanceof Error ? error.message : String(error)
    };
  }
  clearInterval(heartbeatTimer);
  clearInterval(persistCorrelationTimer);
  activityPhase = "finalizing";
  writePhase();
  const finishedAt = now().toISOString();
  store.assertWorkerAttempt(taskId2, attempt);
  const stdoutLog = store.appendLog(taskId2, "stdout", outcome?.stdout ? `${outcome.stdout}
` : "");
  const stderrLog = store.appendLog(
    taskId2,
    "stderr",
    outcome?.stderr ? `${outcome.stderr}
` : failure ? `${failure.code}: ${failure.message}
` : ""
  );
  if (modelProfile.model_id === null && outcome?.modelProfile?.model_id) {
    Object.assign(modelProfile, outcome.modelProfile);
  }
  correlation.rpc_accepted_at = correlation.rpc_accepted_at ?? outcome?.phaseTimestamps?.rpc_accepted_at ?? null;
  correlation.turn_started_at = correlation.turn_started_at ?? outcome?.phaseTimestamps?.turn_started_at ?? null;
  correlation.turn_completed_at = correlation.turn_completed_at ?? outcome?.phaseTimestamps?.turn_completed_at ?? null;
  if (modelProfile.turn_id === null && correlation.turn_id) modelProfile.turn_id = correlation.turn_id;
  const timingNotes = [];
  const timing = {
    queued_ms: phaseDuration(initialStatus.created_at, startedAt, timingNotes),
    execution_ms: phaseDuration(startedAt, finishedAt, timingNotes),
    turn_ms: phaseDuration(correlation.turn_started_at, correlation.turn_completed_at, timingNotes),
    finalize_ms: phaseDuration(correlation.turn_completed_at, finishedAt, timingNotes),
    wall_ms: phaseDuration(startedAt, finishedAt, timingNotes),
    derived: false,
    notes: timingNotes
  };
  const usage = normalizeUsage(outcome?.usage ?? null, {
    source: "zcode_runtime_turn",
    scope: outcome?.sessionId ? `session:${outcome.sessionId}` : null,
    observedAt: finishedAt
  });
  persistCorrelation();
  store.writeAttemptMeta(taskId2, attempt, "outcome.json", {
    started_at: startedAt,
    finished_at: finishedAt,
    failure,
    outcome: outcome ? {
      exitCode: outcome.exitCode,
      signal: outcome.signal,
      sessionId: outcome.sessionId,
      response: outcome.response,
      usage: outcome.usage,
      timedOut: outcome.timedOut,
      cancelled: outcome.cancelled,
      attempts: outcome.attempts,
      errorCode: outcome.errorCode,
      reportError: outcome.reportError,
      stdoutTruncated: outcome.stdoutTruncated,
      stderrTruncated: outcome.stderrTruncated,
      agentReport: outcome.agentReport,
      reportCandidate: outcome.reportCandidate,
      cleanupError: outcome.cleanupError ?? null,
      cleanupVerified: outcome.cleanupVerified === true
    } : null,
    usage_normalized: usage,
    model_profile: modelProfile,
    timing,
    correlation: { ...correlation },
    logs: { stdout_truncated: stdoutLog.truncated, stderr_truncated: stderrLog.truncated }
  });
  const result = buildTaskResult({
    task,
    attempt,
    startedAt,
    finishedAt,
    outcome,
    failure,
    cancelled: outcome?.cancelled === true || failure?.code === "cancelled",
    sessionId: store.readStatus(taskId2).zcode_session_id ?? continueSpec?.previous_session_id,
    usage,
    model: modelProfile,
    timing
  });
  store.appendEvent(taskId2, "task_finished", `Task reached terminal status: ${result.status}`, {
    status: result.status,
    needs_master_decision: result.needs_master_decision
  }, finishedAt);
  store.commitWorkerResult(taskId2, attempt, result, {
    status: result.status,
    finished_at: finishedAt,
    exit_code: result.exit_code,
    zcode_session_id: result.session_id,
    error_code: result.error_code ?? null,
    error: result.status === "failed" ? result.summary : null,
    worker_pid: null,
    cleanup_unverified: failure?.code === "cleanup_failed",
    zcode_pid: failure?.code === "cleanup_failed" ? store.readStatus(taskId2).zcode_pid : null
  });
  return { status: result.status, result };
}
function interactionSummary(request) {
  const params = request.params;
  if (request.method === "interaction/requestPermission") {
    const toolName = typeof params.toolName === "string" ? params.toolName : "tool";
    const reason = typeof params.reason === "string" ? `: ${params.reason}` : "";
    return `ZCode is waiting for the calling host to decide whether ${toolName} may proceed${reason}`;
  }
  if (asRecord3(params.schema).interaction === "plan_approval") {
    return "ZCode is waiting for the calling host to approve or reject its plan";
  }
  return "ZCode is waiting for the calling host to answer a question";
}
function publicInteractionDetails(request) {
  const params = request.params;
  const details = {
    request_id: request.request_id,
    method: request.method,
    ...typeof params.sessionId === "string" ? { session_id: params.sessionId } : {},
    ...typeof params.toolCallId === "string" ? { tool_call_id: params.toolCallId } : {}
  };
  for (const key of ["toolName", "reason", "input", "options", "schema", "questions"]) {
    if (params[key] !== void 0) details[key] = params[key];
  }
  if (details["questions"] === void 0 && Array.isArray(asRecord3(params.input).questions)) {
    details["questions"] = asRecord3(params.input).questions;
  }
  return details;
}
function sanitizeInteractionRequest(request) {
  const params = {};
  for (const key of ["sessionId", "toolCallId", "toolName", "reason", "input", "options", "schema", "questions"]) {
    if (request.params[key] !== void 0) params[key] = request.params[key];
  }
  if (params["questions"] === void 0 && Array.isArray(asRecord3(params["input"]).questions)) {
    params["questions"] = asRecord3(params["input"]).questions;
  }
  return { request_id: request.request_id, method: request.method, params };
}
function interactionDecline2(method, reason) {
  return method === "interaction/requestPermission" ? { decision: "deny", reason } : { action: "decline" };
}
function asRecord3(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value : {};
}
function sleep2(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// src/worker/worker-main.ts
var [dataRoot, taskId, attemptText] = process.argv.slice(2);
if (!dataRoot || !taskId || !attemptText || !/^[1-9]\d*$/u.test(attemptText) || !Number.isSafeInteger(Number(attemptText))) {
  console.error("usage: node worker-main.js <dataRoot> <taskId> <attempt>");
  process.exit(2);
}
try {
  const hostText = process.env["ZCODE_BRIDGE_HOST_PROFILE"];
  const host = hostText ? validateHostProfile(JSON.parse(hostText)) : void 0;
  const { status } = await runWorkerTask({ dataRoot, taskId, host, attempt: Number(attemptText) });
  process.exitCode = 0;
  void status;
} catch (error) {
  console.error(error instanceof Error ? error.stack ?? error.message : String(error));
  process.exitCode = 1;
}
