#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025-2026 Maksim Kochetkov
import os
import sys

if os.name != 'posix' or not all(hasattr(os, name) for name in ('O_NOFOLLOW', 'O_DIRECTORY', 'getuid')):
    print('FAILED: secure history requires POSIX Python 3 (macOS/Linux or WSL); native Windows is unsupported', file=sys.stderr)
    sys.exit(1)
import fcntl
import hashlib
import json
import re
import secrets
import shutil
import stat
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlsplit, parse_qs

LIMIT = 8 * 1024 * 1024
PENDING = b'<!-- brewpage-owner-pending -->\n'
PENDING_ROW = re.compile(rb'<!-- brewpage-owner-pending(?::[a-f0-9]{24})? -->\n?')
OWNER_TOKEN = re.compile(r'[A-Za-z0-9]{32}')
OWNER_ORIGIN = 'https://brewpage.app'
OWNER_PATH = re.compile(r'/api/(html|json|kv|files|sites)/([a-z0-9-]{1,32})/([A-Za-z0-9_-]{1,128})')
READER_PATH = re.compile(r'/([a-z0-9-]{1,32})/([A-Za-z0-9_-]{1,128})')
ROW_KIND = {'html': 'html', 'json': 'json', 'kv': 'kv', 'file': 'files', 'files': 'files', 'site': 'sites', 'sites': 'sites'}
REQUEST_ROW = re.compile(rb'<!-- brewpage-request:(.*) -->\n?')


def regular(directory, name):
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    except FileNotFoundError:
        return None
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
        os.close(fd)
        raise ValueError('unsafe history or ignore file')
    return fd


def same_file(left, right):
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def replace(directory, name, data, mode, exclusive=False):
    temporary = '.brewpage-' + secrets.token_hex(12)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode, dir_fd=directory)
    try:
        with os.fdopen(fd, 'wb') as output:
            os.fchmod(output.fileno(), mode)
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        if exclusive:
            os.link(temporary, name, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
        else:
            os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
    finally:
        try:
            os.unlink(temporary, dir_fd=directory)
        except FileNotFoundError:
            pass


def read(directory, name, private=False):
    fd = regular(directory, name)
    if fd is None:
        return None
    with os.fdopen(fd, 'rb') as source:
        if private and stat.S_IMODE(os.fstat(source.fileno()).st_mode) != 0o600:
            raise ValueError('history must be mode 0600')
        return source.read(LIMIT + 1)


GIT_ENV = ('PATH', 'HOME', 'XDG_CONFIG_HOME', 'GIT_DIR', 'GIT_WORK_TREE', 'GIT_CEILING_DIRECTORIES')


def git(root, arguments, allowed=(0, 1)):
    # Named variables only: repo discovery, PATH and ignore files; nothing else reaches git.
    env = {name: os.environ[name] for name in GIT_ENV if name in os.environ}
    result = subprocess.run(['git', '-C', root] + arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={**env, 'LC_ALL': 'C'})
    if result.returncode not in allowed:
        raise ValueError('Git safety check failed; repair repository configuration before publishing')
    return result


def repository(root):
    if shutil.which('git') is None:
        parent = root
        while True:
            if os.path.lexists(os.path.join(parent, '.git')) or os.environ.get('GIT_DIR'):
                raise ValueError('git required to protect history in a repository')
            ancestor = os.path.dirname(parent)
            if ancestor == parent:
                return False
            parent = ancestor
    result = git(root, ['rev-parse', '--git-dir'], (0, 128))
    if result.returncode == 0:
        return True
    if result.stderr.strip() == b'fatal: not a git repository (or any of the parent directories): .git':
        return False
    raise ValueError('Git repository detection failed; repair repository configuration before publishing')


def lock(directory):
    inherited = os.environ.get('BREWPAGE_HISTORY_LOCK_FD')
    if inherited:
        fd = int(inherited)
        if not same_file(os.fstat(fd), os.fstat(directory)):
            raise ValueError('workspace changed while selecting the owner')
        fcntl.flock(fd, fcntl.LOCK_EX)
    else:
        fcntl.flock(directory, fcntl.LOCK_EX)


def owner_api(value):
    if not isinstance(value, str) or not value.startswith(OWNER_ORIGIN + '/'):
        return None
    return OWNER_PATH.fullmatch(value[len(OWNER_ORIGIN):])


def rows(data):
    for line in data.decode('utf-8').splitlines():
        parts = [value.strip() for value in line.split('|')[1:-1]]
        if len(parts) not in (5, 7):
            continue
        reader = re.fullmatch(r'\[(https://[^\]\s]+)\]\(\1\)', parts[1])
        if reader is None:
            continue
        link = reader[1]
        parsed = urlsplit(link)
        if not parsed.hostname or parsed.username is not None or parsed.fragment or parsed.port not in (None, 443):
            continue
        kind = ROW_KIND.get(parts[4].split(' ', 1)[0])
        api = parts[5] if len(parts) == 7 else ''
        if api:
            match = owner_api(api)
            if match is None:
                continue
            kind, ns, item = match.groups()
            cells = json.loads(parts[6].strip('`')) if parts[6].strip('`') else {}
            if not isinstance(cells, dict) or cells.get('id') not in (None, item) or cells.get('namespace') not in (None, ns):
                raise ValueError('history has a conflicting publication identity')
        else:
            path = READER_PATH.fullmatch(parsed.path) if parsed.netloc == 'brewpage.app' and not parsed.query else None
            if path is not None and kind:
                api = OWNER_ORIGIN + f'/api/{kind}/{path[1]}/{path[2]}'
            elif not (parsed.hostname == 'brewpage.app' or parsed.hostname.endswith('.brewpage.app')):
                api = None
        token = parts[2].strip('`')
        if token:
            yield link, api, token


def external_data(path):
    if not os.path.isabs(path):
        raise ValueError('owner token source must be an absolute path')
    directory = os.open(os.path.dirname(path), os.O_RDONLY | os.O_DIRECTORY)
    try:
        data = read(directory, os.path.basename(path), private=True)
    finally:
        os.close(directory)
    if data is None:
        raise ValueError('owner token file does not exist')
    if len(data) > LIMIT:
        raise ValueError('owner token source exceeds local limit')
    return data


def external_token(path):
    data = external_data(path)
    token = data.decode('ascii').rstrip('\n') if len(data) <= 33 else ''
    if data.lstrip().startswith(b'{'):
        receipt = json.loads(data)
        if not isinstance(receipt, dict) or receipt.get('origin') != OWNER_ORIGIN or not owner_api(receipt.get('ownerApi', '')):
            raise ValueError('recovery receipt must identify an official BrewPage publication')
        token = receipt.get('ownerToken', '')
    if not isinstance(token, str) or not OWNER_TOKEN.fullmatch(token):
        raise ValueError('owner token file must contain one valid BrewPage owner token')
    return token


def select(data, intent, target, source, out):
    if intent == 'anonymous':
        return
    if not source and not target and any(PENDING_ROW.fullmatch(line) for line in data.splitlines(keepends=True)):
        raise ValueError('a previous create needs owner recovery; resolve that receipt before creating again')
    candidates = [(link, api, token) for link, api, token in rows(data) if not target or target in (link, api)]
    if not source and any(api is None for _, api, _ in candidates):
        raise ValueError('saved owner provenance is unresolved; select verified first-party proof before writing')
    tokens = {token for _, _, token in candidates}
    if source:
        token = external_token(source)
    elif len(tokens) > 1:
        raise ValueError('multiple saved owners; select one using its exact saved publication URL')
    elif tokens:
        token, = tokens
    elif target:
        raise ValueError('no saved owner for this target; supply separate proof through a private owner token file')
    else:
        return
    if not OWNER_TOKEN.fullmatch(token):
        raise ValueError('saved owner token is unusable; recover its private proof before sending a write')
    if intent == 'update':
        urls = {api for _, api, _ in candidates if api}
        if owner_api(target) and source:
            urls.add(target)
        if len(urls) != 1:
            raise ValueError('target does not resolve to exactly one official owner API URL')
        print(next(iter(urls)))
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w', encoding='ascii') as header:
        header.write('X-Owner-Token: ' + token + '\n')


def validate_identity(identity, target):
    if not isinstance(identity, dict):
        raise ValueError('owner receipt needs typed publication identity')
    kind, ns, item = target.groups()
    for alias, expected in (('id', item), ('namespace', ns), ('ns', ns), ('kind', kind), ('type', kind)):
        if alias not in identity or identity[alias] is None and alias in ('id', 'namespace', 'type'):
            continue
        value = identity[alias]
        actual = ROW_KIND.get(value) if alias in ('kind', 'type') and isinstance(value, str) else value
        if not isinstance(value, str) or actual != expected:
            raise ValueError('owner receipt has a conflicting publication identity alias')


def validate_receipt(receipt, target):
    validate_identity(receipt, target)
    locations = [receipt]
    result = receipt.get('result')
    if isinstance(result, dict):
        locations.append(result)
        if isinstance(result.get('extras'), dict):
            locations.append(result['extras'])
    for location in locations:
        if 'isOwner' in location and location['isOwner'] is not True:
            raise ValueError('owner receipt has false or invalid ownership confirmation')


def owner_row(target, reader, token, identity):
    api = owner_api(target)
    if api is None or not isinstance(reader, str) or not re.fullmatch(r'https://[^\s\x00-\x20\x7f|`\[\]]+', reader):
        raise ValueError('owner store needs the official target and exact receipt URL')
    kind, ns, item = api.groups()
    if not isinstance(token, str) or not OWNER_TOKEN.fullmatch(token):
        raise ValueError('owner receipt has invalid proof or conflicting target identity')
    validate_identity(identity, api)
    identity = {**identity, 'id': item, 'namespace': ns}
    identity = json.dumps(identity, separators=(',', ':'))
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    return f'| {now} | [{reader}]({reader}) | `{token}` | — | {kind} | {target} | `{identity}` |\n'.encode()


def receipt_row(target, reader, source):
    token = external_token(source)
    identity = {}
    raw = external_data(source)
    if raw.lstrip().startswith(b'{'):
        receipt = json.loads(raw)
        if receipt.get('ownerApi') != target or receipt.get('readerUrl') != reader:
            raise ValueError('recovery receipt does not match the selected publication')
        api = owner_api(target)
        if api is None:
            raise ValueError('owner receipt needs an official target')
        validate_receipt(receipt, api)
        supplied = receipt.get('identity', {})
        validate_identity(supplied, api)
        identity.update(supplied)
        if receipt.get('manageUrl'):
            identity['manageUrl'] = receipt['manageUrl']
    return owner_row(target, reader, token, identity)


def request_binding(value):
    if not isinstance(value, dict) or value.get('method') != 'POST' or value.get('kind') not in ROW_KIND.values() or not isinstance(value.get('endpoint'), str):
        raise ValueError('resolution requires the exact create request binding')
    endpoint = urlsplit(value.get('endpoint', ''))
    if endpoint.scheme != 'https' or endpoint.netloc != 'brewpage.app' or endpoint.fragment or endpoint.path != '/api/' + value['kind'] or parse_qs(endpoint.query).get('ns') != [value.get('namespace')]:
        raise ValueError('request kind, namespace and official endpoint must agree')
    if not isinstance(value.get('namespace'), str) or not isinstance(value.get('payloadSha256'), str) or not re.fullmatch(r'[a-z0-9-]{1,32}', value['namespace']) or not re.fullmatch(r'[a-f0-9]{64}', value['payloadSha256']):
        raise ValueError('request needs a namespace and exact payload fingerprint')
    return value


def pending_entries(data, root):
    requests = {}
    for line in data.splitlines(keepends=True):
        match = REQUEST_ROW.fullmatch(line)
        if match:
            record = json.loads(match[1])
            requests[record['operationId']] = record
    result = []
    for line in data.splitlines(keepends=True):
        if not PENDING_ROW.fullmatch(line):
            continue
        operation = line.decode().strip()[len('<!-- brewpage-owner-pending'): -len(' -->')].lstrip(':')
        operation = operation or 'legacy-' + hashlib.sha256(root.encode()).hexdigest()[:24]
        record = requests.get(operation, {})
        result.append({'operationId': operation, 'request': record.get('request'), 'recordedAt': record.get('recordedAt'), 'localBinding': 'recorded' if record else 'unavailable'})
    return result


def reconciliation(data, root, operation, source, allow_legacy):
    if os.path.basename(source) != 'brewpage-reconciliation.json':
        raise ValueError('private resolution file must be named brewpage-reconciliation.json')
    matches = [row for row in pending_entries(data, root) if row['operationId'] == operation]
    if len(matches) != 1:
        raise ValueError('resolution must identify exactly one pending operation')
    raw = external_data(source)
    value = json.loads(raw)
    if not isinstance(value, dict) or value.get('schema') != 'brewpage-reconciliation-v1' or value.get('operationId') != operation or value.get('outcome') not in ('no-write', 'publication-owned'):
        raise ValueError('resolution needs a supported outcome for this exact operation')
    request = request_binding(value.get('request'))
    local = matches[0]['request']
    if local is not None and request != local:
        raise ValueError('resolution does not match the recorded request')
    if local is not None and allow_legacy:
        raise ValueError('recorded request requires local binding, not external-only resolution')
    if local is None and (allow_legacy != 'external-only' or value.get('binding') != 'external-only'):
        raise ValueError('legacy marker has no local request witness; explicit external-only binding is required')
    evidence = value.get('evidence', {})
    if not isinstance(evidence, dict) or evidence.get('source') != 'owner-verified-first-party' or evidence.get('verifiedByOperator') is not True or not isinstance(evidence.get('reference'), str) or not 1 <= len(evidence['reference'].strip()) <= 1000:
        raise ValueError('resolution requires an explicit verified external finding; helper cannot authenticate it')
    owner = b''
    routing = value.get('routing')
    result_kind = request['kind']
    if routing is not None:
        if routing != 'files-to-html' or request['kind'] != 'files' or value['outcome'] != 'publication-owned':
            raise ValueError('external routing must be the documented files-to-html result')
        result_kind = 'html'
    if value['outcome'] == 'publication-owned':
        receipt = value.get('receipt', {})
        target = owner_api(receipt.get('ownerApi', '')) if isinstance(receipt, dict) else None
        if target is None or receipt.get('origin') != OWNER_ORIGIN or target.group(1) != result_kind or target.group(2) != request['namespace'] or receipt.get('operationId', operation) != operation:
            raise ValueError('external owner receipt does not match the original publication kind and namespace')
        validate_receipt(receipt, target)
        identity = receipt.get('identity', {})
        if not isinstance(identity, dict):
            raise ValueError('external owner receipt needs typed identity')
        identity = {**identity, **({'manageUrl': receipt['manageUrl']} if receipt.get('manageUrl') else {})}
        owner = owner_row(receipt['ownerApi'], receipt.get('readerUrl', ''), receipt.get('ownerToken'), identity)
        if len(list(rows(owner))) != 1:
            raise ValueError('external owner receipt cannot be retained as one verified history row')
    elif value.get('receipt') is not None:
        raise ValueError('a no-write finding cannot carry a publication receipt')
    record = {'operationId': operation, 'outcome': value['outcome'], 'verification': 'external-operator-attestation', 'localRequestBound': local is not None, 'request': request,
              'evidence': {key: evidence[key] for key in ('source', 'verifiedByOperator', 'reference')},
              'resolutionSha256': hashlib.sha256(raw).hexdigest(), 'resolvedAt': datetime.now(timezone.utc).isoformat()}
    if routing is not None:
        record['routing'] = routing
    journal = ('<!-- brewpage-resolution:' + json.dumps(record, separators=(',', ':')) + ' -->\n').encode()
    marker = PENDING if operation.startswith('legacy-') else ('<!-- brewpage-owner-pending:' + operation + ' -->\n').encode()
    prefix = b''.join(line for line in data.splitlines(keepends=True) if line != marker)
    return prefix + journal + owner


def main():
    mode, root, relative, *args = sys.argv[1:]
    if mode not in ('init', 'append', 'lock', 'select', 'pending', 'pending-list', 'reconcile', 'clear', 'store', 'receipt', 'receipt-ready', 'receipt-read') or relative not in ('.claude/brewpage-history.md', 'brewpage-history.md', 'brewpage-recovery.json'):
        raise ValueError('invalid history operation or destination')
    requested_root = os.path.abspath(root)
    if mode.startswith('receipt') and not stat.S_ISDIR(os.lstat(requested_root).st_mode):
        raise ValueError('recovery directory must not be a symlink')
    root = os.path.realpath(root)
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        info = os.fstat(directory)
        if info.st_uid != os.getuid() or info.st_mode & 0o022:
            raise ValueError('workspace must be owned and not writable by others')
        if mode.startswith('receipt'):
            if relative != 'brewpage-recovery.json' or not same_file(os.stat(requested_root, follow_symlinks=False), info):
                raise ValueError('recovery directory must be private')
            external = bool(args and args[0] == '1')
            if external:
                workspace, run = map(os.path.realpath, args[1:])
                if (stat.S_IMODE(info.st_mode) != 0o700 or not same_file(os.fstat(8), info) or
                    any(os.path.commonpath((root, parent)) == parent for parent in (workspace, run)) or repository(root)):
                    raise ValueError('receipt directory requires mode 0700 outside the workspace and Git')
                fcntl.flock(8, fcntl.LOCK_EX | fcntl.LOCK_NB)
            existing = read(directory, relative, private=True)
            if mode == 'receipt-ready':
                if existing or (external and existing is not None):
                    raise ValueError('an owner recovery receipt is pending; retrieve it privately and import it before another saved write')
                if existing is None and not external:
                    replace(directory, relative, b'', 0o600)
                return
            data = existing if mode == 'receipt-read' else sys.stdin.buffer.read(1024 * 1024 + 1)
            if not data:
                raise ValueError('no owner recovery receipt is pending')
            value = json.loads(data)
            if len(data) > 1024 * 1024 or not isinstance(value, dict) or value.get('origin') != OWNER_ORIGIN or not owner_api(value.get('ownerApi')) or not isinstance(value.get('ownerToken'), str) or not OWNER_TOKEN.fullmatch(value['ownerToken']):
                raise ValueError('invalid owner recovery receipt')
            reader = value.get('readerUrl')
            if not isinstance(reader, str) or not re.fullmatch(r'https://[^\s\x00-\x20\x7f#|`]+', reader) or value['ownerToken'] in reader or reader == value.get('manageUrl'):
                raise ValueError('invalid recovery reader URL')
            if mode == 'receipt-read':
                print(json.dumps({'ownerApi': value['ownerApi'], 'readerUrl': reader}, separators=(',', ':')))
                return
            if existing or (external and existing is not None):
                raise ValueError('an unresolved owner recovery receipt must not be overwritten')
            replace(directory, relative, data, 0o600, exclusive=external)
            if not same_file(os.stat(requested_root, follow_symlinks=False), os.fstat(directory)) or read(directory, relative, private=True) != data:
                raise ValueError('recovery receipt readback failed')
            return
        lock(directory)
        if mode == 'lock':
            return
        if mode == 'select':
            intent, target, source, _ = args
            if intent == 'anonymous' or source and (intent == 'create' or owner_api(target)):
                select(b'', *args)
                return
        parts = relative.split('/')
        parent = directory
        for part in parts[:-1]:
            if mode not in ('select', 'pending-list'):
                try:
                    os.mkdir(part, 0o700, dir_fd=parent)
                except FileExistsError:
                    pass
            try:
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            except FileNotFoundError:
                if mode == 'pending-list':
                    print('{"pending":[]}')
                    return
                if mode != 'select':
                    raise
                select(b'', *args)
                return
            info = os.fstat(next_fd)
            if info.st_uid != os.getuid() or info.st_mode & 0o022:
                os.close(next_fd)
                raise ValueError('history directory must be owned and not writable by others')
            if parent != directory:
                os.close(parent)
            parent = next_fd
        try:
            if mode == 'select':
                select(read(parent, parts[-1], private=True) or b'', *args)
                return
            data = read(parent, parts[-1], private=(mode != 'init'))
            if data is not None and len(data) > LIMIT:
                raise ValueError('history exceeds local 8 MiB limit')
            if mode == 'pending-list':
                pending = pending_entries(data or b'', root)
                fallback = read(parent, 'brewpage-recovery.json', private=True)
                receipt = json.loads(fallback) if fallback else {}
                if not isinstance(receipt, dict):
                    raise ValueError('invalid protected recovery receipt')
                for row in pending:
                    row['receiptAvailable'] = receipt.get('operationId') == row['operationId']
                print(json.dumps({'pending': pending}, separators=(',', ':')))
                return
            git_repo = repository(root)
            recovery_relative = '/'.join(parts[:-1] + ['brewpage-recovery.json'])
            if git_repo:
                tracked = git(root, ['ls-files', '--error-unmatch', '--', relative])
                if tracked.returncode == 0:
                    raise ValueError('history is tracked by git; remove it from the index before publishing')
                if git(root, ['ls-files', '--error-unmatch', '--', recovery_relative]).returncode == 0:
                    raise ValueError('recovery receipt is tracked by git; remove it from the index before publishing')
            ignore = read(directory, '.gitignore')
            if ignore is not None and len(ignore) > LIMIT:
                raise ValueError('ignore file exceeds local 8 MiB limit')
            if git_repo or ignore is not None:
                ignore = ignore or b''
                for protected in (relative, recovery_relative, 'brewpage-reconciliation.json'):
                    entry = protected.encode()
                    ignored = git_repo and git(root, ['check-ignore', '--no-index', '--quiet', '--', protected]).returncode == 0
                    if entry not in ignore.splitlines() or (git_repo and not ignored):
                        ignore += (b'\n' if ignore and not ignore.endswith(b'\n') else b'') + entry + b'\n'
                        replace(directory, '.gitignore', ignore, 0o644)
                    if git_repo and git(root, ['check-ignore', '--no-index', '--quiet', '--', protected]).returncode != 0:
                        raise ValueError('owner records are not effectively ignored by git; resolve nested ignore overrides before publishing')
            if data and not data.endswith(b'\n'):
                data += b'\n'
            incoming_store = receipt_row(*args) if mode == 'store' else None
            operation = os.environ.get('BREWPAGE_OPERATION_ID', '')
            if mode == 'store':
                operation = ''
                if os.path.realpath(args[2]) == os.path.join(root, *parts[:-1], 'brewpage-recovery.json'):
                    restored = json.loads(external_data(args[2]))
                    operation = restored.get('operationId', '')
                    if not isinstance(operation, str):
                        raise ValueError('local receipt has an invalid operation reference')
                    pending = [row for row in pending_entries(data or b'', root) if row['operationId'] == operation]
                    if len(pending) > 1:
                        raise ValueError('local receipt must identify exactly one pending operation')
                    request = pending[0]['request'] if pending else None
                    target = owner_api(args[0])
                    if request is not None and (target.group(2) != request['namespace'] or target.group(1) != request['kind'] and (request['kind'], target.group(1)) != ('files', 'html')):
                        raise ValueError('local receipt does not match the pending request kind and namespace')
            marker = ('<!-- brewpage-owner-pending:' + operation + ' -->\n').encode() if re.fullmatch(r'[a-f0-9]{24}', operation) else None
            if mode == 'pending':
                if marker is None or any(PENDING_ROW.fullmatch(line) for line in (data or b'').splitlines(keepends=True)):
                    raise ValueError('a previous create needs owner recovery; resolve that receipt before creating again')
                record = json.loads(sys.stdin.buffer.read(1024 * 1024))
                if record.get('operationId') != operation:
                    raise ValueError('request fingerprint does not identify the pending operation')
                request_binding(record.get('request'))
                updated = (data or b'') + ('<!-- brewpage-request:' + json.dumps(record, separators=(',', ':')) + ' -->\n').encode() + marker
            elif mode == 'reconcile':
                selected = os.path.relpath(os.path.realpath(args[1]), root)
                if git_repo and not selected.startswith('../') and (git(root, ['ls-files', '--error-unmatch', '--', selected]).returncode == 0 or git(root, ['check-ignore', '--no-index', '--quiet', '--', selected]).returncode != 0):
                    raise ValueError('selected private resolution must be untracked and effectively ignored by Git')
                fallback = read(parent, 'brewpage-recovery.json', private=True)
                received = json.loads(fallback) if fallback else {}
                if not isinstance(received, dict):
                    raise ValueError('invalid protected recovery receipt')
                if received.get('operationId') == args[0]:
                    raise ValueError('a local receipt is available; use owner-recovery and owner-store instead')
                updated = reconciliation(data or b'', root, *args)
            elif mode == 'clear':
                if marker is None:
                    raise ValueError('pending reconciliation requires the matching operation')
                updated = b''.join(line for line in (data or b'').splitlines(keepends=True) if line != marker)
            else:
                incoming = incoming_store if mode == 'store' else sys.stdin.buffer.read(1024 * 1024 + 1)
                if len(incoming) > 1024 * 1024:
                    raise ValueError('history row exceeds local limit')
                if mode == 'init':
                    updated = data if data is not None else incoming
                else:
                    if mode == 'store' or args == ['verify-owner']:
                        recovered = list(rows(incoming))
                        if len(recovered) != 1 or not OWNER_TOKEN.fullmatch(recovered[0][2]):
                            raise ValueError('receipt did not identify an official publication and reusable owner token')
                    prefix = b''.join(line for line in (data or b'').splitlines(keepends=True) if marker is None or line != marker)
                    updated = prefix + incoming
            if len(updated) > LIMIT:
                raise ValueError('history exceeds local 8 MiB limit')
            replace(parent, parts[-1], updated, 0o600)
            if not same_file(os.stat(root, follow_symlinks=False), os.fstat(directory)):
                raise ValueError('workspace moved while writing history')
            if len(parts) > 1 and not same_file(os.stat(parts[0], dir_fd=directory, follow_symlinks=False), os.fstat(parent)):
                raise ValueError('history directory moved while writing history')
            if read(parent, parts[-1], private=True) != updated:
                raise ValueError('history readback did not match the saved data')
            if mode == 'store' and os.path.realpath(args[2]) == os.path.join(root, *parts[:-1], 'brewpage-recovery.json'):
                os.unlink('brewpage-recovery.json', dir_fd=parent)
        finally:
            if parent != directory:
                os.close(parent)
    finally:
        os.close(directory)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as error:
        print('FAILED: secure history write refused (' + str(error).split(':')[0] + ')', file=sys.stderr)
        sys.exit(1)
