"""Checks for session-token preparation."""

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from nepseapi._mangle import (
    bdx,
    cdx,
    mangle_access_token,
    mangle_refresh_token,
    mdx,
    ndx,
    rdx,
)

# (salt2, cdx, rdx, bdx, ndx, mdx)
VECTORS = [
    (18259, 31, 48, 76, 102, 121),
    (36234, 27, 42, 70, 96, 117),
    (89054, 27, 42, 70, 98, 115),
    (17980, 28, 55, 83, 102, 125),
    (42483, 26, 48, 76, 100, 118),
    (14621, 27, 45, 73, 95, 121),
    (12734, 26, 46, 74, 95, 121),
    (88412, 31, 46, 74, 98, 123),
    (58336, 25, 41, 69, 94, 116),
    (92825, 26, 46, 74, 94, 122),
    (78895, 30, 57, 85, 105, 126),
    (94419, 26, 41, 69, 93, 118),
    (51120, 29, 42, 70, 97, 118),
]


@pytest.mark.parametrize("salt2,c,r,b,n,m", VECTORS, ids=[str(v[0]) for v in VECTORS])
def test_index_vectors(salt2, c, r, b, n, m):
    assert cdx(0, salt2, 0, 0, 0) == c
    assert rdx(0, salt2, 0, 0, 0) == r
    assert bdx(0, salt2, 0, 0, 0) == b
    assert ndx(0, salt2, 0, 0, 0) == n
    assert mdx(0, salt2, 0, 0, 0) == m


def test_salts_other_than_salt2_are_ignored():
    assert cdx(1, 18259, 2, 3, 4) == cdx(9, 18259, 8, 7, 6)


def test_mangle_removes_exactly_five_characters():
    token = "".join(chr(ord("a") + i % 26) for i in range(250))
    mangled = mangle_access_token(token, 1, 51120, 3, 4, 5)
    assert len(mangled) == len(token) - 5
    assert mangled != token


def test_refresh_token_uses_swapped_salt_order():
    token = "x" * 300
    assert mangle_refresh_token(token, 75632, 51120, 73951, 58948, 12612) == mangle_access_token(
        token, 51120, 75632, 73951, 12612, 58948
    )
