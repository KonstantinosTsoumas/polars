"""Convert Polars string columns to and from leetspeak."""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl
from polars.plugins import register_plugin_function

from polars_leetspeak._utils import LIB

if TYPE_CHECKING:
    from polars._typing import IntoExprColumn

__all__ = ["leetspeak", "unleetspeak", "LeetspeakNameSpace"]

#: The substitutions applied by :func:`leetspeak`, as ``letter -> digit``.
SUBSTITUTIONS = {
    "a": "4",
    "b": "8",
    "e": "3",
    "g": "6",
    "i": "1",
    "o": "0",
    "s": "5",
    "t": "7",
    "z": "2",
}


def leetspeak(expr: IntoExprColumn) -> pl.Expr:
    """
    Convert a string column to leetspeak.

    Letters are substituted with their digit counterparts (``a`` -> ``4``,
    ``b`` -> ``8``, ``e`` -> ``3``, ``g`` -> ``6``, ``i`` -> ``1``,
    ``o`` -> ``0``, ``s`` -> ``5``, ``t`` -> ``7``, ``z`` -> ``2``).
    Substitution is case-insensitive and every other character is left as-is.

    Parameters
    ----------
    expr
        The string column to convert.

    Examples
    --------
    >>> import polars as pl
    >>> from polars_leetspeak import leetspeak
    >>> df = pl.DataFrame({"text": ["hello", "polars"]})
    >>> df.with_columns(leet=leetspeak("text"))  # doctest: +SKIP
    """
    return register_plugin_function(
        plugin_path=LIB,
        function_name="leetspeak",
        args=expr,
        is_elementwise=True,
    )


def unleetspeak(expr: IntoExprColumn) -> pl.Expr:
    """
    Convert a leetspeak string column back to plain text.

    Each digit is substituted with the lowercase letter it stands for. Because
    the mapping has no collisions this inverts :func:`leetspeak` exactly, for
    lowercase input that contained no digits of its own.

    Parameters
    ----------
    expr
        The leetspeak column to convert back.
    """
    return register_plugin_function(
        plugin_path=LIB,
        function_name="unleetspeak",
        args=expr,
        is_elementwise=True,
    )


@pl.api.register_expr_namespace("leet")
class LeetspeakNameSpace:
    """Expression namespace, so you can write ``pl.col("text").leet.encode()``."""

    def __init__(self, expr: pl.Expr) -> None:
        self._expr = expr

    def encode(self) -> pl.Expr:
        """Convert this string expression to leetspeak."""
        return leetspeak(self._expr)

    def decode(self) -> pl.Expr:
        """Convert this leetspeak expression back to plain text."""
        return unleetspeak(self._expr)
