""" Contains helpers to accumulate iterable class attributes.
"""
from collections import Mapping
from functools import partial
from itertools import chain


class Accumulate:
    """ Implements a descriptor for iterable types that chains the current and parent class values together. Values are
        only retrieved from immediate parents, but this can be used repeatedly at multiple inheritance levels.

        Supports mapping types and returns a mapping with collisions preferring the child-most value. If the mapping is
        ordered, the result will be ordered, but note that collisions will maintain the original position.
    """

    def __init__(self, values):
        self.constructor = type(values)
        # Support constructors with factories, such as defaultdict
        if hasattr(values, "default_factory"):
            self.constructor = partial(self.constructor, values.default_factory)
        self.is_mapping = isinstance(values, Mapping)
        self.name = None
        self.overridden = False
        self.values = values

    def __get__(self, obj, type_):
        if self.overridden:
            return self.values
        if self.name is None:
            self._infer_name(type_)
        collection = (
            iterable
            for iterable in chain(
                [self.values],
                (getattr(base, self.name, None) for base in type_.__bases__),
            )
            if iterable
        )
        if self.is_mapping:
            # Reverse the order of mappings to be parent->leaf to prefer leaf values
            collection = (d.items() for d in reversed(tuple(collection)))
        return self.constructor(chain.from_iterable(collection))

    def __set__(self, obj, values):
        self.values = values
        self.overridden = True

    def __set_name__(self, type_, name):
        """ Set the field name during class initialization on py3.6+. See `_infer_name` for cases where this is not
            called.
        """
        self.name = name

    def _infer_name(self, type_):
        """ Infer a field name for py3.5- or when the descriptor is added with setattr (which won't call __set_name__).
        """
        all_attributes = chain.from_iterable(dir(cls) for cls in type_.__mro__)
        attributes = {attr for attr in all_attributes if not attr.startswith("__")}
        for attr in attributes:
            if type_.__dict__[attr] is self:
                self.name = attr
        if self.name is None:
            raise ValueError("Unable to determine attribute name on {}.".format(type_))


accumulate = Accumulate
