struct Queue {
    items: Vec<i32>,
}

impl Queue {
    fn new() -> Queue {
        Queue { items: Vec::new() }
    }

    fn enqueue(&mut self, val: i32) {
        self.items.push(val);
    }

    fn dequeue(&mut self) -> Option<i32> {
        if self.items.is_empty() {
            None
        } else {
            Some(self.items.remove(0))
        }
    }

    fn front(&self) -> Option<&i32> {
        self.items.first()
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
