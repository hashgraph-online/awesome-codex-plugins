#!/usr/bin/env node

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const IGNORED_DIRECTORIES = new Set([
  '.git',
  '.next',
  '.sealos',
  '.turbo',
  'build',
  'coverage',
  'dist',
  'docs',
  'examples',
  'fixtures',
  'node_modules',
  'out',
  'target',
  'test',
  'tests',
  'vendor',
])

const SERVER_DEPENDENCIES = new Map([
  ['next', 'Next.js'],
  ['nuxt', 'Nuxt'],
  ['express', 'Express'],
  ['fastify', 'Fastify'],
  ['hono', 'Hono'],
  ['@nestjs/core', 'NestJS'],
  ['koa', 'Koa'],
  ['@hapi/hapi', 'hapi'],
])

const STATIC_DEPENDENCIES = new Map([
  ['vite', 'Vite'],
  ['astro', 'Astro'],
  ['react-scripts', 'Create React App'],
  ['@angular/core', 'Angular'],
  ['svelte', 'Svelte'],
  ['vue', 'Vue'],
])

const WORKER_DEPENDENCIES = new Map([
  ['bullmq', 'BullMQ'],
  ['bull', 'Bull'],
  ['amqplib', 'AMQP'],
  ['kafkajs', 'KafkaJS'],
  ['agenda', 'Agenda'],
  ['bee-queue', 'Bee-Queue'],
])

const DESKTOP_DEPENDENCIES = new Map([
  ['electron', 'Electron'],
  ['electron-builder', 'electron-builder'],
  ['electron-forge', 'Electron Forge'],
  ['@electron-forge/cli', 'Electron Forge'],
  ['@tauri-apps/api', 'Tauri'],
  ['@tauri-apps/cli', 'Tauri'],
])

const MOBILE_DEPENDENCIES = new Map([
  ['react-native', 'React Native'],
  ['expo', 'Expo'],
  ['@capacitor/core', 'Capacitor'],
  ['cordova', 'Cordova'],
])

const SOURCE_EXTENSIONS = new Set([
  '.c', '.cc', '.cpp', '.cs', '.go', '.java', '.js', '.jsx', '.kt', '.mjs',
  '.php', '.py', '.rb', '.rs', '.swift', '.ts', '.tsx',
])

function normalizeRelativePath(value) {
  const normalized = String(value || '.').replaceAll('\\', '/').replace(/^\.\//, '').replace(/\/$/, '')
  return normalized || '.'
}

function joinRelativePath(base, child) {
  const normalizedBase = normalizeRelativePath(base)
  const normalizedChild = normalizeRelativePath(child)
  if (normalizedBase === '.') return normalizedChild
  if (normalizedChild === '.') return normalizedBase
  return `${normalizedBase}/${normalizedChild}`
}

function repositoryRelativeFile(targetDir, targetPath, filePath) {
  return joinRelativePath(targetPath, path.relative(targetDir, filePath))
}

function readText(filePath) {
  try {
    return fs.readFileSync(filePath, 'utf-8')
  } catch {
    return ''
  }
}

function readJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'))
  } catch {
    return null
  }
}

function readTomlSection(text, sectionName) {
  const lines = text.split(/\r?\n/)
  const expectedHeader = `[${sectionName}]`
  const sectionLines = []
  let collecting = false

  for (const line of lines) {
    const trimmed = line.trim()
    if (/^\[.+\]$/.test(trimmed)) {
      if (collecting) break
      collecting = trimmed === expectedHeader
      continue
    }
    if (collecting) sectionLines.push(line)
  }

  return sectionLines.join('\n')
}

function readTomlArray(sectionText, key) {
  const escapedKey = key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const match = sectionText.match(new RegExp(`^\\s*${escapedKey}\\s*=\\s*\\[([\\s\\S]*?)\\]`, 'm'))
  return match?.[1] || ''
}

function findFiles(rootDir, predicate, maxDepth = 4, depth = 0) {
  if (depth > maxDepth) return []
  const matches = []

  try {
    for (const entry of fs.readdirSync(rootDir, { withFileTypes: true })) {
      if (entry.isDirectory() && IGNORED_DIRECTORIES.has(entry.name)) continue
      const fullPath = path.join(rootDir, entry.name)
      if (entry.isFile() && predicate(entry.name, fullPath)) {
        matches.push(fullPath)
      } else if (entry.isDirectory() && depth < maxDepth) {
        matches.push(...findFiles(fullPath, predicate, maxDepth, depth + 1))
      }
    }
  } catch {
    // Ignore unreadable paths and let the caller return needs_review.
  }

  return matches
}

function sourceContains(rootDir, pattern, maxDepth = 4) {
  const sourceFiles = findFiles(
    rootDir,
    (name) => SOURCE_EXTENSIONS.has(path.extname(name).toLowerCase()),
    maxDepth,
  )
  return sourceFiles.some((filePath) => pattern.test(readText(filePath)))
}

function packageSourceContains(rootDir, pattern, maxDepth = 4, currentDir = rootDir, depth = 0) {
  if (depth > maxDepth) return false

  try {
    for (const entry of fs.readdirSync(currentDir, { withFileTypes: true })) {
      if (entry.isDirectory() && IGNORED_DIRECTORIES.has(entry.name)) continue
      const fullPath = path.join(currentDir, entry.name)

      if (entry.isFile() && SOURCE_EXTENSIONS.has(path.extname(entry.name).toLowerCase())) {
        if (pattern.test(readText(fullPath))) return true
      } else if (entry.isDirectory() && depth < maxDepth) {
        if (fs.existsSync(path.join(fullPath, 'package.json'))) continue
        if (packageSourceContains(rootDir, pattern, maxDepth, fullPath, depth + 1)) return true
      }
    }
  } catch {
    // Ignore unreadable paths and let the caller rely on the remaining evidence.
  }

  return false
}

function dependencyMatches(dependencies, catalog) {
  const matches = []
  for (const [dependency, label] of catalog.entries()) {
    if (Object.prototype.hasOwnProperty.call(dependencies, dependency)) {
      matches.push({ dependency, label })
    }
  }
  return matches
}

function scriptMatches(scripts, pattern) {
  return Object.entries(scripts).some(([name, command]) =>
    pattern.test(name) || pattern.test(String(command)),
  )
}

function collectPackageRecords(targetDir, targetPath, { includeNested = true } = {}) {
  const packageFiles = new Set([
    ...(fs.existsSync(path.join(targetDir, 'package.json')) ? [path.join(targetDir, 'package.json')] : []),
    ...(includeNested ? findFiles(targetDir, (name) => name === 'package.json', 4) : []),
  ])

  return [...packageFiles].flatMap((packageFile) => {
    const manifest = readJson(packageFile)
    if (manifest == null || typeof manifest !== 'object' || Array.isArray(manifest)) return []

    const packageDir = path.dirname(packageFile)
    const localPath = normalizeRelativePath(path.relative(targetDir, packageDir))
    const displayPath = joinRelativePath(targetPath, localPath)
    const dependencies = {
      ...(manifest.dependencies || {}),
      ...(manifest.devDependencies || {}),
      ...(manifest.optionalDependencies || {}),
    }

    return [{
      packageDir,
      packageFile,
      localPath,
      displayPath,
      manifest,
      dependencies,
      scripts: manifest.scripts || {},
    }]
  })
}

function collectNodeSignals(packageRecords) {
  const deployableCandidates = []
  const desktopUnits = []
  const mobileUnits = []
  const cliUnits = []
  const libraryUnits = []

  for (const record of packageRecords) {
    const serverMatches = dependencyMatches(record.dependencies, SERVER_DEPENDENCIES)
    const staticMatches = dependencyMatches(record.dependencies, STATIC_DEPENDENCIES)
    const workerMatches = dependencyMatches(record.dependencies, WORKER_DEPENDENCIES)
    const desktopMatches = dependencyMatches(record.dependencies, DESKTOP_DEPENDENCIES)
    const mobileMatches = dependencyMatches(record.dependencies, MOBILE_DEPENDENCIES)
    const hasDesktopScript = scriptMatches(
      record.scripts,
      /(?:^|:)(?:electron|desktop|tauri)(?:$|:)|\b(?:electron(?:-builder|-forge)?|tauri)\b/i,
    )
    const hasDesktopSource = desktopMatches.length > 0 && packageSourceContains(
      record.packageDir,
      /\b(?:BrowserWindow|ipcMain|ipcRenderer)\b|(?:from\s*['"]electron['"]|require\s*\(\s*['"]electron['"]\s*\)|['"]@tauri-apps\/api(?:\/[^'"]*)?['"])/i,
    )
    const hasMobileScript = scriptMatches(
      record.scripts,
      /\b(?:react-native|expo|capacitor|cordova)\b|(?:^|:)(?:android|ios|mobile)(?:$|:)/i,
    )
    const hasMobileSource = mobileMatches.length > 0 && packageSourceContains(
      record.packageDir,
      /\b(?:AppRegistry\.registerComponent|registerRootComponent)\b|(?:from\s*['"](?:react-native|expo|@capacitor\/core|cordova)(?:\/[^'"]*)?['"]|require\s*\(\s*['"](?:react-native|expo|@capacitor\/core|cordova)(?:\/[^'"]*)?['"]\s*\))/i,
    )
    const hasMobileLayout = fs.existsSync(path.join(record.packageDir, 'android')) ||
      fs.existsSync(path.join(record.packageDir, 'ios'))
    const hasWorkerScript = scriptMatches(record.scripts, /(?:^|:)(?:worker|consumer|queue|scheduler|cron)(?:$|:)/i)
    const hasBuildScript = typeof record.scripts.build === 'string' || scriptMatches(record.scripts, /(?:^|:)build(?:$|:)/i)
    const runtimeCommands = ['start', 'serve']
      .map((name) => record.scripts[name])
      .filter((command) => typeof command === 'string')
    const hasRuntimeScript = runtimeCommands.length > 0
    const hasNonClientRuntimeScript = runtimeCommands.some((command) =>
      !/\b(?:electron(?:-builder|-forge)?|tauri|desktop|react-native|expo|capacitor|cordova)\b/i.test(command),
    )
    const isDesktop = desktopMatches.length > 0 && (hasDesktopScript || hasDesktopSource)
    const isMobile = mobileMatches.length > 0 && (hasMobileScript || hasMobileSource || hasMobileLayout)

    if (isDesktop) {
      const labels = [...new Set(desktopMatches.map(({ label }) => label))]
      desktopUnits.push({
        path: record.displayPath,
        evidence: [
          ...(labels.length > 0 ? [`${record.displayPath}/package.json declares ${labels.join(', ')}`] : []),
          ...(hasDesktopScript ? [`${record.displayPath}/package.json defines a desktop packaging/runtime script`] : []),
          ...(hasDesktopSource ? [`${record.displayPath} source imports desktop runtime APIs`] : []),
        ],
      })
    }

    if (isMobile) {
      const labels = [...new Set(mobileMatches.map(({ label }) => label))]
      mobileUnits.push({
        path: record.displayPath,
        evidence: [
          `${record.displayPath}/package.json declares ${labels.join(', ')}`,
          ...(hasMobileScript ? [`${record.displayPath}/package.json defines a mobile build/runtime script`] : []),
          ...(hasMobileSource ? [`${record.displayPath} source imports mobile runtime APIs`] : []),
          ...(hasMobileLayout ? [`${record.displayPath} contains an Android or iOS project layout`] : []),
        ],
      })
    }

    if (serverMatches.length > 0 && hasNonClientRuntimeScript) {
      const labels = [...new Set(serverMatches.map(({ label }) => label))]
      deployableCandidates.push({
        path: record.displayPath,
        workload_type: 'web_service',
        evidence: [
          `${record.displayPath}/package.json declares ${labels.join(', ')}`,
          `${record.displayPath}/package.json defines a non-interactive start/serve script`,
        ],
      })
    } else if (workerMatches.length > 0 && (hasWorkerScript || hasNonClientRuntimeScript)) {
      const labels = [...new Set(workerMatches.map(({ label }) => label))]
      deployableCandidates.push({
        path: record.displayPath,
        workload_type: 'worker',
        evidence: [
          `${record.displayPath}/package.json declares ${labels.join(', ')}`,
          `${record.displayPath}/package.json defines a non-interactive worker/runtime script`,
        ],
      })
    } else if (!isDesktop && !isMobile && staticMatches.length > 0 && hasBuildScript) {
      const labels = [...new Set(staticMatches.map(({ label }) => label))]
      deployableCandidates.push({
        path: record.displayPath,
        workload_type: 'static_web',
        evidence: [
          `${record.displayPath}/package.json declares ${labels.join(', ')}`,
          `${record.displayPath}/package.json defines a production build script`,
        ],
      })
    }

    if (record.manifest.bin != null && serverMatches.length === 0 && workerMatches.length === 0) {
      cliUnits.push({
        path: record.displayPath,
        evidence: [`${record.displayPath}/package.json exposes a bin entry`],
      })
    }

    const looksLikeLibrary = record.manifest.private !== true &&
      (record.manifest.exports != null || record.manifest.types != null) &&
      !hasRuntimeScript && serverMatches.length === 0 && workerMatches.length === 0
    if (looksLikeLibrary) {
      libraryUnits.push({
        path: record.displayPath,
        evidence: [`${record.displayPath}/package.json exposes library exports without an application start command`],
      })
    }
  }

  return { deployableCandidates, desktopUnits, mobileUnits, cliUnits, libraryUnits }
}

function collectRepositorySignals(targetDir, targetPath) {
  const dockerFiles = findFiles(
    targetDir,
    (name) => /^(?:Dockerfile|dockerfile)(?:\.[\w.-]+)?$|^(?:docker-compose|compose)\.ya?ml$/.test(name),
    3,
  )
  const dockerText = dockerFiles.map(readText).join('\n')
  const hasRemoteDesktopContract = /\b(?:noVNC|Xvfb|Selkies|websockify|Kasm|VNC_SERVER|DISPLAY=:\d+)\b/i.test(dockerText)

  const tauriConfigs = findFiles(targetDir, (name) => /^(?:tauri\.conf\.json|Tauri\.toml)$/.test(name), 4)
  const desktopDependencyText = [
    readText(path.join(targetDir, 'requirements.txt')),
    readText(path.join(targetDir, 'pyproject.toml')),
    readText(path.join(targetDir, 'Pipfile')),
    readText(path.join(targetDir, 'Cargo.toml')),
    readText(path.join(targetDir, 'CMakeLists.txt')),
  ].join('\n')
  const qtGtkMetadata = /\b(?:PyQt[56]|PySide[26]|gtkmm|gtk\+?-?[234]?|find_package\s*\(\s*Qt[56])\b/i.test(desktopDependencyText)
  const flutterManifest = findFiles(targetDir, (name) => name === 'pubspec.yaml', 3)
    .find((filePath) => /^\s*flutter\s*:/m.test(readText(filePath)) || /sdk:\s*flutter/i.test(readText(filePath)))
  const mobileLayout = (fs.existsSync(path.join(targetDir, 'android')) && fs.existsSync(path.join(targetDir, 'ios'))) || flutterManifest != null
  const browserExtensionManifest = findFiles(targetDir, (name) => /^manifest\.json$/.test(name), 3)
    .find((filePath) => /"manifest_version"\s*:\s*[23]/.test(readText(filePath)))
  const hardwareFile = findFiles(
    targetDir,
    (name) => name === 'platformio.ini' || name.endsWith('.ino') || name === 'west.yml',
    3,
  )[0]
  const browserExtensionPath = browserExtensionManifest == null
    ? null
    : joinRelativePath(targetPath, path.dirname(path.relative(targetDir, browserExtensionManifest)))
  const hardwarePath = hardwareFile == null
    ? null
    : joinRelativePath(targetPath, path.dirname(path.relative(targetDir, hardwareFile)))

  const generalCandidates = []
  const serverEvidence = []
  const goServerFile = findFiles(targetDir, (name) => name.endsWith('.go'), 4)
    .find((filePath) => {
      const source = readText(filePath)
      return /^\s*package\s+main\b/m.test(source) && /\b(?:http\.ListenAndServe|ListenAndServeTLS)\s*\(/.test(source)
    })
  if (goServerFile != null) {
    serverEvidence.push(`${repositoryRelativeFile(targetDir, targetPath, goServerFile)} is a Go main package with an HTTP listener`)
  }

  const cargoText = readText(path.join(targetDir, 'Cargo.toml'))
  const rustEntrypoint = findFiles(targetDir, (name) => name === 'main.rs', 3)[0]
  if (/\b(?:actix-web|axum|rocket|warp|hyper)\b/.test(cargoText) &&
      (rustEntrypoint != null || /^\s*\[\[bin\]\]\s*$/m.test(cargoText))) {
    serverEvidence.push('Cargo.toml declares a Rust web framework and an executable target')
  }

  const pyprojectText = readText(path.join(targetDir, 'pyproject.toml'))
  const pythonDependencyText = [
    readText(path.join(targetDir, 'requirements.txt')),
    readText(path.join(targetDir, 'Pipfile')),
    readTomlArray(readTomlSection(pyprojectText, 'project'), 'dependencies'),
    readTomlSection(pyprojectText, 'tool.poetry.dependencies'),
  ].join('\n')
  const pythonFrameworkDependency = /\b(?:aiohttp|django|fastapi|flask|quart|sanic|starlette|tornado)\b/i.test(pythonDependencyText)
  const pythonEntrypointFiles = findFiles(
    targetDir,
    (name) => /^(?:app|asgi|main|manage|server|wsgi)\.py$/.test(name),
    3,
  )
  const pythonEntrypoint = pythonEntrypointFiles.find((filePath) =>
    /\b(?:FastAPI|Flask)\s*\(|\b(?:get_asgi_application|get_wsgi_application)\s*\(/.test(readText(filePath)),
  )
  const pythonRuntimeText = [
    dockerText,
    readText(path.join(targetDir, 'Procfile')),
  ].join('\n')
  const pythonServerCommand = /\b(?:daphne|gunicorn|hypercorn|uvicorn)\b|(?:^|\s)flask\s+run\b|manage\.py\s+runserver\b/im.test(pythonRuntimeText)
  if (pythonServerCommand || (pythonFrameworkDependency && pythonEntrypoint != null)) {
    if (pythonFrameworkDependency) {
      serverEvidence.push('Python dependency declarations include a web framework')
    }
    if (pythonEntrypoint != null) {
      serverEvidence.push(`${repositoryRelativeFile(targetDir, targetPath, pythonEntrypoint)} defines a web application entry point`)
    }
    if (pythonServerCommand) {
      serverEvidence.push('Runtime artifacts define a Python web-server command')
    }
  }

  const javaDependencyText = [
    readText(path.join(targetDir, 'pom.xml')),
    readText(path.join(targetDir, 'build.gradle')),
    readText(path.join(targetDir, 'build.gradle.kts')),
  ].join('\n')
  if (/spring-boot/i.test(javaDependencyText) && sourceContains(targetDir, /@SpringBootApplication\b/, 8)) {
    serverEvidence.push('Java build metadata and source define a Spring Boot application')
  }

  if (serverEvidence.length > 0) {
    generalCandidates.push({
      path: normalizeRelativePath(targetPath),
      workload_type: 'web_service',
      evidence: serverEvidence,
    })
  }

  const workerEvidence = []
  const workerDependencyText = `${pythonDependencyText}\n${readText(path.join(targetDir, 'Gemfile'))}`
  const workerRuntimeText = `${pythonRuntimeText}\n${readText(path.join(targetDir, 'Procfile.dev'))}`
  if (/\b(?:celery|dramatiq|rq|sidekiq|resque)\b/i.test(workerDependencyText) &&
      /\b(?:celery|dramatiq|rq\s+worker|sidekiq|resque)\b/i.test(workerRuntimeText)) {
    workerEvidence.push('Dependency and runtime metadata define a background worker command')
  }
  if (workerEvidence.length > 0) {
    generalCandidates.push({
      path: normalizeRelativePath(targetPath),
      workload_type: 'worker',
      evidence: workerEvidence,
    })
  }

  const scheduledJobFile = findFiles(targetDir, (name) => /\.ya?ml$/.test(name), 4)
    .find((filePath) => {
      const contents = readText(filePath)
      return /^\s*kind\s*:\s*CronJob\s*$/m.test(contents) &&
        /^\s*(?:command|args)\s*:/m.test(contents)
    })
  if (scheduledJobFile != null) {
    generalCandidates.push({
      path: normalizeRelativePath(targetPath),
      workload_type: 'scheduled_job',
      evidence: [`${repositoryRelativeFile(targetDir, targetPath, scheduledJobFile)} defines a Kubernetes CronJob with an explicit command`],
    })
  }

  const explicitCliEvidence = []
  if (/\b(?:clap|structopt|argh)\b/.test(cargoText)) {
    explicitCliEvidence.push('Cargo.toml declares a CLI argument parser')
  }
  if (/\b(?:spf13\/cobra|urfave\/cli)\b/.test(readText(path.join(targetDir, 'go.mod')))) {
    explicitCliEvidence.push('go.mod declares a CLI framework')
  }
  if (/^\s*\[(?:project\.scripts|tool\.poetry\.scripts)\]\s*$/m.test(readText(path.join(targetDir, 'pyproject.toml')))) {
    explicitCliEvidence.push(`${joinRelativePath(targetPath, 'pyproject.toml')} defines console scripts`)
  }

  const libraryEvidence = []
  if (/Topic\s*::\s*Software Development\s*::\s*Libraries\b/i.test(pyprojectText)) {
    libraryEvidence.push(`${joinRelativePath(targetPath, 'pyproject.toml')} classifies the project as a software library`)
  }

  const desktopUnits = tauriConfigs.map((configPath) => {
    let unitDir = path.dirname(configPath)
    if (path.basename(unitDir) === 'src-tauri') unitDir = path.dirname(unitDir)
    return {
      path: joinRelativePath(targetPath, path.relative(targetDir, unitDir)),
      evidence: [`${repositoryRelativeFile(targetDir, targetPath, configPath)} is a Tauri configuration`],
    }
  })
  if (qtGtkMetadata) {
    desktopUnits.push({
      path: normalizeRelativePath(targetPath),
      evidence: ['Dependency/build metadata declares a Qt/GTK desktop toolkit'],
    })
  }

  return {
    browserExtensionManifest,
    browserExtensionPath,
    desktopUnits,
    explicitCliEvidence,
    generalCandidates,
    hardwareFile,
    hardwarePath,
    hasRemoteDesktopContract,
    libraryEvidence,
    mobileEvidence: [
      ...(mobileLayout ? ['Android/iOS or Flutter mobile project layout found'] : []),
    ],
  }
}

function deduplicateCandidates(candidates) {
  const seen = new Set()
  return candidates.filter((candidate) => {
    const key = `${candidate.path}\u0000${candidate.workload_type}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function isSameOrNestedPath(candidatePath, unitPath) {
  const candidate = normalizeRelativePath(candidatePath)
  const unit = normalizeRelativePath(unitPath)
  if (unit === '.') return candidate === '.'
  return candidate === unit || candidate.startsWith(`${unit}/`)
}

function isBundledClientCandidate(candidate, clientUnits) {
  return clientUnits.some(({ path: unitPath }) =>
    isSameOrNestedPath(candidate.path, unitPath) ||
    (normalizeRelativePath(unitPath) === '.' && candidate.workload_type === 'static_web'),
  )
}

function makeResult({ status, workloadType, targetPath, reasonCodes, evidence, candidates = [], source = 'deterministic' }) {
  return {
    version: '1.0',
    generated_at: new Date().toISOString(),
    status,
    workload_type: workloadType,
    target_path: normalizeRelativePath(targetPath),
    reason_codes: reasonCodes,
    evidence: [...new Set(evidence)].filter(Boolean),
    candidates: deduplicateCandidates(candidates),
    source,
  }
}

function classifyProject(targetDir) {
  const normalizedTargetPath = '.'
  const packageRecords = collectPackageRecords(targetDir, normalizedTargetPath)
  const nodeSignals = collectNodeSignals(packageRecords)
  const repoSignals = collectRepositorySignals(targetDir, normalizedTargetPath)
  const candidates = deduplicateCandidates([
    ...nodeSignals.deployableCandidates,
    ...repoSignals.generalCandidates,
  ])

  const desktopUnits = [...nodeSignals.desktopUnits, ...repoSignals.desktopUnits]

  const mobileUnits = [...nodeSignals.mobileUnits]
  if (repoSignals.mobileEvidence.length > 0) {
    mobileUnits.push({ path: normalizedTargetPath, evidence: repoSignals.mobileEvidence })
  }

  const libraryUnits = [...nodeSignals.libraryUnits]
  if (repoSignals.libraryEvidence.length > 0) {
    libraryUnits.push({ path: normalizedTargetPath, evidence: repoSignals.libraryEvidence })
  }

  const excludedUnitPaths = new Set([
    ...desktopUnits.map(({ path: unitPath }) => unitPath),
    ...mobileUnits.map(({ path: unitPath }) => unitPath),
    ...nodeSignals.cliUnits.map(({ path: unitPath }) => unitPath),
    ...libraryUnits.map(({ path: unitPath }) => unitPath),
  ])
  const independentCandidates = candidates.filter((candidate) =>
    (!excludedUnitPaths.has(candidate.path) || candidate.workload_type === 'scheduled_job') &&
    !isBundledClientCandidate(candidate, [...desktopUnits, ...mobileUnits]),
  )
  const clientUnits = [...desktopUnits, ...mobileUnits]
  const conflictingClientUnits = clientUnits.filter(({ path: unitPath }) =>
    candidates.some((candidate) => normalizeRelativePath(candidate.path) === normalizeRelativePath(unitPath)),
  )
  const conflictingClientCandidates = candidates.filter((candidate) =>
    conflictingClientUnits.some(({ path: unitPath }) =>
      normalizeRelativePath(candidate.path) === normalizeRelativePath(unitPath),
    ),
  )
  const hasOnlyScheduledJobCandidates = independentCandidates.length > 0 &&
    independentCandidates.every((candidate) => candidate.workload_type === 'scheduled_job')

  if (repoSignals.hardwareFile != null) {
    const cloudCandidates = independentCandidates.filter((candidate) =>
      !isSameOrNestedPath(candidate.path, repoSignals.hardwarePath) &&
      !(repoSignals.hardwarePath === '.' && candidate.workload_type === 'static_web'),
    )
    if (cloudCandidates.length > 0) {
      return makeResult({
        status: 'needs_review',
        workloadType: 'mixed',
        targetPath: normalizedTargetPath,
        reasonCodes: ['MIXED_REPOSITORY_REQUIRES_REVIEW'],
        evidence: [`${repositoryRelativeFile(targetDir, normalizedTargetPath, repoSignals.hardwareFile)} identifies a hardware-dependent unit`],
        candidates: cloudCandidates,
      })
    }

    return makeResult({
      status: 'ineligible',
      workloadType: 'hardware_dependent',
      targetPath: normalizedTargetPath,
      reasonCodes: ['HARDWARE_DEPENDENT'],
      evidence: [`${repositoryRelativeFile(targetDir, normalizedTargetPath, repoSignals.hardwareFile)} indicates firmware or embedded hardware`],
    })
  }

  if (clientUnits.length > 0 && independentCandidates.length > 0) {
    return makeResult({
      status: 'needs_review',
      workloadType: 'mixed',
      targetPath: normalizedTargetPath,
      reasonCodes: ['MIXED_REPOSITORY_REQUIRES_REVIEW'],
      evidence: clientUnits.flatMap(({ evidence }) => evidence),
      candidates: independentCandidates,
    })
  }

  if (conflictingClientCandidates.length > 0) {
    return makeResult({
      status: 'needs_review',
      workloadType: 'mixed',
      targetPath: normalizedTargetPath,
      reasonCodes: ['CONFLICTING_WORKLOAD_EVIDENCE'],
      evidence: [
        ...conflictingClientUnits.flatMap(({ evidence }) => evidence),
        ...conflictingClientCandidates.flatMap(({ evidence }) => evidence),
      ],
      candidates: conflictingClientCandidates,
    })
  }

  if (desktopUnits.length > 0) {
    if (repoSignals.hasRemoteDesktopContract) {
      return makeResult({
        status: 'needs_review',
        workloadType: 'remote_desktop',
        targetPath: normalizedTargetPath,
        reasonCodes: ['REMOTE_DESKTOP_REQUIRES_REVIEW'],
        evidence: [
          ...desktopUnits.flatMap(({ evidence }) => evidence),
          'Docker artifacts reference a browser/VNC headless runtime',
        ],
      })
    }

    return makeResult({
      status: 'ineligible',
      workloadType: 'desktop_gui',
      targetPath: normalizedTargetPath,
      reasonCodes: ['DESKTOP_GUI_ONLY'],
      evidence: desktopUnits.flatMap(({ evidence }) => evidence),
    })
  }

  if (mobileUnits.length > 0) {
    return makeResult({
      status: 'ineligible',
      workloadType: 'mobile_client',
      targetPath: normalizedTargetPath,
      reasonCodes: ['MOBILE_CLIENT_ONLY'],
      evidence: mobileUnits.flatMap(({ evidence }) => evidence),
    })
  }

  if (repoSignals.browserExtensionManifest != null) {
    const cloudCandidates = independentCandidates.filter((candidate) =>
      !isSameOrNestedPath(candidate.path, repoSignals.browserExtensionPath) &&
      !(repoSignals.browserExtensionPath === '.' && candidate.workload_type === 'static_web'),
    )
    if (cloudCandidates.length > 0) {
      return makeResult({
        status: 'needs_review',
        workloadType: 'mixed',
        targetPath: normalizedTargetPath,
        reasonCodes: ['MIXED_REPOSITORY_REQUIRES_REVIEW'],
        evidence: ['Browser extension manifest found alongside cloud-deployable units'],
        candidates: cloudCandidates,
      })
    }

    return makeResult({
      status: 'ineligible',
      workloadType: 'browser_extension',
      targetPath: normalizedTargetPath,
      reasonCodes: ['BROWSER_EXTENSION_ONLY'],
      evidence: [`${repositoryRelativeFile(targetDir, normalizedTargetPath, repoSignals.browserExtensionManifest)} is a browser extension manifest`],
    })
  }

  if (libraryUnits.length > 0 && independentCandidates.length > 0 && !hasOnlyScheduledJobCandidates) {
    return makeResult({
      status: 'needs_review',
      workloadType: 'mixed',
      targetPath: normalizedTargetPath,
      reasonCodes: ['MIXED_REPOSITORY_REQUIRES_REVIEW'],
      evidence: libraryUnits.flatMap(({ evidence }) => evidence),
      candidates: independentCandidates,
    })
  }

  if (libraryUnits.length > 0 && independentCandidates.length === 0) {
    return makeResult({
      status: 'ineligible',
      workloadType: 'library',
      targetPath: normalizedTargetPath,
      reasonCodes: ['LIBRARY_ONLY'],
      evidence: libraryUnits.flatMap(({ evidence }) => evidence),
    })
  }

  const unresolvedCliUnits = nodeSignals.cliUnits.filter(({ path: unitPath }) =>
    !independentCandidates.some((candidate) => candidate.path === unitPath),
  )
  const hasSelectedApplication = independentCandidates.some((candidate) => candidate.path === normalizedTargetPath)
  const cliEvidence = [
    ...unresolvedCliUnits.flatMap(({ evidence }) => evidence),
    ...(!hasSelectedApplication ? repoSignals.explicitCliEvidence : []),
  ]
  if (cliEvidence.length > 0 && independentCandidates.length > 0 && !hasOnlyScheduledJobCandidates) {
    return makeResult({
      status: 'needs_review',
      workloadType: 'mixed',
      targetPath: normalizedTargetPath,
      reasonCodes: ['MIXED_REPOSITORY_REQUIRES_REVIEW'],
      evidence: cliEvidence,
      candidates: independentCandidates,
    })
  }
  if (cliEvidence.length > 0 && independentCandidates.length === 0) {
    return makeResult({
      status: 'ineligible',
      workloadType: 'cli',
      targetPath: normalizedTargetPath,
      reasonCodes: ['CLI_ONLY'],
      evidence: cliEvidence,
    })
  }

  if (independentCandidates.length > 1) {
    return makeResult({
      status: 'needs_review',
      workloadType: 'mixed',
      targetPath: normalizedTargetPath,
      reasonCodes: ['MIXED_REPOSITORY_REQUIRES_REVIEW'],
      evidence: ['Multiple cloud-deployable units were detected'],
      candidates: independentCandidates,
    })
  }

  if (independentCandidates.length === 1) {
    const [candidate] = independentCandidates
    if (normalizeRelativePath(candidate.path) !== normalizedTargetPath) {
      return makeResult({
        status: 'needs_review',
        workloadType: 'mixed',
        targetPath: normalizedTargetPath,
        reasonCodes: ['NESTED_WORKLOAD_REQUIRES_REVIEW'],
        evidence: [`A supported workload was detected only at ${candidate.path}`],
        candidates: [candidate],
      })
    }

    const reasonCode = {
      static_web: 'STATIC_WEB_BUILD',
      web_service: 'SERVER_WORKLOAD',
      worker: 'BACKGROUND_WORKER',
    }[candidate.workload_type] || 'SUPPORTED_WORKLOAD'
    return makeResult({
      status: 'eligible',
      workloadType: candidate.workload_type,
      targetPath: normalizedTargetPath,
      reasonCodes: [reasonCode],
      evidence: candidate.evidence,
      candidates: [candidate],
    })
  }

  if (repoSignals.hasRemoteDesktopContract) {
    return makeResult({
      status: 'needs_review',
      workloadType: 'remote_desktop',
      targetPath: normalizedTargetPath,
      reasonCodes: ['REMOTE_DESKTOP_REQUIRES_REVIEW'],
      evidence: ['Docker artifacts reference a browser/VNC headless runtime'],
    })
  }

  return makeResult({
    status: 'needs_review',
    workloadType: 'unknown',
    targetPath: normalizedTargetPath,
    reasonCodes: ['INSUFFICIENT_EVIDENCE'],
    evidence: ['No supported headless runtime, static web build, worker, or scheduled job was identified deterministically'],
  })
}

function parseArgs(argv) {
  if (argv.length !== 1 || argv[0].startsWith('-')) {
    throw new Error('Usage: node workload-eligibility.mjs <repo-dir>')
  }
  return { repoDir: argv[0] }
}

function resolveRepository(repoDir) {
  const resolvedRepo = fs.realpathSync(path.resolve(repoDir))
  if (!fs.statSync(resolvedRepo).isDirectory()) {
    throw new Error(`Repository target is not a directory: ${resolvedRepo}`)
  }
  return resolvedRepo
}

function exitCodeForStatus(status) {
  if (status === 'eligible') return 0
  if (status === 'ineligible') return 2
  return 3
}

const isMain = process.argv[1] != null && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
if (isMain) {
  try {
    const args = parseArgs(process.argv.slice(2))
    const result = classifyProject(resolveRepository(args.repoDir))
    console.log(JSON.stringify(result, null, 2))
    process.exitCode = exitCodeForStatus(result.status)
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error))
    process.exitCode = 1
  }
}

export {
  classifyProject,
  exitCodeForStatus,
}
