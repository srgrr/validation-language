# validation-language-mockup

Python mockup for a validation language (AVL) that parses rules with [Lark](https://github.com/lark-parser/lark) and evaluates them against multi-round CSV data using [Polars](https://pola.rs).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
vlm /path/to/rounds /path/to/rules.avl --current-round N
# or
python -m validation_language_mockup /path/to/rounds /path/to/rules.avl --current-round N
```

| Argument | Description |
|----------|-------------|
| `rounds` | Folder with `round_1.csv`, `round_2.csv`, … |
| `rules.avl` | AVL validation rule file |
| `--current-round N` | Value for `CURRENT_ROUND()` when parsing; `N` must match an existing `round_N.csv` |

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
| **GROUP BY** | Join key(s) across round CSVs (e.g. `Item`) |

### Expressions

- **Literals:** `ALWAYS` / `TRUE`, `NEVER` / `FALSE`
- **Boolean ops:** `AND`, `OR`, `NOT`
- **Comparisons:** `<`, `<=`, `>`, `>=`, `=`, `!=` — between columns, integers, or quoted strings
- **Columns:** `COL(name)` — current round; `COL(name, ROUND=N)` — round `N`
- **Strings:** `"Madrid"` — double-quoted literals for comparisons (e.g. `COL(Origin) = "Barcelona"`)
- **Integers:** `1`, `42` — numeric literals in comparisons
- **Round:** `CURRENT_ROUND()` — set by `--current-round`; `CURRENT_ROUND() - 1` in `ROUND=` (resolved at parse time)
- **ALL_EQUAL:** `ALL_EQUAL(COL(name))` — true when every value of the column is the same within each GROUP BY group (evaluated on rows that passed WHEN)

Example combining column and string comparison:

```text
WHEN
    CURRENT_ROUND() > 1
THEN
    COL(Price) <= COL(Price, ROUND=CURRENT_ROUND() - 1) AND COL(Destination) != "Barcelona"
GROUP BY
    "Item"
```

## Evaluation

The evaluator (`validation_language_mockup.evaluator`) compiles AVL to Polars expressions:

1. **GROUP BY** — Joins round dataframes on the group keys. Current-round columns keep their names; other rounds are suffixed (`Price__r1`, `Origin__r2`, …).
2. **WHEN** — Applied as `df.filter(when_expr)`.
3. **THEN** — Rows that matched WHEN must also satisfy `then_expr`; failures are reported per group.

```python
from pathlib import Path

from validation_language_mockup.avl import parse_avl_file
from validation_language_mockup.evaluator import compile_rule, validate_rule
from validation_language_mockup.rounds import load_rounds

loaded = load_rounds(Path("data/rounds"))
rounds = {r.number: df for r, df in loaded}

rule = parse_avl_file(Path("data/rules.avl"), current_round=2)
compiled = compile_rule(rule, current_round=2)  # compiled.when, compiled.then

result = validate_rule(rule, rounds, current_round=2)
print(result.passed, result.violations)
```

## Example

Sample data: `data/rounds/` (`round_1.csv`, `round_2.csv`) with columns
`Item`, `Supplier`, `Description`, `Price`, `Origin`, `Destination`.

`data/rules.avl` — **when the current round is greater than 1, each item's price must be less than or equal to its price in the previous round:**

```text
WHEN
    CURRENT_ROUND() > 1
THEN
    COL(Price) <= COL(Price, ROUND=CURRENT_ROUND() - 1)
GROUP BY
    "Item"
```

Run validation for round 2:

```bash
vlm data/rounds data/rules.avl --current-round 2
```

Example output (sample data has price increases in round 2, so validation fails):

```text
AVL: data/rules.avl
Current round: 2
Group by: Item
Rows: 10 total, 10 matched WHEN
Validation: FAILED
Violations (8 group(s)):
...
```

With `--current-round 1`, `WHEN` is false for every row, so nothing is validated and the run passes.

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

The notebook loads `data/rounds/` and `data/rules.avl` by default. Edit the AVL text area, change the current round, and see compiled Polars expressions plus validation results update reactively.

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
  rounds.py                     # CSV loading
  cli.py                        # `vlm` entry point
data/
  rounds/                       # Sample CSVs
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
