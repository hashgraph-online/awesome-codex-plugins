import {useState} from 'react';
import {api,Details,useLocale,type Json} from './shared';
export function CacheCleanup({act,busy}:{act:(fn:()=>Promise<unknown>)=>unknown,busy:number}) {
  const t = useLocale();
  const [result,setResult]=useState<Json|null>(null);
  const [preview,setPreview]=useState(false);
  return <details><summary>{t('旧版本缓存清理', 'Old version cache cleanup')}</summary><p>{t('一键清理未引用的工作流历史版本、资源及本插件旧安装缓存。保留当前版本、运行记录和固定引用、正在使用的插件版本。已清理的历史版本不能恢复。', 'Clean up unreferenced workflow revisions, resources, and old plugin installation caches in one action. Current versions, run records, pinned references, and versions in use are kept. Cleaned history cannot be recovered.')}</p>
    <button disabled={busy>0} onClick={()=>act(async()=>{setResult(await api('cache_cleanup_preview'));setPreview(true);})}>{t('查看可清理空间', 'Preview reclaimable space')}</button>{' '}
    <button disabled={busy>0} onClick={()=>act(async()=>{setResult(await api('cleanup_caches'));setPreview(false);})}>{t('一键清理旧版本缓存', 'Clean old version caches')}</button>
    {result && <><p>{preview?t('可清理', 'Reclaimable'):t('已清理', 'Cleaned')}: {result.workflow_revisions} {t('个工作流历史版本', 'workflow revisions')}, {result.workflow_resources} {t('个资源', 'resources')}, {result.plugin_versions} {t('个插件旧版本', 'old plugin versions')}; {t('共', 'total')} {(result.bytes/1024/1024).toFixed(2)} MB{t('。', '.')}</p>{!preview && result.deferred_plugin_versions?.length>0 && <p>{t('仍有被系统占用的插件旧版本未清理；已保留，关闭占用它的进程后可重试：', 'Busy plugin versions were retained; close the processes using them and retry: ')}{result.deferred_plugin_versions.join(', ')}</p>}<Details title={t('清理详情与保留记录', 'Cleanup details and retained records')} value={result}/></>}
  </details>;
}
