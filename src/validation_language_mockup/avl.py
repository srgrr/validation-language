from dataclasses import dataclass
from pathlib import Path

from validation_language_mockup.ast import Rule
from validation_language_mockup.parser import parse_avl


@dataclass(frozen=True)
class AvlFile:
    path: Path
    source: str


def load_avl(path: Path) -> AvlFile:
    if not path.is_file():
        raise FileNotFoundError(f"AVL file not found: {path}")
    if path.suffix.lower() != ".avl":
        raise ValueError(f"Expected a .avl file, got: {path}")

    return AvlFile(path=path, source=path.read_text(encoding="utf-8"))


def parse_avl_file(path: Path, *, current_round: int = 1) -> Rule:
    """Load and parse an .avl file."""
    return parse_avl(load_avl(path).source, current_round=current_round)
