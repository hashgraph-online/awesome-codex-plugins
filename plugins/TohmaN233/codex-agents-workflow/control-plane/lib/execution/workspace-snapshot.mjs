import {join, relative} from 'node:path';
import * as fs from 'node:fs/promises';
import {digest} from '../workflow-revisions.mjs';
import {requireValue} from '../workflow-paths.mjs';

const key = path => process.platform === 'win32' ? path.toLowerCase() : path;
const within = (path, boundary) => {
  path=key(path); boundary=key(boundary.replaceAll('\\','/').replace(/\/$/,''));
  return boundary==='.' || path===boundary || path.startsWith(boundary+'/');
};

// A write-scope audit needs the boundary of an authorized private subtree,
// not permission to read all of its contents. Required artifacts still need
// readable bytes; unreadable paths outside the authorized subtree fail closed.
export async function snapshotWorkspace(root, {access='read_only', allowedPaths=[], requiredPaths=[], onUnreadable,
  codePrefix='HOST_MAIN', fileSystem=fs}={}) {
  const result=new Map(); result.unreadablePaths=new Map();
  let files=0, bytes=0;
  async function observeUnreadable(error, path, stat) {
    if(!['EACCES','EPERM'].includes(error.code))throw error;
    const authorized=path && access==='bounded_write' && allowedPaths.some(boundary=>within(path,boundary));
    const required=requiredPaths.some(required=>within(required,path));
    if(!authorized || required || typeof onUnreadable!=='function')throw error;
    const observation={path,kind:stat.isDirectory()?'directory':'file',error_code:error.code,
      coverage:'authorized_boundary_only',dev:String(stat.dev),ino:String(stat.ino),birthtime_ms:String(stat.birthtimeMs)};
    await onUnreadable(observation); // Persistence failure must not hide incomplete coverage.
    result.unreadablePaths.set(path,observation);
  }
  async function walk(directory, directoryStat) {
    let entries;
    try { entries=await fileSystem.readdir(directory,{withFileTypes:true}); }
    catch(error) {
      const path=relative(root,directory).replaceAll('\\','/');
      await observeUnreadable(error,path,directoryStat); return;
    }
    for(const entry of entries) {
      if(entry.name==='.git')continue;
      const absolute=join(directory,entry.name), path=relative(root,absolute).replaceAll('\\','/');
      const stat=await fileSystem.lstat(absolute);
      requireValue(!stat.isSymbolicLink(),codePrefix+'_WORKSPACE_SYMLINK',`Workspace contains a symbolic link: ${path}`);
      if(stat.isDirectory()){await walk(absolute,stat);continue;}
      if(!stat.isFile())continue;
      files++;bytes+=stat.size;
      requireValue(files<=20000 && bytes<=2*1024*1024*1024,codePrefix+'_WORKSPACE_LIMIT','Workspace exceeds the bounded audit snapshot');
      let contents;
      try{contents=await fileSystem.readFile(absolute);}
      catch(error){await observeUnreadable(error,path,stat);continue;}
      result.set(path,digest(contents));
    }
  }
  await walk(root);return result;
}

export function changedWorkspacePaths(before,after) {
  const signature=(snapshot,path)=>snapshot.has(path)?snapshot.get(path):JSON.stringify(snapshot.unreadablePaths?.get(path));
  return [...new Set([...before.keys(),...after.keys(),...(before.unreadablePaths?.keys()??[]),...(after.unreadablePaths?.keys()??[])])]
    .filter(path=>signature(before,path)!==signature(after,path)).sort();
}
