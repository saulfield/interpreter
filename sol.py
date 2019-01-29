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

class Environment:
    def __init__(self, prev):
        self.prev = prev
        self.vars = {}

class Primary:
    def __init__(self, type, val):
        self.type = type
        self.val = val

    def __repr__(self):
        if self.type == Type.Null: return "Null"
        return f"{self.val}"

class BinExp:
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"{self.op} {self.left} {self.right}"

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

class Block:
    def __init__(self, stmts):
        self.stmts = stmts

global_env = Environment(None)
env = global_env

def eval(node):
    global env
    if isinstance(node, Primary):
        if node.type == Type.Ident:
            search_env = env
            while search_env != None:
                if node.val in search_env.vars:
                    break
                search_env = search_env.prev
            assert search_env != None, f"Error: var \'{node.val}\' not found"
            return search_env.vars[node.val]
        return node.val
    elif isinstance(node, BinExp):
        left = eval(node.left)
        right = eval(node.right)
        return arithmetic_ops[node.op](left, right)
    elif isinstance(node, PrintStmt):
        print(eval(node.exp))
    elif isinstance(node, Decl):
        search_env = env
        while search_env != None:
            if node.name in search_env.vars:
                raise ValueError(f"Error: identifier \'{node.name}\' already declared")
            search_env = search_env.prev
        env.vars[node.name] = eval(node.exp)
    elif isinstance(node, Assign):
        search_env = env
        while search_env != None:
            if node.name in search_env.vars:
                break
            search_env = search_env.prev
        assert search_env != None, f"Error: var \'{node.name}\' not found"
        search_env.vars[node.name] = eval(node.exp)
    elif isinstance(node, Block):
        env = Environment(env)
        for stmt in node.stmts:
            eval(stmt)
        env = env.prev
    else:
        raise TypeError(f'Error: type not recognized: {type(node)}')

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
    block     = ws '{' ws stmt*:stmts ws '}' ws         -> Block(stmts)
    stmt      = printStmt
              | declStmt
              | assignStmt
              | block
    program   = stmt*:stmts ws                          -> stmts
"""

def parse(source):
    bindings = {
        'Type':Type,
        'Primary':Primary,
        'BinExp':BinExp,
        'PrintStmt':PrintStmt,
        'Decl':Decl,
        'Assign':Assign,
        'Block':Block
    }
    parser = makeGrammar(parse_grammar, bindings)
    ast = parser(source).program()
    return ast

def interpret(source, reset=True):
    global global_env, env
    if reset:
        global_env = Environment(None)
        env = global_env
    ast = parse(source)
    for stmt in ast:
        eval(stmt)

def main():
    argc = len(sys.argv)
    if argc > 2:
        print(f'Usage:\n\t {sys.argv[0]} <filename>')
        exit(1)
    elif argc == 2:
        # Read and execute file
        with open(sys.argv[1]) as f:
            source = f.read()
        interpret(source)
    else:
        # REPL mode
        while True:
            source = input('>> ')
            interpret(source, reset=False)

if __name__ == "__main__":
    main()
