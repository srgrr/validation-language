import argparse
import sys
from pathlib import Path

from validation_language_mockup.avl import load_avl
from validation_language_mockup.rounds import discover_round_csvs, load_round_csv


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
    return parser


def run(rounds_dir: Path, avl_file: Path) -> int:
    rounds = discover_round_csvs(rounds_dir)
    if not rounds:
        print(
            f"error: no round_N.csv files found in {rounds_dir}",
            file=sys.stderr,
        )
        return 1

    avl = load_avl(avl_file)
    loaded = [(r, load_round_csv(r.path)) for r in rounds]

    print(f"AVL: {avl.path}")
    print(f"Rounds: {len(loaded)}")
    for round_csv, rows in loaded:
        print(f"  round_{round_csv.number}.csv: {len(rows)} row(s)")

    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args.rounds_dir, args.avl_file)
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
