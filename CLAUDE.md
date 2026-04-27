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

There is no test suite or lint config yet.

## Architecture

Layout is a `src/`-style package:

- `src/hexamma/cli.py` — all current logic (constants, helpers, `Node`, `main`)
- `src/hexamma/__main__.py` — module entry point
- `src/hexamma/__init__.py` — empty
- `pyproject.toml` — PEP 621 metadata, setuptools backend, `hexamma = "hexamma.cli:main"` entry point

The package is built by setuptools with `[tool.setuptools.packages.find] where = ["src"]`. There is no separation between traversal, styling, and rendering yet — that's planned.

Two things to know to make non-trivial changes:

1. **Recursive node construction with side effects.** `Node.__init__` walks the filesystem and, as it constructs each child `Node`, also mutates the shared `graphviz.Digraph` passed in via `dot`. Edges from parent to child are added *after* the child is constructed (so children render their own subtree first). Node identity in the Digraph is `md5sum4(relpath)` — a 4-char MD5 prefix of the relative path — so two paths that collide on those 4 hex chars would clash. There is no cycle/symlink protection.

2. **Styling is extension-driven.** `get_node_attrs` / `get_edge_attrs` consult the module-level `SOURCES`, `CONFIGS`, `DOCS` extension lists and the `NODECOLORS` / `EDGECOLORS` palettes. Adding a new file category means extending both an extension list and the palette dicts, then adding a branch in `get_node_attrs`. Folders and dotfiles get their own branches and stack with extension-based styling (last-write-wins on conflicting attrs).
