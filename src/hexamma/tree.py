"""Pure filesystem traversal: produce an FsNode tree from a path.

No graphviz dependency. Children are sorted alphabetically by basename so
the resulting tree is deterministic (the rendered diagram is reproducible
for the same input).

Symlink-to-directory entries are followed (via ``os.path.isdir``); a cycle
through symlinks will raise ``RecursionError``. That is intentional for
this step -- safe symlink handling is wired in once the CLI grows
``--follow-symlinks``.
"""

import os
from typing import NamedTuple, Tuple


class FsNode(NamedTuple):
    basename: str
    relpath: str
    is_dir: bool
    children: Tuple['FsNode', ...]


def walk(path):
    """Return an FsNode tree rooted at ``path``.

    The root node has ``relpath == ''``; descendants carry a forward-slash
    (or os.sep) relative path from the root.
    """
    abs_path = os.path.abspath(path)
    root_basename = os.path.basename(abs_path) or abs_path
    return _build_node(abs_path, root_basename, '')


def _build_node(abs_path, basename, relpath):
    is_dir = os.path.isdir(abs_path)
    if is_dir:
        entries = sorted(os.listdir(abs_path))
        children = tuple(
            _build_node(
                os.path.join(abs_path, entry),
                entry,
                os.path.join(relpath, entry) if relpath else entry,
            )
            for entry in entries
        )
    else:
        children = ()
    return FsNode(
        basename=basename,
        relpath=relpath,
        is_dir=is_dir,
        children=children,
    )
