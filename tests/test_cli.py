import pytest

from hexamma.cli import (
    DEFAULT_EXCLUDES,
    _build_parser,
    _resolve_excludes,
    _resolve_output,
)


def parse(*argv):
    return _build_parser().parse_args(list(argv))


# --- defaults ---------------------------------------------------------------

def test_defaults_path_is_current_dir():
    args = parse()
    assert args.path == '.'


def test_defaults_no_excludes_max_depth_or_output():
    args = parse()
    assert args.exclude == []
    assert args.no_default_excludes is False
    assert args.max_depth is None
    assert args.output is None
    assert args.format == 'png'
    assert args.no_view is False
    assert args.follow_symlinks is False


# --- arguments --------------------------------------------------------------

def test_positional_path():
    args = parse('/some/dir')
    assert args.path == '/some/dir'


def test_exclude_is_repeatable():
    args = parse('-e', 'a', '--exclude', 'b', '-e', 'c')
    assert args.exclude == ['a', 'b', 'c']


def test_max_depth_is_int():
    args = parse('--max-depth', '3')
    assert args.max_depth == 3


def test_max_depth_rejects_non_int():
    with pytest.raises(SystemExit):
        parse('--max-depth', 'three')


def test_output_and_format():
    args = parse('-o', '/tmp/myfile', '-f', 'svg')
    assert args.output == '/tmp/myfile'
    assert args.format == 'svg'


def test_boolean_flags():
    args = parse('--no-view', '-L', '--no-default-excludes')
    assert args.no_view is True
    assert args.follow_symlinks is True
    assert args.no_default_excludes is True


# --- _resolve_excludes ------------------------------------------------------

def test_resolve_excludes_combines_user_and_defaults():
    args = parse('--exclude', 'foo')
    excludes = _resolve_excludes(args)
    assert 'foo' in excludes
    for default in DEFAULT_EXCLUDES:
        assert default in excludes


def test_resolve_excludes_no_default_excludes_disables_built_ins():
    args = parse('--no-default-excludes', '--exclude', 'foo')
    assert _resolve_excludes(args) == ['foo']


def test_resolve_excludes_default_only():
    args = parse()
    assert _resolve_excludes(args) == list(DEFAULT_EXCLUDES)


# --- _resolve_output --------------------------------------------------------

def test_resolve_output_default_uses_tempdir_and_named_tree(tmp_path, monkeypatch):
    monkeypatch.setattr('tempfile.gettempdir', lambda: str(tmp_path))
    args = parse()
    directory, filename = _resolve_output(args, 'myproj')
    assert directory == str(tmp_path)
    assert filename == 'tree__myproj'


def test_resolve_output_explicit_path_strips_extension():
    args = parse('-o', '/tmp/diagram.png')
    directory, filename = _resolve_output(args, 'ignored')
    assert directory == '/tmp'
    assert filename == 'diagram'


def test_resolve_output_explicit_path_without_extension():
    args = parse('-o', '/tmp/diagram')
    directory, filename = _resolve_output(args, 'ignored')
    assert directory == '/tmp'
    assert filename == 'diagram'


def test_resolve_output_relative_path_falls_back_to_dot_dir():
    args = parse('-o', 'diagram')
    directory, filename = _resolve_output(args, 'ignored')
    assert directory == '.'
    assert filename == 'diagram'
