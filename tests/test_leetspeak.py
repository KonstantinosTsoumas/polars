import polars as pl
import pytest
from polars.testing import assert_series_equal

from polars_leetspeak import leetspeak, unleetspeak


def test_encode_basic():
    df = pl.DataFrame({"text": ["hello", "polars", "base"]})
    out = df.with_columns(leet=leetspeak("text"))["leet"]
    assert_series_equal(out, pl.Series("leet", ["h3ll0", "p0l4r5", "8453"]))


def test_encode_is_case_insensitive():
    df = pl.DataFrame({"text": ["HELLO", "Polars"]})
    out = df.with_columns(leet=leetspeak("text"))["leet"]
    assert_series_equal(out, pl.Series("leet", ["H3LL0", "P0l4r5"]))


def test_non_alphabetic_passes_through():
    df = pl.DataFrame({"text": ["hi there!", "café", ""]})
    out = df.with_columns(leet=leetspeak("text"))["leet"]
    assert_series_equal(out, pl.Series("leet", ["h1 7h3r3!", "c4fé", ""]))


def test_roundtrip_lowercase_without_digits():
    words = ["hello", "polars", "leetspeak", "abcdefg", "zigzag"]
    df = pl.DataFrame({"text": words})
    out = df.with_columns(back=unleetspeak(leetspeak("text")))["back"]
    assert_series_equal(out, pl.Series("back", words))


def test_nulls_are_preserved():
    df = pl.DataFrame({"text": ["hello", None]})
    out = df.with_columns(leet=leetspeak("text"))["leet"]
    assert_series_equal(out, pl.Series("leet", ["h3ll0", None]))


def test_namespace():
    df = pl.DataFrame({"text": ["hello"]})
    out = df.with_columns(leet=pl.col("text").leet.encode())["leet"]
    assert_series_equal(out, pl.Series("leet", ["h3ll0"]))
    back = df.with_columns(x=pl.col("text").leet.encode().leet.decode())["x"]
    assert_series_equal(back, pl.Series("x", ["hello"]))


def test_works_in_lazy_and_group_by():
    df = pl.LazyFrame({"g": ["a", "a", "b"], "text": ["hi", "to", "gas"]})
    out = df.with_columns(leet=leetspeak("text")).collect()["leet"]
    assert_series_equal(out, pl.Series("leet", ["h1", "70", "645"]))


def test_non_string_input_raises():
    df = pl.DataFrame({"n": [1, 2]})
    with pytest.raises(Exception):
        df.with_columns(leet=leetspeak("n"))
