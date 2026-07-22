#!/usr/bin/env node

import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

import {
  classifyProject,
  exitCodeForStatus,
} from './workload-eligibility.mjs'

const ELIGIBILITY_SCRIPT = fileURLToPath(new URL('./workload-eligibility.mjs', import.meta.url))

function createFixture(t, files) {
  const fixtureDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sealos-eligibility-test-'))
  t.after(() => fs.rmSync(fixtureDir, { recursive: true, force: true }))

  for (const [relativePath, contents] of Object.entries(files)) {
    const filePath = path.join(fixtureDir, relativePath)
    fs.mkdirSync(path.dirname(filePath), { recursive: true })
    const serialized = typeof contents === 'string' ? contents : `${JSON.stringify(contents, null, 2)}\n`
    fs.writeFileSync(filePath, serialized)
  }

  return fixtureDir
}

function assertValidDecision(result) {
  const supportedStatuses = new Set(['eligible', 'ineligible', 'needs_review'])
  const supportedWorkloads = new Set([
    'web_service', 'static_web', 'worker', 'scheduled_job', 'remote_desktop',
    'desktop_gui', 'mobile_client', 'cli', 'library', 'browser_extension',
    'hardware_dependent', 'mixed', 'unknown',
  ])
  const safeRelativePath = (value) => {
    const normalized = value.replaceAll('\\', '/')
    return !path.isAbsolute(value) && !/^[A-Za-z]:\//.test(normalized) && !normalized.split('/').includes('..')
  }

  assert.equal(result.version, '1.0')
  assert.equal(Number.isNaN(Date.parse(result.generated_at)), false)
  assert.equal(supportedStatuses.has(result.status), true)
  assert.equal(supportedWorkloads.has(result.workload_type), true)
  assert.equal(safeRelativePath(result.target_path), true)
  assert.ok(result.reason_codes.length > 0)
  assert.ok(result.evidence.length > 0)
  assert.ok(Array.isArray(result.candidates))
  assert.ok(['deterministic', 'ai-review'].includes(result.source))

  for (const candidate of result.candidates) {
    assert.equal(safeRelativePath(candidate.path), true)
    assert.ok(candidate.evidence.length > 0)
  }

  if (result.status === 'eligible') {
    assert.ok(result.candidates.some((candidate) =>
      candidate.path === result.target_path && candidate.workload_type === result.workload_type,
    ))
  }
  if (result.status === 'ineligible') assert.equal(result.candidates.length, 0)
}

test('rejects a desktop-only Electron unit even when cloud-readiness artifacts exist', (t) => {
  const fixtureDir = createFixture(t, {
    'package.json': {
      scripts: { start: 'electron .', build: 'electron-builder' },
      dependencies: { electron: '^35.0.0', express: '^5.0.0' },
      devDependencies: { 'electron-builder': '^26.0.0' },
    },
    'src/main.js': 'const { BrowserWindow, app } = require("electron")\napp.whenReady(() => new BrowserWindow())\n',
    '.env.example': 'PORT=3000\n',
    'Dockerfile': 'FROM node:22-slim\nHEALTHCHECK CMD true\n',
    'compose.yaml': 'services:\n  desktop:\n    build: .\n',
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'ineligible')
  assert.equal(result.workload_type, 'desktop_gui')
  assert.deepEqual(result.reason_codes, ['DESKTOP_GUI_ONLY'])
  assert.equal(exitCodeForStatus(result.status), 2)
  assertValidDecision(result)
})

test('accepts an Express service when Electron is only an unused dev dependency', (t) => {
  const fixtureDir = createFixture(t, {
    'package.json': {
      private: true,
      scripts: { start: 'node server.js' },
      dependencies: { express: '^5.0.0' },
      devDependencies: { electron: '^35.0.0' },
    },
    'server.js': 'const express = require("express")\nexpress().listen(process.env.PORT || 3000)\n',
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'eligible')
  assert.equal(result.workload_type, 'web_service')
  assert.deepEqual(result.reason_codes, ['SERVER_WORKLOAD'])
  assertValidDecision(result)
})

test('accepts an Express service when a mobile SDK is only an unused dev dependency', (t) => {
  const fixtureDir = createFixture(t, {
    'package.json': {
      private: true,
      scripts: { start: 'node server.js' },
      dependencies: { express: '^5.0.0' },
      devDependencies: { expo: '^53.0.0' },
    },
    'server.js': 'const express = require("express")\nexpress().listen(process.env.PORT || 3000)\n',
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'eligible')
  assert.equal(result.workload_type, 'web_service')
  assert.deepEqual(result.reason_codes, ['SERVER_WORKLOAD'])
  assertValidDecision(result)
})

test('requires review when one package has desktop and server entry points', (t) => {
  const fixtureDir = createFixture(t, {
    'package.json': {
      private: true,
      scripts: {
        start: 'node server.js',
        desktop: 'electron .',
      },
      dependencies: { express: '^5.0.0' },
      devDependencies: { electron: '^35.0.0' },
    },
    'server.js': 'const express = require("express")\nexpress().listen(process.env.PORT || 3000)\n',
    'desktop.js': 'const { BrowserWindow } = require("electron")\nnew BrowserWindow()\n',
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'needs_review')
  assert.equal(result.workload_type, 'mixed')
  assert.deepEqual(result.reason_codes, ['CONFLICTING_WORKLOAD_EVIDENCE'])
  assert.ok(result.candidates.some((candidate) => candidate.workload_type === 'web_service'))
  assertValidDecision(result)
})

test('requires review when one package has mobile and server entry points', (t) => {
  const fixtureDir = createFixture(t, {
    'package.json': {
      private: true,
      scripts: {
        start: 'node server.js',
        mobile: 'expo start',
      },
      dependencies: { express: '^5.0.0', expo: '^53.0.0' },
    },
    'server.js': 'const express = require("express")\nexpress().listen(process.env.PORT || 3000)\n',
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'needs_review')
  assert.equal(result.workload_type, 'mixed')
  assert.deepEqual(result.reason_codes, ['CONFLICTING_WORKLOAD_EVIDENCE'])
  assert.ok(result.candidates.some((candidate) => candidate.workload_type === 'web_service'))
  assertValidDecision(result)
})

test('CLI emits structured ineligible JSON without writing project files and exits with code 2', (t) => {
  const fixtureDir = createFixture(t, {
    'package.json': {
      scripts: { start: 'electron .' },
      dependencies: { electron: '^35.0.0' },
    },
  })

  const run = spawnSync(process.execPath, [ELIGIBILITY_SCRIPT, fixtureDir], { encoding: 'utf-8' })
  assert.equal(run.status, 2, run.stderr)
  const result = JSON.parse(run.stdout)
  assert.equal(result.status, 'ineligible')
  assertValidDecision(result)
  assert.equal(fs.existsSync(path.join(fixtureDir, '.sealos')), false)
})

test('accepts a standalone static web build without requiring an application listener', (t) => {
  const fixtureDir = createFixture(t, {
    'package.json': {
      private: true,
      scripts: { build: 'vite build' },
      dependencies: { react: '^19.0.0', vite: '^7.0.0' },
    },
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'eligible')
  assert.equal(result.workload_type, 'static_web')
  assert.deepEqual(result.reason_codes, ['STATIC_WEB_BUILD'])
  assertValidDecision(result)
})

test('does not accept a Node server dependency without an application runtime command', (t) => {
  const fixtureDir = createFixture(t, {
    'package.json': {
      private: true,
      dependencies: { express: '^5.0.0' },
    },
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'needs_review')
  assert.equal(result.workload_type, 'unknown')
  assertValidDecision(result)
})

test('accepts a non-interactive queue worker without an inbound HTTP port', (t) => {
  const fixtureDir = createFixture(t, {
    'package.json': {
      private: true,
      scripts: { worker: 'node worker.js' },
      dependencies: { bullmq: '^5.0.0' },
    },
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'eligible')
  assert.equal(result.workload_type, 'worker')
  assertValidDecision(result)
})

test('keeps a worker dependency blocked until a worker command is present', (t) => {
  const fixtureDir = createFixture(t, {
    'requirements.txt': 'celery==5.5.0\n',
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'needs_review')
  assert.equal(result.workload_type, 'unknown')
  assertValidDecision(result)
})

test('accepts a command-line program when it has an explicit scheduled-job contract', (t) => {
  const fixtureDir = createFixture(t, {
    'package.json': {
      name: 'report-cli',
      bin: { report: './cli.js' },
    },
    'deploy/cronjob.yaml': `apiVersion: batch/v1
kind: CronJob
spec:
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: report
              image: example/report
              command: ["node", "cli.js"]
`,
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'eligible')
  assert.equal(result.workload_type, 'scheduled_job')
  assertValidDecision(result)
})

test('does not accept a Rust web-framework library without an executable target', (t) => {
  const fixtureDir = createFixture(t, {
    'Cargo.toml': '[package]\nname = "web-library"\n[dependencies]\naxum = "0.8"\n',
    'src/lib.rs': 'pub fn middleware() {}\n',
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'needs_review')
  assert.equal(result.workload_type, 'unknown')
  assertValidDecision(result)
})

test('blocks a desktop and API monorepo for review', (t) => {
  const fixtureDir = createFixture(t, {
    'package.json': { private: true, workspaces: ['apps/*'] },
    'apps/desktop/package.json': {
      private: true,
      scripts: { start: 'electron .' },
      dependencies: { electron: '^35.0.0', vite: '^7.0.0' },
    },
    'apps/api/package.json': {
      private: true,
      scripts: { start: 'node server.js' },
      dependencies: { express: '^5.0.0' },
    },
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'needs_review')
  assert.equal(result.workload_type, 'mixed')
  assert.deepEqual(result.reason_codes, ['MIXED_REPOSITORY_REQUIRES_REVIEW'])
  assert.ok(result.candidates.some((candidate) => candidate.path === 'apps/api'))
  assertValidDecision(result)
})

test('blocks multiple root and nested workloads for review', (t) => {
  const fixtureDir = createFixture(t, {
    'requirements.txt': 'FastAPI==0.116.0\n',
    'main.py': 'from fastapi import FastAPI\napp = FastAPI()\n',
    'pyproject.toml': '[project.scripts]\nmanage = "demo.cli:main"\n',
    'frontend/package.json': {
      private: true,
      scripts: { start: 'nuxt start' },
      dependencies: { nuxt: '^4.0.0' },
    },
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'needs_review')
  assert.equal(result.workload_type, 'mixed')
  assert.deepEqual(result.reason_codes, ['MIXED_REPOSITORY_REQUIRES_REVIEW'])
  assert.ok(result.candidates.some((candidate) => candidate.path === '.'))
  assert.ok(result.candidates.some((candidate) => candidate.path === 'frontend'))
  assertValidDecision(result)
})

test('blocks a repository whose only supported workload is nested', (t) => {
  const fixtureDir = createFixture(t, {
    'apps/api/package.json': {
      private: true,
      scripts: { start: 'node server.js' },
      dependencies: { express: '^5.0.0' },
    },
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'needs_review')
  assert.equal(result.workload_type, 'mixed')
  assert.deepEqual(result.reason_codes, ['NESTED_WORKLOAD_REQUIRES_REVIEW'])
  assert.ok(result.candidates.some((candidate) => candidate.path === 'apps/api'))
  assertValidDecision(result)
})

test('does not offer a renderer nested inside a desktop package as static web', (t) => {
  const fixtureDir = createFixture(t, {
    'apps/desktop/package.json': {
      private: true,
      scripts: { start: 'electron .' },
      dependencies: { electron: '^35.0.0' },
    },
    'apps/desktop/renderer/package.json': {
      private: true,
      scripts: { build: 'vite build' },
      dependencies: { vite: '^7.0.0' },
    },
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'ineligible')
  assert.equal(result.workload_type, 'desktop_gui')
  assert.equal(result.candidates.length, 0)
  assertValidDecision(result)
})

test('rejects an explicit CLI package with no cloud workload', (t) => {
  const fixtureDir = createFixture(t, {
    'package.json': {
      name: 'demo-cli',
      bin: { demo: './cli.js' },
    },
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'ineligible')
  assert.equal(result.workload_type, 'cli')
  assertValidDecision(result)
})

test('does not mistake a Python web framework package for a deployable service', (t) => {
  const fixtureDir = createFixture(t, {
    'pyproject.toml': `[project]
name = "Flask"
classifiers = ["Topic :: Software Development :: Libraries :: Application Frameworks"]
dependencies = ["click>=8"]

[project.scripts]
flask = "flask.cli:main"

[build-system]
requires = ["flit_core"]
`,
    'src/flask/app.py': 'class Flask:\n  pass\n',
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'ineligible')
  assert.equal(result.workload_type, 'library')
  assert.deepEqual(result.reason_codes, ['LIBRARY_ONLY'])
  assertValidDecision(result)
})

test('accepts a Python web app only when dependency and entry-point evidence agree', (t) => {
  const fixtureDir = createFixture(t, {
    'requirements.txt': 'Flask==3.1.0\ngunicorn==23.0.0\n',
    'app.py': 'from flask import Flask\napp = Flask(__name__)\n',
    'Procfile': 'web: gunicorn app:app\n',
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'eligible')
  assert.equal(result.workload_type, 'web_service')
  assertValidDecision(result)
})

test('does not treat an Electron package nested under examples as the repository workload', (t) => {
  const fixtureDir = createFixture(t, {
    'README.md': '# Library docs\n',
    'examples/desktop/package.json': {
      scripts: { start: 'electron .' },
      dependencies: { electron: '^35.0.0' },
    },
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'needs_review')
  assert.equal(result.workload_type, 'unknown')
  assertValidDecision(result)
})

test('rejects a Vite-powered browser extension instead of treating it as static web', (t) => {
  const fixtureDir = createFixture(t, {
    'package.json': {
      private: true,
      scripts: { build: 'vite build' },
      dependencies: { vite: '^7.0.0' },
    },
    'manifest.json': { manifest_version: 3, name: 'Demo extension', version: '1.0.0' },
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'ineligible')
  assert.equal(result.workload_type, 'browser_extension')
  assertValidDecision(result)
})

test('blocks a mixed firmware and cloud API repository for review', (t) => {
  const fixtureDir = createFixture(t, {
    'firmware/platformio.ini': '[env:board]\nplatform = espressif32\n',
    'services/api/package.json': {
      private: true,
      scripts: { start: 'node server.js' },
      dependencies: { express: '^5.0.0' },
    },
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'needs_review')
  assert.equal(result.workload_type, 'mixed')
  assert.deepEqual(result.reason_codes, ['MIXED_REPOSITORY_REQUIRES_REVIEW'])
  assert.ok(result.candidates.some((candidate) => candidate.path === 'services/api'))
  assertValidDecision(result)
})

test('keeps an explicitly serverized desktop container blocked for review', (t) => {
  const fixtureDir = createFixture(t, {
    'package.json': {
      scripts: { start: 'electron .' },
      dependencies: { electron: '^35.0.0' },
    },
    'Dockerfile': 'FROM node:22\nRUN apt-get update && apt-get install -y xvfb novnc\nENV DISPLAY=:99\n',
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'needs_review')
  assert.equal(result.workload_type, 'remote_desktop')
  assert.equal(exitCodeForStatus(result.status), 3)
  assertValidDecision(result)
})

test('fails closed when deterministic evidence is insufficient without writing project files', (t) => {
  const fixtureDir = createFixture(t, {
    'README.md': '# Source repository with no runnable target\n',
  })

  const result = classifyProject(fixtureDir)
  assert.equal(result.status, 'needs_review')
  assert.equal(result.workload_type, 'unknown')
  assertValidDecision(result)
  assert.equal(fs.existsSync(path.join(fixtureDir, '.sealos')), false)
})
