"""Tests that prove the harness can repair a real failing project."""

from calc import add, multiply


def test_add_positive_numbers():
    assert add(2, 3) == 5


def test_add_negative_numbers():
    assert add(-2, -3) == -5


def test_multiply_numbers():
    assert multiply(4, 5) == 20
