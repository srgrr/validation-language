# validation-language-mockup

Python mockup for a validation language (AVL) that parses rules with [Lark](https://github.com/lark-parser/lark) and evaluates them against a CSV using [Polars](https://pola.rs).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
vlm /path/to/data.csv /path/to/rules.avl
# or
python -m validation_language_mockup /path/to/data.csv /path/to/rules.avl
```

| Argument | Description |
|----------|-------------|
| `data.csv` | CSV file to validate |
| `rules.avl` | AVL validation rule file |
| `--show-polars` | Print the compiled Polars violation pipeline (no validation run) |

Exit code `0` when validation passes, `1` when it fails or on error.

## AVL rule structure

Each rule has three clauses:

```text
WHEN
    <bool_expr>
THEN
    <bool_expr>
GROUP BY
    "col1", "col2"
```

| Clause | Role |
|--------|------|
| **WHEN** | Boolean filter — only rows that match are validated |
| **THEN** | Boolean constraint — must be true on every row that passed WHEN |
| **GROUP BY** | Grouping key(s) for violation reporting (e.g. `Item`) |

### Expressions

- **Literals:** `ALWAYS` / `TRUE`, `NEVER` / `FALSE`
- **Boolean ops:** `AND`, `OR`, `NOT`
- **Comparisons:** `<`, `<=`, `>`, `>=`, `=`, `!=` — between columns, integers, or quoted strings
- **Columns:** `COL(name)`
- **Null checks:** `COL(name) IS NULL` and `COL(name) IS NOT NULL`
- **Strings:** `"Madrid"` — double-quoted literals for comparisons (e.g. `COL(Origin) = "Barcelona"`)
- **Integers:** `1`, `42` — numeric literals in comparisons
- **ALL_EQUAL:** `ALL_EQUAL(COL(name))` — true when every value of the column is the same within each GROUP BY group (evaluated on rows that passed WHEN)
- **ANY / ALL:** `ANY(expr1, expr2, ...)` and `ALL(expr1, expr2, ...)` — boolean conditions over multiple expressions (evaluated like `OR` / `AND`)

Example combining column and string comparison:

```text
WHEN
    COL(Origin) = "Barcelona"
THEN
    COL(Destination) != "Barcelona"
GROUP BY
    "Item"
```

## Evaluation

The evaluator (`validation_language_mockup.evaluator`) compiles AVL to Polars expressions:

1. **WHEN** — Applied as `df.filter(when_expr)`.
2. **THEN** — Rows that matched WHEN must also satisfy `then_expr`; failures are reported per group.
3. **GROUP BY** — Violations are deduplicated to one row per group.

```python
from pathlib import Path

from validation_language_mockup.avl import parse_avl_file
from validation_language_mockup.data import load_csv
from validation_language_mockup.evaluator import compile_rule, validate_rule

df = load_csv(Path("data/sample.csv"))
rule = parse_avl_file(Path("data/rules.avl"))
compiled = compile_rule(rule)  # compiled.when, compiled.then

result = validate_rule(rule, df)
print(result.passed, result.violations)
```

## Example

Sample data: `data/sample.csv` with columns
`Item`, `Supplier`, `Description`, `Price`, `Origin`, `Destination`.

`data/rules.avl` — **when origin is Barcelona, destination must not be Barcelona:**

```text
WHEN
    COL(Origin) = "Barcelona"
THEN
    COL(Destination) != "Barcelona"
GROUP BY
    "Item"
```

Run validation:

```bash
vlm data/sample.csv data/rules.avl
```

Example output (sample data has Barcelona rows with Barcelona destinations, so validation fails):

```text
CSV: data/sample.csv
AVL: data/rules.avl
Group by: Item
Rows: 100 total, 20 matched WHEN
Validation: FAILED
Violations (8 group(s)):
...
```

## Interactive notebook

Explore rules interactively with [marimo](https://marimo.io).

**Recommended** (installs this package from the repo):

```bash
pip install -e ".[notebook]"
marimo edit notebooks/validation_demo.py
# or
marimo run notebooks/validation_demo.py
```

From the repo root with [uv](https://docs.astral.sh/uv/):

```bash
uv sync --extra notebook
uv run marimo edit notebooks/validation_demo.py
```

The notebook loads `data/sample.csv` and `data/rules.avl` by default. Edit the AVL text area and see compiled Polars expressions plus validation results update reactively.

PEP 723 metadata on the notebook only lists PyPI deps (`lark`, `polars`, `marimo`); the local package is loaded via `src/` on `sys.path`, so isolated `uv run notebooks/validation_demo.py` works without publishing to PyPI.

## Project layout

```text
notebooks/
  validation_demo.py            # Interactive AVL playground
src/validation_language_mockup/
  grammar/validation.avl.lark   # Lark grammar
  ast.py                        # Rule AST
  parser.py                     # Parser
  evaluator.py                  # AVL → Polars compilation & validation
  data.py                       # CSV loading
  cli.py                        # `vlm` entry point
data/
  sample.csv                    # Sample CSV
  rules.avl                     # Sample rule
```

## Tests

```bash
pytest
```

## Lint

```bash
ruff check .
ruff format .
```
