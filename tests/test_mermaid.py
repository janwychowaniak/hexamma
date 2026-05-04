from hexamma.mermaid import to_mermaid
from hexamma.tree import FsNode


def _node_lines(diagram):
    return [
        ln for ln in diagram.splitlines()
        if ('["' in ln or '(["' in ln) and '-->' not in ln and 'classDef' not in ln
    ]


def _edge_lines(diagram):
    return [ln for ln in diagram.splitlines() if '-->' in ln or '-.->' in ln]


def _classdef_lines(diagram):
    return [ln for ln in diagram.splitlines() if ln.strip().startswith('classDef')]


def _class_assign_lines(diagram):
    return [
        ln for ln in diagram.splitlines()
        if ln.strip().startswith('class ') and 'classDef' not in ln
    ]


# --- header -------------------------------------------------------------------

def test_to_mermaid_starts_with_flowchart_td():
    root = FsNode(basename='proj', relpath='', is_dir=True, children=())
    assert to_mermaid(root).startswith('flowchart TD')


# --- node / edge counts -------------------------------------------------------

def test_to_mermaid_single_file_one_node_no_edges():
    root = FsNode(basename='foo.txt', relpath='', is_dir=False, children=())
    diagram = to_mermaid(root)
    assert len(_node_lines(diagram)) == 1
    assert _edge_lines(diagram) == []


def test_to_mermaid_empty_directory_one_node_no_edges():
    root = FsNode(basename='proj', relpath='', is_dir=True, children=())
    diagram = to_mermaid(root)
    assert len(_node_lines(diagram)) == 1
    assert _edge_lines(diagram) == []


def test_to_mermaid_n_minus_one_edges():
    main = FsNode(basename='main.py', relpath='src/main.py', is_dir=False, children=())
    src = FsNode(basename='src', relpath='src', is_dir=True, children=(main,))
    tests = FsNode(basename='tests', relpath='tests', is_dir=True, children=())
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(src, tests))
    diagram = to_mermaid(root)
    assert len(_node_lines(diagram)) == 4
    assert len(_edge_lines(diagram)) == 3


# --- IDs ----------------------------------------------------------------------

def test_to_mermaid_root_uses_ROOT_sentinel():
    root = FsNode(basename='proj', relpath='', is_dir=True, children=())
    assert 'ROOT' in to_mermaid(root)


def test_to_mermaid_node_id_sanitizes_slash():
    main = FsNode(basename='main.py', relpath='src/main.py', is_dir=False, children=())
    src = FsNode(basename='src', relpath='src', is_dir=True, children=(main,))
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(src,))
    diagram = to_mermaid(root)
    # No raw slash should appear in any node ID position
    node_ids = [ln.strip().split('(')[0].split('[')[0] for ln in _node_lines(diagram)]
    assert all('/' not in nid for nid in node_ids)


def test_to_mermaid_node_id_sanitizes_leading_dot():
    hidden = FsNode(basename='.gitignore', relpath='.gitignore', is_dir=False, children=())
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(hidden,))
    diagram = to_mermaid(root)
    node_ids = [ln.strip().split('(')[0].split('[')[0] for ln in _node_lines(diagram)]
    assert all(not nid.startswith('.') for nid in node_ids)


# --- labels -------------------------------------------------------------------

def test_to_mermaid_label_is_basename():
    main = FsNode(basename='main.py', relpath='src/main.py', is_dir=False, children=())
    src = FsNode(basename='src', relpath='src', is_dir=True, children=(main,))
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(src,))
    diagram = to_mermaid(root)
    assert '"proj"' in diagram
    assert '"src"' in diagram
    assert '"main.py"' in diagram


# --- shapes -------------------------------------------------------------------

def test_to_mermaid_folder_uses_stadium_shape():
    root = FsNode(basename='proj', relpath='', is_dir=True, children=())
    diagram = to_mermaid(root)
    node_line = _node_lines(diagram)[0]
    assert '(["proj"])' in node_line


def test_to_mermaid_file_uses_rectangle_shape():
    f = FsNode(basename='note.txt', relpath='note.txt', is_dir=False, children=())
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(f,))
    diagram = to_mermaid(root)
    file_line = next(ln for ln in _node_lines(diagram) if 'note.txt' in ln)
    assert '["note.txt"]' in file_line
    assert '(["note.txt"])' not in file_line


# --- edge styles --------------------------------------------------------------

def test_to_mermaid_hidden_file_edge_is_dotted():
    hidden = FsNode(basename='.gitignore', relpath='.gitignore', is_dir=False, children=())
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(hidden,))
    diagram = to_mermaid(root)
    assert '-.->' in _edge_lines(diagram)[0]


def test_to_mermaid_plain_file_edge_is_solid():
    f = FsNode(basename='note.txt', relpath='note.txt', is_dir=False, children=())
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(f,))
    diagram = to_mermaid(root)
    edge = _edge_lines(diagram)[0]
    assert '-->' in edge
    assert '-.->' not in edge


# --- class assignments --------------------------------------------------------

def test_to_mermaid_folder_gets_folder_class():
    root = FsNode(basename='proj', relpath='', is_dir=True, children=())
    diagram = to_mermaid(root)
    assign = next(ln for ln in _class_assign_lines(diagram) if 'ROOT' in ln)
    assert 'folder_cls' in assign


def test_to_mermaid_source_file_gets_source_class():
    f = FsNode(basename='main.py', relpath='main.py', is_dir=False, children=())
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(f,))
    diagram = to_mermaid(root)
    assign = next(ln for ln in _class_assign_lines(diagram) if 'main_dot_py' in ln)
    assert 'source_cls' in assign


def test_to_mermaid_hidden_folder_gets_hidden_class():
    # HIDDEN layer is later than FOLDER in _NODE_LAYER_ORDER, so it wins.
    git = FsNode(basename='.git', relpath='.git', is_dir=True, children=())
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(git,))
    diagram = to_mermaid(root)
    assign = next(ln for ln in _class_assign_lines(diagram) if '_dot_git' in ln)
    assert 'hidden_cls' in assign


# --- classDef stability -------------------------------------------------------

def test_to_mermaid_all_classdefs_always_emitted():
    root = FsNode(basename='proj', relpath='', is_dir=False, children=())
    diagram = to_mermaid(root)
    cdefs = _classdef_lines(diagram)
    names = ' '.join(cdefs)
    for cls in ('folder_cls', 'hidden_cls', 'source_cls', 'config_cls', 'doc_cls', 'default_file'):
        assert cls in names


# --- deep nesting -------------------------------------------------------------

def test_to_mermaid_deeply_nested_id_is_safe():
    c = FsNode(basename='c.py', relpath='a/b/c.py', is_dir=False, children=())
    b = FsNode(basename='b', relpath='a/b', is_dir=True, children=(c,))
    a = FsNode(basename='a', relpath='a', is_dir=True, children=(b,))
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(a,))
    diagram = to_mermaid(root)
    node_ids = [ln.strip().split('(')[0].split('[')[0] for ln in _node_lines(diagram)]
    assert all('/' not in nid for nid in node_ids)
    assert all(not nid.startswith('.') for nid in node_ids)
