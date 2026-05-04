# hexamma

A small command-line utility that renders the current working directory as a
Graphviz diagram, with files color-coded by category so the shape of a project
is readable at a glance.

## What it does

Run from any directory, `hexamma` walks the tree rooted at the current working
directory and emits a PNG diagram (via Graphviz) where:

- folders use the `folder` shape with a warm fill,
- Python sources (`.py`) are rendered as filled rounded boxes,
- configs (`.ini`, `.yml`) use a pale "note" shape,
- docs (`.rst`) use a tinted "note" shape,
- hidden entries (dotfiles and dotdirs) are dimmed and connected with dotted edges.

The rendered file is written to the system temp directory as
`tree__<basename>.png` and opened with the default image viewer.

## Requirements

- Python 3.11+
- The Graphviz system binary (`dot` must be on `PATH`)
- The `graphviz` Python package

Install the system binary first. On Debian/Ubuntu:

```bash
sudo apt install graphviz
```

On macOS:

```bash
brew install graphviz
```

## Install

This project uses [uv](https://docs.astral.sh/uv/) for environment and
dependency management:

```bash
uv sync
```

That creates `.venv/` and installs the package in editable mode. Either
activate the venv or run the CLI through uv:

```bash
uv run hexamma
```

To install the script into a tool environment on your `PATH` instead:

```bash
uv tool install .
```

## Usage

By default `hexamma` renders the current directory:

```bash
hexamma
```

It accepts a path and a few flags:

```bash
hexamma path/to/project                   # render a specific directory
hexamma -d 3                              # cap depth at 3 levels
hexamma -e '*.log' -e build               # add exclude patterns
hexamma --no-default-excludes             # show .git/, __pycache__, etc.
hexamma -f svg -o ~/diagrams/proj         # write SVG to a chosen path
hexamma --no-view                         # don't open the viewer
hexamma -L                                # follow directory symlinks
```

The full flag list is `hexamma --help`. Output path is printed on stdout.

### Default excludes

To keep diagrams readable, the following basenames are excluded by default
(matched as `fnmatch` globs):

```
.git  .hg  .svn
__pycache__  *.egg-info  .pytest_cache  .mypy_cache  .ruff_cache  .tox
.venv  venv
node_modules  .next  .nuxt  .svelte-kit  .astro  .turbo
target  .bsp  .metals  .bloop  .scala-build
```

Pass `--no-default-excludes` to disable, or add your own with `-e PATTERN`
(repeatable).

## Customizing the styling

File categorization and colors live in `src/hexamma/styling.py`:

- `Category` — enum of styling categories (`FOLDER`, `HIDDEN`, `SOURCE`,
  `CONFIG`, `DOC`)
- `SOURCE_EXTS`, `CONFIG_EXTS`, `DOC_EXTS` — extension sets that drive
  categorization
- `NODE_PALETTE`, `EDGE_PALETTE` — per-category attribute layers, applied in
  the order defined by the module-level layer constants (later layers
  overwrite earlier ones on attr-key collisions)

To add a new category, add a `Category` member, add an extension set and a
palette entry, and update `categorize` plus the layer-order tuples.

## Development

`uv sync` installs the `dev` dependency group by default (`pytest`, `ruff`,
`mypy`). The usual checks:

```bash
uv run pytest
uv run ruff check
uv run mypy
```

`mypy` is configured in strict mode.

## License

MIT — see [LICENSE](LICENSE).
