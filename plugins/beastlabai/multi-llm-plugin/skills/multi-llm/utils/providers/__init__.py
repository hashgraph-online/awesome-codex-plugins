"""LLM CLI provider implementations.

The adapter roster is **derived, never hand-maintained**: every concrete
:class:`LLMProvider` subclass defined in this package is imported, bound into
the package namespace and exported. ``PROVIDER_CLASSES`` maps class name →
class, and ``provider_registry._PROVIDERS`` is built from it (one instance per
class, keyed by provider name), so dropping a module in this directory registers
it and deleting one unregisters it. ``tests/test_provider_housekeeping.py``
asserts the exports and the registry agree in both directions. The tables that must stay hand-kept (measured
config rows, fixtures, docs) are compared with the registry by the roster tests;
the order to fill them in is docs/development/providers.md#adding-a-provider-adapter.
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

    Two modules defining classes with one name refuse to load. The result and
    the package exports are keyed by class name, so the later class would
    otherwise replace the earlier one before the registry's provider-name check
    could see both (docs/development/providers.md#adding-a-provider-adapter).
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
                taken = found.get(attr)
                if taken is not None:
                    raise RuntimeError(
                        f"two adapter classes are named {attr!r}: "
                        f"{taken.__module__}.{taken.__qualname__} and "
                        f"{obj.__module__}.{obj.__qualname__}. Adapters are "
                        f"registered and exported by class name, so rename one "
                        f"(docs/development/providers.md#adding-a-provider-adapter)."
                    )
                found[attr] = obj
    return found


#: Class name → adapter class, for every adapter this package ships.
PROVIDER_CLASSES: Dict[str, Type[LLMProvider]] = _discover_provider_classes()

# Bind each discovered adapter as a package attribute, so `from utils.providers
# import GrokProvider` keeps working exactly as it did when the imports were
# typed out one per line.
globals().update(PROVIDER_CLASSES)

__all__ = ["LLMProvider", "PROVIDER_CLASSES"]
__all__.extend(sorted(PROVIDER_CLASSES))
