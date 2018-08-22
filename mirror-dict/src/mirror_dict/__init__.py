""" MirrorDict provides a mapping that returns the key if no value is found.
"""
from collections.abc import Mapping


class MirrorDict(Mapping):
    """ Mapping that returns the key if no value is found.

        >>> snacks = ('cookie', 'biscuit', 'ice cream')
        >>> synonym = MirrorDict(biscuit='cookie')
        >>> sorted(set(synonym[snack] for snack in snacks))
        ['cookie', 'ice cream']
    """

    __slots__ = ("_store",)

    def __init__(self, *args, **kwargs):
        self._store = dict(*args, **kwargs)

    def __getitem__(self, key):
        return self._store.get(key, key)

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def __repr__(self):
        return f"{type(self)}({self._store})"
