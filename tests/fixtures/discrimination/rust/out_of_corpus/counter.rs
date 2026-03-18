struct Counter {
    value: i32,
}

impl Counter {
    fn new() -> Counter {
        Counter { value: 0 }
    }

    fn increment(&mut self) {
        self.value = self.value + 1;
    }

    fn decrement(&mut self) {
        self.value = self.value - 1;
    }

    fn get(&self) -> i32 {
        self.value
    }

    fn reset(&mut self) {
        self.value = 0;
    }
}

fn main() {
    let mut c = Counter::new();
    c.increment();
    c.increment();
    c.decrement();
    println!("Count: {}", c.get());
}
