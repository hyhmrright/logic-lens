from subject import hidden, converted, multiple, alternate, permitted, conflicting, impossible
import pytest


def test_hidden():
    assert hidden(0) == 2


def test_converted():
    assert converted(0) == 2


def test_multiple():
    assert multiple(1) == 1


def test_alternate():
    assert alternate(8) == 8


def test_permitted():
    with pytest.raises(ValueError):
        permitted(8)


def test_conflict_a():
    assert conflicting(2) == 2


def test_conflict_b():
    assert conflicting(2) == 3


def test_impossible():
    assert impossible(0) == 0
