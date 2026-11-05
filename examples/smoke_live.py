"""Live smoke test against the real API: python examples/smoke_live.py"""

import sys

sys.path.insert(0, "src")

from nepseapi import NepseClient


def main() -> None:
    c = NepseClient()
    st = c.market_status()
    print("market:", st.is_open, "id:", st.id, "open:", st.open)
    print("summary:", [(m.detail, m.value) for m in c.market_summary()][:3])
    q = c.index_quotes()[0]
    print("index:", q.index, q.close, q.change)
    p = c.prices(131, size=2)
    print("prices:", p.page, p.total_pages, [(r.business_date, r.close_price) for r in p])
    print("snapshot:", c.security_snapshot(131).last_traded_price)
    print("floorsheet rows:", len(c.floorsheet(size=2)), c.floorsheet_totals())
    print("resolve:", c.security_by_symbol("NABIL").id, c.security_id("NABIL"))
    print("graph points (intraday, empty after 15:00 close):", len(c.graphdata(131)))
    print("daily graph rows:", len(c.daily_trading(131)))
    print("today price:", len(c.today_price(size=2)))
    print("index history:", len(c.index_history(58, size=2)))
    print("board:", c.board_of_directors(131)[0].designation)
    print("classification:", c.classification(share_group="A").total_elements)
    print("notices:", len(c.notices(size=3)))
    print("board members:", len(c.board_members()))
    print("holidays:", c.holidays(2026)[0].holiday_date)


if __name__ == "__main__":
    main()
