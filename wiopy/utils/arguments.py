"""Module with helper functions for managing arguments."""

from __future__ import annotations

__all__ = ("_get_items_ids",)


def _get_items_ids(items: str | list[str]) -> list[str]:
    assert isinstance(items, (str, list)), TypeError(
        "Invalid items argument, it should be a string or List of strings"
    )

    if isinstance(items, str):
        items_ids = items.split(",")
        items_ids = [x.strip() for x in items_ids]

    else:
        items_ids = [x.strip() for x in items]

    return items_ids
