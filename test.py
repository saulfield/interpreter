import unittest
import sol

valid_sources = []
valid_sources.append("var a = 1;")
valid_sources.append("""
var a = 1;
a = 2;
{
    var b = 3;
    a = b;
    {
        var c = 4;
        a = c;
    }
}
""")

invalid_sources = []
invalid_sources.append("var ;")
invalid_sources.append("var a")
invalid_sources.append("""
var a = 1;
{
    var b = 2;
}
b = 3;
""")
invalid_sources.append("""
var a = 1;
{
    var a = 2;
}
""")
valid_sources.append("""
var a1b2 = 1 + 2;
var a = 1;
a = 2;

{
    var b = 3;
    a = b;

    {
        var c = 4;
        a = c;
    }
}
""")
valid_sources.append("var a = 1; if (a == 1) a = 2;")
valid_sources.append("""var a = 1;

if (a == 1)
{
    a = a + 1;
}
""")
valid_sources.append("""
var a = 2;

if (a == 1)
{
    a = a + 1;
}
else
{
    a = 0;
}
""")
valid_sources.append("var a = true; if (a) a = false;")
valid_sources.append("""
var a = 20;

while (a > 0)
{
    a = a - 1;
}
""")
valid_sources.append("for (var a = 0; a < 10; a = a + 1) a = a + 1;")

def create_test(source):
    def f():
        sol.interpret(source)
    return f

def create_invalid_test(source):
    def f():
        exception_thrown = False
        try:
            sol.interpret(source)
        except Exception:
            exception_thrown = True
        assert exception_thrown, "No exception was thrown"
    return f

def suite():
    suite = unittest.TestSuite()
    for source in valid_sources:
        suite.addTest(unittest.FunctionTestCase(create_test(source)))
    for source in invalid_sources:
        suite.addTest(unittest.FunctionTestCase(create_invalid_test(source)))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())