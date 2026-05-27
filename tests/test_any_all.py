import polars as pl

from validation_language_mockup.avl import parse_avl
from validation_language_mockup.evaluator import validate_rule
from validation_language_mockup.parser import parse_avl as parse_avl_rule


def test_any_matches_if_any_operand_true() -> None:
    df = pl.DataFrame({"Item": ["A", "B"], "Price": [12, 13]})

    rule = parse_avl_rule(
        """\
WHEN
    ANY(COL(Price) = 12, COL(Price) = 13)
THEN
    COL(Price) = 12
GROUP BY
    \"Item\"
"""
    )

    result = validate_rule(rule, {1: df}, current_round=1)

    assert result.passed is False
    assert result.when_matched_rows == 2
    assert result.violation_rows == 1


def test_all_matches_only_if_all_operands_true() -> None:
    df = pl.DataFrame(
        {
            "Item": ["A", "B"],
            "Price": [12, 12],
            "Origin": ["Barcelona", "Madrid"],
        }
    )

    rule = parse_avl_rule(
        """\
WHEN
    ALL(COL(Price) = 12, COL(Origin) = \"Barcelona\")
THEN
    TRUE
GROUP BY
    \"Item\"
"""
    )

    result = validate_rule(rule, {1: df}, current_round=1)

    assert result.passed is True
    assert result.when_matched_rows == 1
    assert result.violation_rows == 0

