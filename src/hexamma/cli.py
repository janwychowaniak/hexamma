# [https://graphviz.readthedocs.io]
# [https://graphviz.org/documentation/]

import os
import hashlib
import tempfile
from graphviz import Digraph

from hexamma.styling import categorize, node_attrs, edge_attrs


def md5sum4(inputstr):
    m = hashlib.md5()
    m.update(inputstr.encode('utf-8'))
    return m.hexdigest()[0:4]


def make_relpath(reldirname, basename):
    r = os.path.join(reldirname, basename)
    return r[2:] if r.startswith(f'.{os.path.sep}') else r


class Node:
    def __init__(self, basename, reldirname, dot):
        self.basename = basename
        self.reldirname = reldirname
        self.relpath = make_relpath(self.reldirname, self.basename)
        print(f'visiting node: {self.relpath} ')
        self.folder = os.path.isdir(self.relpath)
        self.dot = dot
        self.dotnodename = md5sum4(self.relpath)
        nodeattrs = node_attrs(categorize(self.folder, self.basename))
        self.dot.node(self.dotnodename, self.basename, **nodeattrs)
        self.nodes = self.listloc(self.relpath)
        for subnode in self.nodes:
            edgeattrs = edge_attrs(categorize(subnode.folder, subnode.basename))
            self.dot.edge(self.dotnodename, subnode.dotnodename, constraint='true', **edgeattrs)

    def listloc(self, selfrelpath):  # TODO
        if not self.folder:
            return []
        else:
            newreldirname = selfrelpath
            listdir = os.listdir(newreldirname)
            nodes = []
            for item in listdir:
                nodes.append(Node(item, newreldirname, self.dot))
            return nodes

    def __str__(self):
        printnodes = os.linesep.join([f'   {n}' for n in self.nodes]) if self.nodes else '-'
        head = ' ; '.join([f'relpath="{self.relpath}"',
                           f'basename="{self.basename}"',
                           f'reldirname="{self.reldirname}"',
                           f'folder={self.folder}'])
        return os.linesep.join([head,
                                f'nodes:',
                                printnodes])


def main():

    basename = os.path.basename(os.getcwd())
    reldirname = os.path.dirname(os.getcwd())

    dot = Digraph(comment=f'{basename} folder tree')

    Node(basename=basename, reldirname=reldirname, dot=dot)

    output_directory = tempfile.gettempdir()
    output_filename = f'tree__{basename}'
    output_format = 'png'

    dot.render(directory=output_directory,
               filename=output_filename,
               view=True,
               cleanup=True,
               format=output_format)

    print(f'Output: {os.path.join(output_directory, ".".join([output_filename, output_format]))}')
