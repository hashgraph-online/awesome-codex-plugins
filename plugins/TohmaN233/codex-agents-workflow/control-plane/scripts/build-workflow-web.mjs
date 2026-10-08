import { build } from 'esbuild';
import { readFile, writeFile, readdir } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const packageMetadata = JSON.parse(await readFile(join(root, 'package.json'), 'utf8'));
const targets = ['chrome120', 'firefox121', 'safari17'];
const common = {
  absWorkingDir: root,
  tsconfig: 'web-src/tsconfig.json',
  bundle: true,
  write: false,
  metafile: true,
  format: 'esm',
  minify: true,
  sourcemap: false,
  target: targets,
  legalComments: 'inline',
  define: {
    'process.env.NODE_ENV': '"production"',
    __CODEX_WORKFLOW_VERSION__: JSON.stringify(packageMetadata.version),
  },
};
const sharedBridgeSource = {
  name: 'shared-mcp-app-client',
  setup(buildApi) {
    buildApi.onResolve({ filter: /^\.\/app-client\.js$/ }, args => {
      if (!args.importer.replaceAll('\\', '/').endsWith('/web/app.js')) return null;
      return { path: join(root, 'web-src', 'mcp-app-client.ts') };
    });
  },
};

const [workflowBuild, appClientBuild] = await Promise.all([
  build({ ...common, plugins: [sharedBridgeSource], stdin: { contents: "import './web-src/main.tsx';", resolveDir: root, sourcefile: 'workflow-entry.tsx', loader: 'tsx' }, outfile: 'web/workflows.js' }),
  build({ ...common, entryPoints: ['web-src/mcp-app-client.ts'], outfile: 'web/app-client.js' }),
]);

function outputFor(result, suffix) {
  const output = result.outputFiles.find(file => file.path.replaceAll('\\', '/').endsWith(suffix));
  if (!output) throw new Error(`Browser build did not emit ${suffix}`);
  return output;
}

const workflowJs = outputFor(workflowBuild, '/web/workflows.js');
const workflowCss = outputFor(workflowBuild, '/web/workflows.css');
const appClientJs = outputFor(appClientBuild, '/web/app-client.js');
// Git checkout line endings vary by platform. Packaged resources must not.
const readTextSource = async name => (await readFile(join(root, 'web', name), 'utf8')).replace(/\r\n/g, '\n');
const settingsHtml = await readTextSource('index.html');
const settingsCss = await readTextSource('styles.css');
const workflowHtml = await readTextSource('workflows.html');
const settingsBody = /<body\b[^>]*>([\s\S]*?)<\/body>/i.exec(settingsHtml)?.[1];
if (!settingsBody) throw new Error('Settings HTML has no body element.');
if (!workflowHtml.includes('<div id="workflow-shell"><div id="root"></div></div><div id="settings-shell" hidden></div>')) {
  throw new Error('Workflow HTML does not define the MCP App view roots.');
}
const settingsMarkup = settingsBody.replace(/<script\b[^>]*src="\/app\.js"[^>]*><\/script>/i, '').trim();
if (!settingsMarkup.includes('id="workflow-workspace"') || !settingsMarkup.includes('id="toast"')) {
  throw new Error('Settings HTML is missing expected navigation or status elements.');
}

function inlineScript(source) {
  return Buffer.from(source).toString('utf8').replace(/<\/script/gi, '<\\/script');
}

function makeAppResource(view) {
  const appMarker = '<meta name="codex-agents-workflow-app" content="mcp">';
  const viewMarker = `<meta name="codex-agents-workflow-view" content="${view}">`;
  const inlineWorkflowCss = `<style id="workflow-styles">${Buffer.from(workflowCss.contents).toString('utf8')}</style>`;
  const templateMarkup = `<template id="settings-template">${settingsMarkup}</template><template id="settings-style-template"><style>${settingsCss}</style></template>`;
  const inlineWorkflowScript = `<script type="module">${inlineScript(workflowJs.contents)}</script>`;
  const resource = workflowHtml
    .replace('</head>', () => `${appMarker}${viewMarker}${inlineWorkflowCss}</head>`)
    .replace('<link rel="stylesheet" href="/workflows.css">', '')
    .replace('<script type="module" src="/workflows.js"></script>', () => `${templateMarkup}${inlineWorkflowScript}`);
  const embeddedCss = /<style id="workflow-styles">([\s\S]*?)<\/style>/i.exec(resource)?.[1];
  if (embeddedCss !== Buffer.from(workflowCss.contents).toString('utf8')) throw new Error('Embedded Workflow stylesheet changed during MCP resource assembly.');
  const embeddedScript = /<script type="module">([\s\S]*?)<\/script>/i.exec(resource)?.[1];
  if (embeddedScript !== inlineScript(workflowJs.contents)) throw new Error('Embedded Workflow script changed during MCP resource assembly.');
  return resource;
}

const packagePaths = [...new Set([...Object.keys(workflowBuild.metafile.inputs), ...Object.keys(appClientBuild.metafile.inputs)]
  .filter(path => path.startsWith('node_modules/'))
  .map(path => {
    const parts = path.split('/');
    return parts.slice(0, parts[1].startsWith('@') ? 3 : 2).join('/');
  }))].sort();
const licenses = [];
for (const path of packagePaths) {
  const metadata = JSON.parse(await readFile(join(root, path, 'package.json'), 'utf8'));
  const files = (await readdir(join(root, path))).filter(name => /^licen[sc]e(?:\..*)?$/i.test(name)).sort();
  if (!files.length) throw new Error('Bundled package has no license file: ' + metadata.name);
  licenses.push(metadata.name + '@' + metadata.version + '\n' + (await Promise.all(files.map(file => readFile(join(root, path, file), 'utf8')))).join('\n'));
}

const outputs = [
  ...workflowBuild.outputFiles,
  appClientJs,
  { path: join(root, 'web', 'workflows-app.html'), contents: Buffer.from(makeAppResource('workflows')) },
  { path: join(root, 'web', 'settings-app.html'), contents: Buffer.from(makeAppResource('settings')) },
  { path: join(root, 'web', 'workflows.LICENSE.txt'), contents: Buffer.from(licenses.join('\n\n--------------------\n\n').replace(/\r\n/g, '\n') + '\n') },
];

for (const output of outputs) {
  if (process.argv.includes('--check')) {
    let existing;
    try { existing = await readFile(output.path); }
    catch (cause) { throw new Error(`Committed browser asset is missing: ${output.path}`, { cause }); }
    if (!existing.equals(Buffer.from(output.contents))) throw new Error('Committed web asset differs from source: ' + output.path);
  } else await writeFile(output.path, output.contents);
}

console.log(process.argv.includes('--check') ? 'Workflow and MCP App web assets match source' : 'Workflow and MCP App web assets built');
