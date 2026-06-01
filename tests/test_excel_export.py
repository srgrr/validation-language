from pathlib import Path

import polars as pl
from openpyxl import load_workbook

from validation_language_mockup.evaluator import compile_rule, row_violation_mask
from validation_language_mockup.excel_export import export_validation_excel
from validation_language_mockup.parser import parse_avl


def test_row_violation_mask_when_not_matched() -> None:
    df = pl.DataFrame({"Origin": ["Madrid", "Barcelona"], "Destination": ["X", "Y"]})
    rule = parse_avl(
        """\
WHEN
    COL(Origin) = "Barcelona"
THEN
    COL(Destination) = "Z"
GROUP BY
    "Origin"
"""
    )
    compiled = compile_rule(rule)
    assert row_violation_mask(df, compiled) == [False, True]


def test_export_validation_excel_uses_conditional_formatting(tmp_path: Path) -> None:
    df = pl.DataFrame(
        {
            "Origin": ["Madrid", "Barcelona"],
            "Destination": ["Madrid", "Barcelona"],
        }
    )
    rule = parse_avl(
        """\
WHEN
    COL(Origin) = "Barcelona"
THEN
    COL(Destination) != "Barcelona"
GROUP BY
    "Origin"
"""
    )
    out = tmp_path / "out.xlsx"

    count, formula = export_validation_excel(df, rule, out)

    assert count == 1
    assert out.is_file()
    assert 'A2="Barcelona"' in formula or "A2" in formula

    ws = load_workbook(out).active
    assert ws.cell(1, 1).value == "Origin"
    cf_key = next(iter(ws.conditional_formatting._cf_rules))
    assert str(cf_key.sqref) == "A2:B3"

    rule_obj = ws.conditional_formatting._cf_rules[cf_key][0]
    assert rule_obj.type == "expression"
    assert rule_obj.formula[0] == 'AND(A2="Barcelona",NOT(B2<>"Barcelona"))'
