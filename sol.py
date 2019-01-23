import sys
from enum import Enum
from parsley import makeGrammar

Type = Enum('Type', 'Null Num Bool Ident')
StmtKind = Enum('StmtKind', 'Print')

arithmetic_ops = {
    '+': lambda x, y: x + y,
    '-': lambda x, y: x - y,
    '*': lambda x, y: x * y,
    '/': lambda x, y: x / y
}

global_env = {}

class Primary:
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

    def __repr__(self):
        return "({} {} {})".format(self.op, self.left, self.right)

class Decl:
    def __init__(self, ident_node, exp):
        self.name = ident_node.val
        self.exp = exp
        if exp is None:
            self.exp = Primary(Type.Null, None)

class Assign:
    def __init__(self, ident_node, exp):
        self.name = ident_node.val
        self.exp = exp
        if exp is None:
            self.exp = Primary(Type.Null, None)

class PrintStmt:
    def __init__(self, exp):
        self.exp = exp

def eval(node):
    if isinstance(node, Primary):
        if node.type == Type.Ident:
            return global_env[node.val]
        return node.val
    elif isinstance(node, BinExp):
        left = eval(node.left)
        right = eval(node.right)
        return arithmetic_ops[node.op](left, right)
    elif isinstance(node, PrintStmt):
        print(eval(node.exp))
    elif isinstance(node, Decl):
        if node.name in global_env: 
            raise ValueError('Identifier {} already declared')
        else: 
            global_env[node.name] = eval(node.exp)
    elif isinstance(node, Assign):
        assert(node.name in global_env)
        global_env[node.name] = eval(node.exp)
    else:
        raise TypeError('Type not recognized: {}'.format(type(node)))

parse_grammar = r"""
    ws = (' ' | '\r' | '\n' | '\t')*
    digit = anything:x ?(x in '0123456789') -> x
    num = <digit+>:ds -> int(ds)
    identifier = <letter+>:first <letterOrDigit*>:rest  -> Primary(Type.Ident, first + rest)

    primary   = ws num:n ws                             -> Primary(Type.Num, n)
              | ws '(' exp:e ')' ws                     -> e
              | ws identifier:i                         -> i
    fac       = fac:x ('*' | '/'):op primary:y          -> BinExp(x, op, y)
              | primary
    exp       = exp:x ('+' | '-'):op fac:y              -> BinExp(x, op, y)
              | fac
    printStmt = ws 'print' exp:e ';'                    -> PrintStmt(e)
    init      = ws '=' exp:e                            -> e
    declStmt  = ws 'var' ws identifier:i init?:e ';'    -> Decl(i, e)
    assignStmt= ws identifier:i init:e ';'              -> Assign(i, e)
    stmt      = printStmt
              | declStmt
              | assignStmt
    program   = stmt*
"""

def parse(source):
    bindings = {
        'Type':Type,
        'Primary':Primary,
        'BinExp':BinExp,
        'PrintStmt':PrintStmt,
        'Decl':Decl,
        'Assign':Assign
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
        # print(ast)
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
