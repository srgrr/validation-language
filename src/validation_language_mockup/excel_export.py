from pathlib import Path

import polars as pl
from openpyxl import Workbook
from openpyxl.styles import PatternFill

from validation_language_mockup.evaluator import CompiledRule, row_violation_mask

_FILL_OK = PatternFill(fill_type="solid", fgColor="FFFFFF")
_FILL_VIOLATION = PatternFill(fill_type="solid", fgColor="FFC7CE")


def default_excel_path(csv_file: Path) -> Path:
    return csv_file.with_name(f"{csv_file.stem}_validated.xlsx")


def export_validation_excel(
    df: pl.DataFrame,
    compiled: CompiledRule,
    path: Path,
) -> int:
    """Write CSV rows to Excel; red background where WHEN matched and THEN failed."""
    violations = row_violation_mask(df, compiled)
    violation_count = sum(violations)

    wb = Workbook()
    ws = wb.active
    ws.title = "data"

    ws.append(df.columns)
    for row_values, is_violation in zip(df.iter_rows(), violations, strict=True):
        ws.append(list(row_values))
        row_idx = ws.max_row
        fill = _FILL_VIOLATION if is_violation else _FILL_OK
        for col_idx in range(1, len(df.columns) + 1):
            ws.cell(row=row_idx, column=col_idx).fill = fill

    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return violation_count
