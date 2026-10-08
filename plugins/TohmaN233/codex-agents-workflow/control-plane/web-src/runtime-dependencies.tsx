import {useEffect, useState} from 'react';
import {api, Details, Field, useLocale, type Json} from './shared';

export function RuntimeDependencies() {
  const t=useLocale();
  const [registry,setRegistry]=useState<Json|null>(null),[result,setResult]=useState<Json|null>(null);
  const [name,setName]=useState(''),[version,setVersion]=useState(''),[modules,setModules]=useState(''),[path,setPath]=useState('');
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  const requirement=()=>({name,...(version.trim()?{version:version.trim()}:{}),...(modules.trim()?{python_modules:modules.split(',').map(value=>value.trim()).filter(Boolean)}:{})});
  const reload=async()=>setRegistry(await api('runtime_dependencies'));
  async function act(work:()=>Promise<void>) {
    setBusy(true);setError('');
    try {await work();} catch(cause:any) {setError(cause.message);} finally {setBusy(false);}
  }
  useEffect(()=>{void act(reload);},[]);
  const candidates=Object.values(registry?.candidates??{}) as Json[];
  return <section>
    <h2>{t('本机任务依赖','Local task dependencies')}</h2>
    <p>{t('启动时先验证已登记位置，再搜索本机安装。这里保存的路径仅用于本机，不随工作流导出；找不到依赖时，安装前会询问。','Startup verifies registered locations, then searches local installations. These paths stay on this host and are excluded from workflow exports. Missing dependencies require approval before installation.')}</p>
    <button disabled={busy} onClick={()=>void act(reload)}>{t('刷新登记记录','Refresh registrations')}</button>
    {candidates.length>0 && <table><thead><tr><th>{t('依赖','Dependency')}</th><th>{t('本机路径','Local path')}</th><th>{t('最近验证','Last verified')}</th><th></th></tr></thead><tbody>{candidates.map(item=><tr key={item.requirement_key}>
      <td>{item.name}{item.evidence.observed_version?` ${item.evidence.observed_version}`:''}</td><td><code>{item.path}</code></td><td>{item.checked_at}</td>
      <td><button disabled={busy} onClick={()=>{setName(item.name);setPath(item.path);setVersion(item.requirement?.version??'');setModules((item.requirement?.python_modules??[]).join(', '));}}>{t('编辑','Edit')}</button></td>
    </tr>)}</tbody></table>}
    <p className="muted">{t('登记记录表示上次验证结果，执行前会再次检查。','Registrations show the last verification result and are checked again before execution.')}</p>
    <Field label={t('工具名称，如 python','Program name, e.g. python')} value={name} onChange={setName}/>
    <Field label={t('版本要求（可选，如 >=3.11,<4）','Version requirement (optional, e.g. >=3.11,<4)')} value={version} onChange={setVersion}/>
    <Field label={t('Python 模块（可选，逗号分隔）','Python modules (optional, comma-separated)')} value={modules} onChange={setModules}/>
    <Field label={t('本机可执行文件路径','Local executable path')} value={path} onChange={setPath}/>
    <button disabled={busy||!name.trim()} onClick={()=>void act(async()=>{setResult(await api('discover_runtime_dependencies',{executables:[requirement()]}));await reload();})}>{t('搜索本机并登记','Discover and register')}</button>
    <button disabled={busy||!name.trim()||!path.trim()} onClick={()=>void act(async()=>{setResult(await api('register_runtime_dependency',{requirement:requirement(),path}));await reload();})}>{t('验证所填路径并保存','Verify path and save')}</button>
    {error && <p role="alert">{error}</p>}
    {result?.status==='installation_approval_required' && <p role="status">{t('搜索后仍未找到满足要求的依赖。可填写已有安装的位置，或同意安装后重新检查。','No matching installation was found. Supply an existing installation path, or approve installation and check again.')}</p>}
    {result && <Details title={t('验证与搜索结果','Verification and discovery results')} value={result}/>}
  </section>;
}
