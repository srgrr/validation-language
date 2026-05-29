from pathlib import Path

from validation_language_mockup.ast import (
    BoolAnd,
    BoolFalse,
    BoolNot,
    BoolOr,
    BoolTrue,
    ColExpr,
    CompareExpr,
    IntLiteral,
    Rule,
)
from validation_language_mockup.parser import parse_avl

SAMPLE_RULE = """\
WHEN
    NOT COL(score) OR COL(score)
THEN
    ALWAYS AND NEVER
GROUP BY
    "team", "region"
"""


def test_parse_full_rule() -> None:
    rule = parse_avl(SAMPLE_RULE)

    assert isinstance(rule, Rule)
    assert rule.group_by == ["team", "region"]

    assert isinstance(rule.when, BoolOr)
    assert isinstance(rule.when.left, BoolNot)
    assert isinstance(rule.when.left.operand, ColExpr)
    assert rule.when.left.operand == ColExpr(name="score")
    assert isinstance(rule.when.right, ColExpr)
    assert rule.when.right == ColExpr(name="score")

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


def test_col_reference() -> None:
    rule = parse_avl(_minimal_when("COL(amount)"))
    assert isinstance(rule.when, ColExpr)
    assert rule.when.name == "amount"


def test_compare_int_literal() -> None:
    rule = parse_avl(_minimal_when("COL(score) > 1"))

    assert isinstance(rule.when, CompareExpr)
    assert isinstance(rule.when.left, ColExpr)
    assert rule.when.op == ">"
    assert isinstance(rule.when.right, IntLiteral)
    assert rule.when.right.value == 1


def test_parse_avl_file(tmp_path: Path) -> None:
    from validation_language_mockup.avl import parse_avl_file

    path = tmp_path / "rules.avl"
    path.write_text(SAMPLE_RULE, encoding="utf-8")
    rule = parse_avl_file(path)
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
