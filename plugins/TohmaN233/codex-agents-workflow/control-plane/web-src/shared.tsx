import { createContext, useContext, useEffect, useId, useState, useSyncExternalStore } from 'react';
import { displayDetails } from './display-data.mjs';
import { getLocale, subscribeLocale, t as translate } from '../web/i18n.js';
import { downloadMcpAppFile, hasInvalidMcpAppMarker, isMcpAppContext, isMcpAppResource, requestMcpApp, token } from './mcp-app-client';
export { token };
export type Json = Record<string, any>; // Open versioned IR: unknown fields must round-trip.
export function useLocale() {
  const locale = useSyncExternalStore(subscribeLocale, getLocale, getLocale);
  return (zh: string, en: string) => locale === 'zh-CN' ? zh : en;
}
export async function request(path: string, data?: unknown, method = 'POST'): Promise<any> {
  if (isMcpAppContext || hasInvalidMcpAppMarker) {
    return requestMcpApp({ path, method: data === undefined ? 'GET' : method, ...(data === undefined ? {} : { body: data }) });
  }
  if (!token) throw new Error(translate('此页面没有控制台凭据。请从 Codex 重新打开控制台。', 'This console page has no credentials. Reopen it from Codex.'));
  const response = await fetch(path, { method: data === undefined ? 'GET' : method,
    headers: { authorization: `Bearer ${token}`, ...(data === undefined ? {} : { 'content-type': 'application/json' }) },
    ...(data === undefined ? {} : { body: JSON.stringify(data) }), signal: AbortSignal.timeout(120000) });
  const body = await response.json();
  if (!response.ok) throw Object.assign(new Error(body.error ?? `HTTP ${response.status}`), { detail: body });
  return body;
}
export const api = (operation: string, args: Json = {}) => request('/api/workflow/' + operation, args);
export const uid = (prefix: string) => prefix + '-' + crypto.randomUUID().slice(0, 8);
export const pretty = (value: unknown) => JSON.stringify(value, null, 2);
export async function download(name: string, value: unknown) {
  const content = pretty(value);
  if (hasInvalidMcpAppMarker) throw new Error('Cannot export from an unsupported MCP App resource.');
  if (isMcpAppResource && await downloadMcpAppFile(name, content)) return;
  const url = URL.createObjectURL(new Blob([content], { type: 'application/json' }));
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = name; anchor.click(); URL.revokeObjectURL(url);
}
export const InvalidContext = createContext<(id: string, invalid: boolean) => void>(() => {});
export const FormValidContext = createContext(true);
export function JsonField({ label, value, onChange, rows = 5 }: { label: string, value: any, onChange: (value: any) => void, rows?: number }) {
  const t = useLocale();
  const id = useId(); const invalid = useContext(InvalidContext); const [text, setText] = useState(pretty(value)); const [error, setError] = useState('');
  const serialized = pretty(value);
  useEffect(() => { setText(serialized); setError(''); invalid(id, false); }, [serialized]);
  useEffect(() => () => invalid(id, false), []);
  return <label className="field">{label}<textarea rows={rows} value={text} spellCheck={false} aria-label={label} aria-invalid={!!error} onChange={event => {
    const next = event.target.value; setText(next);
    try { const parsed = JSON.parse(next); invalid(id, false); setError(''); onChange(parsed); }
    catch (cause) { setError((cause as Error).message); invalid(id, true); }
  }}/>{error && <small role="alert">{t('JSON 格式错误：', 'Invalid JSON: ')}{error}</small>}</label>;
}
export function Field({ label, value, onChange, multiline = false, ...props }: { label: string, value: any, onChange: (value: string) => void, multiline?: boolean, placeholder?: string, readOnly?: boolean }) {
  return <label className="field">{label}{multiline ? <textarea value={value ?? ''} onChange={e => onChange(e.target.value)} rows={6} {...props}/> : <input value={value ?? ''} onChange={e => onChange(e.target.value)} {...props}/>}</label>;
}
export function Select({ label, value, onChange, options }: { label: string, value: string, onChange: (value: string) => void, options: (string | { value: string, label: string })[] }) {
  const t = useLocale();
  const choices = options.map(option => typeof option === 'string' ? { value: option, label: option } : option);
  if (!choices.some(choice => choice.value === value)) choices.unshift({ value, label: value ? `${value} · ${t('缺失，需处理', 'missing; needs attention')}` : t('请选择', 'Select an option') });
  return <label className="field">{label}<select value={value} onChange={e => onChange(e.target.value)}>{choices.map(choice => <option key={choice.value} value={choice.value}>{choice.label}</option>)}</select></label>;
}
export function ProviderField({ providers, value, onChange, main = true, label, emptyLabel }: { providers: Json[], value: string, onChange: (id: string) => void, main?: boolean, label?:string, emptyLabel?:string }) {
  const t = useLocale();
  return <><Select label={label ?? t('固定 Provider', 'Fixed provider')} value={value} onChange={onChange} options={[...(emptyLabel?[{value:'',label:emptyLabel}]:[]),...(main ? [{ value: '$main', label: t('Main · 主控制者', 'Main · controller') }] : []), ...providers.map(p => ({ value: p.id, label: `${p.name ?? p.id}${p.config?.model?' · '+p.config.model+(p.config.reasoning_effort?' / '+p.config.reasoning_effort:''):''}${p.enabled ? '' : ' · '+t('已禁用', 'disabled')}` }))]}/>{providers.find(p=>p.id===value)?.description && <small>{providers.find(p=>p.id===value)?.description}</small>}</>;
}
export function Details({ title, value }: { title: string, value: any }) { return <details><summary>{title}</summary><pre>{displayDetails(value)}</pre></details>; }
const statuses: Record<string, [string, string, string]> = { pending: ['○','等待','Waiting'], ready: ['◇','就绪','Ready'], claimed: ['◈','已领取','Claimed'], running: ['▶','运行中','Running'], succeeded: ['✓','完成','Succeeded'], accepted: ['✓','已接受','Accepted'], exhausted: ['×','轮次耗尽','Round limit reached'], failed: ['×','失败','Failed'], skipped: ['↷','跳过','Skipped'], blocked: ['⊘','阻塞','Blocked'], cancelled: ['■','已取消','Cancelled'], interrupted: ['!','中断','Interrupted'], paused: ['Ⅱ','暂停','Paused'] };
export function Status({ value }: { value?: string }) { const t = useLocale(); const [icon, zh, en] = statuses[value ?? ''] ?? ['○', value ?? '未运行', value ?? 'Not run']; const label = t(zh, en); return <span className={'status status-' + value} title={label} aria-label={label}>{icon} {label}</span>; }
