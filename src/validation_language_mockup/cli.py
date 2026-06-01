import argparse
import sys
from pathlib import Path

from validation_language_mockup.avl import load_avl, parse_avl_file
from validation_language_mockup.data import load_csv
from validation_language_mockup.evaluator import (
    compile_rule,
    format_validation_pipeline,
    validate_rule,
)
from validation_language_mockup.excel_export import default_excel_path, export_validation_excel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validation-language-mockup",
        description="Run validation against a CSV file using an AVL rule.",
    )
    parser.add_argument(
        "csv_file",
        type=Path,
        help="Path to the CSV data file",
    )
    parser.add_argument(
        "avl_file",
        type=Path,
        help="Path to the .avl validation file",
    )
    parser.add_argument(
        "--show-polars",
        action="store_true",
        help="Print the compiled Polars violation pipeline and exit",
    )
    parser.add_argument(
        "--excel",
        nargs="?",
        const="",
        default=None,
        metavar="FILE",
        help=(
            "Write an Excel file with white rows (ok) and red rows (violation); "
            "default output: <csv_stem>_validated.xlsx"
        ),
    )
    return parser


def run(
    csv_file: Path,
    avl_file: Path,
    *,
    show_polars: bool = False,
    excel: str | None = None,
) -> int:
    if show_polars and excel is not None:
        print("error: --show-polars and --excel cannot be used together", file=sys.stderr)
        return 1

    df = load_csv(csv_file)
    avl = load_avl(avl_file)
    rule = parse_avl_file(avl_file)
    compiled = compile_rule(rule)

    if show_polars:
        print(format_validation_pipeline(compiled))
        return 0

    if excel is not None:
        excel_path = Path(excel) if excel else default_excel_path(csv_file)
        violation_rows, cf_formula = export_validation_excel(df, rule, excel_path)
        print(f"CSV: {csv_file}")
        print(f"AVL: {avl.path}")
        print(f"Excel: {excel_path}")
        print(f"Conditional formatting: {cf_formula}")
        print(f"Rows: {df.height} total, {violation_rows} violation row(s)")
        return 1 if violation_rows else 0

    result = validate_rule(rule, df)

    print(f"CSV: {csv_file}")
    print(f"AVL: {avl.path}")
    print(f"Group by: {', '.join(rule.group_by)}")
    print(f"Rows: {result.total_rows} total, {result.when_matched_rows} matched WHEN")
    print(f"Validation: {'PASSED' if result.passed else 'FAILED'}")
    if not result.passed:
        print(f"Violations ({result.violation_rows} group(s)):")
        print(result.violations)
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(
            args.csv_file,
            args.avl_file,
            show_polars=args.show_polars,
            excel=args.excel,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
