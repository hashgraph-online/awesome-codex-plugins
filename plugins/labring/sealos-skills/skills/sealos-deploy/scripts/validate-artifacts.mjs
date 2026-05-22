#!/usr/bin/env node

import fs from 'fs'
import path from 'path'
import {
  inferArtifactKind,
  validateArtifactFile,
} from './artifact-validator.mjs'

function collectProjectArtifacts(workDir) {
  const sealosDir = path.join(workDir, '.sealos')
  const candidates = [
    path.join(sealosDir, 'config.json'),
    path.join(sealosDir, 'analysis.json'),
    path.join(sealosDir, 'build', 'build-result.json'),
    path.join(sealosDir, 'state.json'),
  ]

  return candidates
    .filter((candidate) => fs.existsSync(candidate))
    .map((candidate) => ({
      file: candidate,
      kind: inferArtifactKind(candidate),
    }))
    .filter((entry) => entry.kind)
}

function printAndExit(result, code) {
  console.log(JSON.stringify(result, null, 2))
  process.exit(code)
}

const args = process.argv.slice(2)

if (args.length === 0) {
  printAndExit({
    valid: false,
    error: 'Usage: node validate-artifacts.mjs <file> | <kind> <file> | --dir <work-dir>',
  }, 1)
}

if (args[0] === '--dir') {
  const workDir = args[1]
  if (!workDir) {
    printAndExit({ valid: false, error: 'Missing work directory after --dir' }, 1)
  }

  const results = collectProjectArtifacts(path.resolve(workDir)).map(({ kind, file }) => ({
    file,
    ...validateArtifactFile(kind, file),
  }))

  printAndExit({
    valid: results.every((entry) => entry.valid),
    results,
  }, results.every((entry) => entry.valid) ? 0 : 1)
}

let kind
let filePath

if (args.length === 1) {
  filePath = path.resolve(args[0])
  kind = inferArtifactKind(filePath)
  if (!kind) {
    printAndExit({
      valid: false,
      error: `Could not infer artifact kind from filename: ${path.basename(filePath)}`,
    }, 1)
  }
} else {
  kind = args[0]
  filePath = path.resolve(args[1])
}

const result = validateArtifactFile(kind, filePath)
printAndExit({
  file: filePath,
  ...result,
}, result.valid ? 0 : 1)
