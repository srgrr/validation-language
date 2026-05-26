from dataclasses import dataclass
from typing import Union

BoolExpr = Union[
    "BoolTrue",
    "BoolFalse",
    "BoolNot",
    "BoolAnd",
    "BoolOr",
    "ColExpr",
    "CurrentRoundExpr",
]


@dataclass(frozen=True)
class BoolTrue:
    pass


@dataclass(frozen=True)
class BoolFalse:
    pass


@dataclass(frozen=True)
class BoolNot:
    operand: BoolExpr


@dataclass(frozen=True)
class BoolAnd:
    left: BoolExpr
    right: BoolExpr


@dataclass(frozen=True)
class BoolOr:
    left: BoolExpr
    right: BoolExpr


@dataclass(frozen=True)
class ColExpr:
    name: str
    round: int | None = None


@dataclass(frozen=True)
class CurrentRoundExpr:
    """CURRENT_ROUND() resolved at parse time."""

    value: int


@dataclass(frozen=True)
class Rule:
    when: BoolExpr
    then: BoolExpr
    group_by: list[str]
    rounds: list[int]
