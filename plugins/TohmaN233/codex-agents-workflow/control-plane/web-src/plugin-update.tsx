import {useEffect,useState} from 'react';
import {request,useLocale,type Json} from './shared';
declare const __CODEX_WORKFLOW_VERSION__:string;
const repository='https://github.com/TohmaN233/codex-agents-workflow';
export function PluginUpdate(){
  const t=useLocale(),[update,setUpdate]=useState<Json|null>(null),[error,setError]=useState('');
  useEffect(()=>{let mounted=true;request('/api/plugin-update').then(value=>{if(mounted)setUpdate(value);}).catch(cause=>{if(mounted)setError(cause.message);});return()=>{mounted=false;};},[]);
  return <div className="plugin-update">
    <span>v{__CODEX_WORKFLOW_VERSION__}</span>
    {update&&<span role="status">{update.status==='update_available'?<a className="plugin-update-available" href={repository+'#installation'} target="_blank" rel="noopener noreferrer">{t(`有更新 v${update.latest_version}`,`Update available: v${update.latest_version}`)}</a>:<span className="muted">{update.status==='ahead'?t('本地版本较新','Local version is newer'):t('已是最新','Up to date')}</span>}</span>}
    {error&&<span role="status" title={error}>{t('无法检查更新','Update check unavailable')}</span>}
    <a className="plugin-star" href={repository} target="_blank" rel="noopener noreferrer" aria-label={t('在 GitHub 为项目点 Star','Star the project on GitHub')}>☆ Star</a>
  </div>;
}
