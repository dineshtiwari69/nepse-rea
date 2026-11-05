"""Prepare anonymous session tokens for request headers."""

from __future__ import annotations

_TABLE: tuple[int, ...] = (
    5, 8, 4, 7, 9, 4, 6, 9, 5, 5, 6, 5, 3, 5, 4, 4, 9, 6, 6, 8, 8, 6, 8, 6,
    5, 8, 8, 9, 5, 9, 8, 5, 3, 4, 7, 7, 4, 7, 3,
)


def _digits(salt2: int) -> tuple[int, int, int]:
    """Return (hundreds, tens, units) place values of ``salt2``."""
    return (salt2 // 100) % 10, (salt2 // 10) % 10, salt2 % 10


def _idx(salt2: int) -> int:
    h, t, u = _digits(salt2)
    return h + t + u


def cdx(salt1: int, salt2: int, salt3: int, salt4: int, salt5: int) -> int:
    return _TABLE[_idx(salt2)] + 22


def rdx(salt1: int, salt2: int, salt3: int, salt4: int, salt5: int) -> int:
    h, t, _ = _digits(salt2)
    return h + t + _TABLE[_idx(salt2)] + 32


def bdx(salt1: int, salt2: int, salt3: int, salt4: int, salt5: int) -> int:
    h, t, _ = _digits(salt2)
    return h + t + _TABLE[_idx(salt2)] + 60


def ndx(salt1: int, salt2: int, salt3: int, salt4: int, salt5: int) -> int:
    _, t, _ = _digits(salt2)
    return t + _TABLE[_idx(salt2)] + 88


def mdx(salt1: int, salt2: int, salt3: int, salt4: int, salt5: int) -> int:
    h, _, _ = _digits(salt2)
    return h + _TABLE[_idx(salt2)] + 110


def _cut(token: str, salts: tuple[int, int, int, int, int]) -> str:
    """Reproduce the JavaScript slice chain, dropping one char per index."""
    i1 = cdx(*salts)
    i2 = rdx(*salts)
    i3 = bdx(*salts)
    i4 = ndx(*salts)
    i5 = mdx(*salts)
    return (
        token[:i1]
        + token[i1 + 1 : i2]
        + token[i2 + 1 : i3]
        + token[i3 + 1 : i4]
        + token[i4 + 1 : i5]
        + token[i5 + 1 :]
    )


def mangle_access_token(token: str, salt1: int, salt2: int, salt3: int, salt4: int, salt5: int) -> str:
    """Return the access-token value sent in the Authorization header."""
    return _cut(token, (salt1, salt2, salt3, salt4, salt5))


def mangle_refresh_token(token: str, salt1: int, salt2: int, salt3: int, salt4: int, salt5: int) -> str:
    """Return the refresh-token value sent when renewing a session."""
    return _cut(token, (salt2, salt1, salt3, salt5, salt4))
