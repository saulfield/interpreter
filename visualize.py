import sys
from graphviz import Digraph
from sol import *

dot = None
counter = 0

def node_label(node):
    return str(type(node))[12:-2]

def new_name():
    global counter
    counter = counter + 1
    return f"node{counter}"

def leaf(parent, label):
    name = new_name()
    dot.node(name, label)
    dot.edge(parent, name)
    return name

def visit_node(node):
    name = new_name()
    dot.node(name, node_label(node))
    if isinstance(node, Primary):
        if node.type is Type.Ident:
            leafname = leaf(name, 'Identifier')
            leaf(leafname, str(node.val))
        elif node.type is Type.String: leaf(name, f"\"{node.val}\"")
        else: leaf(name, str(node.val))
    elif isinstance(node, BinExp):
        dot.edge(name, visit_node(node.left))
        leaf(name, '\\' + node.op)
        dot.edge(name, visit_node(node.right))
    elif isinstance(node, Statement):
        if node.exp is not None: dot.edge(name, visit_node(node.exp))
        if node.thenStmt is not None: dot.edge(name, visit_node(node.thenStmt))
        if node.elseStmt is not None: dot.edge(name, visit_node(node.elseStmt))
    elif isinstance(node, VarStatement):
        # if isinstance(node, Decl):
        #     leaf(name, 'var')
        leafname = leaf(name, 'Identifier')
        leaf(leafname, str(node.name))
        leaf(name, '=')
        if node.exp is not None: dot.edge(name, visit_node(node.exp))
    elif isinstance(node, Block):
        for stmt in node.stmts:
            dot.edge(name, visit_node(stmt))
    return name

def main():
    global dot
    argc = len(sys.argv)
    if argc != 2:
        print(f'Usage:\n\t {sys.argv[0]} <filename>')
        exit(1)
    with open(sys.argv[1]) as f:
        source = f.read()
    ast = parse(source)
    dot = Digraph(comment='AST Visualization', node_attr={'shape': 'record'})
    dot.node('Program')
    for stmt in ast:
        dot.edge('Program', visit_node(stmt))
    dot.render('ast', view=True, format='svg', cleanup=True)

if __name__ == "__main__": main()