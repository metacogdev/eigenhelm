struct Stack {
    items: Vec<i32>,
}

impl Stack {
    fn new() -> Stack {
        Stack { items: Vec::new() }
    }

    fn push(&mut self, val: i32) {
        self.items.push(val);
    }

    fn pop(&mut self) -> Option<i32> {
        self.items.pop()
    }

    fn peek(&self) -> Option<&i32> {
        self.items.last()
    }

    fn is_empty(&self) -> bool {
        self.items.is_empty()
    }

    fn size(&self) -> usize {
        self.items.len()
    }

    fn clear(&mut self) {
        self.items.clear();
    }

    fn to_vec(&self) -> Vec<i32> {
        self.items.clone()
    }
}
