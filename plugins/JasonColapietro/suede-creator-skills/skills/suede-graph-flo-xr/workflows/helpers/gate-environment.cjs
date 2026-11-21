'use strict'

const sensitiveSegments = new Set([
  'ACCESS_KEY',
  'ACCESSKEY',
  'AMQP_URL',
  'API_KEY',
  'APIKEY',
  'AUTHORIZATION',
  'AUTHTOKEN',
  'AUTH_TOKEN',
  'BEARER',
  'BROKER_URL',
  'CLIENT_SECRET',
  'CLIENTSECRET',
  'CONNECTION_STRING',
  'COOKIE',
  'CREDENTIAL',
  'CREDENTIALS',
  'DATABASE_URL',
  'DATABASE_URI',
  'DB_URL',
  'DB_URI',
  'DSN',
  'JWT',
  'LICENSE_KEY',
  'LICENCE_KEY',
  'MONGODB_URI',
  'OAUTH',
  'PASSWD',
  'PASSWORD',
  'PRIVATE_KEY',
  'PRIVATEKEY',
  'REDIS_URL',
  'REFRESH_TOKEN',
  'REFRESHTOKEN',
  'SECRET',
  'SESSION',
  'SIGNING_KEY',
  'SIGNINGKEY',
  'TOKEN',
])

const sensitiveNames = new Set([
  'ALL_PROXY',
  'AWS_CONFIG_FILE',
  'AWS_SHARED_CREDENTIALS_FILE',
  'AZURE_CONFIG_DIR',
  'BASH_ENV',
  'CLOUDSDK_CONFIG',
  'DOCKER_CONFIG',
  'ENV',
  'GH_CONFIG_DIR',
  'GIT_ASKPASS',
  'GIT_HTTP_EXTRAHEADER',
  'GOOGLE_APPLICATION_CREDENTIALS',
  'GPG_AGENT_INFO',
  'HTTPS_PROXY',
  'HTTP_PROXY',
  'KUBECONFIG',
  'LD_PRELOAD',
  'MYSQL_PWD',
  'NETRC',
  'NODE_OPTIONS',
  'NO_PROXY',
  'NPM_CONFIG_USERCONFIG',
  'PERL5OPT',
  'PGPASSFILE',
  'PGPASSWORD',
  'PIP_CONFIG_FILE',
  'PYTHONPATH',
  'PYTHONSTARTUP',
  'RUBYOPT',
  'SSH_ASKPASS',
  'SSH_AUTH_SOCK',
  'UV_CONFIG_FILE',
  'XDG_CONFIG_HOME',
  'XDG_CACHE_HOME',
  'XDG_DATA_HOME',
])

const sensitivePrefixes = ['DYLD_', 'GIT_CONFIG_', 'GIT_SSH']

function normalizeName(name) {
  return String(name).toUpperCase().replace(/[^A-Z0-9]+/g, '_')
}

function isSensitiveName(name) {
  const normalized = normalizeName(name)
  if (sensitiveNames.has(normalized)) return true
  if (sensitivePrefixes.some(prefix => normalized.startsWith(prefix))) return true

  const bounded = `_${normalized}_`
  return [...sensitiveSegments].some(segment => bounded.includes(`_${segment}_`))
}

function sanitizeGateEnvironment(env) {
  return Object.fromEntries(
    Object.entries(env).filter(([name]) => !isSensitiveName(name))
  )
}

module.exports = { sanitizeGateEnvironment }
