import sys
from enum import Enum
from parsley import makeGrammar

Type = Enum('Type', 'Num Bool')

class Literal:
    def __init__(self, type, val):
        self.type = type
        self.val = val

    def __repr__(self):
        return "{}".format(self.val)

class BinExp:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    # Recursively prints an S-expression
    def __repr__(self):
        return "({} {} {})".format(self.op, self.left, self.right)

op_table = {
    '+': lambda x, y: x + y,
    '-': lambda x, y: x - y,
    '*': lambda x, y: x * y,
    '/': lambda x, y: x / y
}

def eval(node):
    if isinstance(node, Literal):
        return node.val
    elif isinstance(node, BinExp):
        left = eval(node.left)
        right = eval(node.right)
        return op_table[node.op](left, right)
    else:
        raise TypeError('Type not recognized: {}'.format(type(node)))

parse_grammar = r"""
    ws = (' ' | '\r' | '\n' | '\t')*
    digit = anything:x ?(x in '0123456789') -> x
    num = <digit+>:ds -> int(ds) 

    primary = ws num:n ws                       -> Literal(Type.Num, n)
            | ws '(' exp:e ')' ws               -> e
    fac     = fac:x ('*' | '/'):op primary:y    -> BinExp(x, op, y)
            | primary
    exp     = exp:x ('+' | '-'):op fac:y        -> BinExp(x, op, y)
            | fac
    program = exp
"""

def parse(source):
    bindings = {
        'Type':Type,
        'Literal':Literal,
        'BinExp':BinExp
    }
    parser = makeGrammar(parse_grammar, bindings)
    ast = parser(source).program()
    return ast

def main():
    argc = len(sys.argv)
    if argc > 2:
        print("Usage:\n\t" + sys.argv[0] + " <filename>")
        exit(1)
    elif argc == 2:
        # Read and execute file
        with open(sys.argv[1]) as f:
            source = f.read()
        ast = parse(source)
        print(eval(ast))
    else:
        # REPL mode
        while True:
            source = input('>> ')
            ast = parse(source)
            print(eval(ast))

if __name__ == "__main__": main()
