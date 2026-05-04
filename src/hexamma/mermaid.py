"""Build a Mermaid flowchart string from an FsNode tree."""

from hexamma.styling import Category, categorize
from hexamma.tree import FsNode

_NODE_LAYER_ORDER: tuple[Category, ...] = (
    Category.FOLDER,
    Category.HIDDEN,
    Category.SOURCE,
    Category.CONFIG,
    Category.DOC,
)

_CLASS_NAMES: dict[Category, str] = {
    Category.FOLDER: 'folder_cls',
    Category.HIDDEN: 'hidden_cls',
    Category.SOURCE: 'source_cls',
    Category.CONFIG: 'config_cls',
    Category.DOC:    'doc_cls',
}
_DEFAULT_CLASS_NAME = 'default_file'

# CSS strings for each classDef line; order matches _NODE_LAYER_ORDER.
_CLASSDEFS: list[tuple[str, str]] = [
    ('folder_cls',   'fill:#ffe79c,stroke:#919191,color:#000000'),
    ('hidden_cls',   'fill:#ffffff,stroke:#b8b8b8,color:#b8b8b8'),
    ('source_cls',   'fill:#4381b3,stroke:#ffffff,color:#ffd343'),
    ('config_cls',   'fill:#e1e1e1,stroke:#919191,color:#000000'),
    ('doc_cls',      'fill:#f6f6f6,stroke:#eaa61d,color:#e96028'),
    (_DEFAULT_CLASS_NAME, 'fill:#ffffff,stroke:#919191,color:#000000'),
]


def to_mermaid(root: FsNode) -> str:
    """Return a Mermaid flowchart TD string for the given FsNode tree."""
    node_lines: list[str] = []
    edge_lines: list[str] = []
    class_lines: list[str] = []
    _collect(root, node_lines, edge_lines, class_lines)

    classdef_lines = [f'    classDef {name} {css}' for name, css in _CLASSDEFS]
    parts = ['flowchart TD', *node_lines, *edge_lines, *classdef_lines, *class_lines]
    return '\n'.join(parts) + '\n'


def _collect(
    node: FsNode,
    node_lines: list[str],
    edge_lines: list[str],
    class_lines: list[str],
) -> None:
    nid = _node_id(node)
    cats = categorize(node.is_dir, node.basename)
    label = node.basename.replace('"', '#quot;')

    if node.is_dir:
        node_lines.append(f'    {nid}(["{label}"])')
    else:
        node_lines.append(f'    {nid}["{label}"]')

    class_lines.append(f'    class {nid} {_dominant_class(cats)}')

    for child in node.children:
        child_id = _node_id(child)
        child_cats = categorize(child.is_dir, child.basename)
        arrow = '-.->' if Category.HIDDEN in child_cats else '-->'
        edge_lines.append(f'    {nid} {arrow} {child_id}')
        _collect(child, node_lines, edge_lines, class_lines)


def _node_id(node: FsNode) -> str:
    return _sanitize_id(node.relpath)


def _sanitize_id(relpath: str) -> str:
    if not relpath:
        return 'ROOT'
    s = relpath.replace('.', '_dot_').replace('/', '__').replace(' ', '_sp_')
    if s[0].isdigit():
        s = 'N' + s
    return s


def _dominant_class(categories: frozenset[Category]) -> str:
    name = _DEFAULT_CLASS_NAME
    for layer in _NODE_LAYER_ORDER:
        if layer in categories:
            name = _CLASS_NAMES[layer]
    return name
