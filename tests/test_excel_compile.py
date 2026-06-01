from validation_language_mockup.excel_compile import compile_violation_formula
from validation_language_mockup.parser import parse_avl


def test_compile_barcelona_violation_formula() -> None:
    rule = parse_avl(
        """\
WHEN
    COL(Origin) = "Barcelona"
THEN
    COL(Destination) != "Barcelona"
GROUP BY
    "Item"
"""
    )
    formula = compile_violation_formula(
        rule, ["Item", "Supplier", "Description", "Price", "Origin", "Destination"]
    )

    assert formula.startswith("AND(")
    assert "NOT(" in formula
    assert 'E2="Barcelona"' in formula
    assert 'F2<>"Barcelona"' in formula or "F2<>\"Barcelona\"" in formula


def test_compile_all_equal_formula() -> None:
    rule = parse_avl(
        """\
WHEN
    TRUE
THEN
    ALL_EQUAL(COL(Price))
GROUP BY
    "Item"
"""
    )
    formula = compile_violation_formula(rule, ["Item", "Price"])

    assert "COUNTIFS" in formula
    assert "$A:$A" in formula
    assert "$B:$B" in formula
