func fib(n)
{
  if (n < 2) return n;
  return fib(n - 2) + fib(n - 1);
}

print "Fibonacci:";

for (var i = 0; i < 10; i = i + 1) {
  print fib(i);
}
