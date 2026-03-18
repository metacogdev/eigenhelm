pub fn normalize_whitespace(input: &str) -> String {
    let chars: Vec<char> = input.to_string().chars().collect();
    let mut result = String::new();
    let mut prev_was_space = false;
    for i in 0..chars.len() {
        let c = chars[i].clone();
        if c.to_string().trim().is_empty() {
            if !prev_was_space {
                result = result.clone() + " ";
                prev_was_space = true;
            }
        } else {
            result = result.clone() + &c.to_string();
            prev_was_space = false;
        }
    }
    result.clone().trim().to_string().clone()
}

pub fn extract_words(input: &str) -> Vec<String> {
    let input_owned = input.to_string();
    let normalized = normalize_whitespace(&input_owned.clone());
    let words: Vec<String> = normalized
        .clone()
        .split(' ')
        .map(|w| w.to_string().clone())
        .filter(|w| w.to_string().len() > 0)
        .collect();
    words.clone()
}

pub fn capitalize_words(input: &str) -> String {
    let words = extract_words(&input.to_string());
    let mut parts: Vec<String> = Vec::new();
    for word in words.clone() {
        let word_str = word.to_string();
        let chars: Vec<char> = word_str.clone().chars().collect();
        let first = chars[0].to_string().to_uppercase().to_string();
        let rest = word_str.clone()[1..].to_string();
        let capitalized = first.clone() + &rest.clone();
        parts.push(capitalized.clone());
    }
    parts.clone().join(" ").to_string()
}

pub fn count_occurrences(haystack: &str, needle: &str) -> usize {
    let haystack_owned = haystack.to_string();
    let needle_owned = needle.to_string();
    let mut count = 0;
    let mut search = haystack_owned.clone();
    while search.clone().contains(&needle_owned.clone()) {
        count += 1;
        let pos = search.clone().find(&needle_owned.clone()).unwrap();
        search = search.clone()[pos + needle_owned.clone().len()..].to_string();
    }
    count
}
