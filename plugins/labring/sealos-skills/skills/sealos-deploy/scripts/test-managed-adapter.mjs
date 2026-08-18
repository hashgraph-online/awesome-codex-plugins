#!/usr/bin/env node

import assert from 'node:assert/strict'
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import test from 'node:test'
import {
  MANAGED_INPUTS_PATH,
  adaptTemplateForManagedMode,
  isManagedMode,
  managedIdentityLabels,
  prepareManagedTemplate,
  requireManagedEnvironment,
  sha256Text,
} from './managed-adapter.mjs'

function managedEnv(overrides = {}) {
  return {
    SEALAI_DEPLOY_MODE: 'managed',
    SEALAI_DEPLOY_TASK_ID: 'task-123',
    SEALAI_PROJECT_ID: 'project-456',
    SEALAI_NAMESPACE: 'ns-demo',
    SEALAI_INPUTS_PATH: MANAGED_INPUTS_PATH,
    SEALAI_TURN_DEADLINE_AT: '2026-08-06T12:00:00.000Z',
    ...overrides,
  }
}

const TEMPLATE = `apiVersion: app.sealos.io/v1
kind: Template
metadata:
  name: demo
  labels:
    existing: keep
spec:
  templateType: inline
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo
  labels:
    app: demo
    brain.io/project-id: stale-project
spec:
  replicas: 1
  selector:
    matchLabels:
      app: demo
  template:
    metadata:
      labels:
        app: demo
    spec:
      containers:
        - name: demo
          image: example/demo:1.0.0
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: demo-job
spec:
  jobTemplate:
    spec:
      template:
        metadata:
          labels: {}
        spec:
          restartPolicy: Never
          containers:
            - name: demo
              image: example/demo:1.0.0
`

test('local mode is a no-op and does not add Brain labels', () => {
  const result = adaptTemplateForManagedMode(TEMPLATE, {})
  assert.equal(isManagedMode({}), false)
  assert.equal(result.managed, false)
  assert.equal(result.template, TEMPLATE)
  assert.equal(result.labelsApplied, 0)
})

test('managed environment is strict without a Brain-owned Instance identity', () => {
  const env = managedEnv()
  assert.deepEqual(requireManagedEnvironment(env), {
    taskId: 'task-123',
    projectId: 'project-456',
    namespace: 'ns-demo',
    inputsPath: MANAGED_INPUTS_PATH,
    turnDeadlineAt: '2026-08-06T12:00:00.000Z',
  })
  assert.deepEqual(managedIdentityLabels(env), {
    'brain.io/managed-by': 'brain',
    'brain.io/deployment-kind': 'template',
    'brain.io/project-id': 'project-456',
  })
  assert.throws(
    () => requireManagedEnvironment({ ...env, SEALAI_INPUTS_PATH: '/tmp/inputs.json' }),
    /fixed input path/,
  )
})

test('managed adaptation preserves the exact Template without Brain labels', () => {
  const result = adaptTemplateForManagedMode(TEMPLATE, managedEnv())
  assert.equal(result.managed, true)
  assert.equal(result.labelsApplied, 0)
  assert.equal(result.template, TEMPLATE)
  assert.doesNotMatch(result.template, /brain\.io\/deployment-name/)
  assert.equal((result.template.match(/^---$/gm) ?? []).length, 2)
  assert.equal(result.sha256, sha256Text(result.template))
})

test('managed adaptation does not mutate workload metadata', () => {
  const template = `apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo
spec:
  template:
    spec:
      containers: []
`
  const result = adaptTemplateForManagedMode(template, managedEnv())
  assert.equal(result.template, template)
})

test('prepareManagedTemplate writes atomically and returns the final digest', () => {
  const root = mkdtempSync(join(tmpdir(), 'sealos-managed-adapter-'))
  try {
    const templatePath = join(root, 'index.yaml')
    writeFileSync(templatePath, TEMPLATE)
    const result = prepareManagedTemplate(templatePath, managedEnv())
    const contents = readFileSync(templatePath, 'utf8')
    assert.equal(result.path, templatePath)
    assert.equal(result.sha256, sha256Text(contents))
    assert.equal(contents, TEMPLATE)
  } finally {
    rmSync(root, { recursive: true, force: true })
  }
})
