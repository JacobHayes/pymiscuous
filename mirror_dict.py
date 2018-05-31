""" MirrorDict provides a mapping that returns the key if no value is found.
"""
from collections import Mapping

class MirrorDict(Mapping):
    """ Mapping that returns the key if no value is found.
    """
    def __init__(self, *args, **kwargs):
        self.__dict__.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        return self.__dict__.get(key, key)

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)
