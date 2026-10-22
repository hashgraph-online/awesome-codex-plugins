"""Exercise the actual deepest v3 atomic-publication path before paid calls."""
from pathlib import Path
import uuid
import audit_receipts as durable


def preflight(semantic_folder):
    root=Path(semantic_folder).absolute()
    attempt=root/'u0000'/'inbox'/('attempt-'+uuid.uuid4().hex)
    leaf=attempt/'capture.json'
    created=[];ready=False
    value={'passed':False,'deepest_pending_path_characters':len(str(attempt/('.pending-'+('0'*32)))),
        'same_directory_atomic_publish':False,'model_calls':0}
    try:
        missing=[];part=attempt
        while not part.exists():missing.append(part);part=part.parent
        if part.is_symlink() or not part.is_dir():raise ValueError('UNTRUSTED_OUTPUT_DIRECTORY')
        for directory in reversed(missing):directory.mkdir();created.append(directory)
        raw=durable.encode({'filesystem_probe':True})
        durable.publish(leaf,raw);ready=True
        if leaf.read_bytes()!=raw:raise ValueError('ATOMIC_PROBE_BYTES_CHANGED')
        value.update(passed=True,same_directory_atomic_publish=True)
        return value
    except (OSError,ValueError) as error:
        raise ValueError('FINAL_AUDIT_DURABLE_PATH_UNSUPPORTED') from error
    finally:
        # Only known files/directories created by this exclusive probe. No
        # recursive deletion, permission changes, path-prefix bypass or retry.
        if ready:leaf.unlink()
        for directory in reversed(created):directory.rmdir()
