from pathlib import Path

import pytest

from validation_language_mockup.cli import main
from validation_language_mockup.evaluator import compile_rule, format_validation_pipeline
from validation_language_mockup.parser import parse_avl

MINIMAL_AVL = """\
WHEN
    TRUE
THEN
    TRUE
GROUP BY
    "id"
"""


def test_cli_runs_with_valid_inputs(tmp_path: Path) -> None:
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,value\n1,foo\n")
    avl = tmp_path / "rules.avl"
    avl.write_text(MINIMAL_AVL)

    assert main([str(csv_file), str(avl)]) == 0


def test_cli_errors_when_csv_missing(tmp_path: Path) -> None:
    avl = tmp_path / "rules.avl"
    avl.write_text(MINIMAL_AVL)

    assert main([str(tmp_path / "missing.csv"), str(avl)]) == 1


def test_cli_errors_when_avl_missing(tmp_path: Path) -> None:
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id\n1\n")

    assert main([str(csv_file), str(tmp_path / "missing.avl")]) == 1


def test_cli_errors_when_avl_wrong_extension(tmp_path: Path) -> None:
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id\n1\n")
    rules = tmp_path / "rules.txt"
    rules.write_text(MINIMAL_AVL)

    assert main([str(csv_file), str(rules)]) == 1


def test_show_polars_prints_pipeline(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id,value\n1,foo\n")
    avl = tmp_path / "rules.avl"
    avl.write_text(MINIMAL_AVL)

    assert main([str(csv_file), str(avl), "--show-polars"]) == 0

    out = capsys.readouterr().out.strip()
    rule = parse_avl(MINIMAL_AVL)
    expected = format_validation_pipeline(compile_rule(rule))
    assert out == expected
    assert "df.filter" in out
    assert ".with_columns(_then=" in out


def test_cli_requires_both_arguments(tmp_path: Path) -> None:
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("id\n1\n")

    with pytest.raises(SystemExit) as exc:
        main([str(csv_file)])
    assert exc.value.code == 2
