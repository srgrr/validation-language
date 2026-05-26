from pathlib import Path

import pytest

from validation_language_mockup.ast import (
    BoolAnd,
    BoolFalse,
    BoolNot,
    BoolOr,
    BoolTrue,
    ColExpr,
    CurrentRoundExpr,
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
APPLY TO ROUNDS
    1, 2, 3
"""


def test_parse_full_rule() -> None:
    rule = parse_avl(SAMPLE_RULE, current_round=5)

    assert isinstance(rule, Rule)
    assert rule.group_by == ["team", "region"]
    assert rule.rounds == [1, 2, 3]

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


def test_parse_avl_file(tmp_path: Path) -> None:
    from validation_language_mockup.avl import parse_avl_file

    path = tmp_path / "rules.avl"
    path.write_text(SAMPLE_RULE, encoding="utf-8")
    rule = parse_avl_file(path, current_round=2)
    assert rule.rounds == [1, 2, 3]


def _minimal_when(when_expr: str) -> str:
    return f"""\
WHEN
    {when_expr}
THEN
    TRUE
GROUP BY
    "a"
APPLY TO ROUNDS
    1
"""
