import importlib.metadata
import importlib.resources
import os
import sys
import tempfile
import tomllib
from collections.abc import Sequence
from typing import Annotated

import typer

from hexamma.render import to_dot
from hexamma.tree import FsNode, walk


def _load_default_excludes() -> tuple[str, ...]:
    ref = importlib.resources.files('hexamma').joinpath('excludes.toml')
    with ref.open('rb') as f:
        return tuple(tomllib.load(f)['excludes']['patterns'])


DEFAULT_EXCLUDES: tuple[str, ...] = _load_default_excludes()

app = typer.Typer(add_completion=False)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(importlib.metadata.version('hexamma'))
        raise typer.Exit()


def _resolve_excludes(exclude: list[str], no_default_excludes: bool) -> list[str]:
    excludes = list(exclude)
    if not no_default_excludes:
        excludes.extend(DEFAULT_EXCLUDES)
    return excludes


def _resolve_output(output: str | None, root_basename: str) -> tuple[str, str]:
    if output is None:
        return tempfile.gettempdir(), f'tree__{root_basename}'
    directory = os.path.dirname(output) or '.'
    filename = os.path.splitext(os.path.basename(output))[0]
    return directory, filename


def _count_tree(node: FsNode) -> tuple[int, int]:
    files = dirs = 0
    for child in node.children:
        if child.is_dir:
            dirs += 1
            f, d = _count_tree(child)
            files += f
            dirs += d
        else:
            files += 1
    return files, dirs


def _run_json(output: str | None, root: FsNode) -> None:
    from hexamma.json_output import to_json

    text = to_json(root)
    if output is None:
        print(text)
        return
    directory, stem = _resolve_output(output, root.basename)
    out_path = os.path.join(directory, stem + '.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(out_path)


def _run_mermaid(output: str | None, root: FsNode) -> None:
    from hexamma.mermaid import to_mermaid

    text = to_mermaid(root)
    directory, stem = _resolve_output(output, root.basename)
    out_path = os.path.join(directory, stem + '.mmd')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(out_path)


@app.command()
def _command(
    version: Annotated[
        bool,
        typer.Option(
            '--version',
            callback=_version_callback,
            is_eager=True,
            help='Show version and exit.',
        ),
    ] = False,
    path: Annotated[
        str,
        typer.Argument(help='Directory (or file) to visualize. Default: current directory.'),
    ] = '.',
    exclude: Annotated[
        list[str] | None,
        typer.Option(
            '-e',
            '--exclude',
            help='fnmatch pattern to exclude (basename). Repeatable. '
            'Combined with default excludes unless --no-default-excludes.',
        ),
    ] = None,
    no_default_excludes: Annotated[
        bool,
        typer.Option(
            '--no-default-excludes',
            help='Disable built-in exclude list (.git, __pycache__, node_modules, ...).',
        ),
    ] = False,
    max_depth: Annotated[
        int | None,
        typer.Option(
            '-d', '--max-depth', help='Maximum tree depth (root is depth 0). Default: unlimited.'
        ),
    ] = None,
    output: Annotated[
        str | None,
        typer.Option(
            '-o',
            '--output',
            help='Output file path (extension replaced by --format). '
            'Default: <tempdir>/tree__<basename>.<format>.',
        ),
    ] = None,
    fmt: Annotated[
        str,
        typer.Option(
            '-f',
            '--format',
            help='Output format: "mermaid" for .mmd, or any graphviz format '
            '(png, svg, pdf, dot, ...). Default: png.',
        ),
    ] = 'png',
    no_view: Annotated[
        bool,
        typer.Option('--no-view', help='Do not open the rendered file in the default viewer.'),
    ] = False,
    include: Annotated[
        list[str] | None,
        typer.Option(
            '-i',
            '--include',
            help='fnmatch pattern to include (files only, matched against basename). '
            'Repeatable. When set, files not matching any pattern are hidden; '
            'directories are always shown.',
        ),
    ] = None,
    follow_symlinks: Annotated[
        bool,
        typer.Option(
            '-L',
            '--follow-symlinks',
            help='Follow directory symlinks (cycles broken). Default: do not follow.',
        ),
    ] = False,
    stats: Annotated[
        bool,
        typer.Option('--stats', help='Print file and directory counts to stderr after rendering.'),
    ] = False,
) -> None:
    root = walk(
        path,
        excludes=_resolve_excludes(exclude or [], no_default_excludes),
        includes=include or [],
        max_depth=max_depth,
        follow_symlinks=follow_symlinks,
    )
    if stats:
        files, dirs = _count_tree(root)
        typer.echo(
            f'{files} {"file" if files == 1 else "files"}, '
            f'{dirs} {"directory" if dirs == 1 else "directories"}',
            err=True,
        )
    if fmt == 'json':
        _run_json(output, root)
        return
    if fmt == 'mermaid':
        _run_mermaid(output, root)
        return

    dot = to_dot(root)
    output_directory, output_filename = _resolve_output(output, root.basename)
    rendered_path = dot.render(
        directory=output_directory,
        filename=output_filename,
        view=not no_view,
        cleanup=True,
        format=fmt,
    )
    print(rendered_path)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        app(list(argv) if argv is not None else None)
    except SystemExit as e:
        code = e.code
        if isinstance(code, int):
            return code
        return 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
