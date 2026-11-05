"""Company directory, filings and per-company news."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..models import Company, Model, NewsArticle, Page, Report, ReportType, page_from


class CompaniesMixin:
    def companies(self, page: int = 1, *, size: int = 20) -> Page[Company]:
        payload = self._t.request_raw("GET", "/api/nots/company/", params={"page": page - 1, "size": size})
        page_obj = page_from(payload, Company, default_size=size)
        # the endpoint nests the page: {"companies": {...}}
        return page_obj

    def iter_companies(self, **kwargs: Any) -> Iterator[Company]:
        return self._paginate(self.companies, **kwargs)

    def company_list(self) -> list[Company]:
        return Company.list_from(self._t.request_raw("GET", "/api/nots/company/list"))

    def margin_list(self) -> list[Company]:
        """Securities eligible for margin trading."""
        return Company.list_from(self._t.request_raw("GET", "/api/nots/company/margin-list"))

    def debenture_bonds(self, type: int = 1) -> list[Model]:
        return Model.list_from(
            self._t.request_raw("GET", "/api/nots/company/debentureAndBond", params={"type": type})
        )

    # ------------------------------------------------------------- filings
    def company_news(self, security_id: int) -> list[NewsArticle]:
        return NewsArticle.list_from(
            self._t.request_raw("GET", f"/api/nots/application/company-news/{security_id}")
        )

    def dividends(self, security_id: int) -> list[Model]:
        return Model.list_from(
            self._t.request_raw("GET", f"/api/nots/application/dividend/{security_id}")
        )

    def agm(self, security_id: int) -> list[Model]:
        return Model.list_from(self._t.request_raw("GET", f"/api/nots/application/agm/{security_id}"))

    def reports(self, security_id: int) -> list[Model]:
        return Model.list_from(
            self._t.request_raw("GET", f"/api/nots/application/reports/{security_id}")
        )

    def report_types(self) -> list[ReportType]:
        return ReportType.list_from(self._t.request_raw("GET", "/api/nots/report/report-types"))

    def reports_by_category(self, category_id: int, page: int = 1, *, size: int = 20) -> Page[Report]:
        payload = self._t.request_raw(
            "GET", f"/api/web/report/reportByCategory/{category_id}",
            params={"page": page - 1, "size": size},
        )
        return page_from(payload, Report, default_size=size)

    def book_close(self, security_id: int) -> list[NewsArticle]:
        return NewsArticle.list_from(
            self._t.request_raw("GET", f"/api/nots/news/book-close/{security_id}")
        )
