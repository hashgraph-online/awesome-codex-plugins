// Auto-extracted from suede-graph-flo-xr.js inline node -e scripts. The splice keeps the
// original -e argv convention: process.argv[1] is the first user argument.
process.argv.splice(1,1);
const {execFileSync}=require("node:child_process");const {randomUUID}=require("node:crypto");const {mkdirSync,realpathSync}=require("node:fs");const {dirname,basename}=require("node:path"),parseStatus=value => {
  const fields = String(value || '').split(String.fromCharCode(0))
  const paths = []
  const records = []
  let malformed = false
  for (let index = 0; index < fields.length; index += 1) {
    const record = fields[index]
    if (!record) continue
    if (record.length < 4 || record[2] !== ' ') {
      malformed = true
      continue
    }
    const status = record.slice(0, 2)
    const current = record.slice(3)
    if (!current) {
      malformed = true
      continue
    }
    paths.push(current)
    records.push({ status, path: current })
    if (/[RC]/.test(status)) {
      const original = fields[index + 1]
      index += 1
      if (!original) {
        malformed = true
        continue
      }
      paths.push(original)
      records.push({ status: 'from', path: original })
    }
  }
  return { paths: [...new Set(paths)], records, malformed }
};const root=process.argv[1],prefix=process.argv[2],target=prefix+randomUUID(),tempRoot="/private/tmp/"+basename(target),canonical=value=>{try{return realpathSync(value)}catch{return value}},within=(cwd,worktreePath)=>cwd===worktreePath||cwd.startsWith(worktreePath+"/"),allLines=value=>value.split("\n").filter(Boolean),nulPaths=value=>value.split("\0").filter(Boolean);const run=(file,args,allowed=[0])=>{try{return execFileSync(file,args,{encoding:"utf8",maxBuffer:8*1024*1024})}catch(error){const status=Number.isInteger(error.status)?error.status:null;if(status!==null&&allowed.includes(status))return error.stdout||"";process.stderr.write(error.stderr||String(error||file+" failed"));process.exit(status||1)}};run("/usr/bin/sandbox-exec",["-p","(version 1)(allow default)(deny network*)","/usr/bin/true"]);mkdirSync(tempRoot,{mode:0o700});run("git",["-C",root,"fetch","origin"]);const origin=run("git",["-C",root,"rev-parse","origin/main"]).trim();mkdirSync(dirname(target),{recursive:true});run("git",["-C",root,"worktree","add",target,"origin/main"]);const targetHead=run("git",["-C",target,"rev-parse","HEAD"]).trim(),targetStatus=parseStatus(run("git",["-C",target,"status","--porcelain=v1","-z"]));if(targetHead!==origin||targetStatus.paths.length||targetStatus.malformed){process.stderr.write("target worktree is not a clean origin/main checkout");process.exit(1)}const worktreeList=run("git",["-C",root,"worktree","list","--porcelain"]),liveRaw=run("lsof",["-nP","-a","-d","cwd","-Fn"],[0,1]),liveCwdPaths=[...new Set(liveRaw.split("\n").filter(line=>line.startsWith("n")).map(line=>canonical(line.slice(1))))],rootReal=canonical(root),targetReal=canonical(target),paths=worktreeList.split(/\n\n+/).map(block=>block.split("\n").find(line=>line.startsWith("worktree "))?.slice(9)).filter(Boolean).map(canonical),siblingPaths=paths.filter(worktreePath=>worktreePath!==targetReal&&worktreePath!==rootReal),siblingOverflow=siblingPaths.length>20,siblings=siblingPaths.slice(0,20).map(worktreePath=>{const status=parseStatus(run("git",["-C",worktreePath,"status","--porcelain=v1","-z"])),dirtyFiles=status.paths,committed=nulPaths(run("git",["-C",worktreePath,"diff","--name-only","-z","origin/main...HEAD"])),files=[...new Set([...committed,...dirtyFiles])],cherry=allLines(run("git",["-C",worktreePath,"cherry","origin/main"])),manifestOverflow=status.malformed||dirtyFiles.length>200||committed.length>200||files.length>200||cherry.length>200;return {worktree:worktreePath,branch:run("git",["-C",worktreePath,"rev-parse","--abbrev-ref","HEAD"]).trim(),files:files.slice(0,200),dirtyFiles:dirtyFiles.slice(0,200),status:status.records.slice(0,200),cherry:cherry.slice(0,200),likelyLanded:dirtyFiles.length===0&&cherry.length>0&&cherry.every(line=>line.startsWith("-")),liveProcess:liveCwdPaths.some(cwd=>within(cwd,worktreePath)),manifestOverflow}}),repoStatus=parseStatus(run("git",["-C",root,"status","--porcelain=v1","-z"])),relevantLiveCwds=[...new Set([targetReal,...siblings.map(sibling=>sibling.worktree)].flatMap(worktreePath=>{const hit=liveCwdPaths.find(cwd=>within(cwd,worktreePath));return hit?[hit]:[]}))],manifestOverflow=siblingOverflow||repoStatus.malformed||repoStatus.paths.length>200||siblings.some(sibling=>sibling.manifestOverflow);process.stdout.write(JSON.stringify({target,tempRoot,baseSha:targetHead,repoStatus:repoStatus.records.slice(0,200),repoDirtyFiles:repoStatus.paths.slice(0,200),worktreeList,siblings,liveCwds:relevantLiveCwds,manifestOverflow}))
