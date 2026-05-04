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


# --- excludes ---------------------------------------------------------------


def test_walk_excludes_filter_children_by_basename(tmp_path):
    (tmp_path / 'keep.py').write_text('')
    (tmp_path / 'drop.py').write_text('')
    node = walk(str(tmp_path), excludes=['drop.py'])
    assert [c.basename for c in node.children] == ['keep.py']


def test_walk_excludes_use_fnmatch_globs(tmp_path):
    (tmp_path / 'a.py').write_text('')
    (tmp_path / 'a.pyc').write_text('')
    (tmp_path / 'b.pyc').write_text('')
    node = walk(str(tmp_path), excludes=['*.pyc'])
    assert [c.basename for c in node.children] == ['a.py']


def test_walk_excludes_apply_at_every_depth(tmp_path):
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src' / '__pycache__').mkdir()
    (tmp_path / 'src' / '__pycache__' / 'main.pyc').write_text('')
    (tmp_path / 'src' / 'main.py').write_text('')
    node = walk(str(tmp_path), excludes=['__pycache__'])
    src = node.children[0]
    assert [c.basename for c in src.children] == ['main.py']


def test_walk_root_is_never_excluded_even_when_pattern_matches(tmp_path):
    proj = tmp_path / '.git'
    proj.mkdir()
    (proj / 'HEAD').write_text('')
    node = walk(str(proj), excludes=['.git'])
    # Root keeps its identity; only its children are filtered.
    assert node.basename == '.git'
    assert [c.basename for c in node.children] == ['HEAD']


def test_walk_multiple_exclude_patterns_combine(tmp_path):
    (tmp_path / '.git').mkdir()
    (tmp_path / '__pycache__').mkdir()
    (tmp_path / 'src').mkdir()
    node = walk(str(tmp_path), excludes=['.git', '__pycache__'])
    assert [c.basename for c in node.children] == ['src']


# --- max_depth --------------------------------------------------------------


def test_walk_max_depth_zero_returns_root_only(tmp_path):
    (tmp_path / 'a.txt').write_text('')
    (tmp_path / 'sub').mkdir()
    node = walk(str(tmp_path), max_depth=0)
    assert node.children == ()


def test_walk_max_depth_one_includes_direct_children_only(tmp_path):
    (tmp_path / 'a.txt').write_text('')
    (tmp_path / 'sub').mkdir()
    (tmp_path / 'sub' / 'deep.txt').write_text('')
    node = walk(str(tmp_path), max_depth=1)
    sub = next(c for c in node.children if c.basename == 'sub')
    assert sub.children == ()


def test_walk_max_depth_none_is_unlimited(tmp_path):
    (tmp_path / 'a' / 'b' / 'c').mkdir(parents=True)
    (tmp_path / 'a' / 'b' / 'c' / 'leaf.txt').write_text('')
    node = walk(str(tmp_path), max_depth=None)
    leaf = node.children[0].children[0].children[0].children[0]
    assert leaf.basename == 'leaf.txt'


# --- follow_symlinks --------------------------------------------------------


def test_walk_does_not_follow_dir_symlinks_by_default(tmp_path):
    real = tmp_path / 'real'
    real.mkdir()
    (real / 'inside.txt').write_text('')
    link = tmp_path / 'link'
    link.symlink_to(real, target_is_directory=True)
    node = walk(str(tmp_path))
    link_node = next(c for c in node.children if c.basename == 'link')
    assert link_node.is_dir is True  # os.path.isdir follows links
    assert link_node.children == ()  # but we did not recurse


def test_walk_follows_dir_symlinks_when_requested(tmp_path):
    real = tmp_path / 'real'
    real.mkdir()
    (real / 'inside.txt').write_text('')
    link = tmp_path / 'link'
    link.symlink_to(real, target_is_directory=True)
    node = walk(str(tmp_path), follow_symlinks=True)
    link_node = next(c for c in node.children if c.basename == 'link')
    assert [c.basename for c in link_node.children] == ['inside.txt']


def test_walk_breaks_symlink_cycles_when_following(tmp_path):
    a = tmp_path / 'a'
    a.mkdir()
    # a/loop -> a (a cycle)
    (a / 'loop').symlink_to(a, target_is_directory=True)
    node = walk(str(tmp_path), follow_symlinks=True)
    a_node = node.children[0]
    loop_node = next(c for c in a_node.children if c.basename == 'loop')
    # The cycle is broken on second visit -- no further descent.
    assert loop_node.children == ()
