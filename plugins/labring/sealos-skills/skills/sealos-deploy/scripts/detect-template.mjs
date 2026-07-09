#!/usr/bin/env node

/**
 * Sealos template fast-path detection.
 *
 * Usage:
 *   node detect-template.mjs --github-url <url> --work-dir <dir> --skill-dir <dir>
 *   node detect-template.mjs --work-dir <dir> --skill-dir <dir>
 *
 * The script records a match in .sealos/template-match.json. It materializes
 * .sealos/template/index.yaml only when the matching entry provides complete
 * template YAML via template_yaml, template_path, or template_url.
 */

import fs from 'fs'
import path from 'path'
import { execSync } from 'child_process'

const GIT_SUFFIX_RE = /\.git$/i
const GITHUB_SSH_RE = /^git@github\.com:([^/]+)\/(.+)$/i
const URL_PROTOCOL_RE = /^[a-z][a-z0-9+.-]*:\/\//i
const MAX_TEMPLATE_YAML_BYTES = 1024 * 1024

function usage () {
  console.error('Usage: node detect-template.mjs [--github-url <url>] --work-dir <dir> --skill-dir <dir>')
  process.exit(1)
}

function parseArgs (argv) {
  const parsed = {
    githubUrl: '',
    skillDir: '',
    workDir: '',
  }

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]
    const next = argv[index + 1]
    switch (arg) {
      case '--github-url':
        if (!next) usage()
        parsed.githubUrl = next
        index += 1
        break
      case '--skill-dir':
        if (!next) usage()
        parsed.skillDir = next
        index += 1
        break
      case '--work-dir':
        if (!next) usage()
        parsed.workDir = next
        index += 1
        break
      default:
        usage()
    }
  }

  if (!parsed.workDir || !parsed.skillDir) usage()
  return parsed
}

function normalizeGithubRepoReference (input) {
  const raw = String(input || '').trim()
  if (!raw) return null

  const ssh = GITHUB_SSH_RE.exec(raw)
  if (ssh) {
    const owner = ssh[1]?.trim()
    const repo = ssh[2]?.trim().replace(GIT_SUFFIX_RE, '')
    return owner && repo ? `${owner}/${repo}`.toLowerCase() : null
  }

  const fullName = normalizeGithubFullName(raw)
  if (fullName != null) return fullName

  const withProtocol = URL_PROTOCOL_RE.test(raw) ? raw : `https://${raw}`
  let url
  try {
    url = new URL(withProtocol)
  } catch {
    return normalizeGithubFullName(raw)
  }

  if (url.hostname.toLowerCase() !== 'github.com') return null

  const [owner, repoSegment] = url.pathname
    .split('/')
    .map((part) => part.trim())
    .filter(Boolean)
  const repo = repoSegment?.replace(GIT_SUFFIX_RE, '')
  return owner && repo ? `${owner}/${repo}`.toLowerCase() : null
}

function normalizeGithubFullName (input) {
  const [owner, repo, extra] = input
    .replace(GIT_SUFFIX_RE, '')
    .split('/')
    .map((part) => part.trim())
    .filter(Boolean)
  return owner && repo && extra == null ? `${owner}/${repo}`.toLowerCase() : null
}

function githubUrlFromGitRemote (workDir) {
  try {
    const remote = execSync('git remote get-url origin', {
      cwd: workDir,
      encoding: 'utf-8',
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim()
    return remote.includes('github.com') ? remote : ''
  } catch {
    return ''
  }
}

function readJsonFile (filePath, fallback) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
  } catch {
    return fallback
  }
}

function templateSourceRepos (entry) {
  return [
    entry.source_repos,
    entry.sourceRepos,
    entry.githubRepos,
    entry.githubRepo,
    entry.sourceRepo,
    entry.repoUrl,
    entry.repositoryUrl,
    entry.gitRepo,
  ]
    .flatMap((value) => {
      if (Array.isArray(value)) return value
      if (typeof value === 'string') return [value]
      return []
    })
    .map((value) => value.trim())
    .filter(Boolean)
}

function templateArgs (entry) {
  if (entry.args == null || typeof entry.args !== 'object' || Array.isArray(entry.args)) {
    return {}
  }
  return Object.fromEntries(
    Object.entries(entry.args).map(([key, value]) => [key, String(value)]),
  )
}

function findTemplate (templates, repoRef) {
  return templates.find((entry) =>
    typeof entry.name === 'string' &&
    entry.name.trim() &&
    templateSourceRepos(entry).some((sourceRepo) => normalizeGithubRepoReference(sourceRepo) === repoRef),
  ) || null
}

async function readTemplateYaml (entry, skillDir) {
  let yaml = null

  if (typeof entry.template_yaml === 'string' && entry.template_yaml.trim()) {
    yaml = entry.template_yaml.trimEnd() + '\n'
    assertSealosTemplateYaml(yaml)
    return yaml
  }

  const templatePath = typeof entry.template_path === 'string' ? entry.template_path.trim() : ''
  if (templatePath) {
    const resolvedPath = resolveTemplatePath(templatePath, skillDir)
    yaml = readTemplateFile(resolvedPath).trimEnd() + '\n'
    assertSealosTemplateYaml(yaml)
    return yaml
  }

  const templateUrl = typeof entry.template_url === 'string' ? entry.template_url.trim() : ''
  if (templateUrl) {
    const url = parseTemplateUrl(templateUrl)
    const response = await fetch(url.href, { signal: AbortSignal.timeout(15000) })
    if (!response.ok) {
      throw new Error(`Could not fetch template_url (${response.status})`)
    }
    yaml = (await readTemplateResponse(response)).trimEnd() + '\n'
    assertSealosTemplateYaml(yaml)
    return yaml
  }

  return null
}

function resolveTemplatePath (templatePath, skillDir) {
  if (path.isAbsolute(templatePath)) {
    throw new Error('template_path must be relative to the skill directory')
  }

  const resolvedPath = path.resolve(skillDir, templatePath)
  const relativePath = path.relative(skillDir, resolvedPath)
  if (relativePath.startsWith('..') || path.isAbsolute(relativePath)) {
    throw new Error('template_path must stay inside the skill directory')
  }

  return resolvedPath
}

function readTemplateFile (filePath) {
  const stats = fs.statSync(filePath)
  if (stats.size > MAX_TEMPLATE_YAML_BYTES) {
    throw new Error(`Template YAML must be at most ${MAX_TEMPLATE_YAML_BYTES} bytes`)
  }

  return fs.readFileSync(filePath, 'utf-8')
}

function parseTemplateUrl (templateUrl) {
  let url
  try {
    url = new URL(templateUrl)
  } catch {
    throw new Error('template_url must be a valid URL')
  }

  if (url.protocol !== 'https:') {
    throw new Error('template_url must use https')
  }

  return url
}

async function readTemplateResponse (response) {
  const contentLength = Number(response.headers.get('content-length'))
  if (Number.isFinite(contentLength) && contentLength > MAX_TEMPLATE_YAML_BYTES) {
    throw new Error(`Template YAML must be at most ${MAX_TEMPLATE_YAML_BYTES} bytes`)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    return response.text()
  }

  const chunks = []
  let totalBytes = 0
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    totalBytes += value.byteLength
    if (totalBytes > MAX_TEMPLATE_YAML_BYTES) {
      throw new Error(`Template YAML must be at most ${MAX_TEMPLATE_YAML_BYTES} bytes`)
    }
    chunks.push(value)
  }

  return new TextDecoder().decode(Buffer.concat(chunks))
}

function assertSealosTemplateYaml (yaml) {
  if (!/^\s*apiVersion:\s*app\.sealos\.io\/v1\s*$/m.test(yaml)) {
    throw new Error('Template YAML must include apiVersion: app.sealos.io/v1')
  }
  if (!/^\s*kind:\s*Template\s*$/m.test(yaml)) {
    throw new Error('Template YAML must include kind: Template')
  }
}

function writeJson (filePath, data) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true })
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`)
}

function unmatchedResult (reason) {
  return {
    version: '1.0',
    generated_at: new Date().toISOString(),
    matched: false,
    materialized: false,
    repo: null,
    template: null,
    args: {},
    source: 'none',
    template_path: null,
    reason,
  }
}

const args = parseArgs(process.argv.slice(2))
const workDir = path.resolve(args.workDir)
const skillDir = path.resolve(args.skillDir)
const sealosDir = path.join(workDir, '.sealos')
const outputPath = path.join(sealosDir, 'template-match.json')
const templateOutputPath = path.join(sealosDir, 'template', 'index.yaml')
const config = readJsonFile(path.join(skillDir, 'config.json'), {})
const fastPath = config.template_fast_path ?? {}

if (fastPath.enabled === false) {
  const result = unmatchedResult('Template fast path is disabled in config.json.')
  writeJson(outputPath, result)
  console.log(JSON.stringify(result, null, 2))
  process.exit(0)
}

const githubUrl = args.githubUrl || githubUrlFromGitRemote(workDir)
const repoRef = normalizeGithubRepoReference(githubUrl)
if (repoRef == null) {
  const result = unmatchedResult('No GitHub repository reference was available for template matching.')
  writeJson(outputPath, result)
  console.log(JSON.stringify(result, null, 2))
  process.exit(0)
}

const templates = Array.isArray(fastPath.templates) ? fastPath.templates : []
const match = findTemplate(templates, repoRef)
if (match == null) {
  const result = unmatchedResult(`No configured Sealos template matched ${repoRef}.`)
  writeJson(outputPath, result)
  console.log(JSON.stringify(result, null, 2))
  process.exit(0)
}

let templateYaml = null
let materializeError = ''
try {
  templateYaml = await readTemplateYaml(match, skillDir)
} catch (error) {
  materializeError = error instanceof Error ? error.message : String(error)
}

const materialized = templateYaml != null
if (materialized) {
  fs.mkdirSync(path.dirname(templateOutputPath), { recursive: true })
  fs.writeFileSync(templateOutputPath, templateYaml)
}

const title = typeof match.title === 'string' && match.title.trim()
  ? match.title.trim()
  : String(match.name || '').trim()

const result = {
  version: '1.0',
  generated_at: new Date().toISOString(),
  matched: true,
  materialized,
  repo: {
    reference: repoRef,
    github_url: githubUrl,
  },
  template: {
    name: String(match.name || '').trim(),
    title,
    ...(typeof match.description === 'string' ? { description: match.description } : {}),
  },
  args: templateArgs(match),
  source: 'config',
  template_path: materialized ? '.sealos/template/index.yaml' : null,
  reason: materialized
    ? `Matched ${repoRef} to template ${String(match.name || '').trim()} and materialized template YAML.`
    : `Matched ${repoRef} to template ${String(match.name || '').trim()}, but no template YAML source was configured.${materializeError ? ` ${materializeError}` : ''}`,
}

writeJson(outputPath, result)
console.log(JSON.stringify(result, null, 2))
