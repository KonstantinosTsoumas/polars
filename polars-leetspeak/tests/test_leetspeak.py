from __future__ import annotations

import polars as pl
import pytest
from polars.plugins import register_plugin_function
from polars.testing import assert_frame_equal, assert_series_equal

import leetspeak
import leetspeak.extension  # noqa: F401  (registers the `leet` namespace)
from leetspeak._utils import LIB


def leet(values: list[str | None], **kwargs) -> pl.Series:
    df = pl.DataFrame({"text": values}, schema={"text": pl.String})
    return df.select(leetspeak.leetify("text", **kwargs))["text"]


class TestLeetify:
    def test_basic_level_substitutes_the_classic_set(self):
        assert leet(["polars"], preserve_case=True).to_list() == ["p0l4r5"]

    def test_advanced_level_adds_more_substitutions(self):
        assert leet(["blaze"], level=2, preserve_case=True).to_list() == ["8|423"]

    def test_extreme_level_can_lengthen_the_value(self):
        (out,) = leet(["wm"], level=3, preserve_case=True).to_list()
        assert out == "\\/\\//\\/\\"
        assert len(out) > len("wm")

    def test_level_accepts_names_and_numbers_interchangeably(self):
        for name, number in [("basic", 1), ("advanced", 2), ("extreme", 3)]:
            assert_series_equal(
                leet(["Hello World"], level=name),
                leet(["Hello World"], level=number),
            )

    def test_unsubstituted_characters_are_uppercased_by_default(self):
        assert leet(["hi there"]).to_list() == ["H1 7H3R3"]
        assert leet(["hi there"], preserve_case=True).to_list() == ["h1 7h3r3"]

    def test_nulls_are_preserved(self):
        assert leet(["a", None, "b"]).to_list() == ["4", None, "B"]

    def test_empty_string_stays_empty(self):
        assert leet([""]).to_list() == [""]

    def test_empty_column_returns_empty_column_of_right_dtype(self):
        out = leet([])
        assert out.len() == 0
        assert out.dtype == pl.String

    def test_non_ascii_passes_through(self):
        assert leet(["café"], preserve_case=True).to_list() == ["c4fé"]


class TestUnleetify:
    def test_round_trip_recovers_unambiguous_words(self):
        df = pl.DataFrame({"text": ["beast", "polars", "blaze"]})
        out = df.select(leetspeak.unleetify(leetspeak.leetify("text", level=2)))
        assert out["text"].to_list() == ["beast", "polars", "blaze"]

    def test_multi_character_glyphs_are_matched_before_single_ones(self):
        df = pl.DataFrame({"text": ["\\/\\/", "\\/", "/\\/\\", "|)", "|"]})
        out = df.select(leetspeak.unleetify("text"))
        assert out["text"].to_list() == ["w", "v", "m", "d", "l"]

    def test_case_is_not_recovered(self):
        df = pl.DataFrame({"text": ["BeAsT"]})
        out = df.select(leetspeak.unleetify(leetspeak.leetify("text", level=2)))
        assert out["text"].to_list() == ["beast"]

    def test_nulls_are_preserved(self):
        df = pl.DataFrame({"text": ["4", None]}, schema={"text": pl.String})
        assert df.select(leetspeak.unleetify("text"))["text"].to_list() == ["a", None]


class TestLeetRatio:
    def test_counts_substituted_characters(self):
        df = pl.DataFrame({"text": ["polars", "xyz", ""]})
        out = df.select(leetspeak.leet_ratio("text"))
        assert out["text"].to_list() == [0.5, 0.0, 0.0]

    def test_ratio_rises_with_level(self):
        df = pl.DataFrame({"text": ["blaze"]})
        out = df.select(
            basic=leetspeak.leet_ratio("text", level=1),
            extreme=leetspeak.leet_ratio("text", level=3),
        )
        assert out["basic"][0] < out["extreme"][0]

    def test_output_dtype_is_float64(self):
        df = pl.DataFrame({"text": ["polars"]})
        assert df.select(leetspeak.leet_ratio("text")).dtypes == [pl.Float64]

    def test_nulls_are_preserved(self):
        df = pl.DataFrame({"text": ["polars", None]}, schema={"text": pl.String})
        assert df.select(leetspeak.leet_ratio("text"))["text"].to_list() == [0.5, None]


class TestValidation:
    @pytest.mark.parametrize("level", [0, 4, -1])
    def test_out_of_range_level_is_rejected_in_python(self, level):
        with pytest.raises(ValueError, match="level must be 1, 2 or 3"):
            leetspeak.leetify("text", level=level)

    def test_unknown_level_name_is_rejected_in_python(self):
        with pytest.raises(ValueError, match="unknown level"):
            leetspeak.leetify("text", level="ultra")

    def test_rust_side_also_guards_the_level(self):
        """Bypass the Python wrapper to prove the Rust check is not decorative."""
        expr = register_plugin_function(
            plugin_path=LIB,
            function_name="leetify",
            args=[pl.col("text")],
            kwargs={"level": 9, "preserve_case": False},
            is_elementwise=True,
        )
        df = pl.DataFrame({"text": ["polars"]})
        with pytest.raises(pl.exceptions.ComputeError, match="must be 1, 2 or 3"):
            df.select(expr)

    def test_numeric_input_is_rejected(self):
        """`inputs[0].str()?` fails in Rust; the error crosses the FFI boundary
        as a ComputeError rather than crashing the process."""
        df = pl.DataFrame({"text": [1, 2, 3]})
        with pytest.raises(pl.exceptions.ComputeError):
            df.select(leetspeak.leetify("text"))


class TestIntegration:
    def test_works_in_a_lazy_query(self):
        lf = pl.LazyFrame({"text": ["polars", "pandas", "duckdb"]})
        out = (
            lf.with_columns(leet=leetspeak.leetify("text", preserve_case=True))
            .filter(pl.col("leet").str.contains("0"))
            .collect()
        )
        # Only "polars" contains an `o`, so only it gains a `0`.
        assert out["leet"].to_list() == ["p0l4r5"]

    def test_declared_elementwise_so_it_survives_slicing(self):
        """An elementwise plugin must give the same answer on a slice as on the
        whole frame; this is what `is_elementwise=True` promises the engine."""
        lf = pl.LazyFrame({"text": ["alpha", "beta", "gamma", "delta"]})
        expr = leetspeak.leetify("text", preserve_case=True)
        whole = lf.with_columns(leet=expr).collect()[1:3]
        sliced = lf.slice(1, 2).with_columns(leet=expr).collect()
        assert_frame_equal(whole, sliced)

    def test_works_inside_group_by(self):
        df = pl.DataFrame({"g": ["a", "a", "b"], "text": ["ee", "e", "oo"]})
        out = df.group_by("g").agg(leetspeak.leet_ratio("text").mean()).sort("g")
        assert out["text"].to_list() == [1.0, 1.0]

    def test_namespace_matches_the_plain_function(self):
        df = pl.DataFrame({"text": ["Hello World"]})
        assert_frame_equal(
            df.select(leetspeak.leetify("text", level=3)),
            df.select(pl.col("text").leet.leetify(level=3)),
        )

    def test_namespace_rejects_unknown_attributes(self):
        with pytest.raises(AttributeError):
            pl.col("text").leet.does_not_exist()

    def test_chained_namespace_calls(self):
        df = pl.DataFrame({"text": ["beast"]})
        out = df.select(pl.col("text").leet.leetify(level=2).leet.unleetify())
        assert out["text"].to_list() == ["beast"]
