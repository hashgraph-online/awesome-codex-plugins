#!/usr/bin/env node

import assert from 'node:assert/strict'
import { chmodSync, mkdtempSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { spawnSync } from 'node:child_process'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const scriptPath = resolve(fileURLToPath(new URL('.', import.meta.url)), 'build-push.mjs')

test('lowercases the Docker Hub namespace in the generated image reference', () => {
  const fixtureDir = mkdtempSync(join(tmpdir(), 'sealos-build-push-'))
  const binDir = join(fixtureDir, 'bin')
  const workDir = join(fixtureDir, 'work')
  const dockerLog = join(fixtureDir, 'docker-args.txt')
  mkdirSync(binDir)
  mkdirSync(workDir)
  writeFileSync(join(workDir, 'Dockerfile'), 'FROM scratch\n')

  const dockerPath = join(binDir, 'docker')
  writeFileSync(dockerPath, `#!/bin/sh\nprintf '%s\\n' "$*" > "$DOCKER_LOG"\n`)
  chmodSync(dockerPath, 0o755)

  const result = spawnSync(
    process.execPath,
    [scriptPath, workDir, 'Demo-App', '--registry', 'dockerhub', '--user', 'Che-Zhu'],
    {
      encoding: 'utf8',
      env: {
        ...process.env,
        DOCKER_LOG: dockerLog,
        PATH: `${binDir}:${process.env.PATH}`,
      },
    },
  )

  assert.equal(result.status, 0, result.stderr || result.stdout)
  const output = JSON.parse(result.stdout)
  assert.match(output.image, /^che-zhu\/demo-app:\d{8}-\d{6}$/)
  assert.doesNotMatch(output.image, /Che-Zhu/)
  assert.match(readFileSync(dockerLog, 'utf8'), /-t che-zhu\/demo-app:/)
})

test('routes a private GHCR package directly to the pull Secret flow', () => {
  const fixtureDir = mkdtempSync(join(tmpdir(), 'sealos-build-push-ghcr-'))
  const binDir = join(fixtureDir, 'bin')
  const workDir = join(fixtureDir, 'work')
  const ghLog = join(fixtureDir, 'gh-args.txt')
  mkdirSync(binDir)
  mkdirSync(workDir)
  writeFileSync(join(workDir, 'Dockerfile'), 'FROM scratch\n')

  const dockerPath = join(binDir, 'docker')
  writeFileSync(dockerPath, '#!/bin/sh\nexit 0\n')
  chmodSync(dockerPath, 0o755)

  const ghPath = join(binDir, 'gh')
  writeFileSync(ghPath, `#!/bin/sh
printf '%s\\n' "$*" >> "$GH_LOG"
if [ "$1" = "--version" ]; then
  echo "gh version test"
elif [ "$1" = "auth" ] && [ "$2" = "status" ]; then
  echo "Token scopes: 'repo', 'write:packages'"
elif [ "$1" = "auth" ] && [ "$2" = "token" ]; then
  echo "test-token"
elif [ "$1" = "api" ] && [ "$2" = "user" ]; then
  echo "Che-Zhu"
else
  exit 1
fi
`)
  chmodSync(ghPath, 0o755)

  const result = spawnSync(
    process.execPath,
    [scriptPath, workDir, 'Demo-App', '--registry', 'ghcr'],
    {
      encoding: 'utf8',
      env: {
        ...process.env,
        GH_LOG: ghLog,
        PATH: `${binDir}:${process.env.PATH}`,
      },
    },
  )

  assert.equal(result.status, 0, result.stderr || result.stdout)
  const output = JSON.parse(result.stdout)
  assert.match(output.image, /^ghcr\.io\/che-zhu\/demo-app:\d{8}-\d{6}$/)
  assert.equal(output.requires_image_pull_secret, true)
  assert.match(output.warning, /no visibility or anonymous-pull probe was attempted/)
  assert.match(output.warning, /Proceed directly with the built-in image pull Secret flow/)
  assert.match(output.warning, /Do not attempt to change package visibility/)
  assert.doesNotMatch(output.warning, /package\/demo-app\/settings/)
  assert.doesNotMatch(readFileSync(ghLog, 'utf8'), /packages|graphql/i)
})
