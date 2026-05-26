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
    rounds_dir = root / "data" / "rounds"
    default_avl = (root / "data" / "rules.avl").read_text(encoding="utf-8")
    return default_avl, rounds_dir


@app.cell
def _(rounds_dir):
    from validation_language_mockup.rounds import load_rounds

    loaded = load_rounds(rounds_dir)
    rounds = {r.number: df for r, df in loaded}
    round_options = sorted(rounds.keys())
    return load_rounds, loaded, round_options, rounds


@app.cell
def _(mo):
    mo.md("""
    # AVL validation playground

    Edit the rule below and pick a **current round**. The notebook parses the AVL,
    compiles **WHEN** / **THEN** to Polars expressions, joins rounds on **GROUP BY**
    keys, and reports violations.

    Sample CSVs: `data/rounds/round_1.csv`, `round_2.csv`.
    """)
    return


@app.cell
def _(default_avl, mo, round_options):
    avl_editor = mo.ui.text_area(
        value=default_avl,
        label="AVL rule",
        full_width=True,
        rows=14,
        debounce=True,
    )
    current_round = mo.ui.dropdown(
        options={str(n): n for n in round_options},
        value=str(round_options[-1]) if round_options else "1",
        label="Current round (CURRENT_ROUND())",
    )
    mo.vstack([avl_editor, current_round])
    return avl_editor, current_round


@app.cell
def _(avl_editor, current_round, error, result, mo):
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
                else mo.vstack([mo.md("### Violations"), mo.ui.table(result.violations.to_dicts())]),
            ]
        )
    mo.vstack([avl_editor, current_round, failed_rows_view])


@app.cell
def _(loaded, mo):
    round_tabs = mo.ui.tabs(
        {f"Round {r.number}": mo.ui.table(df) for r, df in loaded}
    )
    return (round_tabs,)


@app.cell
def _(avl_editor, current_round, mo, rounds):
    from lark.exceptions import LarkError
    from validation_language_mockup.evaluator import compile_rule, validate_rule
    from validation_language_mockup.parser import parse_avl

    cr = int(current_round.value)
    source = avl_editor.value

    try:
        rule = parse_avl(source, current_round=cr)
        compiled = compile_rule(rule, current_round=cr)
        result = validate_rule(rule, rounds, current_round=cr)
        error = None
    except (ValueError, LarkError, TypeError) as exc:
        rule = None
        compiled = None
        result = None
        error = str(exc)

    return compile_rule, compiled, cr, error, result, rule, source, validate_rule


@app.cell
def _(compiled, cr, error, mo, rule):
    if error:
        compiled_view = mo.callout(
            mo.md(f"**Parse / compile error:** `{error}`"), kind="danger"
        )
    elif rule is not None:
        compiled_view = mo.md(f"""
        ### Compiled (current round = {cr})

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
        # Keep notebook layout stable; violations panel below will show an appropriate message.
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


@app.cell
def _(error, mo, result):
    # Violations are rendered directly below the AVL textbox in the editor cell.
    # This cell intentionally stays empty to avoid duplicate/blocked rendering.
    if error or result is None:
        None
    else:
        None


@app.cell
def _(round_tabs, mo):
    mo.md("### Round data")
    round_tabs
    return


if __name__ == "__main__":
    app.run()
