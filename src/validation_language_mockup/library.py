from dataclasses import dataclass

import polars as pl

from validation_language_mockup.ast import Rule
from validation_language_mockup.evaluator import compile_rule, validate_rule
from validation_language_mockup.parser import parse_avl


@dataclass(frozen=True)
class LibraryRule:
    """Normalized AVL rule for library-level batch evaluation."""

    source: str
    parsed: Rule


class ValidationLibrary:
    """Public interface for programmatic, batch AVL evaluation."""

    @staticmethod
    def compile_violation_expression(avl_rules: list[str | Rule]) -> pl.Expr:
        """Return one struct expression with per-rule violation flags.

        Each struct field is a boolean expression where:
        - True => row violates that rule (matched WHEN and failed THEN)
        - False => row is valid for that rule
        """
        normalized_rules = _normalize_rules(avl_rules)
        compiled_exprs = []
        for index, normalized_rule in enumerate(normalized_rules):
            compiled = compile_rule(normalized_rule.parsed)
            violation_expr = (compiled.when & ~compiled.then).alias(
                f"rule_{index}_violates"
            )
            compiled_exprs.append(violation_expr)
        return pl.struct(*compiled_exprs).alias("rule_violations")

    @staticmethod
    def evaluate_dataframes(
        dfs: list[pl.DataFrame],
        avl_rules: list[str | Rule],
    ) -> list[pl.DataFrame]:
        """Evaluate each dataframe against all rules and return error dataframes.

        The returned list aligns with the input `dfs` order. Each dataframe contains
        only violation rows and these metadata columns:
        - `_df_index`
        - `_rule_index`
        - `_rule_source`
        """
        normalized_rules = _normalize_rules(avl_rules)
        all_errors: list[pl.DataFrame] = []

        for df_index, df in enumerate(dfs):
            violations_for_df: list[pl.DataFrame] = []
            for rule_index, normalized_rule in enumerate(normalized_rules):
                result = validate_rule(normalized_rule.parsed, df)
                if result.violations.height == 0:
                    continue

                violations_for_df.append(
                    result.violations.with_columns(
                        pl.lit(df_index).alias("_df_index"),
                        pl.lit(rule_index).alias("_rule_index"),
                        pl.lit(normalized_rule.source).alias("_rule_source"),
                    )
                )

            if violations_for_df:
                all_errors.append(pl.concat(violations_for_df, how="diagonal_relaxed"))
            else:
                all_errors.append(
                    pl.DataFrame(
                        schema={
                            "_df_index": pl.Int64,
                            "_rule_index": pl.Int64,
                            "_rule_source": pl.String,
                        }
                    )
                )

        return all_errors


def _normalize_rules(avl_rules: list[str | Rule]) -> list[LibraryRule]:
    normalized_rules: list[LibraryRule] = []
    for avl_rule in avl_rules:
        if isinstance(avl_rule, Rule):
            normalized_rules.append(LibraryRule(source="<rule-ast>", parsed=avl_rule))
            continue
        normalized_rules.append(LibraryRule(source=avl_rule, parsed=parse_avl(avl_rule)))
    return normalized_rules
