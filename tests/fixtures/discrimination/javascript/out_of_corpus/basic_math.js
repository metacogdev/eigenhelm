function add(a, b) {
  return a + b;
}

function subtract(a, b) {
  return a - b;
}

function multiply(a, b) {
  return a * b;
}

function divide(a, b) {
  if (b === 0) {
    console.log("Cannot divide by zero");
    return null;
  }
  return a / b;
}

module.exports = { add, subtract, multiply, divide };
