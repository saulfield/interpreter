import sys
from enum import Enum
from parsley import makeGrammar

Type = Enum('Type', 'Null Num Bool')
StmtKind = Enum('StmtKind', 'Print')

op_table = {
    '+': lambda x, y: x + y,
    '-': lambda x, y: x - y,
    '*': lambda x, y: x * y,
    '/': lambda x, y: x / y
}

global_env = {}

class Decl:
    def __init__(self, name, exp):
        self.name = name
        self.exp = exp
        if exp is None:
            self.exp = Literal(Type.Null, None)

class Stmt:
    def __init__(self, kind, exp):
        self.kind = kind
        self.exp = exp

class Literal:
    def __init__(self, type, val):
        self.type = type
        self.val = val

    def __repr__(self):
        if self.type == Type.Null: return "Null"
        return "{}".format(self.val)

class BinExp:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    # Recursively prints an S-expression
    def __repr__(self):
        return "({} {} {})".format(self.op, self.left, self.right)

def eval(node):
    if isinstance(node, Literal):
        return node.val
    elif isinstance(node, BinExp):
        left = eval(node.left)
        right = eval(node.right)
        return op_table[node.op](left, right)
    elif isinstance(node, Stmt):
        if node.kind == StmtKind.Print: print(eval(node.exp))
    elif isinstance(node, Decl):
        if node.name in global_env: 
            raise ValueError('Identifier {} already declared')
        else: 
            global_env[node.name] = eval(node.exp)
    else:
        raise TypeError('Type not recognized: {}'.format(type(node)))

parse_grammar = r"""
    ws = (' ' | '\r' | '\n' | '\t')*
    digit = anything:x ?(x in '0123456789') -> x
    num = <digit+>:ds -> int(ds)
    identifier = <letter+>:first <letterOrDigit*>:rest -> first + rest

    primary   = ws num:n ws                             -> Literal(Type.Num, n)
              | ws '(' exp:e ')' ws                     -> e
    fac       = fac:x ('*' | '/'):op primary:y          -> BinExp(x, op, y)
              | primary
    exp       = exp:x ('+' | '-'):op fac:y              -> BinExp(x, op, y)
              | fac
    printStmt = ws 'print' exp:e ';'                    -> Stmt(StmtKind.Print, e)
    init      = '=' exp:e                               -> e
    declStmt  = ws 'var' ws identifier:i ws init?:e ';' -> Decl(i, e)
    stmt      = printStmt
              | declStmt
    program   = stmt*
"""

def parse(source):
    bindings = {
        'Type':Type,
        'Literal':Literal,
        'StmtKind':StmtKind,
        'Stmt':Stmt,
        'BinExp':BinExp,
        'Decl':Decl
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
        print(ast)
        for stmt in ast:
            eval(stmt)              
    else:
        # REPL mode
        while True:
            source = input('>> ')
            ast = parse(source)
            for stmt in ast:
                eval(stmt)

if __name__ == "__main__": main()
