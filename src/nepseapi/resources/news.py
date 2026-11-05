"""News, press releases, notices and exchange disclosures."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..models import Model, NewsArticle, Notice, Page, page_from


class NewsMixin:
    def news_and_alerts(self, page: int | None = None, *, size: int = 40) -> list[NewsArticle] | Page[NewsArticle]:
        params = {"page": page - 1, "size": size} if page else {"size": size}
        payload = self._t.request_raw("GET", "/api/nots/news/media/news-and-alerts", params=params)
        return NewsArticle.list_from(payload)

    def press_releases(self, page: int = 1, *, size: int = 20) -> Page[NewsArticle]:
        payload = self._t.request_raw(
            "GET", "/api/nots/news/press-release", params={"page": page - 1, "size": size}
        )
        return page_from(payload, NewsArticle, default_size=size)

    def company_news_feed(self) -> list[NewsArticle]:
        return NewsArticle.list_from(self._t.request_raw("GET", "/api/nots/news/media/company-news"))

    def investor_awareness(self) -> list[NewsArticle]:
        return NewsArticle.list_from(self._t.request_raw("GET", "/api/nots/news/media/investor-awareness"))

    def notices(self, page: int = 1, *, size: int = 20) -> Page[Notice]:
        payload = self._t.request_raw(
            "GET", "/api/nots/news/notice/all", params={"page": page - 1, "size": size}
        )
        return page_from(payload, Notice, default_size=size)

    def iter_notices(self, **kwargs: Any) -> Iterator[Notice]:
        return self._paginate(self.notices, **kwargs)

    def disclosures(self) -> dict[str, list[Model]]:
        """Corporate disclosures + exchange messages shown on the notice board."""
        payload = self._t.request_raw("GET", "/api/nots/news/companies/disclosure") or {}
        return {
            "exchange_messages": Model.list_from(payload.get("exchangeMessages")),
            "corporate_disclosures": Model.list_from(payload.get("corporateDisclosures")),
        }

    def corporate_disclosures(self) -> list[Model]:
        return Model.list_from(self._t.request_raw("GET", "/api/nots/news/companies/disclosure"))
