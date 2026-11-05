"""Exception hierarchy raised by :mod:`nepseapi`."""

from __future__ import annotations


class NepseError(Exception):
    """Base class for every error raised by this library."""

    def __init__(self, message: str, *, status: int | None = None, url: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.url = url


class TransportError(NepseError):
    """Network failure, DNS problem or timeout after all retries."""


class AuthenticationError(NepseError):
    """The anonymous token could not be minted or refreshed."""


class BadRequestError(NepseError):
    """HTTP 400 -- usually a malformed parameter (for example a bad date)."""


class NotFoundError(NepseError):
    """HTTP 404 -- the endpoint or the requested resource does not exist."""


class ForbiddenError(NepseError):
    """HTTP 403 -- WAF rejection or a route that is not publicly reachable."""


class RateLimitError(NepseError):
    """HTTP 429 -- slow down."""


class ServerError(NepseError):
    """HTTP 5xx returned by the NEPSE backend."""


class ParseError(NepseError):
    """The response body was not the JSON/shape the endpoint promises."""
