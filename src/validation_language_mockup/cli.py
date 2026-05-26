import argparse
import sys
from pathlib import Path

from validation_language_mockup.avl import load_avl, parse_avl_file
from validation_language_mockup.evaluator import validate_rule
from validation_language_mockup.rounds import load_rounds


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validation-language-mockup",
        description="Run validation against round CSV files using an AVL file.",
    )
    parser.add_argument(
        "rounds_dir",
        type=Path,
        help="Folder containing round_1.csv, round_2.csv, ...",
    )
    parser.add_argument(
        "avl_file",
        type=Path,
        help="Path to the .avl validation file",
    )
    parser.add_argument(
        "--current-round",
        type=int,
        required=True,
        metavar="N",
        help="Round number for CURRENT_ROUND() (must match an existing round_N.csv)",
    )
    return parser


def validate_current_round(current_round: int, round_numbers: list[int]) -> None:
    if current_round not in round_numbers:
        available = ", ".join(str(n) for n in round_numbers)
        msg = (
            f"current round {current_round} not found in rounds folder "
            f"(available: {available})"
        )
        raise ValueError(msg)


def run(rounds_dir: Path, avl_file: Path, *, current_round: int) -> int:
    loaded = load_rounds(rounds_dir)
    if not loaded:
        print(
            f"error: no round_N.csv files found in {rounds_dir}",
            file=sys.stderr,
        )
        return 1

    round_numbers = [r.number for r, _ in loaded]
    validate_current_round(current_round, round_numbers)

    avl = load_avl(avl_file)
    rule = parse_avl_file(avl_file, current_round=current_round)
    rounds = {r.number: df for r, df in loaded}
    result = validate_rule(rule, rounds, current_round=current_round)

    print(f"AVL: {avl.path}")
    print(f"Current round: {current_round}")
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
        return run(args.rounds_dir, args.avl_file, current_round=args.current_round)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
