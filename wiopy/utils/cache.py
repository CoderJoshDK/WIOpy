"""Internal Module for header cache."""
import time
from functools import lru_cache, update_wrapper
from math import floor
from typing import Any, Callable

__all__ = ("_ttl_cache",)


def _ttl_cache(maxsize: int = 10, typed: bool = False, ttl: int = -1):
    if ttl <= 0:
        ttl = 65536

    hash_gen = _ttl_hash_gen(ttl)

    def wrapper(func: Callable) -> Callable:
        @lru_cache(maxsize, typed)
        def ttl_func(ttl_hash, *args, **kwargs):  # noqa: ARG001
            return func(*args, **kwargs)

        def wrapped(*args, **kwargs) -> Any:
            th = next(hash_gen)
            return ttl_func(th, *args, **kwargs)

        return update_wrapper(wrapped, func)

    return wrapper


def _ttl_hash_gen(seconds: int):
    start_time = time.monotonic()

    while True:
        yield floor((time.monotonic() - start_time) // seconds)
