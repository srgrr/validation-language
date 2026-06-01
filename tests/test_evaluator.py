from pathlib import Path

import polars as pl

from validation_language_mockup.avl import parse_avl_file
from validation_language_mockup.data import load_csv
from validation_language_mockup.evaluator import (
    compile_rule,
    format_validation_pipeline,
    validate_rule,
)

SAMPLE_RULE = Path("data/rules.avl")
SAMPLE_CSV = Path("data/sample.csv")


def test_compile_barcelona_rule_expressions() -> None:
    rule = parse_avl_file(SAMPLE_RULE)
    compiled = compile_rule(rule)

    df = pl.DataFrame({"Origin": ["Barcelona"], "Destination": ["Madrid"]})
    assert df.select(compiled.when).item() is True
    assert df.select(compiled.then).item() is True

    df_fail = pl.DataFrame({"Origin": ["Barcelona"], "Destination": ["Barcelona"]})
    assert df_fail.select(compiled.when).item() is True
    assert df_fail.select(compiled.then).item() is False


def test_format_validation_pipeline() -> None:
    rule = parse_avl_file(SAMPLE_RULE)
    compiled = compile_rule(rule)
    pipeline = format_validation_pipeline(compiled)

    assert pipeline.startswith("df.filter(")
    assert ".with_columns(_then=" in pipeline
    assert ".filter(~pl.col('_then'))" in pipeline
    assert "group_by('Item').agg(pl.all().first())" in pipeline


def test_validate_sample_data() -> None:
    df = load_csv(SAMPLE_CSV)
    rule = parse_avl_file(SAMPLE_RULE)

    result = validate_rule(rule, df)

    assert result.when_matched_rows > 0
    assert result.violation_rows > 0
    assert not result.passed
    assert "Item" in result.violations.columns


def test_validate_skipped_when_no_rows_match() -> None:
    from validation_language_mockup.parser import parse_avl

    df = load_csv(SAMPLE_CSV)
    rule = parse_avl(
        """\
WHEN
    COL(Origin) = "Nonexistent"
THEN
    FALSE
GROUP BY
    "Item"
"""
    )

    result = validate_rule(rule, df)

    assert result.passed
    assert result.when_matched_rows == 0
    assert result.violation_rows == 0
