"""Module with helper functions for managing arguments."""


from .errors import InvalidParameterException
from typing import Union


def get_items_ids(items: Union[str, list[str]]) -> list[str]:
    if not isinstance(items, str) and not isinstance(items, list):
        raise InvalidParameterException('Invalid items argument, it should be a string or List of strings')

    if isinstance(items, str):
        items_ids = items.split(',')
        items_ids = [x.strip() for x in items_ids]

    else:
        items_ids = [x.strip() for x in items]

    return items_ids

def is_documented_by(original):
    """Avoid copying the documentation"""

    def wrapper(target):
        target.__doc__ = original.__doc__
        return target

    return wrapper

