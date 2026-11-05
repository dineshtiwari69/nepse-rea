"""Live market, turnover, price and floorsheet endpoints."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..models import (
    DailyTrading,
    FloorSheetEntry,
    MarcapRecord,
    MarketStatus,
    MarketSummary,
    Model,
    Page,
    PriceRecord,
    SectorSummary,
    SummaryHistory,
    SupplyDemand,
    TopTen,
    page_from,
)


class MarketMixin:
    # ------------------------------------------------------------- status
    def market_status(self) -> MarketStatus | None:
        """Current session state (``OPEN``/``CLOSE``/``HALT``) with its session id."""
        return MarketStatus.from_dict(self._t.request_raw("GET", "/api/nots/nepse-data/market-open"))

    def market_summary(self) -> list[MarketSummary]:
        """Today's turnover / volume / transaction totals."""
        return MarketSummary.list_from(self._t.request_raw("GET", "/api/nots/market-summary"))

    def market_summary_history(self) -> list[SummaryHistory]:
        """Daily totals for every stored trading day."""
        return SummaryHistory.list_from(self._t.request_raw("GET", "/api/nots/market-summary-history"))

    def sectors(self) -> list[Model]:
        payload = self._t.request_raw("GET", "/api/nots/sector")
        rows = payload.get("sectors", []) if isinstance(payload, dict) else []
        return Model.list_from(rows)

    def sector_summary(self, business_date: str | None = None) -> list[SectorSummary]:
        return SectorSummary.list_from(
            self._t.request_raw("GET", "/api/nots/sectorwise", params={"businessDate": business_date})
        )

    # --------------------------------------------------------------- depth
    def supply_demand(self, *, all: bool = False) -> dict[str, list[SupplyDemand]]:
        payload = self._t.request_raw("GET", "/api/nots/nepse-data/supplydemand", params={"all": str(all).lower()})
        payload = payload or {}
        return {
            "supply": SupplyDemand.list_from(payload.get("supplyList")),
            "demand": SupplyDemand.list_from(payload.get("demandList")),
        }

    def market_depth(self, security_id: int) -> str | None:
        """Raw order-book snapshot for one security."""
        return self._t.request_raw("GET", f"/api/nots/nepse-data/marketdepth/{security_id}", raw=True).decode() or None

    def market_depth_odd_lot(self, security_id: int) -> str | None:
        return (
            self._t.request_raw("GET", f"/api/nots/nepse-data/marketdepth-ol/{security_id}", raw=True).decode() or None
        )

    # ------------------------------------------------------------- top ten
    def _top(self, kind: str, *, all: bool) -> list[TopTen]:
        payload = self._t.request_raw("GET", f"/api/nots/top-ten/{kind}", params={"all": str(all).lower()})
        return TopTen.list_from(payload)

    def top_turnover(self, *, all: bool = False) -> list[TopTen]:
        return self._top("turnover", all=all)

    def top_trades(self, *, all: bool = False) -> list[TopTen]:
        return self._top("trade", all=all)

    def top_transactions(self, *, all: bool = False) -> list[TopTen]:
        return self._top("transaction", all=all)

    def top_gainers(self, *, all: bool = False) -> list[TopTen]:
        return self._top("top-gainer", all=all)

    def top_losers(self, *, all: bool = False) -> list[TopTen]:
        return self._top("top-loser", all=all)

    # --------------------------------------------------------------- prices
    def today_price(
        self,
        page: int = 1,
        *,
        size: int = 20,
        business_date: str | None = None,
        stock_id: int | None = None,
        sort: str | None = None,
        order: str | None = None,
    ) -> Page[PriceRecord]:
        payload = self._t.request_raw(
            "POST",
            "/api/nots/nepse-data/today-price",
            params={
                "page": page - 1,
                "size": size,
                "businessDate": business_date,
                "stockId": stock_id,
                "sort": sort,
                "sortOrder": order,
            },
            json_body={"id": self._t.nonce(kind="quote")},
        )
        return page_from(payload, PriceRecord, default_size=size)

    def today_price_all(self, business_date: str | None = None) -> list[PriceRecord]:
        """Every price row for a date (no pagination)."""
        payload = self._t.request_raw(
            "POST",
            f"/api/nots/nepse-data/todays-price/{business_date or ''}",
            json_body={"id": self._t.nonce(kind="quote")},
        )
        return PriceRecord.list_from(payload)

    def price_history(
        self, security_id: int, *, start_date: str | None = None, end_date: str | None = None,
        page: int = 1, size: int = 20,
    ) -> Page[DailyTrading]:
        payload = self._t.request_raw(
            "GET",
            f"/api/nots/market/history/security/{security_id}",
            params={"page": page - 1, "size": size, "startDate": start_date, "endDate": end_date},
        )
        return page_from(payload, DailyTrading, default_size=size)

    def iter_price_history(self, security_id: int, **kwargs: Any) -> Iterator[DailyTrading]:
        return self._paginate(self.price_history, security_id, **kwargs)

    def export_price_history(self, security_id: int, *, start_date: str | None = None,
                             end_date: str | None = None) -> str:
        """CSV export of a security's trading history."""
        body = self._t.request_raw(
            "GET",
            f"/api/nots/market/export/{security_id}",
            params={"startDate": start_date, "endDate": end_date},
            raw=True,
        )
        return body.decode("utf-8", "replace")

    # ------------------------------------------------------------ floorsheet
    def floorsheet(
        self,
        page: int = 1,
        *,
        size: int = 20,
        stock_id: int | None = None,
        contract_no: int | None = None,
        buyer: int | None = None,
        seller: int | None = None,
        sort: str = "contractId",
        order: str = "desc",
    ) -> Page[FloorSheetEntry]:
        payload = self._t.request_raw(
            "POST",
            "/api/nots/nepse-data/floorsheet",
            params={
                "page": page - 1,
                "size": size,
                "stockId": stock_id,
                "contractNo": contract_no,
                "buyerBroker": buyer,
                "sellerBroker": seller,
                "sort": f"{sort},{order}",
            },
            json_body={"id": self._t.nonce(kind="trade")},
        )
        page_obj = page_from(payload, FloorSheetEntry, default_size=size)
        return page_obj

    def iter_floorsheet(self, **kwargs: Any) -> Iterator[FloorSheetEntry]:
        return self._paginate(self.floorsheet, **kwargs)

    def floorsheet_totals(self) -> dict[str, float]:
        """Turnover/quantity aggregates returned next to a floorsheet page."""
        payload = self._t.request_raw(
            "POST", "/api/nots/nepse-data/floorsheet",
            params={"page": 0, "size": 1},
            json_body={"id": self._t.nonce(kind="trade")},
        )
        payload = payload or {}
        return {"total_amount": payload.get("totalAmount", 0), "total_quantity": payload.get("totalQty", 0)}

    # ---------------------------------------------------------------- misc
    def live_market(self) -> list[Model]:
        payload = self._t.request_raw("GET", "/api/nots/lives-market")
        return Model.list_from(payload)

    def ticker(self, security_id: int | None = None) -> list[Model]:
        """Per-security ticker; ``58`` is the NEPSE index ticker."""
        payload = self._t.request_raw("GET", f"/api/nots/securityDailyTradeStat/{security_id or 58}")
        return Model.list_from(payload)

    def marcap_by_date(self, page: int = 1, *, size: int = 20) -> Page[MarcapRecord]:
        payload = self._t.request_raw(
            "GET", "/api/nots/nepse-data/marcapbydate/", params={"page": page - 1, "size": size}
        )
        return page_from(payload, MarcapRecord, default_size=size)
