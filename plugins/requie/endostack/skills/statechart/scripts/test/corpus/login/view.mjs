export const title = 'Sign-in';
const names = { form: 'Sign-in form', checking: 'Checking password', home: 'Home page', locked: 'Account locked' };
export function state({ screen }) { return names[screen]; }
export function step(action, from) {
  switch (action) {
    case 'Submit': return 'submit password';
    case 'Accept': return 'password correct';
    case 'Reject': return `password wrong [${from.tries} earlier failures]`;
    case 'Lock': return 'too many failures';
    case 'Logout': return 'sign out';
    default: return action;
  }
}
export function group({ screen }) { return screen === 'home' ? 'signed in' : 'signed out'; }
export const colors = { 'signed in': 'teal', 'signed out': 'yellow' };
