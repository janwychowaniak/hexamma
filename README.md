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
pip install -r requirements.txt
pip install -e .
```

The second step puts the `hexamma` script onto your `PATH`.

## Usage

There are no arguments. `cd` into the directory you want to visualize and run:

```bash
cd /path/to/project
hexamma
```

The output PNG path is printed on stdout and the image opens in the system
default viewer.

## Customizing the styling

File categorization and colors live as module-level constants at the top of
the `hexamma` script:

- `SOURCES`, `CONFIGS`, `DOCS` — extension lists that drive categorization
- `NODECOLORS`, `EDGECOLORS` — palettes for node and edge attributes

To add a new category, extend one of the extension lists, add the
corresponding palette entries, and add a branch in `get_node_attrs`.

## License

MIT — see [LICENSE](LICENSE).
