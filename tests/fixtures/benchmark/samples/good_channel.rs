use std::collections::VecDeque;
use std::sync::{Condvar, Mutex};

pub struct Channel<T> {
    inner: Mutex<ChannelInner<T>>,
    not_empty: Condvar,
}

struct ChannelInner<T> {
    queue: VecDeque<T>,
    closed: bool,
}

impl<T> Channel<T> {
    // Creates a new unbounded channel.
    pub fn new() -> Self {
        // Initialize the channel with an empty queue
        // and set the closed flag to false.
        Channel {
            inner: Mutex::new(ChannelInner {
                queue: VecDeque::new(),
                closed: false,
            }),
            // The condvar will be used to wake up receivers
            // when a new item is available.
            not_empty: Condvar::new(),
        }
    }

    // Send a value into the channel.
    // Returns false if the channel has been closed.
    pub fn send(&self, value: T) -> bool {
        let mut inner = self.inner.lock().expect("lock poisoned");
        // Check if the channel is closed before sending
        if inner.closed {
            return false;
        }
        // Push the value onto the back of the queue
        inner.queue.push_back(value);
        // Notify one waiting receiver that data is available
        self.not_empty.notify_one();
        true
    }

    // Receive a value from the channel.
    // Blocks until a value is available or the channel is closed.
    // Returns None if the channel is closed and empty.
    pub fn recv(&self) -> Option<T> {
        let mut inner = self.inner.lock().expect("lock poisoned");
        // Loop until we get a value or the channel is closed and empty
        loop {
            // Try to pop a value from the front of the queue
            if let Some(value) = inner.queue.pop_front() {
                return Some(value);
            }
            // If the channel is closed and the queue is empty, return None
            if inner.closed {
                return None;
            }
            // Wait for a notification that data is available
            inner = self.not_empty.wait(inner).expect("lock poisoned");
        }
    }

    // Close the channel so no more values can be sent.
    pub fn close(&self) {
        let mut inner = self.inner.lock().expect("lock poisoned");
        // Set the closed flag
        inner.closed = true;
        // Wake up all waiting receivers so they can see the channel is closed
        self.not_empty.notify_all();
    }
}
