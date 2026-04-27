import os

from hexamma.tree import FsNode, walk


def test_walk_single_file(tmp_path):
    f = tmp_path / 'foo.txt'
    f.write_text('hi')
    node = walk(str(f))
    assert node == FsNode(
        basename='foo.txt',
        relpath='',
        is_dir=False,
        children=(),
    )


def test_walk_empty_directory(tmp_path):
    node = walk(str(tmp_path))
    assert node.is_dir is True
    assert node.children == ()
    assert node.relpath == ''


def test_walk_root_basename_is_directory_name(tmp_path):
    project = tmp_path / 'myproj'
    project.mkdir()
    node = walk(str(project))
    assert node.basename == 'myproj'
    assert node.relpath == ''


def test_walk_directory_with_files(tmp_path):
    (tmp_path / 'a.py').write_text('')
    (tmp_path / 'b.txt').write_text('')
    node = walk(str(tmp_path))
    assert [c.basename for c in node.children] == ['a.py', 'b.txt']
    assert all(not c.is_dir for c in node.children)
    assert all(c.children == () for c in node.children)


def test_walk_nested_directory_relpaths(tmp_path):
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src' / 'main.py').write_text('')
    node = walk(str(tmp_path))
    assert len(node.children) == 1
    src = node.children[0]
    assert src.basename == 'src'
    assert src.is_dir is True
    assert src.relpath == 'src'
    assert len(src.children) == 1
    main = src.children[0]
    assert main.basename == 'main.py'
    assert main.relpath == os.path.join('src', 'main.py')
    assert main.is_dir is False


def test_walk_children_are_sorted_alphabetically(tmp_path):
    for name in ['zebra', 'apple', 'mango']:
        (tmp_path / name).write_text('')
    node = walk(str(tmp_path))
    assert [c.basename for c in node.children] == ['apple', 'mango', 'zebra']


def test_walk_sorts_at_every_depth(tmp_path):
    (tmp_path / 'b').mkdir()
    (tmp_path / 'a').mkdir()
    (tmp_path / 'b' / 'z.txt').write_text('')
    (tmp_path / 'b' / 'a.txt').write_text('')
    node = walk(str(tmp_path))
    assert [c.basename for c in node.children] == ['a', 'b']
    b = node.children[1]
    assert [c.basename for c in b.children] == ['a.txt', 'z.txt']


def test_walk_mixed_files_and_directories(tmp_path):
    (tmp_path / 'README.md').write_text('')
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src' / 'main.py').write_text('')
    (tmp_path / 'tests').mkdir()
    node = walk(str(tmp_path))
    assert [(c.basename, c.is_dir) for c in node.children] == [
        ('README.md', False),
        ('src', True),
        ('tests', True),
    ]


def test_walk_is_deterministic(tmp_path):
    (tmp_path / 'a').mkdir()
    (tmp_path / 'a' / 'b.txt').write_text('')
    assert walk(str(tmp_path)) == walk(str(tmp_path))


def test_walk_accepts_relative_path(tmp_path, monkeypatch):
    (tmp_path / 'foo').mkdir()
    monkeypatch.chdir(tmp_path)
    node = walk('foo')
    assert node.basename == 'foo'
    assert node.is_dir is True
