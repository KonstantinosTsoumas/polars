"""Register a ``leet`` namespace on ``pl.Expr``.

Importing this module enables

    pl.col("text").leet.leetify(level=2)

as an alternative to

    leetspeak.leetify("text", level=2)

Note that static type checkers will not know about the namespace, so calls are
reported as ``"Expr" has no attribute "leet"``.
"""

from __future__ import annotations

from typing import Any, Callable

import polars as pl

from leetspeak import functions


@pl.api.register_expr_namespace("leet")
class Leet:
    def __init__(self, expr: pl.Expr) -> None:
        self._expr = expr

    def __getattr__(self, attr: str) -> Callable[..., pl.Expr]:
        if attr in functions.__all__:

            def func(*args: Any, **kwargs: Any) -> pl.Expr:
                return getattr(functions, attr)(self._expr, *args, **kwargs)

            return func
        msg = f"{type(self).__name__!r} has no attribute {attr!r}"
        raise AttributeError(msg)
