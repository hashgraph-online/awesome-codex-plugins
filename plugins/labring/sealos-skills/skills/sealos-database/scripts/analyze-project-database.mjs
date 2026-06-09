#!/usr/bin/env node

import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { basename, join, resolve } from 'node:path'

const root = resolve(process.argv[2] || process.cwd())

const MAX_FILE_BYTES = 1024 * 1024
const MAX_FINDINGS_PER_KIND = 40

const ignoredDirs = new Set([
  '.git',
  'node_modules',
  'dist',
  'build',
  '.next',
  '.turbo',
  '.venv',
  'venv',
  '__pycache__',
  'coverage',
  '.sealos'
])

const textFilePatterns = [
  /^package\.json$/,
  /^pnpm-lock\.yaml$/,
  /^package-lock\.json$/,
  /^yarn\.lock$/,
  /^bun\.lockb?$/,
  /^docker-compose.*\.ya?ml$/,
  /^compose.*\.ya?ml$/,
  /^\.env.*$/,
  /^.*\.env$/,
  /^.*\.prisma$/,
  /^drizzle\.config\.(ts|js|mjs|cjs)$/,
  /^.*\.(ts|tsx|js|jsx|mjs|cjs|py|rb|go|rs|java|kt|php|yaml|yml|json|toml)$/
]

const signals = [
  {
    type: 'postgresql',
    confidence: 4,
    patterns: [
      /\bpostgres(?:ql)?:\/\//i,
      /\bPOSTGRES(?:QL)?_/i,
      /\bprovider\s*=\s*["']postgres(?:ql)?["']/i,
      /["']postgres(?:ql)?["']\s*:\s*\{/i,
      /\bpg\b/,
      /drizzle-orm\/node-postgres/i,
      /postgresql/i,
      /psycopg/i
    ]
  },
  {
    type: 'mongodb',
    confidence: 4,
    patterns: [
      /\bmongodb(?:\+srv)?:\/\//i,
      /\bMONGODB_URI\b/i,
      /\bMONGO_URL\b/i,
      /\bmongoose\b/i,
      /\bmongodb\b/i
    ]
  },
  {
    type: 'mysql',
    confidence: 3,
    patterns: [
      /\bmysql:\/\//i,
      /\bMYSQL_/i,
      /\bmysql2\b/i,
      /\bprovider\s*=\s*["']mysql["']/i,
      /["']mysql["']\s*:\s*\{/i,
      /\bprisma.*mysql/i
    ]
  },
  {
    type: 'redis',
    confidence: 3,
    patterns: [
      /\bredis:\/\//i,
      /\bREDIS_URL\b/i,
      /\bioredis\b/i,
      /@upstash\/redis/i,
      /\bbullmq?\b/i
    ]
  },
  {
    type: 'qdrant',
    confidence: 2,
    patterns: [/\bQDRANT_/i, /\bqdrant\b/i]
  },
  {
    type: 'weaviate',
    confidence: 2,
    patterns: [/\bWEAVIATE_/i, /\bweaviate\b/i]
  },
  {
    type: 'clickhouse',
    confidence: 2,
    patterns: [/\bCLICKHOUSE_/i, /\bclickhouse\b/i]
  }
]

const envKeyByType = {
  postgresql: ['DATABASE_URL', 'POSTGRES_URL', 'POSTGRES_PRISMA_URL'],
  mysql: ['DATABASE_URL', 'MYSQL_URL', 'MYSQL_DATABASE_URL'],
  mongodb: ['MONGODB_URI', 'MONGO_URL', 'DATABASE_URL'],
  redis: ['REDIS_URL', 'KV_URL', 'CACHE_URL', 'QUEUE_REDIS_URL'],
  qdrant: ['QDRANT_URL'],
  weaviate: ['WEAVIATE_URL'],
  clickhouse: ['CLICKHOUSE_URL']
}

function isTextCandidate (filePath) {
  const name = basename(filePath)
  return textFilePatterns.some((pattern) => pattern.test(name))
}

function walk (dir, files = []) {
  let entries
  try {
    entries = readdirSync(dir, { withFileTypes: true })
  } catch {
    return files
  }

  for (const entry of entries) {
    if (ignoredDirs.has(entry.name)) continue
    const fullPath = join(dir, entry.name)
    if (entry.isDirectory()) {
      walk(fullPath, files)
      continue
    }
    if (!entry.isFile()) continue
    if (!isTextCandidate(fullPath)) continue
    try {
      if (statSync(fullPath).size > MAX_FILE_BYTES) continue
    } catch {
      continue
    }
    files.push(fullPath)
  }

  return files
}

function safeRead (filePath) {
  try {
    return readFileSync(filePath, 'utf8')
  } catch {
    return ''
  }
}

function relative (filePath) {
  return filePath.startsWith(root) ? filePath.slice(root.length + 1) : filePath
}

function addFinding (bucket, finding) {
  if (bucket.length >= MAX_FINDINGS_PER_KIND) return
  bucket.push(finding)
}

function fileWeight (filePath) {
  const rel = relative(filePath)
  const name = basename(filePath)

  if (/^\.env|\.env$/.test(name) || name.includes('.env.')) return 5
  if (name === 'package.json') return 4
  if (/docker-compose.*\.ya?ml$|compose.*\.ya?ml$/i.test(name)) return 3
  if (/schema\.prisma$|drizzle\.config\.(ts|js|mjs|cjs)$/.test(rel)) return 4
  if (/(^|\/)(prisma|drizzle|migrations|db\/migrations|database\/migrations)(\/|$)/.test(rel)) return 3
  if (/(^|\/)(__tests__|test|tests|spec|specs|coverage|docs?|generated)(\/|$)/i.test(rel)) return 0.2
  if (/_openapi\.json$|openapi|swagger/i.test(rel)) return 0.1
  if (/README|CHANGELOG|LICENSE|SECURITY/i.test(name)) return 0.2

  return 1
}

function scanEnvFiles (files) {
  const envFiles = []
  const keys = {}

  for (const filePath of files) {
    const name = basename(filePath)
    if (!/^\.env|\.env$/.test(name) && !name.includes('.env.')) continue
    const content = safeRead(filePath)
    const fileKeys = []
    for (const [index, line] of content.split(/\r?\n/).entries()) {
      const match = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=/)
      if (!match) continue
      const key = match[1]
      fileKeys.push(key)
      if (!keys[key]) keys[key] = []
      keys[key].push({ file: relative(filePath), line: index + 1 })
    }
    envFiles.push({ file: relative(filePath), keys: fileKeys })
  }

  return { envFiles, keys }
}

function scanPackageJson () {
  const packagePath = join(root, 'package.json')
  if (!existsSync(packagePath)) return null

  try {
    const pkg = JSON.parse(readFileSync(packagePath, 'utf8'))
    return {
      packageManager: pkg.packageManager || null,
      scripts: pkg.scripts || {},
      dependencies: {
        ...pkg.dependencies,
        ...pkg.devDependencies
      }
    }
  } catch {
    return null
  }
}

function detectMigrations (files) {
  const candidates = [
    'prisma/schema.prisma',
    'prisma/migrations',
    'drizzle',
    'migrations',
    'db/migrations',
    'database/migrations'
  ]

  const found = []
  for (const candidate of candidates) {
    if (existsSync(join(root, candidate))) {
      found.push(candidate)
    }
  }

  for (const filePath of files) {
    const rel = relative(filePath)
    if (/drizzle\.config\.(ts|js|mjs|cjs)$/.test(rel) && !found.includes(rel)) found.push(rel)
    if (/schema\.prisma$/.test(rel) && !found.includes(rel)) found.push(rel)
  }

  return found
}

function scoreFiles (files) {
  const scores = {}
  const findings = []

  for (const filePath of files) {
    const content = safeRead(filePath)
    if (!content) continue
    const weight = fileWeight(filePath)
    const lines = content.split(/\r?\n/)
    for (const [lineIndex, line] of lines.entries()) {
      for (const signal of signals) {
        for (const pattern of signal.patterns) {
          if (!pattern.test(line)) continue
          scores[signal.type] = (scores[signal.type] || 0) + (signal.confidence * weight)
          addFinding(findings, {
            type: signal.type,
            file: relative(filePath),
            line: lineIndex + 1,
            weight,
            match: pattern.source
          })
          break
        }
      }
    }
  }

  return { scores, findings }
}

function choosePrimary (scores) {
  const ranked = Object.entries(scores)
    .sort((a, b) => b[1] - a[1])
    .map(([type, score]) => ({ type, score: Number(score.toFixed(2)) }))

  if (ranked.length === 0) return { primary: null, ranked }

  const [first, second] = ranked
  const confidence = !second ? 'high' : first.score >= second.score * 1.5 ? 'high' : 'medium'
  return { primary: { ...first, confidence }, ranked }
}

function suggestEnvTargets (primaryType, envKeys) {
  if (!primaryType) return []
  const preferred = envKeyByType[primaryType] || []
  const existing = preferred.filter((key) => envKeys[key])
  return existing.length > 0 ? existing : preferred.slice(0, 1)
}

function suggestCreateCommand (primaryType) {
  const type = primaryType || 'postgresql'
  const safeType = type === 'mysql' ? 'mysql' : type
  return `sealos-cli database create ${safeType} --name <name> --cpu 1 --memory 1 --storage 3 --replicas 1 -o json`
}

if (!existsSync(root)) {
  console.error(JSON.stringify({ ok: false, error: `Path does not exist: ${root}` }, null, 2))
  process.exit(1)
}

const files = walk(root)
const { envFiles, keys: envKeys } = scanEnvFiles(files)
const packageInfo = scanPackageJson()
const migrations = detectMigrations(files)
const { scores, findings } = scoreFiles(files)
const { primary, ranked } = choosePrimary(scores)
const suggestedEnvKeys = suggestEnvTargets(primary?.type, envKeys)

const output = {
  ok: true,
  project: root,
  recommendation: {
    databaseType: primary?.type || 'postgresql',
    confidence: primary?.confidence || 'low',
    reason: primary ? 'Detected project database signals.' : 'No database-specific signal found; postgresql is the default only if the user wants a new relational database.',
    suggestedEnvKeys,
    createCommand: suggestCreateCommand(primary?.type)
  },
  existingEnv: {
    files: envFiles,
    databaseKeys: Object.fromEntries(
      Object.entries(envKeys)
        .filter(([key]) => /DATABASE|POSTGRES|MYSQL|MONGO|REDIS|QDRANT|WEAVIATE|CLICKHOUSE|CACHE|QUEUE|KV/.test(key))
    )
  },
  package: packageInfo
    ? {
        packageManager: packageInfo.packageManager,
        databaseDependencies: Object.keys(packageInfo.dependencies || {}).filter((name) =>
          /(prisma|drizzle|typeorm|sequelize|mongoose|mongodb|pg$|mysql|mysql2|redis|ioredis|upstash|qdrant|weaviate|clickhouse)/i.test(name)
        ),
        migrationScripts: Object.fromEntries(
          Object.entries(packageInfo.scripts || {}).filter(([name, value]) =>
            /(db|database|migrate|migration|prisma|drizzle)/i.test(`${name} ${value}`)
          )
        )
      }
    : null,
  migrations,
  rankedSignals: ranked,
  findings
}

console.log(JSON.stringify(output, null, 2))
