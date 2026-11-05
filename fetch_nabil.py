"""Fetch NABIL's price and related company data.

Run from the repository root:

    python fetch_nabil.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from nepseapi import NepseClient

SYMBOL = "NABIL"
_TAG = re.compile(r"<[^>]+>")


def plain(value: object, limit: int = 320) -> str:
    text = _TAG.sub(" ", "" if value is None else str(value))
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def member_name(person) -> str:
    parts = [person.first_name, person.middle_name, person.last_name]
    return " ".join(part.strip() for part in parts if part and part.strip())


def nested_security(records) -> dict:
    for item in records:
        security = (item.get("companyNews") or {}).get("security") or {}
        if security:
            return security
    return {}


def main() -> None:
    with NepseClient(min_interval=0.3) as client:
        security = client.security_by_symbol(SYMBOL)
        if security is None or security.id is None:
            raise SystemExit(f"unknown symbol: {SYMBOL}")

        sid = security.id
        listed = client.security(sid) or security
        snapshot = client.security_snapshot(sid)
        history = client.prices(sid, size=5)
        profile = client.security_profile(sid)
        board = client.board_of_directors(sid)
        dividends = client.dividends(sid)
        news = client.company_news(sid)
        meetings = client.agm(sid)
        trades = client.floorsheet(stock_id=sid, size=5)

    detail = nested_security([item.raw for item in (*dividends, *news, *meetings)])
    company = detail.get("companyId") or {}
    sector = (company.get("sectorMaster") or {}).get("sectorDescription")
    share_group = (detail.get("shareGroupId") or {}).get("name")
    website = (profile.company_website if profile else None) or company.get("companyWebsite")

    name = listed.security_name or listed.name or security.security_name or SYMBOL
    print(f"{listed.symbol or SYMBOL}  {name}")
    print(
        f"id={sid}  isin={listed.isin or detail.get('isin') or '-'}  "
        f"listed={listed.listing_date or detail.get('listingDate') or '-'}"
    )
    print(
        f"sector={sector or '-'}  group={share_group or '-'}  "
        f"face value={detail.get('faceValue', '-')}"
    )

    if snapshot is None:
        print("price: unavailable")
    else:
        print(
            f"LTP={snapshot.last_traded_price}  open={snapshot.open_price}  "
            f"high={snapshot.high_price}  low={snapshot.low_price}"
        )
        print(f"as of {snapshot.received_date_time or '-'}")

    print("\nrecent closes")
    for row in history:
        print(
            f"  {row.business_date}  close={row.close_price}  "
            f"high={row.high_price}  low={row.low_price}  qty={row.total_traded_quantity}"
        )

    print("\ncompany")
    if profile is None:
        print("  profile unavailable")
    else:
        print(f"  name: {profile.company_name or company.get('companyName') or '-'}")
        print(f"  email: {profile.company_email or company.get('email') or '-'}")
        print(f"  website: {website or '-'}")
        print(f"  contact: {profile.company_contact_person or company.get('companyContactPerson') or '-'}")
        about = plain(profile.company_profile)
        if about:
            print(f"  about: {about}")

    print("\nboard")
    for person in board[:8]:
        print(f"  {member_name(person) or '-'}  {person.designation or ''}".rstrip())
    if len(board) > 8:
        print(f"  ... {len(board) - 8} more")

    print("\ndividends")
    if not dividends:
        print("  none")
    for item in dividends[:5]:
        filing = item.get("companyNews") or {}
        notice = filing.get("dividendsNotice") or {}
        year = (notice.get("financialYear") or {}).get("fyNameNepali")
        added = str(filing.get("addedDate") or "")[:10]
        print(
            f"  {year or added or '-'}  cash={notice.get('cashDividend')}%  "
            f"bonus={notice.get('bonusShare')}%  {plain(filing.get('newsHeadline'), 80)}"
        )

    print("\ncompany news")
    if not news:
        print("  none")
    for item in news[:5]:
        filing = item.get("companyNews") or {}
        added = str(filing.get("addedDate") or "")[:10]
        kind = filing.get("newsType") or ""
        print(f"  {added or '-'}  {kind}  {plain(filing.get('newsHeadline'), 90)}")

    print("\nagm")
    if not meetings:
        print("  none")
    for item in meetings[:3]:
        filing = item.get("companyNews") or {}
        notice = filing.get("agmNotice") or {}
        print(
            f"  {notice.get('agmDate') or '-'}  {notice.get('agmType') or 'AGM'} "
            f"#{notice.get('agmNo') or '-'}  {plain(notice.get('venue'), 60)}"
        )

    print("\nlatest trades")
    if not trades:
        print("  none")
    for trade in trades:
        print(
            f"  {trade.business_date}  qty={trade.contract_quantity}  "
            f"rate={trade.contract_rate}  amount={trade.contract_amount}"
        )


if __name__ == "__main__":
    main()
