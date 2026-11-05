"""NEPSE indices: current values, sub-indices and historical graphs."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..models import Index, IndexHistory, IndexQuote, Page, page_from


class IndicesMixin:
    def indices(self) -> list[Index]:
        return Index.list_from(self._t.request_raw("GET", "/api/nots/index"))

    def index_quotes(self) -> list[IndexQuote]:
        """Current value/change for every published index."""
        return IndexQuote.list_from(self._t.request_raw("GET", "/api/nots/nepse-index"))

    def sub_index_quotes(self) -> list[IndexQuote]:
        return IndexQuote.list_from(self._t.request_raw("GET", "/api/nots"))

    def index_history(self, index_id: int = 58, page: int = 1, *, size: int = 20) -> Page[IndexHistory]:
        payload = self._t.request_raw(
            "GET", f"/api/nots/index/history/{index_id}", params={"page": page - 1, "size": size}
        )
        return page_from(payload, IndexHistory, default_size=size)

    def iter_index_history(self, index_id: int = 58, **kwargs: Any) -> Iterator[IndexHistory]:
        return self._paginate(self.index_history, index_id, **kwargs)

    def index_graph(
        self, index_id: int = 58, *, start_date: str | None = None, end_date: str | None = None
    ) -> list[tuple[int, float]]:
        """Intraday graph of an index (``indexCode`` + optional date range)."""
        params = {"indexCode": index_id, "startDate": start_date, "endDate": end_date}
        payload = self._t.request_raw(
            "POST", f"/api/nots/graph/index/{index_id}", params=params,
            json_body={"id": self._t.nonce(kind="index")},
        )
        if not isinstance(payload, list):
            return []
        out: list[tuple[int, float]] = []
        for row in payload:
            if isinstance(row, (list, tuple)) and len(row) >= 2:
                out.append((int(row[0]), float(row[1])))
        return out
