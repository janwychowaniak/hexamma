"""Pure filesystem traversal: produce an FsNode tree from a path.

No graphviz dependency. Children are sorted alphabetically by basename so
the resulting tree is deterministic (the rendered diagram is reproducible
for the same input).

``walk()`` supports basename-based exclude patterns (``fnmatch`` globs),
a ``max_depth`` cap, and an optional ``follow_symlinks`` mode with cycle
protection via realpath tracking. By default symlinks to directories are
treated as leaves, matching the convention of ``find`` / ``tree`` / ``du``.
"""

import fnmatch
import os
from collections.abc import Iterable
from typing import NamedTuple


class FsNode(NamedTuple):
    basename: str
    relpath: str
    is_dir: bool
    children: tuple['FsNode', ...]


def walk(
    path: str,
    excludes: Iterable[str] = (),
    includes: Iterable[str] = (),
    max_depth: int | None = None,
    follow_symlinks: bool = False,
) -> FsNode:
    """Return an FsNode tree rooted at ``path``.

    The root node has ``relpath == ''``; descendants carry an os.sep
    relative path from the root.

    ``excludes``: iterable of fnmatch patterns. Any directory entry whose
    basename matches at least one pattern is omitted (the root itself is
    never excluded).

    ``includes``: iterable of fnmatch patterns. When non-empty, only files
    whose basename matches at least one pattern are kept. Directories are
    always traversed regardless of includes (so a pattern like ``*.py``
    still descends into subdirectories to find Python files).

    ``max_depth``: cap on tree depth (root is depth 0). ``None`` means
    unlimited.

    ``follow_symlinks``: when ``False`` (the default) symlinks to
    directories are treated as leaves. When ``True``, they are followed,
    but cycles are broken: if a real directory is reached twice via
    symlinks, the second visit is rendered as a leaf.
    """
    abs_path = os.path.abspath(path)
    return _build_node(
        abs_path=abs_path,
        basename=os.path.basename(abs_path) or abs_path,
        relpath='',
        depth=0,
        max_depth=max_depth,
        excludes=tuple(excludes),
        includes=tuple(includes),
        follow_symlinks=follow_symlinks,
        visited=set(),
    )


def _build_node(
    abs_path: str,
    basename: str,
    relpath: str,
    depth: int,
    max_depth: int | None,
    excludes: tuple[str, ...],
    includes: tuple[str, ...],
    follow_symlinks: bool,
    visited: set[str],
) -> FsNode:
    is_dir = os.path.isdir(abs_path)
    children = _children(
        abs_path=abs_path,
        relpath=relpath,
        is_dir=is_dir,
        depth=depth,
        max_depth=max_depth,
        excludes=excludes,
        includes=includes,
        follow_symlinks=follow_symlinks,
        visited=visited,
    )
    return FsNode(basename=basename, relpath=relpath, is_dir=is_dir, children=children)


def _children(
    abs_path: str,
    relpath: str,
    is_dir: bool,
    depth: int,
    max_depth: int | None,
    excludes: tuple[str, ...],
    includes: tuple[str, ...],
    follow_symlinks: bool,
    visited: set[str],
) -> tuple[FsNode, ...]:
    if not is_dir:
        return ()
    if not follow_symlinks and os.path.islink(abs_path):
        return ()
    if max_depth is not None and depth >= max_depth:
        return ()

    real = os.path.realpath(abs_path)
    if real in visited:
        return ()
    visited.add(real)

    entries = sorted(
        entry
        for entry in os.listdir(abs_path)
        if not _is_excluded(entry, excludes)
        and _is_included(entry, includes, os.path.isdir(os.path.join(abs_path, entry)))
    )
    return tuple(
        _build_node(
            abs_path=os.path.join(abs_path, entry),
            basename=entry,
            relpath=os.path.join(relpath, entry) if relpath else entry,
            depth=depth + 1,
            max_depth=max_depth,
            excludes=excludes,
            includes=includes,
            follow_symlinks=follow_symlinks,
            visited=visited,
        )
        for entry in entries
    )


def _is_excluded(basename: str, excludes: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(basename, pattern) for pattern in excludes)


def _is_included(basename: str, includes: tuple[str, ...], is_dir: bool) -> bool:
    if not includes or is_dir:
        return True
    return any(fnmatch.fnmatch(basename, pattern) for pattern in includes)
