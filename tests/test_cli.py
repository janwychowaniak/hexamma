import importlib.metadata
import json

from typer.testing import CliRunner

from hexamma.cli import DEFAULT_EXCLUDES, _count_tree, _resolve_excludes, _resolve_output, app, main
from hexamma.tree import FsNode

runner = CliRunner()


# --- _resolve_excludes -------------------------------------------------------


def test_resolve_excludes_combines_user_and_defaults():
    excludes = _resolve_excludes(['foo'], no_default_excludes=False)
    assert 'foo' in excludes
    for default in DEFAULT_EXCLUDES:
        assert default in excludes


def test_resolve_excludes_no_default_excludes_disables_built_ins():
    assert _resolve_excludes(['foo'], no_default_excludes=True) == ['foo']


def test_resolve_excludes_default_only():
    assert _resolve_excludes([], no_default_excludes=False) == list(DEFAULT_EXCLUDES)


# --- _resolve_output ---------------------------------------------------------


def test_resolve_output_default_uses_tempdir_and_named_tree(tmp_path, monkeypatch):
    monkeypatch.setattr('tempfile.gettempdir', lambda: str(tmp_path))
    directory, filename = _resolve_output(None, 'myproj')
    assert directory == str(tmp_path)
    assert filename == 'tree__myproj'


def test_resolve_output_explicit_path_strips_extension():
    directory, filename = _resolve_output('/tmp/diagram.png', 'ignored')
    assert directory == '/tmp'
    assert filename == 'diagram'


def test_resolve_output_explicit_path_without_extension():
    directory, filename = _resolve_output('/tmp/diagram', 'ignored')
    assert directory == '/tmp'
    assert filename == 'diagram'


def test_resolve_output_relative_path_falls_back_to_dot_dir():
    directory, filename = _resolve_output('diagram', 'ignored')
    assert directory == '.'
    assert filename == 'diagram'


# --- _count_tree -------------------------------------------------------------


def test_count_tree_empty_dir():
    root = FsNode(basename='root', relpath='', is_dir=True, children=())
    assert _count_tree(root) == (0, 0)


def test_count_tree_files_only():
    children = (
        FsNode(basename='a.py', relpath='a.py', is_dir=False, children=()),
        FsNode(basename='b.txt', relpath='b.txt', is_dir=False, children=()),
    )
    root = FsNode(basename='root', relpath='', is_dir=True, children=children)
    assert _count_tree(root) == (2, 0)


def test_count_tree_nested():
    leaf = FsNode(basename='main.py', relpath='src/main.py', is_dir=False, children=())
    src = FsNode(basename='src', relpath='src', is_dir=True, children=(leaf,))
    readme = FsNode(basename='README.md', relpath='README.md', is_dir=False, children=())
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(readme, src))
    files, dirs = _count_tree(root)
    assert files == 2  # README.md + main.py
    assert dirs == 1  # src


def test_count_tree_singular_labels(tmp_path):
    (tmp_path / 'only.py').write_text('')
    (tmp_path / 'sub').mkdir()
    result = runner.invoke(
        app,
        ['--stats', '--format', 'json', '--no-default-excludes', str(tmp_path)],
    )
    assert result.exit_code == 0
    assert '1 file,' in result.output
    assert '1 directory' in result.output


def test_stats_flag_separates_stderr_from_stdout(tmp_path):
    (tmp_path / 'a.py').write_text('')
    (tmp_path / 'b.txt').write_text('')
    (tmp_path / 'sub').mkdir()
    (tmp_path / 'sub' / 'c.py').write_text('')
    result = runner.invoke(
        app,
        ['--stats', '--format', 'json', '--no-default-excludes', str(tmp_path)],
    )
    assert result.exit_code == 0
    assert '3 files' in result.stderr
    assert '1 directory' in result.stderr
    json.loads(result.stdout)  # stdout is clean JSON


# --- version -----------------------------------------------------------------


def test_version_flag():
    result = runner.invoke(app, ['--version'])
    assert result.exit_code == 0
    assert importlib.metadata.version('hexamma') in result.output


# --- CLI argument parsing ----------------------------------------------------


def test_max_depth_rejects_non_int():
    result = runner.invoke(app, ['--max-depth', 'three', '.'])
    assert result.exit_code != 0


def test_exclude_is_repeatable(tmp_path):
    (tmp_path / 'a.py').write_text('')
    out = tmp_path / 'out'
    result = runner.invoke(
        app,
        [
            '-e',
            'a',
            '--exclude',
            'b',
            '-e',
            'c',
            '--format',
            'mermaid',
            '--no-default-excludes',
            '-o',
            str(out),
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0


# --- json format -------------------------------------------------------------


def test_json_format_prints_to_stdout(tmp_path):
    (tmp_path / 'a.py').write_text('')
    result = runner.invoke(app, ['--format', 'json', '--no-default-excludes', str(tmp_path)])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data['is_dir'] is True
    assert any(c['name'] == 'a.py' for c in data['children'])


def test_json_format_writes_file_when_output_given(tmp_path):
    (tmp_path / 'a.py').write_text('')
    out = tmp_path / 'tree'
    result = runner.invoke(
        app, ['--format', 'json', '--no-default-excludes', '-o', str(out), str(tmp_path)]
    )
    assert result.exit_code == 0
    assert (tmp_path / 'tree.json').exists()


# --- include filter ----------------------------------------------------------


def test_include_filters_files_via_json(tmp_path):
    (tmp_path / 'a.py').write_text('')
    (tmp_path / 'b.txt').write_text('')
    result = runner.invoke(
        app, ['-i', '*.py', '--format', 'json', '--no-default-excludes', str(tmp_path)]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    names = [c['name'] for c in data['children']]
    assert 'a.py' in names
    assert 'b.txt' not in names


# --- mermaid integration -----------------------------------------------------


def test_mermaid_format_writes_mmd_file(tmp_path, monkeypatch):
    (tmp_path / 'hello.py').write_text('')
    monkeypatch.setattr('tempfile.gettempdir', lambda: str(tmp_path))
    rc = main(['--format', 'mermaid', '--no-default-excludes', str(tmp_path)])
    assert rc == 0
    mmd_files = list(tmp_path.glob('*.mmd'))
    assert len(mmd_files) == 1
    assert mmd_files[0].read_text().startswith('flowchart TD')


def test_mermaid_format_bypasses_graphviz(tmp_path, monkeypatch):
    import hexamma.render as render_mod

    calls = []
    monkeypatch.setattr(render_mod, 'to_dot', lambda root: calls.append(root))
    monkeypatch.setattr('tempfile.gettempdir', lambda: str(tmp_path))
    main(['--format', 'mermaid', '--no-default-excludes', str(tmp_path)])
    assert calls == []
