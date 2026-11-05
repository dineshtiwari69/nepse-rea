"""HTTP transport: session refresh, retries, and rate limiting."""

from __future__ import annotations

import json
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ._mangle import mangle_access_token, mangle_refresh_token
from .errors import (
    AuthenticationError,
    BadRequestError,
    ForbiddenError,
    NepseError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TransportError,
)

DEFAULT_BASE_URL = "https://nepalstock.com.np"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

#: Constants mixed into some POST bodies.
_DUMMY_DATA: tuple[int, ...] = (
    147, 117, 239, 143, 157, 312, 161, 612, 512, 804, 411, 527, 170, 511, 421,
    667, 764, 621, 301, 106, 133, 793, 411, 511, 312, 423, 344, 346, 653, 758,
    342, 222, 236, 811, 711, 611, 122, 447, 128, 199, 183, 135, 489, 703, 800,
    745, 152, 863, 134, 211, 142, 564, 375, 793, 212, 153, 138, 153, 648, 611,
    151, 649, 318, 143, 117, 756, 119, 141, 717, 113, 112, 146, 162, 660, 693,
    261, 362, 354, 251, 641, 157, 178, 631, 192, 734, 445, 192, 883, 187, 122,
    591, 731, 852, 384, 565, 596, 451, 772, 624, 691,
)


@dataclass(slots=True)
class TokenBundle:
    """Anonymous session credentials."""

    access_token: str
    refresh_token: str
    salts: tuple[int, int, int, int, int]
    expires_at: float

    def auth_header(self) -> str:
        return "Salter " + mangle_access_token(self.access_token, *self.salts)

    def refresh_payload(self) -> dict[str, str]:
        return {"refreshToken": mangle_refresh_token(self.refresh_token, *self.salts)}


class TokenManager:
    """Thread-safe, self-healing holder of the anonymous session token."""

    def __init__(self, transport: Transport, *, token_ttl: float) -> None:
        self._transport = transport
        self._ttl = token_ttl
        self._lock = threading.RLock()
        self._bundle: TokenBundle | None = None

    # ------------------------------------------------------------------ api
    def get(self, *, force: bool = False) -> TokenBundle:
        with self._lock:
            now = time.monotonic()
            if (
                force
                or self._bundle is None
                or self._bundle.expires_at - now < self._ttl * 0.25
            ):
                self._bundle = self._mint()
            return self._bundle

    def refresh(self) -> TokenBundle:
        """Refresh through ``/api/authenticate/refresh-token``, falling back to ``prove``."""
        with self._lock:
            if self._bundle is None:
                return self.get(force=True)
            try:
                payload = self._transport.request_raw(
                    "POST", "/api/authenticate/refresh-token",
                    json_body=self._bundle.refresh_payload(),
                    authorized=False,
                    retries=1,
                )
                self._bundle = self._from_payload(payload)
            except NepseError:
                self._bundle = self._mint()
            return self._bundle

    # -------------------------------------------------------------- internals
    def _mint(self) -> TokenBundle:
        payload = self._transport.request_raw(
            "GET", "/api/authenticate/prove", authorized=False
        )
        return self._from_payload(payload)

    def _from_payload(self, payload: Mapping[str, Any]) -> TokenBundle:
        try:
            return TokenBundle(
                access_token=payload["accessToken"],
                refresh_token=payload.get("refreshToken", ""),
                salts=(
                    int(payload["salt1"]),
                    int(payload["salt2"]),
                    int(payload["salt3"]),
                    int(payload["salt4"]),
                    int(payload["salt5"]),
                ),
                expires_at=time.monotonic() + self._ttl,
            )
        except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - defensive
            raise AuthenticationError(f"malformed session response: {exc!r}") from exc


class Transport:
    """Minimal JSON-over-HTTP client with retries, backoff and rate limiting."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        timeout: float = 30.0,
        retries: int = 3,
        min_interval: float = 0.25,
        token_ttl: float = 60.0,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.min_interval = min_interval
        self.user_agent = user_agent
        self._tokens = TokenManager(self, token_ttl=token_ttl)
        self._throttle = threading.Lock()
        self._last_call = 0.0
        self._market_id: int | None = None

    # ------------------------------------------------------------------ state
    @property
    def market_id(self) -> int:
        """Id of the current trading session."""
        if self._market_id is None:
            status = self.request_raw("GET", "/api/nots/nepse-data/market-open", retries=1)
            self._market_id = int(status.get("id") or 1)
        return self._market_id

    def invalidate_market_id(self) -> None:
        self._market_id = None

    # ------------------------------------------------------------------ nonce
    def base_nonce(self) -> int:
        """Base value mixed into some POST bodies."""
        day = time.localtime().tm_mday
        mid = self.market_id
        return _DUMMY_DATA[mid % len(_DUMMY_DATA)] + mid + 2 * day

    def nonce(self, *, kind: str = "quote") -> int:
        """Body id for ``quote``, ``trade``, or ``index`` requests."""
        base = self.base_nonce()
        salts = self._tokens.get().salts
        day = time.localtime().tm_mday
        if kind == "index":
            k = 3 if base % 10 < 5 else 1
        elif kind == "trade":
            k = 1 if base % 10 < 4 else 3
        else:
            k = 1 if base % 10 < 5 else 3
        return base + salts[k] * day - salts[k - 1]

    # ------------------------------------------------------------------ request
    def _sleep(self) -> None:
        if self.min_interval <= 0:
            return
        with self._throttle:
            wait = self._last_call + self.min_interval - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()

    def request_raw(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        authorized: bool = True,
        retries: int | None = None,
        raw: bool = False,
        auth_retry: bool = True,
    ) -> Any:
        url = self.base_url + path
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                url += ("&" if "?" in url else "?") + urllib.parse.urlencode(clean)
        attempts = self.retries if retries is None else retries
        last_exc: Exception | None = None

        for attempt in range(attempts + 1):
            self._sleep()
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "*/*" if raw else "application/json",
                "Accept-Language": "en-US,en;q=0.9",
            }
            data = None
            if json_body is not None:
                data = json.dumps(json_body).encode()
                headers["Content-Type"] = "application/json"
            if authorized:
                headers["Authorization"] = self._tokens.get().auth_header()
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read()
                    return body if raw else _decode(body, url)
            except urllib.error.HTTPError as exc:
                body = exc.read()
                if exc.code == 401 and authorized and auth_retry:
                    self._tokens.refresh()
                    return self.request_raw(
                        method, path, params=params, json_body=json_body,
                        authorized=authorized, retries=retries, raw=raw, auth_retry=False,
                    )
                if exc.code in (502, 503, 504) and attempt < attempts:
                    last_exc = exc
                    time.sleep(_backoff(attempt))
                    continue
                raise _error_for(exc.code, body, url) from None
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                last_exc = exc
                if attempt < attempts:
                    time.sleep(_backoff(attempt))
                    continue
                raise TransportError(f"{method} {url} failed: {exc}") from exc
        raise TransportError(f"{method} {url} failed: {last_exc}")


def _backoff(attempt: int) -> float:
    return min(8.0, 0.4 * 2**attempt) + random.random() * 0.2


def _decode(body: bytes, url: str) -> Any:
    if not body:
        return None
    text = body.decode("utf-8", "replace").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _error_for(status: int, body: bytes, url: str) -> NepseError:
    detail = _decode(body, url)
    if isinstance(detail, str):
        message = " ".join(detail.split())[:300]
    elif detail is not None:
        message = json.dumps(detail)[:300]
    else:
        message = ""
    message = message or f"HTTP {status}"
    classes = {
        400: BadRequestError,
        403: ForbiddenError,
        404: NotFoundError,
        429: RateLimitError,
    }
    cls = classes.get(status) or (ServerError if status >= 500 else NepseError)
    return cls(message, status=status, url=url)
