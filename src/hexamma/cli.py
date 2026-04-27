import os
import tempfile

from hexamma.render import to_dot
from hexamma.tree import walk


def main():
    root = walk(os.getcwd())
    dot = to_dot(root)

    output_directory = tempfile.gettempdir()
    output_filename = f'tree__{root.basename}'
    output_format = 'png'

    dot.render(
        directory=output_directory,
        filename=output_filename,
        view=True,
        cleanup=True,
        format=output_format,
    )

    print(f'Output: {os.path.join(output_directory, ".".join([output_filename, output_format]))}')
