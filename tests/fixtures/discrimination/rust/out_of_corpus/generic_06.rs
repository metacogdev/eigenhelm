struct SimpleCounter {
    value: i64,
}

impl SimpleCounter {
    fn new() -> SimpleCounter {
        SimpleCounter { value: 0 }
    }

    fn increment(&mut self) -> i64 {
        self.value += 1;
        self.value
    }

    fn decrement(&mut self) -> i64 {
        self.value -= 1;
        self.value
    }

    fn get(&self) -> i64 {
        self.value
    }

    fn reset(&mut self) {
        self.value = 0;
    }

    fn add(&mut self, n: i64) -> i64 {
        self.value += n;
        self.value
    }
}
