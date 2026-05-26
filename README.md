# validation-language-mockup

Python mockup for a validation language.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
vlm /path/to/rounds /path/to/rules.avl
# or
python -m validation_language_mockup /path/to/rounds /path/to/rules.avl
```

`rounds` must be a folder containing `round_1.csv`, `round_2.csv`, and so on.
The second argument is the path to an `.avl` validation file.

## Tests

```bash
pytest
```

## Lint

```bash
ruff check .
ruff format .
```
