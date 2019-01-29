var a = 1;
print a;
a = 2;
print a;

{
    var b = 3;
    a = b;
    print a;

    {
        var c = 4;
        a = c;
        print a;
    }
}