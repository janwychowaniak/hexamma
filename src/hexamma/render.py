"""Build a graphviz Digraph from an FsNode tree.

Node identity in the Digraph is the FsNode's relpath (which is unique
within a tree). The root, whose relpath is the empty string, uses the
sentinel ``'.'`` -- distinct from any descendant relpath because
descendants always have a non-empty relpath.
"""

from graphviz import Digraph

from hexamma.styling import categorize, edge_attrs, node_attrs


_ROOT_ID = '.'


def to_dot(root):
    """Return a graphviz Digraph populated from the given FsNode tree."""
    dot = Digraph(comment=f'{root.basename} folder tree')
    _add_subtree(dot, root)
    return dot


def _add_subtree(dot, node):
    src_id = _node_id(node)
    dot.node(src_id, node.basename, **node_attrs(categorize(node.is_dir, node.basename)))
    for child in node.children:
        _add_subtree(dot, child)
        dot.edge(
            src_id,
            _node_id(child),
            constraint='true',
            **edge_attrs(categorize(child.is_dir, child.basename)),
        )


def _node_id(node):
    return node.relpath if node.relpath else _ROOT_ID
