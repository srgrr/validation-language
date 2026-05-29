# AGENTS.md — Writing AVL (Archlet Validation Language) rules

This repo is a Python mockup of **AVL**, a small validation language for expressing **row-level constraints** over a single CSV. The core flow is:

- Parse an AVL rule (Lark grammar) into an AST.
- Filter rows by `WHEN`.
- Require `THEN` to be true for every row that matched `WHEN`.
- Report violations (grouped by the `GROUP BY` keys).

If you're an agent generating rules or examples, prefer the patterns and examples below over inferring capabilities from the grammar alone.

## Rule shape (always 3 clauses)

```text
WHEN
  <bool_expr>
THEN
  <bool_expr>
GROUP BY
  "col1", "col2"
```

- **WHEN**: selects rows to validate (a boolean filter).
- **THEN**: must hold for every selected row.
- **GROUP BY**: grouping key(s) for violation reporting.

## Semantics (what "fails" means)

Given a rule and a CSV dataframe:

- Compute `when_expr`, filter to matching rows.
- Compute `then_expr` on those rows; rows where `then_expr` is false are violations.
- Violations are returned **one row per group** (first failing row per group) when `GROUP BY` is non-empty.

Important edge case: if **no rows match `WHEN`**, the validation **passes** (nothing was required).

## Column references

- `COL(Price)` refers to the `Price` column in the CSV.

### Column naming constraints

- `COL(name)` only accepts `name` matching `[A-Za-z_][A-Za-z0-9_]*`.
  - Use `Trans_Time` not `"Trans Time"`.
  - `GROUP BY` column names are **strings**, e.g. `"Item"`, but they must still correspond to actual CSV column names.

## Supported boolean expressions

### Literals

- `ALWAYS` / `TRUE`
- `NEVER` / `FALSE`

### Boolean operators

- `NOT <expr>`
- `<expr> AND <expr>`
- `<expr> OR <expr>`
- Parentheses: `( ... )`

### Comparisons

Operators: `<`, `<=`, `>`, `>=`, `=`, `!=`

Operands can be:
- `COL(...)`
- integers like `1`, `42`
- double-quoted strings like `"Something"`

Examples:

```text
COL(Origin) = "Barcelona"
COL(Price) <= 100
```

### Null checks

- `COL(X) IS NULL`
- `COL(X) IS NOT NULL`

### `ANY(...)` and `ALL(...)`

These take a comma-separated list of boolean expressions:

- `ANY(a, b, c)` is equivalent to `(a OR b OR c)`
- `ALL(a, b, c)` is equivalent to `(a AND b AND c)`

### `ALL_EQUAL(COL(...))` (group-wise uniformity)

`ALL_EQUAL(COL(Price))` is true when, **within each `GROUP BY` group**, the column has exactly one unique value **among rows that matched `WHEN`**.

Constraints:
- Requires at least one `GROUP BY` column.

## Idioms (copy-paste patterns)

### Conditional requirement (mandatory only for some rows)

```text
WHEN
  COL(Description) = "Trans"
THEN
  COL(Trans_Time) IS NOT NULL AND COL(Trans_Cost) IS NOT NULL
GROUP BY
  "Item"
```

### "If any row in a group matches, then all matched rows must satisfy"

This is the common "triggered constraint" pattern: define the trigger in `WHEN`, and the required condition in `THEN`.

```text
WHEN
  ANY(COL(Description) = "Something" AND COL(Price) IS NOT NULL)
THEN
  COL(SomethingPrice) IS NOT NULL
GROUP BY
  "Item"
```

### Group-wise uniformity

```text
WHEN
  ALWAYS
THEN
  ALL_EQUAL(COL(Price))
GROUP BY
  "Origin", "Destination"
```

## How to validate rules while developing

- **CLI**

```bash
vlm data/sample.csv data/rules.avl
```

- **Interactive notebook**

```bash
pip install -e ".[notebook]"
marimo edit notebooks/validation_demo.py
```

## Where to look in the repo

- **Grammar**: `src/validation_language_mockup/grammar/validation.avl.lark`
- **Parser**: `src/validation_language_mockup/parser.py`
- **Evaluator (semantics)**: `src/validation_language_mockup/evaluator.py`
- **Examples**: `examples/*/rule.avl` + `data.csv` (small, purpose-built datasets)
- **Sample data**: `data/sample.csv`

## Rule-authoring checklist (agent-friendly)

- **Correctness**
  - Pick `GROUP BY` keys that uniquely identify the entity you're validating (often `"Item"`).
  - Make sure all referenced columns exist in the CSV.
- **Language constraints**
  - Column identifiers in `COL(...)` must be alphanumeric/underscore (no spaces).
  - Strings in comparisons must be double-quoted (`"..."`).
- **Intended semantics**
  - If you want "only validate some rows", put that filter in `WHEN`.
  - Remember: if `WHEN` matches 0 rows, the rule passes.
