"""The :class:`NepseClient` entry point.

Example
-------
>>> from nepseapi import NepseClient
>>> with NepseClient() as client:
...     print(client.market_status().is_open)
...     for row in client.prices(131, size=5):
...         print(row.business_date, row.close_price)
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Self, TypeVar

from ._http import DEFAULT_BASE_URL, DEFAULT_USER_AGENT, Transport
from .models import Model, Security
from .resources.companies import CompaniesMixin
from .resources.indices import IndicesMixin
from .resources.info import InfoMixin
from .resources.market import MarketMixin
from .resources.news import NewsMixin
from .resources.securities import SecuritiesMixin

T = TypeVar("T", bound=Model)


class NepseClient(MarketMixin, SecuritiesMixin, CompaniesMixin, IndicesMixin, NewsMixin, InfoMixin):
    """Client for the public nepalstock.com.np API.

    Parameters
    ----------
    base_url:
        Override the host (for example a mirror).
    timeout:
        Per-request timeout in seconds.
    retries:
        Retries for transient network/5xx failures.
    min_interval:
        Minimum seconds between two requests; keeps you polite to the server.
    token_ttl:
        How long a minted anonymous token is considered fresh. The site rotates
        tokens roughly once a minute; lower it if you see 401 storms.
    user_agent:
        User agent sent with every request.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        timeout: float = 30.0,
        retries: int = 3,
        min_interval: float = 0.25,
        token_ttl: float = 55.0,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self._t = Transport(
            base_url,
            timeout=timeout,
            retries=retries,
            min_interval=min_interval,
            token_ttl=token_ttl,
            user_agent=user_agent,
        )

    # ------------------------------------------------------------- plumbing
    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        """Drop the cached token/session id."""

    @property
    def base_url(self) -> str:
        return self._t.base_url

    def _paginate(self, method: Any, *args: Any, start_page: int = 1, max_pages: int | None = None,
                  **kwargs: Any) -> Iterator[T]:
        page_no = start_page
        while True:
            page = method(*args, page=page_no, **kwargs)
            yield from page
            if not page.has_next or (max_pages is not None and page_no - start_page + 1 >= max_pages):
                return
            page_no += 1

    def paginate(self, method: Any, *args: Any, **kwargs: Any) -> Iterator[T]:
        """Iterate every page of a paginated resource method.

        >>> for row in client.paginate(client.prices, 131, size=100):
        ...     ...
        """
        return self._paginate(method, *args, **kwargs)

    # -------------------------------------------------------------- helpers
    def security_by_symbol(self, symbol: str) -> Security | None:
        """Resolve a ticker (``"NABIL"``) to its security record."""
        wanted = symbol.strip().upper()
        for row in self.securities():
            if (row.symbol or "").upper() == wanted:
                return row
        return None

    def security_id(self, symbol_or_id: str | int) -> int:
        """Accept a symbol or a numeric id and always return the id."""
        if isinstance(symbol_or_id, int) or str(symbol_or_id).isdigit():
            return int(symbol_or_id)
        found = self.security_by_symbol(str(symbol_or_id))
        if found is None or found.id is None:
            raise LookupError(f"unknown security symbol: {symbol_or_id!r}")
        return found.id
