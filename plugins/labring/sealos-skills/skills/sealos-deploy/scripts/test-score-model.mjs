#!/usr/bin/env node

import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import test from 'node:test'

import { scoreProject } from './score-model.mjs'

test('scores a source-ready index.html site as deployable without a package manager', (t) => {
  const fixtureDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sealos-score-static-html-'))
  t.after(() => fs.rmSync(fixtureDir, { recursive: true, force: true }))
  fs.writeFileSync(path.join(fixtureDir, 'index.html'), '<!doctype html><title>Static site</title>\n')

  const result = scoreProject(fixtureDir)
  assert.equal(result.score, 10)
  assert.equal(result.verdict, 'Excellent')
  assert.equal(result.signals.primary_language, 'html')
  assert.deepEqual(result.signals.framework, ['static_html'])
  assert.equal(result.signals.package_manager, null)
  assert.equal(result.signals.port, 8080)
  assert.equal(result.signals.runtime_version.html, 'static')
  assert.equal(result.signals.runtime_version.nginx, '1.31.3')
})
