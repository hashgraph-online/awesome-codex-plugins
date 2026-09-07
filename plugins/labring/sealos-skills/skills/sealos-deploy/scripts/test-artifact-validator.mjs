#!/usr/bin/env node

import assert from 'node:assert/strict'
import test from 'node:test'

import { validateArtifactData } from './artifact-validator.mjs'

function stateWithUrl(url) {
  return {
    version: '1.0',
    last_deploy: {
      app_name: 'demo',
      app_host: 'demo-public',
      namespace: 'ns-demo',
      region: 'usw-1.sealos.io',
      image: 'example/demo:1',
      docker_hub_user: null,
      repo_name: 'demo',
      url,
      deployed_at: '2026-08-05T00:00:00Z',
      last_updated_at: '2026-08-05T00:00:00Z',
    },
    history: [
      {
        at: '2026-08-05T00:00:00Z',
        action: 'deploy',
        image: 'example/demo:1',
        method: 'template-api',
        status: 'success',
        note: 'Initial deployment',
      },
    ],
  }
}

test('accepts an App domain that differs from the control-plane region', () => {
  const result = validateArtifactData(
    'state',
    stateWithUrl('https://demo-public.usw-1.sealos.app'),
  )

  assert.deepEqual(result.errors, [])
  assert.equal(result.valid, true)
})

test('accepts a custom App domain', () => {
  const result = validateArtifactData('state', stateWithUrl('https://demo.example.com'))

  assert.deepEqual(result.errors, [])
  assert.equal(result.valid, true)
})
