# nepse-api

Unofficial, dependency-free Python client for public market data on
[nepalstock.com.np](https://nepalstock.com.np).

No login, no account, no API key, and no third-party runtime. The client
keeps its own short-lived session and refreshes it when needed.

```python
from nepseapi import NepseClient

with NepseClient() as client:
    print(client.market_status().is_open)          # CLOSE
    for row in client.prices("NABIL", size=5):
        print(row.business_date, row.close_price)  # 2026-11-04 550.0
    print(client.top_gainers()[0].symbol)
```

## Install

```bash
pip install nepse-api            # from a checkout: pip install -e .
```

Python 3.11 or newer. No runtime dependencies.

## What you can do

| area | methods |
| --- | --- |
| market | `market_status`, `market_summary`, `sector_summary`, `top_gainers`, `top_losers`, `top_turnover`, `supply_demand`, `market_depth` |
| prices | `today_price`, `today_price_all`, `prices`, `price_history`, `export_price_history`, `security_snapshot` |
| floorsheet | `floorsheet`, `floorsheet_by_security`, `floorsheet_totals` |
| securities | `securities`, `security`, `security_card`, `security_profile`, `board_of_directors`, `corporate_actions`, `classification`, `promoters`, `share_groups` |
| indices | `indices`, `index_quotes`, `sub_index_quotes`, `index_history`, `index_graph` |
| companies | `companies`, `company_list`, `margin_list`, `debenture_bonds`, `company_news`, `dividends`, `agm`, `reports`, `report_types` |
| news | `news_and_alerts`, `press_releases`, `notices`, `disclosures`, `book_close` |
| site info | `menu`, `slider_notices`, `holidays`, `events`, `board_members`, `downloads`, `listing_information`, `info_officer`, `faqs`, `contact_info`, `feedback` |

Every paginated method takes a 1-based `page` and a `size`. Use
`client.paginate(client.prices, "NABIL", size=100)` to stream all pages.
`security_id("NABIL")` and `security_by_symbol("NABIL")` translate tickers.

## Results

Methods return dataclasses (`PriceRecord`, `FloorSheetEntry`, `Security`, and
others) with the untouched payload on `.raw`, or a `Page` wrapper for
paginated calls. `Model` tolerates unknown fields, so new server attributes
do not break parsing.

## CLI

```bash
nepse status
nepse --json indices | jq '.[0]'
nepse floorsheet --symbol NABIL
nepse prices NABIL --start 2026-10-01 --end 2026-11-05
nepse export NABIL > nabil.csv
```

## Configuration

```python
NepseClient(timeout=30, retries=3, min_interval=0.25, token_ttl=55)
```

`min_interval` spaces requests out. The session refreshes on its own before
it expires and again after a 401.

## Errors

`NepseError` is the base class. Subclasses: `TransportError`,
`AuthenticationError`, `BadRequestError`, `ForbiddenError`, `NotFoundError`,
`RateLimitError`, `ServerError`. Each carries `.status` and `.url`.

A few routes currently fail on the server side: `floorsheet_by_security`,
`book_close`, and `investor_awareness`.

## Caveats

This project is not affiliated with Nepal Stock Exchange. The site can change
or limit requests at any time. Data is provided as-is, with no warranty and
no trading advice.

## Development

```bash
pip install -e '.[dev]'
pytest
python examples/smoke_live.py
```

## License

[MIT](LICENSE)
