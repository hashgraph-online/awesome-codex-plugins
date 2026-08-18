import fs from 'node:fs'
import path from 'node:path'

const IGNORED_DIRECTORIES = new Set([
  '.git', '.github', '.sealos', '.vscode', 'node_modules',
])
const IGNORED_METADATA_PATTERN = /^(?:\.DS_Store|\.gitattributes|\.gitignore|CNAME|LICENSE(?:\..*)?|README(?:\..*)?)$/i
const CONTAINER_CONTRACT_PATTERN = /^(?:Dockerfile(?:\..*)?|docker-compose\.ya?ml|compose\.ya?ml)$/i
const BUILD_OR_RUNTIME_MANIFEST_PATTERN = /^(?:package\.json|package-lock\.json|npm-shrinkwrap\.json|pnpm-lock\.ya?ml|yarn\.lock|bun\.lockb?|deno\.jsonc?|go\.mod|go\.sum|Cargo\.(?:toml|lock)|composer\.(?:json|lock)|Gemfile(?:\.lock)?|requirements\.txt|pyproject\.toml|Pipfile(?:\.lock)?|pom\.xml|build\.gradle(?:\.kts)?|Makefile|.*\.csproj)$/i
const BUILD_CONFIG_PATTERN = /^(?:(?:vite|webpack|rollup|parcel|astro|next|nuxt|svelte|angular|gatsby)\.config\..+|tsconfig(?:\..+)?\.json|postcss\.config\..+|tailwind\.config\..+)$/i
const BUILD_OR_RUNTIME_SOURCE_EXTENSIONS = new Set([
  '.c', '.cc', '.cpp', '.cs', '.go', '.java', '.jsx', '.kt', '.less', '.njk',
  '.php', '.pug', '.py', '.rb', '.rs', '.sass', '.scss', '.styl', '.svelte',
  '.swift', '.ts', '.tsx', '.vue',
])
const SENSITIVE_FILE_PATTERN = /^(?:\.env(?:\..+)?|.*\.(?:key|pem|p12|pfx)|id_(?:rsa|dsa|ecdsa|ed25519)|kubeconfig|credentials(?:\..*)?|secrets?(?:\..*)?)$/i
const SENSITIVE_CONTENT_PATTERN = /-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----/
const SERVER_JAVASCRIPT_PATTERN = /(?:\b(?:createServer|listen)\s*\(|(?:from\s+|require\s*\(\s*)['"](?:node:)?(?:http|https|express|fastify|koa)['"])/

function toPosix(relativePath) {
  return relativePath.split(path.sep).join('/')
}

function inspectSourceReadyStaticSite(rootDir) {
  const assets = []
  const evidence = []
  const ignoredFiles = []
  const containerSignals = []
  const runtimeSignals = []
  const blockers = []

  function visit(currentDir) {
    for (const entry of fs.readdirSync(currentDir, { withFileTypes: true })) {
      const absolutePath = path.join(currentDir, entry.name)
      const relativePath = toPosix(path.relative(rootDir, absolutePath))

      if (entry.isSymbolicLink()) {
        blockers.push(`${relativePath}: symbolic links are not copied into the public site`)
        continue
      }
      if (entry.isDirectory()) {
        if (!IGNORED_DIRECTORIES.has(entry.name)) visit(absolutePath)
        continue
      }
      if (!entry.isFile()) continue
      if (IGNORED_METADATA_PATTERN.test(entry.name)) {
        ignoredFiles.push(relativePath)
        continue
      }

      if ((entry.name.startsWith('.') && !IGNORED_METADATA_PATTERN.test(entry.name)) || SENSITIVE_FILE_PATTERN.test(entry.name)) {
        blockers.push(`${relativePath}: potentially sensitive file must not be published`)
        continue
      }
      if (CONTAINER_CONTRACT_PATTERN.test(entry.name)) {
        containerSignals.push(`${relativePath}: existing container deployment contract`)
        continue
      }
      if (BUILD_OR_RUNTIME_MANIFEST_PATTERN.test(entry.name) || BUILD_CONFIG_PATTERN.test(entry.name)) {
        runtimeSignals.push(`${relativePath}: application build or runtime contract`)
        continue
      }

      const extension = path.extname(entry.name).toLowerCase()
      if (BUILD_OR_RUNTIME_SOURCE_EXTENSIONS.has(extension)) {
        runtimeSignals.push(`${relativePath}: source file requires a build or application runtime decision`)
        continue
      }

      const buffer = fs.readFileSync(absolutePath)
      if (SENSITIVE_CONTENT_PATTERN.test(buffer.subarray(0, 8192).toString('utf8'))) {
        blockers.push(`${relativePath}: private-key content must not be published`)
        continue
      }
      if (['.js', '.mjs', '.cjs'].includes(extension) && SERVER_JAVASCRIPT_PATTERN.test(buffer.toString('utf8'))) {
        runtimeSignals.push(`${relativePath}: server-side JavaScript entry-point signal`)
        continue
      }

      assets.push({ absolutePath, relativePath, size: buffer.byteLength })
    }
  }

  visit(rootDir)
  assets.sort((left, right) => left.relativePath.localeCompare(right.relativePath))
  const entryFile = assets.find(({ relativePath }) => /^index\.html?$/i.test(relativePath)) || null
  const nestedAssetCount = assets.filter(({ relativePath }) => relativePath.includes('/')).length
  const totalBytes = assets.reduce((total, asset) => total + asset.size, 0)

  if (entryFile != null) evidence.push(`${entryFile.relativePath}: root document entry point`)
  if (assets.length > 0) evidence.push(`${assets.length} public files can be served without transformation`)
  if (nestedAssetCount > 0) evidence.push(`${nestedAssetCount} public files are preserved in nested directories`)
  if (ignoredFiles.length > 0) evidence.push(`${ignoredFiles.length} repository metadata files are intentionally excluded`)

  let classification = 'source_ready_static'
  let route = 'static_image_build'
  if (blockers.length > 0) {
    classification = 'unsafe_to_publish'
    route = 'stop_and_review'
  } else if (containerSignals.length > 0) {
    classification = 'container_ready'
    route = 'existing_image_or_container_build'
  } else if (runtimeSignals.length > 0) {
    classification = 'build_or_runtime_required'
    route = 'ordinary_analysis'
  } else if (entryFile == null) {
    classification = 'needs_review'
    route = 'ordinary_analysis'
    blockers.push('root index.html is missing')
  }

  return {
    version: '2.0',
    classification,
    route,
    eligible: classification === 'source_ready_static',
    entryFile: entryFile?.relativePath || null,
    assets,
    totalBytes,
    evidence,
    ignoredFiles,
    routeSignals: [...containerSignals, ...runtimeSignals],
    containerSignals,
    runtimeSignals,
    blockers,
  }
}

export { inspectSourceReadyStaticSite }
