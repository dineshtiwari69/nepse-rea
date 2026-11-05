"""Watchlist report: last price, day change and recent contracts per symbol."""

import sys

sys.path.insert(0, "src")

from nepseapi import NepseClient

WATCHLIST = ["NABIL", "NICA", "SCB"]


def main() -> None:
    with NepseClient(min_interval=0.4) as client:
        for symbol in WATCHLIST:
            sid = client.security_id(symbol)
            snap = client.security_snapshot(sid)
            trades = list(client.paginate(client.floorsheet, stock_id=sid, size=5, max_pages=1))
            print(f"{symbol:6} LTP={snap.last_traded_price:>10} open={snap.open_price} trades={len(trades)}")


if __name__ == "__main__":
    main()
