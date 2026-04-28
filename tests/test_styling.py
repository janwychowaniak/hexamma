from hexamma.styling import (
    Category,
    categorize,
    edge_attrs,
    node_attrs,
)


# --- categorize -------------------------------------------------------------

def test_categorize_regular_file_is_uncategorized():
    assert categorize(False, 'foo.txt') == frozenset()


def test_categorize_folder():
    assert categorize(True, 'foo') == frozenset({Category.FOLDER})


def test_categorize_hidden_file():
    assert categorize(False, '.gitignore') == frozenset({Category.HIDDEN})


def test_categorize_hidden_folder():
    assert categorize(True, '.git') == frozenset({Category.FOLDER, Category.HIDDEN})


def test_categorize_python_source():
    assert categorize(False, 'foo.py') == frozenset({Category.SOURCE})


def test_categorize_extension_is_case_insensitive():
    assert categorize(False, 'FOO.PY') == frozenset({Category.SOURCE})


def test_categorize_config_ini():
    assert categorize(False, 'config.ini') == frozenset({Category.CONFIG})


def test_categorize_config_yml():
    assert categorize(False, 'config.yml') == frozenset({Category.CONFIG})


def test_categorize_doc_rst():
    assert categorize(False, 'readme.rst') == frozenset({Category.DOC})


def test_categorize_hidden_source():
    assert categorize(False, '.tool.py') == frozenset({Category.HIDDEN, Category.SOURCE})


def test_categorize_dotfile_with_no_secondary_extension_is_only_hidden():
    # os.path.splitext('.py') -> ('.py', '') so this is HIDDEN, not SOURCE.
    assert categorize(False, '.py') == frozenset({Category.HIDDEN})


# --- node_attrs -------------------------------------------------------------

def test_node_attrs_uncategorized_is_empty():
    assert node_attrs(frozenset()) == {}


def test_node_attrs_folder():
    assert node_attrs(frozenset({Category.FOLDER})) == {
        'fillcolor': '#ffe79c',
        'style': 'filled',
        'shape': 'folder',
        'color': '#919191',
    }


def test_node_attrs_python_source():
    assert node_attrs(frozenset({Category.SOURCE})) == {
        'fillcolor': '#4381b3',
        'style': 'filled,rounded',
        'fontcolor': '#ffd343',
        'color': '#ffffff',
        'shape': 'box',
    }


def test_node_attrs_hidden_folder_hidden_overrides_color_and_adds_fontcolor():
    assert node_attrs(frozenset({Category.FOLDER, Category.HIDDEN})) == {
        'fillcolor': '#ffe79c',
        'style': 'filled',
        'shape': 'folder',
        'color': '#b8b8b8',
        'fontcolor': '#b8b8b8',
    }


def test_node_attrs_hidden_source_source_layer_dominates():
    # SOURCE is applied after HIDDEN, so source styling fully overrides hidden.
    assert node_attrs(frozenset({Category.HIDDEN, Category.SOURCE})) == {
        'fillcolor': '#4381b3',
        'style': 'filled,rounded',
        'fontcolor': '#ffd343',
        'color': '#ffffff',
        'shape': 'box',
    }


# --- edge_attrs -------------------------------------------------------------

def test_edge_attrs_default():
    assert edge_attrs(frozenset()) == {'color': '#919191'}


def test_edge_attrs_folder():
    assert edge_attrs(frozenset({Category.FOLDER})) == {'color': '#000000'}


def test_edge_attrs_hidden():
    assert edge_attrs(frozenset({Category.HIDDEN})) == {
        'color': '#b8b8b8',
        'style': 'dotted',
        'arrowhead': 'empty',
    }


def test_edge_attrs_hidden_folder_hidden_wins():
    assert edge_attrs(frozenset({Category.FOLDER, Category.HIDDEN})) == {
        'color': '#b8b8b8',
        'style': 'dotted',
        'arrowhead': 'empty',
    }
