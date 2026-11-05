import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from nepseapi import NepseClient


class Recorder:
    """Stub transport capturing URLs/params instead of hitting the network."""

    def __init__(self):
        self.base_url = "https://example.test"
        self.calls = []
        self.market_id = 80

    def base_nonce(self):
        return 247

    def nonce(self, *, kind="quote"):
        self.calls.append(("nonce", kind))
        return {"quote": 111, "trade": 222, "index": 333}[kind]

    def request_raw(self, method, path, *, params=None, json_body=None, raw=False, **_):
        self.calls.append((method, path, params, json_body))
        return {"content": [], "totalPages": 0}


@pytest.fixture()
def client():
    c = NepseClient()
    c._t = Recorder()
    return c


def test_prices_converts_to_zero_based_page(client):
    client.prices(131, page=3, size=10)
    method, path, params, _ = client._t.calls[-1]
    assert (method, path) == ("GET", "/api/nots/market/security/price/131")
    assert params["page"] == 2 and params["size"] == 10


def test_today_price_uses_quote_nonce(client):
    client.today_price(size=5, stock_id=131)
    assert ("nonce", "quote") in client._t.calls
    _, _, params, body = client._t.calls[-1]
    assert body == {"id": 111} and params["stockId"] == 131


def test_floorsheet_uses_trade_nonce_and_sort(client):
    client.floorsheet(buyer=45)
    _, _, params, body = client._t.calls[-1]
    assert body == {"id": 222} and params["sort"] == "contractId,desc" and params["buyerBroker"] == 45


def test_index_graph_uses_index_nonce(client):
    client.index_graph(58, start_date="2026-01-01", end_date="2026-02-01")
    _, path, params, body = client._t.calls[-1]
    assert path == "/api/nots/graph/index/58" and body == {"id": 333}
    assert params["indexCode"] == 58


def test_graphdata_uses_base_nonce(client):
    client.graphdata(131)
    assert client._t.calls[-1][3] == {"id": 247}


def test_paginate_walks_pages_until_last(client):
    pages = {"n": 0}

    def fake(page=1, size=20):
        pages["n"] += 1
        return type("P", (), {"has_next": page < 3, "__iter__": lambda self: iter([page])})()

    assert list(client.paginate(fake)) == [1, 2, 3]
    assert pages["n"] == 3


def test_security_id_accepts_int_and_digit_string(client):
    assert client.security_id(131) == 131
    assert client.security_id("131") == 131
