import os
from enum import Enum, auto


class Category(Enum):
    FOLDER = auto()
    HIDDEN = auto()
    SOURCE = auto()
    CONFIG = auto()
    DOC = auto()


SOURCE_EXTS = frozenset({'.py'})
CONFIG_EXTS = frozenset({'.ini', '.yml'})
DOC_EXTS = frozenset({'.rst'})


NODE_PALETTE: dict[Category, dict[str, str]] = {
    Category.FOLDER: {
        'fillcolor': '#ffe79c',
        'style': 'filled',
        'shape': 'folder',
        'color': '#919191',
    },
    Category.HIDDEN: {
        'fontcolor': '#b8b8b8',
        'color': '#b8b8b8',
    },
    Category.SOURCE: {
        'fillcolor': '#4381b3',
        'style': 'filled,rounded',
        'fontcolor': '#ffd343',
        'color': '#ffffff',
        'shape': 'box',
    },
    Category.CONFIG: {
        'fillcolor': '#e1e1e1',
        'style': 'filled',
        'shape': 'note',
        'color': '#919191',
    },
    Category.DOC: {
        'fillcolor': '#f6f6f6',
        'fontcolor': '#e96028',
        'style': 'filled',
        'color': '#eaa61d',
        'shape': 'note',
    },
}


EDGE_DEFAULT: dict[str, str] = {'color': '#919191'}

EDGE_PALETTE: dict[Category, dict[str, str]] = {
    Category.FOLDER: {'color': '#000000'},
    Category.HIDDEN: {'color': '#b8b8b8', 'style': 'dotted', 'arrowhead': 'empty'},
}


# Layer order: later layers overwrite earlier ones on attr-key collisions.
# Mirrors the original branch order in get_node_attrs / get_edge_attrs.
_NODE_LAYER_ORDER = (
    Category.FOLDER,
    Category.HIDDEN,
    Category.SOURCE,
    Category.CONFIG,
    Category.DOC,
)
_EDGE_LAYER_ORDER = (Category.FOLDER, Category.HIDDEN)


def categorize(is_folder: bool, basename: str) -> frozenset[Category]:
    cats: set[Category] = set()
    if is_folder:
        cats.add(Category.FOLDER)
    if basename.startswith('.'):
        cats.add(Category.HIDDEN)
    ext = os.path.splitext(basename)[1].lower()
    if ext in SOURCE_EXTS:
        cats.add(Category.SOURCE)
    if ext in CONFIG_EXTS:
        cats.add(Category.CONFIG)
    if ext in DOC_EXTS:
        cats.add(Category.DOC)
    return frozenset(cats)


def node_attrs(categories: frozenset[Category]) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for layer in _NODE_LAYER_ORDER:
        if layer in categories:
            attrs.update(NODE_PALETTE[layer])
    return attrs


def edge_attrs(categories: frozenset[Category]) -> dict[str, str]:
    attrs: dict[str, str] = dict(EDGE_DEFAULT)
    for layer in _EDGE_LAYER_ORDER:
        if layer in categories:
            attrs.update(EDGE_PALETTE[layer])
    return attrs
