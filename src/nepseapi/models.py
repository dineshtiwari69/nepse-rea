"""Typed views over the payloads returned by the NEPSE API.

Every model keeps the untouched payload in :attr:`Model.raw` so that callers can
reach fields that are not (yet) modelled explicitly.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar


@dataclass
class Model:
    """Base class that tolerates unknown/extra server fields."""

    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any] | None):
        if payload is None:
            return None
        known = {f.name for f in dataclasses.fields(cls)} - {"raw"}
        kwargs = {k: payload[k] for k in known if k in payload}
        return cls(**kwargs, raw=payload)  # type: ignore[arg-type]

    @classmethod
    def list_from(cls, payload: Any) -> list:
        if not isinstance(payload, list):
            return []
        return [item for item in (cls.from_dict(p) for p in payload) if item is not None]

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw.get(key, default)


M = TypeVar("M", bound=Model)


@dataclass
class Page(Generic[M]):
    """One page of a Spring ``Page`` response."""

    items: list[M]
    page: int
    size: int
    total_elements: int
    total_pages: int
    extra: Mapping[str, Any] = field(default_factory=dict, repr=False)

    def __iter__(self) -> Iterator[M]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> M:
        return self.items[index]

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages


def page_from(payload: Any, model: type[M], *, default_size: int = 20) -> Page[M]:
    """Build a :class:`Page` from the various shapes the API uses.

    Some endpoints nest the Spring page one level deep (``{"floorsheets": {...}}``),
    so the first mapping containing a ``content`` list wins.
    """
    holder: Mapping[str, Any] = {}
    if isinstance(payload, Mapping):
        if "content" in payload:
            holder = payload
        else:
            for value in payload.values():
                if isinstance(value, Mapping) and "content" in value:
                    holder = value
                    break
        extra = {k: v for k, v in payload.items() if k not in (holder,) and k != "content"}
    else:
        extra = {}

    content = holder.get("content") or []
    if content and isinstance(content[0], list):  # press releases nest one list per row
        content = [cell for row in content for cell in row]
    items = model.list_from(content)
    return Page(
        items=items,
        page=int(holder.get("number", 0)) + 1,
        size=int(holder.get("size", default_size)),
        total_elements=int(holder.get("totalElements", len(items))),
        total_pages=int(holder.get("totalPages", 0)),
        extra=extra,
    )


# --------------------------------------------------------------------- market
@dataclass
class MarketStatus(Model):
    id: int | None = None
    is_open: str | None = None
    as_of: str | None = None

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(id=payload.get("id"), is_open=payload.get("isOpen"), as_of=payload.get("asOf"), raw=payload)

    @property
    def open(self) -> bool:
        return (self.is_open or "").upper() == "OPEN"


@dataclass
class MarketSummary(Model):
    detail: str | None = None
    value: float | None = None


@dataclass
class SummaryHistory(Model):
    business_date: str | None = None
    total_turnover: float | None = None
    total_traded_shares: int | None = None
    total_transactions: int | None = None

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            business_date=payload.get("businessDate"),
            total_turnover=payload.get("totalTurnover"),
            total_traded_shares=payload.get("totalTradedShares"),
            total_transactions=payload.get("totalTransactions"),
            raw=payload,
        )


@dataclass
class IndexQuote(Model):
    id: int | None = None
    index: str | None = None
    close: float | None = None
    high: float | None = None
    low: float | None = None
    change: float | None = None
    per_change: float | None = None
    current_value: float | None = None
    generated_time: str | None = None

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            id=payload.get("id"),
            index=payload.get("index"),
            close=payload.get("close"),
            high=payload.get("high"),
            low=payload.get("low"),
            change=payload.get("change"),
            per_change=payload.get("perChange"),
            current_value=payload.get("currentValue"),
            generated_time=payload.get("generatedTime"),
            raw=payload,
        )

    @property
    def symbol(self) -> str | None:
        return self.index


@dataclass
class TopTen(Model):
    symbol: str | None = None
    security_id: int | None = None
    security_name: str | None = None
    turnover: float | None = None
    share_traded: int | None = None
    total_trades: int | None = None
    ltp: float | None = None
    cp: float | None = None
    point_change: float | None = None
    percentage_change: float | None = None

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            symbol=payload.get("symbol"),
            security_id=payload.get("securityId"),
            security_name=payload.get("securityName"),
            turnover=payload.get("turnover"),
            share_traded=payload.get("shareTraded"),
            total_trades=payload.get("totalTrades"),
            ltp=payload.get("ltp"),
            cp=payload.get("cp"),
            point_change=payload.get("pointChange"),
            percentage_change=payload.get("percentageChange"),
            raw=payload,
        )


@dataclass
class SectorSummary(Model):
    sector_name: str | None = None
    business_date: str | None = None
    turnover: float | None = None
    volume: int | None = None
    transactions: int | None = None

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            sector_name=payload.get("sectorName"),
            business_date=payload.get("businessDate"),
            turnover=payload.get("turnOverValues"),
            volume=payload.get("turnOverVolume"),
            transactions=payload.get("totalTransactions"),
            raw=payload,
        )


@dataclass
class FloorSheetEntry(Model):
    contract_id: int | None = None
    stock_symbol: str | None = None
    stock_id: int | None = None
    buyer_member_id: str | None = None
    seller_member_id: str | None = None
    contract_quantity: int | None = None
    contract_rate: float | None = None
    contract_amount: float | None = None
    business_date: str | None = None

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            contract_id=payload.get("contractId"),
            stock_symbol=payload.get("stockSymbol"),
            stock_id=payload.get("stockId"),
            buyer_member_id=payload.get("buyerMemberId"),
            seller_member_id=payload.get("sellerMemberId"),
            contract_quantity=payload.get("contractQuantity"),
            contract_rate=payload.get("contractRate"),
            contract_amount=payload.get("contractAmount"),
            business_date=payload.get("businessDate"),
            raw=payload,
        )


# ----------------------------------------------------------------- securities
@dataclass
class Security(Model):
    id: int | None = None
    symbol: str | None = None
    security_name: str | None = None
    name: str | None = None
    isin: str | None = None
    active_status: str | None = None
    listing_date: str | None = None
    permitted_to_trade: str | None = None

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            id=payload.get("id") or payload.get("securityId"),
            symbol=payload.get("symbol") or payload.get("securitySymbol"),
            security_name=payload.get("securityName"),
            name=payload.get("name"),
            isin=payload.get("isin"),
            active_status=payload.get("activeStatus"),
            listing_date=payload.get("listingDate"),
            permitted_to_trade=payload.get("permittedToTrade"),
            raw=payload,
        )

    @property
    def label(self) -> str:
        return self.name or f"({self.symbol}) {self.security_name}" if self.symbol else (self.security_name or "")


@dataclass
class PriceRecord(Model):
    id: int | None = None
    business_date: str | None = None
    open_price: float | None = None
    high_price: float | None = None
    low_price: float | None = None
    close_price: float | None = None
    previous_day_close_price: float | None = None
    total_traded_quantity: int | None = None
    total_traded_value: float | None = None
    total_trades: int | None = None
    security: Security | None = None

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            id=payload.get("id"),
            business_date=payload.get("businessDate"),
            open_price=payload.get("openPrice"),
            high_price=payload.get("highPrice"),
            low_price=payload.get("lowPrice"),
            close_price=payload.get("closePrice"),
            previous_day_close_price=payload.get("previousDayClosePrice"),
            total_traded_quantity=payload.get("totalTradedQuantity"),
            total_traded_value=payload.get("totalTradedValue"),
            total_trades=payload.get("totalTrades"),
            security=Security.from_dict(payload.get("security")),
            raw=payload,
        )


@dataclass
class DailyTrading(Model):
    business_date: str | None = None
    total_trades: int | None = None
    total_traded_quantity: int | None = None
    total_traded_value: float | None = None
    high_price: float | None = None
    low_price: float | None = None
    close_price: float | None = None

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            business_date=payload.get("businessDate"),
            total_trades=payload.get("totalTrades"),
            total_traded_quantity=payload.get("totalTradedQuantity"),
            total_traded_value=payload.get("totalTradedValue"),
            high_price=payload.get("highPrice"),
            low_price=payload.get("lowPrice"),
            close_price=payload.get("closePrice"),
            raw=payload,
        )


@dataclass
class SecurityDetail(Model):
    security_id: int | None = None
    received_date_time: str | None = None
    last_traded_price: float | None = None
    open_price: float | None = None
    high_price: float | None = None
    low_price: float | None = None

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            security_id=payload.get("securityId"),
            received_date_time=payload.get("receivedDateTime"),
            last_traded_price=payload.get("lastTradedPrice"),
            open_price=payload.get("openPrice"),
            high_price=payload.get("highPrice"),
            low_price=payload.get("lowPrice"),
            raw=payload,
        )


@dataclass
class Profile(Model):
    company_name: str | None = None
    company_email: str | None = None
    company_contact_person: str | None = None
    company_profile: str | None = None
    logo_file_path: str | None = None
    company_website: str | None = None
    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            company_name=payload.get("companyName"),
            company_email=payload.get("companyEmail"),
            company_contact_person=payload.get("companyContactPerson"),
            company_profile=payload.get("companyProfile"),
            logo_file_path=payload.get("logoFilePath"),
            company_website=payload.get("companyWebSite") or payload.get("companyWebsite"),
            raw=payload,
        )



@dataclass
class BoardMember(Model):
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    designation: str | None = None
    member_photo_path: str | None = None
    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            first_name=payload.get("firstName"),
            middle_name=payload.get("middleName"),
            last_name=payload.get("lastName"),
            designation=payload.get("designation"),
            member_photo_path=payload.get("memberPhotoPath"),
            raw=payload,
        )



@dataclass
class CorporateAction(Model):
    active_status: str | None = None
    submitted_date: str | None = None
    authorization_comments: str | None = None
    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            active_status=payload.get("activeStatus"),
            submitted_date=payload.get("submittedDate"),
            authorization_comments=payload.get("authorizationComments"),
            raw=payload,
        )



@dataclass
class Company(Model):
    id: int | None = None
    company_name: str | None = None
    company_short_name: str | None = None
    symbol: str | None = None
    security_name: str | None = None
    email: str | None = None
    company_website: str | None = None
    status: str | None = None
    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            id=payload.get("id"),
            company_name=payload.get("companyName"),
            company_short_name=payload.get("companyShortName"),
            symbol=payload.get("symbol"),
            security_name=payload.get("securityName"),
            email=payload.get("email"),
            company_website=payload.get("companyWebsite") or payload.get("companyWebSite"),
            status=payload.get("status"),
            raw=payload,
        )



@dataclass
class PromoterShare(Model):
    id: int | None = None
    symbol: str | None = None
    isin: str | None = None
    listing_date: str | None = None
    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            id=payload.get("id"),
            symbol=payload.get("symbol"),
            isin=payload.get("isin"),
            listing_date=payload.get("listingDate"),
            raw=payload,
        )



# --------------------------------------------------------------------- content
@dataclass
class Notice(Model):
    id: int | None = None
    notice_heading: str | None = None
    notice_body: str | None = None
    published_date: str | None = None

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            id=payload.get("id"),
            notice_heading=payload.get("noticeHeading"),
            notice_body=payload.get("noticeBody"),
            published_date=payload.get("publishedDate"),
            raw=payload,
        )


@dataclass
class NewsArticle(Model):
    id: int | None = None
    headline: str | None = None
    body: str | None = None
    published_date: str | None = None
    source: str | None = None
    file_path: str | None = None

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            id=payload.get("id"),
            headline=payload.get("newsHeadline") or payload.get("noticeHeading") or payload.get("title"),
            body=payload.get("messageBody") or payload.get("newsBody") or payload.get("noticeBody"),
            published_date=payload.get("publishedDate") or payload.get("addedDate"),
            source=payload.get("newsSource") or payload.get("sources"),
            file_path=payload.get("noticeFilePath") or payload.get("filePath"),
            raw=payload,
        )


@dataclass
class Holiday(Model):
    holiday_date: str | None = None
    description: str | None = None

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            holiday_date=payload.get("holidayDate"),
            description=payload.get("holidayDescription"),
            raw=payload,
        )


@dataclass
class Broker(Model):
    id: int | None = None
    member_code: int | None = None
    member_name: str | None = None
    active_status: str | None = None
    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            id=payload.get("id"),
            member_code=payload.get("memberCode"),
            member_name=payload.get("memberName"),
            active_status=payload.get("activeStatus"),
            raw=payload,
        )



@dataclass
class Index(Model):
    id: int | None = None
    index_code: str | None = None
    index_name: str | None = None
    description: str | None = None
    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            id=payload.get("id"),
            index_code=payload.get("indexCode"),
            index_name=payload.get("indexName") or payload.get("index"),
            description=payload.get("description"),
            raw=payload,
        )



@dataclass
class IndexHistory(Model):
    id: int | None = None
    business_date: str | None = None
    closing_index: float | None = None
    open_index: float | None = None
    high_index: float | None = None
    low_index: float | None = None

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            id=payload.get("id"),
            business_date=payload.get("businessDate"),
            closing_index=payload.get("closingIndex"),
            open_index=payload.get("openIndex"),
            high_index=payload.get("highIndex"),
            low_index=payload.get("lowIndex"),
            raw=payload,
        )


@dataclass
class ReportType(Model):
    id: int | None = None
    type_name: str | None = None
    description: str | None = None
    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            id=payload.get("id"),
            type_name=payload.get("typeName"),
            description=payload.get("description"),
            raw=payload,
        )



@dataclass
class Report(Model):
    id: int | None = None
    filename: str | None = None
    report_type: ReportType | None = None

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(id=payload.get("id"), filename=payload.get("filename"),
                   report_type=ReportType.from_dict(payload.get("reportType")), raw=payload)


@dataclass
class SupplyDemand(Model):
    symbol: str | None = None
    security_id: int | None = None
    security_name: str | None = None
    total_quantity: int | None = None
    total_order: int | None = None

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            symbol=payload.get("symbol"),
            security_id=payload.get("securityId"),
            security_name=payload.get("securityName"),
            total_quantity=payload.get("totalQuantity"),
            total_order=payload.get("totalOrder"),
            raw=payload,
        )


@dataclass
class MarcapRecord(Model):
    business_date: str | None = None
    marcap: float | None = None
    sen_marcap: float | None = None
    float_marcap: float | None = None
    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            business_date=payload.get("businessDate"),
            marcap=payload.get("marcap"),
            sen_marcap=payload.get("senMarcap"),
            float_marcap=payload.get("floatMarcap"),
            raw=payload,
        )



@dataclass
class MenuItem(Model):
    nepali_name: str | None = None
    url: str | None = None
    external_link: bool | None = None
    children: list[MenuItem] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload):  # type: ignore[override]
        if not payload:
            return None
        return cls(
            nepali_name=payload.get("nepaliName"),
            url=payload.get("url"),
            external_link=payload.get("externalLink"),
            children=cls.list_from(payload.get("secondaryMenu") or []),
            raw=payload,
        )
