from pathlib import Path

import pytest

from validation_language_mockup.ast import (
    BoolAnd,
    BoolFalse,
    BoolNot,
    BoolOr,
    BoolTrue,
    ColExpr,
    CompareExpr,
    CurrentRoundExpr,
    IntLiteral,
    Rule,
)
from validation_language_mockup.parser import parse_avl

SAMPLE_RULE = """\
WHEN
    NOT COL(score, ROUND=1) OR COL(score)
THEN
    ALWAYS AND NEVER
GROUP BY
    "team", "region"
"""


def test_parse_full_rule() -> None:
    rule = parse_avl(SAMPLE_RULE, current_round=5)

    assert isinstance(rule, Rule)
    assert rule.group_by == ["team", "region"]

    assert isinstance(rule.when, BoolOr)
    assert isinstance(rule.when.left, BoolNot)
    assert isinstance(rule.when.left.operand, ColExpr)
    assert rule.when.left.operand == ColExpr(name="score", round=1)
    assert isinstance(rule.when.right, ColExpr)
    assert rule.when.right.round is None

    assert isinstance(rule.then, BoolAnd)
    assert isinstance(rule.then.left, BoolTrue)
    assert isinstance(rule.then.right, BoolFalse)


def test_bool_literals() -> None:
    for keyword in ("ALWAYS", "TRUE"):
        rule = parse_avl(_minimal_when(keyword))
        assert isinstance(rule.when, BoolTrue)

    for keyword in ("NEVER", "FALSE"):
        rule = parse_avl(_minimal_when(keyword))
        assert isinstance(rule.when, BoolFalse)


def test_current_round_resolved_at_parse_time() -> None:
    rule = parse_avl(_minimal_when("CURRENT_ROUND()"), current_round=7)
    assert isinstance(rule.when, CurrentRoundExpr)
    assert rule.when.value == 7


def test_col_without_round() -> None:
    rule = parse_avl(_minimal_when("COL(amount)"))
    assert isinstance(rule.when, ColExpr)
    assert rule.when.name == "amount"
    assert rule.when.round is None


def test_rejects_non_positive_round() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        parse_avl(_minimal_when("COL(x, ROUND=0)"))


def test_rejects_non_positive_current_round() -> None:
    with pytest.raises(ValueError, match="current_round"):
        parse_avl(_minimal_when("ALWAYS"), current_round=0)


def test_compare_current_round() -> None:
    rule = parse_avl(_minimal_when("CURRENT_ROUND() > 1"), current_round=2)

    assert isinstance(rule.when, CompareExpr)
    assert isinstance(rule.when.left, CurrentRoundExpr)
    assert rule.when.left.value == 2
    assert rule.when.op == ">"
    assert isinstance(rule.when.right, IntLiteral)
    assert rule.when.right.value == 1


def test_price_not_increase_rule() -> None:
    source = """\
WHEN
    CURRENT_ROUND() > 1
THEN
    COL(Price) <= COL(Price, ROUND=CURRENT_ROUND() - 1)
GROUP BY
    "Item"
"""
    rule = parse_avl(source, current_round=2)

    assert isinstance(rule.when, CompareExpr)
    assert isinstance(rule.then, CompareExpr)
    assert rule.then.op == "<="
    assert isinstance(rule.then.left, ColExpr)
    assert rule.then.left == ColExpr(name="Price")
    assert isinstance(rule.then.right, ColExpr)
    assert rule.then.right == ColExpr(name="Price", round=1)


def test_current_round_minus_one_undefined_on_round_one() -> None:
    source = """\
WHEN
    TRUE
THEN
    COL(Price, ROUND=CURRENT_ROUND() - 1)
GROUP BY
    "Item"
"""
    with pytest.raises(ValueError, match="positive integer"):
        parse_avl(source, current_round=1)


def test_parse_avl_file(tmp_path: Path) -> None:
    from validation_language_mockup.avl import parse_avl_file

    path = tmp_path / "rules.avl"
    path.write_text(SAMPLE_RULE, encoding="utf-8")
    rule = parse_avl_file(path, current_round=2)
    assert rule.group_by == ["team", "region"]


def _minimal_when(when_expr: str) -> str:
    return f"""\
WHEN
    {when_expr}
THEN
    TRUE
GROUP BY
    "a"
"""
