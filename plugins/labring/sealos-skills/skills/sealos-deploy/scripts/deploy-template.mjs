#!/usr/bin/env node

/**
 * Sealos Template Deploy
 *
 * Usage:
 *   node deploy-template.mjs <template-path> [--dry-run]
 *   node deploy-template.mjs <template-path> --args-file ./args.json
 *   node deploy-template.mjs <template-path> --args-json '{"PUBLIC_FLAG":"true"}'
 *
 * Behavior:
 *   - Local mode reads ~/.sealos/auth.json and ~/.sealos/kubeconfig
 *   - Managed mode derives the region from the injected kubeconfig and reads
 *     deployment arguments only from SEALAI_INPUTS_PATH
 *   - Sends the selected kubeconfig as encodeURIComponent(kubeconfig)
 *   - Posts the template YAML to:
 *       https://template.<region-domain>/api/v2alpha/templates/raw
 *   - Prints a JSON result to stdout with submitted argument values redacted
 */

import { existsSync, readFileSync, statSync } from 'fs'
import { homedir } from 'os'
import { basename, join, resolve } from 'path'

const SEALOS_DIR = join(homedir(), '.sealos')
const AUTH_PATH = join(SEALOS_DIR, 'auth.json')
const KUBECONFIG_PATH = join(SEALOS_DIR, 'kubeconfig')
const MANAGED_MODE = process.env.SEALAI_DEPLOY_MODE === 'managed'
const MANAGED_INPUTS_PATH = '/run/sealai/deployment/inputs.json'

function fail(message, extra = {}, code = 1) {
  console.error(JSON.stringify({ error: message, ...extra }, null, 2))
  process.exit(code)
}

function parseArgs(argv) {
  const args = argv.slice(2)
  let templatePath = null
  let dryRun = false
  let argsJson = null
  let argsFile = null

  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i]
    if (arg === '--dry-run') {
      dryRun = true
      continue
    }
    if (arg === '--args-json') {
      if (i + 1 >= args.length || args[i + 1].startsWith('--')) {
        fail('--args-json requires a JSON object value')
      }
      argsJson = args[i + 1]
      i += 1
      continue
    }
    if (arg === '--args-file') {
      if (i + 1 >= args.length || args[i + 1].startsWith('--')) {
        fail('--args-file requires a path')
      }
      argsFile = args[i + 1]
      i += 1
      continue
    }
    if (arg === '--help' || arg === '-h') {
      printHelp()
      process.exit(0)
    }
    if (arg.startsWith('--')) {
      fail('Unknown option')
    }
    if (!templatePath) {
      templatePath = arg
      continue
    }
    // Use a fixed diagnostic because an unexpected positional value may be a
    // credential supplied with an incorrect option.
    fail('Unexpected argument after template path')
  }

  if (!templatePath) {
    fail('Missing template path. Run with --help for usage.')
  }

  if (argsJson !== null && argsFile !== null) {
    fail('Use only one of --args-json or --args-file')
  }

  if (MANAGED_MODE && argsJson) {
    fail('Managed deployment arguments must be read from the fixed private input file')
  }

  return {
    templatePath: resolve(process.cwd(), templatePath),
    dryRun,
    argsJson,
    argsFile: argsFile ? resolve(process.cwd(), argsFile) : null,
  }
}

function printHelp() {
  console.log(`Sealos Template Deploy

Usage:
  node deploy-template.mjs <template-path> [--dry-run]
  node deploy-template.mjs <template-path> --args-file ./args.json
  node deploy-template.mjs <template-path> --args-json '{"PUBLIC_FLAG":"true"}'

Use a mode-0600 --args-file for passwords, tokens, API keys, or any other
sensitive value. --args-json is only for values confirmed to be non-sensitive.

Examples:
  node deploy-template.mjs .sealos/template/index.yaml --dry-run
  node deploy-template.mjs template/myapp/index.yaml
`)
}

function loadJson(filePath, label) {
  if (!existsSync(filePath)) {
    fail(`${label} not found`, { path: filePath })
  }

  try {
    return JSON.parse(readFileSync(filePath, 'utf8'))
  } catch {
    fail(`Failed to parse ${label}`, { path: filePath })
  }
}

function normalizeRegion(region) {
  const text = String(region || '').trim()
  if (!text) {
    fail('Auth file is missing region', { path: AUTH_PATH })
  }

  const normalized = text.replace(/\/+$/, '')
  let url
  try {
    url = new URL(normalized)
  } catch (error) {
    fail('Invalid region URL in auth file', { region: text, details: error.message })
  }

  return {
    region: url.toString().replace(/\/+$/, ''),
    regionDomain: url.host,
    deployUrl: `https://template.${url.host}/api/v2alpha/templates/raw`,
  }
}

function resolveManagedRegion(kubeconfig) {
  const match = String(kubeconfig).match(/^\s*server:\s*["']?([^"'\s]+)["']?\s*$/m)
  if (!match) {
    fail('Managed kubeconfig does not contain a cluster API server.')
  }

  let server
  try {
    server = new URL(match[1])
  } catch {
    fail('Managed kubeconfig contains an invalid cluster API server.')
  }
  if (!server.hostname) {
    fail('Managed kubeconfig API server does not contain a hostname.')
  }
  return normalizeRegion(`${server.protocol}//${server.hostname}`)
}

function loadTemplate(templatePath) {
  if (!existsSync(templatePath)) {
    fail('Template file not found', { path: templatePath })
  }

  if (!/\.ya?ml$/i.test(basename(templatePath))) {
    fail('Template path must point to a YAML file', { path: templatePath })
  }

  return readFileSync(templatePath, 'utf8')
}

function loadDeployArgs({ argsJson, argsFile }) {
  if (argsJson !== null) {
    try {
      const parsed = JSON.parse(argsJson)
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        fail('--args-json must be a JSON object')
      }
      return parsed
    } catch {
      // JSON parser errors can quote the submitted input. Template arguments may
      // contain credentials, so never include parser details in diagnostics.
      fail('Failed to parse --args-json')
    }
  }

  if (argsFile) {
    if (!existsSync(argsFile)) {
      fail('Args file not found', { path: argsFile })
    }

    let argsFileStats
    try {
      argsFileStats = statSync(argsFile)
    } catch {
      fail('Failed to inspect args file', { path: argsFile })
    }
    if (!argsFileStats.isFile()) {
      fail('Args file must be a regular file', { path: argsFile })
    }
    if (process.platform !== 'win32' && (argsFileStats.mode & 0o077) !== 0) {
      fail('Args file must not grant access to group or other users', { path: argsFile })
    }

    let parsed
    try {
      parsed = JSON.parse(readFileSync(argsFile, 'utf8'))
    } catch {
      // As above, omit parser details because they may contain argument values.
      fail('Failed to parse args file', { path: argsFile })
    }

    if (MANAGED_MODE && resolve(argsFile) !== MANAGED_INPUTS_PATH) {
      fail(`Managed deployment must read ${MANAGED_INPUTS_PATH}`, { path: resolve(argsFile) })
    }
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      fail('Args file must contain a JSON object', { path: argsFile })
    }
    return parsed
  }

  if (MANAGED_MODE) {
    const inputPath = process.env.SEALAI_INPUTS_PATH
    if (inputPath !== MANAGED_INPUTS_PATH) {
      fail(`Managed deployment must use ${MANAGED_INPUTS_PATH}`, { path: inputPath || null })
    }
    if (existsSync(MANAGED_INPUTS_PATH)) {
      const parsed = loadJson(MANAGED_INPUTS_PATH, 'managed input file')
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        fail('Managed input file must contain a JSON object', { path: MANAGED_INPUTS_PATH })
      }
      return parsed
    }
  }

  return {}
}

function createResponseSanitizer(args) {
  const exactValues = []
  const longStringValues = new Set()

  function collect(value) {
    if (Array.isArray(value)) {
      value.forEach(collect)
      return
    }

    if (value && typeof value === 'object') {
      Object.values(value).forEach(collect)
      return
    }

    exactValues.push(value)
    if (typeof value === 'string' && value.length >= 4) {
      longStringValues.add(value)
    }
  }

  Object.values(args).forEach(collect)

  const fragments = [...longStringValues].sort((left, right) => right.length - left.length)
  const marker = '<redacted>'

  function isExactValue(value) {
    return exactValues.some((candidate) => Object.is(candidate, value))
  }

  function sanitizeScalar(value) {
    if (isExactValue(value)) {
      return marker
    }

    if (value !== null && typeof value === 'object') {
      return marker
    }
    if (typeof value !== 'string') {
      return value
    }

    let sanitized = value
    for (const fragment of fragments) {
      sanitized = sanitized.split(fragment).join(marker)
    }
    return sanitized
  }

  function selectFields(source, fields) {
    if (!source || typeof source !== 'object' || Array.isArray(source)) {
      return {}
    }
    return Object.fromEntries(fields
      .filter((field) => Object.hasOwn(source, field))
      .map((field) => [field, sanitizeScalar(source[field])]))
  }

  function sanitizeResource(resource) {
    const safe = selectFields(resource, ['name', 'uid', 'resourceType', 'kind'])
    if (
      resource
      && resource.quota
      && typeof resource.quota === 'object'
      && !Array.isArray(resource.quota)
    ) {
      safe.quota = Object.fromEntries(
        ['cpu', 'memory', 'storage', 'replicas']
          .filter((field) => Object.hasOwn(resource.quota, field))
          .map((field) => [field, sanitizeScalar(resource.quota[field])]),
      )
    }
    return safe
  }

  function sanitize(value) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) {
      return { details_omitted: true }
    }

    const safe = selectFields(value, [
      'ok',
      'success',
      'name',
      'uid',
      'resourceType',
      'displayName',
      'createdAt',
    ])
    if (Array.isArray(value.resources)) {
      safe.resources = value.resources.map(sanitizeResource)
    }
    if (value.error && typeof value.error === 'object' && !Array.isArray(value.error)) {
      safe.error = {
        ...selectFields(value.error, ['type', 'code']),
        details_omitted: true,
      }
    }
    if (Object.keys(safe).length === 0) {
      safe.details_omitted = true
    }
    return safe
  }

  return sanitize
}

function managedKubeconfigPath() {
  return process.env.SEALAI_KUBECONFIG_PATH || process.env.KUBECONFIG || KUBECONFIG_PATH
}

function loadKubeconfig() {
  const kubeconfigPath = MANAGED_MODE ? managedKubeconfigPath() : KUBECONFIG_PATH
  if (!existsSync(kubeconfigPath)) {
    fail('Kubeconfig not found', { path: kubeconfigPath })
  }
  return readFileSync(kubeconfigPath, 'utf8')
}

async function postTemplate({ deployUrl, kubeconfig, yaml, args, dryRun }) {
  const response = await fetch(deployUrl, {
    method: 'POST',
    headers: {
      Authorization: encodeURIComponent(kubeconfig),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      yaml,
      args,
      dryRun,
    }),
  })

  const text = await response.text()
  let json = null
  try {
    json = text ? JSON.parse(text) : null
  } catch {
    json = null
  }

  return {
    ok: response.ok,
    status: response.status,
    json,
    text,
  }
}

const input = parseArgs(process.argv)
const yaml = loadTemplate(input.templatePath)
const deployArgs = loadDeployArgs(input)
const kubeconfig = loadKubeconfig()
const { region, regionDomain, deployUrl } = MANAGED_MODE
  ? resolveManagedRegion(kubeconfig)
  : normalizeRegion(loadJson(AUTH_PATH, 'auth file').region)
const argsSupplied = Object.keys(deployArgs).length
const sanitizeResponse = createResponseSanitizer(deployArgs)

try {
  const result = await postTemplate({
    deployUrl,
    kubeconfig,
    yaml,
    args: deployArgs,
    dryRun: input.dryRun,
  })

  const payload = {
    success: result.ok,
    dry_run: input.dryRun,
    region,
    region_domain: regionDomain,
    deploy_url: deployUrl,
    template_path: input.templatePath,
    args_supplied: argsSupplied,
    status: result.status,
    status_text: result.ok ? 'OK' : 'Request failed',
    response: sanitizeResponse(result.json !== null ? result.json : result.text),
  }

  if (!result.ok) {
    console.error(JSON.stringify(payload, null, 2))
    process.exit(1)
  }

  console.log(JSON.stringify(payload, null, 2))
} catch (error) {
  fail('Template API request failed', {
    region,
    region_domain: regionDomain,
    deploy_url: deployUrl,
    template_path: input.templatePath,
    args_supplied: argsSupplied,
    details: Object.keys(deployArgs).length > 0 ? 'Request details omitted.' : error.message,
  })
}
