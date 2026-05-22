#!/usr/bin/env node

/**
 * Sealos Template Deploy
 *
 * Usage:
 *   node deploy-template.mjs <template-path> [--dry-run]
 *   node deploy-template.mjs <template-path> --args-json '{"KEY":"value"}'
 *   node deploy-template.mjs <template-path> --args-file ./args.json
 *
 * Behavior:
 *   - Reads ~/.sealos/auth.json for the current region
 *   - Reads ~/.sealos/kubeconfig and sends it as encodeURIComponent(kubeconfig)
 *   - Posts the template YAML to:
 *       https://template.<region-domain>/api/v2alpha/templates/raw
 *   - Prints a JSON result to stdout
 */

import { existsSync, readFileSync } from 'fs'
import { homedir } from 'os'
import { basename, join, resolve } from 'path'

const SEALOS_DIR = join(homedir(), '.sealos')
const AUTH_PATH = join(SEALOS_DIR, 'auth.json')
const KUBECONFIG_PATH = join(SEALOS_DIR, 'kubeconfig')

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
      argsJson = args[i + 1]
      i += 1
      continue
    }
    if (arg === '--args-file') {
      argsFile = args[i + 1]
      i += 1
      continue
    }
    if (arg === '--help' || arg === '-h') {
      printHelp()
      process.exit(0)
    }
    if (!templatePath) {
      templatePath = arg
      continue
    }
    fail(`Unknown argument: ${arg}`)
  }

  if (!templatePath) {
    fail('Missing template path. Run with --help for usage.')
  }

  if (argsJson && argsFile) {
    fail('Use only one of --args-json or --args-file')
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
  node deploy-template.mjs <template-path> --args-json '{"KEY":"value"}'
  node deploy-template.mjs <template-path> --args-file ./args.json

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
  } catch (error) {
    fail(`Failed to parse ${label}`, { path: filePath, details: error.message })
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
  if (argsJson) {
    try {
      const parsed = JSON.parse(argsJson)
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        fail('--args-json must be a JSON object')
      }
      return parsed
    } catch (error) {
      fail('Failed to parse --args-json', { details: error.message })
    }
  }

  if (argsFile) {
    const parsed = loadJson(argsFile, 'args file')
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      fail('Args file must contain a JSON object', { path: argsFile })
    }
    return parsed
  }

  return {}
}

function loadKubeconfig() {
  if (!existsSync(KUBECONFIG_PATH)) {
    fail('Kubeconfig not found', { path: KUBECONFIG_PATH })
  }
  return readFileSync(KUBECONFIG_PATH, 'utf8')
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
    statusText: response.statusText,
    headers: Object.fromEntries(response.headers.entries()),
    json,
    text,
  }
}

const input = parseArgs(process.argv)
const auth = loadJson(AUTH_PATH, 'auth file')
const { region, regionDomain, deployUrl } = normalizeRegion(auth.region)
const yaml = loadTemplate(input.templatePath)
const deployArgs = loadDeployArgs(input)
const kubeconfig = loadKubeconfig()

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
    args: deployArgs,
    status: result.status,
    response: result.json || result.text,
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
    details: error.message,
  })
}
