# NEPSE website API — reverse-engineering notes

Everything below was derived from the production bundles served by
`https://nepalstock.com.np` (Angular build `main.6ca32ef2df433b06ed55.js`,
lazy chunks `5.*`/`6.*`, and `assets/prod/css.wasm`) plus live probing on
2026-11-05. No authentication to the trading platform is involved: the whole
public site is reachable anonymously.

```
base URL   https://nepalstock.com.np
API root   /api/
```

## 1. The anonymous handshake

`GET /api/authenticate/prove` returns a fresh token pair plus five integer
"salts":

```json
{"serverTime":1793889892000,"salt":"|#^7-{r*JPz25-%jZR%P",
 "accessToken":"eyJlbmMiOiJBMTI4Q0JDLUhTMjU2I0iwiYWxnIjoiZ2lipIn0..…",
 "refreshToken":"eyJlbmMiOiJBMTI4Q0JDLUhTMjUO2IiwiYWxnIjoiZGltyIn0..…",
 "salt1":75632,"salt2":51120,"salt3":73951,"salt4":58948,"salt5":12612,
 "isDisplayActive":false,"popupDocFor":""}
```

The tokens are *not* used verbatim. The site loads a 750-byte WebAssembly
module (`/assets/prod/css.wasm`, exports `cdx rdx bdx ndx mdx`) that turns
`salt2` into five indices, then removes the character at each index:

```js
tok = tok.slice(0,A) + tok.slice(A+1,B) + tok.slice(B+1,C)
    + tok.slice(C+1,D) + tok.slice(D+1,E) + tok.slice(E+1)
```

Only `salt2` matters to the arithmetic; every export is
`table[digit-sum] + (hundreds|tens|units digits) + constant`, with `table`
being a 39-entry lookup table baked into the module. `nepseapi._mangle` is a
pure-Python reimplementation, verified byte-for-byte against the wasm.

The un-obfuscated access token goes into every request:

```
Authorization: Salter <mangled accessToken>
```

`GET /api/authenticate/prove` needs no headers at all; everything else needs
the `Salter` header. Tokens live **~60 s** (measured: 200 up to 65 s, then
401). `POST /api/authenticate/refresh-token` with `{"refreshToken": <mangled
refreshToken>}` (swapped salt order) mints a new pair and new salts; the
response is mangled again with the *new* salts.

### Body nonce

Several POST endpoints carry `{"id": <number>}` where the number is an
anti-bot value derived from the current session id (`market-open.id`), the day
of month and the salts:

```
base = DUMMY[sessionId % 100] + sessionId + 2 * day
```

| call site | value |
| --- | --- |
| `market/graphdata/*`, `security/{id}` (POST) | `base` |
| floorsheet | `base + salt[k]*day - salt[k-1]`, `k = 1 if base%10 < 4 else 3` |
| today price | `k = 1 if base%10 < 5 else 3` |
| index graphs | `k = 3 if base%10 < 5 else 1` |

A wrong nonce yields `401` (today price, index graph) or an empty list (graphs).
`DUMMY` is the 100-entry array in `nepseapi/_http.py`.

## 2. Response conventions

* Pagination is Spring Data style, **0-based** `page` + `size`; the website
  sends `page-1`. Responses look like
  `{"content":[…],"number":0,"size":20,"totalElements":…,"totalPages":…}`.
  Some endpoints nest it one level (floorsheet: `{"floorsheet":{"content":…},"totalAmount":…}`).
* Sorted endpoints take `sort=<field>,<asc|desc>`.
* Dates are `yyyy-MM-dd`; some endpoints answer `500 "Searched Date is not valid."`
  when a range is missing.
* Errors are HTML bodies: `401 WARNING: UNAUTHORIZED ACCESS` (token/nonce),
  `401 Invalid Authentication Token` (`/api/users/*`), `403` from nginx for a
  few routes, `500` with a Java stack trace for SQL faults.
* `nots/news/*` bodies contain raw HTML.

## 3. Endpoint reference

### Session / token
| method | path | notes |
| --- | --- | --- |
| GET | `/api/authenticate/prove` | mint token, no auth |
| POST | `/api/authenticate/refresh-token` | `{refreshToken}` |
| POST | `/api/authenticate/login` | credentials — **403 from nginx** (2026-11) |
| GET | `/api/authenticate/pexpiry/token-expiry?token=` | |

### Market
| method | path | params |
| --- | --- | --- |
| GET | `/api/nots/nepse-data/market-open` | `{isOpen,asOf,id}` |
| GET | `/api/nots/market-summary` | turnover/volume/transactions |
| GET | `/api/nots/market-summary-history` | daily totals |
| GET | `/api/nots/sectorwise` | `businessDate` |
| GET | `/api/nots/sector` | |
| GET | `/api/nots/nepse-data/supplydemand` | `all` |
| GET | `/api/nots/nepse-data/marketdepth/{id}` | raw text |
| GET | `/api/nots/nepse-data/marketdepth-ol/{id}` | odd lot |
| GET | `/api/nots/top-ten/{turnover,trade,transaction,top-gainer,top-loser,trade-qty}` | `all` |
| POST | `/api/nots/nepse-data/today-price` | nonce; `page,size,businessDate,stockId,sort` |
| POST | `/api/nots/nepse-data/todays-price/{date}` | nonce, unpaged |
| POST | `/api/nots/nepse-data/floorsheet` | nonce; `page,size,stockId,contractNo,buyerBroker,sellerBroker,sort` |
| GET | `/api/nots/lives-market` | intraday tape |
| GET | `/api/nots/securityDailyTradeStat/{id}` | `58` = index ticker |
| GET | `/api/nots/nepse-data/marcapbydate/` | `page` |
| GET | `/api/nots/market/history/security/{id}` | `startDate,endDate,page,size` |
| GET | `/api/nots/market/export/{id}` | CSV |

### Securities
| method | path | params |
| --- | --- | --- |
| GET | `/api/nots/security` | `nonDelisted`, `nonPromoter` — master list |
| POST | `/api/nots/security/{id}` | nonce — market-picture card |
| GET | `/api/nots/security/{id}` | |
| GET | `/api/nots/security-detail/{id}` | last/open/high/low |
| GET | `/api/nots/security/profile/{id}` · `/boardOfDirectors/{id}` · `/corporate-actions/{id}` | HTML/JSON detail |
| GET | `/api/nots/security/shareGroup/` · `/classification` (`page,shareGroup`) | |
| GET | `/api/nots/security/promoters` | `page` |
| GET | `/api/nots/market/security/price/{id}` | `page,size` |
| POST | `/api/nots/security/floorsheet/{id}` | **403 from nginx**; use `floorsheet?stockId=` |
| POST | `/api/nots/market/graphdata/{id}` · `/daily/{id}` | chart points |
| GET | `/api/nots/security/fetchFiles` · `/getImage` | `fileLocation` |

### Indices
| method | path |
| --- | --- |
| GET | `/api/nots/nepse-index` (values), `/api/nots` (sub-indices), `/api/nots/index` (catalogue) |
| GET | `/api/nots/index/history/{id}` (`page`) |
| POST | `/api/nots/graph/index/{id}` (`indexCode,startDate,endDate`, nonce) |
| GET | `/api/nots/daily-index-change-stat/{id}` — 404 in practice |

### Companies / filings / news
`/api/nots/company/` (`page`), `/company/list`, `/company/margin-list`,
`/company/debentureAndBond?type=`, `/application/{company-news,agm,dividend,reports}/{id}`,
`/report/report-types`, `/news/media/{news-and-alerts,company-news,investor-awareness}`,
`/news/press-release`, `/news/notice/all`, `/news/companies/disclosure`,
`/news/book-close/{id}` (404 in practice).

### Website content
`/api/web/menu/`, `/notice/`, `/display-popup`, `/event/`, `/bod/`, `/download`,
`/listing-info`, `/info-officer`, `/officer-image?fileName=`, `/popup-image`,
`/nepse-faq`, `/nepse-faq/contact`, `/about-us/{introduction,structure,contact-info}`,
`/report/reportByCategory/{id}`, POST `/web/feedback`.

### Captcha (out of scope)

Only the suggestion-box form uses a captcha, and it posts to `/api/mail/send-feedback`
(not `/api/web/feedback`, which needs none). The challenge is minted by
`/api/web/captcha/{id,image,reload,validate}`; the answer travels as query
parameters (`?identifier=&userText=`, body `{}`) and returns `true`/`false`.
Nothing else in the API validates a captcha, so this library omits those helpers.

## 4. Quirks worth knowing

* `/api/authenticate/login`, `/api/nots/security/floorsheet*` return nginx 403
  regardless of method or headers.
* `market/graphdata/{id}` is the intraday tape and is usually empty once the 15:00
  close has passed; `market/graphdata/daily/{id}` keeps ~100 daily rows. Index
  charts go through `graph/index`, not `graphdata`.
* `nots/news/media/investor-awareness` currently fails with a Hibernate
  `SQLGrammarException` (500).
* `/api/users/*` needs a *login* token (`Bearer`), not the anonymous one.
* Do not hammer: the site rate-limits and rotates tokens per IP quickly.
