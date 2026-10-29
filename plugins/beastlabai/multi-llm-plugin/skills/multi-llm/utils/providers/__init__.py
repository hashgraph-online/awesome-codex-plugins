"""LLM CLI provider implementations.

``__all__`` is **generated, never hand-maintained** (§9.1). The hand-written
list this replaced had silently lost ``ClaudeCodeProvider`` — the adapter worked
only because ``provider_registry`` imports its module directly — while
``utils/__init__.py``'s copy of the same roster had lost three
(``ClaudeCodeProvider``, ``KiloCodeProvider``, ``MuseProvider``). Neither drift
was detectable: *deleting* an export left the whole suite green, which is what
makes "add one more line" the wrong fix.

So the roster is derived instead: every concrete :class:`LLMProvider` subclass
defined in this package is imported, bound into the package namespace and
exported. ``PROVIDER_CLASSES`` maps class name → class;
``provider_registry._PROVIDERS`` instantiates exactly this set, and
``tests/test_provider_housekeeping.py`` asserts the two agree in **both**
directions, so an adapter added without an export and an export removed without
its adapter are equally red.
"""
import importlib
import inspect
import pkgutil
from typing import Dict, Type

from .base import LLMProvider


def _discover_provider_classes() -> Dict[str, Type[LLMProvider]]:
    """Every concrete ``LLMProvider`` subclass *defined* in this package.

    ``obj.__module__ == module.__name__`` keeps a class to the module that
    defines it, so an adapter importing a sibling adapter cannot re-export it
    under a second name; ``inspect.isabstract`` drops any partial base an
    adapter family might grow later, and ``LLMProvider`` itself is exported
    separately by name.
    """
    found: Dict[str, Type[LLMProvider]] = {}
    for info in pkgutil.iter_modules(__path__):
        if info.ispkg or info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{__name__}.{info.name}")
        for attr, obj in vars(module).items():
            if (
                inspect.isclass(obj)
                and issubclass(obj, LLMProvider)
                and obj is not LLMProvider
                and not inspect.isabstract(obj)
                and obj.__module__ == module.__name__
            ):
                found[attr] = obj
    return found


#: Class name → adapter class, for every adapter this package ships.
PROVIDER_CLASSES: Dict[str, Type[LLMProvider]] = _discover_provider_classes()

# Bind each discovered adapter as a package attribute, so `from utils.providers
# import GrokProvider` keeps working exactly as it did when the imports were
# typed out one per line.
globals().update(PROVIDER_CLASSES)

__all__ = ["LLMProvider", "PROVIDER_CLASSES", *sorted(PROVIDER_CLASSES)]
