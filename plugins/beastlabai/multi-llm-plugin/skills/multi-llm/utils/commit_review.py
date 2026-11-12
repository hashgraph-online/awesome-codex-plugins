"""The old name of :mod:`utils.commit_front_door`, kept importable.

``utils.commit_review`` *is* that module (one object in ``sys.modules``), so an
attribute read or a ``monkeypatch`` through either name reaches the same code.
The path layer is :mod:`utils.commit_paths`; new code imports the module that
owns the name.
"""

import sys

from . import commit_front_door

sys.modules[__name__] = commit_front_door
