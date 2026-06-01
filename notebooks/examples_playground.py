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
def _(Path, root):
    examples_root = root / "examples"
    example_dirs = sorted([p for p in examples_root.iterdir() if p.is_dir()])
    examples = {p.name: p for p in example_dirs}
    return example_dirs, examples, examples_root


@app.cell
def _(examples, mo):
    mo.md(
        """
        # AVL examples playground

        Pick an example, edit its AVL rule, and see the compiled Polars
        expressions plus which rows/groups fail.
        """
    )
    example_picker = mo.ui.dropdown(
        options={name: name for name in examples.keys()},
        value=next(iter(examples.keys())) if examples else None,
        label="Example",
    )
    example_picker
    return (example_picker,)


@app.cell
def _(example_picker, examples, mo):
    if example_picker.value is None:
        mo.stop()

    example_dir = examples[example_picker.value]
    rule_path = example_dir / "rule.avl"
    csv_path = example_dir / "data.csv"
    return csv_path, example_dir, rule_path


@app.cell
def _(csv_path, mo, rule_path):
    if csv_path is None or rule_path is None:
        mo.stop()

    default_rule = rule_path.read_text(encoding="utf-8")
    rule_editor = mo.ui.text_area(
        value=default_rule,
        label="AVL rule",
        full_width=True,
        rows=12,
        debounce=True,
    )
    rule_editor
    return default_rule, rule_editor


@app.cell
def _(csv_path, mo):
    if csv_path is None:
        mo.stop()
    import polars as pl

    df = pl.read_csv(csv_path)
    mo.md("### Data")
    mo.ui.table(df.to_dicts())
    return df, pl


@app.cell
def _(df, mo, rule_editor):
    from lark.exceptions import LarkError

    from validation_language_mockup.evaluator import compile_rule, validate_rule
    from validation_language_mockup.parser import parse_avl

    source = rule_editor.value
    try:
        rule = parse_avl(source)
        compiled = compile_rule(rule)
        result = validate_rule(rule, df)
        error = None
    except (ValueError, TypeError, LarkError) as exc:
        rule = None
        compiled = None
        result = None
        error = str(exc)

    return compiled, error, result, rule, source


@app.cell
def _(compiled, error, mo, rule):
    mo.md("### Compiled Polars expressions")
    if error:
        mo.callout(mo.md(f"**Error:** `{error}`"), kind="danger")
    elif rule is not None:
        mo.md(f"""
        - **GROUP BY:** {", ".join(rule.group_by)}
        - **WHEN:** `{compiled.when}`
        - **THEN:** `{compiled.then}`
        """)
    else:
        mo.md("_Waiting for a valid rule..._")


@app.cell
def _(error, mo, result):
    mo.md("### Result")
    if error:
        mo.callout(mo.md(f"**Error:** `{error}`"), kind="danger")
        mo.stop()

    status_kind = "success" if result.passed else "warn"
    status_text = (
        f"PASSED — {result.when_matched_rows} matched WHEN row(s)"
        if result.passed
        else f"FAILED — {result.violation_rows} violation group(s)"
    )
    mo.callout(mo.md(status_text), kind=status_kind)

    result_view = (
        mo.md("_No violations._")
        if result.passed
        else mo.vstack([mo.md("### Violations"), mo.ui.table(result.violations.to_dicts())])
    )
    result_view
    return


if __name__ == "__main__":
    app.run()

