import argparse
import importlib.resources
import os
import sys
import tempfile
import tomllib
from collections.abc import Sequence

from hexamma.render import to_dot
from hexamma.tree import FsNode, walk


def _load_default_excludes() -> tuple[str, ...]:
    ref = importlib.resources.files('hexamma').joinpath('excludes.toml')
    with ref.open('rb') as f:
        return tuple(tomllib.load(f)['excludes']['patterns'])


DEFAULT_EXCLUDES: tuple[str, ...] = _load_default_excludes()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='hexamma',
        description='Render a directory tree as a Graphviz diagram.',
    )
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Directory (or file) to visualize. Default: current directory.',
    )
    parser.add_argument(
        '-e',
        '--exclude',
        action='append',
        default=[],
        metavar='PATTERN',
        help='fnmatch pattern to exclude (matched against basename). '
        'Repeatable. Combined with the default excludes unless '
        '--no-default-excludes is given.',
    )
    parser.add_argument(
        '--no-default-excludes',
        action='store_true',
        help='Disable the built-in exclude list '
        '(.git, __pycache__, node_modules, *.egg-info, ...).',
    )
    parser.add_argument(
        '-d',
        '--max-depth',
        type=int,
        default=None,
        metavar='N',
        help='Maximum tree depth (root is depth 0). Default: unlimited.',
    )
    parser.add_argument(
        '-o',
        '--output',
        default=None,
        metavar='PATH',
        help='Output file path (extension is replaced by --format). '
        'Default: <tempdir>/tree__<basename>.<format>.',
    )
    parser.add_argument(
        '-f',
        '--format',
        default='png',
        help='Output format. Use "mermaid" for a .mmd file, or any graphviz '
        'format (png, svg, pdf, dot, ...). Default: png.',
    )
    parser.add_argument(
        '--no-view',
        action='store_true',
        help='Do not open the rendered file in the default viewer.',
    )
    parser.add_argument(
        '-L',
        '--follow-symlinks',
        action='store_true',
        help='Follow directory symlinks (cycles are broken on revisit). Default: do not follow.',
    )
    return parser


def _resolve_excludes(args: argparse.Namespace) -> list[str]:
    excludes: list[str] = list(args.exclude)
    if not args.no_default_excludes:
        excludes.extend(DEFAULT_EXCLUDES)
    return excludes


def _resolve_output(args: argparse.Namespace, root_basename: str) -> tuple[str, str]:
    if args.output is None:
        return tempfile.gettempdir(), f'tree__{root_basename}'
    directory = os.path.dirname(args.output) or '.'
    filename = os.path.splitext(os.path.basename(args.output))[0]
    return directory, filename


def _run_mermaid(args: argparse.Namespace, root: FsNode) -> int:
    from hexamma.mermaid import to_mermaid

    text = to_mermaid(root)
    directory, stem = _resolve_output(args, root.basename)
    out_path = os.path.join(directory, stem + '.mmd')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(out_path)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    root = walk(
        args.path,
        excludes=_resolve_excludes(args),
        max_depth=args.max_depth,
        follow_symlinks=args.follow_symlinks,
    )
    if args.format == 'mermaid':
        return _run_mermaid(args, root)

    dot = to_dot(root)

    output_directory, output_filename = _resolve_output(args, root.basename)
    rendered_path = dot.render(
        directory=output_directory,
        filename=output_filename,
        view=not args.no_view,
        cleanup=True,
        format=args.format,
    )
    print(rendered_path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
