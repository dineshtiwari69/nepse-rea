"""Unofficial Python client for public market data on nepalstock.com.np.

>>> from nepseapi import NepseClient
>>> client = NepseClient()
>>> client.market_status().is_open
'CLOSE'
"""

from __future__ import annotations

from .client import NepseClient
from .errors import (
    AuthenticationError,
    BadRequestError,
    ForbiddenError,
    NepseError,
    NotFoundError,
    ParseError,
    RateLimitError,
    ServerError,
    TransportError,
)
from .models import (
    BoardMember,
    Broker,
    Company,
    CorporateAction,
    DailyTrading,
    FloorSheetEntry,
    Holiday,
    Index,
    IndexHistory,
    IndexQuote,
    MarcapRecord,
    MarketStatus,
    MarketSummary,
    Model,
    NewsArticle,
    Notice,
    Page,
    PriceRecord,
    Profile,
    PromoterShare,
    Report,
    ReportType,
    SectorSummary,
    Security,
    SecurityDetail,
    SupplyDemand,
    TopTen,
)

__version__ = "0.1.0"

__all__ = [
    "AuthenticationError",
    "BadRequestError",
    "BoardMember",
    "Broker",
    "Company",
    "CorporateAction",
    "DailyTrading",
    "FloorSheetEntry",
    "ForbiddenError",
    "Holiday",
    "Index",
    "IndexHistory",
    "IndexQuote",
    "MarcapRecord",
    "MarketStatus",
    "MarketSummary",
    "Model",
    "NepseClient",
    "NepseError",
    "NewsArticle",
    "NotFoundError",
    "Notice",
    "Page",
    "ParseError",
    "PriceRecord",
    "Profile",
    "PromoterShare",
    "RateLimitError",
    "Report",
    "ReportType",
    "SectorSummary",
    "Security",
    "SecurityDetail",
    "ServerError",
    "SupplyDemand",
    "TopTen",
    "TransportError",
    "__version__",
]
