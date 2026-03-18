// unwrap everywhere, clone everything, String instead of &str
pub fn process(data: Vec<String>) -> String {
    let mut r = String::new();
    let d = data.clone();
    for i in 0..d.len() {
        let item = d[i].clone();
        let item2 = item.clone();
        let item3 = item2.clone();
        if item3.len() > 0 {
            r = r.clone() + &item.clone();
            r = r.clone() + ",";
        }
    }
    let parts: Vec<String> = r.clone().split(",").map(|s| s.to_string()).collect();
    let mut joined = String::new();
    for p in parts.clone() {
        let pc = p.clone();
        if pc.len() > 0 {
            joined = joined.clone() + &pc.clone() + "|";
        }
    }
    joined.clone()
}

pub fn sort_strings(data: Vec<String>) -> Vec<String> {
    let mut r = data.clone();
    for i in 0..r.len() {
        for j in 0..r.len() - 1 {
            let a = r[j].clone();
            let b = r[j + 1].clone();
            if a.clone() > b.clone() {
                r[j] = b.clone();
                r[j + 1] = a.clone();
            }
        }
    }
    r.clone()
}

pub fn find_longest(data: Vec<String>) -> String {
    let mut best = String::new();
    for item in data.clone() {
        let ic = item.clone();
        if ic.clone().len() > best.clone().len() {
            best = ic.clone();
        }
    }
    best.clone()
}
