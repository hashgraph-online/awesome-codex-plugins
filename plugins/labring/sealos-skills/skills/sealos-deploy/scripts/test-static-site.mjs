#!/usr/bin/env node

import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import test from 'node:test'

import { inspectSourceReadyStaticSite } from './static-site.mjs'

function fixture(t, files) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'sealos-static-decision-'))
  t.after(() => fs.rmSync(root, { recursive: true, force: true }))
  for (const [relativePath, content] of Object.entries(files)) {
    const target = path.join(root, relativePath)
    fs.mkdirSync(path.dirname(target), { recursive: true })
    fs.writeFileSync(target, content)
  }
  return root
}

test('classifies an arbitrary nested public asset tree by deployment contract, not extension count', (t) => {
  const root = fixture(t, {
    'index.html': '<!doctype html>',
    'assets/app.js': 'document.body.dataset.ready = "yes"',
    'assets/app.wasm': Buffer.from([0, 97, 115, 109]),
    'downloads/archive.custom': Buffer.from([1, 2, 3]),
  })
  const result = inspectSourceReadyStaticSite(root)
  assert.equal(result.classification, 'source_ready_static')
  assert.equal(result.route, 'static_image_build')
  assert.equal(result.eligible, true)
  assert.deepEqual(result.assets.map(({ relativePath }) => relativePath), [
    'assets/app.js', 'assets/app.wasm', 'downloads/archive.custom', 'index.html',
  ])
})

test('routes a build manifest through ordinary application analysis', (t) => {
  const root = fixture(t, {
    'index.html': '<!doctype html>',
    'package.json': '{"scripts":{"build":"vite build"}}',
  })
  const result = inspectSourceReadyStaticSite(root)
  assert.equal(result.classification, 'build_or_runtime_required')
  assert.equal(result.route, 'ordinary_analysis')
  assert.equal(result.eligible, false)
})

test('routes frontend source formats and lockfiles through a reproducible build decision', (t) => {
  const root = fixture(t, {
    'index.html': '<!doctype html>',
    'src/site.scss': '$brand: rebeccapurple;',
    'pnpm-lock.yaml': 'lockfileVersion: 9',
  })
  const result = inspectSourceReadyStaticSite(root)
  assert.equal(result.classification, 'build_or_runtime_required')
  assert.equal(result.eligible, false)
  assert.equal(result.runtimeSignals.length, 2)
})

test('routes every source-ready tree to a static image build', (t) => {
  const root = fixture(t, {
    'index.html': '<!doctype html>',
    'assets/payload.bin': Buffer.alloc(32, 1),
  })
  const result = inspectSourceReadyStaticSite(root)
  assert.equal(result.classification, 'source_ready_static')
  assert.equal(result.route, 'static_image_build')
  assert.equal(result.eligible, true)
})

test('gives an existing container contract precedence over the generated static image', (t) => {
  const root = fixture(t, {
    'index.html': '<!doctype html>',
    Dockerfile: 'FROM nginx:alpine',
  })
  const result = inspectSourceReadyStaticSite(root)
  assert.equal(result.classification, 'container_ready')
  assert.equal(result.route, 'existing_image_or_container_build')
})

test('blocks automatic publication when a sensitive file would enter the public tree', (t) => {
  const root = fixture(t, {
    'index.html': '<!doctype html>',
    '.env.production': 'TOKEN=secret',
  })
  const result = inspectSourceReadyStaticSite(root)
  assert.equal(result.classification, 'unsafe_to_publish')
  assert.equal(result.route, 'stop_and_review')
  assert.match(result.blockers.join('\n'), /sensitive/i)
})

test('blocks hidden credentials and private-key content independent of extension', (t) => {
  const root = fixture(t, {
    'index.html': '<!doctype html>',
    '.npmrc': '//registry.example/:_authToken=secret',
    'downloads/blob.bin': '-----BEGIN PRIVATE KEY-----\nnot-a-real-key',
  })
  const result = inspectSourceReadyStaticSite(root)
  assert.equal(result.classification, 'unsafe_to_publish')
  assert.equal(result.blockers.length, 2)
})
