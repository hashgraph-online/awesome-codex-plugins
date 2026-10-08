const VALID_PROFILES = ['minimal', 'standard', 'strict'];

function getActiveProfile() {
  const raw = (process.env.BOSS_HOOK_PROFILE || 'standard').trim().toLowerCase();
  return VALID_PROFILES.includes(raw) ? raw : 'standard';
}

function getDisabledHooks() {
  const raw = process.env.BOSS_DISABLED_HOOKS || '';
  return raw
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}

function isHookEnabled(hookId, options) {
  var opts = options || {};

  var disabled = getDisabledHooks();
  if (disabled.indexOf(hookId) !== -1) {
    return false;
  }

  var profilesCsv = opts.profiles;
  if (!profilesCsv) {
    return true;
  }

  var allowed = profilesCsv
    .split(',')
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);

  if (allowed.length === 0) {
    return true;
  }

  return allowed.indexOf(getActiveProfile()) !== -1;
}

export { isHookEnabled };
