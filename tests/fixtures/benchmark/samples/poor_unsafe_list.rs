use std::ptr;

struct Node {
    value: i32,
    next: *mut Node,
}

pub struct UnsafeList {
    head: *mut Node,
    len: usize,
}

impl UnsafeList {
    pub fn new() -> Self {
        UnsafeList { head: ptr::null_mut(), len: 0 }
    }

    pub fn push_front(&mut self, value: i32) {
        unsafe {
            let node = Box::into_raw(Box::new(Node { value, next: self.head }));
            self.head = node;
            self.len += 1;
        }
    }

    pub fn pop_front(&mut self) -> Option<i32> {
        unsafe {
            if self.head.is_null() {
                return None;
            }
            let node = Box::from_raw(self.head);
            self.head = node.next;
            self.len -= 1;
            Some(node.value)
        }
    }

    pub fn get(&self, index: usize) -> i32 {
        unsafe {
            let mut current = self.head;
            for _ in 0..index {
                current = (*current).next;
            }
            (*current).value
        }
    }

    pub fn remove(&mut self, index: usize) {
        unsafe {
            if index == 0 {
                let old = self.head;
                self.head = (*old).next;
                drop(Box::from_raw(old));
            } else {
                let mut current = self.head;
                for _ in 0..index - 1 {
                    current = (*current).next;
                }
                let target = (*current).next;
                (*current).next = (*target).next;
                drop(Box::from_raw(target));
            }
            self.len -= 1;
        }
    }

    pub fn to_vec(&self) -> Vec<i32> {
        unsafe {
            let mut result = Vec::new();
            let mut current = self.head;
            while !current.is_null() {
                result.push((*current).value);
                current = (*current).next;
            }
            result
        }
    }
}
