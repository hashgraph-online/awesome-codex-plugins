#!/usr/bin/env node

import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

import { validate } from './validate-dockerfile.mjs'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const templatesDir = path.join(scriptDir, '..', 'templates')

test('static Nginx templates package assets without ConfigMap publication', (t) => {
  const fixtureDir = fs.mkdtempSync(path.join(os.tmpdir(), 'static-nginx-template-'))
  t.after(() => fs.rmSync(fixtureDir, { recursive: true, force: true }))

  const dockerfile = fs.readFileSync(path.join(templatesDir, 'static-nginx.dockerfile'), 'utf8')
  const dockerignore = fs.readFileSync(path.join(templatesDir, 'static-nginx.dockerignore'), 'utf8')
  fs.writeFileSync(path.join(fixtureDir, 'Dockerfile'), dockerfile)
  fs.writeFileSync(path.join(fixtureDir, '.dockerignore'), dockerignore)

  assert.match(dockerfile, /^FROM nginxinc\/nginx-unprivileged:1\.31\.3-alpine3\.24$/m)
  assert.match(dockerfile, /^COPY --chown=101:101 \. \/usr\/share\/nginx\/html$/m)
  assert.match(dockerfile, /^USER 101:101$/m)
  assert.doesNotMatch(dockerfile, /ConfigMap/i)
  assert.match(dockerignore, /^Dockerfile$/m)
  assert.match(dockerignore, /^\.sealos$/m)
  assert.doesNotMatch(dockerignore, /^\*\.md$/m)

  const result = validate(path.join(fixtureDir, 'Dockerfile'), { port: 8080 })
  assert.equal(result.valid, true)
  assert.deepEqual(result.issues, [])
})
