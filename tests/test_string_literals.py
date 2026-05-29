from pathlib import Path

import polars as pl

from validation_language_mockup.data import load_csv
from validation_language_mockup.evaluator import compile_rule, validate_rule
from validation_language_mockup.parser import parse_avl


def test_parse_string_literal_comparison() -> None:
    rule = parse_avl(
        """\
WHEN
    COL(Origin) = "Barcelona"
THEN
    TRUE
GROUP BY
    "Item"
"""
    )
    from validation_language_mockup.ast import CompareExpr, StringLiteral

    assert isinstance(rule.when, CompareExpr)
    assert isinstance(rule.when.right, StringLiteral)
    assert rule.when.right.value == "Barcelona"


def test_compile_string_comparison() -> None:
    rule = parse_avl(
        """\
WHEN
    TRUE
THEN
    COL(Origin) = "Madrid"
GROUP BY
    "Item"
"""
    )
    compiled = compile_rule(rule)
    df = pl.DataFrame({"Origin": ["Madrid", "Barcelona"]})
    assert df.select(compiled.then).to_series().to_list() == [True, False]


def test_validate_origin_barcelona() -> None:
    df = load_csv(Path("data/sample.csv"))
    rule = parse_avl(
        """\
WHEN
    TRUE
THEN
    COL(Origin) = "Barcelona" OR COL(Destination) = "Girona"
GROUP BY
    "Item"
"""
    )
    result = validate_rule(rule, df)
    assert result.when_matched_rows == 100
    assert result.violation_rows > 0
