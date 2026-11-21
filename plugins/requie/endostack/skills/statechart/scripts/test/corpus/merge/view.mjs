export const title = 'Counter, odd values merged';
export function state({ n }) {
  if (n === 0) return 'zero';
  return n % 2 === 0 ? ['even', `n is ${n}`] : 'odd';
}
export function step(action) {
  return action === 'Back' ? 'reset' : 'count';
}
export function group({ n }) {
  return n === 0 ? 'rest' : 'moving';
}
export const colors = { rest: 'blue', moving: 'teal' };
