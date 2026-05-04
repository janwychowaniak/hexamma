import json

from hexamma.json_output import to_json
from hexamma.tree import FsNode


def _leaf(name: str, relpath: str = '') -> FsNode:
    return FsNode(basename=name, relpath=relpath or name, is_dir=False, children=())


def test_to_json_is_valid_json():
    node = FsNode(basename='root', relpath='', is_dir=True, children=())
    json.loads(to_json(node))  # must not raise


def test_to_json_root_fields():
    node = FsNode(basename='root', relpath='', is_dir=True, children=())
    data = json.loads(to_json(node))
    assert data['name'] == 'root'
    assert data['path'] == ''
    assert data['is_dir'] is True
    assert data['children'] == []


def test_to_json_file_node():
    node = _leaf('main.py')
    data = json.loads(to_json(node))
    assert data['name'] == 'main.py'
    assert data['is_dir'] is False
    assert data['children'] == []


def test_to_json_nested():
    child = _leaf('main.py', 'src/main.py')
    root = FsNode(basename='proj', relpath='', is_dir=True, children=(child,))
    data = json.loads(to_json(root))
    assert len(data['children']) == 1
    c = data['children'][0]
    assert c['name'] == 'main.py'
    assert c['path'] == 'src/main.py'
    assert c['is_dir'] is False
    assert c['children'] == []


def test_to_json_deeply_nested():
    leaf = FsNode(basename='leaf.txt', relpath='a/b/leaf.txt', is_dir=False, children=())
    b = FsNode(basename='b', relpath='a/b', is_dir=True, children=(leaf,))
    a = FsNode(basename='a', relpath='a', is_dir=True, children=(b,))
    root = FsNode(basename='root', relpath='', is_dir=True, children=(a,))
    data = json.loads(to_json(root))
    deep = data['children'][0]['children'][0]['children'][0]
    assert deep['name'] == 'leaf.txt'


def test_to_json_multiple_children_preserves_order():
    children = tuple(_leaf(n) for n in ['a.py', 'b.py', 'c.py'])
    root = FsNode(basename='root', relpath='', is_dir=True, children=children)
    data = json.loads(to_json(root))
    assert [c['name'] for c in data['children']] == ['a.py', 'b.py', 'c.py']
