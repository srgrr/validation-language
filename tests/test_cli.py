from pathlib import Path

import pytest

from validation_language_mockup.cli import main, validate_current_round
from validation_language_mockup.rounds import discover_round_csvs

MINIMAL_AVL = """\
WHEN
    TRUE
THEN
    TRUE
GROUP BY
    "id"
"""


def test_discover_round_csvs_sorts_by_number(tmp_path: Path) -> None:
    (tmp_path / "round_2.csv").write_text("a\n")
    (tmp_path / "round_1.csv").write_text("a\n")
    (tmp_path / "other.csv").write_text("a\n")

    rounds = discover_round_csvs(tmp_path)

    assert [r.number for r in rounds] == [1, 2]


def test_validate_current_round_accepts_existing_round() -> None:
    validate_current_round(2, [1, 2])


def test_validate_current_round_rejects_missing_round() -> None:
    with pytest.raises(ValueError, match="current round 3 not found"):
        validate_current_round(3, [1, 2])


def test_cli_runs_with_valid_inputs(tmp_path: Path) -> None:
    rounds_dir = tmp_path / "rounds"
    rounds_dir.mkdir()
    (rounds_dir / "round_1.csv").write_text("id,value\n1,foo\n")
    avl = tmp_path / "rules.avl"
    avl.write_text(MINIMAL_AVL)

    assert main([str(rounds_dir), str(avl), "--current-round", "1"]) == 0


def test_cli_errors_when_current_round_not_in_folder(tmp_path: Path) -> None:
    rounds_dir = tmp_path / "rounds"
    rounds_dir.mkdir()
    (rounds_dir / "round_1.csv").write_text("id,value\n1,foo\n")
    avl = tmp_path / "rules.avl"
    avl.write_text(MINIMAL_AVL)

    assert main([str(rounds_dir), str(avl), "--current-round", "2"]) == 1


def test_cli_errors_when_no_round_files(tmp_path: Path) -> None:
    rounds_dir = tmp_path / "rounds"
    rounds_dir.mkdir()
    avl = tmp_path / "rules.avl"
    avl.write_text(MINIMAL_AVL)

    assert main([str(rounds_dir), str(avl), "--current-round", "1"]) == 1


def test_cli_errors_when_avl_missing(tmp_path: Path) -> None:
    rounds_dir = tmp_path / "rounds"
    rounds_dir.mkdir()
    (rounds_dir / "round_1.csv").write_text("id\n1\n")

    assert main([str(rounds_dir), str(tmp_path / "missing.avl"), "--current-round", "1"]) == 1


def test_cli_errors_when_avl_wrong_extension(tmp_path: Path) -> None:
    rounds_dir = tmp_path / "rounds"
    rounds_dir.mkdir()
    (rounds_dir / "round_1.csv").write_text("id\n1\n")
    rules = tmp_path / "rules.txt"
    rules.write_text(MINIMAL_AVL)

    assert main([str(rounds_dir), str(rules), "--current-round", "1"]) == 1


def test_cli_requires_current_round_flag(tmp_path: Path) -> None:
    rounds_dir = tmp_path / "rounds"
    rounds_dir.mkdir()
    (rounds_dir / "round_1.csv").write_text("id\n1\n")
    avl = tmp_path / "rules.avl"
    avl.write_text(MINIMAL_AVL)

    with pytest.raises(SystemExit) as exc:
        main([str(rounds_dir), str(avl)])
    assert exc.value.code == 2
