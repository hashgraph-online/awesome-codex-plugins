import * as readline from 'node:readline';

// A search-filterable multiselect prompt with an optional locked "always
// included" section, replicating the `npx skills` add wizard. Rendered with
// clack-compatible symbols so it sits seamlessly between clack prompts.

const ESC = '\x1b[';
const show = (code: string) => `${ESC}${code}`;
export const color = {
  reset: (s: string) => `${show('0m')}${s}${show('0m')}`,
  bold: (s: string) => `${show('1m')}${s}${show('22m')}`,
  dim: (s: string) => `${show('2m')}${s}${show('22m')}`,
  cyan: (s: string) => `${show('36m')}${s}${show('39m')}`,
  green: (s: string) => `${show('32m')}${s}${show('39m')}`,
  yellow: (s: string) => `${show('33m')}${s}${show('39m')}`,
  gray: (s: string) => `${show('90m')}${s}${show('39m')}`,
};

const S_BAR = color.gray('│');
const S_BAR_END = color.gray('└');
const S_ACTIVE = color.green('◆');
const S_SUBMIT = color.green('◇');
const S_CANCEL = color.yellow('■');
const S_CHECKBOX_ON = color.green('◼');
const S_CHECKBOX_OFF = '◻';
const S_POINTER = color.cyan('❯');
const S_BULLET = color.green('•');
const RULE = '─';

export const PROMPT_CANCELLED: unique symbol = Symbol('prompt-cancelled');

export interface SearchItem {
  value: string;
  label: string;
  hint?: string;
}

export interface LockedSection {
  title: string;
  items: SearchItem[];
  hiddenCount?: number;
}

export interface SearchMultiselectOptions {
  message: string;
  items: SearchItem[];
  maxVisible?: number;
  initialSelected?: string[];
  required?: boolean;
  /** items always installed, rendered as a bold non-interactive section */
  lockedSection?: LockedSection;
}

function truncate(text: string, max: number): string {
  if (max <= 1 || text.length <= max) return text;
  return `${text.slice(0, max - 1)}…`;
}

function summarize(labels: string[], max = 3): string {
  if (labels.length <= max) return labels.join(', ');
  return `${labels.slice(0, max).join(', ')} +${labels.length - max} more`;
}

export function searchMultiselect(
  options: SearchMultiselectOptions,
): Promise<string[] | typeof PROMPT_CANCELLED> {
  const {
    message,
    items,
    maxVisible = 8,
    initialSelected = [],
    required = false,
    lockedSection,
  } = options;

  return new Promise((resolvePromise) => {
    const stdin = process.stdin;
    const stdout = process.stdout;
    const rl = readline.createInterface({ input: stdin, terminal: false });
    if (stdin.isTTY) stdin.setRawMode(true);
    readline.emitKeypressEvents(stdin, rl);

    let query = '';
    let cursor = 0;
    const selected = new Set(
      initialSelected.filter((value) => items.some((item) => item.value === value)),
    );
    let lastRenderHeight = 0;

    const columns = () => (stdout.columns && stdout.columns > 0 ? stdout.columns : 80);

    const filtered = () => {
      if (!query) return items;
      const q = query.toLowerCase();
      return items.filter(
        (item) => item.label.toLowerCase().includes(q) || item.value.toLowerCase().includes(q),
      );
    };

    const clearRender = () => {
      if (lastRenderHeight > 0) {
        stdout.write(`${ESC}${lastRenderHeight}A`);
        for (let i = 0; i < lastRenderHeight; i += 1) stdout.write(`${ESC}2K${ESC}1B`);
        stdout.write(`${ESC}${lastRenderHeight}A`);
      }
    };

    const selectionSummary = () => {
      const lockedLabels = lockedSection ? lockedSection.items.map((item) => item.label) : [];
      const pickedLabels = items
        .filter((item) => selected.has(item.value))
        .map((item) => item.label);
      return [...lockedLabels, ...pickedLabels];
    };

    const render = (state: 'active' | 'submit' | 'cancel' = 'active') => {
      clearRender();
      const lines: string[] = [];
      const icon = state === 'active' ? S_ACTIVE : state === 'cancel' ? S_CANCEL : S_SUBMIT;
      lines.push(`${icon}  ${color.bold(message)}`);

      if (state === 'active') {
        if (lockedSection && lockedSection.items.length > 0) {
          lines.push(S_BAR);
          const title = `${RULE.repeat(2)} ${color.bold(lockedSection.title)} ${color.dim(`${RULE.repeat(2)} always included`)} ${RULE.repeat(14)}`;
          lines.push(`${S_BAR}  ${color.gray(title)}`);
          for (const item of lockedSection.items) {
            lines.push(`${S_BAR}    ${S_BULLET} ${color.bold(item.label)}`);
          }
          if (lockedSection.hiddenCount && lockedSection.hiddenCount > 0) {
            lines.push(`${S_BAR}    ${color.dim(`...and ${lockedSection.hiddenCount} more`)}`);
          }
          lines.push(S_BAR);
          lines.push(
            `${S_BAR}  ${color.gray(`${RULE.repeat(2)} ${color.bold('Additional agents')} ${RULE.repeat(29)}`)}`,
          );
        }

        lines.push(`${S_BAR}  ${color.dim('Search:')} ${query}${color.reset('█')}`);
        lines.push(`${S_BAR}  ${color.dim('↑↓ move, space select, enter confirm')}`);
        lines.push(S_BAR);

        const list = filtered();
        if (cursor >= list.length) cursor = Math.max(0, list.length - 1);
        const windowStart = Math.max(
          0,
          Math.min(cursor - Math.floor(maxVisible / 2), list.length - maxVisible),
        );
        const visible = list.slice(windowStart, windowStart + maxVisible);

        if (list.length === 0) {
          lines.push(`${S_BAR}  ${color.dim('No matches')}`);
        }
        if (windowStart > 0) {
          lines.push(`${S_BAR}  ${color.dim(`↑ ${windowStart} more`)}`);
        }
        visible.forEach((item, index) => {
          const absolute = windowStart + index;
          const isCursor = absolute === cursor;
          const box = selected.has(item.value) ? S_CHECKBOX_ON : S_CHECKBOX_OFF;
          const label = isCursor ? color.cyan(item.label) : item.label;
          const hint = item.hint
            ? ` ${color.dim(`(${truncate(item.hint, columns() - item.label.length - 12)})`)}`
            : '';
          lines.push(`${isCursor ? S_POINTER : ' '} ${box} ${label}${hint}`);
        });
        const below = list.length - windowStart - visible.length;
        if (below > 0) {
          lines.push(`${S_BAR}  ${color.dim(`↓ ${below} more`)}`);
        }

        const summary = selectionSummary();
        lines.push(S_BAR);
        if (summary.length > 0) {
          lines.push(`${S_BAR}  ${color.green('Selected:')} ${summarize(summary)}`);
        } else {
          lines.push(`${S_BAR}  ${color.dim('Nothing selected yet')}`);
        }
        lines.push(S_BAR_END);
      } else {
        const summary = selectionSummary();
        lines.push(
          `${S_BAR}  ${color.dim(state === 'cancel' ? 'Cancelled' : summarize(summary) || 'none')}`,
        );
      }

      stdout.write(`${lines.join('\n')}\n`);
      lastRenderHeight = lines.length;
    };

    const finish = (result: string[] | typeof PROMPT_CANCELLED, state: 'submit' | 'cancel') => {
      render(state);
      stdin.removeListener('keypress', onKeypress);
      if (stdin.isTTY) stdin.setRawMode(false);
      rl.close();
      resolvePromise(result);
    };

    const onKeypress = (char: string | undefined, key: readline.Key) => {
      if (key.ctrl && key.name === 'c') return finish(PROMPT_CANCELLED, 'cancel');
      if (key.name === 'escape') return finish(PROMPT_CANCELLED, 'cancel');
      if (key.name === 'return' || key.name === 'enter') {
        const hasLocked = Boolean(lockedSection && lockedSection.items.length > 0);
        if (required && selected.size === 0 && !hasLocked) return;
        return finish([...selected], 'submit');
      }
      if (key.name === 'up') {
        cursor = Math.max(0, cursor - 1);
      } else if (key.name === 'down') {
        cursor = Math.min(Math.max(0, filtered().length - 1), cursor + 1);
      } else if (key.name === 'space') {
        const item = filtered()[cursor];
        if (item) {
          if (selected.has(item.value)) selected.delete(item.value);
          else selected.add(item.value);
        }
      } else if (key.name === 'backspace') {
        query = query.slice(0, -1);
        cursor = 0;
      } else if (char && char.length === 1 && !key.ctrl && !key.meta && char >= ' ') {
        query += char;
        cursor = 0;
      }
      render();
    };

    stdin.on('keypress', onKeypress);
    render();
  });
}
