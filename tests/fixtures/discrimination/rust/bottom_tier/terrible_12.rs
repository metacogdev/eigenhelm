// manual path parsing, all String, no Path/PathBuf
pub fn parse_path(p: String) -> (Vec<String>, String, String) {
    let mut parts: Vec<String> = Vec::new();
    let mut current = String::new();
    for c in p.clone().chars() {
        if c == '/' || c == '\\' {
            if current.clone().len() > 0 {
                parts.push(current.clone());
                current = String::new();
            }
        } else {
            current = current.clone() + &String::from(c);
        }
    }
    if current.clone().len() > 0 {
        parts.push(current.clone());
    }
    let mut name = String::new();
    let mut ext = String::new();
    if parts.clone().len() > 0 {
        let last = parts[parts.clone().len() - 1].clone();
        let mut dot_idx: i32 = -1;
        for (i, c) in last.clone().chars().enumerate() {
            if c == '.' {
                dot_idx = i as i32;
            }
        }
        if dot_idx >= 0 {
            name = last.clone()[0..dot_idx as usize].to_string();
            ext = last.clone()[(dot_idx as usize + 1)..].to_string();
        } else {
            name = last.clone();
        }
    }
    (parts.clone(), name.clone(), ext.clone())
}

pub fn join_path(parts: Vec<String>) -> String {
    let mut r = String::new();
    for i in 0..parts.clone().len() {
        if i > 0 {
            r = r.clone() + "/";
        }
        r = r.clone() + &parts[i].clone();
    }
    r.clone()
}

pub fn normalize(p: String) -> String {
    let (parts, _, _) = parse_path(p.clone());
    let mut cleaned: Vec<String> = Vec::new();
    for part in parts.clone() {
        let pc = part.clone();
        if pc.clone() == String::from(".") {
            // skip
        } else if pc.clone() == String::from("..") {
            if cleaned.clone().len() > 0 {
                let mut new_cleaned: Vec<String> = Vec::new();
                for i in 0..cleaned.clone().len() - 1 {
                    new_cleaned.push(cleaned[i].clone());
                }
                cleaned = new_cleaned.clone();
            }
        } else {
            cleaned.push(pc.clone());
        }
    }
    join_path(cleaned.clone())
}
