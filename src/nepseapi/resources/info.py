"""Static website content: menus, notices, events, downloads, FAQ and feedback."""

from __future__ import annotations

from typing import Any

from ..models import Holiday, MenuItem, Model, Notice, Page, page_from


class InfoMixin:
    def menu(self) -> list[MenuItem]:
        """Navigation tree; each top-level item carries its ``children``."""
        payload = self._t.request_raw("GET", "/api/web/menu/")
        rows = [row.get("primaryMenu") for row in payload or [] if isinstance(row, dict)]
        items = MenuItem.list_from(rows)
        by_url = {(i.url or ""): i for i in items}
        for row in payload or []:
            if not isinstance(row, dict):
                continue
            parent = by_url.get((row.get("primaryMenu") or {}).get("url") or "")
            if parent is not None:
                parent.children = MenuItem.list_from(row.get("secondaryMenu") or [])
        return items

    def slider_notices(self) -> list[Notice]:
        return Notice.list_from(self._t.request_raw("GET", "/api/web/notice/"))

    def display_popup(self) -> Model | None:
        return Model.from_dict(self._t.request_raw("GET", "/api/web/display-popup"))

    def holidays(self, year: int) -> list[Holiday]:
        return Holiday.list_from(
            self._t.request_raw("GET", "/api/nots/holiday/list", params={"year": year})
        )

    def holiday_years(self) -> list[int]:
        return list(self._t.request_raw("GET", "/api/nots/holiday/year") or [])

    def events(self, page: int = 1, *, size: int = 20) -> Page[Model]:
        payload = self._t.request_raw("GET", "/api/web/event/", params={"page": page - 1, "size": size})
        return page_from(payload, Model, default_size=size)

    def board_members(self, page: int = 1, *, size: int = 20) -> Page[Model]:
        """NEPSE's own board of directors (``web/bod``); security boards live in ``board_of_directors``."""
        payload = self._t.request_raw("GET", "/api/web/bod/", params={"page": page - 1, "size": size})
        return page_from(payload, Model, default_size=size)

    def downloads(self, page: int = 1, *, size: int = 20) -> Page[Model]:
        payload = self._t.request_raw("GET", "/api/web/download", params={"page": page - 1, "size": size})
        return page_from(payload, Model, default_size=size)

    def listing_information(self) -> Model | None:
        return Model.from_dict(self._t.request_raw("GET", "/api/web/listing-info"))

    def info_officer(self) -> Model | None:
        return Model.from_dict(self._t.request_raw("GET", "/api/web/info-officer"))

    def about_introduction(self, page: int = 1, *, size: int = 20) -> Page[Model]:
        payload = self._t.request_raw(
            "GET", "/api/web/about-us/introduction", params={"page": page - 1, "size": size}
        )
        return page_from(payload, Model, default_size=size)

    def about_structure(self, page: int = 1, *, size: int = 20) -> Page[Model]:
        payload = self._t.request_raw(
            "GET", "/api/web/about-us/structure", params={"page": page - 1, "size": size}
        )
        return page_from(payload, Model, default_size=size)

    def contact_info(self) -> Model | None:
        return Model.from_dict(self._t.request_raw("GET", "/api/web/about-us/contact-info"))

    def faqs(self, page: int = 1, *, size: int = 20) -> Page[Model]:
        payload = self._t.request_raw("GET", "/api/web/nepse-faq", params={"page": page - 1, "size": size})
        return page_from(payload, Model, default_size=size)

    def faq_contacts(self, page: int = 1, *, size: int = 20) -> Page[Model]:
        payload = self._t.request_raw(
            "GET", "/api/web/nepse-faq/contact", params={"page": page - 1, "size": size}
        )
        return page_from(payload, Model, default_size=size)

    # ---------------------------------------------------------------- media
    def image(self, kind: str, file_name: str) -> bytes:
        """Fetch a site image; ``kind`` is ``officer``, ``bod``, ``event`` or ``popup``."""
        if kind == "officer":
            return self._t.request_raw("GET", "/api/web/officer-image", params={"fileName": file_name}, raw=True)
        return self._t.request_raw("GET", f"/api/web/{kind}/getImage", params={"fileName": file_name}, raw=True)

    def feedback(self, payload: dict[str, Any]) -> Model | None:
        """Submit website feedback (no captcha required; the suggestion box's
        ``/api/mail/send-feedback`` is the captcha-guarded variant)."""
        return Model.from_dict(self._t.request_raw("POST", "/api/web/feedback", json_body=payload))
