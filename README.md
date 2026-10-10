# polars-leetspeak

A [Polars](https://pola.rs) expression plugin that converts string columns to and from leetspeak.
The transformation is written in Rust and dynamically linked by the Polars engine, so it runs
without the GIL and benefits from Polars' optimization and parallelism.

## Install

```bash
pip install polars-leetspeak
```

To build from source you need a Rust toolchain and [maturin](https://www.maturin.rs):

```bash
maturin develop --release
```

## Usage

```python
import polars as pl
from polars_leetspeak import leetspeak, unleetspeak

df = pl.DataFrame({"text": ["hello", "polars"]})

df.with_columns(leet=leetspeak("text"))
# ┌────────┬────────┐
# │ text   ┆ leet   │
# ╞════════╪════════╡
# │ hello  ┆ h3ll0  │
# │ polars ┆ p0l4r5 │
# └────────┴────────┘

df.with_columns(leet=leetspeak("text")).with_columns(back=unleetspeak("leet"))
```

An expression namespace is registered as well:

```python
df.with_columns(leet=pl.col("text").leet.encode())
df.with_columns(text=pl.col("leet").leet.decode())
```

## Substitutions

| letter | a | b | e | g | i | o | s | t | z |
| ------ | - | - | - | - | - | - | - | - | - |
| digit  | 4 | 8 | 3 | 6 | 1 | 0 | 5 | 7 | 2 |

Encoding is case-insensitive (`A` and `a` both become `4`) and leaves every other character
untouched. Because no two letters share a digit, decoding is unambiguous and `unleetspeak` inverts
`leetspeak` exactly for lowercase input that contained no digits of its own. Decoding always
produces lowercase letters, and digits that were part of the original text are decoded too.

## License

MIT
