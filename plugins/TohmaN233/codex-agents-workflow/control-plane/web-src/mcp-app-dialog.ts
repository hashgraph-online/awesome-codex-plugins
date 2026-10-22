// Native browser dialogs can be disabled by an MCP host's iframe sandbox.
// Keep existing confirmations inside the App without requesting host privileges.
let pending = Promise.resolve();

export function confirmWorkbench(message: string): Promise<boolean> {
  if (!document.querySelector('meta[name="codex-agents-workflow-app"]')) {
    return Promise.resolve(window.confirm(message));
  }
  const response = pending.then(() => new Promise<boolean>((resolve, reject) => {
    const dialog = document.createElement('dialog');
    dialog.setAttribute('aria-label', message);
    dialog.style.cssText = 'max-width:min(30rem,calc(100vw - 3rem));border:1px solid var(--color-border-primary,#aaa);border-radius:12px;padding:24px;background:var(--color-background-primary,#f5f1e9);color:var(--color-text-primary,#29251f);font:inherit;box-shadow:0 16px 60px #0003';
    const text = document.createElement('p');
    text.textContent = message;
    text.style.cssText = 'margin:0 0 24px;line-height:1.6';
    const actions = document.createElement('div');
    actions.style.cssText = 'display:flex;justify-content:flex-end;gap:12px';
    const english = document.documentElement.lang.startsWith('en');
    const cancel = document.createElement('button');
    const accept = document.createElement('button');
    cancel.textContent = english ? 'Cancel' : '取消';
    accept.textContent = english ? 'Continue' : '继续';
    cancel.autofocus = true;
    for (const button of [cancel, accept]) {
      button.type = 'button';
      button.style.cssText = 'border:1px solid currentColor;border-radius:7px;padding:8px 16px;background:transparent;color:inherit;font:inherit;cursor:pointer';
    }
    actions.append(cancel, accept);
    dialog.append(text, actions);
    let settled = false;
    function finish(value: boolean) {
      if (settled) return;
      settled = true;
      dialog.remove();
      resolve(value);
    }
    cancel.addEventListener('click', () => finish(false));
    accept.addEventListener('click', () => finish(true));
    dialog.addEventListener('cancel', event => { event.preventDefault(); finish(false); });
    dialog.addEventListener('close', () => finish(false));
    document.body.append(dialog);
    try { dialog.showModal(); }
    catch (error) { dialog.remove(); reject(error); }
  }));
  pending = response.then(() => {}, () => {});
  return response;
}
