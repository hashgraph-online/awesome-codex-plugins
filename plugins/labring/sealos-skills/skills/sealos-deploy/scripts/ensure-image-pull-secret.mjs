#!/usr/bin/env node

import { execFileSync } from 'child_process'
import { ensureGhScopesWithPrompt, run } from './gh-auth-utils.mjs'

function runFile (command, args, opts = {}) {
  return execFileSync(command, args, { encoding: 'utf-8', stdio: ['ignore', 'pipe', 'pipe'], ...opts }).trim()
}

function getKubeEnv () {
  return {
    ...process.env,
    KUBECONFIG: process.env.KUBECONFIG || `${process.env.HOME}/.sealos/kubeconfig`,
  }
}

function parseImageRegistry (imageRef) {
  const text = String(imageRef || '').trim()
  if (!text) return ''

  const withoutDigest = text.split('@', 1)[0]
  const withoutTag = withoutDigest.includes(':') && withoutDigest.lastIndexOf(':') > withoutDigest.lastIndexOf('/')
    ? withoutDigest.slice(0, withoutDigest.lastIndexOf(':'))
    : withoutDigest
  const first = withoutTag.split('/', 1)[0]
  if (first.includes('.') || first.includes(':') || first === 'localhost') {
    return first
  }
  return 'docker.io'
}

async function ensureGhAuth () {
  return ensureGhScopesWithPrompt(
    ['write:packages'],
    'GHCR image pull secret creation',
  )
}

function ensureKubectl () {
  try {
    run('kubectl version --client=true --output=yaml', { env: getKubeEnv() })
  } catch {
    throw new Error('kubectl is required to create image pull secrets')
  }
}

function createOrUpdateDockerRegistrySecret ({ namespace, secretName, registry, username, password, email }) {
  const escapedPassword = password.replace(/"/g, '\\"')
  const escapedUsername = username.replace(/"/g, '\\"')
  const escapedEmail = email.replace(/"/g, '\\"')
  const script = [
    `KUBECONFIG=\${KUBECONFIG:-$HOME/.sealos/kubeconfig}`,
    'kubectl --insecure-skip-tls-verify create secret docker-registry ' +
      `${secretName} -n ${namespace} ` +
      `--docker-server=${registry} ` +
      `--docker-username="${escapedUsername}" ` +
      `--docker-password="${escapedPassword}" ` +
      `--docker-email="${escapedEmail}" ` +
      '--dry-run=client -o yaml | ' +
      'kubectl --insecure-skip-tls-verify apply -f -',
  ].join(' && ')

  runFile('sh', ['-c', script], { env: getKubeEnv() })
}

function getDeploymentImagePullSecretNames ({ namespace, deploymentName }) {
  const output = runFile(
    'kubectl',
    ['--insecure-skip-tls-verify', 'get', 'deployment', deploymentName, '-n', namespace, '-o', 'json'],
    { env: getKubeEnv() },
  )
  const deployment = JSON.parse(output)
  return (deployment.spec?.template?.spec?.imagePullSecrets || [])
    .map(secret => secret?.name)
    .filter(Boolean)
}

function ensureDeploymentImagePullSecret ({ namespace, deploymentName, secretName }) {
  if (!deploymentName) {
    return { action: 'skipped', reason: 'no deployment specified' }
  }

  const existingSecretNames = getDeploymentImagePullSecretNames({ namespace, deploymentName })
  if (existingSecretNames.includes(secretName)) {
    return { action: 'already_present', image_pull_secrets: existingSecretNames }
  }

  const mergedSecrets = [...existingSecretNames, secretName].map(name => ({ name }))
  const patch = JSON.stringify({
    spec: {
      template: {
        spec: {
          imagePullSecrets: mergedSecrets,
        },
      },
    },
  })

  runFile(
    'kubectl',
    ['--insecure-skip-tls-verify', 'patch', 'deployment', deploymentName, '-n', namespace, '--type', 'merge', '-p', patch],
    { env: getKubeEnv() },
  )

  return {
    action: 'patched',
    image_pull_secrets: mergedSecrets.map(secret => secret.name),
  }
}

function parseArgs (argv) {
  const args = argv.slice(2)
  if (args.length < 3) {
    throw new Error('Usage: node ensure-image-pull-secret.mjs <namespace> <secret-name> <image-ref> [deployment-name]')
  }

  return {
    namespace: args[0],
    secretName: args[1],
    imageRef: args[2],
    deploymentName: args[3] || null,
  }
}

try {
  const { namespace, secretName, imageRef, deploymentName } = parseArgs(process.argv)
  const registry = parseImageRegistry(imageRef)

  if (registry !== 'ghcr.io') {
    console.log(JSON.stringify({
      success: true,
      action: 'skipped',
      reason: `registry ${registry || 'unknown'} does not use gh CLI pull-secret automation`,
    }, null, 2))
    process.exit(0)
  }

  const authCheck = await ensureGhAuth()
  if (!authCheck.ok) {
    console.log(JSON.stringify({
      success: false,
      ...authCheck,
    }, null, 2))
    process.exit(1)
  }
  ensureKubectl()

  const username = run('gh api user -q .login')
  const password = run('gh auth token')
  createOrUpdateDockerRegistrySecret({
    namespace,
    secretName,
    registry,
    username,
    password,
    email: 'none@example.com',
  })
  const deployment = ensureDeploymentImagePullSecret({
    namespace,
    deploymentName,
    secretName,
  })

  console.log(JSON.stringify({
    success: true,
    action: 'created_or_updated',
    namespace,
    secret_name: secretName,
    registry,
    username,
    deployment_name: deploymentName,
    deployment,
  }, null, 2))
} catch (error) {
  const structured = error && typeof error === 'object' && 'error' in error
  console.log(JSON.stringify({
    success: false,
    ...(structured ? error : { error: error.message }),
  }, null, 2))
  process.exit(1)
}
