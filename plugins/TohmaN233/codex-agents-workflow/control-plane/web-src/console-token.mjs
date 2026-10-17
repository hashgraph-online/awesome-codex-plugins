// The same authenticated tab may reload after its URL fragment is removed.
// Session storage is tab-scoped and does not extend the server token lifetime.
export function consoleToken(location,history,storage){
  const key='caw.console-token:'+location.origin;
  const supplied=new URLSearchParams(location.hash.slice(1)).get('token');
  if(supplied)storage.setItem(key,supplied);
  const token=supplied??storage.getItem(key)??'';
  history.replaceState(null,'',location.pathname);
  return token;
}
