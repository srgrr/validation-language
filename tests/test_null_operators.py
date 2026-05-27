from __future__ import annotations

import polars as pl
import pytest

from validation_language_mockup.ast import ColExpr, IsNullExpr
from validation_language_mockup.avl import parse_avl_file
from validation_language_mockup.evaluator import validate_rule
from validation_language_mockup.parser import parse_avl


def test_parse_is_null() -> None:
    rule = parse_avl(
        """\
WHEN
    COL(Origin) IS NULL
THEN
    TRUE
GROUP BY
    "Item"
"""
    )

    assert isinstance(rule.when, IsNullExpr)
    assert rule.when.col == ColExpr(name="Origin")
    assert rule.when.negated is False


def test_parse_is_not_null() -> None:
    rule = parse_avl(
        """\
WHEN
    COL(Origin) IS NOT NULL
THEN
    TRUE
GROUP BY
    "Item"
"""
    )

    assert isinstance(rule.when, IsNullExpr)
    assert rule.when.col == ColExpr(name="Origin")
    assert rule.when.negated is True


def test_validate_is_not_null_fails_on_null() -> None:
    df = pl.DataFrame({"Item": ["A", "B"], "Origin": [None, "Madrid"]})
    rule = parse_avl(
        """\
WHEN
    TRUE
THEN
    COL(Origin) IS NOT NULL
GROUP BY
    "Item"
"""
    )

    result = validate_rule(rule, {1: df}, current_round=1)
    assert result.passed is False
    assert result.when_matched_rows == 2
    assert result.violation_rows == 1
    assert "Item" in result.violations.columns


def test_validate_is_null_fails_on_non_null() -> None:
    df = pl.DataFrame({"Item": ["A", "B"], "Origin": ["Barcelona", None]})
    rule = parse_avl(
        """\
WHEN
    TRUE
THEN
    COL(Origin) IS NULL
GROUP BY
    "Item"
"""
    )

    result = validate_rule(rule, {1: df}, current_round=1)
    assert result.passed is False
    assert result.when_matched_rows == 2
    assert result.violation_rows == 1

