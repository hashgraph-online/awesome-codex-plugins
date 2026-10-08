#!/usr/bin/env node

import {
  accessSync,
  appendFileSync,
  closeSync,
  constants as fsConstants,
  fstatSync,
  lstatSync,
  mkdirSync,
  mkdtempSync,
  openSync,
  readFileSync,
  realpathSync,
  renameSync,
  rmdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { spawn } from "node:child_process";
import { createHash, randomBytes, randomUUID } from "node:crypto";
import { createServer } from "node:http";
import { isAbsolute, normalize, parse, resolve, sep } from "node:path";
import { createInterface } from "node:readline";
import { fileURLToPath } from "node:url";

export const MANAGEMENT_API_URL = "https://cohesivity.ai/api/";
export const REMOTE_MCP_URL = "https://cohesivity.ai/mcp";
const RETIRED_REMOTE_MCP_URL = "https://cohesivity.ai/mcp/manage";
export const QUICKSTART_URL = "https://cohesivity.ai/quickstart.sh";

export const RESOURCE_NAMES = Object.freeze([
  "openweather-api",
  "google-geocoding-api",
  "openai-api",
  "ai-gateway",
  "deepgram-api",
  "exa-api",
  "steel-browser",
  "inbox",
  "postgres",
  "redis",
  "object-storage",
  "vector-database",
  "railway-hosting",
  "cloudflare-workers",
  "social-login",
  "realtime",
]);

const SERVER_NAME = "cohesivity-project-bootstrap";
export const SERVER_VERSION = "5.0.3";
const SERVER_INSTRUCTIONS =
  "Cohesivity provisions managed backend resources and third-party APIs for the app in project_root, all under one tenant. " +
  "Call order: if project_root has no .cohesivity file, call create_tenant first; it writes .cohesivity and every other tool reads it. " +
  "Then call provision_resource for what the app needs, after fetching that offering's live documentation. " +
  "tenant_status reads the current tenant, claim_tenant hands an ephemeral tenant to the user's account, and give_feedback reports problems. " +
  "create_tenant, provision_resource, and claim_tenant change real state, so pass confirmed: true only when the user explicitly approved that action.";
const MAX_PROJECT_ROOT_LENGTH = 4096;
const MAX_CREDENTIAL_FILE_BYTES = 128 * 1024;
const MAX_GITIGNORE_BYTES = 1024 * 1024;
const MAX_RESPONSE_BYTES = 2 * 1024 * 1024;
const MAX_FEEDBACK_LENGTH = 20_000;
const USER_AGENT = `${SERVER_NAME}/${SERVER_VERSION}`;
const SECRET_DETECT = /(?:coh_(?:man|app)_[a-z0-9]+|mcp_(?:at|rt)_[A-Za-z0-9_-]+|Bearer\s+[^\s"']+)/i;
const MANAGEMENT_OUTPUT_FIELDS = Object.freeze({
  claim: ["approval_url"],
  status: ["account", "resources", "bucket_usage", "account_bucket_usage", "notifications"],
  provision: [
    "success",
    "resource",
    "resource_name",
    "status",
    "created",
    "base_url",
    "endpoint",
    "edge_url",
    "deployment_url",
    "deploy_endpoint",
    "compute_limits",
    "region",
    "primary_region",
    "database_primary_region",
    "quota_profile",
    "already_provisioned",
    "login_url",
    "callback_urls",
    "events_table",
    "events_endpoint",
    "dimensions",
    "metric",
    "project_name",
    "vercel_url",
    "custom_domain",
    "custom_domain_status",
    "vanity",
    "docs_url",
    "address",
    "canonical_address",
    "vanity_address",
    "retention_days",
    "max_message_bytes",
    "max_recipients",
    "storage_limit_bytes",
    "postgres",
    "sessions_url",
    "tools_url",
    "session_limits",
    "admission",
    "message",
    "next_steps",
    "results",
    "resources",
  ],
});

const jsonObjectSchema = {
  type: "object",
  additionalProperties: true,
};

const projectRootProperty = {
  type: "string",
  minLength: 1,
  maxLength: MAX_PROJECT_ROOT_LENGTH,
  description: "Absolute path to the project root holding the .cohesivity file that create_tenant wrote.",
};

const createTenantProjectRootProperty = {
  ...projectRootProperty,
  description: "Absolute path to an existing project directory. create_tenant writes .cohesivity here, or reuses the one already there.",
};

const confirmedProperty = {
  type: "boolean",
  enum: [true],
  description:
    "Set to true only when the current user request explicitly authorized this exact mutation.",
};

const requiresUserInteraction = {
  "anthropic/requiresUserInteraction": true,
};

const noConfigurationResources = RESOURCE_NAMES.filter(
  (name) => !["inbox", "postgres", "realtime", "social-login", "vector-database"].includes(name),
);
const POSTGRES_REGIONS = Object.freeze([
  "apac",
  "aws-us-east-1",
  "aws-us-east-2",
  "aws-us-west-2",
  "aws-eu-central-1",
  "aws-eu-west-2",
  "aws-ap-southeast-1",
  "aws-ap-southeast-2",
  "aws-sa-east-1",
]);
const REALTIME_REGIONS = Object.freeze(["wnam", "enam", "weur", "eeur", "apac", "oc"]);

const inboxConfigurationSchema = {
  type: "object",
  properties: {
    webhook_url: { type: "string", minLength: 1, maxLength: 2048 },
  },
  additionalProperties: false,
};

const postgresConfigurationSchema = {
  type: "object",
  properties: {
    region: { enum: POSTGRES_REGIONS },
  },
  additionalProperties: false,
};

const realtimeConfigurationSchema = {
  type: "object",
  properties: {
    write_region: { enum: REALTIME_REGIONS },
  },
  additionalProperties: false,
};

const socialLoginConfigurationSchema = {
  type: "object",
  properties: {
    callback_urls: {
      type: "array",
      minItems: 1,
      maxItems: 50,
      uniqueItems: true,
      items: { type: "string", minLength: 1, maxLength: 2048 },
    },
  },
  required: ["callback_urls"],
  additionalProperties: false,
};

const vectorConfigurationSchema = {
  type: "object",
  properties: {
    dimensions: { enum: [384, 768, 1024, 1536, 3072] },
    metric: { enum: ["cosine", "euclidean", "dotproduct"] },
  },
  required: ["dimensions"],
  additionalProperties: false,
};

const bulkConfigurationsSchema = {
  type: "object",
  properties: {
    postgres: postgresConfigurationSchema,
    inbox: inboxConfigurationSchema,
    realtime: realtimeConfigurationSchema,
    "social-login": socialLoginConfigurationSchema,
    "vector-database": vectorConfigurationSchema,
  },
  additionalProperties: false,
};

const provisionInputSchema = {
  type: "object",
  oneOf: [
    {
      type: "object",
      properties: {
        project_root: projectRootProperty,
        resource: { enum: noConfigurationResources },
        confirmed: confirmedProperty,
      },
      required: ["project_root", "resource", "confirmed"],
      additionalProperties: false,
    },
    ...[
      ["postgres", postgresConfigurationSchema],
      ["inbox", inboxConfigurationSchema],
      ["realtime", realtimeConfigurationSchema],
      ["social-login", socialLoginConfigurationSchema],
      ["vector-database", vectorConfigurationSchema],
    ].map(([resource, configuration]) => ({
      type: "object",
      properties: {
        project_root: projectRootProperty,
        resource: { const: resource },
        configuration,
        confirmed: confirmedProperty,
      },
      required:
        resource === "social-login" || resource === "vector-database"
          ? ["project_root", "resource", "configuration", "confirmed"]
          : ["project_root", "resource", "confirmed"],
      additionalProperties: false,
    })),
    {
      type: "object",
      properties: {
        project_root: projectRootProperty,
        resources: {
          type: "array",
          minItems: 1,
          maxItems: RESOURCE_NAMES.length,
          uniqueItems: true,
          items: { enum: RESOURCE_NAMES },
        },
        configurations: bulkConfigurationsSchema,
        confirmed: confirmedProperty,
      },
      required: ["project_root", "resources", "confirmed"],
      additionalProperties: false,
    },
  ],
};

const DOCUMENTATION_TOOL = Object.freeze({
  name: "get_cohesivity_documentation",
  title: "Get Cohesivity documentation",
  description:
    "Read a current Cohesivity overview, reference, onboarding guide, pricing guide, offerings catalog, or individual offering document.",
  inputSchema: {
    type: "object",
    required: ["document"],
    properties: {
      document: {
        type: "string",
        enum: ["docs", "quick-reference", "full-reference", "onboarding", "pricing", "offerings", "offering"],
      },
      offering: {
        type: "string",
        minLength: 1,
        maxLength: 64,
        pattern: "^[a-z0-9][a-z0-9-]*$",
        description: 'Offering slug. Required only when document is "offering".',
      },
    },
    additionalProperties: false,
  },
  annotations: {
    readOnlyHint: true,
    destructiveHint: false,
    idempotentHint: true,
    openWorldHint: false,
  },
});
const DOCUMENT_PATHS = Object.freeze({
  docs: "docs",
  "quick-reference": "llms.txt",
  "full-reference": "llms-full.txt",
  onboarding: "onboarding",
  pricing: "pricing",
  offerings: "offerings",
});

export const TOOLS = Object.freeze([
  {
    name: "create_tenant",
    title: "Create or reuse a Cohesivity project tenant",
    description:
      "Cohesivity gives an app managed backend resources and third-party APIs (Postgres, Redis, object storage, social login, realtime, AI and data APIs) through one tenant with one set of credentials. Call this first in any project that has no .cohesivity file; every other Cohesivity tool needs the tenant it creates. Runs the full Cohesivity quickstart in the supplied project: creates or reuses credentials, installs detected client integrations and guidance, and returns only non-secret metadata. Optional local CLI login creates an account-owned tenant without claiming; otherwise creates an ephemeral tenant. Requires explicit approval for all quickstart effects.",
    inputSchema: {
      type: "object",
      properties: { project_root: createTenantProjectRootProperty, confirmed: confirmedProperty },
      required: ["project_root", "confirmed"],
      additionalProperties: false,
    },
    outputSchema: {
      type: "object",
      properties: {
        tenant_id: { type: "string" },
        expires_at: { type: "string" },
        tenant_lifecycle: { enum: ["ephemeral", "claimed"] },
        runtime_profile: { type: "string" },
      },
      required: ["tenant_id"],
      additionalProperties: false,
    },
    _meta: requiresUserInteraction,
  },
  {
    name: "claim_tenant",
    title: "Create a tenant claim approval URL",
    description:
      "Starts the Cohesivity claim handoff using the project credential internally. Claiming is a consent gate; call only after explicit user approval.",
    inputSchema: {
      type: "object",
      properties: { project_root: projectRootProperty, confirmed: confirmedProperty },
      required: ["project_root", "confirmed"],
      additionalProperties: false,
    },
    outputSchema: {
      type: "object",
      properties: {
        tenant_id: { type: "string" },
        approval_url: { type: "string" },
      },
      required: ["tenant_id", "approval_url"],
      additionalProperties: false,
    },
    _meta: requiresUserInteraction,
  },
  {
    name: "tenant_status",
    title: "Read Cohesivity tenant status",
    description:
      "Reads current tenant status from the Cohesivity Management API using the project credential internally and redacts the response.",
    inputSchema: {
      type: "object",
      properties: { project_root: projectRootProperty },
      required: ["project_root"],
      additionalProperties: false,
    },
    outputSchema: {
      type: "object",
      properties: {
        tenant_id: { type: "string" },
        status: jsonObjectSchema,
      },
      required: ["tenant_id", "status"],
      additionalProperties: false,
    },
  },
  {
    name: "provision_resource",
    title: "Provision Cohesivity resources",
    description:
      "Provisions one resource with resource/configuration, or several with resources/configurations. Requires an existing tenant: if project_root has no .cohesivity file, call create_tenant first. Fetch every requested offering's live documentation and obtain any required user consent before calling.",
    inputSchema: provisionInputSchema,
    _meta: requiresUserInteraction,
    outputSchema: {
      type: "object",
      properties: {
        resource: { enum: RESOURCE_NAMES },
        resources: {
          type: "array",
          items: { enum: RESOURCE_NAMES },
        },
        result: jsonObjectSchema,
      },
      required: ["result"],
      oneOf: [
        { required: ["resource"] },
        { required: ["resources"] },
      ],
      additionalProperties: false,
    },
  },
  {
    name: "give_feedback",
    title: "Submit Cohesivity feedback",
    description:
      "Submit feedback on Cohesivity and its services anytime; no user confirmation is needed. Exclude personal information and secrets.",
    inputSchema: {
      type: "object",
      properties: {
        project_root: projectRootProperty,
        feedback: { type: "string", minLength: 1, maxLength: MAX_FEEDBACK_LENGTH, pattern: "\\S" },
      },
      required: ["project_root", "feedback"],
      additionalProperties: false,
    },
    outputSchema: {
      type: "object",
      properties: { success: { type: "boolean", enum: [true] } },
      required: ["success"],
      additionalProperties: false,
    },
    annotations: {
      readOnlyHint: false,
      destructiveHint: false,
      idempotentHint: false,
      openWorldHint: true,
    },
  },
  DOCUMENTATION_TOOL,
]);

class SafeError extends Error {
  constructor(message, code = "tool_call_failed", httpStatus = undefined) {
    super(message);
    this.code = code;
    this.httpStatus = httpStatus;
  }
}

const isRecord = (value) =>
  value !== null && typeof value === "object" && !Array.isArray(value);

function fail(message, code, httpStatus) {
  throw new SafeError(message, code, httpStatus);
}

function exactObject(value, required, optional = []) {
  if (!isRecord(value)) fail("Arguments must be an object.");
  const allowed = new Set([...required, ...optional]);
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) fail(`Unexpected argument: ${key}.`);
  }
  for (const key of required) {
    if (!(key in value)) fail(`Missing required argument: ${key}.`);
  }
  return value;
}

export function validateProjectRoot(value, workspaceRoot = process.env.CLAUDE_PROJECT_DIR) {
  if (typeof value !== "string" || value.length === 0) {
    fail("project_root must be a non-empty absolute path.");
  }
  if (value.length > MAX_PROJECT_ROOT_LENGTH || value.includes("\0") || !isAbsolute(value)) {
    fail("project_root must be a valid absolute path.");
  }
  if (value.split(/[\\/]+/u).includes("..")) {
    fail("project_root must not contain parent-directory traversal.");
  }

  const normalized = normalize(value);
  let canonical;
  try {
    canonical = realpathSync.native(normalized);
    if (!statSync(canonical).isDirectory()) fail("project_root must name a directory.");
    if (parse(canonical).root === canonical) fail("project_root must not be the filesystem root.");
    accessSync(canonical, fsConstants.R_OK | fsConstants.W_OK | fsConstants.X_OK);
  } catch (error) {
    if (error instanceof SafeError) throw error;
    fail("project_root must be an existing, accessible directory.");
  }
  if (workspaceRoot !== undefined && workspaceRoot !== "") {
    let workspace;
    try {
      workspace = realpathSync.native(workspaceRoot);
      if (!statSync(workspace).isDirectory()) fail("The configured workspace root must name a directory.");
    } catch (error) {
      if (error instanceof SafeError) throw error;
      fail("The configured workspace root is invalid.");
    }
    if (canonical !== workspace) {
      fail("project_root must match the current Claude Code project directory.");
    }
  }
  return canonical.endsWith(sep) ? canonical.slice(0, -1) : canonical;
}

function credentialPath(projectRoot) {
  const path = resolve(projectRoot, ".cohesivity");
  if (path !== `${projectRoot}${sep}.cohesivity`) fail("Invalid credential file path.");
  return path;
}

function gitignorePath(projectRoot) {
  const path = resolve(projectRoot, ".gitignore");
  if (path !== `${projectRoot}${sep}.gitignore`) fail("Invalid gitignore path.");
  return path;
}

function readRegularFile(path, label, missingMessage, oversizedMessage, maxBytes, privateFile = false) {
  let descriptor;
  try {
    const initial = lstatSync(path);
    if (initial.isSymbolicLink() || !initial.isFile()) fail(`${label} must be a regular file.`);
    if (initial.size > maxBytes) fail(oversizedMessage);
    descriptor = openSync(
      path,
      fsConstants.O_RDONLY |
        (fsConstants.O_NONBLOCK ?? 0) |
        (fsConstants.O_NOFOLLOW ?? 0),
    );
    const opened = fstatSync(descriptor);
    const current = lstatSync(path);
    if (
      current.isSymbolicLink() ||
      !opened.isFile() ||
      !current.isFile() ||
      opened.dev !== current.dev ||
      opened.ino !== current.ino
    ) {
      fail(`${label} must be a regular file.`);
    }
    if (opened.size > maxBytes) fail(oversizedMessage);
    if (privateFile && ((opened.mode & 0o077) !== 0 || opened.nlink !== 1 || (process.getuid && opened.uid !== process.getuid()))) {
      fail(`${label} must be privately owned with no group or other permissions.`);
    }
    return readFileSync(descriptor, "utf8");
  } catch (error) {
    if (error instanceof SafeError) throw error;
    fail(missingMessage);
  } finally {
    if (descriptor !== undefined) closeSync(descriptor);
  }
}

function ensureCredentialIgnored(projectRoot) {
  const path = gitignorePath(projectRoot);
  let status;
  try {
    status = lstatSync(path);
  } catch (error) {
    if (error?.code !== "ENOENT") fail("Could not validate .gitignore in project_root.");
    try {
      writeFileSync(path, ".cohesivity\n", { encoding: "utf8", flag: "wx", mode: 0o600 });
      return;
    } catch {
      fail("Could not create .gitignore safely in project_root.");
    }
  }
  if (status.isSymbolicLink() || !status.isFile()) fail(".gitignore must be a regular file.");
  const contents = readRegularFile(
    path,
    ".gitignore",
    "No readable .gitignore file exists in project_root.",
    ".gitignore is unexpectedly large.",
    MAX_GITIGNORE_BYTES,
  );
  const lastEffectiveRule = contents
    .split(/\r?\n/u)
    .filter((line) => line.length > 0 && !line.startsWith("#"))
    .at(-1);
  if (lastEffectiveRule === ".cohesivity") return;

  let descriptor;
  try {
    descriptor = openSync(
      path,
      fsConstants.O_WRONLY |
        fsConstants.O_APPEND |
        (fsConstants.O_NONBLOCK ?? 0) |
        (fsConstants.O_NOFOLLOW ?? 0),
    );
    const opened = fstatSync(descriptor);
    const current = lstatSync(path);
    if (
      current.isSymbolicLink() ||
      !opened.isFile() ||
      !current.isFile() ||
      opened.dev !== current.dev ||
      opened.ino !== current.ino
    ) {
      fail(".gitignore must be a regular file.");
    }
    if (opened.size > MAX_GITIGNORE_BYTES) fail(".gitignore is unexpectedly large.");
    appendFileSync(descriptor, `${contents.length > 0 && !contents.endsWith("\n") ? "\n" : ""}.cohesivity\n`, "utf8");
  } catch (error) {
    if (error instanceof SafeError) throw error;
    fail("Could not update .gitignore safely in project_root.");
  } finally {
    if (descriptor !== undefined) closeSync(descriptor);
  }
}

function readCredentialFields(projectRoot, requireManagementKey = false) {
  const path = credentialPath(projectRoot);
  let contents;
  try {
    contents = readRegularFile(
      path,
      ".cohesivity",
      "No readable .cohesivity file exists in project_root.",
      ".cohesivity is unexpectedly large.",
      MAX_CREDENTIAL_FILE_BYTES,
    );
  } catch (error) {
    if (error instanceof SafeError) error.code = "tenant_not_available";
    throw error;
  }

  const fields = Object.create(null);
  const allowedFields = new Set([
    "tenant_id",
    "expires_at",
    "tenant_lifecycle",
    "runtime_profile",
    ...(requireManagementKey ? ["coh_management_key"] : []),
  ]);
  for (const line of contents.split(/\r?\n/u)) {
    const match = /^([A-Za-z][A-Za-z0-9_]*)=(.*)$/u.exec(line);
    if (match && allowedFields.has(match[1]) && fields[match[1]] === undefined) {
      fields[match[1]] = match[2].trim();
    }
  }

  if (!/^[a-z0-9]+(?:-[a-z0-9]+)+$/u.test(fields.tenant_id ?? "")) {
    fail(".cohesivity does not contain a valid tenant_id.", "tenant_not_available");
  }
  if (
    requireManagementKey &&
    !/^coh_man_[a-z0-9]{20}$/u.test(fields.coh_management_key ?? "")
  ) {
    fail(".cohesivity does not contain a valid management credential.", "tenant_not_available");
  }
  return fields;
}

function safeTenantMetadata(projectRoot) {
  const fields = readCredentialFields(projectRoot);
  const metadata = { tenant_id: fields.tenant_id };
  if (fields.expires_at) {
    const timestamp = Date.parse(fields.expires_at);
    if (Number.isFinite(timestamp)) metadata.expires_at = new Date(timestamp).toISOString();
  }
  if (["ephemeral", "claimed"].includes(fields.tenant_lifecycle)) {
    metadata.tenant_lifecycle = fields.tenant_lifecycle;
  }
  if (/^[A-Za-z0-9._-]{1,100}$/u.test(fields.runtime_profile ?? "")) {
    metadata.runtime_profile = fields.runtime_profile;
  }
  return metadata;
}

export function secureEnvironment(environment = process.env) {
  const result = {};
  for (const name of ["HOME", "PATH", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "CODEX_HOME", "HERMES_HOME"]) {
    const value = environment[name];
    if (typeof value === "string" && value.length && !/[\0\r\n]/u.test(value)) result[name] = value;
  }
  result.PATH ??= "/usr/local/bin:/usr/bin:/bin";
  return result;
}

function privateStatus(path, directory = false) {
  const status = lstatSync(path);
  if (status.isSymbolicLink() || (directory ? !status.isDirectory() : !status.isFile()) ||
      (status.mode & (directory ? 0o022 : 0o077)) !== 0 || (!directory && status.nlink !== 1) ||
      (process.getuid && status.uid !== process.getuid())) {
    fail("Local Cohesivity state must be privately owned, non-symlink files and directories.");
  }
  return status;
}

function authDirectory(environment) {
  if (process.platform === "win32") fail("Local account authentication requires a POSIX filesystem.");
  const home = environment.HOME;
  const base = environment.XDG_CONFIG_HOME || (home && resolve(home, ".config"));
  if (!base || !isAbsolute(base) || (home && !isAbsolute(home))) fail("Set an absolute HOME or XDG_CONFIG_HOME for local Cohesivity authentication.");
  const directory = resolve(base, "cohesivity");
  let cursor = parse(directory).root;
  for (const part of directory.slice(cursor.length).split(sep)) {
    cursor = resolve(cursor, part);
    try {
      const status = lstatSync(cursor);
      if (status.isSymbolicLink() || !status.isDirectory()) fail("Local Cohesivity state paths must not contain symlinks.");
    } catch (error) {
      if (error?.code !== "ENOENT") throw error;
      try { mkdirSync(cursor, { mode: 0o700 }); } catch (mkdirError) { if (mkdirError?.code !== "EEXIST") throw mkdirError; }
      const status = lstatSync(cursor);
      if (status.isSymbolicLink() || !status.isDirectory()) fail("Local Cohesivity state paths must not contain symlinks.");
    }
  }
  privateStatus(directory, true);
  return directory;
}

function privateRead(path) {
  privateStatus(path);
  return readRegularFile(path, "Local Cohesivity state", "Could not read local Cohesivity state.", "Local Cohesivity state is unexpectedly large.", 64 * 1024, true);
}

async function withStateLock(directory, name, action, waitMs = 35_000) {
  const path = resolve(directory, name);
  const deadline = Date.now() + waitMs;
  while (true) {
    try { mkdirSync(path, { mode: 0o700 }); break; } catch (error) {
      if (error?.code !== "EEXIST") throw error;
      try { privateStatus(path, true); } catch (statusError) { if (statusError?.code === "ENOENT") continue; throw statusError; }
      if (Date.now() >= deadline) fail(waitMs === 0 ? "A Cohesivity quickstart is already running for this project." : "Local account state is locked by another process. Retry after it finishes.");
      await new Promise((resolvePromise) => setTimeout(resolvePromise, 50));
    }
  }
  const lock = privateStatus(path, true);
  try { return await action(); } finally {
    const current = privateStatus(path, true);
    if (current.dev === lock.dev && current.ino === lock.ino) rmdirSync(path);
  }
}

function writePrivateJson(path, value) {
  try { privateStatus(path); } catch (error) { if (error?.code !== "ENOENT") throw error; }
  const temporary = `${path}.${randomUUID()}.tmp`;
  try {
    writeFileSync(temporary, `${JSON.stringify(value)}\n`, { flag: "wx", mode: 0o600 });
    renameSync(temporary, path);
  } finally {
    rmSync(temporary, { force: true });
  }
}

function validateAccount(value) {
  if (!isRecord(value) || value.principal_type !== "account" || value.token_type !== "Bearer" ||
      !/^mcp_at_[A-Za-z0-9_-]{43}$/u.test(value.access_token ?? "") ||
      !/^mcp_rt_[A-Za-z0-9_-]{43}$/u.test(value.refresh_token ?? "") ||
      !/^[A-Za-z0-9_-]{1,200}$/u.test(value.client_id ?? "") ||
      !Number.isFinite(value.expires_at) || value.expires_at <= 0 ||
      (value.resource !== undefined && typeof value.resource !== "string")) {
    fail("Local account credentials are invalid. Run login again or logout explicitly; guest fallback is disabled.");
  }
  return value;
}

// Saved sign-ins are bound to one OAuth resource. Tokens issued for the retired
// /mcp/manage resource (or saved before the resource was recorded) can no
// longer authorize anything, so they fail closed with a reauthorization hint
// instead of refreshing, falling back to guest, or silently becoming /mcp.
function requireCurrentResource(account) {
  if (account.resource === REMOTE_MCP_URL) return account;
  fail(`Saved Cohesivity account sign-in was issued for the retired ${RETIRED_REMOTE_MCP_URL} endpoint. Run project-bootstrap.mjs logout, then project-bootstrap.mjs login to sign in for ${REMOTE_MCP_URL}. Existing .cohesivity projects keep working without sign-in.`);
}

async function boundedFetch(url, options, fetchImpl, limit = 1024 * 1024) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30_000);
  let reader;
  try {
    const response = await fetchImpl(url, { ...options, redirect: "error", signal: controller.signal });
    if (!response.ok || (response.url && response.url !== String(url)) || response.redirected ||
        Number(response.headers.get("content-length")) > limit) fail("The fixed Cohesivity endpoint returned an invalid or oversized response.");
    reader = response.body?.getReader();
    if (!reader) return "";
    const chunks = [];
    let size = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > limit) fail("The fixed Cohesivity endpoint returned an oversized response.");
      chunks.push(Buffer.from(value));
    }
    return Buffer.concat(chunks).toString("utf8");
  } catch (error) {
    if (error instanceof SafeError) throw error;
    fail("The fixed Cohesivity endpoint request failed.");
  } finally {
    controller.abort();
    if (reader) await reader.cancel().catch(() => {});
    clearTimeout(timer);
  }
}

async function oauthRequest(path, body, fetchImpl, json = false) {
  const text = await boundedFetch(`https://cohesivity.ai/oauth/${path}`, {
    method: "POST",
    headers: { "Content-Type": json ? "application/json" : "application/x-www-form-urlencoded", Accept: "application/json", "User-Agent": USER_AGENT },
    body: json ? JSON.stringify(body) : new URLSearchParams(body),
  }, fetchImpl, 64 * 1024);
  try { return JSON.parse(text); } catch { fail("Cohesivity account authentication returned an invalid response."); }
}

function accountFromResponse(response, clientId) {
  if (!isRecord(response) || !Number.isFinite(response.expires_in) || response.expires_in <= 0 || response.expires_in > 86400) {
    fail("Cohesivity account authentication returned an invalid expiry.");
  }
  if (response.resource !== REMOTE_MCP_URL) fail("Cohesivity account authentication returned an unexpected resource.");
  return validateAccount({ access_token: response.access_token, refresh_token: response.refresh_token, token_type: response.token_type,
    principal_type: response.principal_type, client_id: clientId, resource: response.resource, expires_at: Date.now() + response.expires_in * 1000 });
}

async function loadAccount(environment, fetchImpl) {
  const directory = authDirectory(environment);
  return withStateLock(directory, "mcp-auth.lock", async () => {
    const path = resolve(directory, "mcp-auth.json");
    let contents;
    try { contents = privateRead(path); } catch (error) { if (error?.code === "ENOENT") return undefined; throw error; }
    let account;
    try { account = JSON.parse(contents); } catch { fail("Local account credentials are invalid. Run login again or logout explicitly."); }
    account = requireCurrentResource(validateAccount(account));
    if (account.expires_at > Date.now() + 60_000) return account;
    const response = await oauthRequest("token", { grant_type: "refresh_token", client_id: account.client_id,
      refresh_token: account.refresh_token, resource: REMOTE_MCP_URL }, fetchImpl);
    account = accountFromResponse(response, account.client_id);
    writePrivateJson(path, account);
    return account;
  });
}

export function runQuickstartProcess(script, args, options, dependencies = {}) {
  if (process.platform === "win32") return Promise.reject(new SafeError("Quickstart requires Bash on a POSIX platform."));
  return new Promise((resolvePromise, reject) => {
    let child;
    let timedOut = false;
    let timer;
    try {
      child = (dependencies.spawn ?? spawn)("/bin/bash", ["--noprofile", "--norc", "-s", "--", ...args], {
        ...options, shell: false, detached: true, stdio: ["pipe", "ignore", "ignore"],
      });
      timer = setTimeout(() => {
        timedOut = true;
        try { (dependencies.kill ?? process.kill)(-child.pid, "SIGKILL"); } catch { child.kill?.("SIGKILL"); }
      }, dependencies.timeoutMs ?? 180_000);
      child.on("error", () => { clearTimeout(timer); reject(new SafeError("Could not start the Cohesivity quickstart.")); });
      child.on("close", (code) => {
        clearTimeout(timer);
        if (timedOut || code !== 0) reject(new SafeError("The Cohesivity quickstart failed or timed out; its output was withheld to protect credentials."));
        else resolvePromise();
      });
      child.stdin.on("error", () => {});
      child.stdin.end(script);
    } catch {
      clearTimeout(timer);
      reject(new SafeError("Could not start the Cohesivity quickstart."));
    }
  });
}

function validateProjectCredentials(projectRoot) {
  const path = credentialPath(projectRoot);
  const contents = readRegularFile(path, ".cohesivity", "Could not read .cohesivity.", ".cohesivity is unexpectedly large.", MAX_CREDENTIAL_FILE_BYTES, true);
  readCredentialFields(projectRoot, true);
  if (!/^coh_application_key=coh_app_[a-z0-9]{20}$/mu.test(contents)) fail(".cohesivity does not contain a valid application credential.");
}

async function runProjectQuickstart(projectRoot, dependencies) {
  const environment = dependencies.env ?? process.env;
  const fetchImpl = dependencies.fetch ?? globalThis.fetch;
  return withStateLock(projectRoot, ".cohesivity-bootstrap.lock", async () => {
    let existingProject = false;
    try { lstatSync(credentialPath(projectRoot)); existingProject = true; }
    catch (error) { if (error.code !== "ENOENT") throw error; }
    if (existingProject) validateProjectCredentials(projectRoot);
    const account = existingProject ? null : await loadAccount(environment, fetchImpl);
    const directory = account ? authDirectory(environment) : null;
    const script = await boundedFetch(QUICKSTART_URL, { method: "GET", headers: { Accept: "text/plain", "User-Agent": USER_AGENT } }, fetchImpl);
    if (!script.trim() || script.includes("\0")) fail("The Cohesivity quickstart download is invalid.");
    let temporary;
    try {
      const args = [];
      if (account) {
        if (directory === projectRoot || directory.startsWith(`${projectRoot}${sep}`)) fail("Account state must be outside project_root.");
        const keyPath = resolve(directory, `bootstrap-${createHash("sha256").update(`${account.client_id}\0${projectRoot}`).digest("hex")}.json`);
        let key;
        try { key = JSON.parse(privateRead(keyPath)).idempotency_key; } catch (error) {
          if (error?.code !== "ENOENT") throw error;
          try { writeFileSync(keyPath, JSON.stringify({ idempotency_key: randomUUID() }), { flag: "wx", mode: 0o600 }); } catch (writeError) { if (writeError?.code !== "EEXIST") throw writeError; }
          key = JSON.parse(privateRead(keyPath)).idempotency_key;
        }
        if (!/^[A-Za-z0-9_-]{8,128}$/u.test(key ?? "")) fail("The local bootstrap retry key is invalid.");
        temporary = mkdtempSync(resolve(directory, "bootstrap-auth-"));
        const headerPath = resolve(temporary, "authorization.header");
        writeFileSync(headerPath, `${["Authorization:", "Bearer", account.access_token].join(" ")}\n`, { flag: "wx", mode: 0o600 });
        args.push("--account-auth-file", headerPath, "--idempotency-key", key);
      }
      await (dependencies.runQuickstart ?? runQuickstartProcess)(script, args, { cwd: projectRoot, env: secureEnvironment(environment) });
      validateProjectCredentials(projectRoot);
      ensureCredentialIgnored(projectRoot);
      return safeTenantMetadata(projectRoot);
    } catch (error) {
      if (error instanceof SafeError) throw error;
      fail("The Cohesivity quickstart failed safely; its output was withheld to protect credentials.");
    } finally {
      if (temporary) rmSync(temporary, { recursive: true, force: true });
    }
  }, 0);
}

export function validateOAuthCallback(target, state) {
  const url = new URL(target, "http://127.0.0.1");
  if (url.origin !== "http://127.0.0.1" || url.pathname !== "/callback" || url.searchParams.getAll("state").length !== 1 ||
      url.searchParams.get("state") !== state || url.searchParams.has("error") || url.searchParams.getAll("code").length !== 1 ||
      !/^[A-Za-z0-9_-]{1,2048}$/u.test(url.searchParams.get("code") ?? "")) fail("The account login callback was rejected.");
  return url.searchParams.get("code");
}

async function loopbackCallback(state) {
  let complete;
  let reject;
  const result = new Promise((yes, no) => { complete = yes; reject = no; });
  result.catch(() => {});
  const server = createServer((request, response) => {
    try {
      if (request.method !== "GET" || request.headers.host !== `127.0.0.1:${server.address().port}`) fail("Invalid callback.");
      const code = validateOAuthCallback(request.url, state);
      response.writeHead(200, { "Content-Type": "text/plain", "Cache-Control": "no-store" });
      response.end("Cohesivity authorization received. You can close this tab.");
      complete(code);
    } catch {
      response.writeHead(400, { "Content-Type": "text/plain", "Cache-Control": "no-store" });
      response.end("Invalid Cohesivity authorization callback.");
    }
  });
  await new Promise((yes, no) => { server.once("error", no); server.listen(0, "127.0.0.1", yes); });
  const timer = setTimeout(() => reject(new SafeError("Account login timed out.")), 180_000);
  return {
    redirectUri: `http://127.0.0.1:${server.address().port}/callback`,
    wait: () => result,
    close: () => { clearTimeout(timer); server.close(); server.closeAllConnections?.(); },
  };
}

export async function login(dependencies = {}) {
  const environment = dependencies.env ?? process.env;
  const fetchImpl = dependencies.fetch ?? globalThis.fetch;
  const stderr = dependencies.stderr ?? process.stderr;
  const directory = authDirectory(environment);
  const state = randomBytes(32).toString("base64url");
  const verifier = randomBytes(32).toString("base64url");
  const callback = await (dependencies.callback ?? loopbackCallback)(state);
  try {
    const client = await oauthRequest("register", { client_name: "Cohesivity local project bootstrap", redirect_uris: [callback.redirectUri],
      token_endpoint_auth_method: "none", grant_types: ["authorization_code", "refresh_token"], response_types: ["code"] }, fetchImpl, true);
    if (!/^[A-Za-z0-9_-]{1,200}$/u.test(client?.client_id ?? "")) fail("Cohesivity registration returned an invalid client.");
    const authorize = new URL("https://cohesivity.ai/oauth/authorize");
    authorize.search = new URLSearchParams({ response_type: "code", client_id: client.client_id, redirect_uri: callback.redirectUri,
      scope: "mcp:tenants:create", resource: REMOTE_MCP_URL, state, code_challenge: createHash("sha256").update(verifier).digest("base64url"),
      code_challenge_method: "S256", account_required: "true" }).toString();
    stderr.write(`Open this URL in your browser to sign in to your Cohesivity account:\n${authorize.href}\n`);
    if (dependencies.openBrowser) await dependencies.openBrowser(authorize.href);
    const code = await callback.wait();
    const token = await oauthRequest("token", { grant_type: "authorization_code", client_id: client.client_id, redirect_uri: callback.redirectUri,
      code, code_verifier: verifier, resource: REMOTE_MCP_URL }, fetchImpl);
    const account = accountFromResponse(token, client.client_id);
    await withStateLock(directory, "mcp-auth.lock", () => writePrivateJson(resolve(directory, "mcp-auth.json"), account));
    stderr.write("Cohesivity account sign-in saved. New project tenants will belong to this account.\n");
  } finally { callback.close(); }
}

export async function logout(dependencies = {}) {
  const directory = authDirectory(dependencies.env ?? process.env);
  const stderr = dependencies.stderr ?? process.stderr;
  await withStateLock(directory, "mcp-auth.lock", async () => {
    const path = resolve(directory, "mcp-auth.json");
    let contents;
    try { contents = privateRead(path); } catch (error) { if (error?.code === "ENOENT") return; throw error; }
    let revoked = false;
    try {
      const account = validateAccount(JSON.parse(contents));
      await boundedFetch("https://cohesivity.ai/oauth/revoke", {
        method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded", "User-Agent": USER_AGENT },
        body: new URLSearchParams({ token: account.refresh_token, token_type_hint: "refresh_token", client_id: account.client_id }),
      }, dependencies.fetch ?? globalThis.fetch, 64 * 1024);
      revoked = true;
    } catch {} finally { rmSync(path); }
    stderr.write(revoked ? "Cohesivity account tokens revoked and local sign-in removed.\n" : "Local sign-in removed, but Cohesivity could not confirm server revocation; the server grant may remain active.\n");
  });
}

function validateResource(value) {
  if (typeof value !== "string" || !RESOURCE_NAMES.includes(value)) {
    fail("resource must be a supported Cohesivity resource name.");
  }
  return value;
}

function validateCallbackUrl(value) {
  if (typeof value !== "string" || value.length === 0 || value.length > 2048) {
    fail("callback_urls entries must be non-empty URLs.");
  }
  let parsed;
  try {
    parsed = new URL(value);
  } catch {
    fail("callback_urls contains an invalid URL.");
  }
  if (
    !["http:", "https:"].includes(parsed.protocol) ||
    parsed.username ||
    parsed.password ||
    parsed.hash
  ) {
    fail("callback_urls contains an unsafe URL.");
  }
  if (parsed.protocol === "http:" && !["localhost", "127.0.0.1", "[::1]"].includes(parsed.hostname)) {
    fail("callback_urls permits plain HTTP only for localhost.");
  }
  return value;
}

function validateConfiguration(resource, value, optional) {
  if (value === undefined) {
    if (optional) return undefined;
    fail(`configuration is required for ${resource}.`);
  }
  if (resource === "postgres") {
    const config = exactObject(value, [], ["region"]);
    if (config.region !== undefined && !POSTGRES_REGIONS.includes(config.region)) {
      fail("region must be a supported Cohesivity Postgres region.");
    }
    return config.region === undefined ? {} : { region: config.region };
  }
  if (resource === "inbox") {
    const config = exactObject(value, [], ["webhook_url"]);
    if (config.webhook_url === undefined) return {};
    const webhookUrl = validateCallbackUrl(config.webhook_url);
    if (!webhookUrl.startsWith("https://")) fail("webhook_url must use HTTPS.");
    return { webhook_url: webhookUrl };
  }
  if (resource === "realtime") {
    const config = exactObject(value, [], ["write_region"]);
    if (config.write_region !== undefined && !REALTIME_REGIONS.includes(config.write_region)) {
      fail("write_region must be a documented Cohesivity Realtime region.");
    }
    return config.write_region === undefined
      ? {}
      : { write_region: config.write_region };
  }
  if (resource === "social-login") {
    const config = exactObject(value, ["callback_urls"]);
    if (
      !Array.isArray(config.callback_urls) ||
      config.callback_urls.length === 0 ||
      config.callback_urls.length > 50
    ) {
      fail("callback_urls must contain between 1 and 50 URLs.");
    }
    const callbackUrls = config.callback_urls.map(validateCallbackUrl);
    if (new Set(callbackUrls).size !== callbackUrls.length) fail("callback_urls must be unique.");
    return { callback_urls: callbackUrls };
  }
  if (resource === "vector-database") {
    const config = exactObject(value, ["dimensions"], ["metric"]);
    if (![384, 768, 1024, 1536, 3072].includes(config.dimensions)) {
      fail("dimensions must be one of 384, 768, 1024, 1536, or 3072.");
    }
    if (config.metric !== undefined && !["cosine", "euclidean", "dotproduct"].includes(config.metric)) {
      fail("metric must be cosine, euclidean, or dotproduct.");
    }
    return {
      dimensions: config.dimensions,
      ...(config.metric === undefined ? {} : { metric: config.metric }),
    };
  }
  if (value !== undefined) fail(`${resource} does not accept configuration fields.`);
  return undefined;
}

function redactString(value) {
  return value
    .replace(/(?:coh_(?:man|app)|mcp_(?:at|rt|ac))_[A-Za-z0-9._~-]+/g, "[redacted]")
    .replace(/\b(?:whsec_|sk-|ghp_|xox[baprs]-)[A-Za-z0-9._~-]+/g, "[redacted]")
    .replace(/Bearer\s+[^\s"']+/gi, "Bearer [redacted]")
    .replace(/([?&](?:key|token|secret|password|authorization|api_?key|access_token|refresh_token)=)[^&#\s]+/gi, "$1[redacted]")
    .replace(/\b([a-z][a-z0-9+.-]*:\/\/)(?:[^/@\s:]+(?::[^/@\s]*)?@)/gi, "$1[redacted]@")
    .replace(/\b(password|pwd|pass|user\s*id|uid|access\s*token|refresh\s*token)\s*=\s*[^;\s]+/gi, "$1=[redacted]")
    .replace(/-----BEGIN [^-]+ PRIVATE KEY-----[\s\S]*?-----END [^-]+ PRIVATE KEY-----/g, "[redacted private key]");
}

function sensitiveKey(key, path = []) {
  return /^(?:coh_management_key|coh_application_key|management_key|application_key|access_token|refresh_token|feedback_token|quote_token|approval_token|auth_header|authorization|secret|password|credentials?|config_enc|device_code_enc|raw|details|metadata|logs?|events_raw|command|claude_web|code|value)$/i.test(key)
    || /^(?:(?:connection|database|postgres|redis|jdbc)[_-]?(?:string|uri|url)|credentials?[_-]?(?:uri|url)|dsn)$/i.test(key)
    || /(?:^|_)(?:api_key|private_key|client_secret|provider_secret|bot_token|wait_token|verification_token|verification_code)(?:_|$)/i.test(key)
    || /(?:^|_)(?:feedback|approval|wait|verification|redemption|discount)_(?:token|code|capability)(?:_|$)/i.test(key)
    || (path.length > 0 && (/^(?:approval|checkout_url|operation_handle|redemption|verification|wait)$/i.test(key)
      || /(?:^|_)(?:feedback|approval|wait|verification|redemption|discount)_(?:url|uri|handle)(?:_|$)/i.test(key)));
}

export function safeValue(value, path = []) {
  if (typeof value === "string") return redactString(value);
  if (Array.isArray(value)) return value.map((child, index) => safeValue(child, [...path, index]));
  if (!value || typeof value !== "object") return value;
  const out = {};
  for (const [key, child] of Object.entries(value)) {
    if (sensitiveKey(key, path)) continue;
    out[redactString(key)] = safeValue(child, [...path, key]);
  }
  return out;
}

function projectDto(dto) {
  const fields = new Set(MANAGEMENT_OUTPUT_FIELDS[dto]);
  return (raw) =>
    safeValue(
      Object.fromEntries(
        Object.entries(isRecord(raw) ? raw : {}).filter(([key, value]) => fields.has(key) && value !== undefined),
      ),
    );
}

async function managementRequest(
  projectRoot,
  method,
  path,
  body,
  fetchImpl,
  projectOutput,
) {
  const credentials = readCredentialFields(projectRoot, true);
  const url = new URL(path, MANAGEMENT_API_URL);
  if (url.origin !== new URL(MANAGEMENT_API_URL).origin || !url.pathname.startsWith("/api/")) {
    fail("Invalid Cohesivity Management API path.", "management_operation_failed");
  }

  let response;
  try {
    response = await fetchImpl(url, {
      method,
      redirect: "error",
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${credentials.coh_management_key}`,
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
        "User-Agent": USER_AGENT,
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      signal: AbortSignal.timeout(30_000),
    });
  } catch {
    fail("The Cohesivity Management API request failed.", "management_operation_failed");
  }

  const declaredLength = Number(response.headers.get("content-length"));
  if (Number.isFinite(declaredLength) && declaredLength > MAX_RESPONSE_BYTES) {
    fail("The Cohesivity Management API response is unexpectedly large.", "management_operation_failed");
  }
  const text = await response.text();
  if (Buffer.byteLength(text) > MAX_RESPONSE_BYTES) {
    fail("The Cohesivity Management API response is unexpectedly large.", "management_operation_failed");
  }
  let document = {};
  if (text.length > 0) {
    try {
      document = JSON.parse(text);
    } catch {
      fail("The Cohesivity Management API returned an invalid response.", "management_operation_failed");
    }
  }
  if (!response.ok) {
    const message = isRecord(document) ? document.message || document.error : undefined;
    fail(
      message ? String(message) : "The management operation failed.",
      "management_operation_failed",
      response.status,
    );
  }
  return projectOutput(document);
}

// Fetches one fixed public Cohesivity page. The offering slug only selects a
// path under /offerings/, never a caller-supplied URL.
export async function readDocument(argumentsValue, fetchImpl = globalThis.fetch) {
  const args = exactObject(argumentsValue, ["document"], ["offering"]);
  let path = Object.hasOwn(DOCUMENT_PATHS, args.document) ? DOCUMENT_PATHS[args.document] : undefined;
  if (args.document === "offering") {
    if (typeof args.offering !== "string" || !/^[a-z0-9][a-z0-9-]{0,63}$/u.test(args.offering)) {
      fail("The offering field is required for an offering document.");
    }
    path = `offerings/${args.offering}`;
  } else if (path === undefined || args.offering !== undefined) {
    fail("Unknown document. Use one of the values advertised by tools/list.");
  }
  const url = new URL(path, "https://cohesivity.ai/").href;
  let response;
  let text;
  try {
    response = await fetchImpl(url, {
      redirect: "error",
      headers: { Accept: "text/markdown, text/plain", "User-Agent": USER_AGENT },
      signal: AbortSignal.timeout(30_000),
    });
    text = await response.text();
  } catch {
    fail(`Documentation could not be fetched from ${url}.`);
  }
  if (!response.ok || Buffer.byteLength(text) > MAX_RESPONSE_BYTES) {
    fail(`Documentation was not found at ${url}.`);
  }
  return { text, url };
}

export async function callTool(name, argumentsValue, dependencies = {}) {
  const fetchImpl = dependencies.fetch ?? globalThis.fetch;

  if (name === "create_tenant") {
    const args = exactObject(argumentsValue, ["project_root", "confirmed"]);
    if (args.confirmed !== true) fail("confirmed must be true after explicit user authorization.");
    const projectRoot = validateProjectRoot(args.project_root);
    const path = credentialPath(projectRoot);
    try {
      lstatSync(path);
      validateProjectCredentials(projectRoot);
    } catch (error) {
      if (error instanceof SafeError) throw error;
      if (error?.code !== "ENOENT") fail("Could not validate the project credential path.");
    }
    ensureCredentialIgnored(projectRoot);
    return runProjectQuickstart(projectRoot, dependencies);
  }

  if (name === "claim_tenant") {
    const args = exactObject(argumentsValue, ["project_root", "confirmed"]);
    if (args.confirmed !== true) fail("confirmed must be true after explicit user authorization.");
    const projectRoot = validateProjectRoot(args.project_root);
    const credentials = readCredentialFields(projectRoot, true);
    const response = await managementRequest(
      projectRoot,
      "POST",
      "claim/url",
      undefined,
      fetchImpl,
      projectDto("claim"),
    );
    const approvalUrl = response.approval_url;
    let parsed;
    try {
      parsed = new URL(approvalUrl);
    } catch {
      fail("The claim operation did not return a safe approval URL.", "invalid_management_response");
    }
    if (
      parsed.origin !== "https://cohesivity.ai" ||
      !/^\/c\/[A-Za-z0-9_-]+$/u.test(parsed.pathname) ||
      parsed.username ||
      parsed.password ||
      parsed.search ||
      parsed.hash
    ) {
      fail("The claim operation did not return a safe approval URL.", "invalid_management_response");
    }
    return { tenant_id: credentials.tenant_id, approval_url: approvalUrl };
  }

  if (name === "tenant_status") {
    const args = exactObject(argumentsValue, ["project_root"]);
    const projectRoot = validateProjectRoot(args.project_root);
    const credentials = readCredentialFields(projectRoot, true);
    const status = await managementRequest(
      projectRoot,
      "GET",
      "status",
      undefined,
      fetchImpl,
      projectDto("status"),
    );
    return { tenant_id: credentials.tenant_id, status };
  }

  if (name === "provision_resource") {
    const hasResource =
      isRecord(argumentsValue) && Object.prototype.hasOwnProperty.call(argumentsValue, "resource");
    const hasResources =
      isRecord(argumentsValue) && Object.prototype.hasOwnProperty.call(argumentsValue, "resources");
    if (hasResource === hasResources) {
      fail("Provide exactly one of resource or resources.");
    }
    if (hasResources) {
      const args = exactObject(argumentsValue, ["project_root", "resources", "confirmed"], ["configurations"]);
      if (args.confirmed !== true) fail("confirmed must be true after explicit user authorization.");
      const projectRoot = validateProjectRoot(args.project_root);
      if (
        !Array.isArray(args.resources) ||
        args.resources.length === 0 ||
        args.resources.length > RESOURCE_NAMES.length
      ) {
        fail("resources must be a non-empty array of supported resource names.");
      }
      const resources = args.resources.map(validateResource);
      if (new Set(resources).size !== resources.length) fail("resources must be unique.");

      const configurations = exactObject(args.configurations ?? {}, [], [
        "postgres",
        "inbox",
        "realtime",
        "social-login",
        "vector-database",
      ]);
      const body = { resources };
      for (const [resource, configuration] of Object.entries(configurations)) {
        if (!resources.includes(resource)) fail(`Configuration supplied for unrequested resource: ${resource}.`);
        body[resource] = validateConfiguration(resource, configuration, false);
      }
      for (const required of ["social-login", "vector-database"]) {
        if (resources.includes(required) && configurations[required] === undefined) {
          fail(`configurations.${required} is required when ${required} is requested.`);
        }
      }

      const result = await managementRequest(
        projectRoot,
        "POST",
        "resources",
        body,
        fetchImpl,
        projectDto("provision"),
      );
      return { resources, result };
    }

    const args = exactObject(argumentsValue, ["project_root", "resource", "confirmed"], ["configuration"]);
    if (args.confirmed !== true) fail("confirmed must be true after explicit user authorization.");
    const projectRoot = validateProjectRoot(args.project_root);
    const resource = validateResource(args.resource);
    const configuration = validateConfiguration(
      resource,
      args.configuration,
      !["social-login", "vector-database"].includes(resource),
    );
    const result = await managementRequest(
      projectRoot,
      "POST",
      `resources/${resource}`,
      configuration,
      fetchImpl,
      projectDto("provision"),
    );
    return { resource, result };
  }

  if (name === "give_feedback") {
    let args;
    try {
      args = exactObject(argumentsValue, ["project_root", "feedback"]);
    } catch {
      fail("give_feedback requires only project_root and feedback.");
    }
    if (typeof args.feedback !== "string" || args.feedback.length > MAX_FEEDBACK_LENGTH || !args.feedback.trim()) {
      fail("feedback must be a non-empty string of at most 20000 characters.");
    }
    const projectRoot = validateProjectRoot(args.project_root);
    try {
      return await managementRequest(
        projectRoot,
        "POST",
        "feedback/service",
        { feedback: args.feedback.trim() },
        fetchImpl,
        (response) => {
          if (!isRecord(response) || response.success !== true) fail("Invalid feedback response.");
          return { success: true };
        },
      );
    } catch {
      fail("Feedback submission could not be confirmed.", "feedback_submission_failed");
    }
  }

  fail(`Unknown tool: ${name}.`);
}

function toolError(error) {
  const value =
    error instanceof SafeError
      ? {
          error: error.code,
          ...(error.httpStatus === undefined ? {} : { http_status: error.httpStatus }),
          message: redactString(error.message),
        }
      : { error: "tool_call_failed", message: "The tool call failed safely." };
  return JSON.stringify(value, null, 2);
}

export async function handleRequest(request, dependencies = {}) {
  if (!isRecord(request) || request.jsonrpc !== "2.0" || typeof request.method !== "string") {
    return { jsonrpc: "2.0", id: request?.id ?? null, error: { code: -32600, message: "Invalid Request" } };
  }
  if (request.method === "initialize") {
    return {
      jsonrpc: "2.0",
      id: request.id,
      result: {
        protocolVersion: "2025-06-18",
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: SERVER_NAME, version: SERVER_VERSION },
        instructions: SERVER_INSTRUCTIONS,
      },
    };
  }
  if (request.method === "ping") {
    return { jsonrpc: "2.0", id: request.id, result: {} };
  }
  if (request.method === "tools/list") {
    return { jsonrpc: "2.0", id: request.id, result: { tools: TOOLS } };
  }
  if (request.method === "tools/call") {
    try {
      const params = exactObject(request.params, ["name"], ["arguments", "_meta"]);
      if (params._meta !== undefined && !isRecord(params._meta)) fail("_meta must be an object.");
      if (typeof params.name !== "string") fail("Tool name must be a string.");
      if (params.name === DOCUMENTATION_TOOL.name) {
        const { text, url } = await readDocument(params.arguments ?? {}, dependencies.fetch);
        return {
          jsonrpc: "2.0",
          id: request.id,
          result: {
            content: [{ type: "text", text }],
            structuredContent: { url, contentType: "text/markdown" },
            isError: false,
          },
        };
      }
      const result = await callTool(params.name, params.arguments ?? {}, dependencies);
      const text = JSON.stringify(result, null, 2);
      if (SECRET_DETECT.test(text)) throw new Error("secret reached the MCP output boundary");
      return {
        jsonrpc: "2.0",
        id: request.id,
        result: {
          content: [{ type: "text", text }],
          structuredContent: result,
        },
      };
    } catch (error) {
      return {
        jsonrpc: "2.0",
        id: request.id,
        result: {
          isError: true,
          content: [{ type: "text", text: toolError(error) }],
        },
      };
    }
  }
  if (request.method.startsWith("notifications/")) return undefined;
  return {
    jsonrpc: "2.0",
    id: request.id ?? null,
    error: { code: -32601, message: "Method not found" },
  };
}

export async function runServer(input = process.stdin, output = process.stdout) {
  const lines = createInterface({ input, crlfDelay: Infinity, terminal: false });
  for await (const line of lines) {
    if (line.trim() === "") continue;
    let request;
    try {
      request = JSON.parse(line);
    } catch {
      output.write(`${JSON.stringify({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error" } })}\n`);
      continue;
    }
    const response = await handleRequest(request);
    if (response !== undefined && request.id !== undefined) output.write(`${JSON.stringify(response)}\n`);
  }
}

function launchedDirectly() {
  if (!process.argv[1]) return false;
  try {
    return realpathSync(resolve(process.argv[1])) === realpathSync(fileURLToPath(import.meta.url));
  } catch {
    return false;
  }
}

const isMain = launchedDirectly();
if (isMain) {
  const command = process.argv[2];
  const run = command === undefined ? runServer
    : command === "login" && process.argv.length === 3 ? login
    : command === "logout" && process.argv.length === 3 ? logout
    : () => fail("Usage: project-bootstrap.mjs [login|logout]");
  Promise.resolve().then(run).catch((error) => {
    if (command !== undefined) process.stderr.write(
      `${error instanceof SafeError ? redactString(error.message) : "The command failed safely."}\n`,
    );
    process.exitCode = 1;
  });
}
