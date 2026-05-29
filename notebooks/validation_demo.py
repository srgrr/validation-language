# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "lark>=1.2",
#     "marimo>=0.11",
#     "polars>=1.0",
# ]
# ///

import marimo

__generated_with = "0.11.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import sys
    from pathlib import Path

    import marimo as mo

    root = Path(__file__).resolve().parent.parent
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    return Path, mo, root


@app.cell
def _(root):
    csv_path = root / "data" / "sample.csv"
    default_avl = (root / "data" / "rules.avl").read_text(encoding="utf-8")
    return csv_path, default_avl


@app.cell
def _(csv_path):
    from validation_language_mockup.data import load_csv

    df = load_csv(csv_path)
    return df, load_csv


@app.cell
def _(mo):
    mo.md("""
    # AVL validation playground

    Edit the rule below. The notebook parses the AVL, compiles **WHEN** / **THEN**
    to Polars expressions, and reports violations.

    Sample CSV: `data/sample.csv`.
    """)
    return


@app.cell
def _(default_avl, mo):
    avl_editor = mo.ui.text_area(
        value=default_avl,
        label="AVL rule",
        full_width=True,
        rows=14,
        debounce=True,
    )
    avl_editor
    return (avl_editor,)


@app.cell
def _(avl_editor, error, mo, result):
    if error:
        failed_rows_view = mo.callout(
            mo.md(f"**Parse / compile error:** `{error}`"), kind="danger"
        )
    elif result is None:
        failed_rows_view = mo.md("_Waiting for a valid rule..._")
    else:
        status_kind = "success" if result.passed else "warn"
        status_text = (
            f"PASSED — {result.when_matched_rows} matched WHEN row(s)"
            if result.passed
            else f"FAILED — {result.violation_rows} violation group(s)"
        )
        failed_rows_view = mo.vstack(
            [
                mo.callout(mo.md(status_text), kind=status_kind),
                mo.md("_No violations._")
                if result.passed
                else mo.vstack(
                    [
                        mo.md("### Violations"),
                        mo.ui.table(result.violations.to_dicts()),
                    ]
                ),
            ]
        )
    mo.vstack([avl_editor, failed_rows_view])


@app.cell
def _(df, mo):
    mo.md("### CSV data")
    mo.ui.table(df.to_dicts())


@app.cell
def _(avl_editor, df, mo):
    from lark.exceptions import LarkError

    from validation_language_mockup.evaluator import compile_rule, validate_rule
    from validation_language_mockup.parser import parse_avl

    source = avl_editor.value

    try:
        rule = parse_avl(source)
        compiled = compile_rule(rule)
        result = validate_rule(rule, df)
        error = None
    except (ValueError, LarkError, TypeError) as exc:
        rule = None
        compiled = None
        result = None
        error = str(exc)

    return compile_rule, compiled, error, result, rule, source, validate_rule


@app.cell
def _(compiled, error, mo, rule):
    if error:
        compiled_view = mo.callout(
            mo.md(f"**Parse / compile error:** `{error}`"), kind="danger"
        )
    elif rule is not None:
        compiled_view = mo.md(f"""
        ### Compiled

        - **GROUP BY:** {", ".join(rule.group_by)}
        - **WHEN:** `{compiled.when}`
        - **THEN:** `{compiled.then}`
        """)
    else:
        compiled_view = None
    compiled_view
    return (compiled_view,)


@app.cell
def _(error, mo, result):
    if error or result is None:
        kind, status = ("idle", "—")
    else:
        status = "PASSED" if result.passed else "FAILED"
        kind = "success" if result.passed else "warn"
        mo.callout(
            mo.md(
                f"""
                **{status}** — {result.total_rows} row(s), \
                {result.when_matched_rows} matched WHEN, \
                {result.violation_rows} violation group(s)
                """
            ),
            kind=kind,
        )
    kind, status


if __name__ == "__main__":
    app.run()
