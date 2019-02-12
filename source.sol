func fib(n)
{
  if (n < 2) return n;
  return fib(n-2) + fib(n-1);
}

func fact(n)
{
  if (n == 0) return 1;
  if (n == 1) return 1;
  return n * fact(n-1);
}

print "Fibonacci:";
for (var i = 0; i < 20; i = i + 1) {
  print fib(i);
}
