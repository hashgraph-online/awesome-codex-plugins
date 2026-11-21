"""Immutable runtime value-object base."""


class FrozenValue:
    """Value object that rejects attribute changes after construction."""

    __slots__ = ()

    def __setattr__(self, name, value):
        """Set attributes only until the object is frozen."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError("{} is immutable".format(type(self).__name__))
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        """Delete attributes only until the object is frozen."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError("{} is immutable".format(type(self).__name__))
        object.__delattr__(self, name)

    def _freeze(self):
        """Finish construction and make the object immutable."""
        object.__setattr__(self, "_is_frozen", True)
