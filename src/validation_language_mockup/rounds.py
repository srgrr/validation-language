import re
from dataclasses import dataclass
from pathlib import Path

import polars as pl

ROUND_CSV_PATTERN = re.compile(r"^round_(\d+)\.csv$")


@dataclass(frozen=True)
class RoundCsv:
    number: int
    path: Path


def discover_round_csvs(folder: Path) -> list[RoundCsv]:
    """Return round_N.csv files in numeric order."""
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder}")

    rounds: list[RoundCsv] = []
    for path in folder.iterdir():
        if not path.is_file():
            continue
        match = ROUND_CSV_PATTERN.match(path.name)
        if match:
            rounds.append(RoundCsv(number=int(match.group(1)), path=path))

    rounds.sort(key=lambda r: r.number)
    return rounds


def load_round_csv(path: Path) -> pl.DataFrame:
    return pl.read_csv(path)


def load_rounds(folder: Path) -> list[tuple[RoundCsv, pl.DataFrame]]:
    """Discover and load all round CSVs as Polars DataFrames."""
    return [(r, load_round_csv(r.path)) for r in discover_round_csvs(folder)]
