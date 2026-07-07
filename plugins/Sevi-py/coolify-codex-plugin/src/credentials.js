import { execFileSync } from "node:child_process";
import { chmodSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { resolve } from "node:path";

export const DEFAULT_COOLIFY_BASE_URL = "https://app.coolify.io";

const KEYCHAIN_SERVICE = "coolify-codex-plugin";
const KEYCHAIN_ACCOUNT = "default";
const WINDOWS_CREDENTIAL_TARGET = `${KEYCHAIN_SERVICE}:${KEYCHAIN_ACCOUNT}`;
const SECRET_SERVICE_LABEL = "Coolify Codex Plugin";
const NATIVE_CREDENTIAL_TIMEOUT_MS = 10000;
const NATIVE_TOKEN_STORES = new Set([
  "keychain",
  "windows-credential-manager",
  "secret-service"
]);

export function normalizeBaseUrl(value) {
  const raw = (value || DEFAULT_COOLIFY_BASE_URL).trim().replace(/\/+$/, "");
  if (!raw) {
    throw new Error("A Coolify base URL is required.");
  }
  const url = new URL(raw);
  if (!["http:", "https:"].includes(url.protocol)) {
    throw new Error("The Coolify base URL must start with http:// or https://.");
  }
  const base = url.toString().replace(/\/+$/, "");
  const apiBase = base.endsWith("/api/v1") ? base : `${base}/api/v1`;
  const rootBase = base.endsWith("/api/v1") ? base.slice(0, -"/api/v1".length) : base;
  return { apiBase, rootBase };
}

export function credentialPaths() {
  const codexHome = process.env.CODEX_HOME || resolve(homedir(), ".codex");
  const configDir = resolve(codexHome, "coolify");
  return {
    codexHome,
    configDir,
    configPath: resolve(configDir, "config.json")
  };
}

export function loadCredentials({ requireToken = true } = {}) {
  const stored = readConfigFile();
  const baseUrl = stored.baseUrl || process.env.COOLIFY_BASE_URL || DEFAULT_COOLIFY_BASE_URL;
  const cfg = normalizeBaseUrl(baseUrl);
  const tokenInfo = resolveToken(stored);

  if (requireToken && !tokenInfo.token) {
    throw new Error("Coolify is not connected. Run coolify_configure with a scoped API token, or run npm run setup -- --save.");
  }

  return {
    ...cfg,
    token: tokenInfo.token,
    tokenSource: tokenInfo.source,
    configPath: credentialPaths().configPath
  };
}

export function saveCredentials({ baseUrl, apiToken } = {}) {
  const current = readConfigFile();
  const cfg = normalizeBaseUrl(baseUrl || current.baseUrl || process.env.COOLIFY_BASE_URL || DEFAULT_COOLIFY_BASE_URL);
  const next = {
    version: 1,
    baseUrl: cfg.rootBase
  };

  const cleanToken = typeof apiToken === "string" ? apiToken.trim() : "";
  if (cleanToken) {
    const nativeTokenStore = saveNativeToken(cleanToken);
    if (nativeTokenStore) {
      if (NATIVE_TOKEN_STORES.has(current.tokenStore) && current.tokenStore !== nativeTokenStore) {
        deleteNativeToken(current.tokenStore);
      }
      next.tokenStore = nativeTokenStore;
    } else {
      if (NATIVE_TOKEN_STORES.has(current.tokenStore)) {
        deleteNativeToken(current.tokenStore);
      }
      next.tokenStore = "file";
      next.apiToken = cleanToken;
    }
  } else if (NATIVE_TOKEN_STORES.has(current.tokenStore)) {
    next.tokenStore = current.tokenStore;
  } else if (current.apiToken) {
    next.tokenStore = "file";
    next.apiToken = current.apiToken;
  }

  writeConfigFile(next);
  return credentialStatus();
}

export function credentialStatus() {
  const cfg = loadCredentials({ requireToken: false });
  const stored = readConfigFile();
  return {
    configured: Boolean(cfg.token),
    baseUrl: cfg.rootBase,
    apiBaseUrl: cfg.apiBase,
    tokenSource: cfg.tokenSource || null,
    storage: stored.tokenStore || null,
    configPath: cfg.configPath,
    tokenUrl: `${cfg.rootBase}/security/api-tokens`,
    apiSettingsUrl: `${cfg.rootBase}/settings/advanced`,
    envFallbackPresent: Boolean(process.env.COOLIFY_API_TOKEN)
  };
}

export function clearStoredCredentials() {
  const stored = readConfigFile();
  if (NATIVE_TOKEN_STORES.has(stored.tokenStore)) {
    deleteNativeToken(stored.tokenStore);
  }
  const { configPath } = credentialPaths();
  try {
    rmSync(configPath, { force: true });
  } catch {
    // Nothing to clear.
  }
  return credentialStatus();
}

function readConfigFile() {
  const { configPath } = credentialPaths();
  try {
    return JSON.parse(readFileSync(configPath, "utf8"));
  } catch (error) {
    if (error.code === "ENOENT") {
      return {};
    }
    throw new Error(`Could not read Coolify connection settings: ${error.message}`);
  }
}

function writeConfigFile(value) {
  const { configDir, configPath } = credentialPaths();
  mkdirSync(configDir, { recursive: true, mode: 0o700 });
  chmodSync(configDir, 0o700);
  writeFileSync(configPath, `${JSON.stringify(value, null, 2)}\n`, { mode: 0o600 });
  chmodSync(configPath, 0o600);
}

function resolveToken(stored) {
  if (NATIVE_TOKEN_STORES.has(stored.tokenStore)) {
    const token = readNativeToken(stored.tokenStore);
    if (token) {
      return { token, source: stored.tokenStore };
    }
  }
  if (typeof stored.apiToken === "string" && stored.apiToken.trim()) {
    return { token: stored.apiToken.trim(), source: "file" };
  }
  if (process.env.COOLIFY_API_TOKEN && process.env.COOLIFY_API_TOKEN.trim()) {
    return { token: process.env.COOLIFY_API_TOKEN.trim(), source: "environment" };
  }
  return { token: "", source: null };
}

function saveNativeToken(token) {
  if (process.platform === "darwin" && saveKeychainToken(token)) {
    return "keychain";
  }
  if (process.platform === "win32" && saveWindowsCredentialToken(token)) {
    return "windows-credential-manager";
  }
  if (process.platform === "linux" && saveSecretServiceToken(token)) {
    return "secret-service";
  }
  return null;
}

function readNativeToken(tokenStore) {
  if (tokenStore === "keychain") {
    return readKeychainToken();
  }
  if (tokenStore === "windows-credential-manager") {
    return readWindowsCredentialToken();
  }
  if (tokenStore === "secret-service") {
    return readSecretServiceToken();
  }
  return "";
}

function deleteNativeToken(tokenStore) {
  if (tokenStore === "keychain") {
    deleteKeychainToken();
  } else if (tokenStore === "windows-credential-manager") {
    deleteWindowsCredentialToken();
  } else if (tokenStore === "secret-service") {
    deleteSecretServiceToken();
  }
}

function saveKeychainToken(token) {
  if (process.platform !== "darwin") {
    return false;
  }
  try {
    deleteKeychainToken();
    execFileSync("security", [
      "add-generic-password",
      "-U",
      "-s",
      KEYCHAIN_SERVICE,
      "-a",
      KEYCHAIN_ACCOUNT,
      "-w",
      token
    ], { stdio: "ignore", timeout: NATIVE_CREDENTIAL_TIMEOUT_MS });
    return true;
  } catch {
    return false;
  }
}

function saveWindowsCredentialToken(token) {
  if (process.platform !== "win32") {
    return false;
  }
  try {
    runWindowsCredentialScript(windowsCredentialWriteScript(), {
      target: WINDOWS_CREDENTIAL_TARGET,
      account: KEYCHAIN_ACCOUNT,
      token
    });
    return true;
  } catch {
    return false;
  }
}

function readWindowsCredentialToken() {
  if (process.platform !== "win32") {
    return "";
  }
  try {
    return runWindowsCredentialScript(windowsCredentialReadScript(), {
      target: WINDOWS_CREDENTIAL_TARGET
    }, { encoding: "utf8" }).trim();
  } catch {
    return "";
  }
}

function deleteWindowsCredentialToken() {
  if (process.platform !== "win32") {
    return;
  }
  try {
    runWindowsCredentialScript(windowsCredentialDeleteScript(), {
      target: WINDOWS_CREDENTIAL_TARGET
    });
  } catch {
    // The credential may not exist yet, or Credential Manager may be unavailable.
  }
}

function runWindowsCredentialScript(script, payload, options = {}) {
  const encodedScript = Buffer.from(script, "utf16le").toString("base64");
  const commandArgs = [
    "-NoProfile",
    "-NonInteractive",
    "-ExecutionPolicy",
    "Bypass",
    "-EncodedCommand",
    encodedScript
  ];
  const execOptions = {
    input: JSON.stringify(payload),
    stdio: ["pipe", options.encoding ? "pipe" : "ignore", "ignore"],
    timeout: NATIVE_CREDENTIAL_TIMEOUT_MS
  };
  if (options.encoding) {
    execOptions.encoding = options.encoding;
  }
  const commands = ["powershell.exe", "pwsh.exe"];
  let lastError;
  for (const command of commands) {
    try {
      return execFileSync(command, commandArgs, execOptions);
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError;
}

function windowsCredentialScript(body) {
  return `$ErrorActionPreference = "Stop"
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;

public static class NativeCredential {
  [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
  public struct CREDENTIAL {
    public UInt32 Flags;
    public UInt32 Type;
    public string TargetName;
    public string Comment;
    public FILETIME LastWritten;
    public UInt32 CredentialBlobSize;
    public IntPtr CredentialBlob;
    public UInt32 Persist;
    public UInt32 AttributeCount;
    public IntPtr Attributes;
    public string TargetAlias;
    public string UserName;
  }

  [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
  public static extern bool CredWrite(ref CREDENTIAL credential, UInt32 flags);

  [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
  public static extern bool CredRead(string target, UInt32 type, UInt32 reservedFlag, out IntPtr credentialPtr);

  [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
  public static extern bool CredDelete(string target, UInt32 type, UInt32 flags);

  [DllImport("advapi32.dll", SetLastError = true)]
  public static extern void CredFree(IntPtr buffer);
}
"@
${body}`;
}

function windowsCredentialWriteScript() {
  return windowsCredentialScript(`$payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
$bytes = [Text.Encoding]::Unicode.GetBytes([string]$payload.token)
$blob = [Runtime.InteropServices.Marshal]::AllocCoTaskMem($bytes.Length)
try {
  [Runtime.InteropServices.Marshal]::Copy($bytes, 0, $blob, $bytes.Length)
  $credential = New-Object NativeCredential+CREDENTIAL
  $credential.Type = 1
  $credential.TargetName = [string]$payload.target
  $credential.UserName = [string]$payload.account
  $credential.CredentialBlobSize = $bytes.Length
  $credential.CredentialBlob = $blob
  $credential.Persist = 2
  $ok = [NativeCredential]::CredWrite([ref]$credential, 0)
  if (-not $ok) {
    $errorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
    throw (New-Object System.ComponentModel.Win32Exception($errorCode))
  }
} finally {
  [Runtime.InteropServices.Marshal]::FreeCoTaskMem($blob)
}`);
}

function windowsCredentialReadScript() {
  return windowsCredentialScript(`$payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
$ptr = [IntPtr]::Zero
$ok = [NativeCredential]::CredRead([string]$payload.target, 1, 0, [ref]$ptr)
if (-not $ok) {
  exit 1
}
try {
  $credential = [Runtime.InteropServices.Marshal]::PtrToStructure($ptr, [type][NativeCredential+CREDENTIAL])
  if ($credential.CredentialBlobSize -gt 0) {
    $bytes = New-Object byte[] $credential.CredentialBlobSize
    [Runtime.InteropServices.Marshal]::Copy($credential.CredentialBlob, $bytes, 0, $bytes.Length)
    [Console]::Out.Write([Text.Encoding]::Unicode.GetString($bytes))
  }
} finally {
  [NativeCredential]::CredFree($ptr)
}`);
}

function windowsCredentialDeleteScript() {
  return windowsCredentialScript(`$payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
$ok = [NativeCredential]::CredDelete([string]$payload.target, 1, 0)
if (-not $ok) {
  $errorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
  if ($errorCode -ne 1168) {
    throw (New-Object System.ComponentModel.Win32Exception($errorCode))
  }
}`);
}

function saveSecretServiceToken(token) {
  try {
    execFileSync("secret-tool", [
      "store",
      "--label",
      SECRET_SERVICE_LABEL,
      "service",
      KEYCHAIN_SERVICE,
      "account",
      KEYCHAIN_ACCOUNT
    ], {
      input: token,
      stdio: ["pipe", "ignore", "ignore"],
      timeout: NATIVE_CREDENTIAL_TIMEOUT_MS
    });
    return true;
  } catch {
    return false;
  }
}

function readSecretServiceToken() {
  try {
    return execFileSync("secret-tool", [
      "lookup",
      "service",
      KEYCHAIN_SERVICE,
      "account",
      KEYCHAIN_ACCOUNT
    ], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
      timeout: NATIVE_CREDENTIAL_TIMEOUT_MS
    }).trim();
  } catch {
    return "";
  }
}

function deleteSecretServiceToken() {
  try {
    execFileSync("secret-tool", [
      "clear",
      "service",
      KEYCHAIN_SERVICE,
      "account",
      KEYCHAIN_ACCOUNT
    ], { stdio: "ignore", timeout: NATIVE_CREDENTIAL_TIMEOUT_MS });
  } catch {
    // The Secret Service item may not exist yet, or secret-tool may be unavailable.
  }
}

function readKeychainToken() {
  if (process.platform !== "darwin") {
    return "";
  }
  try {
    return execFileSync("security", [
      "find-generic-password",
      "-w",
      "-s",
      KEYCHAIN_SERVICE,
      "-a",
      KEYCHAIN_ACCOUNT
    ], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
      timeout: NATIVE_CREDENTIAL_TIMEOUT_MS
    }).trim();
  } catch {
    return "";
  }
}

function deleteKeychainToken() {
  if (process.platform !== "darwin") {
    return;
  }
  try {
    execFileSync("security", [
      "delete-generic-password",
      "-s",
      KEYCHAIN_SERVICE,
      "-a",
      KEYCHAIN_ACCOUNT
    ], { stdio: "ignore", timeout: NATIVE_CREDENTIAL_TIMEOUT_MS });
  } catch {
    // The keychain item may not exist yet.
  }
}
