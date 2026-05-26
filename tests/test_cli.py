from pathlib import Path

from validation_language_mockup.cli import main
from validation_language_mockup.rounds import discover_round_csvs


def test_discover_round_csvs_sorts_by_number(tmp_path: Path) -> None:
    (tmp_path / "round_2.csv").write_text("a\n")
    (tmp_path / "round_1.csv").write_text("a\n")
    (tmp_path / "other.csv").write_text("a\n")

    rounds = discover_round_csvs(tmp_path)

    assert [r.number for r in rounds] == [1, 2]


def test_cli_runs_with_valid_inputs(tmp_path: Path) -> None:
    rounds_dir = tmp_path / "rounds"
    rounds_dir.mkdir()
    (rounds_dir / "round_1.csv").write_text("id,value\n1,foo\n")
    avl = tmp_path / "rules.avl"
    avl.write_text("assert true\n")

    assert main([str(rounds_dir), str(avl)]) == 0


def test_cli_errors_when_no_round_files(tmp_path: Path) -> None:
    rounds_dir = tmp_path / "rounds"
    rounds_dir.mkdir()
    avl = tmp_path / "rules.avl"
    avl.write_text("assert true\n")

    assert main([str(rounds_dir), str(avl)]) == 1


def test_cli_errors_when_avl_missing(tmp_path: Path) -> None:
    rounds_dir = tmp_path / "rounds"
    rounds_dir.mkdir()
    (rounds_dir / "round_1.csv").write_text("id\n1\n")

    assert main([str(rounds_dir), str(tmp_path / "missing.avl")]) == 1


def test_cli_errors_when_avl_wrong_extension(tmp_path: Path) -> None:
    rounds_dir = tmp_path / "rounds"
    rounds_dir.mkdir()
    (rounds_dir / "round_1.csv").write_text("id\n1\n")
    rules = tmp_path / "rules.txt"
    rules.write_text("assert true\n")

    assert main([str(rounds_dir), str(rules)]) == 1
