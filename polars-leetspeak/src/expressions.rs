//! Polars wiring: each `#[polars_expr]` function becomes an `extern "C"` symbol
//! that the Polars engine resolves at runtime out of the compiled shared object.

use polars::prelude::*;
use pyo3_polars::derive::polars_expr;
use serde::Deserialize;

use leetspeak_core::{self as leet, Level};

/// Keyword arguments arrive from Python pickled, and are deserialised here.
///
/// The fields must line up with the `kwargs` dict passed to
/// `register_plugin_function` on the Python side; a mismatch surfaces as a
/// `ComputeError` rather than a panic.
#[derive(Deserialize)]
struct LeetKwargs {
    level: u8,
    preserve_case: bool,
}

impl LeetKwargs {
    fn level(&self) -> PolarsResult<Level> {
        Level::from_u8(self.level).ok_or_else(
            || polars_err!(ComputeError: "`level` must be 1, 2 or 3, got {}", self.level),
        )
    }
}

/// Convert a string column to leetspeak.
#[polars_expr(output_type=String)]
fn leetify(inputs: &[Series], kwargs: LeetKwargs) -> PolarsResult<Series> {
    let ca = inputs[0].str()?;
    let level = kwargs.level()?;
    let preserve_case = kwargs.preserve_case;

    // `apply_into_string_amortized` reuses one output buffer across rows rather
    // than allocating a fresh `String` per value, and preserves nulls.
    let out: StringChunked = ca.apply_into_string_amortized(|value, output| {
        leet::leetify(value, level, preserve_case, output)
    });
    Ok(out.into_series())
}

/// Best-effort conversion of a leetspeak column back to plain text.
#[polars_expr(output_type=String)]
fn unleetify(inputs: &[Series]) -> PolarsResult<Series> {
    let ca = inputs[0].str()?;
    let out: StringChunked = ca.apply_into_string_amortized(leet::unleetify);
    Ok(out.into_series())
}

/// Fraction of characters that would be substituted at the given level.
#[polars_expr(output_type=Float64)]
fn leet_ratio(inputs: &[Series], kwargs: LeetKwargs) -> PolarsResult<Series> {
    let ca = inputs[0].str()?;
    let level = kwargs.level()?;

    let out: Float64Chunked = ca
        .iter()
        .map(|opt_value| opt_value.map(|value| leet::substitution_ratio(value, level)))
        .collect_ca(ca.name().clone());
    Ok(out.into_series())
}
