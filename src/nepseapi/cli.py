"""Command line interface: ``nepse <command> [options]``."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections.abc import Iterable, Sequence
from typing import Any

from .client import NepseClient
from .errors import NepseError


def _emit(rows: Iterable[Any], *, as_json: bool, columns: Sequence[str] | None = None) -> None:
    rows = list(rows)
    if as_json:
        print(json.dumps([r.raw if hasattr(r, "raw") else r for r in rows], indent=2, ensure_ascii=False))
        return
    if not rows:
        print("(no rows)")
        return
    if columns is None:
        first = rows[0]
        columns = list(first.raw.keys()) if hasattr(first, "raw") else list(first.__dict__)
    writer = csv.DictWriter(sys.stdout, fieldnames=list(columns), extrasaction="ignore", delimiter="\t")
    writer.writeheader()
    for row in rows:
        source = row.raw if hasattr(row, "raw") else row
        writer.writerow({k: source.get(k, "") for k in columns})


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="nepse", description="Query the public NEPSE API")
    p.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    p.add_argument("--base-url", default=None, help="override the API host")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="market open/close status")
    sub.add_parser("summary", help="today's market summary")
    sub.add_parser("indices", help="index quotes")
    sub.add_parser("sectors", help="sector summary")
    sub.add_parser("holidays", help="holiday list").add_argument("--year", type=int, required=True)

    q = sub.add_parser("quote", help="last traded price snapshot")
    q.add_argument("symbol")

    pr = sub.add_parser("prices", help="historical prices")
    pr.add_argument("symbol")
    pr.add_argument("--start", default=None)
    pr.add_argument("--end", default=None)
    pr.add_argument("--pages", type=int, default=1)

    f = sub.add_parser("floorsheet", help="recent contracts")
    f.add_argument("--symbol", default=None)
    f.add_argument("--pages", type=int, default=1)

    sub.add_parser("top-gainers")
    sub.add_parser("top-losers")
    sub.add_parser("top-turnover")

    s = sub.add_parser("search", help="find a symbol")
    s.add_argument("query")

    c = sub.add_parser("company", help="company profile")
    c.add_argument("symbol")

    n = sub.add_parser("notices", help="latest notices")
    n.add_argument("--pages", type=int, default=1)

    e = sub.add_parser("export", help="CSV history for a symbol")
    e.add_argument("symbol")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = NepseClient(base_url=args.base_url) if args.base_url else NepseClient()
    try:
        if args.command == "status":
            st = client.market_status()
            print(st.is_open if st else "UNKNOWN")
        elif args.command == "summary":
            _emit(client.market_summary(), as_json=args.json)
        elif args.command == "indices":
            _emit(client.index_quotes(), as_json=args.json,
                  columns=["index", "close", "change", "perChange", "generatedTime"])
        elif args.command == "sectors":
            _emit(client.sector_summary(), as_json=args.json)
        elif args.command == "holidays":
            _emit(client.holidays(args.year), as_json=args.json, columns=["holidayDate", "holidayDescription"])
        elif args.command == "quote":
            print(json.dumps(client.security_snapshot(client.security_id(args.symbol)).raw, indent=2))
        elif args.command == "prices":
            sid = client.security_id(args.symbol)
            rows = client.paginate(client.price_history, sid, start_date=args.start, end_date=args.end,
                                   max_pages=args.pages)
            _emit(rows, as_json=args.json, columns=["businessDate", "closePrice", "highPrice", "lowPrice",
                                                    "totalTradedQuantity", "totalTrades"])
        elif args.command == "floorsheet":
            sid = client.security_id(args.symbol) if args.symbol else None
            _emit(client.paginate(client.floorsheet, stock_id=sid, max_pages=args.pages), as_json=args.json,
                  columns=["contractId", "stockSymbol", "contractQuantity", "contractRate", "contractAmount",
                           "buyerMemberId", "sellerMemberId", "businessDate"])
        elif args.command == "top-gainers":
            _emit(client.top_gainers(), as_json=args.json)
        elif args.command == "top-losers":
            _emit(client.top_losers(), as_json=args.json)
        elif args.command == "top-turnover":
            _emit(client.top_turnover(), as_json=args.json)
        elif args.command == "search":
            q = args.query.upper()
            rows = [s for s in client.securities() if q in (s.symbol or "").upper()
                    or q in (s.security_name or "").upper()]
            _emit(rows[:50], as_json=args.json, columns=["id", "symbol", "securityName"])
        elif args.command == "company":
            print(json.dumps(client.security_profile(client.security_id(args.symbol)).raw, indent=2))
        elif args.command == "notices":
            _emit(client.paginate(client.notices, max_pages=args.pages), as_json=args.json,
                  columns=["id", "noticeHeading", "publishedDate"])
        elif args.command == "export":
            sys.stdout.write(client.export_price_history(client.security_id(args.symbol)))
        return 0
    except NepseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except LookupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
