#!/usr/bin/env node
// Scan book project and write status.json + update projects registry.
// Usage: node scan-project.js [project-dir] [--ui]
import { existsSync, mkdirSync, readFileSync, writeFileSync, readdirSync, statSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, basename } from 'node:path';
import { execSync } from 'node:child_process';

const HOME = homedir();
const VELITH = join(HOME, '.velith');
const IMG_EXTS = /\.(jpg|jpeg|png|webp|gif)$/i;

const args = process.argv.slice(2);
const ui = args.includes('--ui');
const pluginRoot = (args.find(a => a.startsWith('--plugin-root=')) || '').slice('--plugin-root='.length) || null;
const dir = args.find(a => !a.startsWith('--')) || process.cwd();

// --- helpers ---
const read = (p, fb) => { try { return JSON.parse(readFileSync(p, 'utf8')); } catch { return fb; } };
const has = (f) => existsSync(join(dir, f));
const lines = (p) => { try { return parseInt(execSync(`wc -l < "${p}"`, { encoding: 'utf8' }).trim()); } catch { return 0; } };
const words = (p) => { try { return parseInt(execSync(`wc -w < "${p}"`, { encoding: 'utf8' }).trim()); } catch { return 0; } };

// --- scan ---
const prd = has('PRD.md') ? readFileSync(join(dir, 'PRD.md'), 'utf8') : '';
// Extract from YAML frontmatter first, then fall back to body
const yamlTitle = (prd.match(/^---\n[\s\S]*?^title:\s*["']?(.+?)["']?\s*$/m) || [])[1]?.trim();
const yamlGenre = (prd.match(/^---\n[\s\S]*?^genre:\s*(.+)$/m) || [])[1]?.trim();
const yamlLang = (prd.match(/^---\n[\s\S]*?^language:\s*(.+)$/m) || [])[1]?.trim();
const meta = {
  title: yamlTitle || (prd.match(/\*\*Title\*?\*?:\s*(.+)/i) || prd.match(/\*\*제목:\*\*\s*(.+)/) || prd.match(/^#\s*PRD[—:\-\s]+(.+)/im) || [,'Untitled'])[1]?.trim(),
  genre: (yamlGenre || (prd.match(/\*\*Genre\*?\*?:\s*(.+)/i) || prd.match(/\*\*장르:\*\*\s*(.+)/) || [,'unknown'])[1])?.trim().toLowerCase(),
  language: (yamlLang || (prd.match(/\*\*Language\*?\*?:\s*(.+)/i) || prd.match(/\*\*언어:\*\*\s*(.+)/) || [,'ko'])[1])?.trim(),
  target_words: (() => {
    // Try Korean 만/억 units first: "5~6만자", "10만 글자", "3억자"
    const manMatch = prd.match(/(?:분량|target|목표)[^\n]*?(\d+)\s*~?\s*(\d+)\s*만\s*(?:자|글자)/i);
    if (manMatch) return parseInt(manMatch[2]) * 10000;
    const eokMatch = prd.match(/(?:분량|target|목표)[^\n]*?(\d+)\s*~?\s*(\d+)\s*억\s*(?:자|글자)/i);
    if (eokMatch) return parseInt(eokMatch[2]) * 100000000;
    // Standard: "80,000 words", "5만자" standalone
    const m = prd.match(/(?:분량|target|목표)[^\n]*?(\d[\d,]+)\s*(?:words|자|글자)/i) || prd.match(/(\d[\d,]+)\s*(?:words|자|글자)/i);
    return parseInt((m || [,'0'])[1]?.replace(/,/g, '')) || 0;
  })(),
};
const CJK_LANGS = new Set(['ko', 'ja', 'zh', 'zh-cn', 'zh-tw', 'zh-hans', 'zh-hant']);
const isCJK = CJK_LANGS.has((meta.language || '').toLowerCase());
const chars = (p) => { try { return parseInt(execSync(`tr -d '[:space:]' < "${p}" | wc -m`, { encoding: 'utf8' }).trim()); } catch { return 0; } };
const countFn = isCJK ? chars : words;
const countUnit = isCJK ? 'chars' : 'words';
const draftsDir = (prd.match(/drafts_dir:\s*(\S+)/i) || prd.match(/\*\*초안\s*경로:\*\*\s*(\S+)/) || [,'drafts'])[1];
const planned = parseInt((prd.match(/(\d+)\s*(?:chapters|장|챕터)/i) || [,'0'])[1]);

// draft scan — fall back to drafts/ if specified path doesn't exist
let draftsPath = join(dir, draftsDir);
if (!existsSync(draftsPath) && draftsDir !== 'drafts') draftsPath = join(dir, 'drafts');
const drafts = existsSync(draftsPath) ? readdirSync(draftsPath).filter(f => f.endsWith('.md')).sort() : [];
const editsPath = join(dir, 'edits');
const editReports = [
  { stage: 'assessment', file: '01-assessment.md' },
  { stage: 'developmental', file: '02-developmental.md' },
  { stage: 'line-edit', file: '03-line-edit.md' },
  { stage: 'copy-edit', file: '04-copy-edit.md' },
  { stage: 'proofread', file: '05-proofread.md' },
];
const edits = existsSync(editsPath) ? readdirSync(editsPath).filter(f => f.endsWith('.md')) : [];
const hasEdits = edits.length > 0;
const editStage = (() => {
  if (!hasEdits) return null;
  let last = null;
  for (const r of editReports) { if (edits.includes(r.file)) last = r.stage; else break; }
  return last;
})();

// Per-chapter edit detection: compare draft mtime vs first edit report mtime
const editStartTime = hasEdits
  ? (() => { const r = editReports.find(r => edits.includes(r.file)); return r ? statSync(join(editsPath, r.file)).mtimeMs : null; })()
  : null;
const editingComplete = hasEdits && edits.includes('editorial-report.md');

function chapterStatus(fp) {
  if (editingComplete) return 'edit';
  if (!editStartTime) return 'draft';
  try { return statSync(fp).mtimeMs > editStartTime ? 'edit' : 'draft'; } catch { return 'draft'; }
}

const chapter_details = drafts.map(f => {
  const fp = join(draftsPath, f);
  return { filename: f, title: basename(f, '.md').replace(/^ch\d+[-_]?/i, '').replace(/[-_]/g, ' '), lines: lines(fp), words: countFn(fp), status: chapterStatus(fp), edit_stage: editStage };
});

// 'wait' entries for planned chapters not yet drafted (parse outline.md)
const outlineText = has('outline.md') ? readFileSync(join(dir, 'outline.md'), 'utf8') : '';
const plannedChapters = [...outlineText.matchAll(/^###\s+Chapter\s+(\d+):\s*(.+)$/gm)].map(m => ({ num: parseInt(m[1]), title: m[2].trim() }));
const draftedNums = new Set(drafts.map(f => { const m = f.match(/^ch(\d+)/i); return m ? parseInt(m[1]) : null; }).filter(Boolean));
for (const pc of plannedChapters) {
  if (!draftedNums.has(pc.num)) {
    chapter_details.push({ filename: `ch${String(pc.num).padStart(2, '0')}-${pc.title.replace(/\s+/g, '-')}.md`, title: pc.title, lines: 0, words: 0, status: 'wait', edit_stage: null });
  }
}
chapter_details.sort((a, b) => a.filename.localeCompare(b.filename, undefined, { numeric: true }));
const effectivePlanned = planned || plannedChapters.length || 0;
const total_words = chapter_details.reduce((s, c) => s + c.words, 0);

// cover scan
let cover_path = null;
const coverDir = join(dir, 'publish', 'cover');
if (existsSync(coverDir)) {
  const imgs = readdirSync(coverDir).filter(f => IMG_EXTS.test(f));
  if (imgs.length) cover_path = imgs.find(f => /^cover\./i.test(f)) || imgs[0];
}

// publish files
const formats = ['epub', 'pdf', 'mobi', 'txt', 'md'];
const output_files = formats.map(fmt => {
  const p = join(dir, 'publish', `book.${fmt}`);
  return { name: `book.${fmt}`, exists: existsSync(p), size_bytes: existsSync(p) ? statSync(p).size : 0 };
});

// agent defaults + artifact-based status inference
const agentDefs = [
  { id: 'book-architect', name: 'Book Architect', icon: 'architecture', role: 'Structural design & outline planning', artifacts: ['PRD.md', 'STYLE.md', 'outline.md'] },
  { id: 'chapter-writer', name: 'Chapter Writer', icon: 'edit_note', role: 'Draft generation', artifacts: [] },
  { id: 'continuity-editor', name: 'Continuity Editor', icon: 'compare_arrows', role: 'Cross-chapter consistency', artifacts: [] },
  { id: 'cover-designer', name: 'Cover Designer', icon: 'palette', role: 'Cover design & brand identity', artifacts: ['publish/cover'] },
  { id: 'marketing-expert', name: 'Marketing Expert', icon: 'campaign', role: 'Marketing copy & launch', artifacts: [] },
  { id: 'scene-generator', name: 'Scene Generator', icon: 'theaters', role: 'Scene creation & expansion', artifacts: [] },
  { id: 'style-doctor', name: 'Style Doctor', icon: 'medical_services', role: 'Style consistency & AI-slop detection', artifacts: [] },
];
const projectAgentsDir = join(dir, '.velith', 'agents');
const globalAgentsDir = join(VELITH, 'agents');
const agents = agentDefs.map(a => {
  const projectFile = join(projectAgentsDir, `${a.id}.json`);
  const globalFile = join(globalAgentsDir, `${a.id}.json`);
  const sf = existsSync(projectFile) ? projectFile : existsSync(globalFile) ? globalFile : null;
  const s = sf ? read(sf, {}) : {};
  let status = s.status || null;
  if (!status) {
    if (a.artifacts.length > 0 && a.artifacts.every(f => existsSync(join(dir, f)))) status = 'complete';
    else if (a.id === 'chapter-writer' && drafts.length > 0) status = drafts.length < (effectivePlanned || Infinity) ? 'running' : 'complete';
    else if (a.id === 'style-doctor' && editStage === 'proofread') status = 'complete';
    else if (a.id === 'continuity-editor' && editStage === 'developmental') status = 'complete';
    else status = 'idle';
  }
  return { id: a.id, name: a.name, icon: a.icon, role: a.role, status, last_run: s.last_run || null, task: s.task || null };
});

// phases
const phase = (n, name, pct, st) => ({ phase: n, name, percent: pct, status: st });
const phases = [
  phase(0, 'Onboarding', has('PRD.md') && has('STYLE.md') ? 100 : has('PRD.md') ? 50 : 0, has('PRD.md') && has('STYLE.md') ? 'complete' : has('PRD.md') ? 'in_progress' : 'pending'),
  phase(1, 'Ideation', has('ideation.md') || has('outline.md') ? 100 : 0, has('ideation.md') || has('outline.md') ? 'complete' : 'pending'),
  phase(2, 'Outlining', has('outline.md') ? 100 : 0, has('outline.md') ? 'complete' : 'pending'),
  phase(3, 'Drafting', effectivePlanned > 0 ? Math.min(Math.round(drafts.length / effectivePlanned * 100), 100) : drafts.length > 0 ? 100 : 0, effectivePlanned > 0 ? (drafts.length > 0 && drafts.length < effectivePlanned ? 'in_progress' : drafts.length >= effectivePlanned ? 'complete' : 'pending') : (drafts.length > 0 ? 'complete' : 'pending')),
  phase(4, 'Editing', has('edits/editorial-report.md') ? 100 : edits.length > 0 ? 50 : 0, has('edits/editorial-report.md') ? 'complete' : edits.length > 0 ? 'in_progress' : 'pending'),
  phase(5, 'Publishing', (() => { const c = [output_files.find(f => f.name === 'book.epub')?.exists, output_files.find(f => f.name === 'book.pdf')?.exists, has('publish/metadata.yaml'), has('publish/title-candidates.md'), has('publish/marketing-plan.md'), cover_path != null]; return Math.round(c.filter(Boolean).length / c.length * 100); })(), (() => { const ep = output_files.find(f => f.name === 'book.epub')?.exists, pd = output_files.find(f => f.name === 'book.pdf')?.exists; return (ep && pd && has('publish/metadata.yaml')) ? 'complete' : (ep || pd) ? 'in_progress' : 'pending'; })()),
];
const current_phase = (() => { const ip = phases.find(p => p.status === 'in_progress'); if (ip) return ip.phase; const last = [...phases].reverse().find(p => p.status === 'complete'); return last ? Math.min(last.phase + 1, phases[phases.length - 1].phase) : 0; })();

// --- build JSON ---
const now = new Date().toISOString();
const totalChapters = effectivePlanned || drafts.length;
const completedChapters = Math.min(drafts.length, totalChapters);
const project = {
  name: meta.title, path: dir, genre: meta.genre, language: meta.language,
  current_phase, phase_status: phases,
  total_chapters: totalChapters, completed_chapters: completedChapters,
  total_words, target_words: meta.target_words || 0, count_unit: countUnit,
  chapter_details, output_files, cover_path,
  last_updated: now,
};
const statusJson = { generated_at: now, agents, projects: [project] };

// --- write ---
mkdirSync(join(dir, '.velith'), { recursive: true });
mkdirSync(join(dir, '.velith', 'agents'), { recursive: true });
writeFileSync(join(dir, '.velith', 'status.json'), JSON.stringify(statusJson, null, 2));

// update registry
const regPath = join(VELITH, 'projects.json');
const reg = read(regPath, { projects: [] });
const idx = reg.projects.findIndex(p => p.path === dir);
const entry = { path: dir, name: meta.title, updated: now };
if (idx >= 0) reg.projects[idx] = entry; else reg.projects.push(entry);
writeFileSync(regPath, JSON.stringify(reg, null, 2));

console.log(`status.json written → ${join(dir, '.velith', 'status.json')}`);

// --- terminal dashboard ---
const bar = (pct) => { const f = Math.round(pct / 100 * 12); return '█'.repeat(f) + '░'.repeat(12 - f); };
const statusLabel = (s) => s === 'complete' ? 'COMPLETE' : s === 'in_progress' ? 'IN PROGRESS' : 'PENDING';
const w = 59;
const line = (s) => `║  ${s.padEnd(w - 4)}║`;
const sep = () => `╠${'═'.repeat(w - 2)}╣`;

let out = `╔${'═'.repeat(w - 2)}╗\n`;
out += line(`${meta.title}`);
out += line(`${meta.genre} · ${meta.language} · ${planned || '?'} chapters`);
out += sep();
phases.forEach(p => out += line(`${p.phase}. ${p.name.padEnd(13)} ${bar(p.percent)} ${String(p.percent).padStart(3)}%  ${statusLabel(p.status)}`));
out += sep();
chapter_details.forEach(c => out += line(`${c.filename.padEnd(20)} ${String(c.lines).padStart(5)} lines  ${String(c.words).padStart(5)} ${countUnit}  [${c.status}]`));
if (chapter_details.length) out += line(`Total: ${total_words} ${countUnit} · Target: ${meta.target_words || '?'}`);
out += sep();
output_files.forEach(f => out += line(`${f.name.padEnd(12)} ${f.exists ? '✓ exists' : '✗ missing'}${f.size_bytes ? ` (${(f.size_bytes / 1024).toFixed(0)}KB)` : ''}`));
out += `╚${'═'.repeat(w - 2)}╝\n`;
console.log(out);

// --- --ui flag ---
if (ui) {
  const config = read(join(VELITH, 'config.json'), {});
  const port = config.port || 9631;
  try { execSync(`curl -sf http://127.0.0.1:${port}/status.json`, { stdio: 'pipe' }); }
  catch {
    const serverPath = pluginRoot ? join(pluginRoot, 'dashboard', 'server.mjs') : join(dir, '..', '..', 'dashboard', 'server.mjs');
    execSync(`nohup node "${serverPath}" > /dev/null 2>&1 &`, { stdio: 'ignore' });
  }
  const pidx = Math.max(0, reg.projects.findIndex(p => p.path === dir));
  execSync(`open http://127.0.0.1:${port}/${pidx}/overview`, { stdio: 'ignore' });
}
