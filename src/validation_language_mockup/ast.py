from dataclasses import dataclass
from typing import Literal, Union

CompareOp = Literal["<", "<=", ">", ">=", "=", "!="]

IntExpr = Union["CurrentRoundExpr", "IntLiteral"]

Expr = Union["ColExpr", "CurrentRoundExpr", "IntLiteral", "StringLiteral"]

BoolExpr = Union[
    "BoolTrue",
    "BoolFalse",
    "BoolNot",
    "BoolAnd",
    "BoolOr",
    "CompareExpr",
    "AllEqualExpr",
    "AnyExpr",
    "AllExpr",
    "IsNullExpr",
    "ColExpr",
    "CurrentRoundExpr",
    "IntLiteral",
    "StringLiteral",
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
class CompareExpr:
    left: Expr
    op: CompareOp
    right: Expr


@dataclass(frozen=True)
class ColExpr:
    name: str
    round: int | None = None


@dataclass(frozen=True)
class AllEqualExpr:
    """True when all values of the column are equal within each GROUP BY group."""

    col: ColExpr


@dataclass(frozen=True)
class IsNullExpr:
    """True when a column is (not) null."""

    col: ColExpr
    negated: bool = False


@dataclass(frozen=True)
class AnyExpr:
    """True when any of the given boolean expressions are true."""

    operands: list[BoolExpr]


@dataclass(frozen=True)
class AllExpr:
    """True when all of the given boolean expressions are true."""

    operands: list[BoolExpr]


@dataclass(frozen=True)
class CurrentRoundExpr:
    """CURRENT_ROUND() resolved at parse time."""

    value: int


@dataclass(frozen=True)
class IntLiteral:
    value: int


@dataclass(frozen=True)
class StringLiteral:
    value: str


@dataclass(frozen=True)
class Rule:
    when: BoolExpr
    then: BoolExpr
    group_by: list[str]
