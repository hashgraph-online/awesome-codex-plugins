#!/usr/bin/env node
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import http from 'node:http'
import os from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const SKILL_DIR = path.dirname(__dirname)
const TEMPLATE_PATH = path.join(SKILL_DIR, 'assets', 'canvas-template.html')

const SAFE_RESOURCE_KINDS = [
  'deployment',
  'pod',
  'service',
  'ingress',
  'persistentvolumeclaim',
  'event'
]

function main() {
  const args = parseArgs(process.argv.slice(2))
  const workDir = path.resolve(args.workDir || process.cwd())
  const statePath = path.join(workDir, '.sealos', 'state.json')

  const state = readJsonIfExists(statePath)
  const lastDeploy = state?.last_deploy
  if (!lastDeploy?.app_name || !lastDeploy?.namespace) {
    return printStop('not_deployed', 'This project has not been deployed by Sealos Skills yet. Run /sealos-deploy first, then run /sealos-canvas again.')
  }

  let resources
  const fixturePath = process.env.SEALOS_CANVAS_KUBE_FIXTURE
  if (fixturePath) {
    resources = readJson(path.resolve(fixturePath))
  } else {
    const kubeconfig = path.join(os.homedir(), '.sealos', 'kubeconfig')
    if (!fs.existsSync(kubeconfig)) {
      return printStop('kubeconfig_missing', 'Sealos kubeconfig was not found at ~/.sealos/kubeconfig. Run /sealos-deploy first, then run /sealos-canvas again.')
    }

    const kubectl = findKubectl()
    if (!kubectl) {
      return printStop('kubectl_missing', 'kubectl is required to view deployed Sealos resources. Install kubectl, then run /sealos-canvas again.')
    }

    resources = readLiveResources({ kubectl, kubeconfig, namespace: lastDeploy.namespace })
  }

  const theme = extractTheme(workDir)
  const graph = buildGraph(lastDeploy, resources)
  const canvasModel = buildCanvasModel({ graph, theme, lastDeploy })
  const html = renderHtml({ canvasModel })
  const outputDir = path.join(workDir, '.sealos', 'canvas')
  const outputPath = path.join(outputDir, 'index.html')

  fs.mkdirSync(outputDir, { recursive: true })
  fs.writeFileSync(outputPath, html)

  if (args.serve) {
    return serveCanvas({ host: args.host, port: args.port, outputDir, outputPath, graph, lastDeploy })
  }

  return printJson({
    ok: true,
    html_path: outputPath,
    node_count: graph.nodes.length,
    edge_count: graph.edges.length,
    app_url: lastDeploy.url || ''
  })
}

function parseArgs(argv) {
  const args = { serve: true, host: '127.0.0.1', port: 0 }
  for (let index = 0; index < argv.length; index++) {
    const item = argv[index]
    if (item === '--work-dir') {
      args.workDir = argv[++index]
    } else if (item === '--host') {
      args.host = argv[++index]
    } else if (item === '--port') {
      args.port = Number(argv[++index])
    } else if (item === '--no-serve') {
      args.serve = false
    } else if (item === '--help' || item === '-h') {
      process.stdout.write('Usage: node generate-canvas.mjs --work-dir <repo-dir> [--host 127.0.0.1] [--port 0] [--no-serve]\n')
      process.exit(0)
    }
  }
  return args
}

function readJsonIfExists(filePath) {
  if (!fs.existsSync(filePath)) return null
  try {
    return readJson(filePath)
  } catch {
    return null
  }
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'))
}

function printStop(reason, message) {
  printJson({ ok: false, reason, message })
}

function printJson(data) {
  process.stdout.write(`${JSON.stringify(data, null, 2)}\n`)
}

function serveCanvas({ host, port, outputDir, outputPath, graph, lastDeploy }) {
  const server = http.createServer((request, response) => {
    const url = new URL(request.url || '/', `http://${host}`)
    const pathname = url.pathname === '/' ? '/index.html' : url.pathname

    if (pathname !== '/index.html') {
      response.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' })
      response.end('Not found')
      return
    }

    fs.createReadStream(path.join(outputDir, 'index.html'))
      .on('error', () => {
        response.writeHead(500, { 'content-type': 'text/plain; charset=utf-8' })
        response.end('Canvas HTML is unavailable')
      })
      .on('open', () => {
        response.writeHead(200, {
          'content-type': 'text/html; charset=utf-8',
          'cache-control': 'no-store'
        })
      })
      .pipe(response)
  })

  server.on('error', (error) => {
    printJson({
      ok: false,
      reason: 'server_start_failed',
      message: `Failed to start local Sealos canvas server: ${error.message}`
    })
    process.exitCode = 1
  })

  server.listen(port, host, () => {
    const address = server.address()
    const actualPort = typeof address === 'object' && address ? address.port : port
    const localUrl = `http://${host}:${actualPort}/index.html`
    printJson({
      ok: true,
      local_url: localUrl,
      html_path: outputPath,
      node_count: graph.nodes.length,
      edge_count: graph.edges.length,
      app_url: lastDeploy.url || ''
    })
  })

  const shutdown = () => {
    server.close(() => process.exit(0))
  }
  process.on('SIGINT', shutdown)
  process.on('SIGTERM', shutdown)
}

function findKubectl() {
  const candidates = ['kubectl', path.join(os.homedir(), '.agents', 'bin', 'kubectl')]
  for (const candidate of candidates) {
    try {
      execFileSync(candidate, ['version', '--client=true'], { stdio: 'ignore', timeout: 10000 })
      return candidate
    } catch {
      // Try the next candidate.
    }
  }
  return null
}

function readLiveResources({ kubectl, kubeconfig, namespace }) {
  const env = { ...process.env, KUBECONFIG: kubeconfig }
  const resources = {}

  for (const kind of SAFE_RESOURCE_KINDS) {
    try {
      const stdout = execFileSync(
        kubectl,
        ['--insecure-skip-tls-verify', '--request-timeout=8s', 'get', kind, '-n', namespace, '-o', 'json'],
        { env, encoding: 'utf8', timeout: 12000, maxBuffer: 12 * 1024 * 1024 }
      )
      resources[toResourceKey(kind)] = JSON.parse(stdout)
    } catch (error) {
      resources[toResourceKey(kind)] = { apiVersion: 'v1', items: [], error: readableExecError(error) }
    }
  }

  resources.configmaps = readConfigMapSummaries({ kubectl, env, namespace })
  resources.secrets = readSecretSummaries({ kubectl, env, namespace })

  return resources
}

function readConfigMapSummaries({ kubectl, env, namespace }) {
  try {
    const template = '{{range .items}}{{.metadata.name}}{{"\\t"}}{{len .data}}{{"\\n"}}{{end}}'
    const stdout = execFileSync(
      kubectl,
      ['--insecure-skip-tls-verify', '--request-timeout=8s', 'get', 'configmap', '-n', namespace, '-o', `go-template=${template}`],
      { env, encoding: 'utf8', timeout: 12000, maxBuffer: 1024 * 1024 }
    )
    return {
      apiVersion: 'v1',
      items: stdout.trim().split('\n').filter(Boolean).map((line) => {
        const [name, keyCount] = line.split('\t')
        return { metadata: { name }, dataKeyCount: Number(keyCount || 0) }
      })
    }
  } catch (error) {
    return { apiVersion: 'v1', items: [], error: readableExecError(error) }
  }
}

function readSecretSummaries({ kubectl, env, namespace }) {
  try {
    const template = '{{range .items}}{{.metadata.name}}{{"\\t"}}{{.type}}{{"\\n"}}{{end}}'
    const stdout = execFileSync(
      kubectl,
      ['--insecure-skip-tls-verify', '--request-timeout=8s', 'get', 'secret', '-n', namespace, '-o', `go-template=${template}`],
      { env, encoding: 'utf8', timeout: 12000, maxBuffer: 1024 * 1024 }
    )
    return {
      apiVersion: 'v1',
      items: stdout.trim().split('\n').filter(Boolean).map((line) => {
        const [name, type] = line.split('\t')
        return { metadata: { name }, type: type || 'Opaque' }
      })
    }
  } catch (error) {
    return { apiVersion: 'v1', items: [], error: readableExecError(error) }
  }
}

function readableExecError(error) {
  const text = String(error.stderr || error.message || error)
  return text.trim().slice(0, 500)
}

function toResourceKey(kind) {
  const map = {
    deployment: 'deployments',
    pod: 'pods',
    service: 'services',
    ingress: 'ingresses',
    persistentvolumeclaim: 'persistentvolumeclaims',
    configmap: 'configmaps',
    secret: 'secrets',
    event: 'events'
  }
  return map[kind] || kind
}

function extractTheme(workDir) {
  const theme = {
    accent: '#6c55ff',
    radius: '8px',
    font: 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
  }

  const files = [
    'tailwind.config.js',
    'tailwind.config.ts',
    'src/app/globals.css',
    'app/globals.css',
    'src/styles/globals.css',
    'src/styles/theme.css',
    'styles/globals.css',
    'package.json'
  ].map((item) => path.join(workDir, item))

  for (const filePath of files) {
    if (!fs.existsSync(filePath) || fs.statSync(filePath).size > 200000) continue
    const content = fs.readFileSync(filePath, 'utf8')
    const accent = findAccent(content)
    if (accent) theme.accent = accent

    const radius = content.match(/--radius:\s*([^;\n]+)/)?.[1]?.trim()
      || content.match(/borderRadius:\s*\{[\s\S]*?(?:DEFAULT|lg):\s*['"]([^'"]+)['"]/)?.[1]
    if (radius && radius.length < 32) theme.radius = normalizeRadius(radius)

    const font = content.match(/--font-(?:sans|body):\s*([^;\n]+)/)?.[1]?.trim()
      || content.match(/fontFamily:\s*\{[\s\S]*?sans:\s*\[([^\]]+)/)?.[1]?.replaceAll("'", '').replaceAll('"', '').trim()
    if (font && font.length < 120) theme.font = `${font}, ${theme.font}`
  }

  return theme
}

function findAccent(content) {
  const patterns = [
    /--(?:primary|accent|brand):\s*(#[0-9a-fA-F]{3,8})/,
    /(?:primary|accent|brand):\s*['"](#[0-9a-fA-F]{3,8})['"]/
  ]
  for (const pattern of patterns) {
    const match = content.match(pattern)
    if (match) return match[1] || match[0]
  }
  return null
}

function normalizeRadius(value) {
  if (value.includes('var(') || value.includes('calc(')) return '8px'
  if (/^\d+(\.\d+)?(px|rem|em)$/.test(value)) {
    const match = value.match(/^(\d+(?:\.\d+)?)(px|rem|em)$/)
    if (!match) return '8px'
    if (match[2] === 'px') return `${Math.min(Number(match[1]), 8)}px`
    if (match[2] === 'rem') return `${Math.min(Number(match[1]), 0.5)}rem`
    return `${Math.min(Number(match[1]), 0.5)}em`
  }
  return '8px'
}

function buildGraph(lastDeploy, resources) {
  const appName = lastDeploy.app_name
  const namespace = lastDeploy.namespace
  const deployments = items(resources.deployments)
  const pods = items(resources.pods)
  const services = items(resources.services)
  const ingresses = items(resources.ingresses)
  const pvcs = items(resources.persistentvolumeclaims)
  const configmaps = items(resources.configmaps)
  const secrets = items(resources.secrets)
  const events = sanitizeEvents(items(resources.events), appName)

  const deployment = deployments.find((item) => nameOf(item) === appName)
    || deployments.find((item) => nameOf(item)?.startsWith(appName))
    || deployments.find((item) => includesAppLabel(item, appName))

  const deploymentName = nameOf(deployment) || appName
  const selector = deployment?.spec?.selector?.matchLabels || {}
  const relatedPods = pods.filter((pod) => isOwnedBy(pod, deploymentName) || labelsMatch(pod.metadata?.labels, selector) || nameOf(pod)?.startsWith(deploymentName))
  const relatedServices = services.filter((service) => serviceTargetsPods(service, relatedPods) || nameOf(service) === appName || includesAppLabel(service, appName))
  const relatedIngresses = ingresses.filter((ingress) => ingressTargetsServices(ingress, relatedServices) || ingressHostsUrl(ingress, lastDeploy.url))
  const volumeClaims = collectVolumeClaims(deployment, relatedPods, pvcs)
  const configRefs = collectConfigRefs(deployment, relatedPods, configmaps)
  const secretRefs = collectSecretRefs(deployment, relatedPods, secrets)

  const nodes = []
  const edges = []

  const appNode = {
    id: 'app',
    kind: 'Application',
    title: appName,
    subtitle: lastDeploy.url || `${deploymentName}.${namespace}`,
    status: statusForDeployment(deployment),
    statusText: statusTextForDeployment(deployment),
    icon: 'app',
    meta: [
      ['Namespace', namespace],
      ['Image', lastDeploy.image || firstContainerImage(deployment) || 'unknown'],
      ['Updated', lastDeploy.last_updated_at || lastDeploy.deployed_at || 'unknown']
    ],
    attachments: volumeClaims.map((pvc) => ({ icon: 'volume', label: `${nameOf(pvc)} volume` }))
  }
  nodes.push(appNode)

  if (relatedIngresses.length > 0 || lastDeploy.url) {
    nodes.push({
      id: 'ingress',
      kind: 'Ingress',
      title: relatedIngresses[0] ? nameOf(relatedIngresses[0]) : 'Public URL',
      subtitle: lastDeploy.url || firstIngressHost(relatedIngresses[0]) || 'external access',
      status: 'ready',
      statusText: 'Published',
      icon: 'ingress',
      meta: [
        ['Host', stripProtocol(lastDeploy.url) || firstIngressHost(relatedIngresses[0]) || 'unknown'],
        ['Rules', String(relatedIngresses.reduce((total, ingress) => total + (ingress.spec?.rules?.length || 0), 0) || 1)]
      ]
    })
    edges.push({ from: 'ingress', to: 'app', label: 'routes', strong: true })
  }

  if (relatedServices.length > 0) {
    nodes.push({
      id: 'service',
      kind: 'Service',
      title: relatedServices.map(nameOf).filter(Boolean).join(', '),
      subtitle: 'Cluster networking',
      status: 'ready',
      statusText: `${relatedServices.length} service${relatedServices.length === 1 ? '' : 's'}`,
      icon: 'service',
      meta: [
        ['Ports', relatedServices.flatMap((svc) => (svc.spec?.ports || []).map((port) => `${port.port}${port.targetPort ? `->${port.targetPort}` : ''}`)).join(', ') || 'none'],
        ['Type', [...new Set(relatedServices.map((svc) => svc.spec?.type || 'ClusterIP'))].join(', ')]
      ]
    })
    edges.push({ from: 'app', to: 'service', label: 'exposes' })
  }

  if (relatedPods.length > 0) {
    const readyCount = relatedPods.filter(podReady).length
    nodes.push({
      id: 'pods',
      kind: 'Pods',
      title: `${readyCount}/${relatedPods.length} pods ready`,
      subtitle: relatedPods.map(nameOf).filter(Boolean).slice(0, 2).join(', '),
      status: readyCount === relatedPods.length ? 'ready' : readyCount === 0 ? 'failed' : 'warning',
      statusText: readyCount === relatedPods.length ? 'Running' : 'Needs attention',
      icon: 'pod',
      meta: [
        ['Restart count', String(totalRestarts(relatedPods))],
        ['Phase', [...new Set(relatedPods.map((pod) => pod.status?.phase || 'Unknown'))].join(', ')]
      ],
      attachments: volumeClaims.map((pvc) => ({ icon: 'volume', label: `${nameOf(pvc)} volume` }))
    })
    edges.push({ from: 'app', to: 'pods', label: 'runs' })
  }

  if (configRefs.length > 0) {
    nodes.push({
      id: 'config',
      kind: 'Config',
      title: `${configRefs.length} config reference${configRefs.length === 1 ? '' : 's'}`,
      subtitle: configRefs.map((item) => item.name).slice(0, 3).join(', '),
      status: 'ready',
      statusText: 'Referenced',
      icon: 'config',
      meta: configRefs.slice(0, 4).map((item) => [item.kind, item.detail])
    })
    edges.push({ from: 'config', to: 'app', label: 'injects' })
  }

  if (secretRefs.length > 0) {
    nodes.push({
      id: 'secrets',
      kind: 'Secrets',
      title: `${secretRefs.length} secret reference${secretRefs.length === 1 ? '' : 's'}`,
      subtitle: secretRefs.map((item) => item.name).slice(0, 3).join(', '),
      status: 'warning',
      statusText: 'Names only',
      icon: 'secret',
      meta: secretRefs.slice(0, 4).map((item) => [item.kind, item.detail])
    })
    edges.push({ from: 'secrets', to: 'app', label: 'injects' })
  }

  if (volumeClaims.length > 0) {
    nodes.push({
      id: 'storage',
      kind: 'Storage',
      title: `${volumeClaims.length} persistent volume${volumeClaims.length === 1 ? '' : 's'}`,
      subtitle: volumeClaims.map(nameOf).filter(Boolean).join(', '),
      status: volumeClaims.every((pvc) => pvc.status?.phase === 'Bound') ? 'ready' : 'warning',
      statusText: volumeClaims.every((pvc) => pvc.status?.phase === 'Bound') ? 'Bound' : 'Pending',
      icon: 'volume',
      meta: volumeClaims.slice(0, 4).map((pvc) => [nameOf(pvc), pvc.spec?.resources?.requests?.storage || pvc.status?.phase || 'volume'])
    })
    edges.push({ from: 'app', to: 'storage', label: 'mounts' })
  }

  return layoutGraph({ nodes, edges, events, namespace, appName })
}

function items(resourceList) {
  return Array.isArray(resourceList?.items) ? resourceList.items : []
}

function nameOf(resource) {
  return resource?.metadata?.name || ''
}

function includesAppLabel(resource, appName) {
  const labels = resource?.metadata?.labels || {}
  return Object.values(labels).some((value) => String(value).includes(appName))
}

function isOwnedBy(resource, ownerName) {
  return (resource?.metadata?.ownerReferences || []).some((owner) => owner.name === ownerName)
}

function labelsMatch(labels = {}, selector = {}) {
  const entries = Object.entries(selector)
  return entries.length > 0 && entries.every(([key, value]) => labels[key] === value)
}

function serviceTargetsPods(service, pods) {
  const selector = service?.spec?.selector || {}
  return Object.keys(selector).length > 0 && pods.some((pod) => labelsMatch(pod.metadata?.labels, selector))
}

function ingressTargetsServices(ingress, services) {
  const names = new Set(services.map(nameOf))
  const backends = []
  for (const rule of ingress?.spec?.rules || []) {
    for (const pathItem of rule.http?.paths || []) {
      if (pathItem.backend?.service?.name) backends.push(pathItem.backend.service.name)
    }
  }
  if (ingress?.spec?.defaultBackend?.service?.name) backends.push(ingress.spec.defaultBackend.service.name)
  return backends.some((name) => names.has(name))
}

function ingressHostsUrl(ingress, url) {
  const host = stripProtocol(url)
  if (!host) return false
  return (ingress?.spec?.rules || []).some((rule) => rule.host === host)
}

function firstIngressHost(ingress) {
  return ingress?.spec?.rules?.[0]?.host || ''
}

function stripProtocol(url = '') {
  return String(url).replace(/^https?:\/\//, '').replace(/\/$/, '')
}

function statusForDeployment(deployment) {
  if (!deployment) return 'warning'
  const desired = deployment.spec?.replicas ?? 1
  const ready = deployment.status?.readyReplicas || 0
  if (desired === 0) return 'sleeping'
  if (ready >= desired) return 'ready'
  if (ready === 0) return 'failed'
  return 'warning'
}

function statusTextForDeployment(deployment) {
  if (!deployment) return 'Deployment not found'
  const desired = deployment.spec?.replicas ?? 1
  const ready = deployment.status?.readyReplicas || 0
  if (desired === 0) return 'Sleeping'
  if (ready >= desired) return 'Running'
  if (ready === 0) return 'Unavailable'
  return `${ready}/${desired} ready`
}

function firstContainerImage(deployment) {
  return deployment?.spec?.template?.spec?.containers?.[0]?.image || ''
}

function podReady(pod) {
  return (pod.status?.conditions || []).some((condition) => condition.type === 'Ready' && condition.status === 'True')
}

function totalRestarts(pods) {
  return pods.reduce((total, pod) => total + (pod.status?.containerStatuses || []).reduce((sum, container) => sum + (container.restartCount || 0), 0), 0)
}

function collectVolumeClaims(deployment, pods, pvcs) {
  const names = new Set()
  for (const spec of [deployment?.spec?.template?.spec, ...pods.map((pod) => pod.spec)]) {
    for (const volume of spec?.volumes || []) {
      if (volume.persistentVolumeClaim?.claimName) names.add(volume.persistentVolumeClaim.claimName)
    }
  }
  return pvcs.filter((pvc) => names.has(nameOf(pvc)))
}

function collectConfigRefs(deployment, pods, configmaps) {
  const existing = new Map(configmaps.map((item) => [nameOf(item), item]))
  const refs = new Map()
  for (const container of allContainers(deployment, pods)) {
    for (const envFrom of container.envFrom || []) {
      if (envFrom.configMapRef?.name) addConfigRef(refs, existing, envFrom.configMapRef.name, 'ConfigMap', 'envFrom')
    }
    for (const env of container.env || []) {
      if (env.valueFrom?.configMapKeyRef?.name) addConfigRef(refs, existing, env.valueFrom.configMapKeyRef.name, 'ConfigMap', `key ${env.valueFrom.configMapKeyRef.key || env.name}`)
    }
  }
  for (const spec of [deployment?.spec?.template?.spec, ...pods.map((pod) => pod.spec)]) {
    for (const volume of spec?.volumes || []) {
      if (volume.configMap?.name) addConfigRef(refs, existing, volume.configMap.name, 'ConfigMap', 'mounted volume')
    }
  }
  return [...refs.values()]
}

function addConfigRef(refs, existing, name, kind, detail) {
  const config = existing.get(name)
  const keyCount = config?.dataKeyCount || 0
  refs.set(`${kind}:${name}:${detail}`, { name, kind, detail: keyCount ? `${detail}, ${keyCount} keys` : detail })
}

function collectSecretRefs(deployment, pods, secrets) {
  const existing = new Map(secrets.map((item) => [nameOf(item), item]))
  const refs = new Map()
  for (const container of allContainers(deployment, pods)) {
    for (const envFrom of container.envFrom || []) {
      if (envFrom.secretRef?.name) addSecretRef(refs, existing, envFrom.secretRef.name, 'Secret', 'envFrom')
    }
    for (const env of container.env || []) {
      if (env.valueFrom?.secretKeyRef?.name) addSecretRef(refs, existing, env.valueFrom.secretKeyRef.name, 'Secret', `key ${env.valueFrom.secretKeyRef.key || env.name}`)
    }
  }
  for (const spec of [deployment?.spec?.template?.spec, ...pods.map((pod) => pod.spec)]) {
    for (const volume of spec?.volumes || []) {
      if (volume.secret?.secretName) addSecretRef(refs, existing, volume.secret.secretName, 'Secret', 'mounted volume')
    }
    for (const secret of spec?.imagePullSecrets || []) {
      if (secret.name) addSecretRef(refs, existing, secret.name, 'ImagePullSecret', 'image pull')
    }
  }
  return [...refs.values()]
}

function addSecretRef(refs, existing, name, kind, detail) {
  const secret = existing.get(name)
  refs.set(`${kind}:${name}:${detail}`, { name, kind, detail: secret?.type ? `${detail}, ${secret.type}` : detail })
}

function allContainers(deployment, pods) {
  const containers = []
  containers.push(...(deployment?.spec?.template?.spec?.containers || []))
  for (const pod of pods) containers.push(...(pod.spec?.containers || []))
  return containers
}

function sanitizeEvents(events, appName) {
  return events
    .filter((event) => {
      const involved = event.involvedObject?.name || ''
      return involved.includes(appName) || String(event.message || '').includes(appName)
    })
    .sort((a, b) => String(b.lastTimestamp || b.eventTime || b.metadata?.creationTimestamp || '').localeCompare(String(a.lastTimestamp || a.eventTime || a.metadata?.creationTimestamp || '')))
    .slice(0, 8)
    .map((event) => ({
      type: event.type || 'Normal',
      reason: event.reason || 'Event',
      involved: event.involvedObject?.name || '',
      message: String(event.message || '').slice(0, 180),
      time: event.lastTimestamp || event.eventTime || event.metadata?.creationTimestamp || ''
    }))
}

function layoutGraph(graph) {
  const preferred = {
    ingress: [80, 80],
    app: [520, 120],
    service: [520, 390],
    pods: [980, 120],
    config: [80, 390],
    secrets: [80, 630],
    storage: [980, 390]
  }
  const fallback = [[520, 630], [980, 630], [1440, 120], [1440, 390]]
  let fallbackIndex = 0

  for (const node of graph.nodes) {
    const coords = preferred[node.id] || fallback[fallbackIndex++] || [80 + fallbackIndex * 440, 80]
    node.x = coords[0]
    node.y = coords[1]
    node.width = ['config', 'secrets'].includes(node.id) ? 330 : 390
    node.height = estimateNodeHeight(node)
  }

  graph.width = Math.max(1320, ...graph.nodes.map((node) => node.x + node.width + 100))
  graph.height = Math.max(820, ...graph.nodes.map((node) => node.y + node.height + 100))
  return graph
}

function estimateNodeHeight(node) {
  const attachments = node.attachments?.length || 0
  const meta = Math.min(node.meta?.length || 0, 4)
  return 132 + meta * 24 + attachments * 58
}

function buildCanvasModel({ graph, theme, lastDeploy }) {
  return {
    generatedAt: new Date().toISOString(),
    app: {
      name: lastDeploy.app_name,
      namespace: lastDeploy.namespace,
      url: lastDeploy.url || '',
      image: lastDeploy.image || '',
      status: graph.nodes.find((node) => node.id === 'app')?.status || 'warning',
      updatedAt: lastDeploy.last_updated_at || lastDeploy.deployed_at || ''
    },
    layout: {
      width: graph.width,
      height: graph.height
    },
    nodes: graph.nodes,
    edges: graph.edges,
    events: graph.events,
    theme
  }
}

function renderHtml({ canvasModel }) {
  const template = fs.readFileSync(TEMPLATE_PATH, 'utf8')
  const title = `${canvasModel.app.name} - Sealos Canvas`

  return template
    .replaceAll('__TITLE__', escapeHtml(title))
    .replace('__CANVAS_MODEL__', escapeScriptJson(canvasModel))
}

function escapeHtml(value = '') {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function escapeCss(value = '') {
  return String(value).replace(/[<>]/g, '')
}

function escapeScriptJson(data) {
  return JSON.stringify(data)
    .replaceAll('<', '\\u003c')
    .replaceAll('>', '\\u003e')
    .replaceAll('&', '\\u0026')
    .replaceAll('\u2028', '\\u2028')
    .replaceAll('\u2029', '\\u2029')
}

try {
  main()
} catch (error) {
  printJson({
    ok: false,
    reason: 'canvas_generation_failed',
    message: `Failed to generate Sealos canvas: ${error.message}`
  })
}
