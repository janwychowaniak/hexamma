# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`hexamma` is a small Python 3 CLI that generates a Graphviz diagram of a directory's folder structure. It accepts a target path (defaulting to `.`) plus filtering flags (`--exclude`, `--max-depth`, `--follow-symlinks`) and output controls (`--output`, `--format`, `--no-view`).

## Commands

Install (requires the system `graphviz` binary in addition to the Python package). The project uses `uv` for env/dependency management:

```
uv sync
```

This creates `.venv/` and installs the package in editable mode. Run the CLI inside the activated venv or via `uv run hexamma`. The `hexamma` script is wired through the `[project.scripts]` entry point in `pyproject.toml`; `python -m hexamma` works too (uses `src/hexamma/__main__.py`).

Default invocation renders the current directory as PNG to the system tempdir, then opens the system viewer:

```
uv run hexamma
```

Common flag combinations:

```
hexamma path/to/proj                 # explicit target
hexamma -d 3                         # cap depth
hexamma -e '*.log' -e build          # add excludes (combined with defaults)
hexamma --no-default-excludes        # show everything (.git, __pycache__, ...)
hexamma -f svg -o out/diagram        # custom format + output path
hexamma --no-view                    # don't open the viewer (useful in CI / SSH)
hexamma -L                           # follow directory symlinks (cycles broken)
```

Tests (`uv sync` already installs the `dev` group, which includes `pytest`, `ruff`, and `mypy`):

```
uv run pytest
```

Lint and type-check:

```
uv run ruff check
uv run mypy
```

`mypy` runs in `strict` mode against `src/` and `tests/`. Test files are exempt
from `disallow_untyped_defs` / `disallow_untyped_calls` so `def test_x():`
stays untyped — listed by name in the override block in `pyproject.toml`.
Library code in `src/hexamma/` is fully annotated and the package is marked
PEP 561-typed via `src/hexamma/py.typed`.

## Architecture

Layout is a `src/`-style package:

- `src/hexamma/cli.py` — typer + orchestration: `main(argv=None)` parses flags, resolves excludes / output, then calls `walk()` → format handler → output. `DEFAULT_EXCLUDES` is loaded at import time from `excludes.toml` via `tomllib` + `importlib.resources`.
- `src/hexamma/excludes.toml` — the built-in basename exclude list, grouped by ecosystem. Add entries here as support for more languages grows.
- `src/hexamma/tree.py` — pure: `FsNode` NamedTuple + `walk(path, excludes=(), includes=(), max_depth=None, follow_symlinks=False)` returning a deterministic tree (children sorted alphabetically). Excludes and includes are fnmatch globs against basename. When following symlinks, cycles are broken via a realpath-visited set.
- `src/hexamma/styling.py` — pure: `Category` enum, palette tables, `categorize` / `node_attrs` / `edge_attrs`
- `src/hexamma/render.py` — `to_dot(root)` consumes an `FsNode` tree and returns a populated `graphviz.Digraph`
- `src/hexamma/json_output.py` — pure: `to_json(root)` serialises an `FsNode` tree to indented JSON
- `src/hexamma/__main__.py` — module entry point
- `src/hexamma/__init__.py` — empty
- `pyproject.toml` — PEP 621 metadata, hatchling build backend, `hexamma = "hexamma.cli:main"` entry point, `[dependency-groups]` with a `dev` group (`pytest`, `pytest-cov`, `ruff`, `mypy`)
- `uv.lock` — uv's resolved lockfile, committed to the repo
- `tests/test_tree.py` — covers `walk()` and its filters against `tmp_path` fixtures
- `tests/test_styling.py` — covers categorize + attr-layering semantics
- `tests/test_render.py` — covers Digraph structure (node/edge counts, IDs, labels, key styling)
- `tests/test_cli.py` — covers CLI flags, helpers, and format integration
- `tests/test_json_output.py` — covers `to_json` serialisation

The pipeline is `walk(path, ...) -> FsNode tree -> to_dot(root) -> graphviz.Digraph -> dot.render(...)`. Each seam is independently testable: traversal needs only a temp dir, styling needs no I/O, rendering produces a Digraph whose `.source` / `.body` can be inspected without the system `dot` binary, and CLI parsing is verified without invoking graphviz at all.

Three things to know to make non-trivial changes:

1. **Node identity in the Digraph is the FsNode's relpath.** Descendants always have a non-empty relpath, so they're unique; the root, whose relpath is `''`, uses the sentinel `'.'` (defined as `_ROOT_ID` in `render.py`). The graphviz Python library quotes IDs that aren't simple identifiers, so paths with `/` or `.` flow through unchanged.

2. **Styling is layered, last-write-wins.** `categorize(is_folder, basename)` returns a `frozenset[Category]`. `node_attrs` / `edge_attrs` apply per-category palette layers in a fixed order (`_NODE_LAYER_ORDER` / `_EDGE_LAYER_ORDER` in `styling.py`); later layers overwrite earlier ones on attr-key collisions. Adding a category means: add a `Category` member, an extension set, a `NODE_PALETTE` / `EDGE_PALETTE` entry, a clause in `categorize`, and the appropriate position in the layer-order tuples.

3. **Excludes and includes are basename-only fnmatch globs and never apply to the root.** `walk()` filters children before recursing, so an exclude pattern that matches a directory name short-circuits the entire subtree. Includes work the inverse way for *files only* — directories always pass the include filter so that a pattern like `*.py` still descends into subdirectories. The root is never filtered. CLI users get `DEFAULT_EXCLUDES` (`.git`, `__pycache__`, `*.egg-info`, `node_modules`, etc.) merged in unless they pass `--no-default-excludes`.
