export const title = 'Two-phase commit (two resource managers)';
export function state({ rm, tm }) {
  const rms = Object.keys(rm).sort().map((k) => `${k} ${rm[k]}`).join(', ');
  return [`coordinator ${tm}`, rms];
}
export function step(action) {
  return action === 'Done' ? 'finished' : action.toLowerCase();
}
export function group({ tm }) { return tm; }
export const colors = { init: 'blue', committed: 'teal', aborted: 'pink' };
