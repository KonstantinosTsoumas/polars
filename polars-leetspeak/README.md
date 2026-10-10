# polars-leetspeak

A [Polars](https://pola.rs) expression plugin that converts string columns to —
and back from — leetspeak. The work happens in compiled Rust, so it runs inside
the Polars engine with no Python callback and no GIL contention.

```python
import polars as pl
import leetspeak

df = pl.DataFrame({"text": ["polars", "Hello World"]})

df.with_columns(
    leet=leetspeak.leetify("text", level=3, preserve_case=True),
    ratio=leetspeak.leet_ratio("text"),
)
# ┌─────────────┬─────────────────┬──────────┐
# │ text        ┆ leet            ┆ ratio    │
# ╞═════════════╪═════════════════╪══════════╡
# │ polars      ┆ p0|4r5          ┆ 0.5      │
# │ Hello World ┆ H3||0 \/\/0r||) ┆ 0.272727 │
# └─────────────┴─────────────────┴──────────┘
```

## Install

```bash
pip install polars-leetspeak
```

## Expressions

| Function | Output | Description |
|---|---|---|
| `leetify(expr, level=1, preserve_case=False)` | `String` | Substitute characters |
| `unleetify(expr)` | `String` | Best-effort inverse (lossy) |
| `leet_ratio(expr, level=1)` | `Float64` | Fraction of characters substituted |

`level` accepts `1`/`"basic"`, `2`/`"advanced"` or `3`/`"extreme"`:

| Level | Adds | Note |
|---|---|---|
| `basic` | `a4 e3 i1 o0 s5 t7` | output length always equals input |
| `advanced` | `b8 g9 l\| z2` | still one character in, one out |
| `extreme` | `w \/\/`, `m /\/\`, `d \|)`, … | output can be **longer** than input |

`preserve_case` keeps the case of characters that were not substituted;
by default they are uppercased.

All three expressions propagate nulls and are registered as `is_elementwise`,
so Polars is free to batch, slice and parallelise them.

### Namespace

```python
import leetspeak.extension  # noqa: F401

df.select(pl.col("text").leet.leetify(level=2).leet.unleetify())
```

Static type checkers do not know about custom namespaces, so this form will be
flagged as `"Expr" has no attribute "leet"`.

## Layout

```
core/src/lib.rs      leetspeak-core — pure logic, zero dependencies
src/expressions.rs   #[polars_expr] wrappers → extern "C" symbols
leetspeak/           Python package; the compiled .so is installed here
```

The transformation lives in its own dependency-free crate. A plugin cdylib is
built with `pyo3/extension-module`, which leaves the CPython symbols
unresolved — correct for a library that is `dlopen`ed into a running
interpreter, but it makes the crate impossible to link as a test binary. Keeping
the logic separate means `cargo test -p leetspeak-core` runs in a fraction of a
second without pyo3, Polars or Python involved.

## Development

```bash
make install-release   # build and install into .venv
make test              # Rust unit tests + Python integration tests
```

Polars caches the shared object per process, so **restart Python after every
rebuild** or the change will not be visible.

## License

MIT
