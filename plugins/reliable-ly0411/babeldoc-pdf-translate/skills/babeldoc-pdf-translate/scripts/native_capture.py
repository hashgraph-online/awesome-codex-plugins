"""Bounded answer-file observation before any JSON parsing or size rejection."""
import hashlib
import os
from pathlib import Path


def observe(path,limit):
    if type(limit) is not int or limit<1:raise ValueError('INVALID_CAPTURE_LIMIT')
    path=Path(path)
    metadata={'observed_file_bytes':None,'captured_bytes':0,'complete_capture':False,
        'full_sha256':None,'captured_prefix_sha256':None,'read_error':None}
    raw=b''
    try:
        with path.open('rb') as stream:
            before=os.fstat(stream.fileno());raw=stream.read(limit+1);after=os.fstat(stream.fileno())
        current=path.stat()
        stable=(before.st_size==after.st_size==current.st_size and before.st_mtime_ns==after.st_mtime_ns==current.st_mtime_ns
            and before.st_ino==after.st_ino==current.st_ino)
        metadata.update(observed_file_bytes=after.st_size,
            complete_capture=stable and len(raw)==after.st_size and len(raw)<=limit)
    except OSError as error:
        metadata['read_error']=type(error).__name__
    prefix=raw[:limit]
    metadata.update(captured_bytes=len(prefix),captured_prefix_sha256=hashlib.sha256(prefix).hexdigest())
    if metadata['complete_capture']:metadata['full_sha256']=metadata['captured_prefix_sha256']
    return prefix,metadata
