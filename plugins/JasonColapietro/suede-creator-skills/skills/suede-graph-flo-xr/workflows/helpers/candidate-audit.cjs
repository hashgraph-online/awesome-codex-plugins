// Auto-extracted from suede-graph-flo-xr.js inline node -e scripts. The splice keeps the
// original -e argv convention: process.argv[1] is the first user argument.
// Besides the no-follow path audit, reports which candidates are tracked in the checkout
// at argv[2] — a clean worktree of the scout's base commit, so ls-files here is ls-files
// at the base SHA. The orchestrator bans non-dot artifact segment names (build, dist,
// coverage, target, tmp) only for paths absent from that tracked set, which is what
// separates a tracked route like src/app/build/page.tsx from a generated artifact.
process.argv.splice(1,1);
const {execFileSync}=require("node:child_process");
const fs=require("node:fs"),path=require("node:path");const repo=fs.realpathSync(process.argv[1]),root=fs.realpathSync(process.argv[2]),candidates=JSON.parse(Buffer.from(process.argv[3],"base64").toString("utf8")),inside=value=>value===root||value.startsWith(root+path.sep),unsafe=[],auditable=new Map();for(const raw of candidates){if(typeof raw!=="string"||!raw.trim()||raw.includes("\0")){unsafe.push(String(raw));continue}const full=path.resolve(root,raw);if(!inside(full)){unsafe.push(raw);continue}try{if(fs.existsSync(full)){const stat=fs.lstatSync(full);if(stat.isSymbolicLink()||stat.isDirectory()||!inside(fs.realpathSync(full))){unsafe.push(raw);continue}}else{let parent=path.dirname(full);while(!fs.existsSync(parent)&&parent!==path.dirname(parent))parent=path.dirname(parent);if(!inside(fs.realpathSync(parent))){unsafe.push(raw);continue}}}catch{unsafe.push(raw);continue}if(!auditable.has(raw))auditable.set(raw,path.relative(root,full))}
const rels=[...new Set([...auditable.values()])].filter(Boolean);let tracked=new Set();
if(rels.length){let stdout;try{stdout=execFileSync("git",["-C",root,"ls-files","-z","--",...rels.map(rel=>":(literal)"+rel)],{encoding:"utf8",maxBuffer:8*1024*1024})}catch(error){process.stderr.write(error.stderr||String(error||"git ls-files failed"));process.exit(Number.isInteger(error.status)?error.status:1)}tracked=new Set(stdout.split("\0").filter(Boolean))}
const trackedCandidateFiles=candidates.filter(raw=>auditable.has(raw)&&tracked.has(auditable.get(raw)));
process.stdout.write(JSON.stringify({repoRoot:repo,worktreePath:root,unsafeCandidateFiles:unsafe,trackedCandidateFiles}))
