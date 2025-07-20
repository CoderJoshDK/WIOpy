"""Internal Module for header cache."""

from __future__ import annotations

import time
from functools import lru_cache, update_wrapper
from math import floor
from typing import Callable, TypeVar

__all__ = ("ttl_cache",)

_C = TypeVar("_C")


def ttl_cache(maxsize: int = 10, typed: bool = False, ttl: int = -1):
    """Generate a TTL cache to be used only for the headers."""
    if ttl <= 0:
        ttl = 65536

    hash_gen = _ttl_hash_gen(ttl)

    def wrapper(func: Callable[[_C], dict[str, str]]) -> Callable[[_C], dict[str, str]]:
        @lru_cache(maxsize, typed)
        def ttl_func(self: _C, _ttl_hash: int):
            return func(self)

        def wrapped(self: _C) -> dict[str, str]:
            th = next(hash_gen)
            return ttl_func(self, th)

        return update_wrapper(wrapped, func)

    return wrapper


def _ttl_hash_gen(seconds: int):
    start_time = time.monotonic()

    while True:
        yield floor((time.monotonic() - start_time) // seconds)
