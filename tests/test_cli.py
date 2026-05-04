from typer.testing import CliRunner

from hexamma.cli import DEFAULT_EXCLUDES, _resolve_excludes, _resolve_output, app, main

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


# --- CLI argument parsing ----------------------------------------------------


def test_max_depth_rejects_non_int():
    result = runner.invoke(app, ['--max-depth', 'three', '.'])
    assert result.exit_code != 0


def test_exclude_is_repeatable(tmp_path):
    (tmp_path / 'a.py').write_text('')
    out = tmp_path / 'out'
    result = runner.invoke(
        app,
        ['-e', 'a', '--exclude', 'b', '-e', 'c', '--format', 'mermaid',
         '--no-default-excludes', '-o', str(out), str(tmp_path)],
    )
    assert result.exit_code == 0


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
