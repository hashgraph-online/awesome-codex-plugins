import { useState } from 'react';
import { api, Field, useLocale, type Json } from './shared';

export function WorkflowInstallPanel({act,busy,installed,back}:{act:(operation:()=>Promise<void>)=>void,busy:number,installed:(pack:Json)=>Promise<void>,back:()=>void}){
  const t=useLocale();const [sourceUrl,setSourceUrl]=useState(''),[packageJson,setPackageJson]=useState(''),[filePackage,setFilePackage]=useState<Json|null>(null),[expectedSha256,setExpectedSha256]=useState(''),[fileName,setFileName]=useState('');
  const selectFile=(file?:File)=>act(async()=>{
    if(!file)return;
    if(file.size>70*1024*1024)throw new Error(t('安装包不能超过 70 MiB。','The install package cannot exceed 70 MiB.'));
    const text=await file.text(),parsed=JSON.parse(text);
    if(parsed?.format!=='codex.workflow.package')throw new Error(t('所选文件不是可安装包。请导出并选择“.workflow-package.json”；完整 Pack 快照仅用于审计和排障。','The selected file is not an install package. Export and choose the “.workflow-package.json” file; a full Pack snapshot is for auditing and diagnosis.'));
    setFilePackage(parsed);setPackageJson('');setFileName(file.name);setSourceUrl('');
  });
  const install=()=>act(async()=>{
    const args:Json={};
    if(sourceUrl.trim()){args.source_url=sourceUrl.trim();if(expectedSha256.trim())args.expected_sha256=expectedSha256.trim();}
    else if(filePackage)args.package=filePackage;
    else {if(!packageJson.trim())throw new Error(t('请选择文件、粘贴安装包 JSON 或填写 HTTPS 地址。','Choose a file, paste package JSON, or enter an HTTPS URL.'));args.package=JSON.parse(packageJson);}
    await installed(await api('install_workflow_package',args));
  });
  return <main className="detail-page scroll"><span className="eyebrow">{t('Workflow 生态','Workflow ecosystem')}</span><h1>{t('安装 Workflow','Install a Workflow')}</h1><p>{t('安装经过内容哈希、格式版本、Workflow Schema、资源清单和依赖清单校验。选择本地文件最直接；远程安装只接受 HTTPS。','Installation verifies the content digest, package format, Workflow schema, resources, and dependency manifest. Selecting a local file is the direct path; remote installation accepts HTTPS only.')}</p>
    <section className="install-source"><h2>{t('选择本地安装包','Choose a local install package')}</h2><label className="file-picker"><span>{t('选择 .workflow-package.json 文件','Choose a .workflow-package.json file')}</span><input type="file" accept=".json,.workflow-package.json,application/json" disabled={busy>0} onChange={event=>selectFile(event.target.files?.[0])}/></label>{fileName&&<p className="muted">{t('已选择：','Selected: ')}{fileName}</p>}</section>
    <details><summary>{t('其他导入方式','Other import methods')}</summary><Field label={t('云端安装包 HTTPS 地址','Cloud package HTTPS URL')} value={sourceUrl} onChange={value=>{setSourceUrl(value);if(value.trim()){setPackageJson('');setFilePackage(null);setFileName('');}}}/><Field label={t('下载文件 SHA-256（可选）','Downloaded file SHA-256 (optional)')} value={expectedSha256} onChange={setExpectedSha256}/><Field label={t('或粘贴本地安装包 JSON','Or paste a local package JSON')} value={packageJson} multiline onChange={value=>{setPackageJson(value);if(value.trim()){setSourceUrl('');setFilePackage(null);setFileName('');}}}/></details>
    <aside className="format-explainer"><strong>{t('两种导出的区别','The two export formats')}</strong><p>{t('「完整 Pack 快照」包含编辑器使用的完整修订和资源，适合审计与故障排查，也可能包含私有转换素材。「可安装包」带兼容性、依赖和完整性清单，并排除私有 source/ 素材；跨电脑导入请选它。','A “full Pack snapshot” contains the complete editor revision and resources for auditing and diagnosis, and may include private conversion material. An “install package” adds compatibility, dependency, and integrity manifests and excludes private source/ material; use it to move a Workflow between computers.')}</p></aside>
    <div className="actions"><button className="primary" disabled={busy>0} onClick={install}>{t('校验并安装','Validate and install')}</button><button disabled={busy>0} onClick={back}>{t('返回流程库','Back to library')}</button></div></main>;
}
