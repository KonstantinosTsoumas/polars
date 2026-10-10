from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl
from polars.plugins import register_plugin_function

from leetspeak._utils import LIB

if TYPE_CHECKING:
    from leetspeak._typing import IntoExprColumn

__all__ = ["leetify", "unleetify", "leet_ratio"]

_LEVELS = {"basic": 1, "advanced": 2, "extreme": 3}


def _resolve_level(level: int | str) -> int:
    """Accept either a numeric level or its name, and fail loudly otherwise.

    Validating here means the common mistake produces a normal Python error
    with a useful message, instead of a ``ComputeError`` raised from across the
    FFI boundary once the query is already executing.
    """
    if isinstance(level, str):
        try:
            return _LEVELS[level]
        except KeyError:
            valid = ", ".join(repr(name) for name in _LEVELS)
            msg = f"unknown level {level!r}; expected one of {valid}"
            raise ValueError(msg) from None
    if level not in _LEVELS.values():
        msg = f"level must be 1, 2 or 3, got {level!r}"
        raise ValueError(msg)
    return level


def leetify(
    expr: IntoExprColumn,
    *,
    level: int | str = 1,
    preserve_case: bool = False,
) -> pl.Expr:
    """Convert a string column to leetspeak.

    Parameters
    ----------
    expr
        The string column to convert.
    level
        ``1``/``"basic"`` swaps the classic ``a e i o s t``; ``2``/``"advanced"``
        adds ``b g l z``; ``3``/``"extreme"`` adds multi-character glyphs such as
        ``w -> \\/\\/``, so the output can be longer than the input.
    preserve_case
        Keep the original case of characters that are not substituted. By
        default they are uppercased.
    """
    return register_plugin_function(
        plugin_path=LIB,
        function_name="leetify",
        args=[expr],
        kwargs={"level": _resolve_level(level), "preserve_case": preserve_case},
        is_elementwise=True,
    )


def unleetify(expr: IntoExprColumn) -> pl.Expr:
    """Convert a leetspeak column back to plain text.

    This is lossy: case is not recovered, and digits present in the original
    text are indistinguishable from substitutions.
    """
    return register_plugin_function(
        plugin_path=LIB,
        function_name="unleetify",
        args=[expr],
        is_elementwise=True,
    )


def leet_ratio(expr: IntoExprColumn, *, level: int | str = 1) -> pl.Expr:
    """Fraction of characters in each value that ``level`` would substitute."""
    return register_plugin_function(
        plugin_path=LIB,
        function_name="leet_ratio",
        args=[expr],
        # `preserve_case` is unused here but the Rust struct expects the field.
        kwargs={"level": _resolve_level(level), "preserve_case": False},
        is_elementwise=True,
    )
