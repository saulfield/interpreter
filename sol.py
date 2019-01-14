import sys
from parsley import makeGrammar

parse_grammar = r"""
    program = anything*
"""

def parse(source):
    parser = makeGrammar(parse_grammar, {})
    ast = parser(source).program()
    return ast

def main():
    # if len(sys.argv) != 2:
    #     print("Usage:\n\t" + sys.argv[0] + " <filename>")
    #     exit(1)

    # filename = sys.argv[1]
    filename = "test.sol"

    with open(filename) as f:
        source = f.read()

    ast = parse(source)
    print(ast)
    
if __name__ == "__main__": main()
