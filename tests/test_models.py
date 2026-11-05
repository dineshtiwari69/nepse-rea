import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from nepseapi.models import FloorSheetEntry, Model, Page, Security, page_from


def test_from_dict_keeps_raw_and_ignores_unknown_fields():
    sec = Security.from_dict({"id": 7, "symbol": "ABC", "securityName": "Abc Ltd", "extra": 1})
    assert sec.id == 7 and sec.symbol == "ABC" and sec.raw["extra"] == 1


def test_from_dict_none():
    assert Security.from_dict(None) is None


def test_page_from_flat():
    page = page_from({"content": [{"contractId": 1}], "number": 2, "size": 5,
                      "totalElements": 11, "totalPages": 3}, FloorSheetEntry)
    assert page.page == 3 and page.size == 5 and page.total_elements == 11
    assert page.has_next is False and len(page) == 1


def test_page_from_nested():
    page = page_from({"totalAmount": 1.5, "floorsheets": {"content": [{"contractId": 9}],
                                                          "number": 0, "totalPages": 2}}, FloorSheetEntry)
    assert page[0].contract_id == 9
    assert page.has_next is True


def test_page_from_garbage():
    page = page_from([], Model)
    assert page.items == [] and page.total_pages == 0


def test_model_list_from():
    rows = Security.list_from([{"id": 1}, None, {"id": 2}])
    assert [r.id for r in rows] == [1, 2]


def test_page_iteration():
    p = Page(items=[1, 2], page=1, size=2, total_elements=2, total_pages=1)
    assert list(p) == [1, 2]
