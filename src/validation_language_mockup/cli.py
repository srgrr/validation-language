import argparse
import sys
from pathlib import Path

from validation_language_mockup.avl import load_avl, parse_avl_file
from validation_language_mockup.data import load_csv
from validation_language_mockup.evaluator import validate_rule


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
    return parser


def run(csv_file: Path, avl_file: Path) -> int:
    df = load_csv(csv_file)
    avl = load_avl(avl_file)
    rule = parse_avl_file(avl_file)
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
        return run(args.csv_file, args.avl_file)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
