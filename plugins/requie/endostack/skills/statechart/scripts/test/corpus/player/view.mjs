export const title = 'Media player';
const cap = (s) => s[0].toUpperCase() + s.slice(1);
export function state({ playback, panel }) {
  return { Playback: cap(playback), Panel: panel === 'open' ? 'Queue open' : 'Queue closed' };
}
export function step(action) {
  return { Play: 'press play', Pause: 'press pause', Stop: 'press stop', OpenPanel: 'open queue', ClosePanel: 'close queue' }[action];
}
