import polars as pl
import pytest

from validation_language_mockup.ast import AllEqualExpr, ColExpr
from validation_language_mockup.evaluator import compile_rule, validate_rule
from validation_language_mockup.parser import parse_avl


def test_parse_all_equal() -> None:
    rule = parse_avl(
        """\
WHEN
    TRUE
THEN
    ALL_EQUAL(COL(Origin))
GROUP BY
    "Item"
"""
    )
    assert isinstance(rule.then, AllEqualExpr)
    assert rule.then.col == ColExpr(name="Origin")


def test_all_equal_requires_group_by_at_compile() -> None:
    from validation_language_mockup.evaluator import compile_all_equal

    with pytest.raises(ValueError, match="GROUP BY"):
        compile_all_equal(
            AllEqualExpr(col=ColExpr(name="Origin")),
            current_round=1,
            group_by=[],
        )


def test_all_equal_passes_when_values_match() -> None:
    df = pl.DataFrame(
        {
            "Item": ["A", "A", "B"],
            "Origin": ["Madrid", "Madrid", "Barcelona"],
            "Price": [1.0, 2.0, 3.0],
        }
    )
    rule = parse_avl(
        """\
WHEN
    TRUE
THEN
    ALL_EQUAL(COL(Origin))
GROUP BY
    "Item"
"""
    )
    result = validate_rule(rule, {1: df}, current_round=1)
    assert result.passed
    assert result.when_matched_rows == 3


def test_all_equal_fails_when_values_differ() -> None:
    df = pl.DataFrame(
        {
            "Item": ["A", "A"],
            "Origin": ["Madrid", "Barcelona"],
            "Price": [1.0, 2.0],
        }
    )
    rule = parse_avl(
        """\
WHEN
    TRUE
THEN
    ALL_EQUAL(COL(Origin))
GROUP BY
    "Item"
"""
    )
    result = validate_rule(rule, {1: df}, current_round=1)
    assert not result.passed
    assert result.violation_rows == 1


def test_all_equal_evaluated_after_when_filter() -> None:
    df = pl.DataFrame(
        {
            "Item": ["A", "A", "A"],
            "Origin": ["Madrid", "Madrid", "Barcelona"],
            "Active": [1, 1, 0],
        }
    )
    rule = parse_avl(
        """\
WHEN
    COL(Active) = 1
THEN
    ALL_EQUAL(COL(Origin))
GROUP BY
    "Item"
"""
    )
    result = validate_rule(rule, {1: df}, current_round=1)
    assert result.passed
    assert result.when_matched_rows == 2


def test_compile_all_equal_expression() -> None:
    rule = parse_avl(
        """\
WHEN
    TRUE
THEN
    ALL_EQUAL(COL(Origin))
GROUP BY
    "Item"
"""
    )
    compiled = compile_rule(rule, current_round=1)
    df = pl.DataFrame({"Item": ["A", "A"], "Origin": ["X", "Y"]})
    assert df.select(compiled.then).to_series().to_list() == [False, False]
