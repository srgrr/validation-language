import polars as pl

from validation_language_mockup.library import ValidationLibrary

RULE_FACTORY_PRICE = """\
WHEN
    COL(Origin) = "Factory"
THEN
    COL(Price) IS NOT NULL AND COL(Price) > 50
GROUP BY
    "Item"
"""

RULE_BARCELONA_DEST = """\
WHEN
    COL(Origin) = "Barcelona"
THEN
    COL(Destination) != "Barcelona"
GROUP BY
    "Item"
"""


def test_compile_violation_expression_evaluates_all_rules() -> None:
    df = pl.DataFrame(
        {
            "Item": ["A", "B", "C"],
            "Origin": ["Factory", "Factory", "Barcelona"],
            "Price": [55, 40, 30],
            "Destination": ["Madrid", "Madrid", "Barcelona"],
        }
    )

    expr = ValidationLibrary.compile_violation_expression(
        [RULE_FACTORY_PRICE, RULE_BARCELONA_DEST]
    )
    result = df.with_columns(expr).unnest("rule_violations")

    assert result["rule_0_violates"].to_list() == [False, True, False]
    assert result["rule_1_violates"].to_list() == [False, False, True]


def test_evaluate_dataframes_returns_one_error_df_per_input_df() -> None:
    df_one = pl.DataFrame(
        {
            "Item": ["A", "B"],
            "Origin": ["Factory", "Factory"],
            "Price": [55, 40],
            "Destination": ["Madrid", "Madrid"],
        }
    )
    df_two = pl.DataFrame(
        {
            "Item": ["C"],
            "Origin": ["Barcelona"],
            "Price": [30],
            "Destination": ["Barcelona"],
        }
    )

    errors = ValidationLibrary.evaluate_dataframes(
        [df_one, df_two],
        [RULE_FACTORY_PRICE, RULE_BARCELONA_DEST],
    )

    assert len(errors) == 2

    assert errors[0].height == 1
    assert errors[0]["Item"].to_list() == ["B"]
    assert errors[0]["_df_index"].to_list() == [0]
    assert errors[0]["_rule_index"].to_list() == [0]

    assert errors[1].height == 1
    assert errors[1]["Item"].to_list() == ["C"]
    assert errors[1]["_df_index"].to_list() == [1]
    assert errors[1]["_rule_index"].to_list() == [1]
