use polars::prelude::*;
use pyo3_polars::derive::polars_expr;

/// Substitute a single character on the way *into* leetspeak.
///
/// Both cases of a letter fold onto the same digit, so the transformation is
/// not case-preserving. Every other character passes through untouched.
#[inline]
fn encode_char(c: char) -> char {
    match c {
        'a' | 'A' => '4',
        'b' | 'B' => '8',
        'e' | 'E' => '3',
        'g' | 'G' => '6',
        'i' | 'I' => '1',
        'o' | 'O' => '0',
        's' | 'S' => '5',
        't' | 'T' => '7',
        'z' | 'Z' => '2',
        _ => c,
    }
}

/// Substitute a single character on the way *out of* leetspeak.
///
/// Each digit has exactly one letter it came from, so decoding is
/// unambiguous; the letter produced is always lowercase.
#[inline]
fn decode_char(c: char) -> char {
    match c {
        '4' => 'a',
        '8' => 'b',
        '3' => 'e',
        '6' => 'g',
        '1' => 'i',
        '0' => 'o',
        '5' => 's',
        '7' => 't',
        '2' => 'z',
        _ => c,
    }
}

fn to_leet(value: &str, output: &mut String) {
    output.extend(value.chars().map(encode_char));
}

fn from_leet(value: &str, output: &mut String) {
    output.extend(value.chars().map(decode_char));
}

#[polars_expr(output_type=String)]
fn leetspeak(inputs: &[Series]) -> PolarsResult<Series> {
    let ca = inputs[0].str()?;
    // Amortized: reuses one output buffer instead of allocating per row.
    let out: StringChunked = ca.apply_into_string_amortized(to_leet);
    Ok(out.into_series())
}

#[polars_expr(output_type=String)]
fn unleetspeak(inputs: &[Series]) -> PolarsResult<Series> {
    let ca = inputs[0].str()?;
    let out: StringChunked = ca.apply_into_string_amortized(from_leet);
    Ok(out.into_series())
}
