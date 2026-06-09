#!/usr/bin/env node

import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { basename, join, resolve } from 'node:path'

const root = resolve(process.argv[2] || process.cwd())

const MAX_FILE_BYTES = 1024 * 1024
const MAX_FINDINGS_PER_KIND = 60

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
  /^.*\.(ts|tsx|js|jsx|mjs|cjs|py|rb|go|rs|java|kt|php|yaml|yml|json|toml|env)$/
]

const signals = [
  {
    type: 's3-sdk',
    confidence: 5,
    patterns: [
      /@aws-sdk\/client-s3/i,
      /\baws-sdk\b/i,
      /\bboto3\b/i,
      /\bbotocore\b/i,
      /\bgithub\.com\/aws\/aws-sdk-go/i,
      /\bsoftware\.amazon\.awssdk/i,
      /\bAws\\S3\\S3Client\b/i
    ]
  },
  {
    type: 's3-env',
    confidence: 5,
    patterns: [
      /\bS3_(ENDPOINT|BUCKET|ACCESS_KEY|ACCESS_KEY_ID|SECRET_ACCESS_KEY|REGION)\b/i,
      /\bAWS_(ACCESS_KEY_ID|SECRET_ACCESS_KEY|REGION|ENDPOINT|BUCKET)\b/i,
      /\bAWS_ENDPOINT_URL_S3\b/i
    ]
  },
  {
    type: 'minio',
    confidence: 4,
    patterns: [
      /\bMINIO_(ENDPOINT|ACCESS_KEY|SECRET_KEY|BUCKET|ROOT_USER|ROOT_PASSWORD)\b/i,
      /\bminio\b/i,
      /minio\/minio/i,
      /play\.min\.io/i
    ]
  },
  {
    type: 'object-storage-code',
    confidence: 3,
    patterns: [
      /\bPutObject(Command)?\b/i,
      /\bGetObject(Command)?\b/i,
      /\bListObjects(V2)?(Command)?\b/i,
      /\bDeleteObject(Command)?\b/i,
      /\bgetSignedUrl\b/i,
      /\bpresigned?\b/i,
      /\bupload(File|Object)?\b/i,
      /\bobject\s*storage\b/i
    ]
  },
  {
    type: 'framework-storage',
    confidence: 3,
    patterns: [
      /\bactive_storage\b/i,
      /\bdjango-storages\b/i,
      /\bstorages\.backends\.s3\b/i,
      /\bfilesystem\s*=>\s*['"]s3['"]/i,
      /\bmulter-s3\b/i,
      /\bnext-s3-upload\b/i
    ]
  }
]

const envKeyPattern = /^(S3_|AWS_|MINIO_|OBJECT_STORAGE_|STORAGE_).+/i

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
  if (/(^|\/)(config|storage|upload|uploads|lib|src|app)(\/|$)/i.test(rel)) return 2
  if (/(^|\/)(__tests__|test|tests|spec|specs|coverage|docs?|generated)(\/|$)/i.test(rel)) return 0.2
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

function suggestEnvTargets (envKeys) {
  const preferredGroups = [
    ['S3_ENDPOINT', 'S3_ACCESS_KEY_ID', 'S3_SECRET_ACCESS_KEY', 'S3_BUCKET', 'S3_REGION'],
    ['AWS_ENDPOINT_URL_S3', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION', 'S3_BUCKET'],
    ['MINIO_ENDPOINT', 'MINIO_ACCESS_KEY', 'MINIO_SECRET_KEY', 'MINIO_BUCKET']
  ]

  const existing = preferredGroups
    .map((group) => group.filter((key) => envKeys[key]))
    .filter((group) => group.length > 0)
    .sort((a, b) => b.length - a.length)

  return existing[0] || preferredGroups[0]
}

function suggestBucketName () {
  const base = basename(root).toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '')
  return `${base || 'app'}-assets`
}

if (!existsSync(root)) {
  console.error(JSON.stringify({ ok: false, error: `Path does not exist: ${root}` }, null, 2))
  process.exit(1)
}

const files = walk(root)
const { envFiles, keys: envKeys } = scanEnvFiles(files)
const packageInfo = scanPackageJson()
const { scores, findings } = scoreFiles(files)
const { primary, ranked } = choosePrimary(scores)
const suggestedEnvKeys = suggestEnvTargets(envKeys)

const output = {
  ok: true,
  project: root,
  recommendation: {
    needsObjectStorage: ranked.length > 0,
    confidence: primary?.confidence || 'low',
    reason: primary ? 'Detected project S3/object-storage signals.' : 'No S3-specific signal found; create object storage only if the user requested it.',
    suggestedBucketName: suggestBucketName(),
    suggestedPolicy: 'private',
    suggestedEnvKeys,
    createCommand: `sealos-cli s3 create-bucket ${suggestBucketName()} --policy private -o json`
  },
  existingEnv: {
    files: envFiles,
    s3Keys: Object.fromEntries(
      Object.entries(envKeys).filter(([key]) => envKeyPattern.test(key))
    )
  },
  package: packageInfo
    ? {
        packageManager: packageInfo.packageManager,
        storageDependencies: Object.keys(packageInfo.dependencies || {}).filter((name) =>
          /(@aws-sdk\/client-s3|@aws-sdk\/s3-request-presigner|aws-sdk|multer-s3|minio|next-s3-upload|s3|uploadthing)/i.test(name)
        ),
        storageScripts: Object.fromEntries(
          Object.entries(packageInfo.scripts || {}).filter(([name, value]) =>
            /(s3|storage|upload|asset|media)/i.test(`${name} ${value}`)
          )
        )
      }
    : null,
  rankedSignals: ranked,
  findings
}

console.log(JSON.stringify(output, null, 2))
