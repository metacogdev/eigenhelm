use std::collections::HashMap;
use std::fs;

pub fn load_scores(path: &str) -> HashMap<String, f64> {
    let content = fs::read_to_string(path).unwrap();
    let mut scores = HashMap::new();
    for line in content.lines() {
        let parts: Vec<&str> = line.split(',').collect();
        let name = parts.get(0).unwrap().to_string();
        let score = parts.get(1).unwrap().parse::<f64>().unwrap();
        scores.insert(name, score);
    }
    scores
}

pub fn top_n(scores: &HashMap<String, f64>, n: usize) -> Vec<(String, f64)> {
    let mut entries: Vec<(String, f64)> = scores
        .iter()
        .map(|(k, v)| (k.clone(), *v))
        .collect();
    entries.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
    entries[..n].to_vec()
}

pub fn merge_score_files(paths: Vec<&str>) -> HashMap<String, f64> {
    let mut merged = HashMap::new();
    for path in paths {
        let scores = load_scores(path);
        for (name, score) in scores {
            let current = merged.get(&name).unwrap_or(&0.0);
            merged.insert(name, current + score);
        }
    }
    merged
}

pub fn compute_stats(scores: &HashMap<String, f64>) -> (f64, f64, f64) {
    let values: Vec<f64> = scores.values().cloned().collect();
    let sum: f64 = values.iter().sum();
    let mean = sum / values.len() as f64;
    let mut sorted = values.clone();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let median = sorted[sorted.len() / 2];
    let variance: f64 = values.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / values.len() as f64;
    let std_dev = variance.sqrt();
    (mean, median, std_dev)
}

pub fn format_report(path: &str) -> String {
    let scores = load_scores(path);
    let (mean, median, std_dev) = compute_stats(&scores);
    let top = top_n(&scores, 3);
    let mut report = format!("Mean: {:.2}\nMedian: {:.2}\nStdDev: {:.2}\nTop 3:\n", mean, median, std_dev);
    for (name, score) in top {
        report += &format!("  {} - {:.2}\n", name, score);
    }
    report
}
