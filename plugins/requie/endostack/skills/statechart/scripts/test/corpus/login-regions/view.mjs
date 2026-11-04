export const title = 'Session and network';
export function state({ auth, net }) {
  return { Account: auth === 'in' ? 'Signed in' : 'Signed out', Network: net === 'online' ? 'Online' : 'Offline' };
}
export function step(action) {
  return { SignIn: 'sign in', SignOut: 'sign out', Drop: 'connection drops', Reconnect: 'connection returns' }[action];
}
