function fibonacci(n) {
  if (n <= 0) return 0;
  if (n === 1) return 1;
  var a = 0;
  var b = 1;
  for (var i = 2; i <= n; i++) {
    var temp = a + b;
    a = b;
    b = temp;
  }
  return b;
}

function isPrime(n) {
  if (n < 2) return false;
  for (var i = 2; i <= Math.sqrt(n); i++) {
    if (n % i === 0) return false;
  }
  return true;
}

function factorial(n) {
  var result = 1;
  for (var i = 2; i <= n; i++) {
    result *= i;
  }
  return result;
}

function gcd(a, b) {
  while (b !== 0) {
    var temp = b;
    b = a % b;
    a = temp;
  }
  return a;
}
