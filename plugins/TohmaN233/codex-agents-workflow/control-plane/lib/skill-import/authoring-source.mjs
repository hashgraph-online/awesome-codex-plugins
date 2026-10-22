import { requireValue } from '../workflow-paths.mjs';

export const SKILL_SOURCE='source/SKILL.md';
export const BRIEF_SOURCE='source/WORKFLOW.md';

export function authoringSourcePath(resources){
  const found=[SKILL_SOURCE,BRIEF_SOURCE].filter(path=>Buffer.isBuffer(resources?.[path]));
  requireValue(found.length===1,'AUTHORING_SOURCE','Workflow authoring requires exactly one pinned Skill or Workflow brief entrypoint');
  return found[0];
}

export function authoringSource(resources){
  const path=authoringSourcePath(resources);
  return {path,bytes:resources[path],kind:path===SKILL_SOURCE?'skill':'brief'};
}
