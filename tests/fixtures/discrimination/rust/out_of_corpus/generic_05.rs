fn reverse_string(s: &str) -> String {
    s.chars().rev().collect()
}

fn is_palindrome(s: &str) -> bool {
    let cleaned: String = s.chars().filter(|c| c.is_alphanumeric()).collect();
    let lower = cleaned.to_lowercase();
    lower == reverse_string(&lower)
}

fn count_vowels(s: &str) -> usize {
    let mut count = 0;
    for ch in s.to_lowercase().chars() {
        if "aeiou".contains(ch) {
            count += 1;
        }
    }
    count
}

fn count_words(s: &str) -> usize {
    s.split_whitespace().count()
}

fn capitalize_first(s: &str) -> String {
    let mut chars = s.chars();
    match chars.next() {
        None => String::new(),
        Some(c) => c.to_uppercase().to_string() + chars.as_str(),
    }
}
