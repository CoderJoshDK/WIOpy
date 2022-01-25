"""Module with helper functions for managing arguments."""


from .errors import InvalidParameterException
from typing import List, Union


def get_items_ids(items: Union[str, List[str]]) -> str:
    if not isinstance(items, str) and not isinstance(items, List):
        raise InvalidParameterException('Invalid items argument, it should be a string or List of strings')

    if isinstance(items, str):
        items_ids = items.split(',')
        items_ids = [x.strip() for x in items_ids]

    else:
        items_ids = [x.strip() for x in items]

    return items_ids



