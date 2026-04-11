"""Case-insensitive dictionary lookup utilities."""

from typing import Any, Dict, Optional


def case_insensitive_lookup(
    lookup_dict: Dict[str, Any], key: str
) -> Optional[Any]:
    """
    Perform a case-insensitive lookup in a dictionary.

    First attempts an exact match, then falls back to case-insensitive matching.

    Args:
        lookup_dict: Dictionary to search in
        key: Key to look up (will be converted to string)

    Returns:
        The value if found, None otherwise
    """
    str_key = str(key)

    # ⚡ Bolt optimization: Check if lookup_dict is actually a dictionary
    # before attempting to use it. When a list is passed (which happens for some
    # command values), accessing .items() raises an AttributeError which is
    # caught and suppressed by the caller. Catching exceptions on the hot path
    # is slow. Returning early avoids this expensive overhead.
    if not isinstance(lookup_dict, dict):
        return None

    # Try exact match first
    if str_key in lookup_dict:
        return lookup_dict[str_key]

    # Try case-insensitive match
    str_key_lower = str_key.lower()
    for dict_key, value in lookup_dict.items():
        if str(dict_key).lower() == str_key_lower:
            return value

    return None
