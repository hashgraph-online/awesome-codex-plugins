"""Nonsecret native-client execution identity; never inspect credential storage."""
import hashlib
import os
import re


def effective_identity():
    """Use the OS identity, not inherited USERNAME/USERPROFILE variables."""
    if os.name == 'nt':
        try:
            import ctypes
            get_name = ctypes.WinDLL('secur32', use_last_error=True).GetUserNameExW
            get_name.argtypes = [ctypes.c_int, ctypes.c_wchar_p,
                                 ctypes.POINTER(ctypes.c_ulong)]
            size = ctypes.c_ulong(0)
            get_name(2, None, ctypes.byref(size))  # NameSamCompatible
            if not 0 < size.value <= 32768:
                return None
            buffer = ctypes.create_unicode_buffer(size.value)
            if get_name(2, buffer, ctypes.byref(size)):
                return buffer.value
        except (OSError, AttributeError):
            pass
        return None
    try:
        import pwd
        return pwd.getpwuid(os.geteuid()).pw_name
    except (ImportError, KeyError, OSError):
        return None


def execution_context(binary, env):
    identity = effective_identity()
    inherited = env.get('USERNAME') if os.name == 'nt' else env.get('USER')
    account = identity.rsplit('\\', 1)[-1] if identity else None
    matches = None
    if os.name == 'nt' and account and inherited:
        matches = account.casefold() == inherited.casefold()
    return {'platform': os.name, 'effective_identity': identity,
            'inherited_username': inherited,
            'inherited_username_matches_identity': matches,
            'profile_directory': env.get('USERPROFILE') if os.name == 'nt' else env.get('HOME'),
            'codex_home_override': env.get('CODEX_HOME'), 'selected_cli': str(binary),
            'credential_storage_read': False}


def login_status_error(returncode, stdout, stderr, context):
    """Classify this CLI's official status without generalizing to desktop/cloud."""
    text = (stdout + '\n' + stderr).strip()
    plain = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text).strip()
    if returncode == 0 and re.search(r'^Logged in using ChatGPT\s*$', plain, re.M):
        return None
    detail = {'scope': 'selected_cli_and_process_identity_only',
              'execution_context': context, 'login_status_exit_code': returncode,
              'status_output_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
              'raw_status_output_retained': False,
              'desktop_web_and_cloud_login': 'not_assessed',
              'automatic_login_or_credential_migration': False}
    if returncode != 0 and plain == 'Not logged in':
        if context.get('inherited_username_matches_identity') is False:
            code = 'CODEX_EXECUTION_CONTEXT_MISMATCH'
            detail['next_step'] = ('Use the already authenticated user execution context; '
                                   'do not copy credentials or change authentication settings.')
        else:
            code = 'CODEX_AUTH_UNAVAILABLE_IN_CONTEXT'
            detail['next_step'] = ('Check the selected CLI, process identity and CODEX_HOME '
                                   'against the already authenticated instance; do not infer desktop logout.')
    elif returncode == 0 and re.search(r'^Logged in using an API key\b', plain, re.M):
        code = 'CODEX_AUTH_METHOD_MISMATCH'
        detail['next_step'] = ('This selected provider requires the existing ChatGPT channel; '
                               'do not switch accounts or authentication methods automatically.')
    else:
        code = 'CODEX_LOGIN_STATUS_FAILED' if returncode else 'CODEX_LOGIN_STATUS_UNRECOGNIZED'
        detail['next_step'] = ('Diagnose this CLI status failure separately from login, '
                               'network transport and cloud task access; no automatic login.')
    return code, detail
