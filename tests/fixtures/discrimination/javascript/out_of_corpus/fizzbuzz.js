function fizzbuzz(n) {
  var results = [];
  for (var i = 1; i <= n; i++) {
    if (i % 15 === 0) {
      results.push("FizzBuzz");
    } else if (i % 3 === 0) {
      results.push("Fizz");
    } else if (i % 5 === 0) {
      results.push("Buzz");
    } else {
      results.push(i);
    }
  }
  return results;
}

function isPrime(num) {
  if (num < 2) return false;
  for (var i = 2; i <= Math.sqrt(num); i++) {
    if (num % i === 0) return false;
  }
  return true;
}

module.exports = { fizzbuzz, isPrime };
