"""Module for errors that the API might encounter."""

from __future__ import annotations

__all__ = ("InvalidRequestException", "WalmartException")


class WalmartException(Exception):
    """Base Class for Walmart Api Exceptions."""


class InvalidRequestException(WalmartException):
    """Exception thrown if an invalid request response is thrown by Walmart."""

    __slots__: tuple[str, ...] = ()

    def __init__(self, status_code: int, **kwargs: str):  # noqa: D107
        error_message = "Error"
        if status_code == 400:
            error_message = "Bad Request"
            if detail := kwargs.get("detail"):
                error_message = error_message + " - " + str(detail)
        elif status_code == 403:
            error_message = "Forbidden"
        elif status_code == 404:
            error_message = "Wrong endpoint"
        elif status_code == 414:
            error_message = "Request URI too long"
        elif status_code == 500:
            error_message = "Internal Server Error"
        elif status_code == 502:
            error_message = "Bad Gateway"
        elif status_code == 503:
            error_message = "Service Unavailable/ API maintenance"
        elif status_code == 504:
            error_message = "Gateway Timeout"
        message = (
            "[Request failed] Walmart server answered with the following error: "
            f"{error_message:s}. Status code: {status_code:d}"
        )
        super(self.__class__, self).__init__(message)
