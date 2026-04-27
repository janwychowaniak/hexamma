from hexamma.render import to_dot
from hexamma.tree import FsNode


def _node_lines(dot):
    return [line for line in dot.body if ' -> ' not in line]


def _edge_lines(dot):
    return [line for line in dot.body if ' -> ' in line]


def test_to_dot_single_file_produces_one_node_no_edges():
    root = FsNode(basename='foo.txt', relpath='', is_dir=False, children=())
    dot = to_dot(root)
    assert len(_node_lines(dot)) == 1
    assert _edge_lines(dot) == []


def test_to_dot_empty_directory_produces_one_node_no_edges():
    root = FsNode(basename='proj', relpath='', is_dir=True, children=())
    dot = to_dot(root)
    assert len(_node_lines(dot)) == 1
    assert _edge_lines(dot) == []


def test_to_dot_root_uses_dot_sentinel_id():
    root = FsNode(basename='proj', relpath='', is_dir=True, children=())
    dot = to_dot(root)
    # The root's ID is '.', which graphviz quotes as "."
    assert '"."' in dot.source


def test_to_dot_descendants_use_relpath_as_id():
    main = FsNode(basename='main.py', relpath='src/main.py', is_dir=False, children=())
    src = FsNode(basename='src', relpath='src', is_dir=True, children=(main,))
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(src,))
    dot = to_dot(root)
    # 'src' is a simple identifier (unquoted); 'src/main.py' is quoted.
    assert '\tsrc [' in dot.source
    assert '"src/main.py"' in dot.source


def test_to_dot_emits_n_minus_one_edges_for_a_tree_of_n_nodes():
    # 4 nodes total: root + src + main.py + tests
    main = FsNode(basename='main.py', relpath='src/main.py', is_dir=False, children=())
    src = FsNode(basename='src', relpath='src', is_dir=True, children=(main,))
    tests = FsNode(basename='tests', relpath='tests', is_dir=True, children=())
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(src, tests))
    dot = to_dot(root)
    assert len(_node_lines(dot)) == 4
    assert len(_edge_lines(dot)) == 3


def test_to_dot_label_is_basename():
    main = FsNode(basename='main.py', relpath='src/main.py', is_dir=False, children=())
    src = FsNode(basename='src', relpath='src', is_dir=True, children=(main,))
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(src,))
    dot = to_dot(root)
    # label=proj for root, label=src, label="main.py" for the file (quoted because of dot)
    assert 'label=proj' in dot.source
    assert 'label=src' in dot.source
    assert 'label="main.py"' in dot.source


def test_to_dot_comment_uses_root_basename():
    root = FsNode(basename='myproj', relpath='', is_dir=True, children=())
    dot = to_dot(root)
    assert dot.source.startswith('// myproj folder tree')


def test_to_dot_folder_node_uses_folder_shape():
    root = FsNode(basename='proj', relpath='', is_dir=True, children=())
    dot = to_dot(root)
    assert 'shape=folder' in dot.source


def test_to_dot_python_source_node_uses_box_shape():
    f = FsNode(basename='m.py', relpath='m.py', is_dir=False, children=())
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(f,))
    dot = to_dot(root)
    # Find the line for m.py and assert it has the source styling.
    line = [ln for ln in _node_lines(dot) if 'm.py' in ln][0]
    assert 'shape=box' in line
    assert 'fillcolor="#4381b3"' in line


def test_to_dot_folder_edge_is_black():
    sub = FsNode(basename='sub', relpath='sub', is_dir=True, children=())
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(sub,))
    dot = to_dot(root)
    edge = _edge_lines(dot)[0]
    assert 'color="#000000"' in edge


def test_to_dot_hidden_edge_is_dotted():
    hidden = FsNode(basename='.gitignore', relpath='.gitignore', is_dir=False, children=())
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(hidden,))
    dot = to_dot(root)
    edge = _edge_lines(dot)[0]
    assert 'style=dotted' in edge
    assert 'arrowhead=empty' in edge


def test_to_dot_default_edge_color_for_plain_file():
    f = FsNode(basename='note.txt', relpath='note.txt', is_dir=False, children=())
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(f,))
    dot = to_dot(root)
    edge = _edge_lines(dot)[0]
    assert 'color="#919191"' in edge
