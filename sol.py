import sys
import operator as op
from enum import Enum
from parsley import makeGrammar

Type = Enum('Type', 'Null Num Bool String Ident')

arithmetic_ops = {'+': op.add, '-': op.sub, '*': op.mul, '/': op.truediv}
logical_ops = {'>':  op.gt, '<':  op.lt, '==': op.eq, '!=': op.ne, '>=': op.ge, '<=': op.le}
ops = {**arithmetic_ops, **logical_ops}

class Environment(object):
    def __init__(self, prev):
        self.prev = prev
        self.vars = {}

class Primary(object):
    def __init__(self, type, val):
        self.type = type
        if type == Type.Bool:
            if val == 'true':  self.val = True
            if val == 'false': self.val = False
        else:
            self.val = val

class BinExp(object):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class FuncDecl(object):
    def __init__(self, ident_node, args, body):
        self.name = ident_node.val
        self.args = [arg.val for arg in args] if args is not None else None
        self.body = body

class FuncCall(object):
    def __init__(self, ident_node, args):
        self.name = ident_node.val
        self.args = args

class Block:
    def __init__(self, stmts):
        self.stmts = stmts

class VarStatement(object):
    def __init__(self, ident_node, exp):
        self.name = ident_node.val
        self.exp = exp
        if exp is None:
            self.exp = Primary(Type.Null, None)

class Statement(object):
    def __init__(self, exp, thenStmt, elseStmt):
        self.exp = exp
        self.thenStmt = thenStmt
        self.elseStmt = elseStmt

class Decl(VarStatement): pass
class Assign(VarStatement): pass
class PrintStmt(Statement): pass
class WhileStmt(Statement): pass
class IfStmt(Statement): pass
class ReturnStmt(Statement): pass
class ReturnException(Exception): pass

parse_grammar = r"""
    ws = (' ' | '\r' | '\n' | '\t')*
    logical_op = ('>' | '<' | '==' | '!=' | '>=' | '<=' )
    digit = anything:x ?(x in '0123456789')                         -> x
    num = <digit+>:ds                                               -> int(ds)
    ident = <letter+>:first <letterOrDigit*>:rest                   -> Primary(Type.Ident, first + rest)
    string = '"' (~'"' anything)*:c '"'                             -> ''.join(c)

    primary     = ws num:x ws                                       -> Primary(Type.Num, x)
                | ws ('true' | 'false'):x ws                        -> Primary(Type.Bool, x)
                | ws string:x ws                                    -> Primary(Type.String, x)
                | ws callExp:x ws                                   -> x
                | ws '(' exp:x ')' ws                               -> x
                | ws ident:x ws                                     -> x
              
    fac         = fac:x ('*' | '/'):op primary:y                    -> BinExp(x, op, y)
                | primary
    add         = add:x ('+' | '-'):op fac:y                        -> BinExp(x, op, y)
                | fac
    logical     = logical:x logical_op:op add:y                     -> BinExp(x, op, y)
                | add
    exp         = logical

    declStmt    = ws 'var' ws ident:i (ws '=' exp)?:e ';'           -> Decl(i, e)
    declArgs    = ws ident:first (',' ws ident)*:rest               -> [first] + rest
    funcDecl    = ws 'func' ws ident:i ws 
                    '(' ws declArgs?:a ws ')' block:body            -> FuncDecl(i, a, body)
    printStmt   = ws 'print' exp:e ';'                              -> PrintStmt(e, None, None)
    returnStmt  = ws 'return' exp?:e ';'                            -> ReturnStmt(e, None, None)
    assignExp   = ws ident:i ws '=' exp:e                           -> Assign(i, e)
    assignStmt  = assignExp:e ';'                                   -> e
    callArgs    = ws exp:first (',' ws exp)*:rest                   -> [first] + rest
    callExp     = ws ident:i ws '(' ws callArgs?:a ws ')'           -> FuncCall(i, a)
    callStmt    = callExp:e ';'                                     -> e
    block       = ws '{' ws stmt*:stmts ws '}' ws                   -> Block(stmts)
    ifStmt      = ws 'if' ws '(' ws exp:e ws ')' stdStmt:thenStmt 
                    (ws 'else' ws stdStmt)?:elseStmt                -> IfStmt(e, thenStmt, elseStmt)
    whileStmt   = ws 'while' ws '(' ws exp:cond ws ')' stdStmt:stmt -> WhileStmt(cond, stmt, None)
    forStmt     = ws 'for' ws '(' ws
                    (declStmt | stdStmt | ';' -> None):init ws
                    exp?:cond ';' ws
                    (assignExp)?:inc ws ')' ws stdStmt:stmt         -> Block([init, 
                                                                              WhileStmt(Primary(Type.Bool, 'true') 
                                                                              if cond is None else cond, 
                                                                              Block([stmt, inc]), None)])
    stdStmt     = printStmt
                | ifStmt
                | whileStmt
                | forStmt
                | assignStmt
                | returnStmt
                | callStmt
                | block
    stmt        = declStmt
                | funcDecl
                | stdStmt
    program     = stmt*:stmts ws                                    -> stmts
"""

def parse(source):
    parser = makeGrammar(parse_grammar, globals())
    ast = parser(source).program()
    return ast

funcs = {}
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

def safe_len(list_):
    if list_ is None: return 0
    else: return len(list_)

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
            try: eval(stmt)
            except ReturnException as e:
                env = env.prev
                raise e
        env = env.prev
    elif isinstance(node, IfStmt):
        assert is_truthy(node.exp), f"Error: if-statement expression must be truthy"
        if eval(node.exp): eval(node.thenStmt)
        elif node.elseStmt: eval(node.elseStmt)
    elif isinstance(node, WhileStmt):
        assert is_truthy(node.exp), f"Error: while-statement expression must be truthy"
        while eval(node.exp):
            eval(node.thenStmt)
    elif isinstance(node, ReturnStmt):
        raise ReturnException(eval(node.exp))
    elif isinstance(node, FuncDecl):
        assert env is global_env, f"Error: functions may only be declared in global scope"
        funcs[node.name] = node
    elif isinstance(node, FuncCall):
        func = funcs[node.name]
        assert safe_len(func.args) == safe_len(node.args), "Error: number of args do not match"
        env = Environment(env)
        if node.args is not None:
            for i, arg in enumerate(node.args):
                env.vars[func.args[i]] = eval(arg)
        try: eval(func.body)
        except ReturnException as e:
            env = env.prev
            return e.args[0]
        env = env.prev
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
        try:
            eval(stmt)
        except ReturnException as e:
            return e.args[0]

def main():
    argc = len(sys.argv)
    if argc > 2:
        print(f'Usage:\n\t {sys.argv[0]} <filename>')
        exit(1)
    elif argc == 2: # Read and execute file
        with open(sys.argv[1]) as f:
            source = f.read()
        return_val = interpret(source)
        if return_val is not None: print(return_val)
    else:           # REPL mode
        while True:
            source = input('>> ')
            return_val = interpret(source, reset=False)
            if return_val is not None: print(return_val)

if __name__ == "__main__": main()
