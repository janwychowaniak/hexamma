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

- Python 3.6+
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

```bash
pip install -e .
```

This puts the `hexamma` script onto your `PATH`.

## Usage

There are no arguments. `cd` into the directory you want to visualize and run:

```bash
cd /path/to/project
hexamma
```

The output PNG path is printed on stdout and the image opens in the system
default viewer.

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

Install with the test extras and run the suite:

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT — see [LICENSE](LICENSE).
