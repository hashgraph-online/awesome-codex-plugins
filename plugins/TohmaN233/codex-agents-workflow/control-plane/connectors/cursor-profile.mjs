import { basename } from 'node:path';

const INPUT_SELECTOR = [
  '[contenteditable="true"].ui-prompt-input-editor__input',
  '.tiptap.ProseMirror[contenteditable="true"]',
  '.aislash-editor-input',
].join(',');

const INPUT_PICKER = `
  const pickInput=()=>[...document.querySelectorAll(${JSON.stringify(INPUT_SELECTOR)})]
    .filter(e=>e.offsetParent!==null&&!e.disabled&&e.getAttribute('aria-disabled')!=='true'&&(e.getAttribute('contenteditable')==='true'||e.tagName==='INPUT'||e.tagName==='TEXTAREA'))
    .sort((a,b)=>(b.classList&&b.classList.contains('ui-prompt-input-editor__input')?1:0)-(a.classList&&a.classList.contains('ui-prompt-input-editor__input')?1:0))[0]||null;`;

const WORKSPACE_SECTIONS = `
  const headText=(el)=>String(el&&(el.innerText||el.textContent)||'').trim();
  const isNewAgentButton=(node)=>{
    if(!node)return false;
    const aria=String(node.getAttribute&&node.getAttribute('aria-label')||'').trim();
    const text=String(node.innerText||'').trim().split('\\n')[0].trim();
    return /^New Agent$/i.test(aria)||/^New Agent$/i.test(text);
  };
  const findNewAgent=(root)=>[...(root&&root.querySelectorAll?root.querySelectorAll('button,[role=button]'):[])].find(isNewAgentButton)||null;
  const collectWorkspaceSections=()=>{
    const sections=[];const seen=new Set();
    const add=(head,node,button)=>{const name=String(head||'').trim();if(!name)return;const key=name.toLowerCase();if(seen.has(key))return;seen.add(key);sections.push({head:name,node,button:button||findNewAgent(node)});};
    for(const section of document.querySelectorAll('section.glass-sidebar-workspace-section-root'))add(headText(section.querySelector('.ui-sidebar-section-head')),section,null);
    for(const headEl of document.querySelectorAll('.ui-sidebar-section-head')){
      const name=headText(headEl);if(!name)continue;let scope=headEl;let chosen=null;
      for(let i=0;scope&&i<16;i++,scope=scope.parentElement){
        const nested=[...scope.querySelectorAll('.ui-sidebar-section-head')].map(headText).filter(Boolean);
        const unique=[...new Set(nested.map(h=>h.toLowerCase()))];const button=findNewAgent(scope);
        if(button&&unique.length===1&&unique[0]===name.toLowerCase()){chosen={node:scope,button};break;}
      }
      add(name,chosen?chosen.node:headEl,chosen&&chosen.button);
    }
    return sections;
  };`;

// Cursor's public DOM does not expose stable Agent ids. This intentionally small adapter
// normalizes the two React surfaces observed in the reference implementation.
const REACT_ADAPTER = `
  const readScalar=value=>value&&typeof value==='object'&&'value' in value?value.value:value;
  const normalizeTimestamp=(value,index)=>{const raw=readScalar(value);let ts=raw instanceof Date?raw.getTime():Number(raw);if(!Number.isFinite(ts))ts=Date.parse(String(raw||''));return Number.isFinite(ts)?ts:index;};
  const findV2Props=()=>{
    const found=[];const seen=new Set();
    for(const root of document.querySelectorAll('.glass-sidebar-agent-list-container')){
      const nodes=[];let n=root;for(let i=0;n&&i<24;i++,n=n.parentElement)nodes.push(n);
      for(const node of nodes)for(const key of Object.keys(node)){
        if(!key.startsWith('__reactFiber$')&&!key.startsWith('__reactProps$'))continue;
        const seed=node[key];let f=key.startsWith('__reactFiber$')?seed:{memoizedProps:seed,return:null};
        for(let j=0;f&&j<80;j++,f=f.return)for(const p of [f.memoizedProps,f.pendingProps,f.stateNode&&f.stateNode.props]){
          if(p&&p.section&&Array.isArray(p.section.headers)&&typeof p.onSelectAgent==='function'&&!seen.has(p)){seen.add(p);found.push(p);}
        }
      }
    }
    return found;
  };
  const findLegacy=()=>{
    const label=[...document.querySelectorAll('.compact-agent-history-react-menu-label')].find(e=>e.offsetParent!==null);if(!label)return null;
    const nodes=[];let n=label;for(let i=0;n&&i<18;i++,n=n.parentElement)nodes.push(n);
    for(const node of nodes)for(const key of Object.keys(node)){
      if(!key.startsWith('__reactFiber$')&&!key.startsWith('__reactProps$'))continue;
      const seed=node[key];let f=key.startsWith('__reactFiber$')?seed:{memoizedProps:seed,return:null};
      for(let j=0;f&&j<36;j++,f=f.return)for(const p of [f.memoizedProps,f.pendingProps,f.stateNode&&f.stateNode.props]){
        if(p&&Array.isArray(p.entries)&&typeof p.onOpenEntry==='function')return p;
      }
    }
    return null;
  };
  const makeAdapter=()=>{
    const v2=findV2Props();
    if(v2.length)return {
      kind:'agents_v2',entries:()=>{const out=[];const seen=new Set();let index=0;for(const p of v2){const selected=String(readScalar(p.selectedAgentId)||'').replace(/^local:/,'');for(const h of p.section.headers){const raw=String(readScalar(h&&h.id)||'').replace(/^local:/,'');if(!raw||seen.has(raw))continue;seen.add(raw);const status=String(readScalar(h&&h.status)||'').toLowerCase();let terminal='unknown';if(/in_progress|running|generating/.test(status))terminal='running';else if(/done|completed|finished|success|stopped/.test(status))terminal='completed';else if(/cancel/.test(status))terminal='cancelled';else if(/fail|error/.test(status))terminal='failed';out.push({id:'local:'+raw,label:String(readScalar(h&&h.name)||readScalar(h&&h.subtitle)||''),timestamp:normalizeTimestamp(readScalar(h&&h.lastUpdatedAt)||readScalar(h&&h.createdAt),index++),selected:selected===raw,state:terminal});}}return out;},
      open:id=>{const raw=String(id||'').replace(/^local:/,'');for(const p of v2){const h=p.section.headers.find(x=>String(readScalar(x&&x.id)||'').replace(/^local:/,'')===raw);if(h){p.onSelectAgent(h);return true;}}return false;}
    };
    const legacy=findLegacy();if(!legacy)return null;
    return {kind:'legacy',entries:()=>legacy.entries.map((e,index)=>({id:String(e&&e.id||''),label:String(e&&e.label||''),timestamp:normalizeTimestamp(e&&e.timestamp,index),selected:!!(e&&e.isSelected),state:e&&e.showSpinner?'running':/check/i.test(String(e&&e.icon||''))?'completed':/cancel/i.test(String(e&&e.icon||''))?'cancelled':/fail|error|warning/i.test(String(e&&e.icon||''))?'failed':'unknown'})).filter(e=>e.id),open:id=>{const value=String(id||'');if(!legacy.entries.some(e=>String(e&&e.id||'')===value))return false;legacy.onOpenEntry(value);return true;}};
  };
  const adapter=makeAdapter();`;

function marker(name, body) {
  return `(function(){/*sol:${name}*/${body}})()`;
}

export function cursorProbeExpression(workspace) {
  const label = JSON.stringify(basename(workspace).toLowerCase());
  return marker('probe', `${INPUT_PICKER}${WORKSPACE_SECTIONS}${REACT_ADAPTER}
    const input=pickInput();const sections=collectWorkspaceSections();const wanted=${label};const matches=sections.filter(s=>s.head.toLowerCase()===wanted);
    const panels=[...document.querySelectorAll('.agent-panel[data-component="agent-panel"][data-layout="panel"]')].filter(e=>e.offsetParent!==null);
    const panel=panels.length===1?panels[0]:null;
    const panelWorkspaces=panel?[...panel.querySelectorAll('button.ui-select-trigger,.composer-messages-standalone-sidecar-host')].filter(e=>{if(e.offsetParent===null)return false;const text=String(e.innerText||e.textContent||'').trim().toLowerCase();return text===wanted||text.split('\\n').some(line=>line.trim()===('on '+wanted));}):[];
    const panelReady=String(document.title||'')==='Cursor Agents'&&String(document.body.className||'').includes('cursor-glass')&&!!panel&&panelWorkspaces.length===1&&!!input&&panel.contains(input);
    const hasNewAgent=matches.length===1&&!!matches[0].button;
    const ui=panelReady?'agents_panel':document.querySelector('.glass-sidebar-agent-list-container')?'agents_v2':document.querySelector('.aislash-editor-input')?'legacy':'unknown';
    const supported=panelReady||(ui==='agents_v2'&&adapter&&adapter.kind==='agents_v2');
    const workspaceCount=panelReady?panelWorkspaces.length:matches.length;
    const available=panelReady?[...new Set([...sections.map(s=>s.head),...panelWorkspaces.map(e=>String(e.innerText||e.textContent||'').trim())])]:sections.map(s=>s.head);
    return JSON.stringify({ok:supported&&workspaceCount===1&&(!!input||hasNewAgent),ui_flavor:ui,has_input:!!input,has_new_agent:hasNewAgent,workspace_ready:workspaceCount===1,workspace_count:workspaceCount,available,adapter_ready:!!adapter,adapter_kind:adapter&&adapter.kind,supported_profile:supported,document_title:String(document.title||'')});`);
}

export function cursorHistoryExpression() {
  return marker('history', `${REACT_ADAPTER}if(!adapter)return JSON.stringify({ok:false,error:'AGENT_ADAPTER_UNAVAILABLE'});return JSON.stringify({ok:true,kind:adapter.kind,entries:adapter.entries()});`);
}

export function cursorCreateAgentExpression(workspace) {
  const label = JSON.stringify(basename(workspace).toLowerCase());
  return marker('create-agent', `${INPUT_PICKER}${WORKSPACE_SECTIONS}const wanted=${label};const input=pickInput();const panels=[...document.querySelectorAll('.agent-panel[data-component="agent-panel"][data-layout="panel"]')].filter(e=>e.offsetParent!==null);const panel=panels.length===1?panels[0]:null;const panelWorkspaces=panel?[...panel.querySelectorAll('button.ui-select-trigger,.composer-messages-standalone-sidecar-host')].filter(e=>{if(e.offsetParent===null)return false;const text=String(e.innerText||e.textContent||'').trim().toLowerCase();return text===wanted||text.split('\\n').some(line=>line.trim()===('on '+wanted));}):[];if(String(document.title||'')==='Cursor Agents'&&String(document.body.className||'').includes('cursor-glass')&&panel&&panelWorkspaces.length===1&&input&&panel.contains(input)){const composers=[...panel.querySelectorAll('.composer-bar[data-composer-id]')].filter(e=>e.offsetParent!==null&&e.dataset.composerId);if(composers.length>1)return JSON.stringify({ok:false,state:'composer_ambiguous',count:composers.length});if(composers.length===1){const buttons=[...panel.querySelectorAll('button[aria-label="New Agent"]')].filter(e=>e.offsetParent!==null&&!e.disabled);if(buttons.length!==1)return JSON.stringify({ok:false,state:buttons.length?'new_agent_ambiguous':'new_agent_missing',count:buttons.length});const previous='local:'+composers[0].dataset.composerId;buttons[0].click();return JSON.stringify({ok:true,state:'panel_new_agent_clicked',deferred_identity:true,previous_composer_id:previous});}return JSON.stringify({ok:true,state:'panel_ready',deferred_identity:true,previous_composer_id:null});}const sections=collectWorkspaceSections();const matches=sections.filter(s=>s.head.toLowerCase()===wanted);if(matches.length!==1)return JSON.stringify({ok:false,state:matches.length?'workspace_ambiguous':'workspace_missing',available:sections.map(s=>s.head)});if(!matches[0].button)return JSON.stringify({ok:false,state:'new_agent_missing'});matches[0].button.click();return JSON.stringify({ok:true,state:'created',deferred_identity:false});`);
}

export function cursorComposerExpression() {
  return marker('composer', `const composers=[...document.querySelectorAll('.composer-bar[data-composer-id]')].filter(e=>e.offsetParent!==null&&e.dataset.composerId);if(composers.length!==1)return JSON.stringify({ok:false,state:composers.length?'ambiguous':'missing',count:composers.length});const c=composers[0];return JSON.stringify({ok:true,id:'local:'+c.dataset.composerId,status:c.dataset.composerStatus||null});`);
}

export function cursorFillExpression(text) {
  const value = JSON.stringify(text);
  const fixturePayload = Buffer.from(text, 'utf8').toString('base64');
  return marker('fill', `/*sol-payload:${fixturePayload}*/${INPUT_PICKER}const input=pickInput();if(!input)return 'NO_INPUT';input.focus();try{const selection=getSelection();const range=document.createRange();range.selectNodeContents(input);selection.removeAllRanges();selection.addRange(range);}catch{}const ok=document.execCommand('insertText',false,${value});try{input.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:${value}}));}catch{input.dispatchEvent(new Event('input',{bubbles:true}));}return ok?'FILLED':'EXEC_FAIL';`);
}

export function cursorSnapshotExpression(agentId = '') {
  const expected = JSON.stringify(String(agentId || '').replace(/^local:/, ''));
  return marker('snapshot', `${INPUT_PICKER}const expected=${expected};const composers=[...document.querySelectorAll('.composer-bar[data-composer-id]')].filter(e=>e.offsetParent!==null&&e.dataset.composerId);const exact=expected?composers.filter(e=>e.dataset.composerId===expected):composers;const md=[...document.querySelectorAll('.markdown-root,.aichat-container [class*=markdown]')].filter(e=>e.offsetParent!==null&&!e.closest('.ui-model-picker__trigger,[class*=model-picker]'));const texts=md.map(e=>(e.innerText||'').trim()).filter(Boolean);const last=texts[texts.length-1]||'';let hash=0;for(let i=0;i<last.length;i++)hash=((hash<<5)-hash+last.charCodeAt(i))|0;const stop=[...document.querySelectorAll('[class*=codicon-stop],[class*=debug-stop],[aria-label*=Stop],[aria-label*=stop],[aria-label*=Cancel],[title*=Stop]')].filter(e=>e.offsetParent!==null).length;const input=pickInput();const inputText=String(input&&(input.innerText||input.textContent)||'').trim();return JSON.stringify({message_count:texts.length,reply_length:last.length,reply_hash:hash,stop,input_length:inputText.length,identity_match:expected?exact.length===1:true,visible_composer_count:composers.length,expected_agent_id:expected||null});`);
}

export function cursorExtractExpression() {
  return marker('extract', `const md=[...document.querySelectorAll('.markdown-root,.aichat-container [class*=markdown]')].filter(e=>e.offsetParent!==null&&!e.closest('.ui-model-picker__trigger,[class*=model-picker]'));const texts=md.map(e=>(e.innerText||'').trim()).filter(Boolean);return texts[texts.length-1]||'';`);
}

export function cursorClickSendExpression() {
  return marker('send', `${INPUT_PICKER}const input=pickInput();if(!input)return 'NO_INPUT';const composer=input.closest('.composer-bar')||input.parentElement;if(!composer)return 'NO_COMPOSER';const buttons=[...composer.querySelectorAll('button.ui-prompt-input-submit-button[data-state="send"],button[aria-label="Send"]')].filter(button=>button.offsetParent!==null&&!button.disabled);if(buttons.length!==1)return buttons.length?'AMBIGUOUS_SEND':'NO_SEND';buttons[0].click();return 'CLICKED';`);
}

export function cursorOpenAgentExpression(agentId) {
  const id = JSON.stringify(agentId);
  return marker('open-agent', `${REACT_ADAPTER}if(!adapter)return 'AGENT_ADAPTER_UNAVAILABLE';return adapter.open(${id})?'OPENED':'AGENT_NOT_FOUND';`);
}

export function cursorStopExpression(agentId) {
  const raw = JSON.stringify(String(agentId).replace(/^local:/, ''));
  return marker('stop', `const expected=${raw};const composers=[...document.querySelectorAll('.composer-bar[data-composer-id]')].filter(e=>e.offsetParent!==null&&e.dataset.composerId===expected);if(composers.length!==1)return JSON.stringify({clicked:false,state:'composer_identity_mismatch',count:composers.length});const composer=composers[0];if(composer.dataset.composerStatus!=='generating')return JSON.stringify({clicked:false,state:'not_generating',status:composer.dataset.composerStatus||null});const generation=[...document.querySelectorAll('button.ui-prompt-input-submit-button[data-state="stop"][aria-label="Stop generation"]')].filter(e=>e.offsetParent!==null&&!e.disabled);const command=[...document.querySelectorAll('button.ui-shell-tool-call__glass-stop[aria-label="Stop command"]')].filter(e=>e.offsetParent!==null&&!e.disabled);const buttons=[...generation,...command];if(buttons.length!==1)return JSON.stringify({clicked:false,state:buttons.length?'ambiguous_stop':'stop_missing',count:buttons.length});buttons[0].click();return JSON.stringify({clicked:true,state:'clicked'});`);
}

export function selectNewCursorAgent(before, after) {
  const known = new Set((before || []).map((entry) => entry.id));
  const fresh = (after || []).filter((entry) => entry?.id && !known.has(entry.id));
  if (fresh.length !== 1) return { agent: null, ambiguous: fresh.length > 1, count: fresh.length };
  return { agent: fresh[0], ambiguous: false, count: 1 };
}

export function classifyCursorEntry(entry) {
  return entry?.state || 'unknown';
}
