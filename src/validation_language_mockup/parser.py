from dataclasses import dataclass
from importlib import resources

from lark import Lark, Token, Transformer, v_args
from lark.exceptions import VisitError

from validation_language_mockup.ast import (
    AllEqualExpr,
    BoolAnd,
    BoolExpr,
    BoolFalse,
    BoolNot,
    BoolOr,
    BoolTrue,
    ColExpr,
    CompareExpr,
    CurrentRoundExpr,
    Expr,
    IntLiteral,
    Rule,
    StringLiteral,
)


@dataclass(frozen=True)
class ParseContext:
    """Values fixed for the duration of a single parse."""

    current_round: int


def _positive_int(value: int) -> int:
    if value < 1:
        msg = f"expected a positive integer, got {value}"
        raise ValueError(msg)
    return value


def _int_value(node: IntLiteral | CurrentRoundExpr) -> int:
    return node.value


def _unquote(token: Token) -> str:
    return str(token)[1:-1]


def _load_grammar() -> str:
    return (
        resources.files("validation_language_mockup.grammar")
        .joinpath("validation.avl.lark")
        .read_text(encoding="utf-8")
    )


_lark_parser: Lark | None = None


def _parser() -> Lark:
    global _lark_parser
    if _lark_parser is None:
        _lark_parser = Lark(_load_grammar(), parser="lalr", propagate_positions=False)
    return _lark_parser


@v_args(inline=True)
class AvlTransformer(Transformer):
    def __init__(self, ctx: ParseContext) -> None:
        super().__init__()
        self._ctx = ctx

    def start(self, avl_rule: Rule) -> Rule:
        return avl_rule

    def avl_rule(self, when: BoolExpr, then: BoolExpr, group_by: list[str]) -> Rule:
        return Rule(when=when, then=then, group_by=group_by)

    def bool_true(self) -> BoolTrue:
        return BoolTrue()

    def bool_false(self) -> BoolFalse:
        return BoolFalse()

    def bool_not(self, operand: BoolExpr) -> BoolNot:
        return BoolNot(operand=operand)

    def bool_and(self, left: BoolExpr, right: BoolExpr) -> BoolAnd:
        return BoolAnd(left=left, right=right)

    def bool_or(self, left: BoolExpr, right: BoolExpr) -> BoolOr:
        return BoolOr(left=left, right=right)

    def compare_operand(self, value: Expr) -> Expr:
        return value

    def compare(self, left: Expr, op: Token, right: Expr) -> CompareExpr:
        return CompareExpr(left=left, op=str(op), right=right)  # type: ignore[arg-type]

    def all_equal_expr(self, col: ColExpr) -> AllEqualExpr:
        return AllEqualExpr(col=col)

    def col_expr(self, name: str, col_round: int | None = None) -> ColExpr:
        return ColExpr(name=name, round=col_round)

    def col_name(self, token: Token) -> str:
        return str(token)

    def col_round(self, round_expr: IntLiteral | CurrentRoundExpr) -> int:
        return round_expr.value

    def int_atom(self, value: IntLiteral | CurrentRoundExpr) -> IntLiteral | CurrentRoundExpr:
        return value

    def int_sub(
        self, left: IntLiteral | CurrentRoundExpr, right: IntLiteral
    ) -> IntLiteral:
        result = _int_value(left) - right.value
        return IntLiteral(value=_positive_int(result))

    def current_round_expr(self) -> CurrentRoundExpr:
        return CurrentRoundExpr(value=self._ctx.current_round)

    def pos_int(self, token: Token) -> IntLiteral:
        return IntLiteral(value=_positive_int(int(token)))

    def string_literal(self, token: Token) -> StringLiteral:
        return StringLiteral(value=_unquote(token))

    def str_list(self, *items: str) -> list[str]:
        return list(items)

    def str(self, token: Token) -> str:
        return _unquote(token)


def parse_avl(source: str, *, current_round: int = 1) -> Rule:
    """Parse AVL source into a Rule AST."""
    if current_round < 1:
        msg = f"current_round must be positive, got {current_round}"
        raise ValueError(msg)

    ctx = ParseContext(current_round=current_round)
    tree = _parser().parse(source)
    try:
        return AvlTransformer(ctx).transform(tree)
    except VisitError as exc:
        if isinstance(exc.orig_exc, ValueError):
            raise exc.orig_exc from None
        raise
