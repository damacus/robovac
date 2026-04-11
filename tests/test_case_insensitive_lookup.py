import pytest
from custom_components.robovac.case_insensitive_lookup import case_insensitive_lookup

def test_case_insensitive_lookup_not_dict():
    """Test lookup with a non-dictionary."""
    result = case_insensitive_lookup(["not", "a", "dict"], "key")
    assert result is None

def test_case_insensitive_lookup_exact_match():
    """Test lookup with exact match."""
    result = case_insensitive_lookup({"key": "value"}, "key")
    assert result == "value"

def test_case_insensitive_lookup_case_insensitive_match():
    """Test lookup with case insensitive match."""
    result = case_insensitive_lookup({"Key": "value"}, "key")
    assert result == "value"

    result2 = case_insensitive_lookup({"kEy": "value2"}, "KEY")
    assert result2 == "value2"

def test_case_insensitive_lookup_not_found():
    """Test lookup with no match."""
    result = case_insensitive_lookup({"other": "value"}, "key")
    assert result is None
