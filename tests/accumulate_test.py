from collections import defaultdict

import pytest

from accumulate import accumulate


def gen_classes(attr, *values):
    """ Generate the chain of classes with `attr` set to the successive values in `values` and return the last one.
    """
    base = object
    for value in values:

        class Accumulate(base):
            pass

        setattr(Accumulate, attr, value)
        base = Accumulate
    return Accumulate, attr


@pytest.mark.parametrize(
    "msg,call,expected",
    (
        (
            "it should handle non-accumulating bases",
            lambda sut: gen_classes("x", [1], sut("x", [2])),
            [2, 1],
        ),
        (
            "it should handle multiple accumulations",
            lambda sut: gen_classes("x", sut("x", [1]), sut("x", [2])),
            [2, 1],
        ),
        (
            "it should handle sets",
            lambda sut: gen_classes("x", sut("x", {1}), sut("x", {2}), sut("x", {2})),
            {1, 2},
        ),
        (
            "it should handle dicts",
            lambda sut: gen_classes(
                "x", sut("x", {1: 1}), sut("x", {2: 2}), sut("x", {1: 3})
            ),
            {1: 3, 2: 2},
        ),
        (
            "it should handle defaultdicts",
            lambda sut: gen_classes(
                "x",
                sut("x", defaultdict(dict, {1: 1})),
                sut("x", defaultdict(dict, {2: 2})),
                sut("x", defaultdict(dict, {1: 3})),
            ),
            {1: 3, 2: 2},
        ),
    ),
)
def test_accumulate(msg, call, expected):
    cls, attr = call(accumulate)
    assert getattr(cls, attr) == expected, msg
