fn fibonacci(n: u64) -> u64 {
    if n <= 1 {
        return n;
    }
    let mut a: u64 = 0;
    let mut b: u64 = 1;
    for _ in 2..=n {
        let temp = b;
        b = a + b;
        a = temp;
    }
    b
}

fn fibonacci_sequence(count: usize) -> Vec<u64> {
    (0..count as u64).map(fibonacci).collect()
}
