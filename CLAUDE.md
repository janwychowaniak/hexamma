# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`hexamma` is a single-file Python 3 script that generates a Graphviz diagram of the current working directory's folder structure. It is intended to be run from the directory you want to visualize — `main()` calls `os.getcwd()` directly, there are no CLI arguments.

## Commands

Install dependencies (requires the system `graphviz` binary in addition to the Python package):

```
pip install -r requirements.txt   # installs the `graphviz` Python package
pip install -e .                  # optional: installs the `hexamma` script via setup.py
```

Run against a target directory by `cd`-ing into it and invoking the script:

```
cd /path/to/target && /path/to/hexamma
```

Output is rendered as PNG to the system temp dir as `tree__<basename>.png` and opened with the default viewer (`view=True` in `dot.render`).

There is no test suite, lint config, or build step.

## Architecture

The whole program is the `hexamma` file (a Python script with no `.py` extension; `setup.py` ships it via `scripts=['hexamma']`, and `find_packages()` finds nothing — there is no importable package).

Two things to know to make non-trivial changes:

1. **Recursive node construction with side effects.** `Node.__init__` walks the filesystem and, as it constructs each child `Node`, also mutates the shared `graphviz.Digraph` passed in via `dot`. Edges from parent to child are added *after* the child is constructed (so children render their own subtree first). Node identity in the Digraph is `md5sum4(relpath)` — a 4-char MD5 prefix of the relative path — so two paths that collide on those 4 hex chars would clash. There is no cycle/symlink protection.

2. **Styling is extension-driven.** `get_node_attrs` / `get_edge_attrs` consult the module-level `SOURCES`, `CONFIGS`, `DOCS` extension lists and the `NODECOLORS` / `EDGECOLORS` palettes. Adding a new file category means extending both an extension list and the palette dicts, then adding a branch in `get_node_attrs`. Folders and dotfiles get their own branches and stack with extension-based styling (last-write-wins on conflicting attrs).
