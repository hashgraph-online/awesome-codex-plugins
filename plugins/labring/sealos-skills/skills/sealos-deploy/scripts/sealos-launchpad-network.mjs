#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import process from "node:process";
import { pathToFileURL } from "node:url";

const ALLOWED_ARGS = new Set(["app", "app-url", "expected-port", "region", "kubeconfig"]);
const REQUEST_TIMEOUT_MS = 15000;

class InputError extends Error {}

export function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) {
      throw new InputError(`unexpected argument: ${token}`);
    }
    const key = token.slice(2);
    if (!ALLOWED_ARGS.has(key)) {
      throw new InputError(`unknown option: --${key}`);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) {
      throw new InputError(`missing value for --${key}`);
    }
    args[key] = value;
    index += 1;
  }

  if (!args.app?.trim()) {
    throw new InputError("usage: node sealos-launchpad-network.mjs --app <app-name> --app-url <url> [--expected-port <port>] [--region <url>] [--kubeconfig <path>]");
  }

  if (!args["app-url"]) {
    throw new InputError("--app-url is required");
  }
  try {
    const url = new URL(args["app-url"]);
    if (!url.hostname) {
      throw new Error("missing hostname");
    }
  } catch {
    throw new InputError("--app-url must be an absolute URL with a hostname");
  }

  if (args["expected-port"]) {
    const port = Number(args["expected-port"]);
    if (!Number.isInteger(port) || port < 1 || port > 65535) {
      throw new InputError("--expected-port must be an integer between 1 and 65535");
    }
    args["expected-port"] = port;
  }

  return {
    app: args.app.trim(),
    appUrl: args["app-url"],
    expectedPort: args["expected-port"] ?? null,
    region: args.region || null,
    kubeconfig: args.kubeconfig || null,
  };
}

function stringValue(value) {
  return typeof value === "string" ? value.trim() : "";
}

function hostFromDomain(value) {
  const text = stringValue(value);
  if (!text) {
    return null;
  }
  try {
    return new URL(text.includes("://") ? text : `https://${text}`).hostname.toLowerCase();
  } catch {
    return null;
  }
}

export function normalizeNetwork(raw) {
  const publicDomain = stringValue(raw?.publicDomain);
  const customDomain = stringValue(raw?.customDomain);
  const domain = stringValue(raw?.domain);
  const publicHost = publicDomain && domain ? hostFromDomain(`${publicDomain}.${domain}`) : null;
  const customHost = hostFromDomain(customDomain);
  const hosts = [...new Set([publicHost, customHost].filter(Boolean))];

  return {
    serviceName: stringValue(raw?.serviceName),
    networkName: stringValue(raw?.networkName),
    portName: stringValue(raw?.portName),
    port: Number.isInteger(raw?.port) ? raw.port : null,
    protocol: stringValue(raw?.protocol),
    appProtocol: stringValue(raw?.appProtocol),
    openPublicDomain: raw?.openPublicDomain === true,
    publicDomain,
    customDomain,
    domain,
    hosts,
  };
}

export function evaluateLaunchpadResponse({ body, httpStatus, appUrl, expectedPort }) {
  const apiCode = Number.isInteger(body?.code) ? body.code : null;
  const rawNetworks = Array.isArray(body?.data?.networks) ? body.data.networks : [];
  const networks = rawNetworks.map(normalizeNetwork);
  const findings = [];

  if (httpStatus < 200 || httpStatus >= 300) {
    findings.push({
      code: "launchpad_http_error",
      message: `Launchpad API returned HTTP ${httpStatus}`,
    });
  } else if (apiCode !== 200) {
    findings.push({
      code: "launchpad_api_error",
      message: `Launchpad API returned code ${apiCode ?? "unknown"}`,
    });
  }

  const publicNetworks = networks.filter(
    (network) => network.openPublicDomain && network.hosts.length > 0,
  );
  if (apiCode === 200 && publicNetworks.length === 0) {
    findings.push({
      code: "public_network_missing",
      message: "Launchpad returned no public network with a complete domain",
    });
  }

  const portNetworks = expectedPort === null
    ? publicNetworks
    : publicNetworks.filter((network) => network.port === expectedPort);
  if (apiCode === 200 && publicNetworks.length > 0 && expectedPort !== null && portNetworks.length === 0) {
    findings.push({
      code: "expected_port_missing",
      message: `Launchpad returned no public network on expected port ${expectedPort}`,
    });
  }

  if (apiCode === 200 && portNetworks.length > 0 && appUrl) {
    const appHost = new URL(appUrl).hostname.toLowerCase();
    const hostMatches = portNetworks.some((network) => network.hosts.includes(appHost));
    if (!hostMatches) {
      findings.push({
        code: "app_url_host_mismatch",
        message: `App URL host ${appHost} does not match the Launchpad public network`,
      });
    }
  }

  return { apiCode, networks, findings };
}

function readContext(options, dependencies) {
  const homeDir = dependencies.homeDir || homedir();
  const env = dependencies.env || process.env;
  const readText = dependencies.readFileText || ((path) => readFileSync(path, "utf8"));
  let region = options.region;

  if (!region) {
    const authPath = join(homeDir, ".sealos", "auth.json");
    let auth;
    try {
      auth = JSON.parse(readText(authPath));
    } catch {
      throw new InputError(`unable to read Sealos auth config at ${authPath}`);
    }
    region = auth?.region;
  }

  let regionUrl;
  try {
    regionUrl = new URL(region);
    if (!regionUrl.hostname) {
      throw new Error("missing hostname");
    }
  } catch {
    throw new InputError("Sealos region must be an absolute URL with a hostname");
  }

  const kubeconfigPath = options.kubeconfig || env.KUBECONFIG || join(homeDir, ".sealos", "kubeconfig");
  let kubeconfig;
  try {
    kubeconfig = readText(kubeconfigPath);
  } catch {
    throw new InputError(`unable to read Sealos kubeconfig at ${kubeconfigPath}`);
  }
  if (!kubeconfig.trim()) {
    throw new InputError(`Sealos kubeconfig is empty at ${kubeconfigPath}`);
  }

  const endpoint = new URL(`https://applaunchpad.${regionUrl.host}/api/getAppByAppName`);
  endpoint.searchParams.set("appName", options.app);
  return { endpoint, kubeconfig };
}

export async function runLaunchpadNetworkCheck(options, dependencies = {}) {
  const { endpoint, kubeconfig } = readContext(options, dependencies);
  const fetchImpl = dependencies.fetchImpl || fetch;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  let response;

  try {
    response = await fetchImpl(endpoint, {
      headers: { Authorization: encodeURIComponent(kubeconfig) },
      signal: controller.signal,
    });
  } catch (error) {
    const message = error?.name === "AbortError"
      ? "Launchpad API request timed out"
      : "Launchpad API request failed";
    return {
      ok: false,
      app: options.app,
      apiCode: null,
      networks: [],
      findings: [{ code: "launchpad_request_failed", message }],
    };
  } finally {
    clearTimeout(timeout);
  }

  let body;
  try {
    body = await response.json();
  } catch {
    return {
      ok: false,
      app: options.app,
      apiCode: null,
      networks: [],
      findings: [{ code: "launchpad_invalid_json", message: "Launchpad API returned invalid JSON" }],
    };
  }

  const evaluated = evaluateLaunchpadResponse({
    body,
    httpStatus: response.status,
    appUrl: options.appUrl,
    expectedPort: options.expectedPort,
  });
  return {
    ok: evaluated.findings.length === 0,
    app: options.app,
    apiCode: evaluated.apiCode,
    networks: evaluated.networks,
    findings: evaluated.findings,
  };
}

function inputErrorReport(app, error) {
  return {
    ok: false,
    app: app || null,
    apiCode: null,
    networks: [],
    findings: [{ code: "input_error", message: error.message }],
  };
}

export async function main(argv, dependencies = {}) {
  let options;
  try {
    options = parseArgs(argv);
    const report = await runLaunchpadNetworkCheck(options, dependencies);
    return { exitCode: report.ok ? 0 : 1, report };
  } catch (error) {
    if (error instanceof InputError) {
      return { exitCode: 2, report: inputErrorReport(options?.app, error) };
    }
    throw error;
  }
}

const isMain = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  const { exitCode, report } = await main(process.argv.slice(2));
  console.log(JSON.stringify(report, null, 2));
  process.exitCode = exitCode;
}
