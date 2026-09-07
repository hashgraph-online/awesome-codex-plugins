#!/usr/bin/env node

/**
 * Small, deterministic adapter for the Brain-managed deployment contract.
 *
 * The deploy skill is intentionally prompt-driven, but the two pieces that
 * must not be left to model text is the artifact digest sent to Brain. This
 * helper keeps that operation reproducible without adding a runtime dependency
 * to the skill bundle.
 */

import { createHash } from 'node:crypto'
import {
  existsSync,
  readFileSync,
  renameSync,
  statSync,
  writeFileSync,
} from 'node:fs'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

export const MANAGED_MODE = 'managed'
export const MANAGED_INPUTS_PATH = '/run/sealai/deployment/inputs.json'

export const BRAIN_IDENTITY_LABELS = Object.freeze({
  'brain.io/managed-by': 'brain',
  'brain.io/deployment-kind': 'template',
})

const REQUIRED_MANAGED_ENV = [
  'SEALAI_DEPLOY_TASK_ID',
  'SEALAI_PROJECT_ID',
  'SEALAI_NAMESPACE',
  'SEALAI_INPUTS_PATH',
  'SEALAI_TURN_DEADLINE_AT',
]

const WORKLOAD_KINDS = new Set([
  'Deployment',
  'StatefulSet',
  'DaemonSet',
  'Job',
  'CronJob',
  'ReplicaSet',
])

function nonEmpty(value) {
  return typeof value === 'string' && value.trim().length > 0
}

export function isManagedMode(env = process.env) {
  return env.SEALAI_DEPLOY_MODE === MANAGED_MODE
}

/**
 * Validate the Brain contract without printing any values. Empty task IDs are
 * not useful for a task-scoped callback and are therefore rejected here.
 */
export function requireManagedEnvironment(env = process.env) {
  if (!isManagedMode(env)) {
    throw new Error('Managed adapter is available only when SEALAI_DEPLOY_MODE=managed.')
  }

  const missing = REQUIRED_MANAGED_ENV.filter((name) => !nonEmpty(env[name]))
  if (missing.length > 0) {
    throw new Error(`Managed deployment environment is incomplete: ${missing.join(', ')}`)
  }

  if (env.SEALAI_INPUTS_PATH !== MANAGED_INPUTS_PATH) {
    throw new Error(
      `Managed deployment must use the fixed input path ${MANAGED_INPUTS_PATH}.`,
    )
  }

  return {
    taskId: env.SEALAI_DEPLOY_TASK_ID,
    projectId: env.SEALAI_PROJECT_ID,
    namespace: env.SEALAI_NAMESPACE,
    inputsPath: env.SEALAI_INPUTS_PATH,
    turnDeadlineAt: env.SEALAI_TURN_DEADLINE_AT,
  }
}

export function managedIdentityLabels(env = process.env) {
  if (!isManagedMode(env)) {
    throw new Error('Identity labels are only resolved in managed mode.')
  }
  if (!nonEmpty(env.SEALAI_PROJECT_ID)) {
    throw new Error('Managed deployment identity requires SEALAI_PROJECT_ID.')
  }

  return {
    'brain.io/managed-by': BRAIN_IDENTITY_LABELS['brain.io/managed-by'],
    'brain.io/project-id': env.SEALAI_PROJECT_ID.trim(),
    'brain.io/deployment-kind': BRAIN_IDENTITY_LABELS['brain.io/deployment-kind'],
  }
}

export function sha256Text(text) {
  return createHash('sha256').update(text, 'utf8').digest('hex')
}

function lineIndent(line) {
  const match = line.match(/^ */)
  return match ? match[0].length : 0
}

function isDocumentSeparator(line) {
  return /^---(?:\s+#.*)?\s*$/.test(line)
}

function isIgnorableLine(line) {
  const trimmed = line.trim()
  return trimmed === '' || trimmed.startsWith('#') || /^\$\{\{.*\}\}$/.test(trimmed)
}

function parseKeyLine(line) {
  const match = line.match(
    /^( *)(?:([A-Za-z0-9_./-]+)|'([^']+)'|"([^"]+)")\s*:\s*(.*)$/,
  )
  if (!match) return null
  return {
    indent: match[1].length,
    key: match[2] ?? match[3] ?? match[4],
    value: match[5],
  }
}

function quoteLabel(value) {
  return JSON.stringify(String(value))
}

function splitDocuments(lines) {
  const documents = []
  const separators = []
  let current = []
  for (const line of lines) {
    if (isDocumentSeparator(line)) {
      documents.push(current)
      separators.push(line)
      current = []
    } else {
      current.push(line)
    }
  }
  documents.push(current)
  return { documents, separators }
}

function documentEntries(lines) {
  const entries = []
  const stack = []
  for (let index = 0; index < lines.length; index += 1) {
    const parsed = parseKeyLine(lines[index])
    if (!parsed || isIgnorableLine(lines[index])) continue

    while (stack.length > 0 && parsed.indent <= stack.at(-1).indent) {
      stack.pop()
    }
    entries.push({
      ...parsed,
      index,
      ancestors: stack.map((item) => item.key),
    })
    stack.push({ indent: parsed.indent, key: parsed.key, index })
  }
  return entries
}

function findBlockEnd(lines, startIndex, baseIndent) {
  for (let index = startIndex + 1; index < lines.length; index += 1) {
    const line = lines[index]
    if (isDocumentSeparator(line)) return index
    if (!isIgnorableLine(line) && lineIndent(line) <= baseIndent) return index
  }
  return lines.length
}

function hasInlineMap(value) {
  const trimmed = value.trim()
  return trimmed.startsWith('{') && trimmed.endsWith('}')
}

function splitInlinePairs(value) {
  const inner = value.trim().slice(1, -1)
  const pairs = []
  let current = ''
  let quote = null
  let depth = 0
  for (const character of inner) {
    if (quote != null) {
      current += character
      if (character === quote) quote = null
      continue
    }
    if (character === '"' || character === "'") {
      quote = character
      current += character
      continue
    }
    if (character === '{' || character === '[' || character === '(') depth += 1
    if (character === '}' || character === ']' || character === ')') depth -= 1
    if (character === ',' && depth === 0) {
      if (current.trim()) pairs.push(current.trim())
      current = ''
    } else {
      current += character
    }
  }
  if (current.trim()) pairs.push(current.trim())
  return pairs
}

function inlinePairKey(pair) {
  const match = pair.match(/^(?:([^:'"\s][^:]*)|'([^']+)'|"([^"]+)")\s*:/)
  return match ? (match[1] ?? match[2] ?? match[3]).trim() : null
}

function inlineLabelsLine(line, labels) {
  const open = line.indexOf('{')
  const close = line.lastIndexOf('}')
  if (open < 0 || close <= open) return null

  const prefix = line.slice(0, open)
  const suffix = line.slice(close + 1)
  const pairs = splitInlinePairs(line.slice(open, close + 1))
  const byKey = new Map(pairs.map((pair) => [inlinePairKey(pair), pair]))
  for (const [key, value] of Object.entries(labels)) {
    byKey.set(key, `${key}: ${quoteLabel(value)}`)
  }
  const rendered = [...byKey.values()].filter(Boolean).join(', ')
  return `${prefix}{${rendered}}${suffix}`
}

function directChildEntries(entries, startIndex, endIndex, parentIndent) {
  return entries.filter(
    (entry) =>
      entry.index > startIndex && entry.index < endIndex && entry.indent > parentIndent,
  )
}

function patchMetadata(lines, metadata, labels) {
  const end = findBlockEnd(lines, metadata.index, metadata.indent)
  const children = directChildEntries(documentEntries(lines), metadata.index, end, metadata.indent)
  const firstChildIndent = children[0]?.indent ?? metadata.indent + 2
  const labelsEntry = children.find(
    (entry) => entry.key === 'labels' && entry.indent === firstChildIndent,
  )

  if (labelsEntry == null) {
    if (metadata.value.trim() !== '' && metadata.value.trim() !== '{}') {
      throw new Error(`Cannot add managed labels to inline metadata at line ${metadata.index + 1}.`)
    }
    const additions = [
      `${' '.repeat(metadata.indent + 2)}labels:`,
      ...Object.entries(labels).map(
        ([key, value]) => `${' '.repeat(metadata.indent + 4)}${key}: ${quoteLabel(value)}`,
      ),
    ]
    lines.splice(metadata.index + 1, 0, ...additions)
    return Object.keys(labels).length
  }

  const labelsEnd = findBlockEnd(lines, labelsEntry.index, labelsEntry.indent)
  if (hasInlineMap(labelsEntry.value)) {
    const patched = inlineLabelsLine(lines[labelsEntry.index], labels)
    if (patched == null) throw new Error(`Invalid inline labels at line ${labelsEntry.index + 1}.`)
    lines[labelsEntry.index] = patched
    return Object.keys(labels).length
  }
  if (labelsEntry.value.trim() !== '') {
    throw new Error(`Cannot add managed labels to scalar labels at line ${labelsEntry.index + 1}.`)
  }

  const childIndent = labelsEntry.indent + 2
  const entries = documentEntries(lines)
  const existing = new Map()
  for (const entry of entries) {
    if (
      entry.index > labelsEntry.index &&
      entry.index < labelsEnd &&
      entry.indent === childIndent
    ) {
      existing.set(entry.key, entry)
    }
  }

  let insertionIndex = labelsEnd
  for (const [key, value] of Object.entries(labels)) {
    const entry = existing.get(key)
    const rendered = `${' '.repeat(childIndent)}${key}: ${quoteLabel(value)}`
    if (entry == null) {
      lines.splice(insertionIndex, 0, rendered)
      insertionIndex += 1
    } else {
      lines[entry.index] = rendered
    }
  }
  return Object.keys(labels).length
}

function topLevelKind(entries) {
  const entry = entries.find((item) => item.ancestors.length === 0 && item.key === 'kind')
  return entry?.value.trim().replace(/^['"]|['"]$/g, '') ?? null
}

function patchDocument(lines, labels) {
  const entries = documentEntries(lines)
  const kind = topLevelKind(entries)
  const rootIndent = entries.find((entry) => entry.ancestors.length === 0)?.indent ?? 0
  const metadataTargets = entries.filter(
    (entry) =>
      entry.key === 'metadata' &&
      (entry.indent === rootIndent || entry.ancestors.includes('template')),
  )

  let labelsApplied = 0
  // Work from the bottom so insertions do not invalidate earlier line offsets.
  for (const metadata of [...metadataTargets].sort((left, right) => right.index - left.index)) {
    labelsApplied += patchMetadata(lines, metadata, labels)
  }

  if (WORKLOAD_KINDS.has(kind)) {
    const refreshed = documentEntries(lines)
    const templateEntries = refreshed.filter((entry) => entry.key === 'template')
    for (const template of [...templateEntries].sort((left, right) => right.index - left.index)) {
      const end = findBlockEnd(lines, template.index, template.indent)
      const nestedMetadata = documentEntries(lines).some(
        (entry) =>
          entry.key === 'metadata' &&
          entry.index > template.index &&
          entry.index < end &&
          entry.indent > template.indent,
      )
      if (nestedMetadata || template.value.trim() !== '') continue
      const additions = [
        `${' '.repeat(template.indent + 2)}metadata:`,
        `${' '.repeat(template.indent + 4)}labels:`,
        ...Object.entries(labels).map(
          ([key, value]) => `${' '.repeat(template.indent + 6)}${key}: ${quoteLabel(value)}`,
        ),
      ]
      lines.splice(template.index + 1, 0, ...additions)
      labelsApplied += Object.keys(labels).length
    }
  }

  return { lines, labelsApplied, kind }
}

/**
 * Prepare a generated Template for managed mode without injecting a Brain-
 * owned Instance identity. Sealos/Template owns the actual app name.
 */
export function adaptTemplateForManagedMode(template, env = process.env) {
  if (!isManagedMode(env)) {
    return {
      managed: false,
      template,
      sha256: sha256Text(template),
      labelsApplied: 0,
    }
  }

  return {
    managed: true,
    template,
    sha256: sha256Text(template),
    labelsApplied: 0,
    kinds: [],
  }
}

export function readManagedInputs(env = process.env) {
  if (!isManagedMode(env)) {
    throw new Error('Managed inputs are available only when SEALAI_DEPLOY_MODE=managed.')
  }
  const inputPath = env.SEALAI_INPUTS_PATH
  if (inputPath !== MANAGED_INPUTS_PATH) {
    throw new Error(`Managed deployment must read ${MANAGED_INPUTS_PATH}.`)
  }
  if (!existsSync(inputPath)) {
    throw new Error(`Managed deployment input file is not available at ${MANAGED_INPUTS_PATH}.`)
  }
  let parsed
  try {
    parsed = JSON.parse(readFileSync(inputPath, 'utf8'))
  } catch {
    throw new Error('Managed deployment input file is not valid JSON.')
  }
  if (parsed == null || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error('Managed deployment input file must contain a JSON object.')
  }
  return parsed
}

export function prepareManagedTemplate(templatePath, env = process.env) {
  requireManagedEnvironment(env)
  const absolutePath = resolve(templatePath)
  if (!existsSync(absolutePath)) throw new Error(`Template file not found: ${absolutePath}`)
  const source = readFileSync(absolutePath, 'utf8')
  const result = adaptTemplateForManagedMode(source, env)
  const temporaryPath = `${absolutePath}.managed-${process.pid}-${Date.now()}.tmp`
  writeFileSync(temporaryPath, result.template, { mode: statSync(absolutePath).mode & 0o777 })
  renameSync(temporaryPath, absolutePath)
  return { path: absolutePath, ...result }
}

function printUsage() {
  console.error(
    'Usage: node managed-adapter.mjs context | prepare-template <path> | sha256 <path> | read-inputs',
  )
}

function main(argv = process.argv.slice(2)) {
  try {
    const [command, value] = argv
    if (command === 'context') {
      console.log(JSON.stringify({ managed: true, ...requireManagedEnvironment() }, null, 2))
      return
    }
    if (command === 'prepare-template') {
      if (!value) throw new Error('Missing template path.')
      const result = prepareManagedTemplate(value)
      console.log(JSON.stringify({
        managed: result.managed,
        path: result.path,
        sha256: result.sha256,
        labelsApplied: result.labelsApplied,
        kinds: result.kinds,
      }, null, 2))
      return
    }
    if (command === 'sha256') {
      if (!value || !existsSync(resolve(value))) throw new Error('Template file not found.')
      console.log(JSON.stringify({
        path: resolve(value),
        sha256: sha256Text(readFileSync(resolve(value), 'utf8')),
      }, null, 2))
      return
    }
    if (command === 'read-inputs') {
      const inputs = readManagedInputs()
      console.log(JSON.stringify({ managed: true, path: MANAGED_INPUTS_PATH, keys: Object.keys(inputs).sort() }, null, 2))
      return
    }
    printUsage()
    process.exitCode = 1
  } catch (error) {
    console.error(JSON.stringify({ managed: isManagedMode(), error: error.message }, null, 2))
    process.exitCode = 1
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main()
}
