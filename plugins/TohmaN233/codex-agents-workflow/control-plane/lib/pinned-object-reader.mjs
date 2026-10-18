import {readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {statNoSymlinks,requireValue} from './workflow-paths.mjs';
import {digest,LIMITS} from './workflow-revisions.mjs';

// A fresh committed manifest identifies the exact object. Every actual
// consumption checks the file and bytes; ordinary journal reads confer no
// resource-content integrity and never replace this boundary.
export async function readPinnedObject(objectDirectory,pin){
  requireValue(pin&&/^[a-f0-9]{64}$/.test(pin.sha256)&&Number.isSafeInteger(pin.bytes)
    &&pin.bytes>=0&&pin.bytes<=LIMITS.resource,'RUN_RESOURCE','Invalid pinned object digest or byte bound');
  const path=join(objectDirectory,pin.sha256),{stat:info}=await statNoSymlinks(path);
  requireValue(info.isFile()&&info.size<=LIMITS.resource,'RUN_RESOURCE','Pinned object must be a bounded regular file');
  const bytes=await readFile(path);
  requireValue(bytes.length<=LIMITS.resource&&bytes.length===pin.bytes&&digest(bytes)===pin.sha256,
    'RUN_RESOURCE_CORRUPT','Pinned object is missing or modified');
  return bytes;
}
