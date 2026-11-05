"""Exercise every public method once and report OK / error per call.

Usage: python examples/verify_all.py [--json]
Known-dead routes (nginx 403, 404, SQL 500) are reported as DEAD instead of failing.
"""

import sys
import traceback

sys.path.insert(0, "src")

from nepseapi import NepseClient
from nepseapi.errors import ForbiddenError, NotFoundError, ServerError

DEAD = (ForbiddenError, NotFoundError, ServerError)

CALLS = [
    ("market_status", lambda c: c.market_status()),
    ("market_summary", lambda c: c.market_summary()),
    ("market_summary_history", lambda c: c.market_summary_history()),
    ("sectors", lambda c: c.sectors()),
    ("sector_summary", lambda c: c.sector_summary()),
    ("supply_demand", lambda c: c.supply_demand()),
    ("market_depth", lambda c: c.market_depth(131)),
    ("market_depth_odd_lot", lambda c: c.market_depth_odd_lot(131)),
    ("top_turnover", lambda c: c.top_turnover()),
    ("top_trades", lambda c: c.top_trades()),
    ("top_transactions", lambda c: c.top_transactions()),
    ("top_gainers", lambda c: c.top_gainers()),
    ("top_losers", lambda c: c.top_losers()),
    ("today_price", lambda c: c.today_price(size=2)),
    ("today_price_all", lambda c: c.today_price_all()),
    ("price_history", lambda c: c.price_history(131, start_date="2026-10-01", end_date="2026-11-05", size=2)),
    ("export_price_history", lambda c: c.export_price_history(131, start_date="2026-10-01", end_date="2026-11-05")),
    ("floorsheet", lambda c: c.floorsheet(size=2)),
    ("floorsheet_totals", lambda c: c.floorsheet_totals()),
    ("securities", lambda c: c.securities()),
    ("securities_lite", lambda c: c.securities_lite()),
    ("security", lambda c: c.security(131)),
    ("security_card", lambda c: c.security_card(131)),
    ("security_snapshot", lambda c: c.security_snapshot(131)),
    ("security_profile", lambda c: c.security_profile(131)),
    ("board_of_directors", lambda c: c.board_of_directors(131)),
    ("corporate_actions", lambda c: c.corporate_actions(131)),
    ("share_groups", lambda c: c.share_groups()),
    ("classification", lambda c: c.classification(share_group="A", size=2)),
    ("promoters", lambda c: c.promoters(size=2)),
    ("prices", lambda c: c.prices(131, size=2)),
    ("floorsheet_by_security", lambda c: c.floorsheet_by_security(131, size=2)),
    ("graphdata", lambda c: c.graphdata(131)),
    ("daily_trading", lambda c: c.daily_trading(131)),
    ("security_image", lambda c: c.security_image("/logos/nabil.png")),
    ("companies", lambda c: c.companies(size=2)),
    ("company_list", lambda c: c.company_list()),
    ("margin_list", lambda c: c.margin_list()),
    ("debenture_bonds", lambda c: c.debenture_bonds(1)),
    ("company_news", lambda c: c.company_news(131)),
    ("dividends", lambda c: c.dividends(131)),
    ("agm", lambda c: c.agm(131)),
    ("reports", lambda c: c.reports(131)),
    ("report_types", lambda c: c.report_types()),
    ("reports_by_category", lambda c: c.reports_by_category(1, size=2)),
    ("book_close", lambda c: c.book_close(131)),
    ("indices", lambda c: c.indices()),
    ("index_quotes", lambda c: c.index_quotes()),
    ("sub_index_quotes", lambda c: c.sub_index_quotes()),
    ("index_history", lambda c: c.index_history(58, size=2)),
    ("index_graph", lambda c: c.index_graph(58)),
    ("news_and_alerts", lambda c: c.news_and_alerts()),
    ("press_releases", lambda c: c.press_releases(size=2)),
    ("company_news_feed", lambda c: c.company_news_feed()),
    ("investor_awareness", lambda c: c.investor_awareness()),
    ("notices", lambda c: c.notices(size=2)),
    ("disclosures", lambda c: c.disclosures()),
    ("corporate_disclosures", lambda c: c.corporate_disclosures()),
    ("menu", lambda c: c.menu()),
    ("slider_notices", lambda c: c.slider_notices()),
    ("display_popup", lambda c: c.display_popup()),
    ("holidays", lambda c: c.holidays(2026)),
    ("holiday_years", lambda c: c.holiday_years()),
    ("events", lambda c: c.events(size=2)),
    ("board_members", lambda c: c.board_members(size=2)),
    ("downloads", lambda c: c.downloads(size=2)),
    ("listing_information", lambda c: c.listing_information()),
    ("info_officer", lambda c: c.info_officer()),
    ("about_introduction", lambda c: c.about_introduction(size=2)),
    ("about_structure", lambda c: c.about_structure(size=2)),
    ("contact_info", lambda c: c.contact_info()),
    ("faqs", lambda c: c.faqs(size=2)),
    ("faq_contacts", lambda c: c.faq_contacts(size=2)),
]


def main() -> int:
    ok = dead = bad = 0
    with NepseClient(min_interval=0.15) as client:
        for name, call in CALLS:
            try:
                result = call(client)
                size = len(result) if hasattr(result, "__len__") else 1
                print(f"OK    {name:26} {size}")
                ok += 1
            except DEAD as exc:
                print(f"DEAD  {name:26} {type(exc).__name__}: {str(exc)[:60]}")
                dead += 1
            except Exception as exc:  # noqa: BLE001
                print(f"FAIL  {name:26} {type(exc).__name__}: {str(exc)[:80]}")
                traceback.print_exc(limit=1)
                bad += 1
    print(f"\n{ok} ok, {dead} known-dead, {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
