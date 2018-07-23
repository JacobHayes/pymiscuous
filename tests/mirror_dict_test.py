import pytest

from mirror_dict import MirrorDict

@pytest.mark.parametrize('msg,call,expected', [
    (
        'it should hold the set keys',
        lambda sut: sut({1: 10, 2: 20}),
        {'key': 1, 'value': 10},
    ),
    (
        'it should return non-existent keys',
        lambda sut: sut({1: 10, 2: 20}),
        {'key': 3, 'value': 3},
    ),
])
def test_mirror_dict(msg, call, expected):
    assert call(MirrorDict)[expected['key']] == expected['value'], msg
