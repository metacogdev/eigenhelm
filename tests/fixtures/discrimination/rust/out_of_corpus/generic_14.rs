use std::collections::HashMap;

struct WordCounter {
    counts: HashMap<String, usize>,
}

impl WordCounter {
    fn new() -> WordCounter {
        WordCounter {
            counts: HashMap::new(),
        }
    }

    fn add_word(&mut self, word: &str) {
        let lower = word.to_lowercase();
        let count = self.counts.entry(lower).or_insert(0);
        *count += 1;
    }

    fn add_text(&mut self, text: &str) {
        for word in text.split_whitespace() {
            self.add_word(word);
        }
    }

    fn get_count(&self, word: &str) -> usize {
        let lower = word.to_lowercase();
        *self.counts.get(&lower).unwrap_or(&0)
    }

    fn total_words(&self) -> usize {
        let mut total = 0;
        for count in self.counts.values() {
            total += count;
        }
        total
    }

    fn unique_words(&self) -> usize {
        self.counts.len()
    }
}
