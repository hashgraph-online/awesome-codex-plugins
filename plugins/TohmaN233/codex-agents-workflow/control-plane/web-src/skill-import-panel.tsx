import { useEffect, useRef, useState } from 'react';
import { api, Field, ProviderField, Details, uid, useLocale, type Json } from './shared';

export function SkillImportPanel({act, busy, providers, imported}: {act:(work:()=>Promise<any>)=>void, busy:number, providers:Json[], imported:(value:Json)=>Promise<void>}) {
  const t = useLocale();
  const [folder,setFolder] = useState('');
  const [provider,setProvider] = useState('$main');
  const [inventory,setInventory] = useState<Json|null>(null);
  const generation = useRef(0);
  const scan = (path:string) => { const ticket = ++generation.current; setInventory(null); act(async()=>{
    const result = await api('skill_inventory',{discovery:'folders',...(path.trim()?{folder:path.trim()}:{})});
    if (generation.current === ticket) setInventory({...result,folder:path.trim()});
  }); };
  useEffect(()=>{scan('');return ()=>{generation.current++;};},[]);
  return <main className="detail-page scroll"><span className="eyebrow">{t('单向导入', 'One-way import')}</span><h1>{t('从 Skill 创建 Draft', 'Create a draft from a Skill')}</h1>
    <p>{t('默认扫描当前用户的 Codex 技能目录和插件缓存（通常位于 C:/Users/用户名/.codex）。也可以指定自己的文件夹。这里只发现可导入文件，不代表这些 Skill 已启用或获得执行权限。', 'By default, scans the current user’s Codex skills directory and plugin cache (usually under C:/Users/username/.codex). You can also specify a folder. This only discovers importable files; it does not mean those Skills are enabled or authorized to run.')}</p>
    <Field label={t('其他 Skill 文件夹（可选，绝对路径）', 'Other Skill folder (optional, absolute path)')} value={folder} onChange={value=>{setFolder(value);generation.current++;setInventory(null);}}/>
    <button disabled={busy>0} onClick={()=>scan(folder)}>{t('扫描文件夹', 'Scan folder')}</button><button disabled={busy>0} onClick={()=>{setFolder('');scan('');}}>{t('扫描默认 Codex 目录', 'Scan the default Codex directory')}</button>
    <details><summary>{t('高级导入设置', 'Advanced import settings')}</summary><p>{t('初始草稿执行者。自动生成时会按规则为各步骤分别选择执行者。', 'Initial draft executor. Automatic generation chooses an executor for each step according to the routing rules.')}</p>
    <ProviderField providers={providers} value={provider} onChange={setProvider}/></details>
    {inventory && <><Details title={t('扫描范围与错误（缓存可能包含多个版本）', 'Scan scope and errors (the cache may contain multiple versions)')} value={{...inventory,entries:undefined}}/>{inventory.entries.map((item:Json)=><article className="history-row" key={item.id}><div><strong>{item.name}</strong><p>{item.path}</p><small>{item.source_hash}</small></div><button disabled={!provider || busy>0} onClick={()=>act(async()=>imported(await api('import_skill',{discovery:'folders',...(inventory.folder?{folder:inventory.folder}:{}),skill_id:item.id,workflow_id:uid('import'),...(provider==='$main'?{}:{provider_id:provider})})))}>{t('导入此版本', 'Import this version')}</button></article>)}</>}
  </main>;
}
