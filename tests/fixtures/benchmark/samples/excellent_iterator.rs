use std::collections::VecDeque;

pub struct WindowedAvg {
    source: Box<dyn Iterator<Item = f64>>,
    window: VecDeque<f64>,
    size: usize,
    sum: f64,
}

impl WindowedAvg {
    pub fn new(source: impl Iterator<Item = f64> + 'static, size: usize) -> Self {
        Self {
            source: Box::new(source),
            window: VecDeque::with_capacity(size),
            size,
            sum: 0.0,
        }
    }
}

impl Iterator for WindowedAvg {
    type Item = f64;

    fn next(&mut self) -> Option<Self::Item> {
        let value = self.source.next()?;
        self.sum += value;
        self.window.push_back(value);

        if self.window.len() > self.size {
            self.sum -= self.window.pop_front().unwrap_or(0.0);
        }

        Some(self.sum / self.window.len() as f64)
    }
}

impl std::iter::FusedIterator for WindowedAvg {}
