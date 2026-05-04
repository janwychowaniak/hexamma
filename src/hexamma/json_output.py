import json

from hexamma.tree import FsNode


def _node_to_dict(node: FsNode) -> dict[str, object]:
    return {
        'name': node.basename,
        'path': node.relpath,
        'is_dir': node.is_dir,
        'children': [_node_to_dict(c) for c in node.children],
    }


def to_json(root: FsNode) -> str:
    return json.dumps(_node_to_dict(root), indent=2)
