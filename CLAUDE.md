# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`hexamma` is a small Python 3 CLI that generates a Graphviz diagram of the current working directory's folder structure. It is intended to be run from the directory you want to visualize — `main()` calls `os.getcwd()` directly, there are no CLI arguments yet.

## Commands

Install (requires the system `graphviz` binary in addition to the Python package):

```
pip install -e .
```

This puts the `hexamma` script onto `PATH` via the `[project.scripts]` entry point in `pyproject.toml`.

Run against a target directory by `cd`-ing into it and invoking the script:

```
cd /path/to/target && hexamma
```

`python -m hexamma` works too (uses `src/hexamma/__main__.py`).

Output is rendered as PNG to the system temp dir as `tree__<basename>.png` and opened with the default viewer (`view=True` in `dot.render`).

Tests:

```
pip install -e ".[dev]"
pytest
```

There is no lint config yet.

## Architecture

Layout is a `src/`-style package:

- `src/hexamma/cli.py` — orchestration only: `main()` calls `walk()` then `to_dot()` then `dot.render()`
- `src/hexamma/tree.py` — pure: `FsNode` NamedTuple + `walk(path)` returning a deterministic tree (children sorted alphabetically)
- `src/hexamma/styling.py` — pure: `Category` enum, palette tables, `categorize` / `node_attrs` / `edge_attrs`
- `src/hexamma/render.py` — `to_dot(root)` consumes an `FsNode` tree and returns a populated `graphviz.Digraph`
- `src/hexamma/__main__.py` — module entry point
- `src/hexamma/__init__.py` — empty
- `pyproject.toml` — PEP 621 metadata, setuptools backend, `hexamma = "hexamma.cli:main"` entry point, `[dev]` extras with `pytest`
- `tests/test_tree.py` — covers `walk()` against `tmp_path` fixtures (sort order, relpath construction, file/dir mix)
- `tests/test_styling.py` — covers categorize + attr-layering semantics
- `tests/test_render.py` — covers Digraph structure (node/edge counts, IDs, labels, key styling)

The pipeline is `walk(path) -> FsNode tree -> to_dot(root) -> graphviz.Digraph -> dot.render(...)`. Each seam is independently testable: traversal needs only a temp dir, styling needs no I/O, rendering produces a Digraph whose `.source` / `.body` can be inspected without the system `dot` binary.

Two things to know to make non-trivial changes:

1. **Node identity in the Digraph is the FsNode's relpath.** Descendants always have a non-empty relpath, so they're unique; the root, whose relpath is `''`, uses the sentinel `'.'` (defined as `_ROOT_ID` in `render.py`). The graphviz Python library quotes IDs that aren't simple identifiers, so paths with `/` or `.` flow through unchanged. There is no cycle/symlink protection on traversal — a symlink loop will raise `RecursionError`. `--follow-symlinks` is planned for the CLI step.

2. **Styling is layered, last-write-wins.** `categorize(is_folder, basename)` returns a `frozenset[Category]`. `node_attrs` / `edge_attrs` apply per-category palette layers in a fixed order (`_NODE_LAYER_ORDER` / `_EDGE_LAYER_ORDER` in `styling.py`); later layers overwrite earlier ones on attr-key collisions. Adding a category means: add a `Category` member, an extension set, a `NODE_PALETTE` / `EDGE_PALETTE` entry, a clause in `categorize`, and the appropriate position in the layer-order tuples.
