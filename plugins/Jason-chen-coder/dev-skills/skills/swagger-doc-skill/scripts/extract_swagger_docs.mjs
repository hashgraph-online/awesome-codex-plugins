#!/usr/bin/env node
// Extract endpoint documentation from Swagger/OpenAPI URLs without external dependencies.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HTTP_METHODS = ["get", "put", "post", "delete", "patch", "options", "head", "trace"];
const DEFAULT_CANDIDATE_PATHS = [
  "/openapi.json",
  "/swagger.json",
  "/v3/api-docs",
  "/v2/api-docs",
  "/api-docs",
  "/doc.json",
  "/swagger/doc.json",
  "/swagger/v1/swagger.json",
  "/swagger-resources",
];
const SEARCH_SYNONYMS = new Map([
  ["登录", ["login", "signin", "sign in", "auth", "authenticate", "token", "session"]],
  ["登出", ["logout", "signout", "sign out", "session"]],
  ["注册", ["register", "signup", "sign up", "create user"]],
  ["用户", ["user", "account", "profile"]],
  ["设备", ["device", "equipment", "instrument"]],
  ["任务", ["task", "job", "run", "execution"]],
  ["运行", ["run", "task", "job", "execution"]],
  ["协议", ["protocol", "workflow", "method"]],
  ["创建", ["create", "add", "new"]],
  ["查询", ["query", "search", "list", "get", "find"]],
  ["删除", ["delete", "remove"]],
  ["更新", ["update", "modify", "edit", "patch"]],
  ["上传", ["upload", "import"]],
  ["下载", ["download", "export"]],
  ["login", ["登录", "auth", "token", "session"]],
  ["auth", ["登录", "认证", "token", "authorize"]],
  ["token", ["登录", "auth", "session"]],
  ["device", ["设备", "equipment", "instrument"]],
  ["task", ["任务", "run", "job"]],
  ["run", ["运行", "任务", "execution"]],
]);

class ExtractionError extends Error {}

function parseArgs(argv) {
  const args = {
    url: "",
    mode: "document",
    format: "markdown",
    output: "",
    config: "",
    configHeaders: {},
    cache: "",
    refreshCache: false,
    header: [],
    timeout: 15000,
    insecure: false,
    includeDeprecated: false,
    verbose: false,
    tag: [],
    method: [],
    path: [],
    type: [],
    search: [],
    details: false,
    noTypes: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    const readValue = () => {
      index += 1;
      if (index >= argv.length) {
        throw new ExtractionError(`Missing value for ${item}`);
      }
      return argv[index];
    };

    if (item === "--mode") args.mode = readValue();
    else if (item === "--format") args.format = readValue();
    else if (item === "--output" || item === "-o") args.output = readValue();
    else if (item === "--config") args.config = readValue();
    else if (item === "--cache") args.cache = readValue();
    else if (item === "--refresh-cache") args.refreshCache = true;
    else if (item === "--header") args.header.push(readValue());
    else if (item === "--timeout") args.timeout = Number(readValue()) * 1000;
    else if (item === "--insecure") args.insecure = true;
    else if (item === "--include-deprecated") args.includeDeprecated = true;
    else if (item === "--verbose") args.verbose = true;
    else if (item === "--tag") args.tag.push(readValue());
    else if (item === "--method") args.method.push(readValue());
    else if (item === "--path") args.path.push(readValue());
    else if (item === "--type") args.type.push(readValue());
    else if (item === "--search") args.search.push(readValue());
    else if (item === "--details") args.details = true;
    else if (item === "--no-types") args.noTypes = true;
    else if (item === "--help" || item === "-h") {
      printHelp();
      process.exit(0);
    } else if (item.startsWith("-")) {
      throw new ExtractionError(`Unknown option ${item}`);
    } else if (!args.url) {
      args.url = item;
    } else {
      throw new ExtractionError(`Unexpected argument ${item}`);
    }
  }

  applyConfig(args);

  if (!args.url) {
    printHelp();
    throw new ExtractionError("Missing Swagger/OpenAPI URL. Pass a URL or use --config swagger.config.json.");
  }
  if (["endpoint", "api"].includes(args.mode)) {
    args.mode = "endpoints";
    args.details = true;
  }
  if (!["document", "modules", "endpoints", "types", "integration"].includes(args.mode)) {
    throw new ExtractionError("--mode must be one of document, modules, endpoints, endpoint, api, types, integration.");
  }
  if (!["markdown", "json"].includes(args.format)) {
    throw new ExtractionError("--format must be markdown or json.");
  }
  if (!Number.isFinite(args.timeout) || args.timeout <= 0) {
    throw new ExtractionError("--timeout must be a positive number of seconds.");
  }
  return args;
}

function printHelp() {
  console.log(`Usage: extract_swagger_docs.mjs <url> [options]

Options:
  --mode <document|modules|endpoints|endpoint|api|types|integration>
                                            Query/export mode. Default: document
  --format <markdown|json>                    Output format. Default: markdown
  --output, -o <path>                         Output file path. Defaults to stdout
  --config <path>                             Explicit JSON config with swaggerUrl, token, headers, and cache
  --cache <path>                              Read/write a local spec cache for repeated queries
  --refresh-cache                             Fetch remote spec and overwrite --cache
  --tag <text>                                Filter endpoints by tag/module substring
  --method <GET|POST|...>                     Filter endpoints by HTTP method
  --path <text>                               Filter endpoints by path substring
  --type <text>                               Filter type definitions by schema name
  --search <text>                             Search endpoints/types by keyword
  --details                                  Include endpoint request/response details in endpoints mode
  --no-types                                 Omit type definitions in document mode
  --header "Name: value"                     Pass an HTTP header. Repeatable
  --timeout <seconds>                        Per-request timeout. Default: 15
  --insecure                                 Disable TLS certificate verification
  --include-deprecated                       Include deprecated operations
  --verbose                                  Print failed discovery attempts to stderr

Examples:
  node extract_swagger_docs.mjs http://host/doc#/ --mode modules
  node extract_swagger_docs.mjs http://host/doc#/ --mode endpoints --tag 用户管理
  node extract_swagger_docs.mjs http://host/doc#/ --mode integration --search 登录
  node extract_swagger_docs.mjs http://host/doc#/ --mode types --type CreateRun
  node extract_swagger_docs.mjs http://host/doc#/ --mode document --output swagger-api.md`);
}

function applyConfig(args) {
  const configPath = args.config;
  if (!configPath) return;

  const resolvedConfigPath = path.resolve(configPath);
  if (!fs.existsSync(resolvedConfigPath)) {
    throw new ExtractionError(`Config file not found: ${resolvedConfigPath}`);
  }

  let config;
  try {
    config = JSON.parse(fs.readFileSync(resolvedConfigPath, "utf8"));
  } catch (error) {
    throw new ExtractionError(`Could not parse config file ${resolvedConfigPath}: ${error.message}`);
  }

  const configuredUrl = config.swaggerUrl || config.url;
  if (!args.url && configuredUrl) {
    args.url = resolveConfiguredUrl(configuredUrl, resolvedConfigPath);
  }

  if (config.headers && typeof config.headers === "object" && !Array.isArray(config.headers)) {
    for (const [name, value] of Object.entries(config.headers)) {
      setHeader(args.configHeaders, name, String(value));
    }
  }
  if (config.token && !hasHeader(args.configHeaders, "Authorization")) {
    setHeader(args.configHeaders, "Authorization", String(config.token));
  }
  if (!args.cache && (config.cachePath || config.cache)) {
    args.cache = resolveConfiguredPath(config.cachePath || config.cache, resolvedConfigPath);
  }
}

function resolveConfiguredUrl(value, configPath) {
  const text = String(value);
  if (/^[a-zA-Z][a-zA-Z\d+.-]*:/.test(text)) return text;
  const relativeToConfig = path.resolve(path.dirname(configPath), text);
  return fs.existsSync(relativeToConfig) ? relativeToConfig : text;
}

function resolveConfiguredPath(value, configPath) {
  const text = String(value);
  return path.isAbsolute(text) ? text : path.resolve(path.dirname(configPath), text);
}

function parseHeaders(values, baseHeaders = {}) {
  const headers = { ...baseHeaders };
  for (const value of values) {
    const splitAt = value.indexOf(":");
    if (splitAt === -1) {
      throw new ExtractionError(`Invalid header ${JSON.stringify(value)}; expected "Name: value".`);
    }
    setHeader(headers, value.slice(0, splitAt).trim(), value.slice(splitAt + 1).trim());
  }
  return headers;
}

function setHeader(headers, name, value) {
  const existing = Object.keys(headers).find((key) => key.toLowerCase() === name.toLowerCase());
  if (existing) delete headers[existing];
  headers[name] = value;
}

function hasHeader(headers, name) {
  return Object.keys(headers).some((key) => key.toLowerCase() === name.toLowerCase());
}

function normalizeInputUrl(value) {
  const trimmed = value.trim();
  if (fs.existsSync(trimmed)) {
    return pathToFileURL(path.resolve(trimmed)).href;
  }
  if (!/^[a-zA-Z][a-zA-Z\d+.-]*:/.test(trimmed)) {
    return `http://${trimmed}`;
  }
  return trimmed;
}

function stripFragment(value) {
  const url = new URL(value);
  url.hash = "";
  return url.href;
}

async function fetchUrl(url, headers, timeout, insecure) {
  if (url.startsWith("file:")) {
    const filePath = fileURLToPath(url);
    return {
      url,
      text: fs.readFileSync(filePath, "utf8"),
      contentType: guessContentType(filePath),
    };
  }

  if (insecure) {
    process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";
  }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(url, {
      headers: {
        Accept: "application/json, application/yaml, text/yaml, text/html, */*",
        "User-Agent": "swagger-doc-skill/1.0",
        ...headers,
      },
      redirect: "follow",
      signal: controller.signal,
    });
    const text = await response.text();
    if (!response.ok) {
      throw new ExtractionError(`HTTP ${response.status} for ${url}: ${text.slice(0, 300)}`);
    }
    return {
      url: response.url || url,
      text,
      contentType: response.headers.get("content-type") || "",
    };
  } catch (error) {
    if (error instanceof ExtractionError) throw error;
    const reason = error?.name === "AbortError" ? "timed out" : error?.message || String(error);
    throw new ExtractionError(`Could not fetch ${url}: ${reason}`);
  } finally {
    clearTimeout(timer);
  }
}

function guessContentType(filePath) {
  const lower = filePath.toLowerCase();
  if (lower.endsWith(".html") || lower.endsWith(".htm")) return "text/html";
  if (lower.endsWith(".yaml") || lower.endsWith(".yml")) return "application/yaml";
  return "application/json";
}

async function parseSpecText(text, sourceUrl) {
  const stripped = text.replace(/^\uFEFF/, "").trimStart();
  if (!stripped) return null;
  let parsed = null;
  try {
    parsed = JSON.parse(stripped);
  } catch {
    parsed = await parseYamlIfAvailable(stripped, sourceUrl);
  }
  if (parsed && typeof parsed === "object" && ("paths" in parsed || "swagger" in parsed || "openapi" in parsed)) {
    return parsed;
  }
  return null;
}

async function parseYamlIfAvailable(text, sourceUrl) {
  try {
    const yaml = await import("yaml");
    return yaml.parse(text);
  } catch (error) {
    if (sourceUrl.toLowerCase().endsWith(".yaml") || sourceUrl.toLowerCase().endsWith(".yml")) {
      throw new ExtractionError(
        `Could not parse YAML from ${sourceUrl}. Install the optional npm package "yaml" or use a JSON/OpenAPI URL.`
      );
    }
    return null;
  }
}

async function discoverSpecs(inputUrl, headers, timeout, insecure, verbose) {
  const startUrl = stripFragment(normalizeInputUrl(inputUrl));
  const attempts = [];
  const discovered = [];
  const fetchedPages = [];

  const addCandidate = (candidate) => {
    if (!candidate) return;
    const absolute = stripFragment(new URL(htmlDecode(candidate.trim()), startUrl).href);
    if (!attempts.includes(absolute) && !discovered.includes(absolute)) {
      discovered.push(absolute);
    }
  };

  addCandidate(startUrl);
  for (const candidate of commonCandidateUrls(startUrl)) {
    addCandidate(candidate);
  }

  const specs = [];
  while (discovered.length > 0) {
    const url = discovered.shift();
    attempts.push(url);
    let result;
    try {
      result = await fetchUrl(url, headers, timeout, insecure);
    } catch (error) {
      if (url === startUrl) {
        throw new ExtractionError(`Could not access Swagger document URL ${startUrl}: ${error.message}`);
      }
      if (verbose) console.error(`[skip] ${error.message}`);
      continue;
    }

    const spec = await parseSpecText(result.text, result.url);
    if (spec) {
      specs.push({ url: result.url, spec });
      continue;
    }

    const embeddedSpec = await parseEmbeddedSpec(result.text);
    if (embeddedSpec) {
      specs.push({ url: result.url, spec: embeddedSpec });
      continue;
    }

    const resourceLocations = parseSwaggerResources(result.text);
    if (resourceLocations.length > 0) {
      for (const location of resourceLocations) {
        addCandidate(new URL(location, result.url).href);
      }
      continue;
    }

    if (looksLikeHtml(result)) {
      fetchedPages.push(result);
      for (const candidate of extractSpecUrlsFromHtml(result)) {
        addCandidate(candidate);
      }
      for (const scriptUrl of extractScriptUrls(result)) {
        if (attempts.includes(scriptUrl)) continue;
        let script;
        try {
          script = await fetchUrl(scriptUrl, headers, timeout, insecure);
        } catch (error) {
          if (verbose) console.error(`[skip] ${error.message}`);
          continue;
        }
        attempts.push(scriptUrl);
        const embeddedScriptSpec = await parseEmbeddedSpec(script.text);
        if (embeddedScriptSpec) {
          specs.push({ url: script.url, spec: embeddedScriptSpec });
          continue;
        }
        for (const candidate of extractSpecUrlsFromText(script.text, script.url)) {
          addCandidate(candidate);
        }
      }
    }
  }

  if (specs.length > 0) return dedupeSpecs(specs);
  const pageHint = fetchedPages.length > 0 ? "\nFetched UI pages but did not find a spec URL in their config." : "";
  throw new ExtractionError(`No Swagger/OpenAPI spec found for ${inputUrl}.${pageHint}\nAttempted:\n${attempts.map((u) => `- ${u}`).join("\n")}`);
}

function looksLikeHtml(result) {
  const contentType = result.contentType.toLowerCase();
  const text = result.text.slice(0, 1000).toLowerCase();
  return contentType.includes("html") || text.includes("<html") || text.includes("<!doctype html");
}

function commonCandidateUrls(value) {
  const url = new URL(value);
  const root = `${url.protocol}//${url.host}`;
  const candidates = DEFAULT_CANDIDATE_PATHS.map((candidatePath) => new URL(candidatePath, root).href);
  const baseDirs = new Set([url.pathname || "/"]);
  if (!url.pathname.endsWith("/")) {
    baseDirs.add(`${url.pathname.split("/").slice(0, -1).join("/")}/`);
  }
  if (/\/(doc|docs|swagger-ui|swagger|redoc|api-docs)\/?$/.test(url.pathname)) {
    const withoutTail = url.pathname.replace(/\/$/, "").split("/").slice(0, -1).join("/") || "/";
    baseDirs.add(withoutTail.endsWith("/") ? withoutTail : `${withoutTail}/`);
  }

  const relativeNames = [
    "openapi.json",
    "swagger.json",
    "v3/api-docs",
    "v2/api-docs",
    "api-docs",
    "doc.json",
    "swagger/doc.json",
    "swagger-resources",
    "swagger-initializer.js",
    "swagger-ui-init.js",
  ];
  for (const base of baseDirs) {
    const baseUrl = `${url.protocol}//${url.host}${base}`;
    for (const name of relativeNames) {
      candidates.push(new URL(name, baseUrl).href);
    }
  }
  return candidates;
}

function parseSwaggerResources(text) {
  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    return [];
  }
  const locations = [];
  const collectFromObject = (item) => {
    for (const key of ["url", "location", "configUrl"]) {
      if (typeof item?.[key] === "string") locations.push(item[key]);
    }
  };

  if (Array.isArray(parsed)) {
    for (const item of parsed) {
      if (item && typeof item === "object") collectFromObject(item);
    }
  } else if (parsed && typeof parsed === "object") {
    collectFromObject(parsed);
    for (const key of ["urls", "resources"]) {
      if (Array.isArray(parsed[key])) {
        for (const item of parsed[key]) {
          if (item && typeof item === "object") collectFromObject(item);
        }
      }
    }
  }
  return locations;
}

function extractScriptUrls(result) {
  const urls = [];
  for (const match of result.text.matchAll(/<script[^>]+src=["']([^"']+)["']/gi)) {
    const url = new URL(htmlDecode(match[1]), result.url).href;
    const name = new URL(url).pathname.split("/").pop().toLowerCase();
    if (["init", "initializer", "config"].some((token) => name.includes(token))) {
      urls.push(url);
    }
  }
  return urls;
}

function extractSpecUrlsFromHtml(result) {
  const candidates = extractSpecUrlsFromText(result.text, result.url);
  for (const attr of ["spec-url", "data-url", "url"]) {
    const pattern = new RegExp(`${attr}=["']([^"']+(?:json|yaml|api-docs|swagger-resources)[^"']*)["']`, "gi");
    for (const match of result.text.matchAll(pattern)) {
      candidates.push(new URL(htmlDecode(match[1]), result.url).href);
    }
  }
  return candidates;
}

function extractSpecUrlsFromText(text, baseUrl) {
  const candidates = [];
  const patterns = [
    /\burl\s*:\s*["']([^"']+)["']/gi,
    /\bconfigUrl\s*:\s*["']([^"']+)["']/gi,
    /\bspecUrl\s*:\s*["']([^"']+)["']/gi,
    /["'](?:url|location)["']\s*:\s*["']([^"']+)["']/gi,
    /["']([^"']*(?:openapi|swagger|api-docs|doc\.json|swagger-resources)[^"']*)["']/gi,
  ];
  for (const pattern of patterns) {
    for (const match of text.matchAll(pattern)) {
      if (isProbableSpecUrl(match[1])) {
        candidates.push(new URL(htmlDecode(match[1]), baseUrl).href);
      }
    }
  }
  return stableUnique(candidates);
}

function isProbableSpecUrl(value) {
  const trimmed = value.trim();
  if (trimmed.length > 300 || /[\s\x00-\x1f<>`{}]/.test(trimmed)) return false;
  if (!trimmed || trimmed.startsWith("javascript:") || trimmed.startsWith("data:") || trimmed.startsWith("#")) return false;
  let scheme = "";
  try {
    scheme = new URL(trimmed).protocol.replace(":", "");
  } catch {
    scheme = "";
  }
  if (scheme && !["http", "https", "file"].includes(scheme)) return false;
  const lower = trimmed.toLowerCase();
  if (lower === "swagger" || lower === "openapi") return false;
  return ["openapi", "swagger.json", "api-docs", "doc.json", ".json", ".yaml", ".yml", "swagger-resources"].some((token) =>
    lower.includes(token)
  );
}

async function parseEmbeddedSpec(text) {
  for (const pattern of [/"swaggerDoc"\s*:/g, /\bswaggerDoc\s*:/g, /\bspec\s*:/g]) {
    for (const match of text.matchAll(pattern)) {
      const start = text.indexOf("{", match.index + match[0].length);
      if (start === -1) continue;
      const objectText = extractBalancedObject(text, start);
      if (!objectText) continue;
      const spec = await parseSpecText(objectText, "embedded swaggerDoc");
      if (spec) return spec;
    }
  }
  return null;
}

function extractBalancedObject(text, start) {
  let depth = 0;
  let inString = "";
  let escape = false;
  for (let index = start; index < text.length; index += 1) {
    const char = text[index];
    if (inString) {
      if (escape) escape = false;
      else if (char === "\\") escape = true;
      else if (char === inString) inString = "";
      continue;
    }
    if (char === "\"" || char === "'") inString = char;
    else if (char === "{") depth += 1;
    else if (char === "}") {
      depth -= 1;
      if (depth === 0) return text.slice(start, index + 1);
    }
  }
  return null;
}

function dedupeSpecs(specs) {
  const seen = new Set();
  const output = [];
  for (const item of specs) {
    const paths = item.spec?.paths && typeof item.spec.paths === "object" ? Object.keys(item.spec.paths).sort() : [];
    const key = `${JSON.stringify(item.spec?.info || {})}|${JSON.stringify(paths)}`;
    if (!seen.has(key)) {
      seen.add(key);
      output.push(item);
    }
  }
  return output;
}

function stableUnique(values) {
  const seen = new Set();
  const output = [];
  for (const value of values) {
    if (!seen.has(value)) {
      seen.add(value);
      output.push(value);
    }
  }
  return output;
}

function resolveRef(spec, value, seen = new Set()) {
  if (!value || typeof value !== "object") return value;
  const ref = typeof value.$ref === "string" ? value.$ref : typeof value.originalRef === "string" ? value.originalRef : "";
  if (!ref) return value;
  if (seen.has(ref)) return { $ref: ref };
  seen.add(ref);
  const current = ref.startsWith("#/") ? resolveJsonPointer(spec, ref) : getSchemaByName(spec, ref);
  if (!current) return value;
  if (current && typeof current === "object" && !Array.isArray(current)) {
    const overrides = Object.fromEntries(Object.entries(value).filter(([key]) => key !== "$ref" && key !== "originalRef"));
    return resolveRef(spec, { ...current, ...overrides }, seen);
  }
  return current;
}

function resolveJsonPointer(spec, ref) {
  let current = spec;
  for (const part of ref.slice(2).split("/")) {
    const key = part.replaceAll("~1", "/").replaceAll("~0", "~");
    if (current && typeof current === "object" && key in current) current = current[key];
    else return null;
  }
  return current;
}

function getSchemaByName(spec, name) {
  return spec.components?.schemas?.[name] || spec.definitions?.[name] || null;
}

function refName(ref) {
  return ref.split("/").pop().replaceAll("~1", "/").replaceAll("~0", "~");
}

function schemaLabel(schema, spec, depth = 0) {
  schema = resolveRef(spec, schema);
  if (!schema || typeof schema !== "object") return "any";
  if (typeof schema.$ref === "string") return refName(schema.$ref);
  if (Array.isArray(schema.oneOf)) return `oneOf(${schema.oneOf.map((item) => schemaLabel(item, spec, depth + 1)).join(" | ")})`;
  if (Array.isArray(schema.anyOf)) return `anyOf(${schema.anyOf.map((item) => schemaLabel(item, spec, depth + 1)).join(" | ")})`;
  if (Array.isArray(schema.allOf)) return `allOf(${schema.allOf.map((item) => schemaLabel(item, spec, depth + 1)).join(" + ")})`;
  let schemaType = schema.type;
  if (!schemaType && schema.properties) schemaType = "object";
  if (!schemaType && schema.items) schemaType = "array";
  if (schemaType === "array") return `array<${schemaLabel(schema.items || {}, spec, depth + 1)}>`;
  if (schemaType === "object") {
    if (schema.additionalProperties && !schema.properties) {
      return `object<string, ${schemaLabel(schema.additionalProperties, spec, depth + 1)}>`;
    }
    return "object";
  }
  if (schemaType) return schema.format ? `${schemaType}(${schema.format})` : String(schemaType);
  if (schema.example !== undefined && !hasSchemaShape(schema)) return exampleLabel(schema.example);
  return String(schema.title || "any");
}

function schemaLines(schema, spec, indent = 0, depth = 0, maxDepth = 4, expandNestedDepth = 2) {
  const prefix = "  ".repeat(indent);
  schema = resolveRef(spec, schema);
  if (!schema || typeof schema !== "object") return [`${prefix}- any`];
  if (typeof schema.$ref === "string") return [`${prefix}- ${refName(schema.$ref)}`];
  if (depth > maxDepth) return [`${prefix}- ${schemaLabel(schema, spec, depth)}`];

  for (const key of ["allOf", "oneOf", "anyOf"]) {
    if (Array.isArray(schema[key])) {
      const lines = [`${prefix}- ${key}:`];
      for (const item of schema[key]) {
        lines.push(...schemaLines(item, spec, indent + 1, depth + 1, maxDepth, expandNestedDepth));
      }
      return lines;
    }
  }

  if (schema.example !== undefined && !hasSchemaShape(schema)) {
    return exampleLines(schema.example, indent, depth, maxDepth, expandNestedDepth);
  }

  const enumValues = schema.enum ? ` enum=${JSON.stringify(schema.enum)}` : "";
  const defaultValue = schema.default !== undefined ? ` default=${JSON.stringify(schema.default)}` : "";
  const description = cleanText(schema.description || schema.title || "");
  const suffix = `${enumValues}${defaultValue}${description ? ` - ${description}` : ""}`;
  const lines = [`${prefix}- ${schemaLabel(schema, spec, depth)}${suffix}`];

  if (schema.properties && typeof schema.properties === "object") {
    const required = new Set(Array.isArray(schema.required) ? schema.required : []);
    for (const [name, child] of Object.entries(schema.properties)) {
      const childSchema = resolveRef(spec, child);
      const childDescription = childSchema && typeof childSchema === "object" ? cleanText(childSchema.description || "") : "";
      let line = `${prefix}  - \`${name}\`: ${schemaLabel(childSchema, spec, depth + 1)}${required.has(name) ? " required" : ""}`;
      if (childDescription) line += ` - ${childDescription}`;
      lines.push(line);
      if (childSchema && typeof childSchema === "object" && childSchema.properties && depth < expandNestedDepth) {
        lines.push(...schemaLines(childSchema, spec, indent + 2, depth + 1, maxDepth, expandNestedDepth).slice(1));
      }
    }
  } else if (schema.items) {
    lines.push(...schemaLines(schema.items, spec, indent + 1, depth + 1, maxDepth, expandNestedDepth));
  }
  return lines;
}

function hasSchemaShape(schema) {
  return Boolean(
    schema.properties ||
      schema.items ||
      schema.additionalProperties ||
      Array.isArray(schema.allOf) ||
      Array.isArray(schema.oneOf) ||
      Array.isArray(schema.anyOf)
  );
}

function exampleLabel(value) {
  if (Array.isArray(value)) {
    const sample = value.find((item) => item !== null && item !== undefined);
    return `array<${sample === undefined ? "any" : exampleLabel(sample)}>`;
  }
  if (value === null || value === undefined) return "any";
  if (typeof value === "object") return "object";
  if (typeof value === "number") return Number.isInteger(value) ? "integer" : "number";
  return typeof value;
}

function exampleLines(value, indent = 0, depth = 0, maxDepth = 4, expandNestedDepth = 2) {
  const prefix = "  ".repeat(indent);
  if (depth > maxDepth) return [`${prefix}- ${exampleLabel(value)} - example: ${formatExample(value)}`];
  if (Array.isArray(value)) {
    const sample = value.find((item) => item !== null && item !== undefined);
    const lines = [`${prefix}- ${exampleLabel(value)}`];
    if (sample !== undefined && depth < expandNestedDepth) {
      lines.push(...exampleLines(sample, indent + 1, depth + 1, maxDepth, expandNestedDepth));
    }
    return lines;
  }
  if (value && typeof value === "object") {
    const lines = [`${prefix}- object`];
    for (const [name, child] of Object.entries(value)) {
      const label = exampleLabel(child);
      if (child && typeof child === "object" && depth < expandNestedDepth) {
        lines.push(`${prefix}  - \`${name}\`: ${label}`);
        lines.push(...exampleLines(child, indent + 2, depth + 1, maxDepth, expandNestedDepth).slice(1));
      } else {
        lines.push(`${prefix}  - \`${name}\`: ${label} - example: ${formatExample(child)}`);
      }
    }
    return lines;
  }
  return [`${prefix}- ${exampleLabel(value)} - example: ${formatExample(value)}`];
}

function formatExample(value) {
  const text = JSON.stringify(value);
  if (text === undefined) return "undefined";
  return text.length > 120 ? `${text.slice(0, 117)}...` : text;
}

function buildExample(schema, spec, depth = 0) {
  schema = resolveRef(spec, schema);
  if (!schema || typeof schema !== "object" || depth > 5) return null;
  if (schema.example !== undefined) return schema.example;
  if (schema.default !== undefined) return schema.default;
  if (Array.isArray(schema.enum) && schema.enum.length > 0) return schema.enum[0];
  if (Array.isArray(schema.oneOf) && schema.oneOf.length > 0) return buildExample(schema.oneOf[0], spec, depth + 1);
  if (Array.isArray(schema.anyOf) && schema.anyOf.length > 0) return buildExample(schema.anyOf[0], spec, depth + 1);
  if (Array.isArray(schema.allOf)) {
    const merged = {};
    for (const item of schema.allOf) {
      const value = buildExample(item, spec, depth + 1);
      if (value && typeof value === "object" && !Array.isArray(value)) Object.assign(merged, value);
    }
    return Object.keys(merged).length > 0 ? merged : null;
  }

  let schemaType = schema.type;
  if (!schemaType && schema.properties) schemaType = "object";
  if (!schemaType && schema.items) schemaType = "array";
  if (schemaType === "array") {
    const item = buildExample(schema.items || {}, spec, depth + 1);
    return item === null ? [] : [item];
  }
  if (schemaType === "object") {
    const output = {};
    for (const [name, child] of Object.entries(schema.properties || {})) {
      output[name] = buildExample(child, spec, depth + 1);
    }
    return output;
  }
  if (schemaType === "integer") return 0;
  if (schemaType === "number") return 0;
  if (schemaType === "boolean") return true;
  if (schemaType === "string") {
    if (schema.format === "date-time") return "2026-01-01T00:00:00Z";
    if (schema.format === "date") return "2026-01-01";
    if (schema.format === "uuid") return "00000000-0000-0000-0000-000000000000";
    if (schema.format === "password") return "string";
    return "string";
  }
  return null;
}

function cleanText(value) {
  if (value === null || value === undefined) return "";
  return String(value).replace(/\r|\n/g, " ").replace(/\s+/g, " ").trim();
}

function mergedParameters(operation, pathItem) {
  const params = new Map();
  for (const source of [...(pathItem.parameters || []), ...(operation.parameters || [])]) {
    if (source && typeof source === "object") {
      params.set(`${source.name || ""}|${source.in || ""}`, source);
    }
  }
  return [...params.values()];
}

function extractEndpoints(spec, sourceUrl, includeDeprecated) {
  const paths = spec.paths;
  if (!paths || typeof paths !== "object") {
    throw new ExtractionError(`Spec at ${sourceUrl} does not contain a paths object.`);
  }

  const endpoints = [];
  for (const apiPath of Object.keys(paths).sort()) {
    const pathItem = resolveRef(spec, paths[apiPath]);
    if (!pathItem || typeof pathItem !== "object") continue;
    for (const method of HTTP_METHODS) {
      let operation = pathItem[method];
      if (!operation || typeof operation !== "object") continue;
      operation = resolveRef(spec, operation);
      if (operation.deprecated && !includeDeprecated) continue;
      endpoints.push({
        method: method.toUpperCase(),
        path: apiPath,
        tags: operation.tags || ["default"],
        summary: cleanText(operation.summary || ""),
        description: cleanText(operation.description || ""),
        operationId: operation.operationId || "",
        parameters: normalizeParameters(spec, mergedParameters(operation, pathItem)),
        requestBody: normalizeRequestBody(spec, operation),
        responses: normalizeResponses(spec, operation),
        security: normalizeSecurity(spec, operation),
        deprecated: Boolean(operation.deprecated),
      });
    }
  }

  const info = spec.info && typeof spec.info === "object" ? spec.info : {};
  return {
    source: sourceUrl,
    title: info.title || "",
    version: info.version || "",
    description: cleanText(info.description || ""),
    baseUrls: extractBaseUrls(spec, sourceUrl),
    securitySchemes: extractSecuritySchemes(spec),
    endpointCount: endpoints.length,
    endpoints,
  };
}

function extractBaseUrls(spec, sourceUrl) {
  const urls = [];
  if (Array.isArray(spec.servers)) {
    for (const server of spec.servers) {
      if (!server || typeof server !== "object" || !server.url) continue;
      urls.push(resolveServerUrl(applyServerVariables(String(server.url), server.variables), sourceUrl));
    }
  }

  if (spec.host) {
    const scheme = Array.isArray(spec.schemes) && spec.schemes.length > 0 ? spec.schemes[0] : sourceProtocol(sourceUrl) || "https";
    urls.push(`${scheme}://${spec.host}${spec.basePath || ""}`);
  }

  if (urls.length === 0) {
    const origin = sourceOrigin(sourceUrl);
    if (origin) urls.push(origin);
  }
  return stableUnique(urls.filter(Boolean));
}

function applyServerVariables(value, variables) {
  if (!variables || typeof variables !== "object") return value;
  return value.replace(/\{([^}]+)\}/g, (match, name) => {
    const variable = variables[name];
    return variable && typeof variable === "object" && variable.default !== undefined ? String(variable.default) : match;
  });
}

function resolveServerUrl(value, sourceUrl) {
  if (/^[a-zA-Z][a-zA-Z\d+.-]*:/.test(value)) return value.replace(/\/$/, "");
  const origin = sourceOrigin(sourceUrl);
  if (!origin) return value.replace(/\/$/, "");
  return new URL(value, origin).href.replace(/\/$/, "");
}

function sourceOrigin(sourceUrl) {
  try {
    const url = new URL(sourceUrl);
    if (!["http:", "https:"].includes(url.protocol)) return "";
    return url.origin;
  } catch {
    return "";
  }
}

function sourceProtocol(sourceUrl) {
  try {
    const url = new URL(sourceUrl);
    return url.protocol.replace(":", "");
  } catch {
    return "";
  }
}

function extractSecuritySchemes(spec) {
  const schemes = spec.components?.securitySchemes || spec.securityDefinitions || {};
  const output = {};
  if (!schemes || typeof schemes !== "object") return output;
  for (const [name, value] of Object.entries(schemes)) {
    if (!value || typeof value !== "object") continue;
    output[name] = {
      type: value.type || "",
      scheme: value.scheme || "",
      bearerFormat: value.bearerFormat || "",
      in: value.in || "",
      name: value.name || "",
      flows: value.flows ? Object.keys(value.flows) : [],
      authorizationUrl: value.authorizationUrl || "",
      tokenUrl: value.tokenUrl || "",
      description: cleanText(value.description || ""),
    };
  }
  return output;
}

function normalizeSecurity(spec, operation) {
  const requirements = Object.prototype.hasOwnProperty.call(operation, "security") ? operation.security : spec.security;
  if (!Array.isArray(requirements) || requirements.length === 0) return [];
  return requirements
    .filter((requirement) => requirement && typeof requirement === "object")
    .map((requirement) =>
      Object.entries(requirement).map(([name, scopes]) => ({
        name,
        scopes: Array.isArray(scopes) ? scopes : [],
      }))
    )
    .filter((requirement) => requirement.length > 0);
}

function normalizeParameters(spec, parameters) {
  const output = [];
  for (let parameter of parameters) {
    parameter = resolveRef(spec, parameter);
    if (!parameter || typeof parameter !== "object") continue;
    let schema = parameter.schema || {};
    if (["body", "formData"].includes(parameter.in) && Object.keys(schema).length === 0) {
      schema = Object.fromEntries(["type", "format", "items"].filter((key) => key in parameter).map((key) => [key, parameter[key]]));
    }
    output.push({
      name: parameter.name || "",
      in: parameter.in || "",
      required: Boolean(parameter.required),
      description: cleanText(parameter.description || ""),
      type: schemaLabel(schema, spec),
      schema: schemaLines(schema, spec),
      example: buildExample(schema, spec),
    });
  }
  return output;
}

function normalizeRequestBody(spec, operation) {
  let body = operation.requestBody;
  const output = [];
  if (body && typeof body === "object") {
    body = resolveRef(spec, body);
    if (body.content && typeof body.content === "object") {
      for (const [contentType, media] of Object.entries(body.content)) {
        const schema = schemaWithMediaExample(media && typeof media === "object" ? media.schema || {} : {}, media);
        output.push({
          contentType,
          required: Boolean(body.required),
          description: cleanText(body.description || ""),
          type: schemaLabel(schema, spec),
          schema: schemaLines(schema, spec),
          example: buildExample(schema, spec),
        });
      }
    }
    return output;
  }

  for (let parameter of operation.parameters || []) {
    parameter = resolveRef(spec, parameter);
    if (!parameter || typeof parameter !== "object") continue;
    if (parameter.in === "body") {
      const schema = parameter.schema || {};
      output.push({
        contentType: "application/json",
        required: Boolean(parameter.required),
        description: cleanText(parameter.description || ""),
        type: schemaLabel(schema, spec),
        schema: schemaLines(schema, spec),
        example: buildExample(schema, spec),
      });
    } else if (parameter.in === "formData") {
      const schema = Object.fromEntries(["type", "format", "items"].filter((key) => key in parameter).map((key) => [key, parameter[key]]));
      output.push({
        contentType: "multipart/form-data",
        required: Boolean(parameter.required),
        description: cleanText(parameter.description || parameter.name || ""),
        type: schemaLabel(schema, spec),
        schema: schemaLines(schema, spec),
        example: buildExample(schema, spec),
      });
    }
  }
  return output;
}

function normalizeResponses(spec, operation) {
  const responses = operation.responses || {};
  const output = [];
  if (!responses || typeof responses !== "object") return output;
  for (const status of Object.keys(responses).sort()) {
    const response = resolveRef(spec, responses[status]);
    if (!response || typeof response !== "object") continue;
    const contentEntries = [];
    if (response.content && typeof response.content === "object") {
      for (const [contentType, media] of Object.entries(response.content)) {
        const schema = schemaWithMediaExample(media && typeof media === "object" ? media.schema || {} : {}, media);
        contentEntries.push({
          contentType,
          type: schemaLabel(schema, spec),
          schema: schemaLines(schema, spec),
          example: buildExample(schema, spec),
        });
      }
    } else if (response.schema) {
      contentEntries.push({
        contentType: "application/json",
        type: schemaLabel(response.schema, spec),
        schema: schemaLines(response.schema, spec),
        example: buildExample(response.schema, spec),
      });
    }
    output.push({
      status: String(status),
      description: cleanText(response.description || ""),
      content: contentEntries,
    });
  }
  return output;
}

function schemaWithMediaExample(schema, media) {
  const base = schema && typeof schema === "object" && !Array.isArray(schema) ? schema : {};
  if (base.example !== undefined || !media || typeof media !== "object") return base;
  if (media.example !== undefined) return { ...base, example: media.example };
  if (media.examples && typeof media.examples === "object") {
    for (const example of Object.values(media.examples)) {
      if (example && typeof example === "object" && "value" in example) return { ...base, example: example.value };
      if (example !== undefined) return { ...base, example };
    }
  }
  return base;
}

function extractSchemas(spec) {
  const schemaMaps = [];
  if (spec.components?.schemas && typeof spec.components.schemas === "object") schemaMaps.push(spec.components.schemas);
  if (spec.definitions && typeof spec.definitions === "object") schemaMaps.push(spec.definitions);

  const schemas = [];
  const seen = new Set();
  for (const schemaMap of schemaMaps) {
    for (const name of Object.keys(schemaMap).sort()) {
      if (seen.has(name)) continue;
      seen.add(name);
      const schema = resolveRef(spec, schemaMap[name]);
      const description = schema && typeof schema === "object" ? cleanText(schema.description || schema.title || "") : "";
      schemas.push({
        name,
        type: schemaLabel(schema, spec),
        description,
        schema: schemaLines(schema, spec, 0, 0, 8, 8),
        rawSchema: schema,
      });
    }
  }
  return schemas;
}

function extractModules(endpoints) {
  const modules = new Map();
  for (const endpoint of endpoints) {
    const name = String((endpoint.tags || ["default"])[0]);
    if (!modules.has(name)) modules.set(name, { name, endpointCount: 0, methods: {}, paths: [] });
    const module = modules.get(name);
    module.endpointCount += 1;
    module.methods[endpoint.method] = (module.methods[endpoint.method] || 0) + 1;
    module.paths.push({
      method: endpoint.method,
      path: endpoint.path,
      summary: endpoint.summary || endpoint.description || "",
    });
  }
  return [...modules.keys()].sort().map((name) => modules.get(name));
}

function applyFilters(document, args) {
  const searchTerms = expandSearchTerms(args.search);
  const endpoints = document.endpoints.filter((endpoint) => endpointMatches(endpoint, args.tag, args.method, args.path, searchTerms));
  const schemas = (document.schemas || []).filter((schema) => schemaMatches(schema, args.type, searchTerms));
  return {
    ...document,
    endpoints,
    endpointCount: endpoints.length,
    modules: extractModules(endpoints),
    moduleCount: extractModules(endpoints).length,
    schemas,
    typeCount: schemas.length,
  };
}

function endpointMatches(endpoint, tags, methods, pathTerms, searchTerms) {
  if (tags.length > 0 && !(endpoint.tags || []).some((tag) => contains(String(tag), tags))) return false;
  if (methods.length > 0 && !new Set(methods.map((method) => method.toUpperCase())).has(String(endpoint.method || "").toUpperCase())) return false;
  if (pathTerms.length > 0 && !contains(endpoint.path || "", pathTerms)) return false;
  const haystack = [
    endpoint.method,
    endpoint.path,
    endpoint.summary,
    endpoint.description,
    endpoint.operationId,
    ...(endpoint.tags || []),
  ].join(" ");
  return searchTerms.length === 0 || contains(haystack, searchTerms);
}

function schemaMatches(schema, typeTerms, searchTerms) {
  if (typeTerms.length > 0 && !contains(schema.name || "", typeTerms)) return false;
  const haystack = [schema.name, schema.type, schema.description, ...(schema.schema || [])].join(" ");
  return searchTerms.length === 0 || contains(haystack, searchTerms);
}

function contains(value, needles) {
  const lower = String(value).toLowerCase();
  return needles.some((needle) => lower.includes(String(needle).toLowerCase()));
}

function expandSearchTerms(terms) {
  const output = [];
  const add = (value) => {
    const text = cleanText(value);
    if (text) output.push(text);
  };
  for (const term of terms) {
    add(term);
    for (const piece of String(term).split(/[\s,，/|]+/)) add(piece);
    const lower = String(term).toLowerCase();
    for (const [key, values] of SEARCH_SYNONYMS.entries()) {
      const lowerKey = key.toLowerCase();
      if (lower.includes(lowerKey) || (lower.length >= 2 && lowerKey.includes(lower))) {
        for (const value of values) add(value);
      }
    }
  }
  return stableUnique(output);
}

function renderMarkdown(documents, mode = "document", includeTypes = true, details = false) {
  const parts = ["# API Documentation Summary", ""];
  documents.forEach((document, docIndex) => {
    const multi = documents.length > 1;
    const heading = multi ? `## Spec ${docIndex + 1}: ${document.title || document.source}` : "## Overview";
    parts.push(
      heading,
      "",
      `- Source: ${document.source}`,
      `- Title: ${document.title || "N/A"}`,
      `- Version: ${document.version || "N/A"}`,
      `- Modules: ${document.moduleCount || 0}`,
      `- Endpoints: ${document.endpointCount}`,
      `- Types: ${document.typeCount || 0}`
    );
    if (document.description) parts.push(`- Description: ${document.description}`);
    if (document.baseUrls && document.baseUrls.length > 0) parts.push(`- Base URLs: ${document.baseUrls.map((url) => `\`${url}\``).join(", ")}`);
    const securityNames = Object.keys(document.securitySchemes || {});
    if (securityNames.length > 0) parts.push(`- Security Schemes: ${securityNames.map((name) => `\`${name}\``).join(", ")}`);
    parts.push("");

    const level = multi ? 3 : 2;
    if (mode === "modules") {
      parts.push(...renderModules(document.modules || [], level));
    } else if (mode === "endpoints") {
      parts.push(...renderIndex(document.endpoints, level));
      if (details) parts.push(...renderDetails(document.endpoints, level, document.securitySchemes || {}));
    } else if (mode === "integration") {
      parts.push(...renderIntegration(document, level));
    } else if (mode === "types") {
      parts.push(...renderTypes(document.schemas || [], level));
    } else {
      parts.push(...renderModules(document.modules || [], level));
      parts.push(...renderIndex(document.endpoints, level));
      parts.push(...renderDetails(document.endpoints, level, document.securitySchemes || {}));
      if (includeTypes) parts.push(...renderTypes(document.schemas || [], level));
    }
  });
  return `${parts.join("\n").trimEnd()}\n`;
}

function renderModules(modules, level) {
  const marker = "#".repeat(level);
  const parts = [`${marker} Module List`, ""];
  if (modules.length === 0) return [...parts, "No modules matched.", ""];
  parts.push("| Module | Endpoints | Methods |", "|---|---:|---|");
  for (const module of modules) {
    const methods = Object.entries(module.methods || {})
      .sort()
      .map(([method, count]) => `${method} ${count}`)
      .join(", ");
    parts.push(`| ${escapeTable(module.name || "")} | ${module.endpointCount || 0} | ${escapeTable(methods)} |`);
  }
  parts.push("");
  return parts;
}

function renderIndex(endpoints, level) {
  const marker = "#".repeat(level);
  const parts = [`${marker} Endpoint Index`, ""];
  if (endpoints.length === 0) return [...parts, "No endpoints matched.", ""];
  const byTag = new Map();
  for (const endpoint of endpoints) {
    const tag = String((endpoint.tags || ["default"])[0]);
    if (!byTag.has(tag)) byTag.set(tag, []);
    byTag.get(tag).push(endpoint);
  }
  for (const tag of [...byTag.keys()].sort()) {
    parts.push(`${marker}# ${tag}`, "", "| Method | Path | Summary |", "|---|---|---|");
    for (const endpoint of byTag.get(tag)) {
      parts.push(`| ${endpoint.method} | \`${endpoint.path}\` | ${escapeTable(endpoint.summary || endpoint.description || "")} |`);
    }
    parts.push("");
  }
  return parts;
}

function renderTypes(schemas, level) {
  const marker = "#".repeat(level);
  const parts = [`${marker} Type Definitions`, ""];
  if (schemas.length === 0) return [...parts, "No reusable schemas documented.", ""];
  parts.push("| Type | Kind | Description |", "|---|---|---|");
  for (const schema of schemas) {
    parts.push(`| \`${schema.name}\` | ${escapeTable(schema.type || "")} | ${escapeTable(schema.description || "")} |`);
  }
  parts.push("");
  for (const schema of schemas) {
    parts.push(`${marker}# ${schema.name}`, "");
    if (schema.description) parts.push(`- Description: ${schema.description}`);
    parts.push(`- Type: \`${schema.type || "any"}\``, "");
    for (const line of schema.schema || []) parts.push(line);
    parts.push("");
  }
  return parts;
}

function renderDetails(endpoints, level, securitySchemes = {}) {
  const marker = "#".repeat(level);
  const parts = [`${marker} Endpoint Details`, ""];
  for (const endpoint of endpoints) {
    parts.push(`${marker}# ${endpoint.method} ${endpoint.path}`, "", `- Tag: ${(endpoint.tags || ["default"]).join(", ")}`);
    if (endpoint.summary) parts.push(`- Summary: ${endpoint.summary}`);
    if (endpoint.description) parts.push(`- Description: ${endpoint.description}`);
    if (endpoint.operationId) parts.push(`- Operation ID: \`${endpoint.operationId}\``);
    if (endpoint.deprecated) parts.push("- Deprecated: true");
    parts.push("");
    parts.push(...renderSecurity(endpoint, { securitySchemes }));
    parts.push(...renderRequest(endpoint));
    parts.push(...renderResponse(endpoint));
  }
  return parts;
}

function renderIntegration(document, level) {
  const marker = "#".repeat(level);
  const parts = [`${marker} Integration Guide`, ""];
  const endpoints = document.endpoints || [];
  if (endpoints.length === 0) return [...parts, "No endpoints matched.", ""];

  if (endpoints.length > 1) {
    parts.push("Multiple endpoints matched. Use `--path` and `--method` to narrow the integration target.", "");
    parts.push("| Method | Path | Summary |", "|---|---|---|");
    for (const endpoint of endpoints) {
      parts.push(`| ${endpoint.method} | \`${endpoint.path}\` | ${escapeTable(endpoint.summary || endpoint.description || "")} |`);
    }
    parts.push("");
  }

  for (const endpoint of endpoints) {
    const url = buildEndpointUrl(document, endpoint);
    parts.push(`${marker}# ${endpoint.method} ${endpoint.path}`, "", `- Request URL: \`${endpoint.method} ${url}\``);
    if (endpoint.summary) parts.push(`- Summary: ${endpoint.summary}`);
    if (endpoint.description) parts.push(`- Description: ${endpoint.description}`);
    if (endpoint.operationId) parts.push(`- Operation ID: \`${endpoint.operationId}\``);
    parts.push(...renderSecurity(endpoint, document), ...renderRequest(endpoint), ...renderResponse(endpoint));
    parts.push(...renderCurlExample(endpoint, document), ...renderFetchExample(endpoint, document));
  }
  return parts;
}

function renderSecurity(endpoint, document) {
  const parts = ["#### Auth", ""];
  const requirements = endpoint.security || [];
  if (requirements.length === 0) return [...parts, "- Auth: none documented for this endpoint.", ""];
  const schemes = document.securitySchemes || {};
  for (const requirement of requirements) {
    const labels = requirement.map((item) => {
      const scheme = schemes[item.name] || {};
      const detail = securitySchemeLabel(scheme);
      const scopes = item.scopes && item.scopes.length > 0 ? ` scopes=${item.scopes.join(",")}` : "";
      return `\`${item.name}\`${detail ? ` (${detail}${scopes})` : scopes}`;
    });
    parts.push(`- Auth: ${labels.join(" + ")}`);
  }
  parts.push("");
  return parts;
}

function securitySchemeLabel(scheme) {
  const tokens = [];
  if (scheme.type) tokens.push(scheme.type);
  if (scheme.scheme) tokens.push(scheme.scheme);
  if (scheme.bearerFormat) tokens.push(scheme.bearerFormat);
  if (scheme.in && scheme.name) tokens.push(`${scheme.in} ${scheme.name}`);
  return tokens.join(" ");
}

function renderCurlExample(endpoint, document) {
  const lines = [`curl --request ${endpoint.method} ${shellQuote(buildEndpointUrl(document, endpoint))}`];
  for (const [name, value] of Object.entries(sampleHeaders(endpoint, document))) {
    lines.push(`  --header ${shellQuote(`${name}: ${value}`)}`);
  }
  const body = preferredRequestBody(endpoint);
  if (body) {
    const contentType = body.contentType || "application/json";
    if (!Object.keys(sampleHeaders(endpoint, document)).some((name) => name.toLowerCase() === "content-type")) {
      lines.push(`  --header ${shellQuote(`Content-Type: ${contentType}`)}`);
    }
    lines.push(`  --data ${shellQuote(JSON.stringify(body.example ?? {}, null, 2))}`);
  }
  return ["#### cURL", "", "```bash", lines.join(" \\\n"), "```", ""];
}

function renderFetchExample(endpoint, document) {
  const url = buildEndpointUrl(document, endpoint);
  const headers = sampleHeaders(endpoint, document);
  const body = preferredRequestBody(endpoint);
  if (body && !Object.keys(headers).some((name) => name.toLowerCase() === "content-type")) {
    headers["Content-Type"] = body.contentType || "application/json";
  }

  const options = [`method: ${JSON.stringify(endpoint.method)}`];
  if (Object.keys(headers).length > 0) {
    options.push(`headers: ${formatJsObject(headers, 2)}`);
  }
  if (body) {
    options.push(`body: JSON.stringify(${formatJsObject(body.example ?? {}, 2)})`);
  }
  return [
    "#### fetch",
    "",
    "```js",
    `const response = await fetch(${JSON.stringify(url)}, {`,
    options.map((line) => `  ${line}`).join(",\n"),
    "});",
    "const data = await response.json();",
    "```",
    "",
  ];
}

function preferredRequestBody(endpoint) {
  const bodies = endpoint.requestBody || [];
  return bodies.find((body) => String(body.contentType || "").includes("json")) || bodies[0] || null;
}

function sampleHeaders(endpoint, document) {
  const headers = {};
  const schemes = document.securitySchemes || {};
  const requirement = (endpoint.security || [])[0] || [];
  for (const item of requirement) {
    const scheme = schemes[item.name] || {};
    if (scheme.type === "http" && String(scheme.scheme).toLowerCase() === "bearer") {
      headers.Authorization = "Bearer <token>";
    } else if (scheme.type === "http" && String(scheme.scheme).toLowerCase() === "basic") {
      headers.Authorization = "Basic <base64>";
    } else if (scheme.type === "apiKey" && scheme.in === "header" && scheme.name) {
      headers[scheme.name] = `<${item.name}>`;
    } else if (["oauth2", "openIdConnect"].includes(scheme.type)) {
      headers.Authorization = "Bearer <access_token>";
    }
  }
  return headers;
}

function buildEndpointUrl(document, endpoint) {
  const base = (document.baseUrls || [])[0] || "";
  const pathWithParams = String(endpoint.path || "").replace(/\{([^}]+)\}/g, "<$1>");
  const joined = joinUrl(base, pathWithParams);
  const query = new URLSearchParams();
  for (const parameter of endpoint.parameters || []) {
    if (parameter.in === "query" && parameter.name) {
      query.set(parameter.name, exampleForUrl(parameter.example, parameter.name));
    }
  }
  const schemes = document.securitySchemes || {};
  const requirement = (endpoint.security || [])[0] || [];
  for (const item of requirement) {
    const scheme = schemes[item.name] || {};
    if (scheme.type === "apiKey" && scheme.in === "query" && scheme.name) {
      query.set(scheme.name, `<${item.name}>`);
    }
  }
  const queryText = query.toString();
  return queryText ? `${joined}${joined.includes("?") ? "&" : "?"}${queryText}` : joined;
}

function joinUrl(base, apiPath) {
  if (!base) return apiPath || "/";
  const left = String(base).replace(/\/$/, "");
  const right = String(apiPath || "").replace(/^\//, "");
  return `${left}/${right}`;
}

function exampleForUrl(value, name) {
  if (value === null || value === undefined) return `<${name}>`;
  if (typeof value === "object") return `<${name}>`;
  return String(value);
}

function shellQuote(value) {
  return `'${String(value).replaceAll("'", "'\\''")}'`;
}

function formatJsObject(value, indent = 0) {
  const pad = " ".repeat(indent);
  const childPad = " ".repeat(indent + 2);
  if (!value || typeof value !== "object" || Array.isArray(value)) return JSON.stringify(value);
  const entries = Object.entries(value);
  if (entries.length === 0) return "{}";
  return `{\n${entries.map(([key, child]) => `${childPad}${JSON.stringify(key)}: ${formatJsObject(child, indent + 2)}`).join(",\n")}\n${pad}}`;
}

function renderRequest(endpoint) {
  const parts = ["#### Request", ""];
  const params = endpoint.parameters || [];
  const requestBody = endpoint.requestBody || [];
  if (params.length === 0 && requestBody.length === 0) return [...parts, "No documented request parameters or body.", ""];

  if (params.length > 0) {
    const grouped = new Map();
    for (const parameter of params) {
      const location = parameter.in || "unknown";
      if (!grouped.has(location)) grouped.set(location, []);
      grouped.get(location).push(parameter);
    }
    for (const location of [...grouped.keys()].sort()) {
      parts.push(`**${location} parameters**`, "", "| Name | Type | Required | Description |", "|---|---|---|---|");
      for (const parameter of grouped.get(location)) {
        parts.push(
          `| \`${parameter.name}\` | ${parameter.type} | ${parameter.required ? "yes" : "no"} | ${escapeTable(parameter.description || "")} |`
        );
      }
      parts.push("");
    }
  }

  if (requestBody.length > 0) {
    parts.push("**Request body**", "");
    for (const body of requestBody) {
      parts.push(`- Content-Type: \`${body.contentType}\`; type: \`${body.type}\`; required: ${body.required ? "yes" : "no"}`);
      if (body.description) parts.push(`  - Description: ${body.description}`);
      for (const line of body.schema || []) parts.push(`  ${line}`);
      parts.push("");
    }
  }
  return parts;
}

function renderResponse(endpoint) {
  const parts = ["#### Response", ""];
  const responses = endpoint.responses || [];
  if (responses.length === 0) return [...parts, "No documented responses.", ""];
  for (const response of responses) {
    parts.push(`- \`${response.status}\`${response.description ? `: ${response.description}` : ""}`);
    if (!response.content || response.content.length === 0) parts.push("  - No response schema documented.");
    for (const content of response.content || []) {
      parts.push(`  - Content-Type: \`${content.contentType}\`; type: \`${content.type}\``);
      for (const line of content.schema || []) parts.push(`    ${line}`);
    }
    parts.push("");
  }
  return parts;
}

function escapeTable(value) {
  return cleanText(value).replaceAll("|", "\\|");
}

async function buildDocuments(args) {
  const specs = await loadSpecs(args);
  return specs.map((item) => {
    const document = extractEndpoints(item.spec, item.url, args.includeDeprecated);
    document.schemas = extractSchemas(item.spec);
    return applyFilters(document, args);
  });
}

async function loadSpecs(args) {
  const cachePath = args.cache ? path.resolve(args.cache) : "";
  const normalizedInput = normalizeCacheInput(args.url);
  if (cachePath && !args.refreshCache && fs.existsSync(cachePath)) {
    const cached = readSpecCache(cachePath);
    if (!cached.inputUrl || cached.inputUrl === normalizedInput || cached.rawInput === args.url || cached.url === args.url) {
      return cached.specs;
    }
  }

  const specs = await discoverSpecs(
    args.url,
    parseHeaders(args.header, args.configHeaders),
    args.timeout,
    args.insecure,
    args.verbose
  );
  if (cachePath) writeSpecCache(cachePath, normalizedInput, args.url, specs);
  return specs;
}

function normalizeCacheInput(value) {
  try {
    return stripFragment(normalizeInputUrl(value));
  } catch {
    return String(value);
  }
}

function readSpecCache(cachePath) {
  let cache;
  try {
    cache = JSON.parse(fs.readFileSync(cachePath, "utf8"));
  } catch (error) {
    throw new ExtractionError(`Could not read cache file ${cachePath}: ${error.message}`);
  }
  const specs = Array.isArray(cache?.specs) ? cache.specs : [];
  if (specs.length === 0 || specs.some((item) => !item || typeof item.url !== "string" || !item.spec)) {
    throw new ExtractionError(`Cache file ${cachePath} does not contain cached Swagger/OpenAPI specs.`);
  }
  return { inputUrl: cache.inputUrl || "", rawInput: cache.rawInput || "", url: cache.url || "", specs };
}

function writeSpecCache(cachePath, inputUrl, rawInput, specs) {
  fs.mkdirSync(path.dirname(cachePath), { recursive: true });
  fs.writeFileSync(
    cachePath,
    JSON.stringify(
      {
        inputUrl,
        rawInput,
        cachedAt: new Date().toISOString(),
        specs,
      },
      null,
      2
    ),
    "utf8"
  );
}

function selectJsonPayload(documents, mode) {
  if (mode === "modules") {
    return documents.map((document) => ({
      source: document.source,
      title: document.title,
      version: document.version,
      moduleCount: document.moduleCount,
      modules: document.modules,
    }));
  }
  if (mode === "endpoints" || mode === "integration") {
    return documents.map((document) => ({
      source: document.source,
      title: document.title,
      version: document.version,
      baseUrls: document.baseUrls,
      securitySchemes: document.securitySchemes,
      endpointCount: document.endpointCount,
      endpoints: document.endpoints,
    }));
  }
  if (mode === "types") {
    return documents.map((document) => ({
      source: document.source,
      title: document.title,
      version: document.version,
      typeCount: document.typeCount,
      schemas: document.schemas,
    }));
  }
  return documents;
}

function renderSuccessSummary(documents, args) {
  const totals = documents.reduce(
    (acc, document) => {
      acc.modules += document.moduleCount || 0;
      acc.endpoints += document.endpointCount || 0;
      acc.types += document.typeCount || 0;
      return acc;
    },
    { modules: 0, endpoints: 0, types: 0 }
  );

  return [
    "Parsed Swagger/OpenAPI document successfully.",
    `Output: ${path.resolve(args.output)}`,
    `Mode: ${args.mode}`,
    `Format: ${args.format}`,
    `Sources: ${documents.length}`,
    `Modules: ${totals.modules}`,
    `Endpoints: ${totals.endpoints}`,
    `Types: ${totals.types}`,
    "",
  ].join("\n");
}

function htmlDecode(value) {
  return value
    .replaceAll("&amp;", "&")
    .replaceAll("&quot;", "\"")
    .replaceAll("&#39;", "'")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">");
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const documents = await buildDocuments(args);
  const output =
    args.format === "json"
      ? `${JSON.stringify(selectJsonPayload(documents, args.mode), null, 2)}\n`
      : renderMarkdown(documents, args.mode, !args.noTypes, args.details);

  if (args.output) {
    fs.writeFileSync(args.output, output, "utf8");
    process.stdout.write(renderSuccessSummary(documents, args));
  } else {
    process.stdout.write(output);
  }
}

main().catch((error) => {
  console.error(`error: ${error.message || error}`);
  process.exit(1);
});
