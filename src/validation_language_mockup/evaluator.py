from dataclasses import dataclass

import polars as pl

from validation_language_mockup.ast import (
    AllEqualExpr,
    AllExpr,
    AnyExpr,
    BoolAnd,
    BoolExpr,
    BoolFalse,
    BoolNot,
    BoolOr,
    BoolTrue,
    ColExpr,
    CompareExpr,
    CompareOp,
    Expr,
    IntLiteral,
    IsNullExpr,
    Rule,
    StringLiteral,
)

_COMPARE_OPS: dict[CompareOp, type] = {
    "<": pl.Expr.lt,
    "<=": pl.Expr.le,
    ">": pl.Expr.gt,
    ">=": pl.Expr.ge,
    "=": pl.Expr.eq,
    "!=": pl.Expr.ne,
}


@dataclass(frozen=True)
class CompiledRule:
    """Polars expressions compiled from an AVL rule."""

    when: pl.Expr
    then: pl.Expr
    group_by: list[str]


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    total_rows: int
    when_matched_rows: int
    violation_rows: int
    violations: pl.DataFrame


def compile_rule(rule: Rule) -> CompiledRule:
    """Compile WHEN/THEN clauses to Polars expressions."""
    group_by = list(rule.group_by)
    return CompiledRule(
        when=compile_bool(rule.when, group_by=group_by),
        then=compile_bool(rule.then, group_by=group_by),
        group_by=group_by,
    )


def compile_bool(
    expr: BoolExpr,
    *,
    group_by: list[str],
) -> pl.Expr:
    if isinstance(expr, BoolTrue):
        return pl.lit(True)
    if isinstance(expr, BoolFalse):
        return pl.lit(False)
    if isinstance(expr, BoolNot):
        return ~compile_bool(expr.operand, group_by=group_by)
    if isinstance(expr, BoolAnd):
        left = compile_bool(expr.left, group_by=group_by)
        right = compile_bool(expr.right, group_by=group_by)
        return left & right
    if isinstance(expr, BoolOr):
        left = compile_bool(expr.left, group_by=group_by)
        right = compile_bool(expr.right, group_by=group_by)
        return left | right
    if isinstance(expr, CompareExpr):
        left = compile_value(expr.left)
        right = compile_value(expr.right)
        return _COMPARE_OPS[expr.op](left, right)
    if isinstance(expr, AllEqualExpr):
        return compile_all_equal(expr, group_by=group_by)
    if isinstance(expr, AnyExpr):
        if not expr.operands:
            return pl.lit(False)
        compiled = compile_bool(expr.operands[0], group_by=group_by)
        for operand in expr.operands[1:]:
            compiled = compiled | compile_bool(operand, group_by=group_by)
        return compiled
    if isinstance(expr, AllExpr):
        if not expr.operands:
            return pl.lit(True)
        compiled = compile_bool(expr.operands[0], group_by=group_by)
        for operand in expr.operands[1:]:
            compiled = compiled & compile_bool(operand, group_by=group_by)
        return compiled
    if isinstance(expr, IsNullExpr):
        col_expr = compile_column(expr.col)
        return col_expr.is_not_null() if expr.negated else col_expr.is_null()
    if isinstance(expr, ColExpr):
        return compile_column(expr).is_not_null()
    if isinstance(expr, IntLiteral):
        return pl.lit(expr.value)
    if isinstance(expr, StringLiteral):
        return pl.lit(expr.value)
    msg = f"unsupported boolean expression: {type(expr).__name__}"
    raise TypeError(msg)


def compile_all_equal(
    expr: AllEqualExpr,
    *,
    group_by: list[str],
) -> pl.Expr:
    if not group_by:
        msg = "ALL_EQUAL requires at least one GROUP BY column"
        raise ValueError(msg)
    column = compile_column(expr.col)
    return column.n_unique().over(group_by) == 1


def compile_value(expr: Expr) -> pl.Expr:
    if isinstance(expr, ColExpr):
        return compile_column(expr)
    if isinstance(expr, IntLiteral):
        return pl.lit(expr.value)
    if isinstance(expr, StringLiteral):
        return pl.lit(expr.value)
    msg = f"unsupported value expression: {type(expr).__name__}"
    raise TypeError(msg)


def compile_column(col: ColExpr) -> pl.Expr:
    return pl.col(col.name)


def _validate_columns(df: pl.DataFrame, columns: list[str]) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        msg = f"columns {missing} missing from CSV"
        raise ValueError(msg)


def validate_rule(rule: Rule, df: pl.DataFrame) -> ValidationResult:
    """Apply WHEN filter and THEN validation on a single CSV dataframe."""
    compiled = compile_rule(rule)
    _validate_columns(df, compiled.group_by)

    when_matched = df.filter(compiled.when)
    if when_matched.height == 0:
        return ValidationResult(
            passed=True,
            total_rows=df.height,
            when_matched_rows=0,
            violation_rows=0,
            violations=when_matched,
        )

    when_matched = when_matched.with_columns(_then=compiled.then)
    violations = when_matched.filter(~pl.col("_then"))

    if violations.height > 0 and compiled.group_by:
        violations = violations.group_by(compiled.group_by).agg(pl.all().first())

    drop_cols = [c for c in ("_then",) if c in violations.columns]
    if drop_cols:
        violations = violations.drop(*drop_cols)

    return ValidationResult(
        passed=violations.height == 0,
        total_rows=df.height,
        when_matched_rows=when_matched.height,
        violation_rows=violations.height,
        violations=violations,
    )
