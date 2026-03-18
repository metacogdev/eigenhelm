function fibonacci(n) {
    if (n <= 0) return 0;
    if (n === 1) return 1;
    let a = 0, b = 1;
    for (let i = 2; i <= n; i++) {
        const temp = b;
        b = a + b;
        a = temp;
    }
    return b;
}

function fibonacciSequence(count) {
    const result = [];
    for (let i = 0; i < count; i++) {
        result.push(fibonacci(i));
    }
    return result;
}
