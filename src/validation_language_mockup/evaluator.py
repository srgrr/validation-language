from dataclasses import dataclass

import polars as pl

from validation_language_mockup.ast import (
    AllEqualExpr,
    AllExpr,
    IsNullExpr,
    BoolAnd,
    BoolExpr,
    BoolFalse,
    BoolNot,
    BoolOr,
    BoolTrue,
    AnyExpr,
    ColExpr,
    CompareExpr,
    CompareOp,
    CurrentRoundExpr,
    Expr,
    IntLiteral,
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


def compile_rule(rule: Rule, *, current_round: int) -> CompiledRule:
    """Compile WHEN/THEN clauses to Polars expressions."""
    group_by = list(rule.group_by)
    return CompiledRule(
        when=compile_bool(rule.when, current_round=current_round, group_by=group_by),
        then=compile_bool(rule.then, current_round=current_round, group_by=group_by),
        group_by=group_by,
    )


def compile_bool(
    expr: BoolExpr,
    *,
    current_round: int,
    group_by: list[str],
) -> pl.Expr:
    if isinstance(expr, BoolTrue):
        return pl.lit(True)
    if isinstance(expr, BoolFalse):
        return pl.lit(False)
    if isinstance(expr, BoolNot):
        return ~compile_bool(expr.operand, current_round=current_round, group_by=group_by)
    if isinstance(expr, BoolAnd):
        left = compile_bool(expr.left, current_round=current_round, group_by=group_by)
        right = compile_bool(expr.right, current_round=current_round, group_by=group_by)
        return left & right
    if isinstance(expr, BoolOr):
        left = compile_bool(expr.left, current_round=current_round, group_by=group_by)
        right = compile_bool(expr.right, current_round=current_round, group_by=group_by)
        return left | right
    if isinstance(expr, CompareExpr):
        left = compile_value(expr.left, current_round=current_round)
        right = compile_value(expr.right, current_round=current_round)
        return _COMPARE_OPS[expr.op](left, right)
    if isinstance(expr, AllEqualExpr):
        return compile_all_equal(expr, current_round=current_round, group_by=group_by)
    if isinstance(expr, AnyExpr):
        if not expr.operands:
            return pl.lit(False)
        compiled = compile_bool(expr.operands[0], current_round=current_round, group_by=group_by)
        for operand in expr.operands[1:]:
            compiled = compiled | compile_bool(
                operand, current_round=current_round, group_by=group_by
            )
        return compiled
    if isinstance(expr, AllExpr):
        if not expr.operands:
            return pl.lit(True)
        compiled = compile_bool(expr.operands[0], current_round=current_round, group_by=group_by)
        for operand in expr.operands[1:]:
            compiled = compiled & compile_bool(
                operand, current_round=current_round, group_by=group_by
            )
        return compiled
    if isinstance(expr, IsNullExpr):
        col_expr = compile_column(expr.col, current_round=current_round)
        return col_expr.is_not_null() if expr.negated else col_expr.is_null()
    if isinstance(expr, ColExpr):
        return compile_column(expr, current_round=current_round).is_not_null()
    if isinstance(expr, CurrentRoundExpr):
        return pl.lit(expr.value)
    if isinstance(expr, IntLiteral):
        return pl.lit(expr.value)
    if isinstance(expr, StringLiteral):
        return pl.lit(expr.value)
    msg = f"unsupported boolean expression: {type(expr).__name__}"
    raise TypeError(msg)


def compile_all_equal(
    expr: AllEqualExpr,
    *,
    current_round: int,
    group_by: list[str],
) -> pl.Expr:
    if not group_by:
        msg = "ALL_EQUAL requires at least one GROUP BY column"
        raise ValueError(msg)
    column = compile_column(expr.col, current_round=current_round)
    return column.n_unique().over(group_by) == 1


def compile_value(expr: Expr, *, current_round: int) -> pl.Expr:
    if isinstance(expr, ColExpr):
        return compile_column(expr, current_round=current_round)
    if isinstance(expr, CurrentRoundExpr):
        return pl.lit(expr.value)
    if isinstance(expr, IntLiteral):
        return pl.lit(expr.value)
    if isinstance(expr, StringLiteral):
        return pl.lit(expr.value)
    msg = f"unsupported value expression: {type(expr).__name__}"
    raise TypeError(msg)


def compile_column(col: ColExpr, *, current_round: int) -> pl.Expr:
    return pl.col(_column_name(col.name, col.round, current_round))


def _column_name(name: str, round_num: int | None, current_round: int) -> str:
    if round_num is None or round_num == current_round:
        return name
    return f"{name}__r{round_num}"


def referenced_rounds(rule: Rule, *, current_round: int) -> set[int]:
    rounds = {current_round}
    rounds.update(_rounds_in_bool(rule.when, current_round=current_round))
    rounds.update(_rounds_in_bool(rule.then, current_round=current_round))
    return rounds


def _rounds_in_bool(expr: BoolExpr, *, current_round: int) -> set[int]:
    if isinstance(expr, (BoolTrue, BoolFalse, CurrentRoundExpr, IntLiteral, StringLiteral)):
        return set()
    if isinstance(expr, BoolNot):
        return _rounds_in_bool(expr.operand, current_round=current_round)
    if isinstance(expr, (BoolAnd, BoolOr)):
        return _rounds_in_bool(expr.left, current_round=current_round) | _rounds_in_bool(
            expr.right, current_round=current_round
        )
    if isinstance(expr, CompareExpr):
        return _rounds_in_value(expr.left, current_round=current_round) | _rounds_in_value(
            expr.right, current_round=current_round
        )
    if isinstance(expr, AllEqualExpr):
        return _rounds_in_col(expr.col, current_round=current_round)
    if isinstance(expr, AnyExpr):
        rounds: set[int] = set()
        for operand in expr.operands:
            rounds |= _rounds_in_bool(operand, current_round=current_round)
        return rounds
    if isinstance(expr, AllExpr):
        rounds: set[int] = set()
        for operand in expr.operands:
            rounds |= _rounds_in_bool(operand, current_round=current_round)
        return rounds
    if isinstance(expr, IsNullExpr):
        return _rounds_in_col(expr.col, current_round=current_round)
    if isinstance(expr, ColExpr):
        return _rounds_in_col(expr, current_round=current_round)
    return set()


def _rounds_in_value(expr: Expr, *, current_round: int) -> set[int]:
    if isinstance(expr, ColExpr):
        return _rounds_in_col(expr, current_round=current_round)
    return set()


def _rounds_in_col(col: ColExpr, *, current_round: int) -> set[int]:
    if col.round is None:
        return set()
    return {col.round}


def build_eval_frame(
    rounds: dict[int, pl.DataFrame],
    *,
    current_round: int,
    group_by: list[str],
    join_rounds: set[int],
) -> pl.DataFrame:
    """Join round dataframes on GROUP BY keys for cross-round column access."""
    if current_round not in rounds:
        msg = f"round {current_round} not loaded"
        raise ValueError(msg)

    df = rounds[current_round]
    _validate_columns(df, group_by, label=f"round {current_round}")

    for round_num in sorted(join_rounds):
        if round_num == current_round:
            continue
        if round_num not in rounds:
            msg = f"round {round_num} referenced in rule but not loaded"
            raise ValueError(msg)

        other = rounds[round_num]
        _validate_columns(other, group_by, label=f"round {round_num}")

        value_cols = [c for c in other.columns if c not in group_by]
        renamed = other.select(
            group_by + [pl.col(c).alias(f"{c}__r{round_num}") for c in value_cols]
        )
        df = df.join(renamed, on=group_by, how="left")

    return df


def _validate_columns(df: pl.DataFrame, columns: list[str], *, label: str) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        msg = f"columns {missing} missing from {label}"
        raise ValueError(msg)


def validate_rule(
    rule: Rule,
    rounds: dict[int, pl.DataFrame],
    *,
    current_round: int,
) -> ValidationResult:
    """Apply WHEN filter, GROUP BY join context, and THEN validation."""
    compiled = compile_rule(rule, current_round=current_round)
    join_rounds = referenced_rounds(rule, current_round=current_round)
    df = build_eval_frame(
        rounds,
        current_round=current_round,
        group_by=compiled.group_by,
        join_rounds=join_rounds,
    )

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
