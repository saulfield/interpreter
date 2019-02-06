import sys
from enum import Enum
from parsley import makeGrammar

Type = Enum('Type', 'Null Num Bool Ident')
StmtKind = Enum('StmtKind', 'Print')

# TODO: could probably do some fancy python ast stuff here to make these more compact
arithmetic_ops = {
    '+': lambda x, y: x + y, '-': lambda x, y: x - y,
    '*': lambda x, y: x * y, '/': lambda x, y: x / y,
}

logical_ops = {
    '>': lambda x, y: x > y, '<': lambda x, y: x < y,
    '==': lambda x, y: x == y, '!=': lambda x, y: x != y,
    '>=': lambda x, y: x >= y, '<=': lambda x, y: x <= y,
}

ops = {**arithmetic_ops, **logical_ops}

class Environment:
    def __init__(self, prev):
        self.prev = prev
        self.vars = {}

class Primary:
    def __init__(self, type, val):
        self.type = type
        if type == Type.Bool:
            if val == 'true':  self.val = True
            if val == 'false': self.val = False
        else:
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

class IfStmt:
    def __init__(self, exp, thenStmt, elseStmt):
        self.exp = exp
        self.thenStmt = thenStmt
        self.elseStmt = elseStmt

class WhileStmt:
    def __init__(self, exp, thenStmt):
        self.exp = exp
        self.thenStmt = thenStmt

class Block:
    def __init__(self, stmts):
        self.stmts = stmts

parse_grammar = r"""
    ws = (' ' | '\r' | '\n' | '\t')*
    logical_op = ('>' | '<' | '==' | '!=' | '>=' | '<=' )
    digit = anything:x ?(x in '0123456789')                         -> x
    num = <digit+>:ds                                               -> int(ds)
    identifier = <letter+>:first <letterOrDigit*>:rest              -> Primary(Type.Ident, first + rest)

    primary     = ws num:x ws                                       -> Primary(Type.Num, x)
                | ws ('true' | 'false'):x ws                        -> Primary(Type.Bool, x)
                | ws '(' exp:x ')' ws                               -> x
                | ws identifier:x ws                                -> x
              
    fac         = fac:x ('*' | '/'):op primary:y                    -> BinExp(x, op, y)
                | primary
    add         = add:x ('+' | '-'):op fac:y                        -> BinExp(x, op, y)
                | fac
    logical     = logical:x logical_op:op add:y                     -> BinExp(x, op, y)
                | add
    exp         = logical

    declStmt    = ws 'var' ws identifier:i (ws '=' exp)?:e ';'      -> Decl(i, e)
    printStmt   = ws 'print' exp:e ';'                              -> PrintStmt(e)
    assignExp   = ws identifier:i ws '=' exp:e                      -> Assign(i, e)
    assignStmt  = assignExp:e ';'                                   -> e
    block       = ws '{' ws stmt*:stmts ws '}' ws                   -> Block(stmts)
    ifStmt      = ws 'if' ws '(' ws exp:e ws ')' stdStmt:thenStmt 
                    (ws 'else' ws stdStmt)?:elseStmt                -> IfStmt(e, thenStmt, elseStmt)
    whileStmt   = ws 'while' ws '(' ws exp:cond ws ')' stdStmt:stmt -> WhileStmt(cond, stmt)
    forStmt     = ws 'for' ws '(' ws
                    (declStmt | stdStmt | ';' -> None):init ws
                    exp?:cond ';' ws
                    (assignExp)?:inc ws ')' ws stdStmt:stmt         -> Block([init, 
                                                                              WhileStmt(Primary(Type.Bool, 'true') if cond is None else cond, 
                                                                              Block([stmt, inc]))])
    stdStmt     = printStmt
                | ifStmt
                | whileStmt
                | forStmt
                | assignStmt
                | block
    stmt        = declStmt
                | stdStmt
    program     = stmt*:stmts ws                                -> stmts
"""

def parse(source):
    bindings = {
        'Type':Type,
        'Primary':Primary,
        'BinExp':BinExp,
        'Decl':Decl,
        'PrintStmt':PrintStmt,
        'Assign':Assign,
        'IfStmt':IfStmt,
        'WhileStmt':WhileStmt,
        'Block':Block,
    }
    parser = makeGrammar(parse_grammar, bindings)
    ast = parser(source).program()
    return ast

global_env = Environment(None)
env = global_env

def find_var(varname, env):
    search_env = env
    while search_env != None:
        if varname in search_env.vars:
            break
        search_env = search_env.prev
    return search_env

def is_truthy(node):
    if isinstance(node, Primary) and node.type == Type.Ident: return True
    if isinstance(node, Primary) and node.type == Type.Bool:  return True
    if isinstance(node, BinExp)  and node.op in logical_ops:  return True
    return False

def eval(node):
    global env
    if isinstance(node, Primary):
        if node.type == Type.Ident:
            found_env = find_var(node.val, env)
            assert found_env != None, f"Error: var \'{node.val}\' not found"
            return found_env.vars[node.val]
        return node.val
    elif isinstance(node, BinExp):
        left = eval(node.left)
        right = eval(node.right)
        return ops[node.op](left, right)
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
        found_env = find_var(node.name, env)
        assert found_env != None, f"Error: var \'{node.name}\' not found"
        found_env.vars[node.name] = eval(node.exp)
    elif isinstance(node, Block):
        env = Environment(env)
        for stmt in node.stmts:
            eval(stmt)
        env = env.prev
    elif isinstance(node, IfStmt):
        assert is_truthy(node.exp), f"Error: if-statement expression must be truthy"
        if eval(node.exp):
            eval(node.thenStmt)
        elif node.elseStmt:
                eval(node.elseStmt)
    elif isinstance(node, WhileStmt):
        assert is_truthy(node.exp), f"Error: while-statement expression must be truthy"
        while eval(node.exp):
            eval(node.thenStmt)
    elif node is None:
        pass
    else:
        raise TypeError(f'Error: type not recognized: {type(node)}')

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
