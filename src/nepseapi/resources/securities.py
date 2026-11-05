"""Security master data, company detail pages and order books."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..models import (
    BoardMember,
    CorporateAction,
    DailyTrading,
    FloorSheetEntry,
    Model,
    Page,
    PriceRecord,
    Profile,
    PromoterShare,
    Security,
    SecurityDetail,
    page_from,
)


class SecuritiesMixin:
    def securities(self, *, non_delisted: bool = True, non_promoter: bool = False) -> list[Security]:
        """Full tradable security master (symbol, ISIN, listing data...)."""
        params: dict[str, Any] = {}
        if non_promoter:
            params["nonPromoter"] = "true"
        elif non_delisted:
            params["nonDelisted"] = "true"
        return Security.list_from(self._t.request_raw("GET", "/api/nots/security", params=params))

    def securities_lite(self) -> list[Security]:
        """Compact id/symbol list used by the site's own search boxes."""
        return Security.list_from(self._t.request_raw("GET", "/api/nots/securities"))

    def security(self, security_id: int) -> Security | None:
        return Security.from_dict(self._t.request_raw("GET", f"/api/nots/security/{security_id}"))

    def security_card(self, security_id: int) -> Model | None:
        """Combined market-picture payload (``securityData`` + ``securityMcsData``)."""
        return Model.from_dict(
            self._t.request_raw("POST", f"/api/nots/security/{security_id}", json_body={"id": self._t.base_nonce()})
        )

    def security_snapshot(self, security_id: int) -> SecurityDetail | None:
        """Last traded price / open / high / low for one security."""
        return SecurityDetail.from_dict(
            self._t.request_raw("GET", f"/api/nots/security-detail/{security_id}")
        )

    def security_profile(self, security_id: int) -> Profile | None:
        return Profile.from_dict(self._t.request_raw("GET", f"/api/nots/security/profile/{security_id}"))

    def board_of_directors(self, security_id: int) -> list[BoardMember]:
        return BoardMember.list_from(
            self._t.request_raw("GET", f"/api/nots/security/boardOfDirectors/{security_id}")
        )

    def corporate_actions(self, security_id: int) -> list[CorporateAction]:
        return CorporateAction.list_from(
            self._t.request_raw("GET", f"/api/nots/security/corporate-actions/{security_id}")
        )

    def share_groups(self) -> list[Model]:
        return Model.list_from(self._t.request_raw("GET", "/api/nots/security/shareGroup/"))

    def classification(self, page: int = 1, *, share_group: str | None = None,
                       size: int = 20) -> Page[Security]:
        payload = self._t.request_raw(
            "GET", "/api/nots/security/classification",
            params={"page": page - 1, "shareGroup": share_group, "size": size},
        )
        return page_from(payload, Security, default_size=size)

    def promoters(self, page: int = 1, *, size: int = 20) -> Page[PromoterShare]:
        payload = self._t.request_raw(
            "GET", "/api/nots/security/promoters", params={"page": page - 1, "size": size}
        )
        return page_from(payload, PromoterShare, default_size=size)

    # --------------------------------------------------------------- prices
    def prices(self, security_id: int, page: int = 1, *, size: int = 20) -> Page[PriceRecord]:
        payload = self._t.request_raw(
            "GET", f"/api/nots/market/security/price/{security_id}",
            params={"page": page - 1, "size": size},
        )
        return page_from(payload, PriceRecord, default_size=size)

    def iter_prices(self, security_id: int, **kwargs: Any) -> Iterator[PriceRecord]:
        return self._paginate(self.prices, security_id, **kwargs)

    def floorsheet_by_security(
        self, security_id: int, page: int = 1, *, size: int = 20
    ) -> Page[FloorSheetEntry]:
        payload = self._t.request_raw(
            "POST", f"/api/nots/security/floorsheet/{security_id}",
            params={"page": page - 1, "size": size, "sort": "contractId,asc"},
            json_body={"id": self._t.nonce(kind="trade")},
        )
        return page_from(payload, FloorSheetEntry, default_size=size)

    def graphdata(self, security_id: int, *, daily: bool = False) -> list[tuple[int, float]]:
        """Intraday (or daily) ``[timestamp, price]`` chart points."""
        path = f"/api/nots/market/graphdata/{'daily/' if daily else ''}{security_id}"
        payload = self._t.request_raw("POST", path, json_body={"id": self._t.base_nonce()})
        return _points(payload)

    def daily_trading(self, security_id: int) -> list[DailyTrading]:
        """Aggregate rows behind the market-picture chart."""
        payload = self._t.request_raw("POST", f"/api/nots/market/graphdata/daily/{security_id}",
                                      json_body={"id": self._t.base_nonce()})
        return DailyTrading.list_from(payload)

    # ---------------------------------------------------------------- media
    def security_file(self, file_location: str) -> bytes:
        return self._t.request_raw("GET", "/api/nots/security/fetchFiles",
                                   params={"fileLocation": file_location}, raw=True)

    def security_image(self, file_location: str) -> bytes:
        return self._t.request_raw("GET", "/api/nots/security/getImage",
                                   params={"fileLocation": file_location}, raw=True)


def _points(payload: Any) -> list[tuple[int, float]]:
    out: list[tuple[int, float]] = []
    if not isinstance(payload, list):
        return out
    for row in payload:
        if isinstance(row, (list, tuple)) and len(row) >= 2:
            try:
                out.append((int(row[0]), float(row[1])))
            except (TypeError, ValueError):
                continue
        elif isinstance(row, dict):
            ts = row.get("time") or row.get("businessDate")
            val = row.get("value") or row.get("price") or row.get("closingPrice")
            if ts is not None and val is not None:
                out.append((int(ts), float(val)))
    return out
