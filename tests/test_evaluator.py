from pathlib import Path

import polars as pl

from validation_language_mockup.avl import parse_avl_file
from validation_language_mockup.evaluator import (
    compile_rule,
    validate_rule,
)
from validation_language_mockup.rounds import load_rounds

PRICE_RULE = Path("data/rules.avl")


def test_compile_price_rule_expressions() -> None:
    rule = parse_avl_file(PRICE_RULE, current_round=2)
    compiled = compile_rule(rule, current_round=2)

    df = pl.DataFrame({"Price": [10.0], "Price__r1": [12.0]})
    assert df.select(compiled.when).item() is True
    assert df.select(compiled.then).item() is True

    df_fail = pl.DataFrame({"Price": [13.0], "Price__r1": [12.0]})
    assert df_fail.select(compiled.then).item() is False


def test_validate_sample_data_round_two() -> None:
    loaded = load_rounds(Path("data/rounds"))
    rounds = {r.number: df for r, df in loaded}
    rule = parse_avl_file(PRICE_RULE, current_round=2)

    result = validate_rule(rule, rounds, current_round=2)

    assert result.when_matched_rows == 100
    assert result.violation_rows > 0
    assert not result.passed
    assert "Item" in result.violations.columns


def test_validate_skipped_on_round_one() -> None:
    from validation_language_mockup.parser import parse_avl

    loaded = load_rounds(Path("data/rounds"))
    rounds = {r.number: df for r, df in loaded}
    rule_round_one = parse_avl(
        """\
WHEN
    CURRENT_ROUND() > 1
THEN
    TRUE
GROUP BY
    "Item"
""",
        current_round=1,
    )

    result = validate_rule(rule_round_one, rounds, current_round=1)

    assert result.passed
    assert result.when_matched_rows == 0
    assert result.violation_rows == 0
